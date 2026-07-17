#!/usr/bin/env python3
"""
Test file for KosDWM Menu Parser

Run with: python parsers/test_kosdwm_menu.py
"""

import sys
import os
import tempfile
import shutil
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from parsers.kosdwm_menu_parser import KosDWMMenuParser, MenuItem, MenuFolder


# Sample menu structure to create for testing
SAMPLE_MENU_STRUCTURE = {
    "Applications": {
        "config.json": {
            "label": "Applications",
            "icon": "applications.png",
            "description": "Application menu"
        },
        "items": {
            "firefox.py": '''#!/usr/bin/env python3
"""
Firefox Web Browser

Launch Firefox browser
"""

LABEL = "Firefox"
ICON = "firefox.png"
DESCRIPTION = "Web browser"

import subprocess

def main():
    subprocess.run(["firefox"])

if __name__ == "__main__":
    main()
''',
            "terminal.py": '''#!/usr/bin/env python3
"""
Terminal

Launch terminal emulator
"""

LABEL = "Terminal"
ICON = "terminal.png"

import subprocess

def main():
    subprocess.run(["xterm"])

if __name__ == "__main__":
    main()
'''
        }
    },
    "System": {
        "config.json": {
            "label": "System",
            "icon": "system.png"
        },
        "items": {
            "settings.py": '''#!/usr/bin/env python3
"""
Settings

System settings
"""

LABEL = "Settings"
ICON = "settings.png"

def main():
    print("Opening settings...")

if __name__ == "__main__":
    main()
''',
            "Submenu": {
                "config.json": {
                    "label": "Tools",
                    "icon": "tools.png"
                },
                "items": {
                    "calculator.py": '''#!/usr/bin/env python3
"""
Calculator

Calculator application
"""

LABEL = "Calculator"

def main():
    print("Calculator")

if __name__ == "__main__":
    main()
'''
                }
            }
        }
    }
}


def create_test_menu_structure(base_path: str, structure: dict):
    """Create test menu folder structure."""
    for name, content in structure.items():
        item_path = os.path.join(base_path, name)
        
        if isinstance(content, dict):
            if "items" in content:
                # It's a menu folder
                os.makedirs(item_path, exist_ok=True)
                
                # Create config.json
                config = content.get("config.json", {"label": name})
                with open(os.path.join(item_path, "config.json"), 'w') as f:
                    import json
                    json.dump(config, f, indent=2)
                
                # Create items
                create_test_menu_structure(item_path, content["items"])
            else:
                # It's a regular folder
                os.makedirs(item_path, exist_ok=True)
                create_test_menu_structure(item_path, content)


def test_basic_parsing():
    """Test basic menu parsing."""
    print("=" * 60)
    print("TEST 1: Basic Menu Parsing")
    print("=" * 60)
    
    # Create temporary test structure
    with tempfile.TemporaryDirectory() as tmpdir:
        create_test_menu_structure(tmpdir, SAMPLE_MENU_STRUCTURE)
        
        parser = KosDWMMenuParser()
        root = parser.parse(tmpdir)
        
        print(f"Root menu: {root.label}")
        print(f"Number of top-level menus: {len(root.items)}")
        
        for item in root.items:
            if isinstance(item, MenuFolder):
                print(f"  [Menu] {item.label} ({len(item.items)} items)")
        
        assert len(root.items) == 2  # Applications and System
        assert isinstance(root.items[0], MenuFolder)
        
        print("  ✓ Basic parsing works")
    
    print()
    return True


def test_menu_hierarchy():
    """Test nested menu hierarchy."""
    print("=" * 60)
    print("TEST 2: Menu Hierarchy")
    print("=" * 60)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        create_test_menu_structure(tmpdir, SAMPLE_MENU_STRUCTURE)
        
        parser = KosDWMMenuParser()
        root = parser.parse(tmpdir)
        
        # Find System menu
        system_menu = None
        for item in root.items:
            if isinstance(item, MenuFolder) and item.name == "System":
                system_menu = item
                break
        
        assert system_menu is not None
        print(f"System menu found: {system_menu.label}")
        
        # Check for submenu
        tools_submenu = None
        for item in system_menu.items:
            if isinstance(item, MenuFolder):
                tools_submenu = item
                print(f"  Submenu: {item.label} ({len(item.items)} items)")
        
        assert tools_submenu is not None
        assert tools_submenu.name == "Submenu"
        
        print("  ✓ Hierarchy parsing works")
    
    print()
    return True


