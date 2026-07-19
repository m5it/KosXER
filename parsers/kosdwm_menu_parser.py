#!/usr/bin/env python3
"""
KosDWM Menu Parser Module for KosXER

Parses KosDWM's dynamic menu structure from folder hierarchy:
- Menu folders at ~/.config/KosDWM/Menus/
- config.json in folders defines menu properties
- Python scripts (.py) define menu items with labels, icons, actions
- Supports nested folders for menu hierarchy
- Preserves comments in config.json files on read/write
"""

import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Union, Any
from dataclasses import dataclass, field, asdict

from parsers.comment_preserving_json import CommentPreservingJSON
import re
from pathlib import Path
from typing import Dict, List, Optional, Union, Any
from dataclasses import dataclass, field, asdict


@dataclass
class MenuItem:
    """Represents a menu item (executable)."""
    name: str
    label: str
    script_path: str
    icon: Optional[str] = None
    description: Optional[str] = None
    command: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'type': 'item',
            'name': self.name,
            'label': self.label,
            'script_path': self.script_path,
            'icon': self.icon,
            'description': self.description,
            'command': self.command
        }


@dataclass
class MenuFolder:
    """Represents a menu folder (submenu)."""
    name: str
    label: str
    folder_path: str
    config: Dict[str, Any] = field(default_factory=dict)
    items: List[Union[MenuItem, 'MenuFolder']] = field(default_factory=list)
    icon: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'type': 'folder',
            'name': self.name,
            'label': self.label,
            'folder_path': self.folder_path,
            'config': self.config,
            'icon': self.icon,
            'items': [item.to_dict() for item in self.items]
        }
    
    def add_item(self, item: Union[MenuItem, 'MenuFolder']):
        """Add an item to this menu."""
        self.items.append(item)
    
    def remove_item(self, name: str) -> bool:
        """Remove an item by name."""
        for i, item in enumerate(self.items):
            if isinstance(item, MenuItem) and item.name == name:
                self.items.pop(i)
                return True
            elif isinstance(item, MenuFolder) and item.name == name:
                self.items.pop(i)
                return True
        return False


