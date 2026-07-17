#!/usr/bin/env python3
"""
KosDWM Configuration Parser Module for KosXER

Parses KosDWM's config.json file with support for:
- JSON configuration parsing with validation
- Default values for missing keys
- Color validation (hex colors)
- Proper JSON formatting on write-back
"""

import json
import re
from pathlib import Path
from typing import Dict, Optional, Union, Any
from dataclasses import dataclass, field, asdict


@dataclass
class KosDWMConfig:
    """Represents KosDWM configuration."""
    active_button_bg: str = "#4a90d9"
    inactive_button_bg: str = "#606060"
    bar_height: int = 50
    button_height: int = 1
    combobox_ipady: int = 1
    layout_mode: str = "buttons"  # "buttons" or "comboboxes"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'KosDWMConfig':
        """Create from dictionary with defaults for missing keys."""
        return cls(
            active_button_bg=data.get('active_button_bg', cls.active_button_bg),
            inactive_button_bg=data.get('inactive_button_bg', cls.inactive_button_bg),
            bar_height=data.get('bar_height', cls.bar_height),
            button_height=data.get('button_height', cls.button_height),
            combobox_ipady=data.get('combobox_ipady', cls.combobox_ipady),
            layout_mode=data.get('layout_mode', cls.layout_mode)
        )


class KosDWMConfigParser:
    """
    Parser for KosDWM config.json files.
    
    Supports:
    - JSON parsing with validation
    - Default value handling
    - Color validation
    - Formatted JSON output
    """
    
    # Default configuration
    DEFAULT_CONFIG = {
        "active_button_bg": "#4a90d9",
        "inactive_button_bg": "#606060",
        "bar_height": 50,
        "button_height": 1,
        "combobox_ipady": 1,
        "layout_mode": "buttons"
    }
    
    # Valid layout modes
    VALID_LAYOUT_MODES = ["buttons", "comboboxes"]
    
    # Hex color pattern
    COLOR_PATTERN = re.compile(r'^#[0-9a-fA-F]{6}$')
    
    def __init__(self):
        self.config: KosDWMConfig = KosDWMConfig()
        self.config_path: Optional[Path] = None
        self._raw_data: Dict[str, Any] = {}
        
    def parse(self, content: str) -> KosDWMConfig:
        """
        Parse JSON configuration content.
        
        Args:
            content: JSON content string
            
        Returns:
            KosDWMConfig object
            
        Raises:
            json.JSONDecodeError: If content is invalid JSON
        """
        try:
            data = json.loads(content)
            self._raw_data = data
            self.config = KosDWMConfig.from_dict(data)
            return self.config
        except json.JSONDecodeError as e:
            raise json.JSONDecodeError(f"Invalid JSON: {e}", e.doc, e.pos)
    
    def parse_file(self, filepath: Union[str, Path]) -> KosDWMConfig:
        """
        Parse KosDWM config from file.
        
        Args:
            filepath: Path to config.json
            
        Returns:
            KosDWMConfig object
        """
        filepath = Path(filepath)
        self.config_path = filepath
        
        if not filepath.exists():
            # Return default config
            self.config = KosDWMConfig()
            return self.config
        
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return self.parse(content)
    
    def write_back(self, filepath: Optional[Union[str, Path]] = None) -> str:
        """
        Generate formatted JSON content.
        
        Args:
            filepath: Optional path to write to
            
        Returns:
            Formatted JSON string
        """
        data = self.config.to_dict()
        
        # Create formatted JSON
        content = json.dumps(data, indent=4, sort_keys=False)
        
        if filepath:
            filepath = Path(filepath)
            filepath.parent.mkdir(parents=True, exist_ok=True)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
        
        return content
    
    def update_value(self, key: str, value: Any) -> bool:
        """
        Update a configuration value.
        
        Args:
            key: Configuration key
            value: New value
            
        Returns:
            True if updated, False if key doesn't exist
        """
        if hasattr(self.config, key):
            setattr(self.config, key, value)
            return True
        return False
    
    def validate(self) -> tuple[bool, list[str]]:
        """
        Validate current configuration.
        
        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []
        
        # Validate colors
        if not self._is_valid_color(self.config.active_button_bg):
            errors.append(f"Invalid active_button_bg color: {self.config.active_button_bg}")
        
        if not self._is_valid_color(self.config.inactive_button_bg):
            errors.append(f"Invalid inactive_button_bg color: {self.config.inactive_button_bg}")
        
        # Validate layout_mode
        if self.config.layout_mode not in self.VALID_LAYOUT_MODES:
            errors.append(f"Invalid layout_mode: {self.config.layout_mode}. "
                         f"Must be one of: {', '.join(self.VALID_LAYOUT_MODES)}")
        
        # Validate numeric values
        if self.config.bar_height < 0:
            errors.append(f"bar_height must be non-negative: {self.config.bar_height}")
        
        if self.config.button_height < 0:
            errors.append(f"button_height must be non-negative: {self.config.button_height}")
        
        if self.config.combobox_ipady < 0:
            errors.append(f"combobox_ipady must be non-negative: {self.config.combobox_ipady}")
        
        return len(errors) == 0, errors
    
    def _is_valid_color(self, color: str) -> bool:
        """Check if string is a valid hex color."""
        return bool(self.COLOR_PATTERN.match(color))
    
    def get_color_preview(self, color_name: str) -> Optional[str]:
        """Get color value for preview."""
        if color_name == 'active_button_bg':
            return self.config.active_button_bg
        elif color_name == 'inactive_button_bg':
            return self.config.inactive_button_bg
        return None
    
    def reset_to_defaults(self):
        """Reset configuration to default values."""
        self.config = KosDWMConfig()
    
    def __str__(self) -> str:
        """String representation."""
        return f"KosDWMConfig(active={self.config.active_button_bg}, " \
               f"inactive={self.config.inactive_button_bg}, " \
               f"layout={self.config.layout_mode})"
    
    def __repr__(self) -> str:
        """Detailed representation."""
        return f"KosDWMConfigParser(config={self.config.to_dict()})"


# Convenience functions

def parse_kosdwm_config(filepath: Union[str, Path]) -> KosDWMConfig:
    """
    Parse KosDWM config from file.
    
    Args:
        filepath: Path to config.json
        
    Returns:
        KosDWMConfig object
    """
    parser = KosDWMConfigParser()
    return parser.parse_file(filepath)


def create_default_config(filepath: Union[str, Path]):
    """
    Create a default KosDWM config file.
    
    Args:
        filepath: Path to create config at
    """
    parser = KosDWMConfigParser()
    parser.write_back(filepath)