def test_script_parsing():
    """Test Python script parsing."""
    print("=" * 60)
    print("TEST 3: Script Parsing")
    print("=" * 60)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        create_test_menu_structure(tmpdir, SAMPLE_MENU_STRUCTURE)
        
        parser = KosDWMMenuParser()
        parser.parse(tmpdir)
        
        # Check parsed items
        firefox = parser.get_item("firefox")
        assert firefox is not None
        print(f"Firefox item: {firefox.label}")
        print(f"  Icon: {firefox.icon}")
        print(f"  Description: {firefox.description}")
        
        terminal = parser.get_item("terminal")
        assert terminal is not None
        print(f"Terminal item: {terminal.label}")
        
        assert firefox.label == "Firefox"
        assert firefox.icon == "firefox.png"
        assert "Web browser" in (firefox.description or "")
        
        print("  ✓ Script parsing works")
    
    print()
    return True


def test_menu_tree():
    """Test menu tree visualization."""
    print("=" * 60)
    print("TEST 4: Menu Tree")
    print("=" * 60)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        create_test_menu_structure(tmpdir, SAMPLE_MENU_STRUCTURE)
        
        parser = KosDWMMenuParser()
        parser.parse(tmpdir)
        
        tree = parser.get_menu_tree()
        print("Menu tree:")
        print(tree)
        
        assert "Applications" in tree
        assert "Firefox" in tree
        assert "System" in tree
        
        print("  ✓ Menu tree generation works")
    
    print()
    return True


def test_write_back():
    """Test write back functionality."""
    print("=" * 60)
    print("TEST 5: Write Back")
    print("=" * 60)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Parse existing structure
        create_test_menu_structure(tmpdir, SAMPLE_MENU_STRUCTURE)
        parser = KosDWMMenuParser()
        parser.parse(tmpdir)
        
        # Write to new location
        output_dir = os.path.join(tmpdir, "output")
        result = parser.write_back(output_dir)
        
        print(f"Written to: {result}")
        
        # Verify structure exists
        assert os.path.exists(output_dir)
        assert os.path.exists(os.path.join(output_dir, "config.json"))
        assert os.path.exists(os.path.join(output_dir, "Applications"))
        
        print("  ✓ Write back works")
    
    print()
    return True


def test_add_remove_items():
    """Test adding and removing items."""
    print("=" * 60)
    print("TEST 6: Add/Remove Items")
    print("=" * 60)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        create_test_menu_structure(tmpdir, SAMPLE_MENU_STRUCTURE)
        parser = KosDWMMenuParser()
        parser.parse(tmpdir)
        
        # Add new item
        new_item = MenuItem(
            name="newapp",
            label="New Application",
            script_path="/tmp/newapp.py",
            icon="newapp.png"
        )
        
        result = parser.add_menu_item("Applications", new_item)
        assert result == True
        print(f"Added item: {new_item.label}")
        
        # Verify it was added
        apps_folder = parser.get_folder("Applications")
        assert any(i.name == "newapp" for i in apps_folder.items if isinstance(i, MenuItem))
        
        # Remove item
        result = parser.remove_menu_item("firefox")
        assert result == True
        print("Removed firefox item")
        
        # Verify it was removed
        assert parser.get_item("firefox") is None
        
        print("  ✓ Add/Remove works")
    
    print()
    return True


def run_all_tests():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("KOSDWM MENU PARSER TEST SUITE")
    print("=" * 60 + "\n")
    
    tests = [
        test_basic_parsing,
        test_menu_hierarchy,
        test_script_parsing,
        test_menu_tree,
        test_write_back,
        test_add_remove_items,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"  ✗ Test failed with exception: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
            print()
    
    print("=" * 60)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("=" * 60)
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
