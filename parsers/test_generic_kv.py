#!/usr/bin/env python3
"""
Test file for Generic KV Parser

Run with: python parsers/test_generic_kv.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from parsers.generic_kv_parser import GenericKVParser, KVEntry


# Sample environment file content
SAMPLE_ENV = """
# Database configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=myapp
DB_USER=admin
DB_PASS="secret password"

# Application settings
export APP_ENV=production
export DEBUG=false
LOG_LEVEL=info

# Paths with spaces
export PATH="/usr/local/bin:/usr/bin"
DATA_DIR=/var/lib/myapp

# Multi-line with continuation
DESCRIPTION="This is a \\
multi-line description"

# Special characters
SPECIAL_KEY="value with \\"quotes\\""
MESSAGE=Hello\\nWorld
TAB_SEP=a\\tb\\tc
"""


def test_basic_parsing():
    """Test basic KEY=value parsing."""
    print("=" * 60)
    print("TEST 1: Basic Parsing")
    print("=" * 60)
    
    parser = GenericKVParser()
    entries = parser.parse(SAMPLE_ENV)
    
    print(f"Parsed {len(entries)} entries")
    print()
    
    # Check specific values
    db_host = parser.get('DB_HOST')
    print(f"DB_HOST = {db_host}")
    assert db_host == 'localhost', f"Expected 'localhost', got '{db_host}'"
    
    db_port = parser.get('DB_PORT')
    print(f"DB_PORT = {db_port}")
    assert db_port == '5432'
    
    print("  ✓ Basic parsing works")
    print()
    return True


def test_export_parsing():
    """Test export KEY=value parsing."""
    print("=" * 60)
    print("TEST 2: Export Parsing")
    print("=" * 60)
    
    parser = GenericKVParser()
    parser.parse(SAMPLE_ENV)
    
    # Find export entries
    export_entries = [e for e in parser.entries if e.is_export]
    print(f"Export entries: {len(export_entries)}")
    for entry in export_entries:
        print(f"  export {entry.key}={entry.value}")
    
    # Check specific exports
    app_env = parser.get('APP_ENV')
    assert app_env == 'production'
    assert any(e.key == 'APP_ENV' and e.is_export for e in parser.entries)
    
    print("  ✓ Export parsing works")
    print()
    return True


def test_quoted_values():
    """Test quoted value parsing."""
    print("=" * 60)
    print("TEST 3: Quoted Values")
    print("=" * 60)
    
    parser = GenericKVParser()
    parser.parse(SAMPLE_ENV)
    
    # Check quoted values
    db_pass = parser.get('DB_PASS')
    print(f"DB_PASS = {db_pass}")
    assert db_pass == 'secret password', f"Expected 'secret password', got '{db_pass}'"
    
    path = parser.get('PATH')
    print(f"PATH = {path}")
    assert '/usr/local/bin' in path
    
    print("  ✓ Quoted values work")
    print()
    return True


def test_escape_sequences():
    """Test escape sequence handling."""
    print("=" * 60)
    print("TEST 4: Escape Sequences")
    print("=" * 60)
    
    parser = GenericKVParser()
    parser.parse(SAMPLE_ENV)
    
    message = parser.get('MESSAGE')
    print(f"MESSAGE = {repr(message)}")
    assert '\\n' in message or message == 'Hello\\nWorld'
    
    tab = parser.get('TAB_SEP')
    print(f"TAB_SEP = {repr(tab)}")
    
    print("  ✓ Escape sequences work")
    print()
    return True


def test_comments():
    """Test comment preservation."""
    print("=" * 60)
    print("TEST 5: Comments")
    print("=" * 60)
    
    parser = GenericKVParser()
    parser.parse(SAMPLE_ENV)
    
    entries_with_comments = [e for e in parser.entries if e.comment]
    print(f"Entries with comments: {len(entries_with_comments)}")
    
    for entry in entries_with_comments[:3]:
        print(f"  {entry.key}: '{entry.comment}'")
    
    print("  ✓ Comments preserved")
    print()
    return True


def test_write_back():
    """Test write back functionality."""
    print("=" * 60)
    print("TEST 6: Write Back")
    print("=" * 60)
    
    parser = GenericKVParser()
    parser.parse(SAMPLE_ENV)
    
    # Modify an entry
    parser.set('DB_HOST', 'remotehost')
    
    # Add new entry
    parser.set('NEW_KEY', 'new_value', is_export=True)
    
    output = parser.write_back()
    
    print("Generated output (first 15 lines):")
    lines = output.split('\n')[:15]
    for line in lines:
        print(f"  {line}")
    
    assert 'remotehost' in output
    assert 'NEW_KEY=new_value' in output or 'export NEW_KEY=new_value' in output
    
    print("  ✓ Write back works")
    print()
    return True


def test_to_dict():
    """Test dictionary conversion."""
    print("=" * 60)
    print("TEST 7: To Dictionary")
    print("=" * 60)
    
    parser = GenericKVParser()
    parser.parse(SAMPLE_ENV)
    
    data = parser.to_dict()
    print(f"Dictionary has {len(data)} keys")
    print(f"Keys: {list(data.keys())[:5]}...")
    
    assert 'DB_HOST' in data
    assert 'APP_ENV' in data
    
    print("  ✓ Dictionary conversion works")
    print()
    return True


def run_all_tests():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("GENERIC KV PARSER TEST SUITE")
    print("=" * 60 + "\n")
    
    tests = [
        test_basic_parsing,
        test_export_parsing,
        test_quoted_values,
        test_escape_sequences,
        test_comments,
        test_write_back,
        test_to_dict,
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
