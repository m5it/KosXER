#!/usr/bin/env python3
"""
XResources Editor Widget for KosXER

Treeview-based editor for .Xresources and .Xdefaults files.
"""

import tkinter as tk
from tkinter import ttk, colorchooser, messagebox, simpledialog
import re
from typing import Optional, List

from gui.editor_base import EditorWidget
from parsers.xresources_parser import XResourcesParser, XResourceEntry


class XResourcesEditor(EditorWidget):
    """Editor widget for XResources files."""
    
    COLOR_HEX_PATTERN = re.compile(r'^#[0-9a-fA-F]{6}$')
    COLOR_RGB_PATTERN = re.compile(r'^rgb:([0-9a-fA-F]{2,4})/([0-9a-fA-F]{2,4})/([0-9a-fA-F]{2,4})$')
    
    def __init__(self, parent, main_window=None, filepath: Optional[str] = None, **kwargs):
        self.parser = XResourcesParser()
        self.entries: List[XResourceEntry] = []
        self.filtered_entries: List[XResourceEntry] = []
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
        
        # Bindings
        self.tree.bind('<Double-1>', self._on_double_click)
    
    def _get_value_type(self, value: str) -> str:
        """Determine value type."""
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
        """Handle double click for editing."""
        selection = self.tree.selection()
        if not selection:
            return
        
        item = selection[0]
        values = self.tree.item(item, 'values')
        if not values:
            return
        
        resource_path, current_value, value_type, _ = values
        
        if value_type == 'color':
            self._edit_color(resource_path, current_value)
        else:
            self._edit_generic(resource_path, current_value)
    
    def _edit_color(self, resource_path: str, current_value: str):
        """Edit color value with color picker."""
        # Get initial color
        initial_color = current_value
        if self.COLOR_RGB_PATTERN.match(current_value):
            # Convert rgb:rr/gg/bb to #rrggbb
            match = self.COLOR_RGB_PATTERN.match(current_value)
            if match:
                r, g, b = match.groups()
                initial_color = f"#{r[:2]}{g[:2]}{b[:2]}"
        
        # Open color picker
        color = colorchooser.askcolor(initialcolor=initial_color, title=f"Choose color for {resource_path}")
        
        if color and color[1]:  # color is (rgb_tuple, hex_string)
            new_value = color[1]
            self._update_entry(resource_path, new_value)
    
    def _edit_generic(self, resource_path: str, current_value: str):
        """Edit value with simple dialog."""
        new_value = simpledialog.askstring(
            "Edit Resource",
            f"Value for {resource_path}:",
            initialvalue=current_value
        )
        
        if new_value is not None:
            self._update_entry(resource_path, new_value)
    
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
    
    def _add_resource(self):
        """Add new resource."""
        dialog = tk.Toplevel(self)
        dialog.title("Add Resource")
        dialog.transient(self)
        dialog.grab_set()
        
        ttk.Label(dialog, text="Resource Path:").pack(padx=10, pady=5)
        path_var = tk.StringVar()
        ttk.Entry(dialog, textvariable=path_var, width=40).pack(padx=10, pady=5)
        
        ttk.Label(dialog, text="Value:").pack(padx=10, pady=5)
        value_var = tk.StringVar()
        ttk.Entry(dialog, textvariable=value_var, width=40).pack(padx=10, pady=5)
        
        def on_ok():
            path = path_var.get().strip()
            value = value_var.get().strip()
            
            if path and value:
                entry = self.parser.add_entry(path, value)
                self.entries.append(entry)
                self.filtered_entries = self.entries[:]
                self.mark_dirty(True)
                self._populate_tree()
                self.set_status(f"Added {path}")
            
            dialog.destroy()
        
        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(pady=10)
        ttk.Button(btn_frame, text="OK", command=on_ok).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Cancel", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
    
    def _delete_selected(self):
        """Delete selected resource."""
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
                self.entries = [e for e in self.entries if e.resource_path != resource_path]
                self.filtered_entries = [e for e in self.filtered_entries if e.resource_path != resource_path]
                
                self.mark_dirty(True)
                self._populate_tree()
                self.set_status(f"Deleted {resource_path}")
    
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
