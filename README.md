# KosXER - X11 Configuration Editor

A Python/tkinter GUI application for editing Unix/Linux configuration files including `.Xresources`, OpenBox `menu.xml` and `rc.xml`, KosDWM configs, and other key-value configuration formats.

## Features

- **Dual-pane layout**: File browser + tabbed editor
- **Multiple format support**:
  - `.Xresources` / `.Xdefaults` - X11 resource definitions with live apply
  - `menu.xml` / `rc.xml` - OpenBox configuration
  - KosDWM `config.json` and menu files
  - Generic key-value configs (`.conf`, `.env`, `.rc`, `.bashrc`, `.zshrc`)
- **Intelligent Presets** - Auto-detects resource types and suggests colors, fonts, booleans
- **Syntax-aware editing** with validation
- **Live XResources Apply** - Click "Apply" to reload resources without restart
- **XTerm Helper** - Launch new xterm with current resources + restart tips
- **Show/Hide Hidden Files** - Toggle in file browser (Ctrl+H)
- **Backup on save** - automatic `.bak` file creation
- **Search and filter** capabilities
- **Recent files** history
- **Auto-versioning** - Version increments on every git commit

## Installation

```bash
# Clone the repository
git clone https://github.com/m5it/kosxer.git
cd kosxer

# Install dependencies
pip install -r requirements.txt

# Setup git hook for auto-versioning (optional)
chmod +x .git/hooks/pre-commit

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

# Check version
python AUTOVERSION.py --show
```

## Project Structure

```
KosXER/
├── AUTOVERSION.py      # Single source of truth for version
├── config/             # Configuration settings
│   ├── constants.py
│   ├── presets.py      # Known values database
│   ├── settings.py
│   └── VERSION
├── gui/                # UI components and widgets
│   ├── editor_base.py
│   ├── file_browser.py
│   ├── xresources_editor.py
│   ├── openbox_editor.py
│   ├── kv_editor.py
│   ├── kosdwm_config_editor.py
│   └── kosdwm_menu_editor.py
├── parsers/            # File format parsers
│   ├── __init__.py
│   ├── xresources_parser.py
│   ├── openbox_parser.py
│   ├── keyvalue_parser.py
│   └── kosdwm_parser.py
├── utils/              # Utility functions
│   └── backup.py
├── main.py             # Application entry point
├── requirements.txt    # Python dependencies
└── CHANGELOG.md        # Version history
```

## Supported File Formats

| Format | Extension | Features |
|--------|-----------|----------|
| X Resources | `.Xresources`, `.Xdefaults` | Preprocessor directives, wildcards, colors, **Apply button**, **Intelligent Presets** |
| OpenBox Menu | `menu.xml` | Nested menus, actions, icons |
| OpenBox RC | `rc.xml` | Keybindings, themes, settings |
| KosDWM Config | `config.json` | JSON-based DWM configuration |
| KosDWM Menu | `menu.json` | Application menu definitions |
| Generic Config | `.conf`, `.rc`, `.env` | Sections, key-value pairs, shell exports |

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+O` | Open file |
| `Ctrl+S` | Save |
| `Ctrl+Shift+S` | Save as |
| `Ctrl+W` | Close tab |
| `Ctrl+Q` | Quit |
| `Ctrl+B` | Toggle file browser |
| `Ctrl+H` | Toggle hidden files |
| `F5` | Refresh file browser |
| `Ctrl+Z` | Undo |
| `Ctrl+Y` | Redo |

## Intelligent Presets

KosXER automatically detects resource types and suggests appropriate values:

### How It Works

When you double-click a resource to edit, KosXER analyzes the resource name:

| Resource Pattern | Detected Type | Editor Shown |
|------------------|---------------|--------------|
| `*color*`, `*background`, `*foreground` | Color | Color picker + preset palette |
| `*font*`, `*face*` | Font | Font dropdown with presets |
| `*scroll*`, `*bell*`, `*bold*` | Boolean | True/False dropdown |
| Others | Generic | Text editor with preset picker |

### Using Presets

1. **Double-click** any resource to edit
2. For colors: See color picker + quick presets (White, Black, Red, etc.)
3. For fonts: Choose from common monospace fonts
4. For booleans: Select true/false/yes/no/on/off
5. Or use **"Insert Preset"** button for full preset browser

### Preset Categories

- **Colors** 🎨 - 16 terminal colors + common colors
- **Fonts** 🔤 - xft fonts (Monospace, DejaVu, Source Code Pro, etc.)
- **Booleans** ☑️ - true/false, yes/no, on/off, 1/0
- **XTerm** 💻 - Common xterm resource values

## XResources Live Apply

Edit your `.Xresources` and apply changes **without logging out**:

1. Open `~/.Xresources`
2. Edit colors or values
3. **Save** (Ctrl+S)
4. Click **"Apply (xrdb)"** button
5. Changes take effect immediately!

The Apply button runs `xrdb -merge ~/.Xresources` and shows success/error messages.

## XTerm Color Reference

Standard terminal color palette (color0-color15):

| Color | Hex Value | Usage |
|-------|-----------|-------|
| color0 | `#000000` | Black |
| color1 | `#ff0000` | Red |
| color2 | `#00ff00` | Green |
| color3 | `#ffff00` | Yellow |
| color4 | `#0000ff` | Blue |
| color5 | `#ff00ff` | Magenta |
| color6 | `#00ffff` | Cyan |
| **color7** | **`#ffffff`** | **White** |
| color8 | `#808080` | Bright Black |
| color9 | `#ff5555` | Bright Red |
| color10 | `#55ff55` | Bright Green |
| color11 | `#ffff55` | Bright Yellow |
| color12 | `#5555ff` | Bright Blue |
| color13 | `#ff55ff` | Bright Magenta |
| color14 | `#55ffff` | Bright Cyan |
| **color15** | **`#ffffff`** | **Bright White** |

