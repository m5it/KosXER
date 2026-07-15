# Changelog

All notable changes to KosXER will be documented in this file.

## [Unreleased]

### Added
- Initial project structure with tkinter main window
- XResources parser with support for:
  - `.Xresources` and `.Xdefaults` files
  - Preprocessor directives (`#include`, `#ifdef`, `#ifndef`, `#endif`, `#else`)
  - Wildcard pattern matching (`*`, `?`)
  - Multi-line values with backslash continuation
  - Comment preservation
  - Write-back functionality
- OpenBox parser with support for:
  - `menu.xml` - Application menus with nested submenus
  - `rc.xml` - Window manager configuration
  - Keybindings and mouse bindings
  - Theme settings
  - Application-specific rules
- Generic key-value parser with support for:
  - INI-style sections
  - Shell export syntax
  - Comment preservation
  - Multiple delimiter types
- Backup utility for safe file operations
- Configuration management system

### Planned
- GUI editor widgets for each format
- File browser and workspace panel
- Syntax highlighting
- Live preview
- Search and filter functionality
- Preferences dialog
- User documentation and examples

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
