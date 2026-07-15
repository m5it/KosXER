# KosXER Documentation

Welcome to KosXER - the X11 Configuration Editor!

## Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [Features](#features)
- [Supported Formats](#supported-formats)
- [Getting Help](#getting-help)

## Installation

### Requirements

- Python 3.8 or higher
- tkinter (usually included with Python)
- Linux/Unix system with X11

### Install from Source

```bash
# Clone the repository
git clone https://github.com/yourusername/kosxer.git
cd kosxer

# Create virtual environment (recommended)
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run KosXER
python main.py
```

### System-wide Installation

```bash
# Install to /usr/local
sudo make install

# Or create a desktop entry
cp kosxer.desktop ~/.local/share/applications/
```

## Quick Start

### Opening Your First File

1. Launch KosXER: `python main.py`
2. Click **File → Open** or press **Ctrl+O**
3. Navigate to your config file (e.g., `~/.Xresources`)
4. The file will open in the appropriate editor

### Quick Access

The left sidebar provides quick access to common config locations:
- **Home** - Your home directory
- **.Xresources** - X11 resource definitions
- **OpenBox** - Window manager config
- **.config** - XDG config directory
- **Shell configs** - .bashrc, .zshrc, etc.

### Making Changes

1. Navigate to the setting you want to change
2. Double-click to edit
3. For colors: Use the color picker
4. For other values: Edit directly in the tree
5. Press **Ctrl+S** to save

## Features

### Dual-Pane Layout

- **Left**: File browser with quick access and bookmarks
- **Right**: Editor area with tabs for multiple files

### Smart Editors

Each file type gets a specialized editor:
- **XResources**: Tree view with color pickers
- **OpenBox Menu**: Visual menu editor with drag-drop
- **Key-Value**: Simple two-column editor for .env files

### Automatic Backups

KosXER creates backups before saving:
- Timestamped backups: `file.20260115_143022.bak`
- Simple backups: `file.bak`
- Configurable retention (default: keep last 5)

### Syntax Validation

Built-in validators catch errors before saving:
- Unmatched quotes
- Invalid resource paths
- XML syntax errors
- Duplicate keys

### File Watching

Detects external changes and prompts to reload.

## Supported Formats

See [FORMATS.md](FORMATS.md) for detailed information about each supported format.

### Overview

| Format | Extension | Editor Type |
|--------|-----------|-------------|
| X Resources | `.Xresources`, `.Xdefaults` | Tree with color picker |
| OpenBox Menu | `menu.xml` | Visual hierarchy |
| OpenBox RC | `rc.xml` | Key bindings & settings |
| Environment | `.env`, `.conf` | Key-value table |
| Shell Config | `.bashrc`, `.zshrc` | Key-value with exports |

## Getting Help

### Keyboard Shortcuts

Press **F1** or see [SHORTCUTS.md](SHORTCUTS.md) for a complete list.

### Tooltips

Hover over buttons and fields for helpful hints.

### Context Menus

Right-click on files and items for additional options.

## Troubleshooting

### "No module named 'tkinter'"

Install tkinter for your distribution:

```bash
# Debian/Ubuntu
sudo apt-get install python3-tk

# Fedora
sudo dnf install python3-tkinter

# Arch
sudo pacman -S tk
```

### "Permission denied" when saving

KosXER will ask to make the file writable. If that fails, check file ownership:

```bash
ls -la ~/.Xresources
# Fix ownership if needed:
sudo chown $USER:$USER ~/.Xresources
```

### Backups not being created

Check that the backup directory exists and is writable:

```bash
# Default backup location is same as original file
# Check permissions:
ls -la $(dirname ~/.Xresources)
```

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

KosXER is released under the MIT License. See [LICENSE](../LICENSE) for details.
