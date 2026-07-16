#!/usr/bin/env python3
"""
Quick import test for KosXER
Run this to check if all modules import correctly.
"""

import sys
from pathlib import Path

def test_imports():
    """Test all imports."""
    errors = []
    
    print("Testing KosXER imports...")
    print("=" * 50)
    
    # Test config
    try:
        from config.constants import APP_NAME, VERSION
        print(f"✓ config.constants: {APP_NAME} v{VERSION}")
    except Exception as e:
        errors.append(f"config.constants: {e}")
        print(f"✗ config.constants: {e}")
    
    try:
        from config.settings import Settings
        print("✓ config.settings")
    except Exception as e:
        errors.append(f"config.settings: {e}")
        print(f"✗ config.settings: {e}")
    
    # Test parsers
    try:
        from parsers import XResourcesParser, OpenBoxMenuParser, GenericKVParser
        print("✓ parsers")
    except Exception as e:
        errors.append(f"parsers: {e}")
        print(f"✗ parsers: {e}")
    
    # Test utils
    try:
        from utils.backup import BackupManager
        from utils.validation import ValidationManager
        print("✓ utils")
    except Exception as e:
        errors.append(f"utils: {e}")
        print(f"✗ utils: {e}")
    
    # Test GUI
    try:
        from gui.editor_base import EditorWidget
        print("✓ gui.editor_base (EditorWidget)")
    except Exception as e:
        errors.append(f"gui.editor_base: {e}")
        print(f"✗ gui.editor_base: {e}")
    
    try:
        from gui.file_browser import FileBrowser
        print("✓ gui.file_browser")
    except Exception as e:
        errors.append(f"gui.file_browser: {e}")
        print(f"✗ gui.file_browser: {e}")
    
    try:
        from gui.xresources_editor import XResourcesEditor
        print("✓ gui.xresources_editor")
    except Exception as e:
        errors.append(f"gui.xresources_editor: {e}")
        print(f"✗ gui.xresources_editor: {e}")
    
    try:
        from gui.openbox_editor import OpenBoxEditor
        print("✓ gui.openbox_editor")
    except Exception as e:
        errors.append(f"gui.openbox_editor: {e}")
        print(f"✗ gui.openbox_editor: {e}")
    
    try:
        from gui.kv_editor import KVEditor
        print("✓ gui.kv_editor")
    except Exception as e:
        errors.append(f"gui.kv_editor: {e}")
        print(f"✗ gui.kv_editor: {e}")
    
    print("=" * 50)
    
    if errors:
        print(f"\n✗ {len(errors)} import errors found:")
        for error in errors:
            print(f"  - {error}")
        return 1
    else:
        print("\n✓ All imports successful!")
        print("\nYou can now run: python main.py")
        return 0

if __name__ == "__main__":
    sys.exit(test_imports())