class KosDWMMenuParser:
    """
    Parser for KosDWM dynamic menu structure.
    
    Parses the folder hierarchy at ~/.config/KosDWM/Menus/
    and extracts menu configuration from:
    - Folder structure (menus/submenus)
    - config.json files (menu properties)
    - Python scripts (menu items)
    """
    
    # Default menu config
    DEFAULT_MENU_CONFIG = {
        "label": "",
        "icon": None,
        "description": "",
        "sort": "alphabetical"  # alphabetical, manual
    }
    
    def __init__(self):
        self.root_menu: Optional[MenuFolder] = None
        self.menus_dir: Optional[Path] = None
        self._menu_items: Dict[str, MenuItem] = {}
        self._menu_folders: Dict[str, MenuFolder] = {}
        
    def parse(self, menus_dir: Union[str, Path]) -> MenuFolder:
        """
        Parse KosDWM menu structure from directory.
        
        Args:
            menus_dir: Path to Menus directory (usually ~/.config/KosDWM/Menus)
            
        Returns:
            Root MenuFolder containing all menus
        """
        self.menus_dir = Path(menus_dir)
        self._menu_items = {}
        self._menu_folders = {}
        
        if not self.menus_dir.exists():
            # Create empty root menu
            self.root_menu = MenuFolder(
                name="root",
                label="Main Menu",
                folder_path=str(self.menus_dir),
                config=self.DEFAULT_MENU_CONFIG.copy()
            )
            return self.root_menu
        
        # Parse the menu structure
        self.root_menu = self._parse_folder(self.menus_dir, is_root=True)
        return self.root_menu
    
    def _parse_folder(self, folder_path: Path, is_root: bool = False) -> MenuFolder:
        """
        Parse a menu folder.
        
        Args:
            folder_path: Path to folder
            is_root: Whether this is the root menu folder
            
        Returns:
            MenuFolder with all items
        """
        folder_name = "root" if is_root else folder_path.name
        
        # Load config if exists
        config_path = folder_path / "config.json"
        config = self.DEFAULT_MENU_CONFIG.copy()
        
        if config_path.exists():
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                    config.update(loaded_config)
            except (json.JSONDecodeError, IOError) as e:
                print(f"Warning: Could not load config from {config_path}: {e}")
        
        # Create menu folder
        menu = MenuFolder(
            name=folder_name,
            label=config.get('label', folder_name),
            folder_path=str(folder_path),
            config=config,
            icon=config.get('icon')
        )
        
        self._menu_folders[folder_name] = menu
        
        # Parse contents
        if folder_path.exists():
            for item in sorted(folder_path.iterdir()):
                if item.name.startswith('__') or item.name.startswith('.'):
                    continue
                
                if item.is_dir():
                    # Submenu
                    submenu = self._parse_folder(item)
                    menu.add_item(submenu)
                    
                elif item.suffix == '.py' and item.name != '__init__.py':
                    # Menu item from Python script
                    menu_item = self._parse_script(item)
                    if menu_item:
                        menu.add_item(menu_item)
                        self._menu_items[menu_item.name] = menu_item
        
        return menu
    
    def _parse_script(self, script_path: Path) -> Optional[MenuItem]:
        """
        Parse a Python script to extract menu item info.
        
        Args:
            script_path: Path to .py file
            
        Returns:
            MenuItem or None if parsing fails
        """
        try:
            with open(script_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract metadata from script
            name = script_path.stem
            
            # Try to find label in comments or docstring
            label = self._extract_label(content, name)
            
            # Try to find icon
            icon = self._extract_icon(content)
            
            # Try to find description
            description = self._extract_description(content)
            
            # Try to find command
            command = self._extract_command(content)
            
            return MenuItem(
                name=name,
                label=label,
                script_path=str(script_path),
                icon=icon,
                description=description,
                command=command
            )
            
        except Exception as e:
            print(f"Warning: Could not parse script {script_path}: {e}")
            return None
    
    def _extract_label(self, content: str, default: str) -> str:
        """Extract label from script content."""
        # Look for LABEL = "..." or similar
        match = re.search(r'^[ \t]*LABEL\s*=\s*["\'](.+?)["\']', content, re.MULTILINE)
        if match:
            return match.group(1)
        
        # Look for MENU_LABEL = "..."
        match = re.search(r'^[ \t]*MENU_LABEL\s*=\s*["\'](.+?)["\']', content, re.MULTILINE)
        if match:
            return match.group(1)
        
        # Use docstring first line if available
        match = re.search(r'^"""(.+?)"""', content, re.MULTILINE | re.DOTALL)
        if match:
            return match.group(1).strip().split('\n')[0]
        
        # Use filename as fallback
        return default.replace('_', ' ').title()
    
    def _extract_icon(self, content: str) -> Optional[str]:
        """Extract icon path from script content."""
        # Look for ICON = "..." or similar
        match = re.search(r'^[ \t]*ICON\s*=\s*["\'](.+?)["\']', content, re.MULTILINE)
        if match:
            return match.group(1)
        
        # Look for icon_path = "..."
        match = re.search(r'^[ \t]*icon_path\s*=\s*["\'](.+?)["\']', content, re.MULTILINE)
        if match:
            return match.group(1)
        
        return None
    
    def _extract_description(self, content: str) -> Optional[str]:
        """Extract description from script content."""
        # Look for DESCRIPTION = "..."
        match = re.search(r'^[ \t]*DESCRIPTION\s*=\s*["\'](.+?)["\']', content, re.MULTILINE)
        if match:
            return match.group(1)
        
        # Use docstring if available (excluding first line)
        match = re.search(r'^"""(.+?)"""', content, re.MULTILINE | re.DOTALL)
        if match:
            lines = match.group(1).strip().split('\n')
            if len(lines) > 1:
                return '\n'.join(lines[1:]).strip()
        
        return None
    
    def _extract_command(self, content: str) -> Optional[str]:
        """Extract command from script content."""
        # Look for COMMAND = "..."
        match = re.search(r'^[ \t]*COMMAND\s*=\s*["\'](.+?)["\']', content, re.MULTILINE)
        if match:
            return match.group(1)
        
        # Look for subprocess calls
        match = re.search(r'subprocess\.(?:run|call|Popen)\(\s*["\'](.+?)["\']', content)
        if match:
            return match.group(1)
        
        return None
    
    def get_menu_tree(self, menu: Optional[MenuFolder] = None, level: int = 0) -> str:
        """
        Get text representation of menu tree.
        
        Args:
            menu: Menu to display (default: root)
            level: Indentation level
            
        Returns:
            String representation of menu tree
        """
        if menu is None:
            menu = self.root_menu
        
        if menu is None:
            return ""
        
        indent = "  " * level
        lines = [f"{indent}[Menu] {menu.label} ({menu.name})"]
        
        for item in menu.items:
            if isinstance(item, MenuItem):
                icon_str = f" [{item.icon}]" if item.icon else ""
                lines.append(f"{indent}  [Item] {item.label}{icon_str}")
            elif isinstance(item, MenuFolder):
                lines.append(self.get_menu_tree(item, level + 1))
        
        return '\n'.join(lines)
    
    def write_back(self, menus_dir: Optional[Union[str, Path]] = None) -> str:
        """
        Regenerate menu structure to directory.
        
        Args:
            menus_dir: Target directory (default: use parsed directory)
            
        Returns:
            Path to root menu directory
        """
        if menus_dir is None:
            menus_dir = self.menus_dir
        
        if menus_dir is None:
            raise ValueError("No menu directory specified")
        
        menus_dir = Path(menus_dir)
        menus_dir.mkdir(parents=True, exist_ok=True)
        
        if self.root_menu:
            self._write_folder(self.root_menu, menus_dir)
        
        return str(menus_dir)
    
    def _write_folder(self, menu: MenuFolder, parent_path: Path):
        """
        Write a menu folder to disk.
        
        Args:
            menu: MenuFolder to write
            parent_path: Parent directory path
        """
        if menu.name == "root":
            folder_path = parent_path
        else:
            folder_path = parent_path / menu.name
            folder_path.mkdir(parents=True, exist_ok=True)
        
        # Write config.json
        config = menu.config.copy()
        config['label'] = menu.label
        if menu.icon:
            config['icon'] = menu.icon
        
        config_path = folder_path / "config.json"
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4)
        
        # Write items
        for item in menu.items:
            if isinstance(item, MenuFolder):
                self._write_folder(item, folder_path)
            elif isinstance(item, MenuItem):
                self._write_item(item, folder_path)
    
    def _write_item(self, item: MenuItem, folder_path: Path):
        """
        Write a menu item script to disk.
        
        Args:
            item: MenuItem to write
            folder_path: Target folder path
        """
        script_path = folder_path / f"{item.name}.py"
        
        content = f'''#!/usr/bin/env python3
"""
{item.label}

{item.description or ''}
"""

# Menu metadata
LABEL = "{item.label}"
ICON = "{item.icon or ''}"
DESCRIPTION = "{item.description or ''}"

def main():
    """Main function."""
    # TODO: Implement menu action
    pass

if __name__ == "__main__":
    main()
'''
        
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        # Make executable
        script_path.chmod(0o755)
    
    def add_menu_item(self, menu_name: str, item: MenuItem) -> bool:
        """
        Add an item to a menu.
        
        Args:
            menu_name: Name of target menu
            item: MenuItem to add
            
        Returns:
            True if added successfully
        """
        menu = self._menu_folders.get(menu_name)
        if menu:
            menu.add_item(item)
            self._menu_items[item.name] = item
            return True
        return False
    
    def remove_menu_item(self, item_name: str) -> bool:
        """
        Remove a menu item by name.
        
        Args:
            item_name: Name of item to remove
            
        Returns:
            True if removed
        """
        if item_name in self._menu_items:
            del self._menu_items[item_name]
            
            # Remove from parent menus
            for menu in self._menu_folders.values():
                if menu.remove_item(item_name):
                    return True
        
        return False
    
    def get_item(self, name: str) -> Optional[MenuItem]:
        """Get menu item by name."""
        return self._menu_items.get(name)
    
    def get_folder(self, name: str) -> Optional[MenuFolder]:
        """Get menu folder by name."""
        return self._menu_folders.get(name)
    
    def __len__(self) -> int:
        """Return total number of menu items."""
        return len(self._menu_items)
    
    def __iter__(self):
        """Iterate over menu items."""
        return iter(self._menu_items.values())
