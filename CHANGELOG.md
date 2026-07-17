# Changelog

All notable changes to KosXER will be documented in this file.

## [Unreleased]

### Added
- **Intelligent Presets System** (`config/presets.py`)
  - Auto-detects resource types from resource names (color, font, boolean)
  - Color editor with picker + preset palette (16 terminal colors + common colors)
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
