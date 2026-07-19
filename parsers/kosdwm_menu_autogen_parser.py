#!/usr/bin/env python3
"""
KosDWM Auto-Generative Menu Parser Module for KosXER

DESIGN DECISION
===============
The existing KosDWMMenuParser models the *dynamic* menu tree used by KosDWM:
  - folder == submenu
  - config.json holds menu metadata (label, icon, description, sort)
  - *.py scripts inside folders are menu items

The auto-generative menu system discovered under ~/.config/KosDWM/Menus/
uses a DIFFERENT model:
  - each LEAF folder is a single auto-generated window/menu entry
  - config.json controls how the window is generated
  - companion files (content.html, ok.py) provide static content and callbacks

Because the schemas, file relationships, and editing workflows are different,
this is implemented as a SEPARATE parser class. The existing KosDWMMenuParser
is left untouched for the dynamic/script-based menu tree.

SHARED INFRASTRUCTURE
=====================
Both parsers share the reusable CommentPreservingJSON helper so that
config.json files containing // and /* */ comments can be round-tripped
without losing comments.

AUTO-GENERATIVE SCHEMA
======================
config.json fields:
  - windowContent : str  (filename of static content file, e.g. "content.html")
  - windowScript  : str  (shell command whose output fills the window)
  - title         : str  (window title, used with windowScript)
  - loop          : int  (refresh interval for windowScript output)
  - looptype      : str  (time unit for loop, e.g. "second", "minute", "hour")

Companion files:
  - content.html  : static body content (plain text / HTML)
  - ok.py         : Python module providing run(window) callback

At least one of windowContent or windowScript should be present.

PARSER RESPONSIBILITIES
=======================
1. Read the Menus/ tree and identify every leaf folder as an AutoGenMenuItem.
2. Parse each folder's config.json into AutoGenMenuConfig, preserving comments.
3. Track companion files (content.html, ok.py) without modifying their format.
4. Write config.json back with preserved comments and valid JSON.
5. Provide validation for required fields and allowed looptype values.
"""

from pathlib import Path
from typing import Dict, List, Optional, Union, Any
from dataclasses import dataclass, field

from parsers.comment_preserving_json import CommentPreservingJSON


# Allowed time units for the loop field.
VALID_LOOPTYPES = {"second", "minute", "hour", "millisecond"}


@dataclass
class AutoGenMenuConfig:
    """
    Represents the config.json of a single auto-generative menu entry.
    """
    window_content: Optional[str] = None   # maps to "windowContent"
    window_script: Optional[str] = None    # maps to "windowScript"
    title: Optional[str] = None
    loop: Optional[int] = None
    looptype: Optional[str] = None

    # Raw extra fields preserved for forward compatibility.
    extra: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to a dictionary ready for JSON serialization."""
        data: Dict[str, Any] = {}
        if self.window_content is not None:
            data["windowContent"] = self.window_content
        if self.window_script is not None:
            data["windowScript"] = self.window_script
        if self.title is not None:
            data["title"] = self.title
        if self.loop is not None:
            data["loop"] = self.loop
        if self.looptype is not None:
            data["looptype"] = self.looptype
        data.update(self.extra)
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AutoGenMenuConfig":
        """Create from a parsed dictionary, preserving unknown fields."""
        known = {"windowContent", "windowScript", "title", "loop", "looptype"}
        return cls(
            window_content=data.get("windowContent"),
            window_script=data.get("windowScript"),
            title=data.get("title"),
            loop=data.get("loop"),
            looptype=data.get("looptype"),
            extra={k: v for k, v in data.items() if k not in known},
        )

    def validate(self) -> List[str]:
        """Validate this configuration and return a list of error messages."""
        errors: List[str] = []
        if self.window_content is None and self.window_script is None:
            errors.append("Auto-gen menu must have either windowContent or windowScript")
        if self.loop is not None and (not isinstance(self.loop, int) or self.loop < 0):
            errors.append("loop must be a non-negative integer")
        if self.looptype is not None and self.looptype not in VALID_LOOPTYPES:
            errors.append(f"looptype must be one of: {', '.join(sorted(VALID_LOOPTYPES))}")
        if self.loop is not None and self.looptype is None:
            errors.append("loop requires looptype")
        if self.looptype is not None and self.loop is None:
            errors.append("looptype requires loop")
        return errors


@dataclass
class AutoGenMenuItem:
    """
    Represents a single auto-generative menu entry (one leaf folder).
    """
    name: str
    folder_path: str
    config: AutoGenMenuConfig
    content_path: Optional[str] = None   # e.g. content.html
    ok_script_path: Optional[str] = None # e.g. ok.py

    # Raw bodies loaded from disk; used for write-back.
    content_body: Optional[str] = None
    ok_script: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to a dictionary representation."""
        return {
            "name": self.name,
            "folder_path": self.folder_path,
            "config": self.config.to_dict(),
            "content_path": self.content_path,
            "ok_script_path": self.ok_script_path,
        }

    def validate(self) -> List[str]:
        """Validate this menu entry, including companion file existence."""
        errors: List[str] = []
        errors.extend(self.config.validate())

        cfg = self.config
        if cfg.window_content is not None and self.content_path is None:
            errors.append(f"windowContent references missing file: {cfg.window_content}")
        if cfg.window_script is not None and not cfg.window_script.strip():
            errors.append("windowScript cannot be empty")

        return errors


