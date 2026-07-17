#!/usr/bin/env python3
"""
Test file for KosDWM Config Parser

Run with: python parsers/test_kosdwm_config.py
"""

import sys
import os
import json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from parsers.kosdwm_config_parser import KosDWMConfigParser, KosDWMConfig


# Sample KosDWM config
SAMPLE_CONFIG = """{
    "active_button_bg": "#4a90d9",
    "inactive_button_bg": "#606060",
    "bar_height": 50,
    "button_height": 1,
    "combobox_ipady": 1,
    "layout_mode": "buttons"
}"""

# Config with custom colors
CUSTOM_COLORS_CONFIG = """{
    "active_button_bg": "#ff6b6b",
    "inactive_button_bg": "#2d3436",
    "bar_height": 60,
    "button_height": 2,
    "combobox_ipady": 2,
    "layout_mode": "comboboxes"
}"""

# Config with missing keys (should use defaults)
PARTIAL_CONFIG = """{
    "active_button_bg": "#00ff00",
    "bar_height": 75
}"""

# Invalid config (bad color)
INVALID_COLOR_CONFIG = """{
    "active_button_bg": "not-a-color",
    "inactive_button_bg": "#606060",
    "bar_height": 50,
    "button_height": 1,
    "combobox_ipady": 1,
    "layout_mode": "buttons"
}"""


def test_basic_parsing():
    """Test basic config parsing."""
    print("=" * 60)
    print("TEST 1: Basic Parsing")
    print("=" * 60)
    
    parser = KosDWMConfigParser()
    config = parser.parse(SAMPLE_CONFIG)
    
    print(f"Active button BG: {config.active_button_bg}")
    print(f"Inactive button BG: {config.inactive_button_bg}")
    print(f"Bar height: {config.bar_height}")
    print(f"Layout mode: {config.layout_mode}")
    
    assert config.active_button_bg == "#4a90d9"
    assert config.inactive_button_bg == "#606060"
    assert config.bar_height == 50
    assert config.layout_mode == "buttons"
    
    print("  ✓ Basic parsing works")
    print()
    return True


def test_partial_config():
    """Test parsing with missing keys."""
    print("=" * 60)
    print("TEST 2: Partial Config (Defaults)")
    print("=" * 60)
    
    parser = KosDWMConfigParser()
    config = parser.parse(PARTIAL_CONFIG)
    
    print(f"Active button BG (from config): {config.active_button_bg}")
    print(f"Inactive button BG (default): {config.inactive_button_bg}")
    print(f"Bar height (from config): {config.bar_height}")
    print(f"Button height (default): {config.button_height}")
    
    # These were in the config
    assert config.active_button_bg == "#00ff00"
    assert config.bar_height == 75
    
    # These should be defaults
    assert config.inactive_button_bg == "#606060"  # default
    assert config.button_height == 1  # default
    assert config.layout_mode == "buttons"  # default
    
    print("  ✓ Defaults applied correctly")
    print()
    return True


def test_custom_colors():
    """Test custom color configuration."""
    print("=" * 60)
    print("TEST 3: Custom Colors")
    print("=" * 60)
    
    parser = KosDWMConfigParser()
    config = parser.parse(CUSTOM_COLORS_CONFIG)
    
    print(f"Active button BG: {config.active_button_bg}")
    print(f"Inactive button BG: {config.inactive_button_bg}")
    print(f"Layout mode: {config.layout_mode}")
    
    assert config.active_button_bg == "#ff6b6b"
    assert config.inactive_button_bg == "#2d3436"
    assert config.layout_mode == "comboboxes"
    
    print("  ✓ Custom colors work")
    print()
    return True


def test_validation():
    """Test config validation."""
    print("=" * 60)
    print("TEST 4: Validation")
    print("=" * 60)
    
    # Valid config
    parser = KosDWMConfigParser()
    parser.parse(SAMPLE_CONFIG)
    is_valid, errors = parser.validate()
    
    print(f"Valid config check: {is_valid}")
    assert is_valid == True
    assert len(errors) == 0
    
    # Invalid color
    parser2 = KosDWMConfigParser()
    parser2.parse(INVALID_COLOR_CONFIG)
    is_valid, errors = parser2.validate()
    
    print(f"Invalid color check: {is_valid}, errors: {errors}")
    assert is_valid == False
    assert len(errors) > 0
    assert any("not-a-color" in error for error in errors)
    
    print("  ✓ Validation works")
    print()
    return True


def test_write_back():
    """Test write back functionality."""
    print("=" * 60)
    print("TEST 5: Write Back")
    print("=" * 60)
    
    parser = KosDWMConfigParser()
    parser.parse(CUSTOM_COLORS_CONFIG)
    
    # Modify a value
    parser.update_value("bar_height", 100)
    
    # Generate output
    output = parser.write_back()
    print("Generated JSON:")
    print(output)
    
    # Parse the output to verify it's valid JSON
    data = json.loads(output)
    assert data["bar_height"] == 100
    assert data["active_button_bg"] == "#ff6b6b"
    
    print("  ✓ Write back produces valid JSON")
    print()
    return True


def test_color_preview():
    """Test color preview functionality."""
    print("=" * 60)
    print("TEST 6: Color Preview")
    print("=" * 60)
    
    parser = KosDWMConfigParser()
    parser.parse(SAMPLE_CONFIG)
    
    active_color = parser.get_color_preview('active_button_bg')
    inactive_color = parser.get_color_preview('inactive_button_bg')
    unknown = parser.get_color_preview('unknown')
    
    print(f"Active color: {active_color}")
    print(f"Inactive color: {inactive_color}")
    print(f"Unknown color: {unknown}")
    
    assert active_color == "#4a90d9"
    assert inactive_color == "#606060"
    assert unknown is None
    
    print("  ✓ Color preview works")
    print()
    return True


def test_dataclass():
    """Test KosDWMConfig dataclass."""
    print("=" * 60)
    print("TEST 7: Config Dataclass")
    print("=" * 60)
    
    # Create with defaults
    config1 = KosDWMConfig()
    print(f"Default config: {config1}")
    
    # Create with custom values
    config2 = KosDWMConfig(
        active_button_bg="#ff0000",
        bar_height=100,
        layout_mode="comboboxes"
    )
    print(f"Custom config: {config2}")
    
    # Test to_dict
    data = config2.to_dict()
    print(f"As dict: {data}")
    
    assert data["active_button_bg"] == "#ff0000"
    assert data["bar_height"] == 100
    
    # Test from_dict
    config3 = KosDWMConfig.from_dict({
        "active_button_bg": "#00ff00",
        "missing_key": "ignored"
    })
    print(f"From partial dict: {config3}")
    
    assert config3.active_button_bg == "#00ff00"
    assert config3.bar_height == 50  # default
    
    print("  ✓ Dataclass works correctly")
    print()
    return True


def run_all_tests():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("KOSDWM CONFIG PARSER TEST SUITE")
    print("=" * 60 + "\n")
    
    tests = [
        test_basic_parsing,
        test_partial_config,
        test_custom_colors,
        test_validation,
        test_write_back,
        test_color_preview,
        test_dataclass,
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
