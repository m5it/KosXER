#!/usr/bin/env python3
"""
XResources Editor Widget for KosXER

Treeview-based editor for .Xresources and .Xdefaults files.
Includes Apply button to reload resources with xrdb, preset picker, and user presets.
"""

import tkinter as tk
from tkinter import ttk, colorchooser, messagebox, simpledialog
import re
import subprocess
import os
from typing import Optional, List

from gui.editor_base import EditorWidget
from parsers.xresources_parser import XResourcesParser, XResourceEntry
from config.presets import (
    get_presets_for_resource, get_all_presets, XTERM_COLORS,
    add_user_preset, delete_user_preset, get_user_presets_list,
    load_user_presets, USER_PRESETS_FILE
)


class XResourcesEditor(EditorWidget):
    """Editor widget for XResources files."""
    
    COLOR_HEX_PATTERN = re.compile(r'^#[0-9a-fA-F]{6}$')
    COLOR_RGB_PATTERN = re.compile(r'^rgb:([0-9a-fA-F]{2,4})/([0-9a-fA-F]{2,4})/([0-9a-fA-F]{2,4})$')
    
    def __init__(self, parent, main_window=None, filepath: Optional[str] = None, **kwargs):
        self.parser = XResourcesParser()
        self.entries: List[XResourceEntry] = []
        self.filtered_entries: List[XResourceEntry] = []
        self._dialog_open = False
        self._delete_in_progress = False
        super().__init__(parent, main_window, filepath, **kwargs)
    
    def _create_editor_widgets(self):
        """Create the XResources editor UI."""
        # Filter frame
        filter_frame = ttk.Frame(self.editor_frame)
        filter_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(filter_frame, text="Filter:").pack(side=tk.LEFT, padx=5)
        self.filter_var = tk.StringVar()
        self.filter_var.trace('w', self._on_filter_changed)
        ttk.Entry(filter_frame, textvariable=self.filter_var, width=30).pack(side=tk.LEFT, padx=5)
        ttk.Button(filter_frame, text="Clear", command=self._clear_filter).pack(side=tk.LEFT, padx=5)
        
        # Treeview
        tree_frame = ttk.Frame(self.editor_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        columns = ('resource', 'value', 'type', 'preview')
        self.tree = ttk.Treeview(tree_frame, columns=columns, show='headings')
        
        self.tree.heading('resource', text='Resource Path')
        self.tree.heading('value', text='Value')
        self.tree.heading('type', text='Type')
        self.tree.heading('preview', text='Preview')
        
        self.tree.column('resource', width=300)
        self.tree.column('value', width=250)
        self.tree.column('type', width=100)
        self.tree.column('preview', width=50)
        
        y_scroll = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
        x_scroll = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=y_scroll.set, xscrollcommand=x_scroll.set)
        
        y_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        x_scroll.pack(side=tk.BOTTOM, fill=tk.X)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Buttons
        btn_frame = ttk.Frame(self.editor_frame)
        btn_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(btn_frame, text="Add Resource", command=self._add_resource).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Delete Selected", command=self._delete_selected).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Insert Preset", command=self._show_preset_picker).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="My Presets", command=self._manage_user_presets).pack(side=tk.LEFT, padx=5)
        
        ttk.Separator(btn_frame, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=10)
        ttk.Button(btn_frame, text="New XTerm", command=self._launch_new_xterm).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="XTerm Tips", command=self._show_xterm_tips).pack(side=tk.LEFT, padx=5)
        
        self.apply_btn = ttk.Button(btn_frame, text="Apply (xrdb)", command=self._apply_resources, 
                                    state=tk.DISABLED)
        self.apply_btn.pack(side=tk.RIGHT, padx=5)
        
        # Info label
        info_frame = ttk.Frame(self.editor_frame)
        info_frame.pack(fill=tk.X, padx=5, pady=2)
        self.info_label = ttk.Label(info_frame, text="💡 Tip: xterm needs restart to see changes. Use 'New XTerm' or close/reopen.", 
                                   foreground="gray", font=('Helvetica', 9, 'italic'))
        self.info_label.pack(side=tk.LEFT)
        
        # Bindings
        self.tree.bind('<Double-1>', self._on_double_click)
        self.tree.bind('<Delete>', lambda e: self._delete_selected())
    
    def _detect_resource_type(self, resource_path: str) -> str:
        """Detect resource type from resource path name."""
        if not resource_path:
            return 'generic'
        
        path_lower = resource_path.lower()
        
        color_patterns = ['color', 'background', 'foreground', 'cursorcolor', 
                       'bordercolor', 'highlightcolor', 'troughcolor']
        if any(p in path_lower for p in color_patterns):
            return 'color'
        
        font_patterns = ['font', 'face', 'facename']
        if any(p in path_lower for p in font_patterns):
            return 'font'
        
        bool_patterns = ['shell', 'video', 'scroll', 'bell', 'bold', 'allow', 
                        'blink', 'underline', 'active', 'enabled', 'visible',
                        'reverse', 'iconic', 'hold', 'utmp']
        if any(p in path_lower for p in bool_patterns):
            return 'boolean'
        
        num_patterns = ['lines', 'chars', 'pixels', 'width', 'height', 'size',
                       'borderwidth', 'margin', 'padding', 'timeout', 'interval']
        if any(p in path_lower for p in num_patterns):
            return 'number'
        
        return 'generic'
    
    def _launch_new_xterm(self):
        """Launch a new xterm instance with current XResources."""
        try:
            if self.filepath and os.path.exists(self.filepath):
                subprocess.run(['xrdb', '-merge', self.filepath], check=True, capture_output=True)
            subprocess.Popen(['xterm'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            self.set_status("✓ Launched new xterm with current resources")
        except FileNotFoundError:
            try:
                subprocess.Popen(['uxterm'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                self.set_status("✓ Launched new uxterm with current resources")
            except FileNotFoundError:
                messagebox.showerror("xterm Not Found", "Neither 'xterm' nor 'uxterm' found.")
        except subprocess.CalledProcessError as e:
            messagebox.showerror("Error", f"Failed to apply resources: {e}")
    
    def _show_xterm_tips(self):
        """Show dialog explaining xterm restart behavior."""
        tips_text = """XTerm Resource Loading - How It Works

Why don't my changes appear immediately?

1. xrdb -merge loads resources into the X server
2. Running xterm instances keep their OLD resources
3. Only NEW xterm windows see the changes

Solutions:

✓ Use "New XTerm" button - launches fresh xterm with current resources
✓ Close and reopen xterm
✓ Start xterm with specific file: xterm -xrm "*background: #ffffff"

Remember: Save → Apply → New XTerm to see changes!"""
        
        dialog = tk.Toplevel(self)
        dialog.title("XTerm Tips")
        dialog.transient(self)
        dialog.geometry("500x450")
        
        text = tk.Text(dialog, wrap=tk.WORD, padx=10, pady=10, font=('Courier', 10))
        text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        text.insert('1.0', tips_text)
        text.config(state=tk.DISABLED)
        
        ttk.Button(dialog, text="Close", command=dialog.destroy).pack(pady=5)
    
    def _get_value_type(self, value: str) -> str:
        """Determine value type from value string."""
        value = value.strip().lower()
        
        if self.COLOR_HEX_PATTERN.match(value) or self.COLOR_RGB_PATTERN.match(value):
            return 'color'
        if value in ['true', 'false', 'yes', 'no', 'on', 'off']:
            return 'boolean'
        if 'font' in value or value.startswith('xft:') or value.startswith('-*-'):
            return 'font'
        
        try:
            int(value)
            return 'number'
        except ValueError:
            try:
                float(value)
                return 'number'
            except ValueError:
                pass
        
        return 'string'
    
    def _get_color_preview(self, value: str) -> str:
        """Get color for preview."""
        if self.COLOR_HEX_PATTERN.match(value):
            return value
        return ''
    
    def _populate_tree(self):
        """Populate treeview with entries."""
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        for entry in self.filtered_entries:
            value_type = self._get_value_type(entry.value)
            preview = self._get_color_preview(entry.value) if value_type == 'color' else ''
            
            item_id = self.tree.insert('', 'end', values=(
                entry.resource_path,
                entry.value,
                value_type,
                preview
            ))
            
            if preview:
                self.tree.item(item_id, tags=(preview,))
                self.tree.tag_configure(preview, background=preview)
    
    def _on_filter_changed(self, *args):
        """Apply filter."""
        filter_text = self.filter_var.get().lower()
        
        if not filter_text:
            self.filtered_entries = self.entries[:]
        else:
            self.filtered_entries = [
                e for e in self.entries 
                if filter_text in e.resource_path.lower() or filter_text in e.value.lower()
            ]
        
        self._populate_tree()
    
    def _clear_filter(self):
        """Clear filter."""
        self.filter_var.set('')
        self.filtered_entries = self.entries[:]
        self._populate_tree()
    
    def _on_double_click(self, event):
        """Handle double click for editing."""
        selection = self.tree.selection()
        if not selection:
            return
        
        item = selection[0]
        values = self.tree.item(item, 'values')
        if not values:
            return
        
        resource_path, current_value, value_type, _ = values
        detected_type = self._detect_resource_type(resource_path)
        
        if detected_type == 'color' or value_type == 'color':
            self._edit_color_with_presets(resource_path, current_value)
        elif detected_type == 'font':
            self._edit_with_presets(resource_path, current_value, 'font')
        elif detected_type == 'boolean':
            self._edit_with_presets(resource_path, current_value, 'boolean')
        else:
            self._edit_generic(resource_path, current_value)
    
    def _setup_dropdown_accessibility(self, combobox, dialog, tooltip_text):
        """Setup keyboard navigation and tooltips for dropdown."""
        # Alt+Down to open dropdown
        combobox.bind('<Alt-Down>', lambda e: combobox.event_generate('<Down>'))
        
        # Enter to accept and move to next field
        def on_enter(event):
            combobox.selection_clear()
            event.widget.tk_focusNext().focus_set()
            return 'break'
        
        combobox.bind('<Return>', on_enter)
        
        # Escape to close dropdown
        def on_escape(event):
            combobox.selection_clear()
            dialog.focus_set()
            return 'break'
        
        combobox.bind('<Escape>', on_escape)
        
        # Tab navigation
        def on_tab(event):
            combobox.selection_clear()
        
        combobox.bind('<Tab>', on_tab)
        combobox.bind('<Shift-Tab>', on_tab)
        
        # Tooltip
        def show_tooltip(event):
            self._tooltip = tk.Toplevel(combobox)
            self._tooltip.wm_overrideredirect(True)
            self._tooltip.attributes('-topmost', True)
            x = event.x_root
            y = event.y_root - 30
            self._tooltip.wm_geometry(f"+{x}+{y}")
            label = ttk.Label(self._tooltip, text=tooltip_text, background="#ffffe0", 
                            relief=tk.SOLID, borderwidth=1, padding=5, font=('Helvetica', 9))
            label.pack()
        
        def hide_tooltip(event):
            if hasattr(self, '_tooltip') and self._tooltip:
                self._tooltip.destroy()
                self._tooltip = None
        
        combobox.bind('<Enter>', show_tooltip)
        combobox.bind('<Leave>', hide_tooltip)
    
    def _edit_generic(self, resource_path: str, current_value: str):
        """Edit value with intelligent dropdown."""
        dialog = tk.Toplevel(self)
        dialog.title(f"Edit Resource - {resource_path}")
        dialog.transient(self)
        dialog.grab_set()
        dialog.geometry("550x450")
        
        from config.presets import XTERM_SPECIFIC
        
        # Resource Path section
        path_frame = ttk.LabelFrame(dialog, text="Resource Path", padding=10)
        path_frame.pack(fill=tk.X, padx=10, pady=5)
        
        common_paths = [
            'XTerm*background', 'XTerm*foreground', 'XTerm*cursorColor',
            'XTerm*font', '*.background', '*.foreground',
            '*.color0', '*.color1', '*.color2', '*.color3',
            '*.color4', '*.color5', '*.color6', '*.color7',
        ] + sorted([k for k in XTERM_SPECIFIC.keys()])[:50]
        
        path_var = tk.StringVar(value=resource_path)
        path_combo = ttk.Combobox(path_frame, textvariable=path_var, values=common_paths, width=50)
        path_combo.pack(fill=tk.X, pady=2)
        
        self._setup_dropdown_accessibility(path_combo, dialog, 
            "Alt+Down: Open list  |  ↑/↓: Navigate  |  Enter: Select  |  Tab: Next field  |  Esc: Close")
        
        type_label = ttk.Label(path_frame, text="", foreground="gray")
        type_label.pack(anchor=tk.W, pady=2)
        
        def update_path_type(*args):
            path = path_var.get()
            res_type = self._detect_resource_type(path)
            type_icons = {'color': '🎨 Color', 'font': '🔤 Font', 'boolean': '☑️ Boolean', 
                        'number': '🔢 Number', 'generic': '⚙️ Generic'}
            type_label.config(text=f"Type: {type_icons.get(res_type, res_type)}")
        
        path_var.trace('w', update_path_type)
        update_path_type()
        
        # Value section
        value_frame = ttk.LabelFrame(dialog, text="Value", padding=10)
        value_frame.pack(fill=tk.X, padx=10, pady=5)
        
        value_input_frame = ttk.Frame(value_frame)
        value_input_frame.pack(fill=tk.X, pady=2)
        
        value_var = tk.StringVar(value=current_value)
        value_combo = ttk.Combobox(value_input_frame, textvariable=value_var, width=40)
        value_combo.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        self._setup_dropdown_accessibility(value_combo, dialog,
            "Alt+Down: Open suggestions  |  ↑/↓: Navigate  |  Enter: Select  |  Tab: Next  |  Esc: Close")
        
        color_picker_btn = ttk.Button(value_input_frame, text="🎨 Pick...", width=10)
        color_picker_btn.pack(side=tk.RIGHT, padx=5)
        color_picker_btn.pack_forget()
        
        preview_frame = ttk.Frame(value_frame)
        preview_frame.pack(fill=tk.X, pady=5)
        
        color_preview_label = ttk.Label(preview_frame, text="Preview:")
        color_preview_label.pack(side=tk.LEFT)
        
        color_preview = tk.Label(preview_frame, text="   ", bg='#808080', relief=tk.RIDGE, bd=2, width=4, height=2)
        color_preview.pack(side=tk.LEFT, padx=5)
        color_preview.pack_forget()
        
        format_label = ttk.Label(value_frame, text="", foreground="gray", font=('Helvetica', 9))
        format_label.pack(anchor=tk.W)
        
        def update_value_suggestions(*args):
            path = path_var.get()
            res_type = self._detect_resource_type(path)
            
            presets = get_presets_for_resource(path)
            values = []
            
            if presets and 'values' in presets:
                values = [str(v) for v in presets['values']][:50]
            elif res_type == 'color':
                values = [f"{name}: {hex_val}" for name, hex_val in XTERM_COLORS.items()]
                color_picker_btn.pack(side=tk.RIGHT, padx=5)
                color_preview_label.pack(side=tk.LEFT)
                color_preview.pack(side=tk.LEFT, padx=5)
                format_label.config(text="Formats: #ffffff or rgb:ff/ff/ff")
            elif res_type == 'font':
                from config.presets import COMMON_FONTS
                values = COMMON_FONTS
                format_label.config(text="Enter font name or select from list")
            elif res_type == 'boolean':
                from config.presets import ALL_BOOLEAN_VALUES
                values = ALL_BOOLEAN_VALUES
                format_label.config(text="true/false, yes/no, on/off, 1/0")
            
            value_combo['values'] = values
            
            if res_type != 'color':
                color_picker_btn.pack_forget()
                color_preview.pack_forget()
                color_preview_label.pack_forget()
                if res_type not in ['font', 'boolean']:
                    format_label.config(text="")
        
        def on_value_changed(*args):
            value = value_var.get()
            hex_color = self._extract_hex_color(value)
            if hex_color:
                color_preview.config(bg=hex_color)
        
        path_var.trace('w', update_value_suggestions)
        value_var.trace('w', on_value_changed)
        update_value_suggestions()
        
        def pick_color():
            current = value_var.get()
            initial = self._extract_hex_color(current) or '#808080'
            color = colorchooser.askcolor(initialcolor=initial, title="Choose Color")
            if color and color[1]:
                value_var.set(color[1])
        
        color_picker_btn.config(command=pick_color)
        
        def save_as_preset():
            name = simpledialog.askstring("Save Preset", "Enter preset name:", parent=dialog)
            if name:
                if add_user_preset(name, value_var.get()):
                    messagebox.showinfo("Success", f"Saved '{name}' to My Presets", parent=dialog)
                else:
                    messagebox.showerror("Error", "Failed to save preset", parent=dialog)
        
        ttk.Button(dialog, text="⭐ Save as Preset", command=save_as_preset).pack(pady=10)
        
        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(pady=10)
        
        def on_ok():
            new_path = path_var.get().strip()
            new_value = value_var.get().strip()
            
            if not new_path or not new_value:
                messagebox.showerror("Error", "Path and value are required")
                return
            
            if new_path != resource_path:
                self.parser.remove_entry(resource_path)
                self.entries = [e for e in self.entries if e.resource_path != resource_path]
                entry = self.parser.add_entry(new_path, new_value)
                self.entries.append(entry)
            else:
                self._update_entry(resource_path, new_value)
            
            self.mark_dirty(True)
            self._on_filter_changed()
            dialog.destroy()
        
        ttk.Button(btn_frame, text="OK", command=on_ok).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Cancel", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
    
    def _extract_hex_color(self, value: str) -> Optional[str]:
        """Extract hex color from value string."""
        if not value:
            return None
        hex_match = re.search(r'#[0-9a-fA-F]{6}', value)
        if hex_match:
            return hex_match.group()
        rgb_match = self.COLOR_RGB_PATTERN.match(value)
        if rgb_match:
            r, g, b = rgb_match.groups()
            return f"#{r[:2]}{g[:2]}{b[:2]}"
        return None
    
    def _edit_color_with_presets(self, resource_path: str, current_value: str):
        """Edit color with color picker."""
        dialog = tk.Toplevel(self)
        dialog.title(f"Edit Color - {resource_path}")
        dialog.transient(self)
        dialog.grab_set()
        dialog.geometry("400x550")
        
        ttk.Label(dialog, text="Current Value:", font=('Helvetica', 10, 'bold')).pack(pady=5)
        current_var = tk.StringVar(value=current_value)
        ttk.Entry(dialog, textvariable=current_var, width=40, state='readonly').pack(padx=10, pady=5)
        
        preview_frame = ttk.Frame(dialog, width=100, height=50)
        preview_frame.pack(pady=10)
        preview_frame.pack_propagate(False)
        
        preview_label = tk.Label(preview_frame, text="Preview", 
                                bg=current_value if self.COLOR_HEX_PATTERN.match(current_value) else 'gray')
        preview_label.pack(fill=tk.BOTH, expand=True)
        
        def pick_color():
            initial = current_var.get()
            hex_color = self._extract_hex_color(initial)
            if hex_color:
                initial = hex_color
            color = colorchooser.askcolor(initialcolor=initial, title="Choose Color")
            if color and color[1]:
                current_var.set(color[1])
                preview_label.config(bg=color[1])
        
        ttk.Button(dialog, text="🎨 Pick Color", command=pick_color).pack(pady=5)
        
        ttk.Label(dialog, text="Quick Presets:", font=('Helvetica', 9)).pack(pady=5)
        presets_frame = ttk.Frame(dialog)
        presets_frame.pack(pady=5)
        
        common_colors = [
            ('White', '#ffffff'), ('Black', '#000000'),
            ('Red', '#ff0000'), ('Green', '#00ff00'), ('Blue', '#0000ff'),
            ('Yellow', '#ffff00'), ('Cyan', '#00ffff'), ('Magenta', '#ff00ff'),
            ('Gray', '#808080'), ('Orange', '#ffa500'), ('Purple', '#800080'),
        ]
        
        for name, hex_val in common_colors:
            btn = tk.Button(presets_frame, text=name, bg=hex_val, width=8,
                          command=lambda v=hex_val: (current_var.set(v), preview_label.config(bg=v)))
            btn.pack(side=tk.LEFT, padx=2, pady=2)
        
        presets = get_all_presets()
        if 'color' in presets and presets['color']['items']:
            ttk.Label(dialog, text="My Presets:", font=('Helvetica', 9)).pack(pady=5)
            user_frame = ttk.Frame(dialog)
            user_frame.pack(pady=5)
            for name, val in presets['color']['items'][:6]:
                btn = ttk.Button(user_frame, text=name, width=10,
                               command=lambda v=val: (current_var.set(v), preview_label.config(bg=v)))
                btn.pack(side=tk.LEFT, padx=2, pady=2)
        
        def save_as_preset():
            name = simpledialog.askstring("Save Preset", "Enter preset name:", parent=dialog)
            if name:
                if add_user_preset(name, current_var.get()):
                    messagebox.showinfo("Success", f"Saved '{name}' to My Presets", parent=dialog)
        
        ttk.Button(dialog, text="⭐ Save as Preset", command=save_as_preset).pack(pady=10)
        
        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(pady=10)
        
        def on_ok():
            new_value = current_var.get().strip()
            if new_value:
                self._update_entry(resource_path, new_value)
                self.mark_dirty(True)
                self._on_filter_changed()
                dialog.destroy()
        
        ttk.Button(btn_frame, text="OK", command=on_ok).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Cancel", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
    
    def _edit_with_presets(self, resource_path: str, current_value: str, preset_type: str):
        """Edit with presets for fonts/booleans."""
        dialog = tk.Toplevel(self)
        dialog.title(f"Edit {preset_type.title()} - {resource_path}")
        dialog.transient(self)
        dialog.grab_set()
        dialog.geometry("550x400")
        
        from config.presets import XTERM_SPECIFIC
        
        path_frame = ttk.LabelFrame(dialog, text="Resource Path", padding=10)
        path_frame.pack(fill=tk.X, padx=10, pady=5)
        
        if preset_type == 'font':
            relevant_paths = [k for k in XTERM_SPECIFIC.keys() if 'font' in k.lower() or 'face' in k.lower()]
        elif preset_type == 'boolean':
            bool_patterns = ['shell', 'scroll', 'bell', 'bold', 'allow', 'blink', 'video']
            relevant_paths = [k for k in XTERM_SPECIFIC.keys() if any(b in k.lower() for b in bool_patterns)]
        else:
            relevant_paths = list(XTERM_SPECIFIC.keys())[:30]
        
        common_paths = ['XTerm*background', 'XTerm*foreground', 'XTerm*cursorColor', 'XTerm*font'] + sorted(relevant_paths)[:40]
        
        path_var = tk.StringVar(value=resource_path)
        path_combo = ttk.Combobox(path_frame, textvariable=path_var, values=common_paths, width=50)
        path_combo.pack(fill=tk.X, pady=2)
        
        self._setup_dropdown_accessibility(path_combo, dialog,
            "Alt+Down: Open list  |  ↑/↓: Navigate  |  Enter: Select  |  Tab: Next  |  Esc: Close")
        
        ttk.Label(path_frame, text=f"Type: {preset_type.title()}", foreground="gray").pack(anchor=tk.W, pady=2)
        
        value_frame = ttk.LabelFrame(dialog, text="Value", padding=10)
        value_frame.pack(fill=tk.X, padx=10, pady=5)
        
        value_input_frame = ttk.Frame(value_frame)
        value_input_frame.pack(fill=tk.X, pady=2)
        
        value_var = tk.StringVar(value=current_value)
        value_combo = ttk.Combobox(value_input_frame, textvariable=value_var, width=45)
        value_combo.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        self._setup_dropdown_accessibility(value_combo, dialog,
            "Alt+Down: Open suggestions  |  ↑/↓: Navigate  |  Enter: Select  |  Tab: Next  |  Esc: Close")
        
        presets = get_all_presets()
        if preset_type in presets:
            preset_values = [val for name, val in presets[preset_type]['items']]
            value_combo['values'] = preset_values
        
        if preset_type == 'font':
            ttk.Label(value_frame, text="Enter font name or select from presets", foreground="gray").pack(anchor=tk.W)
        elif preset_type == 'boolean':
            ttk.Label(value_frame, text="true/false, yes/no, on/off, 1/0", foreground="gray").pack(anchor=tk.W)
        
        def save_as_preset():
            name = simpledialog.askstring("Save Preset", "Enter preset name:", parent=dialog)
            if name:
                if add_user_preset(name, value_var.get()):
                    messagebox.showinfo("Success", f"Saved '{name}' to My Presets", parent=dialog)
        
        ttk.Button(dialog, text="⭐ Save as Preset", command=save_as_preset).pack(pady=10)
        
        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(pady=10)
        
        def on_ok():
            new_path = path_var.get().strip()
            new_value = value_var.get().strip()
            
            if not new_path or not new_value:
                messagebox.showerror("Error", "Path and value are required")
                return
            
            if new_path != resource_path:
                self.parser.remove_entry(resource_path)
                self.entries = [e for e in self.entries if e.resource_path != resource_path]
                entry = self.parser.add_entry(new_path, new_value)
                self.entries.append(entry)
            else:
                self._update_entry(resource_path, new_value)
            
            self.mark_dirty(True)
            self._on_filter_changed()
            dialog.destroy()
        
        ttk.Button(btn_frame, text="OK", command=on_ok).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Cancel", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
    
    def _add_resource(self):
        """Add new resource with dropdown functionality."""
        if self._dialog_open:
            return
        self._dialog_open = True
        
        dialog = tk.Toplevel(self)
        dialog.title("Add Resource")
        dialog.transient(self)
        dialog.grab_set()
        dialog.protocol("WM_DELETE_WINDOW", lambda: self._close_dialog(dialog))
        dialog.geometry("550x520")
        
        from config.presets import XTERM_SPECIFIC
        
        def get_grouped_paths():
            """Group resource paths by category."""
            grouped = []
            type_icons = {'color': '🎨', 'font': '🔤', 'boolean': '☑️', 'number': '🔢', 'generic': '⚙️'}
            
            def get_icon(path):
                res_type = self._detect_resource_type(path)
                return type_icons.get(res_type, '⚙️')
            
            # Most Common
            common = ['XTerm*background', 'XTerm*foreground', 'XTerm*cursorColor', 'XTerm*font', '*.background', '*.foreground']
            grouped.append('⭐ Most Common')
            grouped.extend([f"{get_icon(p)} {p}" for p in common])
            
            # Colors
            color_paths = sorted([k for k in XTERM_SPECIFIC.keys() 
                                if 'color' in k.lower() or 'ground' in k.lower() or 'cursor' in k.lower()])
            if color_paths:
                grouped.append('── 🎨 Colors ──')
                grouped.extend([f"🎨 {p}" for p in sorted(color_paths)])
            
            # Fonts
            font_paths = sorted([k for k in XTERM_SPECIFIC.keys() if 'font' in k.lower() or 'face' in k.lower()])
            if font_paths:
                grouped.append('── 🔤 Fonts ──')
                grouped.extend([f"🔤 {p}" for p in sorted(font_paths)])
            
            # Booleans
            bool_patterns = ['shell', 'scroll', 'bell', 'bold', 'allow', 'blink', 'video', 'reverse', 'iconic']
            bool_paths = sorted([k for k in XTERM_SPECIFIC.keys() 
                               if any(b in k.lower() for b in bool_patterns)])
            if bool_paths:
                grouped.append('── ☑️ Booleans ──')
                grouped.extend([f"☑️ {p}" for p in sorted(bool_paths)])
            
            # Geometry
            geom_patterns = ['lines', 'chars', 'pixels', 'width', 'height', 'size', 'borderwidth', 'margin']
            geom_paths = sorted([k for k in XTERM_SPECIFIC.keys() 
                               if any(p in k.lower() for p in geom_patterns)])
            if geom_paths:
                grouped.append('── 📐 Geometry ──')
                grouped.extend([f"🔢 {p}" for p in sorted(geom_paths)])
            
            # Other
            categorized = set(common + color_paths + font_paths + bool_paths + geom_paths)
            other_paths = sorted([k for k in XTERM_SPECIFIC.keys() if k not in categorized])
            if other_paths:
                grouped.append('── 💻 XTerm Specific ──')
                grouped.extend([f"{get_icon(p)} {p}" for p in sorted(other_paths)])
            
            # Generic
            grouped.append('── ⚙️ Generic ──')
            generic = [f"*.color{i}" for i in range(16)] + ['*.background', '*.foreground', '*.cursorColor']
            grouped.extend([f"🎨 {p}" if 'color' in p else f"⚙️ {p}" for p in generic])
            
            return grouped
        
        def strip_icon(path_with_icon):
            """Remove icon prefix from path."""
            if not path_with_icon:
                return ''
            if path_with_icon.startswith('──') or path_with_icon == '⭐ Most Common':
                return None
            if path_with_icon[0] in '⭐🎨🔤☑️🔢⚙️💻' and len(path_with_icon) > 2:
                if path_with_icon[1] == ' ':
                    return path_with_icon[2:].strip()
                parts = path_with_icon.split(' ', 1)
                if len(parts) > 1:
                    return parts[1].strip()
            return path_with_icon.strip()
        
        all_paths = get_grouped_paths()
        
        # Path section
        path_frame = ttk.LabelFrame(dialog, text="Resource Path", padding=10)
        path_frame.pack(fill=tk.X, padx=10, pady=5)
        
        path_var = tk.StringVar()
        path_combo = ttk.Combobox(path_frame, textvariable=path_var, values=all_paths, width=50)
        path_combo.pack(fill=tk.X, pady=2)
        
        self._setup_dropdown_accessibility(path_combo, dialog,
            "Alt+Down: Open list  |  ↑/↓: Navigate  |  Enter: Select  |  Tab: Next  |  Esc: Close")
        
        type_label = ttk.Label(path_frame, text="Type: (select a path)", foreground="gray")
        type_label.pack(anchor=tk.W, pady=2)
        
        # Filter
        filter_frame = ttk.Frame(path_frame)
        filter_frame.pack(fill=tk.X, pady=2)
        ttk.Label(filter_frame, text="Filter:").pack(side=tk.LEFT)
        filter_var = tk.StringVar()
        filter_entry = ttk.Entry(filter_frame, textvariable=filter_var, width=35)
        filter_entry.pack(side=tk.LEFT, padx=5)
        
        # Tooltip for filter
        filter_entry.bind('<Enter>', lambda e: self._show_tooltip(filter_entry,
            "Type to filter paths\nAlt+Down: Open dropdown\nTab: Next field\nEnter: Select first", e.x_root, e.y_root))
        filter_entry.bind('<Leave>', lambda e: self._hide_tooltip())
        
        no_matches = ttk.Label(filter_frame, text="⚠️ No matches found", foreground="red")
        
        def filter_paths(*args):
            text = filter_var.get().lower()
            if text:
                filtered = [p for p in all_paths if not p.startswith('──') and p != '⭐ Most Common' 
                          and text in strip_icon(p).lower()]
                path_combo['values'] = filtered
                if not filtered:
                    no_matches.pack(side=tk.LEFT, padx=5)
                else:
                    no_matches.pack_forget()
                    path_combo.event_generate('<Down>')
            else:
                path_combo['values'] = all_paths
                no_matches.pack_forget()
        
        filter_var.trace('w', filter_paths)
        
        def update_type(*args):
            path = strip_icon(path_var.get())
            if path and not path.startswith('──'):
                res_type = self._detect_resource_type(path)
                icons = {'color': '🎨 Color', 'font': '🔤 Font', 'boolean': '☑️ Boolean', 
                        'number': '🔢 Number', 'generic': '⚙️ Generic'}
                type_label.config(text=f"Type: {icons.get(res_type, res_type)}", foreground="black")
        
        path_var.trace('w', update_type)
        
        # Value section
        value_frame = ttk.LabelFrame(dialog, text="Value", padding=10)
        value_frame.pack(fill=tk.X, padx=10, pady=5)
        
        value_var = tk.StringVar()
        value_combo = ttk.Combobox(value_frame, textvariable=value_var, width=40)
        value_combo.pack(fill=tk.X, pady=2)
        
        self._setup_dropdown_accessibility(value_combo, dialog,
            "Alt+Down: Open suggestions  |  ↑/↓: Navigate  |  Enter: Select  |  Tab: OK button  |  Esc: Close")
        
        value_original = []
        
        # No matches label for value
        value_no_matches = ttk.Label(value_frame, text="⚠️ No matches found", foreground="red")
        
        def filter_values(*args):
            text = value_var.get().lower()
            if value_original and text:
                filtered = [v for v in value_original if text in v.lower()]
                if not filtered:
                    value_combo['values'] = [text]
                    value_no_matches.pack(anchor=tk.W, pady=2)
                else:
                    value_combo['values'] = filtered
                    value_no_matches.pack_forget()
                    value_combo.event_generate('<Down>')
            elif value_original and not text:
                value_combo['values'] = value_original
                value_no_matches.pack_forget()
        
        def on_value_keyrelease(event):
            if event.keysym in ('Return', 'KP_Enter'):
                if value_combo['values']:
                    value_var.set(value_combo['values'][0])
                    value_combo.event_generate('<Escape>')
                return
            if event.char and event.char.isprintable():
                dialog.after(10, filter_values)
        
        value_combo.bind('<KeyRelease>', on_value_keyrelease)
        
        def update_suggestions(*args):
            nonlocal value_original
            path = strip_icon(path_var.get())
            if not path or path.startswith('──'):
                value_combo['values'] = []
                value_original = []
                return
            
            res_type = self._detect_resource_type(path)
            presets = get_presets_for_resource(path)
            values = []
            
            if presets and 'values' in presets:
                values = [str(v) for v in presets['values']][:50]
            elif res_type == 'color':
                values = [f"{name}: {hex_val}" for name, hex_val in XTERM_COLORS.items()]
            elif res_type == 'font':
                from config.presets import COMMON_FONTS
                values = COMMON_FONTS
            elif res_type == 'boolean':
                from config.presets import ALL_BOOLEAN_VALUES
                values = ALL_BOOLEAN_VALUES
            
            value_original = values[:]
            value_combo['values'] = values
        
        path_var.trace('w', update_suggestions)
        
        # Buttons
        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(pady=15)
        
        self._add_processed = False
        
        def on_ok():
            if self._add_processed:
                return
            self._add_processed = True
            
            path = strip_icon(path_var.get())
            value = value_var.get().strip()
            
            if not path or path.startswith('──') or path == '⭐ Most Common':
                messagebox.showerror("Error", "Please select a valid resource path")
                self._add_processed = False
                return
            
            if not value:
                messagebox.showerror("Error", "Value is required")
                self._add_processed = False
                return
            
            if any(e.resource_path == path for e in self.entries):
                messagebox.showerror("Error", f"Resource '{path}' already exists")
                self._add_processed = False
                return
            
            # Extract hex from "name: #hex" format
            hex_match = re.search(r'#[0-9a-fA-F]{6}$', value)
            if hex_match:
                value = hex_match.group()
            
            entry = self.parser.add_entry(path, value)
            self.entries.append(entry)
            self.filtered_entries = self.entries[:]
            self.mark_dirty(True)
            self._populate_tree()
            self.set_status(f"Added {path}")
            self._close_dialog(dialog)
        
        def on_cancel():
            self._close_dialog(dialog)
        
        ttk.Button(btn_frame, text="OK", command=on_ok).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Cancel", command=on_cancel).pack(side=tk.LEFT, padx=5)
        
        # Center dialog
        dialog.update_idletasks()
        x = self.winfo_rootx() + (self.winfo_width() - dialog.winfo_width()) // 2
        y = self.winfo_rooty() + (self.winfo_height() - dialog.winfo_height()) // 2
        dialog.geometry(f"+{x}+{y}")
        
        path_combo.focus_set()
    
    def _show_tooltip(self, widget, text, x=None, y=None):
        """Display a tooltip."""
        self._tooltip = tk.Toplevel(widget)
        self._tooltip.wm_overrideredirect(True)
        self._tooltip.attributes('-topmost', True)
        if x is None:
            x = widget.winfo_rootx() + widget.winfo_width() // 2
        if y is None:
            y = widget.winfo_rooty() - 30
        self._tooltip.wm_geometry(f"+{x}+{y}")
        label = ttk.Label(self._tooltip, text=text, background="#ffffe0", 
                        relief=tk.SOLID, borderwidth=1, padding=5, font=('Helvetica', 9))
        label.pack()
    
    def _hide_tooltip(self):
        """Hide the tooltip."""
        if hasattr(self, '_tooltip') and self._tooltip:
            self._tooltip.destroy()
            self._tooltip = None
    
    def _close_dialog(self, dialog):
        """Close dialog and reset flag."""
        self._dialog_open = False
        dialog.destroy()
    
    def _update_entry(self, resource_path: str, new_value: str):
        """Update entry value."""
        for entry in self.entries:
            if entry.resource_path == resource_path:
                entry.value = new_value
                self.parser.update_entry(resource_path, new_value)
                break
    
    def _delete_selected(self):
        """Delete selected resource."""
        if self._delete_in_progress:
            return
        self._delete_in_progress = True
        
        try:
            selection = self.tree.selection()
            if not selection:
                messagebox.showwarning("No Selection", "Please select a resource to delete")
                return
            
            item = selection[0]
            values = self.tree.item(item, 'values')
            resource_path = values[0]
            
            if messagebox.askyesno("Confirm Delete", f"Delete {resource_path}?"):
                if self.parser.remove_entry(resource_path):
                    self.entries = [e for e in self.entries if e.resource_path != resource_path]
                    self.filtered_entries = [e for e in self.filtered_entries if e.resource_path != resource_path]
                    self.mark_dirty(True)
                    self._populate_tree()
                    self.set_status(f"Deleted {resource_path}")
        finally:
            self._delete_in_progress = False
    
    def _apply_resources(self):
        """Apply X resources using xrdb."""
        if not self.filepath or not os.path.exists(self.filepath):
            messagebox.showerror("Error", "Save the file before applying.")
            return
        
        try:
            subprocess.run(['xrdb', '-merge', self.filepath], capture_output=True, text=True, check=True)
            self.set_status(f"✓ Applied: {self.filepath}")
            messagebox.showinfo("Success", "X resources applied successfully!")
        except subprocess.CalledProcessError as e:
            messagebox.showerror("xrdb Error", f"Failed to apply resources:\n{e.stderr}")
        except FileNotFoundError:
            messagebox.showerror("xrdb Not Found", "xrdb command not found.")
    
    def _show_preset_picker(self):
        """Show preset picker dialog."""
        dialog = tk.Toplevel(self)
        dialog.title("Insert Preset Value")
        dialog.transient(self)
        dialog.grab_set()
        dialog.geometry("500x400")
        
        ttk.Label(dialog, text="Category:", font=('Helvetica', 10, 'bold')).pack(pady=5)
        
        category_var = tk.StringVar(value='colors')
        category_frame = ttk.Frame(dialog)
        category_frame.pack(fill=tk.X, padx=10)
        
        categories = [('colors', 'Colors 🎨'), ('fonts', 'Fonts 🔤'), 
                     ('booleans', 'Booleans ☑️'), ('xterm', 'XTerm 💻'), ('user', 'My Presets ⭐')]
        
        for val, text in categories:
            ttk.Radiobutton(category_frame, text=text, variable=category_var, 
                         value=val).pack(side=tk.LEFT, padx=5)
        
        # Preset list
        list_frame = ttk.Frame(dialog)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        columns = ('name', 'value')
        preset_tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=12)
        preset_tree.heading('name', text='Name')
        preset_tree.heading('value', text='Value')
        preset_tree.column('name', width=150)
        preset_tree.column('value', width=280)
        
        y_scroll = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=preset_tree.yview)
        preset_tree.configure(yscrollcommand=y_scroll.set)
        y_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        preset_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        def load_presets():
            for item in preset_tree.get_children():
                preset_tree.delete(item)
            presets = get_all_presets()
            cat = category_var.get()
            if cat in presets:
                for name, value in presets[cat]['items']:
                    preset_tree.insert('', 'end', values=(name, value))
        
        category_var.trace('w', lambda *args: load_presets())
        load_presets()
        
        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(fill=tk.X, padx=10, pady=10)
        
        def on_select():
            selection = preset_tree.selection()
            if selection:
                item = selection[0]
                values = preset_tree.item(item, 'values')
                value = values[1] if len(values) > 1 else values[0]
                tree_selection = self.tree.selection()
                if tree_selection:
                    item_id = tree_selection[0]
                    res_values = self.tree.item(item_id, 'values')
                    if res_values:
                        self._update_entry(res_values[0], value)
                        self.mark_dirty(True)
                        self._on_filter_changed()
                dialog.destroy()
        
        ttk.Button(btn_frame, text="Update Selected", command=on_select).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Cancel", command=dialog.destroy).pack(side=tk.RIGHT, padx=5)
        
        preset_tree.bind('<Double-1>', lambda e: on_select())
    
    def _manage_user_presets(self):
        """Manage user presets dialog."""
        dialog = tk.Toplevel(self)
        dialog.title("My Presets")
        dialog.transient(self)
        dialog.grab_set()
        dialog.geometry("600x400")
        
        columns = ('name', 'value')
        preset_tree = ttk.Treeview(dialog, columns=columns, show='headings')
        preset_tree.heading('name', text='Name')
        preset_tree.heading('value', text='Value')
        preset_tree.column('name', width=150)
        preset_tree.column('value', width=400)
        preset_tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        def refresh():
            for item in preset_tree.get_children():
                preset_tree.delete(item)
            for name, value in get_user_presets_list():
                display = value[:50] + '...' if len(value) > 50 else value
                preset_tree.insert('', 'end', values=(name, display))
        
        refresh()
        
        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(fill=tk.X, padx=10, pady=10)
        
        def delete():
            selection = preset_tree.selection()
            if selection:
                item = selection[0]
                name = preset_tree.item(item, 'values')[0]
                if messagebox.askyesno("Confirm", f"Delete '{name}'?", parent=dialog):
                    delete_user_preset(name)
                    refresh()
        
        def add_new():
            name = simpledialog.askstring("New Preset", "Enter name:", parent=dialog)
            if name:
                value = simpledialog.askstring("New Preset", "Enter value:", parent=dialog)
                if value:
                    add_user_preset(name, value)
                    refresh()
        
        ttk.Button(btn_frame, text="➕ Add", command=add_new).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="🗑️ Delete", command=delete).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Close", command=dialog.destroy).pack(side=tk.RIGHT, padx=5)
    
    def _update_apply_button(self):
        """Enable/disable apply button."""
        if self.filepath and os.path.exists(self.filepath):
            self.apply_btn.config(state=tk.NORMAL)
        else:
            self.apply_btn.config(state=tk.DISABLED)
    
    def load_data(self, data: str):
        """Load XResources content."""
        self.entries = self.parser.parse(data)
        self.filtered_entries = self.entries[:]
        self._original_data = data
        self._populate_tree()
        self.mark_dirty(False)
        self._update_apply_button()
        self.set_status(f"Loaded {len(self.entries)} resources")
    
    def get_data(self) -> str:
        """Get XResources content."""
        return self.parser.write_back()
    
    def validate(self) -> tuple[bool, str]:
        """Validate XResources content."""
        if not self.entries:
            return False, "No resources defined"
        
        paths = [e.resource_path for e in self.entries]
        if len(paths) != len(set(paths)):
            return False, "Duplicate resource paths found"
        
        return True, ""
        value_var = tk.StringVar()
        value_combo = ttk.Combobox(value_input_frame, textvariable=value_var, width=40)
        value_combo.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Color picker button (initially hidden)
        color_picker_btn = ttk.Button(value_input_frame, text="🎨 Pick...", width=10)
        color_picker_btn.pack(side=tk.RIGHT, padx=5)
        color_picker_btn.pack_forget()  # Hide initially
        
        # Store original values for filtering (using list in enclosing scope)
        value_original_values = []
        
        # No matches label for value (initially hidden)
        value_no_matches = ttk.Label(value_frame, text="⚠️ No matches found", foreground="red")
        
        def filter_values(*args):
            """Filter value dropdown based on user input in real-time."""
            filter_text = value_var.get().lower()
            
            # Only filter if we have original values stored and user is typing
            if value_original_values and filter_text:
                filtered = [v for v in value_original_values if filter_text in v.lower()]
                # Allow custom entry by including current text if no matches
                if not filtered:
                    value_combo['values'] = [filter_text]
                else:
                    value_combo['values'] = filtered
                
                # Show/hide "no matches" message
                if not filtered and filter_text:
                    value_no_matches.pack(anchor=tk.W, pady=2)
                else:
                    value_no_matches.pack_forget()
                
                # Open dropdown to show filtered results
                if filtered:
                    value_combo.event_generate('<Down>')
            elif value_original_values and not filter_text:
                # Restore original values when empty
                value_combo['values'] = value_original_values
                value_no_matches.pack_forget()
        
        # Bind to value changes for real-time filtering
        def on_value_keyrelease(event):
            """Handle key release for value dropdown navigation."""
            if event.keysym in ('Return', 'KP_Enter'):
                # Select first match on Enter
                if value_combo['values']:
                    value_var.set(value_combo['values'][0])
                    value_combo.event_generate('<Escape>')
                return
            
            # Trigger filtering on printable characters
            if event.char and event.char.isprintable():
                dialog.after(10, filter_values)
        
        value_combo.bind('<KeyRelease>', on_value_keyrelease)
        
        # Color preview frame
        preview_frame = ttk.Frame(value_frame)
        preview_frame.pack(fill=tk.X, pady=5)
        
        color_preview_label = ttk.Label(preview_frame, text="Color Preview:")
        color_preview_label.pack(side=tk.LEFT)
        
        color_preview = tk.Label(preview_frame, text="   ", bg='#808080', relief=tk.RIDGE, bd=2, width=4, height=2)
        color_preview.pack(side=tk.LEFT, padx=5)
        color_preview.pack_forget()  # Hide initially
        
        # Format indicator
        format_label = ttk.Label(value_frame, text="", foreground="gray", font=('Helvetica', 9))
        format_label.pack(anchor=tk.W)
        
        def update_value_suggestions(*args):
            """Update value dropdown based on selected resource path."""
            nonlocal value_original_values
            
            path_raw = path_var.get()
            path = strip_icon(path_raw)
            if not path or path.startswith('──') or path == '⭐ Most Common':
                value_combo['values'] = []
                value_original_values = []
                value_var.set('')
                color_picker_btn.pack_forget()
                color_preview.pack_forget()
                color_preview_label.pack_forget()
                format_label.config(text="")
                value_no_matches.pack_forget()
                return
            
            res_type = self._detect_resource_type(path)
            
            # Get presets for this specific path if available
            from config.presets import get_presets_for_resource
            presets = get_presets_for_resource(path)
            
            values = []
            if presets and 'values' in presets:
                # Use specific presets for this resource
                values = [str(v) for v in presets['values']][:50]  # Limit to first 50
            elif res_type == 'color':
                # Show color suggestions
                from config.presets import XTERM_COLORS
                values = [f"{name}: {hex_val}" for name, hex_val in XTERM_COLORS.items()]
                # Show color picker and preview
                color_picker_btn.pack(side=tk.RIGHT, padx=5)
                color_preview_label.pack(side=tk.LEFT)
                color_preview.pack(side=tk.LEFT, padx=5)
                format_label.config(text="Formats: #ffffff or rgb:ff/ff/ff")
            elif res_type == 'font':
                from config.presets import COMMON_FONTS
                values = COMMON_FONTS
                format_label.config(text="Enter font name or select from list")
            elif res_type == 'boolean':
                from config.presets import ALL_BOOLEAN_VALUES
                values = ALL_BOOLEAN_VALUES
                format_label.config(text="true/false, yes/no, on/off, 1/0")
            
            # Store original values and set dropdown
            value_original_values = values[:]
            value_combo['values'] = values
            value_var.set('')  # Clear value when path changes
            
            # Hide color UI for non-color types
            if res_type != 'color':
                color_picker_btn.pack_forget()
                color_preview.pack_forget()
                color_preview_label.pack_forget()
                if res_type not in ['font', 'boolean']:
                    format_label.config(text="")
        
        def on_value_changed(*args):
            """Update color preview when value changes."""
            value = value_var.get()
            # Try to extract hex color from value
            hex_match = re.search(r'#[0-9a-fA-F]{6}', value)
            if hex_match:
                color_preview.config(bg=hex_match.group())
                color_preview.pack(side=tk.LEFT, padx=5)
            elif self.COLOR_RGB_PATTERN.match(value):
                # Convert rgb:ff/ff/ff to #ffffff
                match = self.COLOR_RGB_PATTERN.match(value)
                if match:
                    r, g, b = match.groups()
                    hex_color = f"#{r[:2]}{g[:2]}{b[:2]}"
                    color_preview.config(bg=hex_color)
                    color_preview.pack(side=tk.LEFT, padx=5)
            elif value in ['true', 'True', 'TRUE', 'on', 'On', 'ON', 'yes', 'Yes', 'YES', '1']:
                color_preview.config(bg='#00ff00')  # Green for true
                color_preview.pack(side=tk.LEFT, padx=5)
            elif value in ['false', 'False', 'FALSE', 'off', 'Off', 'OFF', 'no', 'No', 'NO', '0']:
                color_preview.config(bg='#ff0000')  # Red for false
                color_preview.pack(side=tk.LEFT, padx=5)
        
        path_var.trace('w', update_value_suggestions)
        value_var.trace('w', on_value_changed)
        
        # Color picker functionality
        def pick_color():
            """Open color picker dialog."""
            current = value_var.get()
            initial = '#808080'  # Default gray
            
            # Try to parse current value
            hex_match = re.search(r'#[0-9a-fA-F]{6}', current)
            if hex_match:
                initial = hex_match.group()
            elif self.COLOR_RGB_PATTERN.match(current):
                match = self.COLOR_RGB_PATTERN.match(current)
                if match:
                    r, g, b = match.groups()
                    initial = f"#{r[:2]}{g[:2]}{b[:2]}"
            
            color = colorchooser.askcolor(initialcolor=initial, title="Choose Color")
            if color and color[1]:
                value_var.set(color[1])
                color_preview.config(bg=color[1])
        
        color_picker_btn.config(command=pick_color)
        
        # Bind combobox selection to prevent selecting separator lines
        def on_path_select(event):
            selected = path_combo.get()
            if selected.startswith('──') or selected == '⭐ Most Common':
                path_combo.set('')
                return 'break'
            # Auto-strip icon if user selected from dropdown
            clean_path = strip_icon(selected)
            if clean_path and clean_path != selected:
                path_var.set(clean_path)
        
        path_combo.bind('<<ComboboxSelected>>', on_path_select)
        
        # Buttons
        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(pady=15)
        
        # Track if already processed
        self._add_processed = False
        
        def on_ok():
            # Prevent double execution
            if self._add_processed:
                return
            self._add_processed = True
            
            path_raw = path_var.get().strip()
            path = strip_icon(path_raw)
            value = value_var.get().strip()
            
            # Validate path is not a separator
            if not path or path.startswith('──') or path == '⭐ Most Common':
                messagebox.showerror("Error", "Please select a valid resource path")
                self._add_processed = False
                return
            
            if not value:
                messagebox.showerror("Error", "Value is required")
                self._add_processed = False
                return
            
            # Check for duplicate
            if any(e.resource_path == path for e in self.entries):
                messagebox.showerror("Error", f"Resource '{path}' already exists")
                self._add_processed = False
                return
            
            # Extract actual value if it has a color name prefix (e.g., "white: #ffffff")
            hex_match = re.search(r'#[0-9a-fA-F]{6}$', value)
            if hex_match:
                value = hex_match.group()
            
            entry = self.parser.add_entry(path, value)
            self.entries.append(entry)
            self.filtered_entries = self.entries[:]
            self.mark_dirty(True)
            self._populate_tree()
            self.set_status(f"Added {path}")
            
            self._close_dialog(dialog)
        
        def on_cancel():
            self._close_dialog(dialog)
        
        ttk.Button(btn_frame, text="OK", command=on_ok).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Cancel", command=on_cancel).pack(side=tk.LEFT, padx=5)
        
        # Center dialog
        dialog.update_idletasks()
        x = self.winfo_rootx() + (self.winfo_width() - dialog.winfo_width()) // 2
        y = self.winfo_rooty() + (self.winfo_height() - dialog.winfo_height()) // 2
        dialog.geometry(f"+{x}+{y}")
        
        # Set focus to path combobox
        path_combo.focus_set()
    def _delete_selected(self):
        """Delete selected resource."""
        # Prevent concurrent delete operations
        if self._delete_in_progress:
            return
        self._delete_in_progress = True
        
        try:
            selection = self.tree.selection()
            if not selection:
                messagebox.showwarning("No Selection", "Please select a resource to delete")
                return
            
            item = selection[0]
            values = self.tree.item(item, 'values')
            resource_path = values[0]
            
            if messagebox.askyesno("Confirm Delete", f"Delete {resource_path}?"):
                # Remove from parser
                if self.parser.remove_entry(resource_path):
                    # Remove from our list
                    original_len = len(self.entries)
                    self.entries = [e for e in self.entries if e.resource_path != resource_path]
                    self.filtered_entries = [e for e in self.filtered_entries if e.resource_path != resource_path]
                    
                    if len(self.entries) < original_len:
                        self.mark_dirty(True)
                        self._populate_tree()
                        self.set_status(f"Deleted {resource_path}")
        finally:
            self._delete_in_progress = False
    
    def _apply_resources(self):
        """Apply X resources using xrdb command."""
        if not self.filepath:
            messagebox.showerror("Error", "No file path set. Save the file first.")
            return
        
        # Check if file exists
        if not os.path.exists(self.filepath):
            messagebox.showerror("Error", f"File not found: {self.filepath}\nSave before applying.")
            return
        
        try:
            # Run xrdb to load the resources
            result = subprocess.run(
                ['xrdb', '-merge', self.filepath],
                capture_output=True,
                text=True,
                check=True
            )
            
            self.set_status(f"✓ Applied: {self.filepath}")
            messagebox.showinfo("Success", f"X resources applied successfully!\n\nFile: {self.filepath}")
            
        except subprocess.CalledProcessError as e:
            error_msg = e.stderr if e.stderr else str(e)
            messagebox.showerror("xrdb Error", f"Failed to apply resources:\n{error_msg}")
            self.set_status(f"✗ Apply failed: {error_msg[:50]}...")
        except FileNotFoundError:
            messagebox.showerror("xrdb Not Found", 
                                "xrdb command not found.\n\n"
                                "Make sure you're running on an X11 system with xrdb installed.")
    
    def _update_apply_button(self):
        """Enable/disable apply button based on file existence."""
        if self.filepath and os.path.exists(self.filepath):
            self.apply_btn.config(state=tk.NORMAL)
        else:
            self.apply_btn.config(state=tk.DISABLED)
    
    def _on_delete_key(self, event):
        """Handle delete key."""
        self._delete_selected()
    
    def _on_edit_key(self, event):
        """Handle edit key."""
        self._on_double_click(event)
    
    # Required abstract methods
    
    def load_data(self, data: str):
        """Load XResources content."""
        self.entries = self.parser.parse(data)
        self.filtered_entries = self.entries[:]
        self._original_data = data
        self._populate_tree()
        self.mark_dirty(False)
        self._update_apply_button()
        self.set_status(f"Loaded {len(self.entries)} resources")
    
    def get_data(self) -> str:
        """Get XResources content."""
        return self.parser.write_back()
    
    def validate(self) -> tuple[bool, str]:
        """Validate XResources content."""
        if not self.entries:
            return False, "No resources defined"
        
        # Check for duplicate resource paths
        paths = [e.resource_path for e in self.entries]
        if len(paths) != len(set(paths)):
            return False, "Duplicate resource paths found"
        
        return True, ""
