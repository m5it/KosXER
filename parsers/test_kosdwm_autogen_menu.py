#!/usr/bin/env python3
"""
Test file for KosDWM Auto-Generative Menu Parser.

Run with: python3 parsers/test_kosdwm_autogen_menu.py
"""

import sys
import os
import tempfile
import shutil
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from parsers.kosdwm_autogen_menu_parser import (
    KosDWMAutoGenMenuParser,
    AutoGenMenuConfig,
    AutoGenMenuItem,
)


def create_test_menu_tree(base: str):
    """Create a small auto-generative menu tree for testing."""
    home = os.path.join(base, "Menus", "Home", "About")
    scripts = os.path.join(base, "Menus", "Scripts", "Test")

    os.makedirs(home, exist_ok=True)
    os.makedirs(scripts, exist_ok=True)

    # Home/About: static content menu
    with open(os.path.join(home, "config.json"), "w", encoding="utf-8") as f:
        f.write('''// About menu
{
    /* static content */
    "windowContent": "content.html"
}
''')
    with open(os.path.join(home, "content.html"), "w", encoding="utf-8") as f:
        f.write("<h1>About</h1>\n")
    with open(os.path.join(home, "ok.py"), "w", encoding="utf-8") as f:
        f.write("def run(window):\n    window.destroy()\n")

    # Scripts/Test: dynamic script menu
    with open(os.path.join(scripts, "config.json"), "w", encoding="utf-8") as f:
        f.write('''{
    "title": "Network",
    "windowScript": "echo hello",
    "loop": 5,
    "looptype": "second"
}
''')


def test_parse_real_directory():
    """Parse the real KosDWM Menus directory if available."""
    real_dir = os.path.expanduser("~/.config/KosDWM/Menus")
    if not os.path.isdir(real_dir):
        print("SKIP: real KosDWM Menus directory not found")
        return True

    print("=" * 60)
    print("TEST: Parse real KosDWM Menus directory")
    print("=" * 60)

    parser = KosDWMAutoGenMenuParser()
    items = parser.parse(real_dir)

    assert len(items) >= 3, f"Expected at least 3 items, got {len(items)}"
    print(f"Found {len(items)} auto-gen menu items:")
    for item in items:
        print(f"  - {item.name}: {item.config.to_dict()}")

    valid, errors = parser.validate()
    if not valid:
        print("Validation errors:")
        for err in errors:
            print(f"  {err}")
    assert valid, "Validation failed on real directory"

    print("  ✓ Real directory parsing passed")
    print()
    return True


def test_parse_and_write_back():
    """Parse a synthetic tree and write it back, preserving comments."""
    print("=" * 60)
    print("TEST: Parse and write-back roundtrip")
    print("=" * 60)

    with tempfile.TemporaryDirectory() as tmpdir:
        create_test_menu_tree(tmpdir)

        parser = KosDWMAutoGenMenuParser()
        items = parser.parse(os.path.join(tmpdir, "Menus"))

        assert len(items) == 2, f"Expected 2 items, got {len(items)}"

        about = parser.get_item("About")
        assert about is not None
        assert about.config.window_content == "content.html"
        assert about.content_body == "<h1>About</h1>\n"
        assert about.ok_script is not None

        script = parser.get_item("Test")
        assert script is not None
        assert script.config.title == "Network"
        assert script.config.window_script == "echo hello"
        assert script.config.loop == 5
        assert script.config.looptype == "second"

        # Write back to a new location
        output = os.path.join(tmpdir, "output")
        parser.write_back(output)

        # Verify files exist
        assert os.path.exists(os.path.join(output, "Home", "About", "config.json"))
        assert os.path.exists(os.path.join(output, "Home", "About", "content.html"))
        assert os.path.exists(os.path.join(output, "Home", "About", "ok.py"))
        assert os.path.exists(os.path.join(output, "Scripts", "Test", "config.json"))

        # Verify comments preserved in About config
        with open(os.path.join(output, "Home", "About", "config.json"), "r", encoding="utf-8") as f:
            text = f.read()
        assert "// About menu" in text, "Inline comment not preserved"
        assert "/* static content */" in text, "Block comment not preserved"

        # Verify JSON still parses
        with open(os.path.join(output, "Home", "About", "config.json"), "r", encoding="utf-8") as f:
            data = json.load(f)
        assert data["windowContent"] == "content.html"

        print("  ✓ Roundtrip with comment preservation passed")

    print()
    return True


def test_validation():
    """Test validation catches missing required fields."""
    print("=" * 60)
    print("TEST: Validation")
    print("=" * 60)

    cfg = AutoGenMenuConfig()
    errors = cfg.validate()
    assert len(errors) == 1
    assert "windowContent or windowScript" in errors[0]

    cfg = AutoGenMenuConfig(window_script="ls", loop=5)
    errors = cfg.validate()
    assert len(errors) == 1
    assert "looptype" in errors[0]

    cfg = AutoGenMenuConfig(window_script="ls", loop=5, looptype="minute")
    assert cfg.validate() == []

    print("  ✓ Validation passed")
    print()
    return True


def run_all_tests():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("KOSDWM AUTO-GENERATIVE MENU PARSER TEST SUITE")
    print("=" * 60 + "\n")

    tests = [
        test_parse_real_directory,
        test_parse_and_write_back,
        test_validation,
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
            print(f"  ✗ Test failed: {e}")
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
