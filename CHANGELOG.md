# Changelog

All notable changes to KosXER will be documented in this file.

## [Unreleased]

### Added
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
  - XResources Editor with treeview, color picker, filter
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

### Fixed
- File browser now filters hidden files by default
- Apply button disabled until file is saved

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
