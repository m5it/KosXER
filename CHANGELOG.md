# Changelog

All notable changes to KosXER will be documented in this file.

## [Unreleased] - 2026-01-16

### Fixed
- **UI Bug**: Fixed dropdown blinking when searching in Add Resource dialog
  - Removed auto-open dropdown on every keystroke
  - Dropdown now only opens with Alt+Down or manual click
  - Filter still updates values without forcing dropdown open
- **UI Bug**: Fixed double-click on tree item opening empty window
  - Changed to use identify() to get actual item under cursor
  - Added proper item selection before processing
  - Improved validation of tree item values
- **Data Bug**: Fixed save/update not persisting changes
  - Changed _update_entry() to use parser.update_value() method
  - Fixed method name mismatch causing updates to fail

## [1.1.0] - 2025-01-15
  - Filter still updates values without forcing dropdown open
- **UI Bug**: Fixed double-click on tree item opening empty window
  - Changed to use identify() to get actual item under cursor
  - Added proper item selection before processing
  - Improved validation of tree item values
- **Data Bug**: Fixed save/update not persisting changes
  - Changed _update_entry() to use parser.update_value() method
  - Fixed method name mismatch causing updates to fail

## [1.1.0] - 2025-01-15

### Fixed
- **Critical Bug**: Fixed duplicate add/delete operations in KV Editor and XResources Editor
  - Fixed race conditions in add/delete handlers
- **Critical Bug**: Fixed save functionality not working properly
  - Added backup creation before save operations
  - Added proper error handling and verification
  - Fixed file write verification
  - Fixed Save As to update editor tracking correctly
- **Critical Bug**: Fixed new code not being visible due to import errors
  - Fixed IndentationError in main.py
  - Cleared stale __pycache__ files
  - Verified all KosDWM editors are properly registered

### Added
- Comprehensive debug logging system
  - Added utils/logging_config.py for centralized logging
  - Added operation tracking throughout the application
  - Added error logging with stack traces
- Test suite for critical operations (test_critical_operations.py)
  - Tests for all parser modules
  - Tests for file save operations
  - Tests for module imports

### Changed
- Improved error messages for file operations
- Enhanced status bar feedback during save operations

## [1.0.0] - 2025-01-10

### Added
- Initial release of KosXER
- Support for .Xresources/.Xdefaults files with live xrdb apply
- Support for OpenBox menu.xml and rc.xml
- Support for KosDWM config.json and menu structure
- Support for generic key-value config files (.conf, .env, .rc)
- Dual-pane layout with file browser and tabbed editor
- Intelligent presets with color picker and font selection
- XTerm helper buttons for testing resources
- Auto-versioning with git integration
- Backup on save functionality
  - Font editor with dropdown of common monospace fonts
  - Boolean editor with true/false/yes/no/on/off options
  - Preset picker dialog with search/filter across all categories
  - Double-click resource to get smart editor based on name

- **XTerm Helper Features**
  - "New XTerm" button - launches fresh xterm with current resources
  - "XTerm Tips" button - educational dialog explaining restart behavior
  - Info label explaining why xterm needs restart to see changes
  - Color reference table showing color0-color15 values

- **Auto-Versioning System** (`AUTOVERSION.py`)
  - Single source of truth for version number
  - Git pre-commit hook automatically increments version
  - Version displayed in window title and About dialog

- **File Browser Enhancements**
  - Show/hide hidden files toggle (Ctrl+H)
  - Checkbox in file browser and menu item in View menu
  - Keyboard shortcut Ctrl+H to toggle
  - F5 to refresh file browser

- **XResources Editor - Apply Button**
  - "Apply (xrdb)" button to reload X resources without restart
  - Runs `xrdb -merge` on current file
  - Smart enable/disable based on file saved state
  - Error handling for xrdb not found or syntax errors

- **GUI Editors Implemented**
  - XResources Editor with treeview, color picker, filter, presets
  - OpenBox Menu Editor for menu.xml
  - Generic Key-Value Editor for .conf, .env, .rc files
  - KosDWM Config Editor
  - KosDWM Menu Editor

- **Main Application Features**
  - Tabbed interface with notebook
  - Recent files menu
  - Status bar with file info, parser type, position
  - Keyboard shortcuts (Ctrl+O, Ctrl+S, Ctrl+Q, etc.)
  - About dialog with version info

### Changed
- Refactored project structure with gui/, parsers/, config/ directories
- Version now imported from AUTOVERSION.py throughout codebase
- XResources editor now intelligently detects resource types

### Fixed
- File browser now filters hidden files by default
- Apply button disabled until file is saved
- XTerm restart behavior now clearly documented

## [0.1.0] - 2026-07-15

### Added
- Project initialization
- Basic directory structure
- Parser modules for XResources, OpenBox, and generic configs
- Test suites for parsers
- README and project documentation

---

## Version Format

- MAJOR: Breaking changes
- MINOR: New features (backward compatible)
- PATCH: Bug fixes
