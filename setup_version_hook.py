#!/usr/bin/env python3
"""
Setup script for AUTOVERSION git hook

Run this to enable automatic version incrementing on commits.
"""

import os
import stat
import sys
from pathlib import Path

def setup_hook():
    """Setup the git pre-commit hook."""
    hook_path = Path(".git/hooks/pre-commit")
    
    if not hook_path.parent.exists():
        print("Error: Not a git repository or .git directory not found")
        print("Run this from the project root directory")
        return 1
    
    # Make hook executable
    current_permissions = hook_path.stat().st_mode
    hook_path.chmod(current_permissions | stat.S_IEXEC)
    
    print("✓ Git pre-commit hook is now executable")
    print("✓ Version will auto-increment on each commit")
    print("")
    print("Current version:", end=" ")
    
    # Show current version
    version_file = Path("config/VERSION")
    if version_file.exists():
        print(version_file.read_text().strip())
    else:
        print("1.0.0 (will be created on first commit)")
    
    return 0

if __name__ == "__main__":
    sys.exit(setup_hook())
