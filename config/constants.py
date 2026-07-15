"""Application constants for KosXER."""

import os

APP_NAME = "KosXER"
VERSION = "0.1.0"

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
        "theme": "default",
        "font_family": "monospace",
        "font_size": 10,
    },
    "files": {
        "recent_files": [],
        "max_recent": 10,
        "auto_reload": True,
    },
    "parsers": {
        "preserve_comments": True,
        "strict_mode": False,
    }
}

# File type associations
FILE_TYPES = {
    ".Xresources": "xresources",
    ".Xdefaults": "xresources",
    ".xrdb": "xresources",
    "menu.xml": "openbox_menu",
    "rc.xml": "keyvalue",
}
