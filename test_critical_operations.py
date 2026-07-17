#!/usr/bin/env python3
"""
Critical Operations Test Suite for KosXER

Tests the fixes for:
- Duplicate add/delete operations
- Save functionality
- Module imports and visibility

Run with: python test_critical_operations.py
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

import logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


class TestResult:
    """Track test results."""
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.errors = []
    
    def add_pass(self, test_name):
        self.passed += 1
        print(f"  ✓ {test_name}")
    
    def add_fail(self, test_name, error):
        self.failed += 1
        self.errors.append((test_name, error))
        print(f"  ✗ {test_name}: {error}")
    
    def summary(self):
        total = self.passed + self.failed
        print(f"\n{'='*50}")
        print(f"Test Summary: {self.passed}/{total} passed")
        if self.failed > 0:
            print(f"Failed tests:")
            for name, error in self.errors:
                print(f"  - {name}: {error}")
        print(f"{'='*50}")
        return self.failed == 0


def test_imports():
    """Test that all modules import correctly."""
    results = TestResult()
    print("\n--- Testing Module Imports ---")
    
    tests = [
        ("gui.editor_base", "EditorWidget"),
        ("gui.kv_editor", "KVEditor"),
        ("gui.xresources_editor", "XResourcesEditor"),
        ("gui.openbox_editor", "OpenBoxEditor"),
        ("gui.kosdwm_config_editor", "KosDWMConfigEditor"),
        ("gui.kosdwm_menu_editor", "KosDWMMenuEditor"),
        ("parsers.generic_kv_parser", "GenericKVParser"),
        ("parsers.xresources_parser", "XResourcesParser"),
        ("parsers.openbox_parser", "OpenBoxMenuParser"),
        ("parsers.kosdwm_config_parser", "KosDWMConfigParser"),
        ("parsers.kosdwm_menu_parser", "KosDWMMenuParser"),
        ("utils.logging_config", "setup_logging"),
    ]
    
    for module_name, item_name in tests:
        try:
            module = __import__(module_name, fromlist=[item_name])
            getattr(module, item_name)
            results.add_pass(f"Import {module_name}.{item_name}")
        except Exception as e:
            results.add_fail(f"Import {module_name}.{item_name}", str(e))
    
    return results


def test_kv_parser():
    """Test KV parser operations."""
    results = TestResult()
    print("\n--- Testing KV Parser Operations ---")
    
    try:
        from parsers.generic_kv_parser import GenericKVParser, KVEntry
        
        # Test parse
        content = """KEY1=value1
KEY2=value2
# Comment
KEY3=value3"""
        
        parser = GenericKVParser()
        entries = parser.parse(content)
        
        if len(entries) == 3:
            results.add_pass("Parse 3 entries")
        else:
            results.add_fail("Parse 3 entries", f"Expected 3, got {len(entries)}")
        
        # Test write back
        output = parser.write_back()
        if "KEY1=value1" in output and "KEY2=value2" in output:
            results.add_pass("Write back preserves content")
        else:
            results.add_fail("Write back preserves content", "Content mismatch")
        
        # Test add entry
        parser.add_entry("KEY4", "value4")
        if len(parser.entries) == 4:
            results.add_pass("Add entry increases count")
        else:
            results.add_fail("Add entry increases count", f"Expected 4, got {len(parser.entries)}")
        
        # Test remove entry
        parser.remove("KEY1")
        if len(parser.entries) == 3:
            results.add_pass("Remove entry decreases count")
        else:
            results.add_fail("Remove entry decreases count", f"Expected 3, got {len(parser.entries)}")
        
    except Exception as e:
        results.add_fail("KV Parser tests", str(e))
    
    return results


def test_xresources_parser():
    """Test XResources parser operations."""
    results = TestResult()
    print("\n--- Testing XResources Parser Operations ---")
    
    try:
        from parsers.xresources_parser import XResourcesParser
        
        # Test parse
        content = """XTerm*background: #000000
XTerm*foreground: #ffffff
*.color0: #000000
*.color1: #ff0000"""
        
        parser = XResourcesParser()
        entries = parser.parse(content)
        
        if len(entries) == 4:
            results.add_pass("Parse 4 resources")
        else:
            results.add_fail("Parse 4 resources", f"Expected 4, got {len(entries)}")
        
        # Test write back
        output = parser.write_back()
        if "XTerm*background:\t#000000" in output:
            results.add_pass("Write back preserves resources")
        else:
            results.add_fail("Write back preserves resources", "Content mismatch")
        
        # Test add entry
        parser.add_entry("NewResource", "newvalue")
        if len(parser.entries) == 5:
            results.add_pass("Add resource increases count")
        else:
            results.add_fail("Add resource increases count", f"Expected 5, got {len(parser.entries)}")
        
        # Test remove entry
        parser.remove_entry("XTerm*background")
        if len(parser.entries) == 4:
            results.add_pass("Remove resource decreases count")
        else:
            results.add_fail("Remove resource decreases count", f"Expected 4, got {len(parser.entries)}")
        
    except Exception as e:
        results.add_fail("XResources Parser tests", str(e))
    
    return results


