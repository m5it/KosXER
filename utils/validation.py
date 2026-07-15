#!/usr/bin/env python3
"""
Validation Utilities for KosXER

Provides syntax checking and validation for various configuration
file formats before saving.
"""

import re
import os
from pathlib import Path
from typing import Tuple, List, Optional, Callable
import tkinter as tk
from tkinter import messagebox


class ValidationError:
    """Represents a validation error."""
    def __init__(self, message: str, line: Optional[int] = None, 
                 column: Optional[int] = None, severity: str = "error"):
        self.message = message
        self.line = line
        self.column = column
        self.severity = severity  # "error", "warning", "info"
    
    def __str__(self) -> str:
        if self.line:
            return f"Line {self.line}: {self.message}"
        return self.message


class SyntaxValidator:
    """
    Base class for syntax validators.
    
    Validates configuration files before saving to prevent
    syntax errors that could break applications.
    """
    
    def __init__(self):
        self.errors: List[ValidationError] = []
        self.warnings: List[ValidationError] = []
    
    def validate(self, content: str) -> Tuple[bool, List[ValidationError]]:
        """
        Validate content.
        
        Args:
            content: File content to validate
            
        Returns:
            Tuple of (is_valid, errors)
        """
        self.errors = []
        self.warnings = []
        
        self._do_validation(content)
        
        all_issues = self.errors + self.warnings
        return len(self.errors) == 0, all_issues
    
    def _do_validation(self, content: str):
        """
        Perform validation. Override in subclasses.
        
        Args:
            content: File content
        """
        pass
    
    def add_error(self, message: str, line: Optional[int] = None):
        """Add validation error."""
        self.errors.append(ValidationError(message, line, severity="error"))
    
    def add_warning(self, message: str, line: Optional[int] = None):
        """Add validation warning."""
        self.warnings.append(ValidationError(message, line, severity="warning"))


class XResourcesValidator(SyntaxValidator):
    """Validator for XResources files."""
    
    def _do_validation(self, content: str):
        """Validate XResources syntax."""
        lines = content.split('\n')
        
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            
            # Skip empty lines and comments
            if not stripped or stripped.startswith('!'):
                continue
            
            # Skip preprocessor directives
            if stripped.startswith('#'):
                continue
            
            # Check for resource definitions
            if ':' not in stripped:
                # Might be a continuation line
                if i > 1 and not lines[i-2].rstrip().endswith('\\'):
                    self.add_warning(f"Line without colon (might be invalid): {stripped[:30]}", i)
                continue
            
            # Split resource and value
            parts = stripped.split(':', 1)
            if len(parts) != 2:
                self.add_error(f"Invalid resource format (missing colon): {stripped[:30]}", i)
                continue
            
            resource = parts[0].strip()
            value = parts[1].strip()
            
            # Check resource path
            if not resource:
                self.add_error("Empty resource path", i)
            elif '*' not in resource and '.' not in resource:
                self.add_warning(f"Resource without class specification: {resource}", i)
            
            # Check for unmatched quotes
            if value.count('"') % 2 != 0:
                self.add_error("Unmatched double quote in value", i)
            if value.count("'") % 2 != 0:
                self.add_error("Unmatched single quote in value", i)


class OpenBoxMenuValidator(SyntaxValidator):
    """Validator for OpenBox menu.xml files."""
    
    def _do_validation(self, content: str):
        """Validate OpenBox menu XML."""
        try:
            import xml.etree.ElementTree as ET
            root = ET.fromstring(content)
            
            # Check root element
            if root.tag != 'openbox_menu':
                self.add_error(f"Invalid root element: {root.tag} (expected 'openbox_menu')")
            
            # Check for menu elements
            menus = root.findall('.//menu')
            if not menus:
                self.add_warning("No menu elements found")
            
            # Validate menu structure
            for menu in menus:
                if not menu.get('id'):
                    self.add_error("Menu without id attribute")
                if not menu.get('label'):
                    self.add_error("Menu without label attribute")
            
            # Check for items
            items = root.findall('.//item')
            for item in items:
                if not item.get('label'):
                    self.add_warning("Item without label")
                action = item.find('action')
                if action is None:
                    self.add_error("Item without action")
                    
        except ET.ParseError as e:
            self.add_error(f"XML Parse Error: {str(e)}")
        except Exception as e:
            self.add_error(f"Validation Error: {str(e)}")


