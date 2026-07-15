#!/usr/bin/env python3
"""
Generic Key-Value Configuration Parser Module for KosXER

Parses simple key-value configuration files like:
- tint2/tint2rc
- openbox autostart
- compton/picom.conf
- General INI-style configs
- Shell-style exports (KEY=value)
"""

import re
from pathlib import Path
from typing import List, Dict, Optional, Union, Any, Callable
from dataclasses import dataclass, field


@dataclass
class KeyValueEntry:
    """Represents a single key-value entry."""
    key: str
    value: str
    section: Optional[str] = None
    comment: Optional[str] = None
    line_number: int = 0
    raw_line: str = ""  # Original line for preservation
    
    def __str__(self) -> str:
        if self.section:
            return f"[{self.section}] {self.key}={self.value}"
        return f"{self.key}={self.value}"


@dataclass
class ConfigSection:
    """Represents a section in a config file."""
    name: str
    entries: List[KeyValueEntry] = field(default_factory=list)
    comment: Optional[str] = None
    line_number: int = 0
    
    def add_entry(self, entry: KeyValueEntry):
        """Add an entry to this section."""
        entry.section = self.name
        self.entries.append(entry)
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get value by key."""
        for entry in self.entries:
            if entry.key == key:
                return entry.value
        return default
    
    def set(self, key: str, value: str):
        """Set or add a key-value pair."""
        for entry in self.entries:
            if entry.key == key:
                entry.value = value
                return
        # If not found, add new
        self.entries.append(KeyValueEntry(key=key, value=value, section=self.name))


class KeyValueParser:
    """
    Generic parser for key-value configuration files.
    
    Supports multiple formats:
    - Simple KEY=VALUE
    - INI-style [section] headers
    - Shell-style exports (export KEY=value)
    - Comment preservation (# and ;)
    - Quoted values
    - Line continuation with backslash
    """
    
    # Patterns for different formats
    SECTION_PATTERN = re.compile(r'^\s*\[(.+?)\]\s*(?:#.*)?$')
    COMMENT_PATTERN = re.compile(r'^\s*(?:#|;|//)(.*)$')
    EXPORT_PATTERN = re.compile(r'^\s*export\s+([A-Za-z_][A-Za-z0-9_]*)=(.*)$')
    KEY_VALUE_PATTERN = re.compile(r'^\s*([A-Za-z_][A-Za-z0-9_\.]*)\s*[=:]\s*(.*)$')
    FLAG_PATTERN = re.compile(r'^\s*([A-Za-z_][A-Za-z0-9_\.]+)\s*(?:#.*)?$')  # Flags without values
    
    def __init__(self, 
                 comment_chars: str = '#;',
                 key_value_delimiter: str = '=',
                 supports_sections: bool = True,
                 supports_exports: bool = False,
                 case_sensitive: bool = True):
        """
        Initialize parser with format options.
        
        Args:
            comment_chars: Characters that start comments
            key_value_delimiter: Character between key and value
            supports_sections: Whether [section] headers are supported
            supports_exports: Whether 'export KEY=value' syntax is supported
            case_sensitive: Whether keys are case sensitive
        """
        self.comment_chars = comment_chars
        self.key_value_delimiter = key_value_delimiter
        self.supports_sections = supports_sections
        self.supports_exports = supports_exports
        self.case_sensitive = case_sensitive
        
        self.entries: List[KeyValueEntry] = []
        self.sections: Dict[str, ConfigSection] = {}
        self.current_section: Optional[ConfigSection] = None
        self.global_section: ConfigSection = ConfigSection(name='global')
        
    def parse(self, content: str) -> Dict[str, ConfigSection]:
        """
        Parse key-value configuration content.
        
        Args:
            content: Configuration file content
            
        Returns:
            Dictionary of sections (includes 'global' for entries before first section)
        """
        self.entries = []
        self.sections = {'global': self.global_section}
        self.current_section = self.global_section
        self.global_section.entries = []
        
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
            if not stripped:
                pending_comment = None
                i += 1
                continue
            
            # Check for comments
            if stripped[0] in self.comment_chars:
                comment_text = stripped[1:].strip()
                pending_comment = comment_text
                i += 1
                continue
            
            # Check for section header
            if self.supports_sections:
                section_match = self.SECTION_PATTERN.match(line)
                if section_match:
                    section_name = section_match.group(1).strip()
                    section = ConfigSection(
                        name=section_name,
                        comment=pending_comment,
                        line_number=line_num
                    )
                    self.sections[section_name] = section
                    self.current_section = section
                    pending_comment = None
                    i += 1
                    continue
            
            # Try export pattern first if supported
            if self.supports_exports:
                export_match = self.EXPORT_PATTERN.match(line)
                if export_match:
                    key = export_match.group(1)
                    value = self._unquote_value(export_match.group(2).strip())
                    self._add_entry(key, value, pending_comment, line_num, line)
                    pending_comment = None
                    i += 1
                    continue
            
            # Try key-value pattern
            kv_match = self.KEY_VALUE_PATTERN.match(line)
            if kv_match:
                key = kv_match.group(1).strip()
                if not self.case_sensitive:
                    key = key.lower()
                value = self._unquote_value(kv_match.group(2).strip())
                self._add_entry(key, value, pending_comment, line_num, line)
                pending_comment = None
                i += 1
                continue
            
            # Try flag pattern (key without value)
            flag_match = self.FLAG_PATTERN.match(line)
            if flag_match:
                key = flag_match.group(1).strip()
                if not self.case_sensitive:
                    key = key.lower()
                # Flags are treated as boolean true
                self._add_entry(key, 'true', pending_comment, line_num, line)
                pending_comment = None
                i += 1
                continue
            
            i += 1
        
        return self.sections
    
    def _add_entry(self, key: str, value: str, comment: Optional[str],
                   line_number: int, raw_line: str):
        """Add an entry to the current section."""
        entry = KeyValueEntry(
            key=key,
            value=value,
            section=self.current_section.name if self.current_section else 'global',
            comment=comment,
            line_number=line_number,
            raw_line=raw_line
        )
        self.entries.append(entry)
        self.current_section.add_entry(entry)
    
    def _unquote_value(self, value: str) -> str:
        """Remove quotes from value if present."""
        if len(value) >= 2:
            if (value[0] == '"' and value[-1] == '"') or \
               (value[0] == "'" and value[-1] == "'"):
                return value[1:-1]
        return value
    
    def _quote_value(self, value: str) -> str:
        """Add quotes to value if needed."""
        if ' ' in value or '\t' in value or '#' in value or ';' in value:
            if '"' not in value:
                return f'"{value}"'
            elif "'" not in value:
                return f"'{value}'"
            else:
                # Value contains both quote types, use double and escape
                return f'"{value.replace(\'"\', \'\\"\')}"'
        return value
    
    def parse_file(self, filepath: Union[str, Path]) -> Dict[str, ConfigSection]:
        """
        Parse a configuration file from disk.
        
        Args:
            filepath: Path to config file
            
        Returns:
            Dictionary of sections
        """
        filepath = Path(filepath)
        
        if not filepath.exists():
            raise FileNotFoundError(f"File not found: {filepath}")
        
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return self.parse(content)
    
    def get(self, key: str, section: Optional[str] = None, default: Any = None) -> Any:
        """
        Get value by key.
        
        Args:
            key: Key to look up
            section: Section name (None for current/global)
            default: Default value if not found
            
        Returns:
            Value or default
        """
        if section:
            sec = self.sections.get(section)
            if sec:
                return sec.get(key, default)
            return default
        
        # Search in current section first, then global
        if self.current_section:
            val = self.current_section.get(key)
            if val is not None:
                return val
        
        return self.global_section.get(key, default)
    
    def set(self, key: str, value: str, section: Optional[str] = None):
        """
        Set value by key.
        
        Args:
            key: Key to set
            value: Value to set
            section: Section name (None for current/global)
        """
        target_section = section or (self.current_section.name if self.current_section else 'global')
        
        if target_section in self.sections:
            self.sections[target_section].set(key, value)
        else:
            # Create new section
            new_section = ConfigSection(name=target_section)
            new_section.set(key, value)
            self.sections[target_section] = new_section
    
    def get_section(self, name: str) -> Optional[ConfigSection]:
        """Get a section by name."""
        return self.sections.get(name)
    
    def add_section(self, name: str) -> ConfigSection:
        """Add a new section."""
        if name not in self.sections:
            self.sections[name] = ConfigSection(name=name)
        return self.sections[name]
    
    def remove_section(self, name: str) -> bool:
        """Remove a section."""
        if name in self.sections and name != 'global':
            del self.sections[name]
            return True
        return False
    
    def get_all_keys(self) -> List[str]:
        """Get all keys across all sections."""
        keys = []
        for section in self.sections.values():
            for entry in section.entries:
                keys.append(f"{section.name}.{entry.key}" if section.name != 'global' else entry.key)
        return keys
    
    def get_sections(self) -> List[str]:
        """Get list of section names."""
        return list(self.sections.keys())
    
    def write_back(self, filepath: Optional[Union[str, Path]] = None,
                   preserve_format: bool = True) -> str:
        """
        Generate configuration file content.
        
        Args:
            filepath: Optional path to write to
            preserve_format: Try to preserve original formatting
            
        Returns:
            Configuration content string
        """
        lines = []
        
        # Write global section first
        if 'global' in self.sections:
            lines.extend(self._format_section(self.sections['global'], preserve_format))
        
        # Write other sections
        for name, section in self.sections.items():
            if name == 'global':
                continue
            
            if lines and lines[-1].strip():
                lines.append('')  # Blank line before section
            
            # Section header
            if section.comment:
                lines.append(f"# {section.comment}")
            lines.append(f"[{name}]")
            
            lines.extend(self._format_section(section, preserve_format))
        
        content = '\n'.join(lines)
        
        if filepath:
            filepath = Path(filepath)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
        
        return content
    
    def _format_section(self, section: ConfigSection, preserve_format: bool) -> List[str]:
        """Format entries in a section."""
        lines = []
        
        for entry in section.entries:
            # Write comment if present
            if entry.comment:
                lines.append(f"# {entry.comment}")
            
            # Format the entry
            if preserve_format and entry.raw_line:
                # Try to preserve original format
                lines.append(entry.raw_line)
            else:
                if entry.value.lower() == 'true' and self._is_flag(entry):
                    # Flag without value
                    lines.append(entry.key)
                else:
                    quoted_value = self._quote_value(entry.value)
                    lines.append(f"{entry.key}{self.key_value_delimiter}{quoted_value}")
        
        return lines
    
    def _is_flag(self, entry: KeyValueEntry) -> bool:
        """Check if entry looks like a flag."""
        return entry.raw_line and '=' not in entry.raw_line and ':' not in entry.raw_line
    
    def __len__(self) -> int:
        """Return total number of entries."""
n        return len(self.entries)
    
    def __iter__(self):
        """Iterate over all entries."""
        return iter(self.entries)
    
    def __contains__(self, key: str) -> bool:
        """Check if key exists."""
        return self.get(key) is not None


# Convenience functions for specific formats

def parse_ini(content: str) -> Dict[str, ConfigSection]:
    """Parse INI-style configuration."""
    parser = KeyValueParser(
        comment_chars=';#',
        key_value_delimiter='=',
        supports_sections=True,
        case_sensitive=False
    )
    return parser.parse(content)


def parse_shell_exports(content: str) -> Dict[str, ConfigSection]:
    """Parse shell export statements."""
    parser = KeyValueParser(
        comment_chars='#',
        key_value_delimiter='=',
        supports_sections=False,
        supports_exports=True
    )
    return parser.parse(content)


def parse_simple_config(content: str) -> Dict[str, ConfigSection]:
    """Parse simple key=value config without sections."""
    parser = KeyValueParser(
        comment_chars='#',
        key_value_delimiter='=',
        supports_sections=False
    )
    return parser.parse(content)
