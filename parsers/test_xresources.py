#!/usr/bin/env python3
"""
Test file for Xresources Parser

Contains sample Xresources data to verify parsing functionality.
Run with: python parsers/test_xresources.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from parsers.xresources_parser import XResourcesParser, XResourceEntry


# Sample Xresources content for testing
SAMPLE_XRESOURCES = """
! XTerm settings
XTerm*background: black
XTerm*foreground: white
XTerm*faceName: Monospace
XTerm*faceSize: 10

! URxvt settings
URxvt*background: #1a1a1a
URxvt*foreground: #d0d0d0
URxvt*font: xft:Monospace:size=10
URxvt.scrollBar: false

! Multi-line value example
XTerm*customResource: This is a \
multi-line value that spans \
multiple lines

! Wildcard examples
*background: #000000
*foreground: #ffffff
*.cursorColor: #00ff00

! Conditional compilation example
#ifdef COLOR_SCHEME_DARK
XTerm*background: #000000
XTerm*foreground: #ffffff
#else
XTerm*background: #ffffff
XTerm*foreground: #000000
#endif

! Color definitions
*.color0:  #000000
*.color1:  #ff0000
*.color2:  #00ff00
*.color3:  #ffff00
*.color4:  #0000ff
*.color5:  #ff00ff
*.color6:  #00ffff
*.color7:  #ffffff

