#!/usr/bin/env python3
"""
Test file for OpenBox Parser

Contains sample OpenBox menu.xml and rc.xml data to verify parsing.
Run with: python parsers/test_openbox.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from parsers.openbox_parser import OpenBoxMenuParser, OpenBoxRCParser, OpenBoxMenu, OpenBoxMenuItem


# Sample OpenBox menu.xml content
SAMPLE_MENU_XML = """<?xml version="1.0" encoding="UTF-8"?>
<openbox_menu xmlns="http://openbox.org/3.4/menu">
    <menu id="root-menu" label="Openbox 3">
        <item label="Terminal">
            <action name="Execute">
                <command>xterm</command>
            </action>
        </item>
        <item label="Web Browser">
            <action name="Execute">
                <command>firefox</command>
            </action>
        </item>
        <separator/>
        <menu id="preferences-menu" label="Preferences">
            <item label="Openbox Configuration">
                <action name="Execute">
                    <command>obconf</command>
                </action>
            </item>
            <item label="Tint2 Panel">
                <action name="Execute">
                    <command>tint2conf</command>
                </action>
            </item>
        </menu>
        <separator/>
        <item label="Exit">
            <action name="Exit"/>
        </item>
    </menu>
</openbox_menu>
"""

# Sample OpenBox rc.xml content (truncated)
SAMPLE_RC_XML = """<?xml version="1.0" encoding="UTF-8"?>
<openbox_config xmlns="http://openbox.org/3.4/rc">
    <theme>
        <name>Clearlooks</name>
        <titleLayout>NLIMC</titleLayout>
        <animateIconify>yes</animateIconify>
    </theme>
    <desktops>
        <number>4</number>
        <firstdesk>1</firstdesk>
        <names>
            <name>Desktop 1</name>
            <name>Desktop 2</name>
            <name>Desktop 3</name>
            <name>Desktop 4</name>
        </names>
        <popupTime>875</popupTime>
    </desktops>
    <resize>
        <drawContents>yes</drawContents>
        <popupShow>Nonpixel</popupShow>
        <popupPosition>Center</popupPosition>
    </resize>
    <focus>
        <focusNew>yes</focusNew>
        <followMouse>no</followMouse>
        <focusLast>yes</focusLast>
        <underMouse>no</underMouse>
    </focus>
    <keyboard>
        <chainQuitKey>C-g</chainQuitKey>
        <keybind key="C-A-t">
            <action name="Execute">
                <command>xterm</command>
            </action>
        </keybind>
        <keybind key="C-A-f">
            <action name="Execute">
                <command>firefox</command>
            </action>
        </keybind>
        <keybind key="A-F4">
            <action name="Close"/>
        </keybind>
    </keyboard>
</openbox_config>
"""


def test_menu_parsing():
    """Test menu.xml parsing."""
    print("=" * 60)
    print("TEST 1: Menu.xml Parsing")
    print("=" * 60)
    
    parser = OpenBoxMenuParser()
    root_menu = parser.parse(SAMPLE_MENU_XML)
    
    print(f"Root menu: {root_menu.label} (ID: {root_menu.id})")
    print(f"Total menus: {len(parser)}")
    print(f"Total items: {len(parser.items)}")
    print()
    
    # Print tree structure
    print("Menu structure:")
    print(parser.get_menu_tree())
    print()
    
    assert root_menu.label == "Openbox 3"
    assert len(root_menu.items) == 5  # 2 items + 1 separator + 1 submenu + 1 separator + 1 item
    
    print("  ✓ Menu parsing works")
    return True


def test_rc_parsing():
    """Test rc.xml parsing."""
    print("=" * 60)
    print("TEST 2: rc.xml Parsing")
    print("=" * 60)
    
    parser = OpenBoxRCParser()
    config = parser.parse(SAMPLE_RC_XML)
    
    print(f"Theme: {config.get('theme', {}).get('name', 'N/A')}")
    print(f"Desktops: {config.get('desktops', {}).get('number', 'N/A')}")
    print(f"Keybindings: {len(parser.keybindings)}")
    print()
    
    # Print keybindings
    print("Keybindings:")
    for kb in parser.keybindings:
        actions = ', '.join([a['name'] for a in kb['actions']])
        print(f"  {kb['key']}: {actions}")
    print()
    
    assert config['theme']['name'] == 'Clearlooks'
    assert config['desktops']['number'] == '4'
    assert len(parser.keybindings) == 3
    
    print("  ✓ rc.xml parsing works")
    return True


def test_menu_modification():
    """Test menu modification."""
    print("=" * 60)
    print("TEST 3: Menu Modification")
    print("=" * 60)
    
    parser = OpenBoxMenuParser()
    parser.parse(SAMPLE_MENU_XML)
    
    # Add a new item
    new_item = OpenBoxMenuItem(
        id="new-item",
        label="New Application",
        action="Execute",
        action_params={'command': 'newapp'},
        icon='application.png'
    )
    
    success = parser.add_item("root-menu", new_item)
    print(f"Added new item: {success}")
    
    # Verify
    root = parser.root_menu
    item_labels = []
    for item in root.items:
        if isinstance(item, OpenBoxMenuItem):
            item_labels.append(item.label)
    
    print(f"Items in root menu: {item_labels}")
    assert "New Application" in item_labels
    
    print("  ✓ Menu modification works")
    return True


def test_write_back():
    """Test writing back to XML."""
    print("=" * 60)
    print("TEST 4: Write Back")
    print("=" * 60)
    
    parser = OpenBoxMenuParser()
    parser.parse(SAMPLE_MENU_XML)
    
    # Generate XML
    output = parser.write_back(pretty=True)
    
    print("Generated XML (first 30 lines):")
    lines = output.split('\n')[:30]
    for line in lines:
        print(f"  {line}")
    
    # Verify it contains expected elements
    assert '<openbox_menu' in output
    assert 'root-menu' in output
    assert 'Terminal' in output
    
    print("  ✓ Write back works")
    return True


def run_all_tests():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("OPENBOX PARSER TEST SUITE")
    print("=" * 60 + "\n")
    
    tests = [
        test_menu_parsing,
        test_rc_parsing,
        test_menu_modification,
        test_write_back,
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
