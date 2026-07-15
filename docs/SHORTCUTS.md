# Keyboard Shortcuts Reference

Complete list of keyboard shortcuts for KosXER.

## Global Shortcuts

These work anywhere in the application.

| Shortcut | Action |
|----------|--------|
| `Ctrl+N` | New file |
| `Ctrl+O` | Open file |
| `Ctrl+S` | Save current file |
| `Ctrl+Shift+S` | Save as |
| `Ctrl+W` | Close current tab |
| `Ctrl+Q` | Quit application |
| `Ctrl+B` | Toggle file browser |
| `F1` | Open help |

## Navigation

| Shortcut | Action |
|----------|--------|
| `Ctrl+Tab` | Next tab |
| `Ctrl+Shift+Tab` | Previous tab |
| `Alt+1-9` | Switch to tab 1-9 |
| `Ctrl+B` | Show/hide file browser |

## Editing (Global)

| Shortcut | Action |
|----------|--------|
| `Ctrl+Z` | Undo |
| `Ctrl+Y` | Redo |
| `Ctrl+Shift+Z` | Redo (alternative) |
| `Ctrl+X` | Cut |
| `Ctrl+C` | Copy |
| `Ctrl+V` | Paste |
| `Ctrl+A` | Select all |
| `Ctrl+F` | Find/Search |
| `Ctrl+H` | Replace |

## XResources Editor

| Shortcut | Action |
|----------|--------|
| `Double-click` | Edit value |
| `Enter` | Edit selected |
| `Delete` | Delete selected resource |
| `Ctrl+N` | Add new resource |
| `Ctrl+F` | Filter resources |

## OpenBox Menu Editor

| Shortcut | Action |
|----------|--------|
| `Double-click` | Edit item |
| `Delete` | Delete selected item |
| `Ctrl+N` | Add new item |
| `Ctrl+M` | Add new menu |
| `Ctrl+Up` | Move item up |
| `Ctrl+Down` | Move item down |
| `Ctrl+Left` | Move item out (unindent) |
| `Ctrl+Right` | Move item in (indent) |

## Key-Value Editor

| Shortcut | Action |
|----------|--------|
| `Double-click` | Edit value |
| `Enter` | Edit selected |
| `Delete` | Delete selected row |
| `Ctrl+N` | Add new row |
| `Ctrl+I` | Import from file |
| `Ctrl+E` | Export to file |
| `Ctrl+F` | Filter/search |

## File Browser

| Shortcut | Action |
|----------|--------|
| `Enter` | Open selected |
| `Backspace` | Go to parent directory |
| `F5` | Refresh |
| `Ctrl+D` | Add to bookmarks |
| `Right-click` | Context menu |

## Text Editors (if applicable)

| Shortcut | Action |
|----------|--------|
| `Ctrl+G` | Go to line |
| `Ctrl+/` | Toggle comment |
| `Tab` | Indent |
| `Shift+Tab` | Unindent |
| `Ctrl+Space` | Autocomplete (if available) |

## Dialog Shortcuts

| Shortcut | Action |
|----------|--------|
| `Enter` | Confirm/OK |
| `Escape` | Cancel |
| `Tab` | Next field |
| `Shift+Tab` | Previous field |

## Custom Shortcuts

You can customize shortcuts by editing the configuration file:

```bash
# Edit settings
nano ~/.config/kosxer/settings.json
```

Example customization:

```json
{
  "shortcuts": {
    "save": "Ctrl+S",
    "open": "Ctrl+O",
    "quit": "Ctrl+Q"
  }
}
```

## Tips

### Shortcut Conflicts

If a shortcut doesn't work, it may conflict with:
- Window manager shortcuts
- Desktop environment shortcuts
- Other applications

Check your window manager settings if shortcuts don't respond.

### Learning Shortcuts

- Hover over menu items to see their shortcuts
- Shortcuts are shown in the menu bar
- Most common: **Ctrl+O** (Open), **Ctrl+S** (Save)

### Accessibility

- All functions are accessible via menus
- Keyboard navigation works throughout the app
- Screen reader compatible (tkinter standard)

## Platform Differences

### macOS

On macOS, replace `Ctrl` with `Cmd`:

| Linux/Windows | macOS |
|---------------|-------|
| `Ctrl+O` | `Cmd+O` |
| `Ctrl+S` | `Cmd+S` |
| `Ctrl+Q` | `Cmd+Q` |

Note: KosXER currently focuses on Linux/X11 systems.
