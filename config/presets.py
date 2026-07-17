#!/usr/bin/env python3
"""
Presets Database for KosXER

Provides known/common values for XResources and other configuration formats.
Includes standard terminal colors, fonts, boolean values, xterm-specific presets,
and user-defined custom presets.
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Union, Optional


# =============================================================================
# USER PRESETS CONFIGURATION
# =============================================================================

USER_PRESETS_FILE = Path.home() / ".config" / "kosxer" / "user_presets.json"


def ensure_user_presets_dir():
    """Ensure the user presets directory exists."""
    USER_PRESETS_FILE.parent.mkdir(parents=True, exist_ok=True)


# =============================================================================
# STANDARD TERMINAL COLORS (16-color palette)
# =============================================================================

XTERM_COLORS = {
    # Standard colors
    'black': '#000000',
    'red': '#ff0000',
    'green': '#00ff00',
    'yellow': '#ffff00',
    'blue': '#0000ff',
    'magenta': '#ff00ff',
    'cyan': '#00ffff',
    'white': '#ffffff',
    
    # Bright colors
    'bright_black': '#808080',
    'bright_red': '#ff5555',
    'bright_green': '#55ff55',
    'bright_yellow': '#ffff55',
    'bright_blue': '#5555ff',
    'bright_magenta': '#ff55ff',
    'bright_cyan': '#55ffff',
    'bright_white': '#ffffff',
    
    # Color indices (color0 - color15)
    'color0': '#000000',   # Black
    'color1': '#ff0000',   # Red
    'color2': '#00ff00',   # Green
    'color3': '#ffff00',   # Yellow
    'color4': '#0000ff',   # Blue
    'color5': '#ff00ff',   # Magenta
    'color6': '#00ffff',   # Cyan
    'color7': '#ffffff',   # White
    'color8': '#808080',   # Bright Black
    'color9': '#ff5555',   # Bright Red
    'color10': '#55ff55',  # Bright Green
    'color11': '#ffff55',  # Bright Yellow
    'color12': '#5555ff',  # Bright Blue
    'color13': '#ff55ff',  # Bright Magenta
    'color14': '#55ffff',  # Bright Cyan
    'color15': '#ffffff',  # Bright White
}

# =============================================================================
# COMMON FONTS
# =============================================================================

COMMON_FONTS = [
    # XFT fonts (modern)
    'xft:Monospace:size=10',
    'xft:Monospace:size=12',
    'xft:Monospace:size=14',
    'xft:DejaVu Sans Mono:size=10',
    'xft:DejaVu Sans Mono:size=12',
    'xft:Source Code Pro:size=10',
    'xft:Source Code Pro:size=12',
    'xft:Hack:size=10',
    'xft:Hack:size=12',
    'xft:JetBrains Mono:size=10',
    'xft:JetBrains Mono:size=12',
    'xft:Fira Code:size=10',
    'xft:Fira Code:size=12',
    'xft:Ubuntu Mono:size=12',
    'xft:Ubuntu Mono:size=14',
    
    # X11 core fonts (legacy)
    '-*-courier-medium-r-*-*-*-120-*-*-*-*-*-*',
    '-*-courier-bold-r-*-*-*-120-*-*-*-*-*-*',
    '-*-courier-medium-r-*-*-*-140-*-*-*-*-*-*',
    '-*-fixed-medium-r-*-*-*-120-*-*-*-*-*-*',
    '-*-terminus-medium-r-*-*-*-120-*-*-*-*-*-*',
    '-*-terminus-bold-r-*-*-*-120-*-*-*-*-*-*',
    '-*-terminus-medium-r-*-*-*-140-*-*-*-*-*-*',
    '-*-terminus-bold-r-*-*-*-140-*-*-*-*-*-*',
    '6x13',
    '7x13',
    '8x13',
    '9x15',
    '10x20',
    '12x24',
]

# =============================================================================
# BOOLEAN VALUES
# =============================================================================

BOOLEAN_VALUES = {
    'true': ['true', 'True', 'TRUE', 'on', 'On', 'ON', 'yes', 'Yes', 'YES', '1'],
    'false': ['false', 'False', 'FALSE', 'off', 'Off', 'OFF', 'no', 'No', 'NO', '0'],
}

# Flattened list for UI
ALL_BOOLEAN_VALUES = BOOLEAN_VALUES['true'] + BOOLEAN_VALUES['false']

# =============================================================================
# XTERM SPECIFIC RESOURCES
# =============================================================================

XTERM_SPECIFIC = {
    # Background/Foreground
    '*background': list(XTERM_COLORS.values()),
    '*foreground': list(XTERM_COLORS.values()),
    'XTerm*background': list(XTERM_COLORS.values()),
    'XTerm*foreground': list(XTERM_COLORS.values()),
    'XTerm*cursorColor': list(XTERM_COLORS.values()),
    
    # Fonts
    '*font': COMMON_FONTS,
    'XTerm*font': COMMON_FONTS,
    'XTerm*faceName': [
        'Monospace',
        'DejaVu Sans Mono',
        'Source Code Pro',
        'Hack',
        'JetBrains Mono',
        'Fira Code',
        'Ubuntu Mono',
    ],
    
    # Boolean settings
    'XTerm*loginShell': ALL_BOOLEAN_VALUES,
    'XTerm*reverseVideo': ALL_BOOLEAN_VALUES,
    'XTerm*scrollBar': ALL_BOOLEAN_VALUES,
    'XTerm*scrollTtyOutput': ALL_BOOLEAN_VALUES,
    'XTerm*scrollKey': ALL_BOOLEAN_VALUES,
    'XTerm*saveLines': ['1000', '2500', '5000', '10000', '25000'],
    'XTerm*visualBell': ALL_BOOLEAN_VALUES,
    'XTerm*allowBoldFonts': ALL_BOOLEAN_VALUES,
    'XTerm*allowColorOps': ALL_BOOLEAN_VALUES,
    'XTerm*allowFontOps': ALL_BOOLEAN_VALUES,
    'XTerm*allowTcapOps': ALL_BOOLEAN_VALUES,
    'XTerm*allowTitleOps': ALL_BOOLEAN_VALUES,
    'XTerm*allowWindowOps': ALL_BOOLEAN_VALUES,
    
    # Cursor
    'XTerm*cursorBlink': ALL_BOOLEAN_VALUES,
    'XTerm*cursorUnderLine': ALL_BOOLEAN_VALUES,
    
    # Geometry
    'XTerm*geometry': ['80x24', '80x25', '80x40', '80x50', '120x40', '120x50'],
    
    # Translations/Key bindings
    'XTerm*translations': [
        '#override\\n<Ctrl>Shift<C>:copy-selection(CLIPBOARD)\\n<Ctrl>Shift<V>:insert-selection(CLIPBOARD)',
        '#override\\n<Ctrl>C:copy-selection(CLIPBOARD)\\n<Ctrl>V:insert-selection(CLIPBOARD)',
    ],
}

# =============================================================================
# USER CUSTOM PRESETS FUNCTIONS
# =============================================================================

def load_user_presets() -> Dict[str, str]:
    """
    Load user-defined custom presets from file.
    
    Returns:
        Dictionary of user preset name -> value
    """
    if not USER_PRESETS_FILE.exists():
        return {}
    
    try:
        with open(USER_PRESETS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}


def save_user_presets(presets: Dict[str, str]):
    """
    Save user-defined custom presets to file.
    
    Args:
        presets: Dictionary of preset name -> value
    """
    ensure_user_presets_dir()
    
    try:
        with open(USER_PRESETS_FILE, 'w', encoding='utf-8') as f:
            json.dump(presets, f, indent=2)
    except IOError as e:
        print(f"Error saving user presets: {e}")


def add_user_preset(name: str, value: str) -> bool:
    """
    Add a new user preset.
    
    Args:
        name: Preset name (display name)
        value: Preset value
    
    Returns:
        True if added successfully, False otherwise
    """
    if not name or not value:
        return False
    
    presets = load_user_presets()
    presets[name] = value
    save_user_presets(presets)
    return True


def delete_user_preset(name: str) -> bool:
    """
    Delete a user preset.
    
    Args:
        name: Preset name to delete
    
    Returns:
        True if deleted, False if not found
    """
    presets = load_user_presets()
    if name in presets:
        del presets[name]
        save_user_presets(presets)
        return True
    return False


def get_user_presets_list() -> List[tuple]:
    """
    Get user presets as list of tuples for UI.
    
    Returns:
        List of (name, value) tuples
    """
    presets = load_user_presets()
    return list(presets.items())


# =============================================================================
# GENERIC PRESETS BY TYPE
# =============================================================================

PRESETS_BY_TYPE = {
    'color': {
        'name': 'Colors',
        'values': list(XTERM_COLORS.items()),
        'description': 'Standard terminal colors (color0-color15)',
    },
    'font': {
        'name': 'Fonts',
        'values': [(f, f) for f in COMMON_FONTS],
        'description': 'Common monospace fonts for terminals',
    },
    'boolean': {
        'name': 'Booleans',
        'values': [(v, v) for v in ALL_BOOLEAN_VALUES],
        'description': 'True/False values',
    },
    'number': {
        'name': 'Numbers',
        'values': [('0', '0'), ('1', '1'), ('8', '8'), ('10', '10'), ('12', '12'), 
                   ('16', '16'), ('24', '24'), ('100', '100'), ('1000', '1000')],
        'description': 'Common numeric values',
    },
}

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_presets_for_resource(resource_name: str) -> Optional[Dict]:
    """
    Get appropriate presets for a given resource name.
    
    Args:
        resource_name: The resource path (e.g., 'XTerm*background', '*.color0')
    
    Returns:
        Dictionary with presets or None if no specific presets found
    """
    if not resource_name:
        return None
    
    name_lower = resource_name.lower()
    
    # Check XTERM_SPECIFIC first
    if resource_name in XTERM_SPECIFIC:
        values = XTERM_SPECIFIC[resource_name]
        return {
            'type': 'specific',
            'name': resource_name,
            'values': values,
            'description': f'Specific values for {resource_name}',
        }
    
    # Detect by pattern
    if 'color' in name_lower or name_lower.endswith('ground'):
        return PRESETS_BY_TYPE['color']
    
    if 'font' in name_lower or 'face' in name_lower:
        return PRESETS_BY_TYPE['font']
    
    if any(b in name_lower for b in ['shell', 'video', 'scroll', 'bell', 'bold', 'allow', 'blink']):
        return PRESETS_BY_TYPE['boolean']
    
    return None


def get_color_name(hex_value: str) -> Optional[str]:
    """
    Get color name from hex value.
    
    Args:
        hex_value: Hex color code (e.g., '#ffffff')
    
    Returns:
        Color name if found, None otherwise
    """
    hex_clean = hex_value.lower().lstrip('#')
    hex_formatted = f'#{hex_clean}'
    
    for name, value in XTERM_COLORS.items():
        if value.lower() == hex_formatted.lower():
            return name
    return None


def normalize_boolean(value: str) -> Optional[bool]:
    """
    Normalize a boolean string to Python bool.
    
    Args:
        value: String value to check
    
    Returns:
        True/False if recognized boolean, None otherwise
    """
    val_lower = value.lower()
    if val_lower in [v.lower() for v in BOOLEAN_VALUES['true']]:
        return True
    if val_lower in [v.lower() for v in BOOLEAN_VALUES['false']]:
        return False
    return None


def get_all_presets() -> Dict[str, Dict]:
    """
    Get all available presets organized by category.
    
    Returns:
        Dictionary of all preset categories including user presets
    """
    presets = {
        'colors': {
            'name': 'Terminal Colors',
            'icon': '🎨',
            'items': list(XTERM_COLORS.items()),
        },
        'fonts': {
            'name': 'Fonts',
            'icon': '🔤',
            'items': [(f, f) for f in COMMON_FONTS],
        },
        'booleans': {
            'name': 'Booleans',
            'icon': '☑️',
            'items': [(v, v) for v in ALL_BOOLEAN_VALUES],
        },
        'xterm': {
            'name': 'XTerm Specific',
            'icon': '💻',
            'items': [(k, ', '.join(v[:3]) + '...' if isinstance(v, list) else str(v)) 
                     for k, v in list(XTERM_SPECIFIC.items())[:20]],
        },
    }
    
    # Add user presets if any exist
    user_presets = get_user_presets_list()
    if user_presets:
        presets['user'] = {
            'name': 'My Presets',
            'icon': '⭐',
            'items': user_presets,
        }
    
    return presets


# =============================================================================
# MODULE TEST
# =============================================================================

if __name__ == '__main__':
    print("KosXER Presets Database")
    print("=" * 50)
    
    print("\n--- XTerm Colors (first 8) ---")
    for i in range(8):
        name = f'color{i}'
        print(f"  {name}: {XTERM_COLORS[name]}")
    
    print("\n--- White Colors ---")
    whites = [k for k in XTERM_COLORS.keys() if 'white' in k.lower() or k == 'color7' or k == 'color15']
    for w in whites:
        print(f"  {w}: {XTERM_COLORS[w]}")
    
    print("\n--- Common Fonts (first 5) ---")
    for font in COMMON_FONTS[:5]:
        print(f"  {font}")
    
    print("\n--- Presets for XTerm*background ---")
    presets = get_presets_for_resource('XTerm*background')
    if presets:
        print(f"  Type: {presets['name']}")
        print(f"  Values: {len(presets['values'])} colors available")
    
    print("\n--- Get color name ---")
    print(f"  #ffffff -> {get_color_name('#ffffff')}")
    print(f"  #ff0000 -> {get_color_name('#ff0000')}")
    
    print("\n--- User Presets ---")
    user = load_user_presets()
    if user:
        for name, value in user.items():
            print(f"  {name}: {value}")
    else:
        print("  No user presets saved yet.")
        print(f"  Save location: {USER_PRESETS_FILE}")
