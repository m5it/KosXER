"""Application constants for KosXER."""

import os
import sys
from pathlib import Path

# Import version from AUTOVERSION (single source of truth)
sys.path.insert(0, str(Path(__file__).parent.parent))
from AUTOVERSION import VERSION

APP_NAME = "KosXER"
# VERSION imported from AUTOVERSION

# Default configuration paths
HOME_DIR = os.path.expanduser("~")
CONFIG_DIR = os.path.join(HOME_DIR, ".config", "kosxer")
BACKUP_DIR = os.path.join(CONFIG_DIR, "backups")

# Ensure directories exist
os.makedirs(CONFIG_DIR, exist_ok=True)
os.makedirs(BACKUP_DIR, exist_ok=True)

DEFAULT_CONFIG = {
    "editor": {
        "auto_backup": True,
        "backup_count": 5,
        "show_line_numbers": True,
        "theme": "dark"
    },
    "file_browser": {
        "show_hidden": False,
        "follow_symlinks": True
    }
}

# Supported file types
SUPPORTED_EXTENSIONS = [
    '.Xresources',
    '.Xdefaults', 
    '.xml',
    '.conf',
    '.rc',
    '.cfg',
    '.env',
    '.json'
]

# UI Constants
WINDOW_MIN_WIDTH = 800
WINDOW_MIN_HEIGHT = 600
DEFAULT_WINDOW_WIDTH = 1400
DEFAULT_WINDOW_HEIGHT = 900
