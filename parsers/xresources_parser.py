#!/usr/bin/env python3
"""
Xresources/Xdefaults Parser Module for KosXER

Parses .Xresources and .Xdefaults files with support for:
- X11 resource format: resource.class*subresource: value
- Preprocessor directives: #include, #ifdef, #ifndef, #endif, #else
- Comments and empty lines
- Escaped newlines for multi-line values
"""

import re
import os
from pathlib import Path
from typing import List, Dict, Optional, Union
from dataclasses import dataclass, field


@dataclass
class XResourceEntry:
    """Represents a single X resource entry."""
    resource_path: str          # Full resource path (e.g., "XTerm*background")
    value: str                  # The value
    comment: Optional[str] = None  # Associated comment
    line_number: int = 0        # Line number in file
    is_conditional: bool = False  # Whether inside #ifdef/#ifndef
    condition: Optional[str] = None  # The condition variable name
    
    def __str__(self) -> str:
        return f"{self.resource_path}: {self.value}"


@dataclass
class PreprocessorDirective:
    """Represents a preprocessor directive."""
    directive: str              # #include, #ifdef, #endif, etc.
    argument: Optional[str] = None  # File path or condition variable
    line_number: int = 0


class XResourcesParser:
    """
    Parser for X11 .Xresources and .Xdefaults files.
    
    Supports:
    - Standard resource definitions
    - Wildcards (* and ?)
    - Preprocessor directives
    - Comments preservation
    """
    
    # Regex patterns
    RESOURCE_PATTERN = re.compile(r'^([^:]+):\s*(.+)$')
    COMMENT_PATTERN = re.compile(r'^\s*!(.*)$')
    PREPROC_PATTERN = re.compile(r'^\s*#(include|ifdef|ifndef|endif|else)\s*(.*)$')
    WHITESPACE_PATTERN = re.compile(r'^\s*$')
    
    def __init__(self):
        self.entries: List[XResourceEntry] = []
        self.preprocessor_directives: List[PreprocessorDirective] = []
        self.includes: List[str] = []
        self.conditional_stack: List[str] = []
        self.current_condition: Optional[str] = None
        
    def parse(self, content: str, base_path: Optional[str] = None) -> List[XResourceEntry]:
        """
        Parse Xresources content.
        
        Args:
            content: The file content to parse
            base_path: Base directory for resolving #include paths
            
        Returns:
            List of XResourceEntry objects
        """
        self.entries = []
        self.preprocessor_directives = []
        self.includes = []
        self.conditional_stack = []
        self.current_condition = None
        
        lines = content.split('\n')
        pending_comment = None
        i = 0
        
        while i < len(lines):
            line = lines[i]
            line_num = i + 1
            
            # Handle escaped newlines (line ending with \)
            while line.rstrip().endswith('\\') and i + 1 < len(lines):
                line = line.rstrip()[:-1] + lines[i + 1]
                i += 1
            
            stripped = line.strip()
            
            # Skip empty lines but track them for context
            if self.WHITESPACE_PATTERN.match(stripped):
                pending_comment = None
                i += 1
                continue
            
            # Handle comments (lines starting with !)
            if stripped.startswith('!'):
                comment_text = stripped[1:].strip()
                pending_comment = comment_text
                i += 1
                continue
            
            # Handle preprocessor directives
            preproc_match = self.PREPROC_PATTERN.match(line)
            if preproc_match:
                directive = preproc_match.group(1)
                argument = preproc_match.group(2).strip() if preproc_match.group(2) else None
                
                self._handle_preprocessor(directive, argument, line_num, base_path)
                i += 1
                continue
            
            # Handle resource definitions
            resource_match = self.RESOURCE_PATTERN.match(line)
            if resource_match:
                resource_path = resource_match.group(1).strip()
                value = resource_match.group(2).strip()
                
                entry = XResourceEntry(
                    resource_path=resource_path,
                    value=value,
                    comment=pending_comment,
                    line_number=line_num,
                    is_conditional=bool(self.conditional_stack),
                    condition=self.current_condition
                )
                self.entries.append(entry)
                pending_comment = None
            
            i += 1
        
        return self.entries
    
    def _handle_preprocessor(self, directive: str, argument: Optional[str], 
                            line_num: int, base_path: Optional[str]):
        """Handle preprocessor directives."""
        self.preprocessor_directives.append(
            PreprocessorDirective(directive=directive, argument=argument, line_number=line_num)
        )
        
        if directive == 'include' and argument:
            # Handle include directive
            self.includes.append(argument)
            
            # Try to load and parse included file
            if base_path:
                include_path = os.path.join(base_path, argument)
                if os.path.exists(include_path):
                    with open(include_path, 'r') as f:
                        include_content = f.read()
                    # Recursively parse included content
                    self.parse(include_content, os.path.dirname(include_path))
                    
        elif directive in ('ifdef', 'ifndef'):
            # Track conditional context
            self.conditional_stack.append(directive)
            self.current_condition = argument
            
        elif directive == 'endif':
            # Pop conditional context
            if self.conditional_stack:
                self.conditional_stack.pop()
            self.current_condition = self.conditional_stack[-1] if self.conditional_stack else None
            
        elif directive == 'else':
            # Toggle conditional state
            if self.conditional_stack:
                # Simple toggle - in real implementation would need symbol table
                pass
    
    def parse_file(self, filepath: Union[str, Path]) -> List[XResourceEntry]:
        """
        Parse an Xresources file from disk.
        
        Args:
            filepath: Path to the .Xresources or .Xdefaults file
            
        Returns:
            List of XResourceEntry objects
        """
        filepath = Path(filepath)
        
        if not filepath.exists():
            raise FileNotFoundError(f"File not found: {filepath}")
        
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        base_path = str(filepath.parent)
        return self.parse(content, base_path)
    
    def get_value(self, resource_path: str) -> Optional[str]:
        """
        Get value for a specific resource path.
        
        Supports wildcard matching for * and ?.
        """
        # First try exact match
        for entry in self.entries:
            if entry.resource_path == resource_path:
                return entry.value
        
        # Then try wildcard matching
        for entry in self.entries:
            if self._match_pattern(entry.resource_path, resource_path):
                return entry.value
        
        return None
    
    def _match_pattern(self, pattern: str, target: str) -> bool:
        """Match a resource pattern against a target path."""
        # Convert X11 pattern to regex
        # * matches any sequence of characters
        # ? matches any single character
        regex_pattern = pattern.replace('.', r'\.')
        regex_pattern = regex_pattern.replace('*', '.*')
        regex_pattern = regex_pattern.replace('?', '.')
        regex_pattern = '^' + regex_pattern + '$'
        
        try:
            return bool(re.match(regex_pattern, target))
        except re.error:
            return False
    
    def get_resources_by_class(self, class_name: str) -> List[XResourceEntry]:
        """Get all resources for a specific class (e.g., 'XTerm')."""
        return [e for e in self.entries if class_name in e.resource_path]
    
    def get_all_classes(self) -> List[str]:
        """Extract all unique resource class names."""
        classes = set()
        for entry in self.entries:
            # Extract class from resource path (first component)
            parts = entry.resource_path.replace('*', '.').replace('?', '.').split('.')
            if parts and parts[0]:
                classes.add(parts[0])
        return sorted(list(classes))
    
    def write_back(self, filepath: Optional[Union[str, Path]] = None) -> str:
        """
        Generate Xresources file content from parsed entries.
        
        Args:
            filepath: Optional path to write to file
            
        Returns:
            The generated content as string
        """
        lines = []
        last_comment = None
        
        for entry in self.entries:
            # Write comment if present and different from last
            if entry.comment and entry.comment != last_comment:
                lines.append(f"! {entry.comment}")
                last_comment = entry.comment
            
            # Write conditional directives if needed
            if entry.is_conditional and entry.condition:
                # This is simplified - real implementation would track full conditional structure
                pass
            
            # Write resource definition
            lines.append(f"{entry.resource_path}:\t{entry.value}")
        
        content = '\n'.join(lines)
        
        if filepath:
            filepath = Path(filepath)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
        
        return content
    
    def update_value(self, resource_path: str, new_value: str) -> bool:
        """
        Update the value of an existing resource.
        
        Args:
            resource_path: The resource path to update
            new_value: The new value
            
        Returns:
            True if updated, False if not found
        """
        for entry in self.entries:
            if entry.resource_path == resource_path:
                entry.value = new_value
                return True
        return False
    
    def add_entry(self, resource_path: str, value: str, 
                  comment: Optional[str] = None) -> XResourceEntry:
        """
        Add a new resource entry.
        
        Args:
            resource_path: The resource path
            value: The value
            comment: Optional comment
            
        Returns:
            The created XResourceEntry
        """
        entry = XResourceEntry(
            resource_path=resource_path,
            value=value,
            comment=comment,
            line_number=len(self.entries) + 1
        )
        self.entries.append(entry)
        return entry
    
    def remove_entry(self, resource_path: str) -> bool:
        """
        Remove a resource entry by path.
        
        Args:
            resource_path: The resource path to remove
            
        Returns:
            True if removed, False if not found
        """
        for i, entry in enumerate(self.entries):
            if entry.resource_path == resource_path:
                self.entries.pop(i)
                return True
        return False
    
    def __len__(self) -> int:
        """Return number of entries."""
        return len(self.entries)
    
    def __iter__(self):
        """Allow iteration over entries."""
        return iter(self.entries)