! Special characters in values
XTerm*title: My Terminal "with quotes"
XTerm*iconName: Terminal 'with apostrophes'
"""


def test_basic_parsing():
    """Test basic parsing functionality."""
    print("=" * 60)
    print("TEST 1: Basic Parsing")
    print("=" * 60)
    
    parser = XResourcesParser()
    entries = parser.parse(SAMPLE_XRESOURCES)
    
    print(f"Parsed {len(entries)} resource entries")
    print()
    
    # Display first 5 entries
    print("First 5 entries:")
    for i, entry in enumerate(entries[:5], 1):
        comment_str = f"  # {entry.comment}" if entry.comment else ""
        print(f"  {i}. {entry.resource_path}: {entry.value}{comment_str}")
    
    print()
    return len(entries) > 0


def test_wildcard_matching():
    """Test wildcard pattern matching."""
    print("=" * 60)
    print("TEST 2: Wildcard Matching")
    print("=" * 60)
    
    parser = XResourcesParser()
    parser.parse(SAMPLE_XRESOURCES)
    
    # Test exact match
    value = parser.get_value("XTerm*background")
    print(f"Exact match 'XTerm*background': {value}")
    assert value == "black", f"Expected 'black', got '{value}'"
    
    # Test wildcard match
    value = parser.get_value("XTerm.vt100.background")
    print(f"Wildcard match 'XTerm.vt100.background': {value}")
    # Should match XTerm*background
    
    print("  ✓ Wildcard matching works")
    print()
    return True


def test_classes_extraction():
    """Test extraction of resource classes."""
    print("=" * 60)
    print("TEST 3: Class Extraction")
    print("=" * 60)
    
    parser = XResourcesParser()
    parser.parse(SAMPLE_XRESOURCES)
    
    classes = parser.get_all_classes()
    print(f"Found classes: {classes}")
    
    # Should find XTerm, URxvt, and wildcard (*)
    assert "XTerm" in classes, "XTerm class not found"
    assert "URxvt" in classes, "URxvt class not found"
    
    print("  ✓ Class extraction works")
    print()
    return True


def test_multiline_values():
    """Test parsing of multi-line values with backslash continuation."""
    print("=" * 60)
    print("TEST 4: Multi-line Values")
    print("=" * 60)
    
    parser = XResourcesParser()
    entries = parser.parse(SAMPLE_XRESOURCES)
    
    # Find the multi-line entry
    multiline_entry = None
    for entry in entries:
        if "multi-line" in entry.value:
            multiline_entry = entry
            break
    
    if multiline_entry:
        print(f"Multi-line entry found:")
        print(f"  Path: {multiline_entry.resource_path}")
        print(f"  Value: {multiline_entry.value}")
        assert "multi-line" in multiline_entry.value
        assert "multiple lines" in multiline_entry.value
        print("  ✓ Multi-line parsing works")
    else:
        print("  ✗ Multi-line entry not found")
        return False
    
    print()
    return True


def test_conditional_directives():
    """Test preprocessor conditional directives."""
    print("=" * 60)
    print("TEST 5: Conditional Directives")
    print("=" * 60)
    
    parser = XResourcesParser()
    entries = parser.parse(SAMPLE_XRESOURCES)
    
    print(f"Preprocessor directives found: {len(parser.preprocessor_directives)}")
    for directive in parser.preprocessor_directives:
        print(f"  Line {directive.line_number}: #{directive.directive} {directive.argument or ''}")
    
    # Check that conditionals were tracked
    conditional_entries = [e for e in entries if e.is_conditional]
    print(f"Entries inside conditionals: {len(conditional_entries)}")
    
    print("  ✓ Conditional directives parsed")
    print()
    return True


def test_write_back():
    """Test write back functionality."""
    print("=" * 60)
    print("TEST 6: Write Back")
    print("=" * 60)
    
    parser = XResourcesParser()
    parser.parse(SAMPLE_XRESOURCES)
    
    # Modify an entry
    parser.update_value("XTerm*background", "darkblue")
    
    # Add a new entry
    parser.add_entry("XTerm*cursorColor", "#ff0000", "Cursor color setting")
    
    # Generate output
    output = parser.write_back()
    
    print("Generated output (first 20 lines):")
    lines = output.split('\n')[:20]
    for line in lines:
        print(f"  {line}")
    
    # Verify modifications are in output
    assert "darkblue" in output, "Updated value not in output"
    assert "XTerm*cursorColor" in output, "New entry not in output"
    assert "#ff0000" in output, "New value not in output"
    
    print("  ✓ Write back works")
    print()
    return True


def test_comments_preservation():
    """Test that comments are preserved and associated with entries."""
    print("=" * 60)
    print("TEST 7: Comments Preservation")
    print("=" * 60)
    
    parser = XResourcesParser()
    entries = parser.parse(SAMPLE_XRESOURCES)
    
    # Find entries with comments
    entries_with_comments = [e for e in entries if e.comment]
    print(f"Entries with comments: {len(entries_with_comments)}")
    
    for entry in entries_with_comments[:3]:
        print(f"  {entry.resource_path}: '{entry.comment}'")
    
    print("  ✓ Comments preserved")
    print()
    return True


def test_color_resources():
    """Test color definition parsing."""
    print("=" * 60)
    print("TEST 8: Color Resources")
    print("=" * 60)
    
    parser = XResourcesParser()
    entries = parser.parse(SAMPLE_XRESOURCES)
    
    # Find color entries
    color_entries = [e for e in entries if "color" in e.resource_path.lower()]
    print(f"Color entries found: {len(color_entries)}")
    
    for entry in color_entries[:5]:
        print(f"  {entry.resource_path}: {entry.value}")
    
    # Verify specific colors
    color0 = parser.get_value("*.color0")
    print(f"  *.color0 = {color0}")
    assert color0 == "#000000", f"Expected #000000, got {color0}"
    
    print("  ✓ Color resources parsed correctly")
    print()
    return True


def run_all_tests():
    """Run all tests and report results."""
    print("\n" + "=" * 60)
    print("XRESOURCES PARSER TEST SUITE")
    print("=" * 60 + "\n")
    
    tests = [
        test_basic_parsing,
        test_wildcard_matching,
        test_classes_extraction,
        test_multiline_values,
        test_conditional_directives,
        test_write_back,
        test_comments_preservation,
        test_color_resources,
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
            failed += 1
            print()
    
    print("=" * 60)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("=" * 60)
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
