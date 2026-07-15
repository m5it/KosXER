#!/usr/bin/env python3
"""
Generic Key-Value Parser for KosXER

Handles simple KEY=value format files:
- Bash-style exports (export KEY=value)
- Systemd environment files
- Application config files
- .env files

Features:
- Comments (#)
- Empty lines
- Quoted values (single/double quotes)
- Escape sequences (\\n, \\t, etc.)
- Line continuation with backslash
"""

import re
import os
from pathlib import Path
from typing import List, Dict, Optional, Union, Any
from dataclasses import dataclass, field


@dataclass
class KVEntry:
    """Represents a key-value entry."""
    key: str
    value: str
    comment: Optional[str] = None
    line_number: int = 0
    is_export: bool = False  # Whether it was defined with 'export'
    raw_line: str = ""  # Original line
    
    def to_line(self) -> str:
        """Convert back to file line format."""
        export_prefix = "export " if self.is_export else ""
        if self.comment:
            return f"{export_prefix}{self.key}={self.value}  # {self.comment}"
        return f"{export_prefix}{self.key}={self.value}"


class GenericKVParser:
    """
    Parser for generic KEY=value configuration files.
    
    Supports:
    - Simple KEY=value
    - export KEY=value (bash-style)
    - Comments (#)
    - Quoted values
    - Escape sequences
    - Line continuation
    """
    
    # Patterns
    COMMENT_PATTERN = re.compile(r'^\s*#(.*)$')
    EXPORT_PATTERN = re.compile(r'^\s*export\s+([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)$')
    KV_PATTERN = re.compile(r'^([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)$')
    WHITESPACE_PATTERN = re.compile(r'^\s*$')
    
    def __init__(self):
        self.entries: List[KVEntry] = []
        self._escape_map = {
            '\\n': '\n',
            '\\t': '\t',
            '\\r': '\r',
            '\\\\': '\\',
            '\\"': '"',
            "\\'": "'",
        }
        
    def parse(self, content: str) -> List[KVEntry]:
        """
        Parse KEY=value content.
        
        Args:
            content: File content to parse
            
        Returns:
            List of KVEntry objects
        """
        self.entries = []
        lines = content.split('\n')
        pending_comment = None
        i = 0
        
        while i < len(lines):
            line = lines[i]
            line_num = i + 1
            
            # Handle line continuation with backslash
            while line.rstrip().endswith('\\') and i + 1 < len(lines):
                line = line.rstrip()[:-1] + lines[i + 1]
                i += 1
            
            stripped = line.strip()
            
            # Skip empty lines
            if self.WHITESPACE_PATTERN.match(stripped):
                pending_comment = None
                i += 1
                continue
            
            # Handle comments
            if stripped.startswith('#'):
                comment_text = stripped[1:].strip()
                pending_comment = comment_text
                i += 1
                continue
            
            # Try export pattern first
            export_match = self.EXPORT_PATTERN.match(line)
            if export_match:
                key = export_match.group(1)
                value = self._unescape_value(self._unquote(export_match.group(2).strip()))
                self._add_entry(key, value, pending_comment, line_num, line, is_export=True)
                pending_comment = None
                i += 1
                continue
            
            # Try simple KEY=value
            kv_match = self.KV_PATTERN.match(line)
            if kv_match:
                key = kv_match.group(1)
                value = self._unescape_value(self._unquote(kv_match.group(2).strip()))
                self._add_entry(key, value, pending_comment, line_num, line, is_export=False)
                pending_comment = None
                i += 1
                continue
            
            i += 1
        
        return self.entries
    
    def _add_entry(self, key: str, value: str, comment: Optional[str],
                   line_number: int, raw_line: str, is_export: bool = False):
        """Add a new entry."""
        entry = KVEntry(
            key=key,
            value=value,
            comment=comment,
            line_number=line_number,
            is_export=is_export,
            raw_line=raw_line
        )
        self.entries.append(entry)
    
    def _unquote(self, value: str) -> str:
        """Remove quotes from value."""
        if len(value) >= 2:
            # Double quotes
            if value[0] == '"' and value[-1] == '"':
                return value[1:-1]
            # Single quotes
            if value[0] == "'" and value[-1] == "'":
                return value[1:-1]
        return value
    
    def _unescape_value(self, value: str) -> str:
        """Process escape sequences."""
        result = []
        i = 0
        while i < len(value):
            if value[i] == '\\' and i + 1 < len(value):
                escape = value[i:i+2]
                if escape in self._escape_map:
                    result.append(self._escape_map[escape])
                    i += 2
                    continue
            result.append(value[i])
            i += 1
        return ''.join(result)
    
    def _escape_value(self, value: str) -> str:
        """Escape special characters for writing back."""
        # Reverse the escape map
        reverse_map = {v: k for k, v in self._escape_map.items()}
        result = value
        for char, esc in reverse_map.items():
            result = result.replace(char, esc)
        return result
    
    def parse_file(self, filepath: Union[str, Path]) -> List[KVEntry]:
        """
        Parse a file from disk.
        
        Args:
            filepath: Path to file
            
        Returns:
            List of KVEntry objects
        """
        filepath = Path(filepath)
        
        if not filepath.exists():
            raise FileNotFoundError(f"File not found: {filepath}")
        
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return self.parse(content)
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get value by key."""
        for entry in self.entries:
            if entry.key == key:
                return entry.value
        return default
    
    def set(self, key: str, value: str, is_export: bool = False):
        """Set or add a key-value pair."""
        for entry in self.entries:
            if entry.key == key:
                entry.value = value
                entry.is_export = is_export
                return
        # Add new
        self.entries.append(KVEntry(key=key, value=value, is_export=is_export))
    
    def remove(self, key: str) -> bool:
        """Remove an entry by key."""
        for i, entry in enumerate(self.entries):
            if entry.key == key:
                self.entries.pop(i)
                return True
        return False
    
    def write_back(self, filepath: Optional[Union[str, Path]] = None) -> str:
        """
        Generate file content from entries.
        
        Args:
            filepath: Optional path to write to
            
        Returns:
            File content as string
        """
        lines = []
        
        for entry in self.entries:
            # Write comment if present
            if entry.comment:
                lines.append(f"# {entry.comment}")
            
            # Write the entry
            export_prefix = "export " if entry.is_export else ""
            escaped_value = self._escape_value(entry.value)
            # Quote if contains spaces
            if ' ' in escaped_value and not (escaped_value.startswith('"') or escaped_value.startswith("'")):
                escaped_value = f'"{escaped_value}"'
            lines.append(f"{export_prefix}{entry.key}={escaped_value}")
        
        content = '\n'.join(lines)
        
        if filepath:
            filepath = Path(filepath)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
        
        return content
    
    def to_dict(self) -> Dict[str, str]:
        """Convert entries to dictionary."""
        return {entry.key: entry.value for entry in self.entries}
    
    def from_dict(self, data: Dict[str, str], is_export: bool = False):
        """Load from dictionary."""
        self.entries = []
        for key, value in data.items():
            self.entries.append(KVEntry(key=key, value=value, is_export=is_export))
    
    def __len__(self) -> int:
        """Return number of entries."""
        return len(self.entries)
    
    def __iter__(self):
        """Iterate over entries."""
        return iter(self.entries)
    
    def __contains__(self, key: str) -> bool:
        """Check if key exists."""
        return any(entry.key == key for entry in self.entries)


# Convenience functions

def parse_env_file(filepath: Union[str, Path]) -> Dict[str, str]:
    """Parse a .env file and return dictionary."""
    parser = GenericKVParser()
    parser.parse_file(filepath)
    return parser.to_dict()


def parse_exports(content: str) -> Dict[str, str]:
    """Parse bash export statements."""
    parser = GenericKVParser()
    parser.parse(content)
    return parser.to_dict()