class KeyValueValidator(SyntaxValidator):
    """Validator for key=value files."""
    
    def _do_validation(self, content: str):
        """Validate KEY=value syntax."""
        lines = content.split('\n')
        
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            
            # Skip empty lines and comments
            if not stripped or stripped.startswith('#'):
                continue
            
            # Skip export keyword
            if stripped.startswith('export '):
                stripped = stripped[7:].strip()
            
            # Check for equals sign
            if '=' not in stripped:
                # Might be a flag
                if ' ' in stripped:
                    self.add_warning(f"Line without equals sign: {stripped[:30]}", i)
                continue
            
            # Split key and value
            parts = stripped.split('=', 1)
            if len(parts) != 2:
                self.add_error(f"Invalid format: {stripped[:30]}", i)
                continue
            
            key = parts[0].strip()
            value = parts[1].strip()
            
            # Validate key
            if not key:
                self.add_error("Empty key", i)
            elif ' ' in key:
                self.add_error(f"Key contains space: {key}", i)
            elif not re.match(r'^[A-Za-z_][A-Za-z0-9_]*$', key):
                self.add_warning(f"Key has unusual characters: {key}", i)
            
            # Check for unmatched quotes
            if value.count('"') % 2 != 0:
                self.add_error("Unmatched double quote", i)
            if value.count("'") % 2 != 0:
                self.add_error("Unmatched single quote", i)


class ValidationManager:
    """
    Manages validators for different file types.
    
    Automatically selects appropriate validator based on file type.
    """
    
    def __init__(self):
        self.validators: dict = {
            'xresources': XResourcesValidator(),
            'openbox_menu': OpenBoxMenuValidator(),
            'openbox_rc': OpenBoxMenuValidator(),  # Same XML structure
            'generic_kv': KeyValueValidator(),
            'shell_exports': KeyValueValidator(),
        }
    
    def get_validator(self, file_type: str) -> Optional[SyntaxValidator]:
        """Get validator for file type."""
        return self.validators.get(file_type)
    
    def validate_file(self, filepath: str, content: str) -> Tuple[bool, List[ValidationError]]:
        """
        Validate file content based on file type.
        
        Args:
            filepath: Path to file (for type detection)
            content: File content
            
        Returns:
            Tuple of (is_valid, errors)
        """
        from parsers import detect_parser
        
        parser_class = detect_parser(filepath)
        if not parser_class:
            # Unknown type, skip validation
            return True, []
        
        # Map parser to validator
        validator_map = {
            'XResourcesParser': 'xresources',
            'OpenBoxMenuParser': 'openbox_menu',
            'OpenBoxRCParser': 'openbox_rc',
            'GenericKVParser': 'generic_kv',
        }
        
        parser_name = parser_class.__name__
        validator_key = validator_map.get(parser_name)
        
        if validator_key and validator_key in self.validators:
            return self.validators[validator_key].validate(content)
        
        return True, []
    
    def confirm_save_with_errors(self, errors: List[ValidationError], 
                                  parent_widget=None) -> bool:
        """
        Show confirmation dialog when validation has errors.
        
        Args:
            errors: List of validation errors
            parent_widget: Parent widget for dialog
            
        Returns:
            True if user wants to save anyway
        """
        if not errors:
            return True
        
        # Separate errors and warnings
        errors_only = [e for e in errors if e.severity == "error"]
        warnings = [e for e in errors if e.severity == "warning"]
        
        if not errors_only:
            # Only warnings, proceed with warning
            warning_text = "\\n".join([str(w) for w in warnings[:5]])
            response = messagebox.askyesno(
                "Validation Warnings",
                f"The following warnings were found:\\n\\n{warning_text}\\n\\n"
                f"Save anyway?",
                parent=parent_widget
            )
            return response
        
        # Has errors
        error_text = "\\n".join([str(e) for e in errors_only[:5]])
        if len(errors_only) > 5:
            error_text += f"\\n... and {len(errors_only) - 5} more errors"
        
        messagebox.showerror(
            "Validation Failed",
            f"Cannot save due to errors:\\n\\n{error_text}\\n\\n"
            f"Please fix the errors before saving.",
            parent=parent_widget
        )
        return False


# Convenience functions

def validate_before_save(filepath: str, content: str, 
                        parent_widget=None) -> bool:
    """
    Validate file before saving.
    
    Args:
        filepath: Path to file
        content: File content
        parent_widget: Parent widget for dialogs
        
    Returns:
        True if validation passed or user chose to save anyway
    """
    manager = ValidationManager()
    is_valid, errors = manager.validate_file(filepath, content)
    
    if is_valid:
        return True
    
    return manager.confirm_save_with_errors(errors, parent_widget)


def quick_validate(filepath: str, content: str) -> Tuple[bool, List[str]]:
    """
    Quick validation returning simple results.
    
    Args:
        filepath: Path to file
        content: File content
        
    Returns:
        Tuple of (is_valid, error_messages)
    """
    manager = ValidationManager()
    is_valid, errors = manager.validate_file(filepath, content)
    
    messages = [str(e) for e in errors]
    return is_valid, messages
