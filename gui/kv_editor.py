#!/usr/bin/env python3
"""
Key-Value Editor Widget for KosXER

Simple two-column editor for KEY=value files.
Good for .env files, simple configs, shell exports, etc.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import Optional, List, Dict

from gui.editor_base import EditorWidget
from parsers.generic_kv_parser import GenericKVParser, KVEntry


class KVEditor(EditorWidget):
    """
    Editor widget for key-value configuration files.
    
    Features:
    - Two-column editable treeview (Key, Value)
    - Add/Delete rows
    - Import/Export functionality
    - Search/filter
    - Intelligent quote handling
    """
    
    def __init__(self, parent, main_window=None, filepath: Optional[str] = None, **kwargs):
        self.parser = GenericKVParser()
        self.entries: List[KVEntry] = []
        self.filtered_entries: List[KVEntry] = []
        self._edit_popup: Optional[tk.Toplevel] = None
        
        super().__init__(parent, main_window, filepath, **kwargs)
    
    def _create_editor_widgets(self):
        """Create the KV editor UI."""
        # Filter frame
        filter_frame = ttk.Frame(self.editor_frame)
        filter_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(filter_frame, text="Search:").pack(side=tk.LEFT, padx=5)
        self.filter_var = tk.StringVar()
        self.filter_var.trace('w', self._on_filter_changed)
        ttk.Entry(filter_frame, textvariable=self.filter_var, width=30).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(filter_frame, text="Clear", command=self._clear_filter).pack(side=tk.LEFT, padx=5)
        
        # Treeview frame
        tree_frame = ttk.Frame(self.editor_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Treeview
        columns = ('key', 'value', 'export')
        self.tree = ttk.Treeview(tree_frame, columns=columns, show='headings')
        
        self.tree.heading('key', text='Key')
        self.tree.heading('value', text='Value')
        self.tree.heading('export', text='Export')
        
        self.tree.column('key', width=200)
        self.tree.column('value', width=400)
        self.tree.column('export', width=60)
        
        # Scrollbars
        y_scroll = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
        x_scroll = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=y_scroll.set, xscrollcommand=x_scroll.set)
        
        y_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        x_scroll.pack(side=tk.BOTTOM, fill=tk.X)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Button frame
        btn_frame = ttk.Frame(self.editor_frame)
        btn_frame.pack(fill=tk.X, pady=5)
        
        # Row operations
        ttk.Button(btn_frame, text="Add Row", command=self._add_row).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Delete Selected", command=self._delete_selected).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Edit Selected", command=self._edit_selected).pack(side=tk.LEFT, padx=5)
        
        ttk.Separator(btn_frame, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=10)
        
        # Import/Export
        ttk.Button(btn_frame, text="Import", command=self._import_file).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Export", command=self._export_file).pack(side=tk.LEFT, padx=5)
        
        # Bindings
        self.tree.bind('<Double-1>', self._on_double_click)
        self.tree.bind('<Delete>', lambda e: self._delete_selected())
        self.tree.bind('<Return>', lambda e: self._edit_selected())
    
    def _populate_tree(self):
        """Populate treeview with entries."""
        # Clear existing
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Add filtered entries
        for entry in self.filtered_entries:
            export_mark = '✓' if entry.is_export else ''
            self.tree.insert('', 'end', values=(
                entry.key,
                entry.value,
                export_mark
            ))
    
    def _on_filter_changed(self, *args):
        """Apply filter."""
        filter_text = self.filter_var.get().lower()
        
        if not filter_text:
            self.filtered_entries = self.entries[:]
        else:
            self.filtered_entries = [
                e for e in self.entries 
                if filter_text in e.key.lower() or filter_text in e.value.lower()
            ]
        
        self._populate_tree()
        self.set_status(f"Showing {len(self.filtered_entries)} of {len(self.entries)} entries")
    
    def _clear_filter(self):
        """Clear filter."""
        self.filter_var.set('')
        self.filtered_entries = self.entries[:]
        self._populate_tree()
    
    def _on_double_click(self, event):
        """Handle double click for editing."""
        self._edit_selected()
    
    def _add_row(self):
        """Add new key-value row."""
        dialog = tk.Toplevel(self)
        dialog.title("Add Entry")
        dialog.transient(self)
        dialog.grab_set()
        
        # Key field
        ttk.Label(dialog, text="Key:").pack(anchor=tk.W, padx=10, pady=2)
        key_var = tk.StringVar()
        ttk.Entry(dialog, textvariable=key_var, width=40).pack(padx=10, pady=2)
        
        # Value field
        ttk.Label(dialog, text="Value:").pack(anchor=tk.W, padx=10, pady=2)
        value_var = tk.StringVar()
        ttk.Entry(dialog, textvariable=value_var, width=40).pack(padx=10, pady=2)
        
        # Export checkbox
        export_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(dialog, text="Export (bash)", variable=export_var).pack(anchor=tk.W, padx=10, pady=5)
        
        def on_ok():
            key = key_var.get().strip()
            value = value_var.get().strip()
            
            if not key:
                messagebox.showerror("Error", "Key is required")
                return
            
            # Check for duplicate
            if any(e.key == key for e in self.entries):
                messagebox.showerror("Error", f"Key '{key}' already exists")
                return
            
            entry = KVEntry(key=key, value=value, is_export=export_var.get())
            self.entries.append(entry)
            self.filtered_entries = self.entries[:]
            self.mark_dirty(True)
            self._populate_tree()
            self.set_status(f"Added: {key}")
            dialog.destroy()
        
        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(pady=10)
        ttk.Button(btn_frame, text="OK", command=on_ok).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Cancel", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
    
    def _delete_selected(self):
        """Delete selected row(s)."""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a row to delete")
            return
        
        if messagebox.askyesno("Confirm", "Delete selected row(s)?"):
            for item_id in selection:
                values = self.tree.item(item_id, 'values')
                key = values[0]
                
                # Remove from entries
                self.entries = [e for e in self.entries if e.key != key]
            
            self.filtered_entries = self.entries[:]
            self.mark_dirty(True)
            self._populate_tree()
            self.set_status(f"Deleted {len(selection)} row(s)")
    
    def _edit_selected(self):
        """Edit selected row."""
        selection = self.tree.selection()
        if not selection:
            return
        
        item_id = selection[0]
        values = self.tree.item(item_id, 'values')
        old_key = values[0]
        old_value = values[1]
        old_export = values[2] == '✓'
        
        # Find entry
        entry = next((e for e in self.entries if e.key == old_key), None)
        if not entry:
            return
        
        dialog = tk.Toplevel(self)
        dialog.title("Edit Entry")
        dialog.transient(self)
        dialog.grab_set()
        
        # Key field
        ttk.Label(dialog, text="Key:").pack(anchor=tk.W, padx=10, pady=2)
        key_var = tk.StringVar(value=old_key)
        ttk.Entry(dialog, textvariable=key_var, width=40).pack(padx=10, pady=2)
        
        # Value field
        ttk.Label(dialog, text="Value:").pack(anchor=tk.W, padx=10, pady=2)
        value_var = tk.StringVar(value=old_value)
        ttk.Entry(dialog, textvariable=value_var, width=40).pack(padx=10, pady=2)
        
        # Export checkbox
        export_var = tk.BooleanVar(value=old_export)
        ttk.Checkbutton(dialog, text="Export (bash)", variable=export_var).pack(anchor=tk.W, padx=10, pady=5)
        
        def on_ok():
            new_key = key_var.get().strip()
            new_value = value_var.get().strip()
            
            if not new_key:
                messagebox.showerror("Error", "Key is required")
                return
            
            # Check if key changed and new key exists
            if new_key != old_key and any(e.key == new_key for e in self.entries):
                messagebox.showerror("Error", f"Key '{new_key}' already exists")
                return
            
            # Update entry
            entry.key = new_key
            entry.value = new_value
            entry.is_export = export_var.get()
            
            self.mark_dirty(True)
            self._on_filter_changed()
            self.set_status(f"Updated: {new_key}")
            dialog.destroy()
        
        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(pady=10)
        ttk.Button(btn_frame, text="OK", command=on_ok).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Cancel", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
    
    def _import_file(self):
        """Import from another file."""
        filepath = filedialog.askopenfilename(
            title="Import Key-Value File",
            filetypes=[("All Files", "*.*"), ("Env Files", "*.env"), ("Config", "*.conf")]
        )
        if not filepath:
            return
        
        try:
            new_parser = GenericKVParser()
            new_entries = new_parser.parse_file(filepath)
            
            # Merge or replace
            if messagebox.askyesno("Import", "Replace current entries?"):
                self.entries = new_entries
            else:
                # Merge, skipping duplicates
                existing_keys = {e.key for e in self.entries}
                for entry in new_entries:
                    if entry.key not in existing_keys:
                        self.entries.append(entry)
            
            self.filtered_entries = self.entries[:]
            self.mark_dirty(True)
            self._populate_tree()
            self.set_status(f"Imported {len(new_entries)} entries from {filepath}")
        
        except Exception as e:
            messagebox.showerror("Import Error", str(e))
    
    def _export_file(self):
        """Export to another file."""
        filepath = filedialog.asksaveasfilename(
            title="Export Key-Value File",
            defaultextension=".env",
            filetypes=[("Env File", "*.env"), ("Config", "*.conf"), ("All", "*.*")]
        )
        if not filepath:
            return
        
        try:
            # Update parser entries
            self.parser.entries = self.entries
            self.parser.write_back(filepath)
            self.set_status(f"Exported to {filepath}")
        
        except Exception as e:
            messagebox.showerror("Export Error", str(e))
    
    # Required abstract methods
    
    def load_data(self, data: str):
        """Load key-value content."""
        self.entries = self.parser.parse(data)
        self.filtered_entries = self.entries[:]
        self._original_data = data
        self._populate_tree()
        self.mark_dirty(False)
        self.set_status(f"Loaded {len(self.entries)} entries")
    
    def get_data(self) -> str:
        """Get key-value content."""
        self.parser.entries = self.entries
        return self.parser.write_back()
    
    def validate(self) -> tuple[bool, str]:
        """Validate key-value data."""
        if not self.entries:
            return True, ""  # Empty is valid
        
        # Check for duplicate keys
        keys = [e.key for e in self.entries]
        if len(keys) != len(set(keys)):
            return False, "Duplicate keys found"
        
        # Check for invalid key names
        for entry in self.entries:
            if not entry.key:
                return False, "Empty key found"
            if ' ' in entry.key:
                return False, f"Key contains space: {entry.key}"
        
        return True, ""
