#!/usr/bin/env python3
"""
AUTOVERSION - Single Source of Truth for KosXER Version

This file defines the VERSION constant and provides functions
to increment it automatically on git commits.

Usage as module:
    from AUTOVERSION import VERSION
    print(f"App version: {VERSION}")

Usage as script:
    python AUTOVERSION.py          # Increment version
    python AUTOVERSION.py --show   # Show current version
"""

import sys
import re
import os
from pathlib import Path

# =============================================================================
# VERSION - Single Source of Truth
# =============================================================================
VERSION = "1.0.2"

# Version file location (relative to this file)
VERSION_FILE = Path(__file__).parent / "config" / "VERSION"


def parse_version(version_str: str) -> tuple:
    """Parse version string into tuple (major, minor, patch)."""
    parts = version_str.split('.')
    major = int(parts[0]) if len(parts) > 0 else 1
    minor = int(parts[1]) if len(parts) > 1 else 0
    patch = int(parts[2]) if len(parts) > 2 else 0
    return (major, minor, patch)


def format_version(major: int, minor: int, patch: int) -> str:
    """Format version tuple into string."""
    return f"{major}.{minor}.{patch}"


def increment_version(version_str: str) -> str:
    """
    Increment version number (patch level).
    
    Examples:
        "1.0"     -> "1.0.1"
        "1.0.0"   -> "1.0.1"
        "1.0.9"   -> "1.0.10"
        "1.2.99"  -> "1.2.100"
    """
    major, minor, patch = parse_version(version_str)
    
    if len(version_str.split('.')) == 2:
        # Was X.Y format, start patch at 1
        return format_version(major, minor, 1)
    else:
        # Increment patch
        return format_version(major, minor, patch + 1)


def update_version_file(new_version: str):
    """Update the VERSION constant in this file."""
    this_file = Path(__file__)
    
    try:
        content = this_file.read_text()
        
        # Replace VERSION = "X.Y.Z" with new version
        new_content = re.sub(
            r'^(VERSION\s*=\s*["\'])([\d.]+)(["\'])',
            rf'\g<1>{new_version}\g<3>',
            content,
            flags=re.MULTILINE
        )
        
        if new_content != content:
            this_file.write_text(new_content)
            print(f"Updated AUTOVERSION.py: {new_version}")
        
    except Exception as e:
        print(f"Error updating AUTOVERSION.py: {e}", file=sys.stderr)


def update_constants_py(new_version: str):
    """Update version in config/constants.py."""
    constants_file = Path(__file__).parent / "config" / "constants.py"
    
    if not constants_file.exists():
        return
    
    try:
        content = constants_file.read_text()
        
        # Update VERSION constant
        new_content = re.sub(
            r'^(VERSION\s*=\s*["\'])([\d.]+)(["\'])',
            rf'\g<1>{new_version}\g<3>',
            content,
            flags=re.MULTILINE
        )
        
        if new_content != content:
            constants_file.write_text(new_content)
            print(f"Updated config/constants.py: {new_version}")
        
    except Exception as e:
        print(f"Error updating constants.py: {e}", file=sys.stderr)


def update_version_file_txt(new_version: str):
    """Update plain text VERSION file."""
    version_file = Path(__file__).parent / "config" / "VERSION"
    
    try:
        version_file.parent.mkdir(parents=True, exist_ok=True)
        version_file.write_text(new_version + '\n')
        print(f"Updated config/VERSION: {new_version}")
    except Exception as e:
        print(f"Error writing VERSION file: {e}", file=sys.stderr)


def show_version():
    """Display current version."""
    print(f"KosXER version: {VERSION}")
    print(f"Version file: {VERSION_FILE}")


def main():
    """Main entry point for auto-versioning."""
    # Check for --show flag
    if len(sys.argv) > 1 and sys.argv[1] in ('--show', '-s', 'show'):
        show_version()
        return 0
    
    # Increment version
    current = VERSION
    new_version = increment_version(current)
    
    print(f"Incrementing version: {current} -> {new_version}")
    
    # Update all version files
    update_version_file(new_version)
    update_constants_py(new_version)
    update_version_file_txt(new_version)
    
    # Stage files for git
    os.system("git add AUTOVERSION.py")
    os.system("git add config/constants.py")
    os.system("git add config/VERSION")
    
    print(f"\n✓ Version bumped to {new_version}")
    print("  Files staged for commit")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
