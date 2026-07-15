"""
Parsers module for KosXER.

Contains parsers for various configuration file formats and
a registry system for automatic parser detection.
"""

import os
import re
from pathlib import Path
from typing import Dict, Type, Optional, Callable, Any, Tuple
from functools import wraps

# Import all parsers
from .xresources_parser import XResourcesParser, XResourceEntry
from .openbox_parser import (
    OpenBoxMenuParser, OpenBoxRCParser,
    OpenBoxMenu, OpenBoxMenuItem, OpenBoxSeparator
)
from .generic_kv_parser import GenericKVParser, KVEntry


class ParserInfo:
    """Information about a registered parser."""
    def __init__(self, name: str, parser_class: Type, 
                 extensions: list = None, patterns: list = None,
                 description: str = "", icon_hint: str = ""):
        self.name = name
        self.parser_class = parser_class
        self.extensions = extensions or []
        self.patterns = patterns or []  # Regex patterns for filenames
        self.description = description
        self.icon_hint = icon_hint
    
    def matches(self, filepath: str) -> bool:
        """Check if filepath matches this parser."""
        filename = os.path.basename(filepath).lower()
        
        # Check extensions
        for ext in self.extensions:
            if filename.endswith(ext.lower()):
                return True
        
        # Check patterns
        for pattern in self.patterns:
            if re.match(pattern, filename, re.IGNORECASE):
                return True
        
        return False


class ParserRegistry:
    """
    Registry for managing parsers and their file associations.
    
    Provides automatic parser detection based on file extensions
    and patterns.
    """
    
    def __init__(self):
        self._parsers: Dict[str, ParserInfo] = {}
        self._register_default_parsers()
    
    def _register_default_parsers(self):
        """Register the built-in parsers."""
        # XResources parser
        self.register(
            name="xresources",
            parser_class=XResourcesParser,
            extensions=['.Xresources', '.Xdefaults', '.Xresources-xft'],
            patterns=[r'.*\.Xresources.*'],
            description="X11 Resource Configuration",
            icon_hint="preferences-desktop-theme"
        )
        
        # OpenBox Menu parser
        self.register(
            name="openbox_menu",
            parser_class=OpenBoxMenuParser,
            extensions=[],
            patterns=[r'^menu\.xml$', r'^pipemenu.*\.xml$'],
            description="OpenBox Application Menu",
            icon_hint="applications-other"
        )
        
        # OpenBox RC parser
        self.register(
            name="openbox_rc",
            parser_class=OpenBoxRCParser,
            extensions=[],
            patterns=[r'^rc\.xml$'],
            description="OpenBox Window Manager Configuration",
            icon_hint="preferences-system-windows"
        )
        
        # Generic Key-Value parser (for .conf, .env, etc.)
        self.register(
            name="generic_kv",
            parser_class=GenericKVParser,
            extensions=['.conf', '.cfg', '.env', '.rc', '.ini'],
            patterns=[r'.*\.env\..*', r'.*\.config$'],
            description="Configuration File",
            icon_hint="text-x-generic"
        )
        
        # Shell exports parser (for .sh, .bashrc, etc.)
        self.register(
            name="shell_exports",
            parser_class=GenericKVParser,
            extensions=['.sh', '.bashrc', '.bash_profile', '.profile', '.zshrc'],
            patterns=[r'^\.bash.*', r'^\.zsh.*', r'^\.profile$'],
            description="Shell Environment File",
            icon_hint="text-x-script"
        )
    
    def register(self, name: str, parser_class: Type,
                 extensions: list = None, patterns: list = None,
                 description: str = "", icon_hint: str = ""):
        """
        Register a new parser.
        
        Args:
            name: Unique identifier for this parser
            parser_class: The parser class
            extensions: List of file extensions (e.g., ['.conf', '.cfg'])
            patterns: List of regex patterns for matching filenames
            description: Human-readable description
            icon_hint: Icon name for GUI
        """
        self._parsers[name] = ParserInfo(
            name=name,
            parser_class=parser_class,
            extensions=extensions or [],
            patterns=patterns or [],
            description=description,
            icon_hint=icon_hint
        )
    
    def unregister(self, name: str) -> bool:
        """Remove a parser from registry."""
        if name in self._parsers:
            del self._parsers[name]
            return True
        return False
    
    def get_parser_info(self, name: str) -> Optional[ParserInfo]:
        """Get parser info by name."""
        return self._parsers.get(name)
    
    def detect(self, filepath: str) -> Optional[ParserInfo]:
        """
        Detect the appropriate parser for a file.
        
        Args:
            filepath: Path to the file
            
        Returns:
            ParserInfo or None if no match
        """
        filepath = str(filepath)
        
        for parser_info in self._parsers.values():
            if parser_info.matches(filepath):
                return parser_info
        
        return None
    
    def create_parser(self, name: str, *args, **kwargs) -> Any:
        """
        Create a parser instance by name.
        
        Args:
            name: Parser name
            *args, **kwargs: Arguments for parser constructor
            
        Returns:
            Parser instance
        """
        info = self._parsers.get(name)
        if info:
            return info.parser_class(*args, **kwargs)
        raise ValueError(f"Unknown parser: {name}")
    
    def list_parsers(self) -> Dict[str, str]:
        """Get list of registered parsers with descriptions."""
        return {name: info.description for name, info in self._parsers.items()}
    
    def get_supported_extensions(self) -> set:
        """Get all supported file extensions."""
        extensions = set()
        for info in self._parsers.values():
            extensions.update(info.extensions)
        return extensions