def test_file_save():
    """Test actual file save operations."""
    results = TestResult()
    print("\n--- Testing File Save Operations ---")
    
    try:
        from parsers.generic_kv_parser import GenericKVParser
        
        # Create temp directory
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.env"
            
            # Create parser and add entries
            parser = GenericKVParser()
            parser.add_entry("TEST_KEY", "test_value")
            parser.add_entry("ANOTHER_KEY", "another_value")
            
            # Write to file
            content = parser.write_back(str(test_file))
            
            # Verify file exists
            if test_file.exists():
                results.add_pass("File created")
            else:
                results.add_fail("File created", "File does not exist")
            
            # Verify backup created
            backup_file = str(test_file) + '.bak'
            # Note: backup is created by main.py, not parser
            
            # Read back and verify
            with open(test_file, 'r') as f:
                read_content = f.read()
            
            if "TEST_KEY=test_value" in read_content:
                results.add_pass("Content written correctly")
            else:
                results.add_fail("Content written correctly", f"Content: {read_content}")
            
            # Test round-trip
            parser2 = GenericKVParser()
            parser2.parse_file(test_file)
            
            if len(parser2.entries) == 2:
                results.add_pass("Round-trip preserves entries")
            else:
                results.add_fail("Round-trip preserves entries", f"Expected 2, got {len(parser2.entries)}")
                
    except Exception as e:
        results.add_fail("File save tests", str(e))
    
    return results


def test_dialog_protection():
    """Test that dialog protection flags exist."""
    results = TestResult()
    print("\n--- Testing Dialog Protection ---")
    
    try:
        from gui.kv_editor import KVEditor
        
        # Check that protection attributes exist
        if hasattr(KVEditor, '_add_row'):
            results.add_pass("KVEditor has _add_row method")
        else:
            results.add_fail("KVEditor has _add_row method", "Method not found")
        
        # Check XResourcesEditor
        from gui.xresources_editor import XResourcesEditor
        
        if hasattr(XResourcesEditor, '_add_resource'):
            results.add_pass("XResourcesEditor has _add_resource method")
        else:
            results.add_fail("XResourcesEditor has _add_resource method", "Method not found")
            
    except Exception as e:
        results.add_fail("Dialog protection tests", str(e))
    
    return results


def test_kosdwm_parsers():
    """Test KosDWM parsers."""
    results = TestResult()
    print("\n--- Testing KosDWM Parsers ---")
    
    try:
        from parsers.kosdwm_config_parser import KosDWMConfigParser, KosDWMConfig
        
        # Test config creation
        config = KosDWMConfig()
        if config.active_button_bg == "#4a90d9":
            results.add_pass("Default config values")
        else:
            results.add_fail("Default config values", f"Got {config.active_button_bg}")
        
        # Test parser
        parser = KosDWMConfigParser()
        test_json = '{"active_button_bg": "#ff0000", "bar_height": 100}'
        config = parser.parse(test_json)
        
        if config.active_button_bg == "#ff0000" and config.bar_height == 100:
            results.add_pass("Parse JSON config")
        else:
            results.add_fail("Parse JSON config", "Values mismatch")
        
        # Test write back
        output = parser.write_back()
        if '"active_button_bg": "#ff0000"' in output:
            results.add_pass("Write back JSON")
        else:
            results.add_fail("Write back JSON", "Output mismatch")
        
        # Test validation
        is_valid, errors = parser.validate()
        if is_valid:
            results.add_pass("Config validation")
        else:
            results.add_fail("Config validation", f"Errors: {errors}")
            
    except Exception as e:
        results.add_fail("KosDWM parser tests", str(e))
    
    return results


def test_main_py_syntax():
    """Test that main.py has no syntax errors."""
    results = TestResult()
    print("\n--- Testing main.py Syntax ---")
    
    try:
        import py_compile
        py_compile.compile('main.py', doraise=True)
        results.add_pass("main.py compiles without errors")
    except Exception as e:
        results.add_fail("main.py syntax", str(e))
    
    return results


def run_all_tests():
    """Run all tests and return overall result."""
    print("="*50)
    print("KosXER Critical Operations Test Suite")
    print("="*50)
    
    all_results = [
        test_imports(),
        test_kv_parser(),
        test_xresources_parser(),
        test_file_save(),
        test_dialog_protection(),
        test_kosdwm_parsers(),
        test_main_py_syntax(),
    ]
    
    total_passed = sum(r.passed for r in all_results)
    total_failed = sum(r.failed for r in all_results)
    total = total_passed + total_failed
    
    print(f"\n{'='*50}")
    print(f"OVERALL RESULTS: {total_passed}/{total} tests passed")
    
    if total_failed > 0:
        print(f"\nFailed tests by category:")
        for results in all_results:
            if results.failed > 0:
                print(f"\n{results.failed} failures:")
                for name, error in results.errors:
                    print(f"  - {name}")
        print(f"\n{'='*50}")
        return False
    
    print(f"\n✓ All tests passed!")
    print(f"{'='*50}")
    return True


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