class KosDWMMenuAutoGenParser:
    """
    Parser for KosDWM auto-generative menu folders.

    Discovers every leaf folder under a Menus/ directory, parses its
    config.json (preserving comments), and tracks companion files.
    """

    # Default config values for a new auto-gen menu entry.
    DEFAULT_CONFIG = AutoGenMenuConfig()

    def __init__(self):
        self.menus_dir: Optional[Path] = None
        self.items: Dict[str, AutoGenMenuItem] = {}
        self._config_helpers: Dict[Path, CommentPreservingJSON] = {}

    def parse(self, menus_dir: Union[str, Path]) -> List[AutoGenMenuItem]:
        """
        Parse the auto-generative menu tree from a directory.

        Args:
            menus_dir: Path to the Menus directory.

        Returns:
            List of AutoGenMenuItem instances found in leaf folders.
        """
        self.menus_dir = Path(menus_dir).expanduser().resolve()
        self.items = {}
        self._config_helpers = {}

        if not self.menus_dir.exists():
            return []

        for folder_path in sorted(self._discover_leaf_folders(self.menus_dir)):
            item = self._parse_folder(folder_path)
            if item is not None:
                self.items[item.name] = item

        return list(self.items.values())

    def _discover_leaf_folders(self, root: Path) -> List[Path]:
        """
        Discover leaf menu folders.

        A folder is considered a leaf menu entry if it contains a
        config.json file. Intermediate folders that only hold other
        folders are ignored.
        """
        leafs: List[Path] = []
        for path in root.rglob("*"):
            if path.is_dir() and (path / "config.json").exists():
                leafs.append(path)
        return leafs

    def _parse_folder(self, folder_path: Path) -> Optional[AutoGenMenuItem]:
        """
        Parse a single leaf folder into an AutoGenMenuItem.
        """
        config_path = folder_path / "config.json"
        cpj = CommentPreservingJSON()

        try:
            with open(config_path, "r", encoding="utf-8") as f:
                raw_text = f.read()
            data = cpj.load(raw_text)
        except Exception as exc:
            print(f"Warning: could not parse {config_path}: {exc}")
            return None

        self._config_helpers[folder_path] = cpj
        config = AutoGenMenuConfig.from_dict(data)

        # Load static content companion file.
        content_path: Optional[str] = None
        content_body: Optional[str] = None
        if config.window_content:
            cp = folder_path / config.window_content
            if cp.exists():
                content_path = str(cp)
                try:
                    with open(cp, "r", encoding="utf-8") as f:
                        content_body = f.read()
                except Exception as exc:
                    print(f"Warning: could not read {cp}: {exc}")

        # Load OK callback script.
        ok_script_path: Optional[str] = None
        ok_script: Optional[str] = None
        op = folder_path / "ok.py"
        if op.exists():
            ok_script_path = str(op)
            try:
                with open(op, "r", encoding="utf-8") as f:
                    ok_script = f.read()
            except Exception as exc:
                print(f"Warning: could not read {op}: {exc}")

        return AutoGenMenuItem(
            name=folder_path.name,
            folder_path=str(folder_path),
            config=config,
            content_path=content_path,
            ok_script_path=ok_script_path,
            content_body=content_body,
            ok_script=ok_script,
        )

    def write_back(self, menus_dir: Optional[Union[str, Path]] = None) -> str:
        """
        Write all auto-gen menu items back to disk, preserving comments.

        Args:
            menus_dir: Target directory (defaults to parsed directory).

        Returns:
            Path to the root menu directory.
        """
        if menus_dir is None:
            menus_dir = self.menus_dir
        if menus_dir is None:
            raise ValueError("No menu directory specified")

        menus_dir = Path(menus_dir)
        menus_dir.mkdir(parents=True, exist_ok=True)

        for item in self.items.values():
            self._write_item(item, menus_dir)

        return str(menus_dir)

    def _write_item(self, item: AutoGenMenuItem, root: Path):
        """
        Write a single auto-gen menu item back to disk.
        """
        folder_path = Path(item.folder_path)
        if not folder_path.is_absolute():
            folder_path = root / folder_path
        folder_path.mkdir(parents=True, exist_ok=True)

        # Write config.json, preserving comments.
        config_path = folder_path / "config.json"
        cpj = self._config_helpers.get(folder_path, CommentPreservingJSON())
        config_text = cpj.dump(item.config.to_dict())
        with open(config_path, "w", encoding="utf-8") as f:
            f.write(config_text)

        # Write static content companion file.
        if item.content_body is not None and item.config.window_content:
            cp = folder_path / item.config.window_content
            with open(cp, "w", encoding="utf-8") as f:
                f.write(item.content_body)

        # Write OK callback script.
        if item.ok_script is not None:
            op = folder_path / "ok.py"
            with open(op, "w", encoding="utf-8") as f:
                f.write(item.ok_script)

    def validate(self) -> tuple[bool, List[str]]:
        """
        Validate all loaded auto-gen menu items.

        Returns:
            Tuple of (is_valid, list_of_error_messages).
        """
        errors: List[str] = []
        for item in self.items.values():
            item_errors = item.validate()
            for err in item_errors:
                errors.append(f"[{item.name}] {err}")
        return len(errors) == 0, errors

    def get_item(self, name: str) -> Optional[AutoGenMenuItem]:
        """Get an auto-gen menu item by folder name."""
        return self.items.get(name)

    def add_item(self, item: AutoGenMenuItem) -> None:
        """Add or replace an auto-gen menu item."""
        self.items[item.name] = item

    def remove_item(self, name: str) -> bool:
        """Remove an auto-gen menu item by name."""
        if name in self.items:
            del self.items[name]
            return True
        return False

    def __len__(self) -> int:
        return len(self.items)

    def __iter__(self):
        return iter(self.items.values())
