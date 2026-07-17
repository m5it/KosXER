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
        self._dialog_open = False  # Prevent duplicate dialogs
        self._delete_in_progress = False  # Prevent duplicate deletes
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
        
        # User presets button
        ttk.Button(btn_frame, text="My Presets", command=self._manage_user_presets).pack(side=tk.LEFT, padx=5)
        
        # XTerm helper buttons
        ttk.Separator(btn_frame, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=10)
        ttk.Button(btn_frame, text="New XTerm", command=self._launch_new_xterm).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="XTerm Tips", command=self._show_xterm_tips).pack(side=tk.LEFT, padx=5)
        
        # Apply button (reloads X resources)
        self.apply_btn = ttk.Button(btn_frame, text="Apply (xrdb)", command=self._apply_resources, 
                                    state=tk.DISABLED)
        self.apply_btn.pack(side=tk.RIGHT, padx=5)
        
        # Info label about xterm restart
        info_frame = ttk.Frame(self.editor_frame)
        info_frame.pack(fill=tk.X, padx=5, pady=2)
        self.info_label = ttk.Label(info_frame, text="💡 Tip: xterm needs restart to see changes. Use 'New XTerm' or close/reopen.", 
                                   foreground="gray", font=('Helvetica', 9, 'italic'))
        self.info_label.pack(side=tk.LEFT)
        
        # Bindings
        self.tree.bind('<Double-1>', self._on_double_click)
    
    def _detect_resource_type(self, resource_path: str) -> str:
        """
        Detect resource type from resource path name for intelligent suggestions.
        
        Args:
            resource_path: Resource path like 'XTerm*background', '*.color0'
        
        Returns:
            'color', 'font', 'boolean', 'number', or 'generic'
        """
        if not resource_path:
            return 'generic'
        
        path_lower = resource_path.lower()
        
        # Color patterns
        color_patterns = ['color', 'background', 'foreground', 'cursorcolor', 
                       'bordercolor', 'highlightcolor', 'troughcolor']
        if any(p in path_lower for p in color_patterns):
            return 'color'
        
        # Font patterns
        font_patterns = ['font', 'face', 'facename']
        if any(p in path_lower for p in font_patterns):
            return 'font'
        
        # Boolean patterns
        bool_patterns = ['shell', 'video', 'scroll', 'bell', 'bold', 'allow', 
                        'blink', 'underline', 'active', 'enabled', 'visible',
                        'reverse', 'iconic', 'hold', 'utmp']
        if any(p in path_lower for p in bool_patterns):
            return 'boolean'
        
        # Number patterns
        num_patterns = ['lines', 'chars', 'pixels', 'width', 'height', 'size',
                       'borderwidth', 'margin', 'padding', 'timeout', 'interval']
        if any(p in path_lower for p in num_patterns):
            return 'number'
        
        return 'generic'
    
    def _launch_new_xterm(self):
        """Launch a new xterm instance with current XResources."""
        try:
            # First apply current resources
            if self.filepath and os.path.exists(self.filepath):
                subprocess.run(['xrdb', '-merge', self.filepath], check=True, capture_output=True)
            
            # Launch xterm in background
            subprocess.Popen(['xterm'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            self.set_status("✓ Launched new xterm with current resources")
            
        except FileNotFoundError:
            # Try uxterm as fallback
            try:
                subprocess.Popen(['uxterm'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                self.set_status("✓ Launched new uxterm with current resources")
            except FileNotFoundError:
                messagebox.showerror("xterm Not Found", 
                                   "Neither 'xterm' nor 'uxterm' found.\n\n"
                                   "Install xterm: sudo apt-get install xterm")
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

✓ Use "New XTerm" button
  - Applies resources then launches fresh xterm
  - New window sees all changes immediately

✓ Close and reopen xterm
  - Old window keeps old colors/fonts
  - New window loads fresh resources

✓ Start xterm with specific file
  - xterm -xrm "*background: #ffffff"

Common White Colors for xterm:

  XTerm*background: #ffffff    (pure white)
  XTerm*foreground: #000000    (black text)
  XTerm*background: #f0f0f0    (off-white)
  XTerm*foreground: #ffffff    (white text)

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
        # Clear existing
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Add filtered entries
        for entry in self.filtered_entries:
            value_type = self._get_value_type(entry.value)
            preview = self._get_color_preview(entry.value) if value_type == 'color' else ''
            
            item_id = self.tree.insert('', 'end', values=(
                entry.resource_path,
                entry.value,
                value_type,
                preview
            ))
            
            # Set tag for color background
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
        """Handle double click for editing with intelligent type detection."""
        selection = self.tree.selection()
        if not selection:
            return
        
        item = selection[0]
        values = self.tree.item(item, 'values')
        if not values:
            return
        
        resource_path, current_value, value_type, _ = values
        
        # Use intelligent detection based on resource name
        detected_type = self._detect_resource_type(resource_path)
        
        # Override with detected type if it's more specific
        if detected_type == 'color' or value_type == 'color':
            self._edit_color_with_presets(resource_path, current_value)
        elif detected_type == 'font':
            self._edit_with_presets(resource_path, current_value, 'font')
        elif detected_type == 'boolean':
            self._edit_with_presets(resource_path, current_value, 'boolean')
        else:
            self._edit_generic(resource_path, current_value)
    
    def _edit_color_with_presets(self, resource_path: str, current_value: str):
        """Edit color with color picker and preset colors."""
        dialog = tk.Toplevel(self)
        dialog.title(f"Edit Color - {resource_path}")
        dialog.transient(self)
        dialog.grab_set()
        dialog.geometry("400x550")
        
        # Current value display
        ttk.Label(dialog, text="Current Value:", font=('Helvetica', 10, 'bold')).pack(pady=5)
        current_var = tk.StringVar(value=current_value)
        ttk.Entry(dialog, textvariable=current_var, width=40, state='readonly').pack(padx=10, pady=5)
        
        # Color preview
        preview_frame = ttk.Frame(dialog, width=100, height=50)
        preview_frame.pack(pady=10)
        preview_frame.pack_propagate(False)
        
        preview_label = tk.Label(preview_frame, text="Preview", bg=current_value if self.COLOR_HEX_PATTERN.match(current_value) else 'gray')
        preview_label.pack(fill=tk.BOTH, expand=True)
        
        # Color picker button
        def pick_color():
            initial = current_var.get()
            if self.COLOR_RGB_PATTERN.match(initial):
                match = self.COLOR_RGB_PATTERN.match(initial)
                if match:
                    r, g, b = match.groups()
                    initial = f"#{r[:2]}{g[:2]}{b[:2]}"
            
            color = colorchooser.askcolor(initialcolor=initial, title="Choose Color")
            if color and color[1]:
                current_var.set(color[1])
                preview_label.config(bg=color[1])
        
        ttk.Button(dialog, text="🎨 Pick Color...", command=pick_color).pack(pady=5)
        
        # Preset colors
        ttk.Label(dialog, text="Quick Presets:", font=('Helvetica', 10, 'bold')).pack(pady=5)
        
        preset_frame = ttk.Frame(dialog)
        preset_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Show common colors in a grid
        common_colors = [
            ('White', '#ffffff'), ('Black', '#000000'),
            ('Red', '#ff0000'), ('Green', '#00ff00'),
            ('Blue', '#0000ff'), ('Yellow', '#ffff00'),
            ('Cyan', '#00ffff'), ('Magenta', '#ff00ff'),
            ('Gray', '#808080'), ('Orange', '#ffa500'),
        ]
        
        for i, (name, color) in enumerate(common_colors):
            btn = tk.Button(preset_frame, text=name, bg=color, fg='white' if color in ['#000000', '#0000ff', '#808080'] else 'black',
                          width=8, command=lambda c=color: (current_var.set(c), preview_label.config(bg=c)))
            btn.grid(row=i//5, column=i%5, padx=2, pady=2)
        
        # Terminal colors
        ttk.Label(dialog, text="Terminal Colors:", font=('Helvetica', 10, 'bold')).pack(pady=5)
        
        term_frame = ttk.Frame(dialog)
        term_frame.pack(fill=tk.X, padx=10, pady=5)
        
        for i in range(8):
            color_val = XTERM_COLORS[f'color{i}']
            btn = tk.Button(term_frame, text=f"color{i}", bg=color_val, 
                          fg='white' if i in [0, 4] else 'black',
                          width=8, command=lambda c=color_val: (current_var.set(c), preview_label.config(bg=c)))
            btn.grid(row=0, column=i, padx=2, pady=2)
        
        # Save as preset button
        def save_as_preset():
            name = simpledialog.askstring("Save Preset", "Enter preset name:", parent=dialog)
            if name:
                if add_user_preset(name, current_var.get()):
                    messagebox.showinfo("Success", f"Saved '{name}' to My Presets", parent=dialog)
                else:
                    messagebox.showerror("Error", "Failed to save preset", parent=dialog)
        
        ttk.Button(dialog, text="⭐ Save as Preset", command=save_as_preset).pack(pady=10)
        
        # Buttons
        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(fill=tk.X, padx=10, pady=10)
        
        def on_ok():
            self._update_entry(resource_path, current_var.get())
            dialog.destroy()
        
        ttk.Button(btn_frame, text="OK", command=on_ok).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Cancel", command=dialog.destroy).pack(side=tk.RIGHT, padx=5)
    
    def _edit_with_presets(self, resource_path: str, current_value: str, preset_type: str):
        """Edit with preset dropdown for fonts, booleans, etc."""
        dialog = tk.Toplevel(self)
        dialog.title(f"Edit {preset_type.title()} - {resource_path}")
        dialog.transient(self)
        dialog.grab_set()
        dialog.geometry("400x350")
        
        # Current value
        ttk.Label(dialog, text="Current Value:", font=('Helvetica', 10, 'bold')).pack(pady=5)
        current_var = tk.StringVar(value=current_value)
        ttk.Entry(dialog, textvariable=current_var, width=40).pack(padx=10, pady=5)
        
        # Preset selection
        ttk.Label(dialog, text=f"Choose {preset_type.title()} Preset:", font=('Helvetica', 10, 'bold')).pack(pady=10)
        
        presets = get_all_presets()
        if preset_type in presets:
            preset_names = [name for name, _ in presets[preset_type]['items']]
            preset_var = tk.StringVar()
            
            combo = ttk.Combobox(dialog, textvariable=preset_var, values=preset_names, width=35, state='readonly')
            combo.pack(padx=10, pady=5)
            
            def on_preset_select(event):
                selected = combo.get()
                for name, val in presets[preset_type]['items']:
                    if name == selected:
                        current_var.set(val)
                        break
            
            combo.bind('<<ComboboxSelected>>', on_preset_select)
        
        # Save as preset button
        def save_as_preset():
            name = simpledialog.askstring("Save Preset", "Enter preset name:", parent=dialog)
            if name:
                if add_user_preset(name, current_var.get()):
                    messagebox.showinfo("Success", f"Saved '{name}' to My Presets", parent=dialog)
                else:
                    messagebox.showerror("Error", "Failed to save preset", parent=dialog)
        
        ttk.Button(dialog, text="⭐ Save as Preset", command=save_as_preset).pack(pady=10)
        
        # Buttons
        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(fill=tk.X, padx=10, pady=10)
        
        def on_ok():
            self._update_entry(resource_path, current_var.get())
            dialog.destroy()
        
        ttk.Button(btn_frame, text="OK", command=on_ok).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Cancel", command=dialog.destroy).pack(side=tk.RIGHT, padx=5)
    
    def _edit_generic(self, resource_path: str, current_value: str):
        """Edit value with simple dialog."""
        dialog = tk.Toplevel(self)
        dialog.title(f"Edit Resource - {resource_path}")
        dialog.transient(self)
        dialog.grab_set()
        dialog.geometry("400x250")
        
        ttk.Label(dialog, text="Value:", font=('Helvetica', 10, 'bold')).pack(pady=5)
        current_var = tk.StringVar(value=current_value)
        ttk.Entry(dialog, textvariable=current_var, width=40).pack(padx=10, pady=5)
        
        # Save as preset button
        def save_as_preset():
            name = simpledialog.askstring("Save Preset", "Enter preset name:", parent=dialog)
            if name:
                if add_user_preset(name, current_var.get()):
                    messagebox.showinfo("Success", f"Saved '{name}' to My Presets", parent=dialog)
                else:
                    messagebox.showerror("Error", "Failed to save preset", parent=dialog)
        
        ttk.Button(dialog, text="⭐ Save as Preset", command=save_as_preset).pack(pady=10)
        
        # Buttons
        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(fill=tk.X, padx=10, pady=10)
        
        def on_ok():
            self._update_entry(resource_path, current_var.get())
            dialog.destroy()
        
        ttk.Button(btn_frame, text="OK", command=on_ok).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Cancel", command=dialog.destroy).pack(side=tk.RIGHT, padx=5)
    
    def _update_entry(self, resource_path: str, new_value: str):
        """Update an entry value."""
        # Update in parser
        if self.parser.update_value(resource_path, new_value):
            # Update in our list
            for entry in self.entries:
                if entry.resource_path == resource_path:
                    entry.value = new_value
                    break
            
            self.mark_dirty(True)
            self._on_filter_changed()  # Refresh display
            self.set_status(f"Updated {resource_path}")
    
    def _manage_user_presets(self):
        """Show dialog to manage user presets."""
        dialog = tk.Toplevel(self)
        dialog.title("My Presets")
        dialog.transient(self)
        dialog.grab_set()
        dialog.geometry("500x400")
        
        ttk.Label(dialog, text="Your Custom Presets", font=('Helvetica', 12, 'bold')).pack(pady=10)
        ttk.Label(dialog, text=f"Saved in: {USER_PRESETS_FILE}", foreground="gray").pack()
        
        # Preset list
        list_frame = ttk.Frame(dialog)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        columns = ('name', 'value')
        preset_tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=12)
        preset_tree.heading('name', text='Preset Name')
        preset_tree.heading('value', text='Value')
        preset_tree.column('name', width=150)
        preset_tree.column('value', width=300)
        
        y_scroll = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=preset_tree.yview)
        preset_tree.configure(yscrollcommand=y_scroll.set)
        y_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        preset_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Load user presets
        def refresh_presets():
            for item in preset_tree.get_children():
                preset_tree.delete(item)
            
            user_presets = get_user_presets_list()
            for name, value in user_presets:
                # Truncate long values for display
                display_value = value[:50] + '...' if len(value) > 50 else value
                preset_tree.insert('', 'end', values=(name, display_value))
        
        refresh_presets()
        
        # Buttons
        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(fill=tk.X, padx=10, pady=10)
        
        def delete_selected():
            selection = preset_tree.selection()
            if selection:
                item = selection[0]
                values = preset_tree.item(item, 'values')
                name = values[0]
                if messagebox.askyesno("Confirm Delete", f"Delete preset '{name}'?", parent=dialog):
                    if delete_user_preset(name):
                        refresh_presets()
                        self.set_status(f"Deleted preset '{name}'")
        
        def add_new_preset():
            name = simpledialog.askstring("New Preset", "Enter preset name:", parent=dialog)
            if name:
                value = simpledialog.askstring("New Preset", "Enter preset value:", parent=dialog)
                if value:
                    if add_user_preset(name, value):
                        refresh_presets()
                        self.set_status(f"Added preset '{name}'")
        
        ttk.Button(btn_frame, text="➕ Add New", command=add_new_preset).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="🗑️ Delete Selected", command=delete_selected).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Close", command=dialog.destroy).pack(side=tk.RIGHT, padx=5)
    
    def _show_preset_picker(self):
        """Show preset picker dialog."""
        dialog = tk.Toplevel(self)
        dialog.title("Insert Preset Value")
        dialog.transient(self)
        dialog.grab_set()
        dialog.geometry("500x400")
        
        # Category selector
        ttk.Label(dialog, text="Category:", font=('Helvetica', 10, 'bold')).pack(pady=5)
        
        category_var = tk.StringVar(value='colors')
        category_frame = ttk.Frame(dialog)
        category_frame.pack(fill=tk.X, padx=10)
        
        categories = [
            ('colors', 'Colors 🎨'),
            ('fonts', 'Fonts 🔤'),
            ('booleans', 'Booleans ☑️'),
            ('xterm', 'XTerm 💻'),
            ('user', 'My Presets ⭐'),
        ]
        
        for val, text in categories:
            ttk.Radiobutton(category_frame, text=text, variable=category_var, 
                         value=val, command=lambda: self._on_preset_category_changed(category_var, dialog)).pack(side=tk.LEFT, padx=5)
        
        # Search filter
        filter_frame = ttk.Frame(dialog)
        filter_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(filter_frame, text="Search:").pack(side=tk.LEFT)
        search_var = tk.StringVar()
        search_entry = ttk.Entry(filter_frame, textvariable=search_var, width=30)
        search_entry.pack(side=tk.LEFT, padx=5)
        
        # Preset list
        list_frame = ttk.Frame(dialog)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Create treeview for presets
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
        
        # Store reference for updates
        dialog.preset_tree = preset_tree
        dialog.search_var = search_var
        
        # Load initial data
        self._load_presets_to_tree(preset_tree, 'colors')
        
        # Search binding
        def on_search(*args):
            self._filter_presets(preset_tree, category_var.get(), search_var.get())
        
        search_var.trace('w', on_search)
        
        # Buttons
        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(fill=tk.X, padx=10, pady=10)
        
        result = {'value': None}
        
        def on_select():
            selection = preset_tree.selection()
            if selection:
                item = selection[0]
                values = preset_tree.item(item, 'values')
                result['value'] = values[1] if len(values) > 1 else values[0]
                dialog.destroy()
        
        def on_insert_new():
            # Insert as new resource
            selection = preset_tree.selection()
            if selection:
                item = selection[0]
                values = preset_tree.item(item, 'values')
                value = values[1] if len(values) > 1 else values[0]
                self._add_preset_as_new(value)
                dialog.destroy()
        
        ttk.Button(btn_frame, text="Update Selected Resource", command=on_select).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Insert as New Resource", command=on_insert_new).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Cancel", command=dialog.destroy).pack(side=tk.RIGHT, padx=5)
        
        # Double-click to select
        preset_tree.bind('<Double-1>', lambda e: on_select())
        
        self.wait_window(dialog)
        
        # Apply result if any
        if result['value']:
            selection = self.tree.selection()
            if selection:
                item = selection[0]
                values = self.tree.item(item, 'values')
                if values:
                    resource_path = values[0]
                    self._update_entry(resource_path, result['value'])
    
    def _on_preset_category_changed(self, category_var, dialog):
        """Handle preset category change."""
        if hasattr(dialog, 'preset_tree'):
            self._load_presets_to_tree(dialog.preset_tree, category_var.get())
    
    def _load_presets_to_tree(self, tree, category):
        """Load presets into treeview."""
        # Clear existing
        for item in tree.get_children():
            tree.delete(item)
        
        presets = get_all_presets()
        
        if category in presets:
            for name, value in presets[category]['items']:
                tree.insert('', 'end', values=(name, value))
    
    def _filter_presets(self, tree, category, search_text):
        """Filter presets by search text."""
        # Clear and reload
        for item in tree.get_children():
            tree.delete(item)
        
        presets = get_all_presets()
        search_lower = search_text.lower()
        
        if category in presets:
            for name, value in presets[category]['items']:
                if not search_text or search_lower in name.lower() or search_lower in str(value).lower():
                    tree.insert('', 'end', values=(name, value))
    
    def _add_preset_as_new(self, value):
        """Add a new resource with preset value."""
        # Prevent duplicate dialogs
        if self._dialog_open:
            return
        self._dialog_open = True
        
        dialog = tk.Toplevel(self)
        dialog.title("New Resource with Preset")
        dialog.transient(self)
        dialog.grab_set()
        dialog.protocol("WM_DELETE_WINDOW", lambda: self._close_dialog(dialog))
        
        ttk.Label(dialog, text=f"Preset Value: {value[:50]}{'...' if len(value) > 50 else ''}").pack(padx=10, pady=5)
        ttk.Label(dialog, text="Resource Path:").pack(padx=10, pady=5)
        
        path_var = tk.StringVar()
        ttk.Entry(dialog, textvariable=path_var, width=40).pack(padx=10, pady=5)
        
        def on_ok():
            path = path_var.get().strip()
            if path:
                entry = self.parser.add_entry(path, value)
                self.entries.append(entry)
                self.filtered_entries = self.entries[:]
                self.mark_dirty(True)
                self._populate_tree()
                self.set_status(f"Added {path} with preset value")
            self._close_dialog(dialog)
        
        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(pady=10)
        ttk.Button(btn_frame, text="OK", command=on_ok).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Cancel", command=lambda: self._close_dialog(dialog)).pack(side=tk.LEFT, padx=5)
        
        # Center dialog
        dialog.update_idletasks()
        x = self.winfo_rootx() + (self.winfo_width() - dialog.winfo_width()) // 2
        y = self.winfo_rooty() + (self.winfo_height() - dialog.winfo_height()) // 2
        dialog.geometry(f"+{x}+{y}")
    
    def _add_resource(self):
        """Add new resource."""
        # Prevent duplicate dialogs
        if self._dialog_open:
            return
        self._dialog_open = True
        
        dialog = tk.Toplevel(self)
        dialog.title("Add Resource")
        dialog.transient(self)
        dialog.grab_set()
        dialog.protocol("WM_DELETE_WINDOW", lambda: self._close_dialog(dialog))
        
        ttk.Label(dialog, text="Resource Path:").pack(padx=10, pady=5)
        path_var = tk.StringVar()
        ttk.Entry(dialog, textvariable=path_var, width=40).pack(padx=10, pady=5)
        
        ttk.Label(dialog, text="Value:").pack(padx=10, pady=5)
        value_var = tk.StringVar()
        ttk.Entry(dialog, textvariable=value_var, width=40).pack(padx=10, pady=5)
        
        # Track if already processed
        self._add_processed = False
        
        def on_ok():
            # Prevent double execution
            if self._add_processed:
                return
            self._add_processed = True
            
            path = path_var.get().strip()
            value = value_var.get().strip()
            
            if path and value:
                entry = self.parser.add_entry(path, value)
                self.entries.append(entry)
                self.filtered_entries = self.entries[:]
                self.mark_dirty(True)
                self._populate_tree()
                self.set_status(f"Added {path}")
            
            self._close_dialog(dialog)
        
        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(pady=10)
        ttk.Button(btn_frame, text="OK", command=on_ok).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Cancel", command=lambda: self._close_dialog(dialog)).pack(side=tk.LEFT, padx=5)
        
        # Center dialog
        dialog.update_idletasks()
        x = self.winfo_rootx() + (self.winfo_width() - dialog.winfo_width()) // 2
        y = self.winfo_rooty() + (self.winfo_height() - dialog.winfo_height()) // 2
        dialog.geometry(f"+{x}+{y}")
    
    def _close_dialog(self, dialog):
        """Close dialog and reset flag."""
        self._dialog_open = False
        dialog.destroy()
    
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