### Common XTerm White Background Examples

```bash
# Pure white background with black text
XTerm*background: #ffffff
XTerm*foreground: #000000

# Off-white background
XTerm*background: #f0f0f0
XTerm*foreground: #000000

# Using color7 (white)
XTerm*background: color7
XTerm*foreground: color0
```

## XTerm Helper

KosXER includes special buttons to help with xterm:

- **"New XTerm"** - Launches fresh xterm with current resources applied
- **"XTerm Tips"** - Shows help dialog explaining restart behavior

### Why xterm Needs Restart

**Important:** `xrdb -merge` only affects **NEW** xterm windows!

- Running xterm instances keep their old resources
- Changes only appear in windows opened AFTER applying
- Use **"New XTerm"** button to see changes immediately

## Auto-Versioning

KosXER uses `AUTOVERSION.py` as the single source of truth:

- Version is defined once in `AUTOVERSION.py`
- Git pre-commit hook auto-increments version (1.0.0 → 1.0.1)
- Version displayed in window title and About dialog
- Import anywhere: `from AUTOVERSION import VERSION`

```bash
# Check current version
python AUTOVERSION.py --show

# Manual version bump
python AUTOVERSION.py
```

## File Browser Features

- **Quick Access** panel for common config locations
- **Show/Hide Hidden Files** toggle (checkbox + Ctrl+H)
- **File System** tree view with navigation
- **Filter** by file type (only shows supported configs)
- Double-click to open files

## Troubleshooting

### Changes Don't Appear in xterm

**Problem:** Applied resources but xterm looks the same

**Solution:**
1. Click **"New XTerm"** button to launch fresh window
2. Or close all xterm windows and reopen them
3. Remember: `xrdb -merge` only affects NEW windows

### xrdb Command Not Found

**Problem:** "xrdb not found" error when applying

**Solution:**
```bash
# Install x11-xserver-utils (contains xrdb)
sudo apt-get install x11-xserver-utils   # Debian/Ubuntu
sudo yum install xorg-x11-xutils         # RHEL/CentOS
```

### White Background Not Working

**Problem:** Set white background but xterm still dark

**Solution:**
```bash
# Check if resource is being overridden
xrdb -query | grep -i background

# Use specific resource path
echo "XTerm*background: #ffffff" | xrdb -merge
```

## Development

```bash
# Run tests
python -m pytest parsers/

# Test specific parser
python parsers/test_xresources.py
python parsers/test_openbox.py
python parsers/test_keyvalue.py

# Check code style
flake8 parsers/ gui/ --max-line-length=100
```

## Requirements

- Python 3.8+
- tkinter (usually included with Python)
- watchdog (optional, for file watching)
- lxml (for XML parsing)

```bash
pip install -r requirements.txt
```

## License

MIT License - See LICENSE file for details.

## Contributing

Contributions welcome! Please submit pull requests or open issues for bugs and feature requests.

### Feature Ideas

- [ ] Syntax highlighting in editors
- [ ] Live preview for colors
- [ ] Import/export themes
- [ ] Plugin system for custom parsers
- [ ] Dark/light theme toggle

---

**Current Version:** Import from `AUTOVERSION.py`
