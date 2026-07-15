# Supported File Formats

KosXER supports various Unix/Linux configuration file formats. This document describes each format and how KosXER handles them.

## Table of Contents

- [X Resources (.Xresources, .Xdefaults)](#x-resources)
- [OpenBox Menu (menu.xml)](#openbox-menu)
- [OpenBox RC (rc.xml)](#openbox-rc)
- [Key-Value Files (.env, .conf)](#key-value-files)
- [Shell Configuration (.bashrc, .zshrc)](#shell-configuration)

---

## X Resources

**File Extensions:** `.Xresources`, `.Xdefaults`, `.Xresources-xft`

### Description

X Resources are used to configure X11 applications like XTerm, URxvt, and other X-based programs. They define appearance (colors, fonts) and behavior settings.

### Format

```
resource.class*subresource: value
```

### Examples

```
! Comments start with !
XTerm*background: black
XTerm*foreground: white
XTerm*faceName: Monospace
XTerm*faceSize: 10

! Wildcards
*background: #000000
*.color0: #000000
*.color1: #ff0000

! Preprocessor directives
#ifdef COLOR_SCHEME_DARK
XTerm*background: #000000
#else
XTerm*background: #ffffff
#endif
```

### KosXER Support

- **Tree View**: Hierarchical display of resource paths
- **Color Picker**: Click color values to open picker
- **Color Preview**: Color swatch shown next to hex values
- **Type Detection**: Automatically detects colors, fonts, booleans
- **Wildcard Support**: Handles `*` and `?` in resource paths
- **Preprocessor**: Preserves `#ifdef`, `#include` directives

### Common Resources

| Resource | Description | Typical Values |
|----------|-------------|--------------|
| `*background` | Background color | `#000000`, `black` |
| `*foreground` | Text color | `#ffffff`, `white` |
| `*font` | Font specification | `Monospace-10` |
| `*color0-15` | Terminal colors | Hex colors |

---

## OpenBox Menu

**File:** `menu.xml`

### Description

Defines the OpenBox right-click menu structure. Contains menus, items (applications), and separators.

### Format

```xml
<?xml version="1.0" encoding="UTF-8"?>
<openbox_menu xmlns="http://openbox.org/3.4/menu">
    <menu id="root-menu" label="Openbox 3">
        <item label="Terminal">
            <action name="Execute">
                <command>xterm</command>
            </action>
        </item>
        <separator/>
        <menu id="preferences-menu" label="Preferences">
            <item label="Openbox Configuration">
                <action name="Execute">
                    <command>obconf</command>
                </action>
            </item>
        </menu>
    </menu>
</openbox_menu>
```

### KosXER Support

- **Visual Editor**: Tree view of menu hierarchy
- **Drag & Drop**: Reorder items and menus
- **Property Editor**: Edit label, icon, action, command
- **Action Types**: Execute, Reconfigure, Restart, Exit, etc.
- **Menu Preview**: Text preview of menu structure

### Action Types

| Action | Description | Parameters |
|--------|-------------|------------|
| `Execute` | Run a command | `<command>` |
| `Reconfigure` | Reload OpenBox config | None |
| `Restart` | Restart OpenBox | None |
| `Exit` | Exit OpenBox | `<prompt>` |
| `ShowMenu` | Show another menu | `<menu>` |

---

## OpenBox RC

**File:** `rc.xml`

### Description

Main OpenBox configuration file. Defines themes, key bindings, mouse bindings, and window behavior.

### Format

```xml
<?xml version="1.0" encoding="UTF-8"?>
<openbox_config xmlns="http://openbox.org/3.4/rc">
    <theme>
        <name>Clearlooks</name>
    </theme>
    <keyboard>
        <keybind key="C-A-t">
            <action name="Execute">
                <command>xterm</command>
            </action>
        </keybind>
    </keyboard>
</openbox_config>
```

### KosXER Support

- **Theme Editor**: Modify theme settings
- **Key Binding Editor**: Visual key binding configuration
- **Application Rules**: Per-application settings

### Common Sections

| Section | Description |
|---------|-------------|
| `theme` | Visual appearance |
| `desktops` | Virtual desktop settings |
| `keyboard` | Key bindings |
| `mouse` | Mouse bindings |
| `applications` | Per-app rules |

---

## Key-Value Files

**Extensions:** `.env`, `.conf`, `.cfg`, `.rc`, `.ini`

### Description

Simple configuration files with `KEY=value` format. Used by many applications and shell scripts.

### Format

```
# Comment
KEY=value
ANOTHER_KEY="quoted value"
EXPORTED_VAR="value"
```

### KosXER Support

- **Two-Column Editor**: Key and value columns
- **Import/Export**: Merge with other files
- **Quote Handling**: Smart quote management
- **Search/Filter**: Find keys quickly

### Variations

| Type | Example | Notes |
|------|---------|-------|
| Environment | `.env` | Often no exports |
| Systemd | `/etc/sysctl.conf` | May need sudo |
| Application | `app.conf` | Custom formats |

---

## Shell Configuration

**Files:** `.bashrc`, `.bash_profile`, `.zshrc`, `.profile`

### Description

Shell startup files containing environment variables, aliases, and functions.

### Format

```bash
# Exports
export PATH="$HOME/bin:$PATH"
export EDITOR=vim

# Aliases
alias ll='ls -la'
alias grep='grep --color=auto'
```

### KosXER Support

- **Export Detection**: Shows which variables are exported
- **Value Editing**: Edit values preserving quotes
- **Safe Editing**: Avoids breaking shell syntax

### Important Notes

- **Order matters**: Files are loaded in specific order
- **Quote carefully**: Spaces in values need quotes
- **Test changes**: Use `source ~/.bashrc` to test

---

## Format Detection

KosXER automatically detects file formats based on:

1. **File extension** (e.g., `.Xresources`)
2. **Filename** (e.g., `menu.xml`)
3. **Content inspection** (for files without standard extensions)

If a format cannot be detected, KosXER will try to open it as a generic text file.

## Adding New Formats

To add support for a new format:

1. Create a parser in `parsers/`
2. Add editor widget in `gui/`
3. Register in `parsers/__init__.py`
4. Add documentation to this file

See the developer documentation for details.