# Global registry instance
_registry = ParserRegistry()


# Registration decorator
def parser_for(extensions: list = None, patterns: list = None,
               description: str = "", icon_hint: str = ""):
    """
    Decorator to register a parser class.
    
    Usage:
        @parser_for(extensions=['.conf'], description="Config file")
        class MyParser:
            pass
    """
    def decorator(cls):
        name = cls.__name__.lower().replace('parser', '')
        _registry.register(
            name=name,
            parser_class=cls,
            extensions=extensions or [],
            patterns=patterns or [],
            description=description or cls.__doc__ or "",
            icon_hint=icon_hint
        )
        return cls
    return decorator


# Convenience functions
def detect_parser(filepath: str) -> Optional[Type]:
    """
    Detect and return the appropriate parser class for a file.
    
    Args:
        filepath: Path to the file
        
    Returns:
        Parser class or None
    """
    info = _registry.detect(filepath)
    return info.parser_class if info else None


def get_file_type_info(filepath: str) -> Tuple[str, str, Optional[Type]]:
    """
    Get file type information for a file.
    
    Args:
        filepath: Path to the file
        
    Returns:
        Tuple of (description, icon_hint, parser_class)
    """
    info = _registry.detect(filepath)
    if info:
        return (info.description, info.icon_hint, info.parser_class)
    
    # Default for unknown files
    return ("Unknown File Type", "text-x-generic", None)


def create_parser_for_file(filepath: str, *args, **kwargs) -> Any:
    """
    Create a parser instance appropriate for the file.
    
    Args:
        filepath: Path to the file
        *args, **kwargs: Arguments for parser constructor
        
    Returns:
        Parser instance
        
    Raises:
        ValueError: If no suitable parser found
    """
    parser_class = detect_parser(filepath)
    if parser_class:
        return parser_class(*args, **kwargs)
    raise ValueError(f"No parser available for: {filepath}")


def get_supported_formats() -> Dict[str, Dict[str, Any]]:
    """
    Get information about all supported formats.
    
    Returns:
        Dictionary mapping format names to their info
    """
    return {
        name: {
            'description': info.description,
            'extensions': info.extensions,
            'patterns': info.patterns,
            'icon_hint': info.icon_hint,
        }
        for name, info in _registry._parsers.items()
    }


# Export all parser classes
__all__ = [
    # Registry
    'ParserRegistry', 'parser_for', 'detect_parser',
    'get_file_type_info', 'create_parser_for_file', 'get_supported_formats',
    
    # XResources
    'XResourcesParser', 'XResourceEntry',
    
    # OpenBox
    'OpenBoxMenuParser', 'OpenBoxRCParser',
    'OpenBoxMenu', 'OpenBoxMenuItem', 'OpenBoxSeparator',
    
    # Generic KV
    'GenericKVParser', 'KVEntry',
]
