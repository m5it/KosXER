#!/usr/bin/env python3
"""
KosDWM Menu Editor Widget for KosXER

Treeview-based editor for KosDWM's dynamic menu structure.
Supports editing menu folders and Python script items.
"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog
from typing import Optional

from gui.editor_base import EditorWidget
from parsers.kosdwm_menu_parser import KosDWMMenuParser, MenuItem, MenuFolder


class KosDWMMenuEditor(EditorWidget):
    """
    Editor widget for KosDWM dynamic menus.
    
    Features:
    - Treeview showing menu hierarchy
    - Add/Delete/Edit menu folders and items
    - Python script editing
    - Menu preview
    """
    
    def __init__(self, parent, main_window=None, filepath: Optional[str] = None, **kwargs):
        self.parser = KosDWMMenuParser()
        self.menus_dir: Optional[str] = None
        super().__init__(parent, main_window, filepath, **kwargs)
    
    def _create_editor_widgets(self):
        """Create the KosDWM menu editor UI."""
        # Main paned window
        paned = ttk.PanedWindow(self.editor_frame, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Left: Treeview
        left_frame = ttk.Frame(paned)
        paned.add(left_frame, weight=2)
        
        # Treeview frame
        tree_frame = ttk.Frame(left_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True)
        
        # Treeview
        self.tree = ttk.Treeview(tree_frame, columns=('type',), show='tree headings')
        self.tree.heading('#0', text='Menu Structure')
        self.tree.heading('type', text='Type')
        self.tree.column('type', width=80)
        
        # Scrollbars
        y_scroll = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=y_scroll.set)
        y_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Buttons
        btn_frame = ttk.Frame(left_frame)
        btn_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(btn_frame, text="Add Folder", command=self._add_folder).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Add Script", command=self._add_script).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Delete", command=self._delete_selected).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Edit", command=self._edit_selected).pack(side=tk.LEFT, padx=2)
        
        # Right: Properties/Preview
        right_frame = ttk.Notebook(paned)
        paned.add(right_frame, weight=1)
        
        # Properties tab
        props_frame = ttk.Frame(right_frame, padding=10)
        right_frame.add(props_frame, text="Properties")
        
        self._create_properties_panel(props_frame)
        
        # Preview tab
        preview_frame = ttk.Frame(right_frame, padding=10)
        right_frame.add(preview_frame, text="Preview")
        
        self._create_preview_panel(preview_frame)
        
        # Bindings
        self.tree.bind('<<TreeviewSelect>>', self._on_select)
        self.tree.bind('<Double-1>', self._on_double_click)
    
    def _create_properties_panel(self, parent):
        """Create properties panel."""
        # Name
        ttk.Label(parent, text="Name:").pack(anchor=tk.W, pady=2)
        self.prop_name_var = tk.StringVar()
        ttk.Entry(parent, textvariable=self.prop_name_var, state='readonly').pack(fill=tk.X, pady=2)
        
        # Label
        ttk.Label(parent, text="Label:").pack(anchor=tk.W, pady=2)
        self.prop_label_var = tk.StringVar()
        ttk.Entry(parent, textvariable=self.prop_label_var).pack(fill=tk.X, pady=2)
        
        # Icon
        icon_frame = ttk.Frame(parent)
        icon_frame.pack(fill=tk.X, pady=2)
        ttk.Label(icon_frame, text="Icon:").pack(side=tk.LEFT)
        self.prop_icon_var = tk.StringVar()
        ttk.Entry(icon_frame, textvariable=self.prop_icon_var).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        ttk.Button(icon_frame, text="Browse...", command=self._browse_icon).pack(side=tk.RIGHT)
        
        # Description (for scripts)
        ttk.Label(parent, text="Description:").pack(anchor=tk.W, pady=2)
        self.prop_desc_var = tk.StringVar()
        ttk.Entry(parent, textvariable=self.prop_desc_var).pack(fill=tk.X, pady=2)
        
        # Apply button
        ttk.Button(parent, text="Apply Changes", command=self._apply_properties).pack(fill=tk.X, pady=20)
    
    def _create_preview_panel(self, parent):
        """Create preview panel."""
        self.preview_text = tk.Text(parent, wrap=tk.WORD, state=tk.DISABLED, 
                                     bg='#1a1a1a', fg='#d0d0d0',
                                     font=('Courier', 10))
        self.preview_text.pack(fill=tk.BOTH, expand=True)
        ttk.Button(parent, text="Refresh Preview", command=self._update_preview).pack(fill=tk.X, pady=5)
    
    def _populate_tree(self):
        """Populate treeview with menu structure."""
        # Clear tree
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        if not self.parser.root_menu:
            return
        
        # Add root
        root_node = self.tree.insert('', 'end', text=self.parser.root_menu.label,
                                     values=('root',), open=True)
        self.tree.item(root_node, tags=(self.parser.root_menu.name,))
        
        # Add children
        self._add_items_to_tree(root_node, self.parser.root_menu)
    
    def _add_items_to_tree(self, parent_node: str, menu: MenuFolder):
        """Add menu items to tree."""
        for item in menu.items:
            if isinstance(item, MenuFolder):
                node = self.tree.insert(parent_node, 'end', text=item.label,
                                       values=('folder',), open=True)
                self.tree.item(node, tags=(item.name,))
                self._add_items_to_tree(node, item)
            elif isinstance(item, MenuItem):
                node = self.tree.insert(parent_node, 'end', text=item.label,
                                       values=('script',))
                self.tree.item(node, tags=(item.name,))
    
    def _on_select(self, event=None):
        """Handle tree selection."""
        selection = self.tree.selection()
        if not selection:
            return
        
        item = selection[0]
        tags = self.tree.item(item, 'tags')
        
        if not tags:
            return
        
        name = tags[0]
        
        # Find the item
        menu_item = self.parser.get_item(name)
        if menu_item:
            self.prop_name_var.set(menu_item.name)
            self.prop_label_var.set(menu_item.label)
            self.prop_icon_var.set(menu_item.icon or '')
            self.prop_desc_var.set(menu_item.description or '')
        else:
            menu_folder = self.parser.get_folder(name)
            if menu_folder:
                self.prop_name_var.set(menu_folder.name)
                self.prop_label_var.set(menu_folder.label)
                self.prop_icon_var.set(menu_folder.icon or '')
                self.prop_desc_var.set('')
    
    def _on_double_click(self, event):
        """Handle double click."""
        self._edit_selected()
    
    def _add_folder(self):
        """Add new menu folder."""
        name = simpledialog.askstring("New Folder", "Enter folder name:")
        if not name:
            return
        
        label = simpledialog.askstring("New Folder", "Enter display label:")
        if not label:
            label = name
        
        # Create folder in parser
        selection = self.tree.selection()
        if selection:
            # Add to selected folder
            tags = self.tree.item(selection[0], 'tags')
            if tags:
                parent_name = tags[0]
                parent = self.parser.get_folder(parent_name)
                if parent:
                    new_folder = MenuFolder(
                        name=name,
                        label=label,
                        folder_path=f"{parent.folder_path}/{name}"
                    )
                    parent.add_item(new_folder)
        else:
            # Add to root
            new_folder = MenuFolder(
                name=name,
                label=label,
                folder_path=f"{self.parser.menus_dir}/{name}"
            )
            self.parser.root_menu.add_item(new_folder)
        
        self.mark_dirty(True)
        self._populate_tree()
    
    def _add_script(self):
        """Add new script item."""
        name = simpledialog.askstring("New Script", "Enter script name (without .py):")
        if not name:
            return
        
        label = simpledialog.askstring("New Script", "Enter display label:")
        if not label:
            label = name
        
        selection = self.tree.selection()
        if selection:
            tags = self.tree.item(selection[0], 'tags')
            if tags:
                parent_name = tags[0]
                parent = self.parser.get_folder(parent_name)
                if parent:
                    new_item = MenuItem(
                        name=name,
                        label=label,
                        script_path=f"{parent.folder_path}/{name}.py"
                    )
                    parent.add_item(new_item)
        
        self.mark_dirty(True)
        self._populate_tree()
    
    def _delete_selected(self):
        """Delete selected item."""
        selection = self.tree.selection()
        if not selection:
            return
        
        if messagebox.askyesno("Confirm", "Delete selected item?"):
            item = selection[0]
            tags = self.tree.item(item, 'tags')
            
            if tags:
                name = tags[0]
                self.parser.remove_menu_item(name)
                self.mark_dirty(True)
                self._populate_tree()
    
    def _edit_selected(self):
        """Edit selected item."""
        selection = self.tree.selection()
        if not selection:
            return
        
        # Properties panel handles editing
        self._apply_properties()
    
    def _apply_properties(self):
        """Apply property changes."""
        name = self.prop_name_var.get()
        if not name:
            return
        
        # Find and update item
        item = self.parser.get_item(name)
        if item:
            item.label = self.prop_label_var.get()
            item.icon = self.prop_icon_var.get() or None
            item.description = self.prop_desc_var.get() or None
        else:
            folder = self.parser.get_folder(name)
            if folder:
                folder.label = self.prop_label_var.get()
                folder.icon = self.prop_icon_var.get() or None
        
        self.mark_dirty(True)
        self._populate_tree()
    
    def _browse_icon(self):
        """Browse for icon file."""
        filepath = filedialog.askopenfilename(
            title="Select Icon",
            filetypes=[("Images", "*.png *.jpg *.svg"), ("All", "*.*")]
        )
        if filepath:
            self.prop_icon_var.set(filepath)
    
    def _update_preview(self):
        """Update menu preview."""
        if self.parser.root_menu:
            preview = self.parser.get_menu_tree()
            self.preview_text.config(state=tk.NORMAL)
            self.preview_text.delete('1.0', tk.END)
            self.preview_text.insert('1.0', preview)
            self.preview_text.config(state=tk.DISABLED)
    
    # Required abstract methods
    
    def load_data(self, data: str):
        """Load menu structure."""
        # For menus, data is the directory path
        self.menus_dir = data
        self.parser.parse(data)
        self._original_data = data
        self._populate_tree()
        self._update_preview()
        self.mark_dirty(False)
        self.set_status(f"Loaded KosDWM menu from {data}")
    
    def get_data(self) -> str:
        """Get menu directory path."""
        return self.menus_dir or ''
    
    def validate(self) -> tuple[bool, str]:
        """Validate menu structure."""
        if not self.parser.root_menu:
            return False, "No menu loaded"
        
        if not self.parser.root_menu.items:
            return False, "Menu is empty"
        
        return True, ""
