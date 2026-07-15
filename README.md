# KosXER - X11 Configuration Editor

A Python/tkinter GUI application for editing Unix/Linux configuration files including `.Xresources`, OpenBox `menu.xml` and `rc.xml`, and other key-value configuration formats.

## Features

- **Dual-pane layout**: Tree navigation + editor
- **Multiple format support**:
  - `.Xresources` / `.Xdefaults` - X11 resource definitions
  - `menu.xml` - OpenBox application menus
  - `rc.xml` - OpenBox window manager configuration
  - Generic key-value configs (tint2, compton, etc.)
- **Syntax-aware editing** with validation
- **Backup on save** - automatic `.bak` file creation
- **Search and filter** capabilities
- **Recent files** history
- **Live preview** of changes

## Installation

```bash
# Clone the repository
git clone https://github.com/m5it/kosxer.git
cd kosxer

# Install dependencies
pip install -r requirements.txt

# Run the application
python main.py
```

## Usage

```bash
# Launch with default empty workspace
python main.py

# Open specific file
python main.py ~/.Xresources

# Open OpenBox menu
python main.py ~/.config/openbox/menu.xml
```

## Project Structure

```
KosXER/
├── config/           # Configuration settings
├── gui/             # UI components and widgets
├── parsers/         # File format parsers
│   ├── xresources_parser.py
│   ├── openbox_parser.py
│   └── keyvalue_parser.py
├── utils/           # Utility functions
├── main.py          # Application entry point
└── requirements.txt # Python dependencies
```

## Supported File Formats

| Format | Extension | Features |
|--------|-----------|----------|
| X Resources | `.Xresources`, `.Xdefaults` | Preprocessor directives, wildcards, comments |
| OpenBox Menu | `menu.xml` | Nested menus, actions, icons |
| OpenBox RC | `rc.xml` | Keybindings, themes, settings |
| Generic Config | `.conf`, `.rc` | Sections, key-value pairs |

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+O` | Open file |
| `Ctrl+S` | Save |
| `Ctrl+Shift+S` | Save as |
| `Ctrl+F` | Find |
| `Ctrl+Q` | Quit |
| `Ctrl+Z` | Undo |
| `Ctrl+Y` | Redo |

## Development

```bash
# Run tests
python -m pytest parsers/

# Test specific parser
python parsers/test_xresources.py
python parsers/test_openbox.py
```

## License

MIT License - See LICENSE file for details.

## Contributing

Contributions welcome! Please submit pull requests or open issues for bugs and feature requests.
