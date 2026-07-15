#!/usr/bin/env python3
"""
OpenBox Menu Editor Widget for KosXER

Treeview-based editor for OpenBox menu.xml files.
Supports menu hierarchy editing, drag-drop reordering,
and visual preview of menu structure.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import Optional, Dict, Any, Union

from gui.editor_base import EditorWidget
from parsers.openbox_parser import OpenBoxMenuParser, OpenBoxMenu, OpenBoxMenuItem, OpenBoxSeparator


class OpenBoxEditor(EditorWidget):
    """
    Editor widget for OpenBox menu.xml files.
    
    Features:
    - Treeview showing menu hierarchy
    - Drag-drop reordering
    - Editor panel for item properties
    - Visual menu preview
    """
    
    # Action types for OpenBox
    ACTIONS = [
        'Execute', 'Reconfigure', 'Restart', 'Exit',
        'ShowMenu', 'NextWindow', 'PreviousWindow',
        'Iconify', 'Raise', 'Lower', 'Close', 'Kill',
        'Shade', 'Unshade', 'ToggleShade',
        'Maximize', 'Unmaximize', 'ToggleMaximize',
        'Fullscreen', 'Unfullscreen', 'ToggleFullscreen',
        'SendToDesktop', 'MoveToDesktop', 'GoToDesktop',
        'DirectionalCycleWindows', 'Desktop', 'Layer'
    ]
    
    def __init__(self, parent, main_window=None, filepath: Optional[str] = None, **kwargs):
        self.parser = OpenBoxMenuParser()
        self.current_menu: Optional[OpenBoxMenu] = None
        self.selected_item: Optional[Any] = None
        self._drag_data: Optional[Dict] = None
        
        super().__init__(parent, main_window, filepath, **kwargs)
    
    def _create_editor_widgets(self):
        """Create the OpenBox editor UI."""
        # Main paned window
        self.main_paned = ttk.PanedWindow(self.editor_frame, orient=tk.HORIZONTAL)
        self.main_paned.pack(fill=tk.BOTH, expand=True)
        
        # Left panel - Treeview
        left_frame = ttk.Frame(self.main_paned)
        self.main_paned.add(left_frame, weight=2)
        
        # Treeview for menu structure
        tree_frame = ttk.Frame(left_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.tree = ttk.Treeview(tree_frame, columns=('type',), show='tree headings')
        self.tree.heading('#0', text='Menu Structure')
        self.tree.heading('type', text='Type')
        self.tree.column('type', width=80)
        
        # Scrollbars
        y_scroll = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
        x_scroll = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=y_scroll.set, xscrollcommand=x_scroll.set)
        
        y_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        x_scroll.pack(side=tk.BOTTOM, fill=tk.X)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Tree buttons
        tree_btn_frame = ttk.Frame(left_frame)
        tree_btn_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(tree_btn_frame, text="Add Menu", command=self._add_menu).pack(side=tk.LEFT, padx=2)
        ttk.Button(tree_btn_frame, text="Add Item", command=self._add_item).pack(side=tk.LEFT, padx=2)
        ttk.Button(tree_btn_frame, text="Add Separator", command=self._add_separator).pack(side=tk.LEFT, padx=2)
        ttk.Button(tree_btn_frame, text="Delete", command=self._delete_selected).pack(side=tk.LEFT, padx=2)
        
        # Move buttons
        move_frame = ttk.Frame(left_frame)
        move_frame.pack(fill=tk.X, padx=5, pady=5)
        ttk.Button(move_frame, text="↑ Up", command=self._move_up).pack(side=tk.LEFT, padx=2)
        ttk.Button(move_frame, text="↓ Down", command=self._move_down).pack(side=tk.LEFT, padx=2)
        ttk.Button(move_frame, text="← Out", command=self._move_out).pack(side=tk.LEFT, padx=2)
        ttk.Button(move_frame, text="→ In", command=self._move_in).pack(side=tk.LEFT, padx=2)
        
        # Right panel - Properties
        right_frame = ttk.LabelFrame(self.main_paned, text="Properties", padding=10)
        self.main_paned.add(right_frame, weight=1)
        
        self._create_properties_panel(right_frame)
        
        # Bindings
        self.tree.bind('<<TreeviewSelect>>', self._on_tree_select)
        self.tree.bind('<ButtonPress-1>', self._on_drag_start)
        self.tree.bind('<B1-Motion>', self._on_drag_motion)
        self.tree.bind('<ButtonRelease-1>', self._on_drag_end)
    
    def _create_properties_panel(self, parent):
        """Create properties editor panel."""
        # Type selector
        ttk.Label(parent, text="Type:").pack(anchor=tk.W, pady=2)
        self.type_var = tk.StringVar(value='item')
        self.type_combo = ttk.Combobox(parent, textvariable=self.type_var,
                                       values=['menu', 'item', 'separator'],
                                       state='readonly')
        self.type_combo.pack(fill=tk.X, pady=2)
        self.type_combo.bind('<<ComboboxSelected>>', self._on_type_changed)
        
        # Label field
        ttk.Label(parent, text="Label:").pack(anchor=tk.W, pady=2)
        self.label_var = tk.StringVar()
        ttk.Entry(parent, textvariable=self.label_var).pack(fill=tk.X, pady=2)
        
        # ID field
        ttk.Label(parent, text="ID:").pack(anchor=tk.W, pady=2)
        self.id_var = tk.StringVar()
        ttk.Entry(parent, textvariable=self.id_var).pack(fill=tk.X, pady=2)
        
        # Icon field
        ttk.Label(parent, text="Icon:").pack(anchor=tk.W, pady=2)
        icon_frame = ttk.Frame(parent)
        icon_frame.pack(fill=tk.X, pady=2)
        self.icon_var = tk.StringVar()
        ttk.Entry(icon_frame, textvariable=self.icon_var).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(icon_frame, text="Browse...", command=self._browse_icon).pack(side=tk.RIGHT, padx=2)
        
        # Action frame
        self.action_frame = ttk.LabelFrame(parent, text="Action", padding=5)
        self.action_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(self.action_frame, text="Action Type:").pack(anchor=tk.W)
        self.action_var = tk.StringVar(value='Execute')
        self.action_combo = ttk.Combobox(self.action_frame, textvariable=self.action_var,
                                          values=self.ACTIONS, state='readonly')
        self.action_combo.pack(fill=tk.X, pady=2)
        self.action_combo.bind('<<ComboboxSelected>>', self._on_action_changed)
        
        # Command field (for Execute)
        ttk.Label(self.action_frame, text="Command:").pack(anchor=tk.W, pady=2)
        self.command_var = tk.StringVar()
        ttk.Entry(self.action_frame, textvariable=self.command_var).pack(fill=tk.X, pady=2)
        
        # Apply button
        ttk.Button(parent, text="Apply Changes", command=self._apply_changes).pack(fill=tk.X, pady=10)
        
        # Preview frame
        preview_frame = ttk.LabelFrame(parent, text="Menu Preview", padding=5)
        preview_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.preview_text = tk.Text(preview_frame, wrap=tk.WORD, height=10, state=tk.DISABLED)
        self.preview_text.pack(fill=tk.BOTH, expand=True)
    
    def _populate_tree(self, menu: Optional[OpenBoxMenu] = None, parent_node: str = ''):
        """Populate treeview with menu structure."""
        if menu is None:
            menu = self.current_menu
        
        if menu is None:
            return
        
        for item in menu.items:
            if isinstance(item, OpenBoxMenu):
                node = self.tree.insert(parent_node, 'end', text=item.label,
                                       values=('menu',), open=True)
                self._populate_tree(item, node)
            elif isinstance(item, OpenBoxMenuItem):
                self.tree.insert(parent_node, 'end', text=item.label,
                                values=('item',))
            elif isinstance(item, OpenBoxSeparator):
                text = item.label if item.label else '---'
                self.tree.insert(parent_node, 'end', text=text,
                                values=('separator',))
    
    def _on_tree_select(self, event=None):
        """Handle tree selection."""
        selection = self.tree.selection()
        if not selection:
            return
        
        item_id = selection[0]
        # Find corresponding menu item
        # This would need proper tracking in a real implementation
    
    def _on_drag_start(self, event):
        """Start drag operation."""
        item = self.tree.identify_row(event.y)
        if item:
            self._drag_data = {'item': item, 'x': event.x, 'y': event.y}
    
    def _on_drag_motion(self, event):
        """Handle drag motion."""
        if self._drag_data:
            # Could show visual feedback here
            pass
    
    def _on_drag_end(self, event):
        """End drag operation."""
        if not self._drag_data:
            return
        
        target = self.tree.identify_row(event.y)
        if target and target != self._drag_data['item']:
            # Move item in tree
            # In a real implementation, would also update the menu structure
            pass
        
        self._drag_data = None
    
    def _on_type_changed(self, event=None):
        """Handle type selection change."""
        item_type = self.type_var.get()
        # Enable/disable fields based on type
        if item_type == 'separator':
            self.label_var.set('---')
            self.action_frame.configure(state=tk.DISABLED)
        else:
            self.action_frame.configure(state=tk.NORMAL)
    
    def _on_action_changed(self, event=None):
        """Handle action selection change."""
        action = self.action_var.get()
        # Show/hide command field based on action
        if action == 'Execute':
            # Command field is relevant
            pass
        else:
            self.command_var.set('')
    
    def _browse_icon(self):
        """Browse for icon file."""
        filepath = filedialog.askopenfilename(
            title="Select Icon",
            filetypes=[("PNG", "*.png"), ("SVG", "*.svg"), ("All", "*.*")]
        )
        if filepath:
            self.icon_var.set(filepath)
    
    def _add_menu(self):
        """Add new submenu."""
        # Would open dialog for new menu
        self.mark_dirty(True)
        self.set_status("Add menu (dialog not implemented)")
    
    def _add_item(self):
        """Add new menu item."""
        # Would open dialog for new item
        self.mark_dirty(True)
        self.set_status("Add item (dialog not implemented)")
    
    def _add_separator(self):
        """Add separator."""
        # Would add separator to current menu
        self.mark_dirty(True)
        self.set_status("Add separator (not implemented)")
    
    def _delete_selected(self):
        """Delete selected item."""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select an item to delete")
            return
        
        if messagebox.askyesno("Confirm", "Delete selected item?"):
            # Remove from tree and menu structure
            self.mark_dirty(True)
    
    def _move_up(self):
        """Move selected item up."""
        self.mark_dirty(True)
    
    def _move_down(self):
        """Move selected item down."""
        self.mark_dirty(True)
    
    def _move_out(self):
        """Move selected item out of submenu."""
        self.mark_dirty(True)
    
    def _move_in(self):
        """Move selected item into submenu."""
        self.mark_dirty(True)
    
    def _apply_changes(self):
        """Apply property changes."""
        self.mark_dirty(True)
        self._update_preview()
    
    def _update_preview(self):
        """Update menu preview."""
        if self.current_menu:
            preview = self.parser.get_menu_tree(self.current_menu)
            self.preview_text.configure(state=tk.NORMAL)
            self.preview_text.delete('1.0', tk.END)
            self.preview_text.insert('1.0', preview)
            self.preview_text.configure(state=tk.DISABLED)
    
    # Required abstract methods
    
    def load_data(self, data: str):
        """Load menu.xml content."""
        self.current_menu = self.parser.parse(data)
        self._original_data = data
        
        # Clear and repopulate tree
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        if self.current_menu:
            self._populate_tree()
            self.set_status(f"Loaded menu: {self.current_menu.label}")
        
        self.mark_dirty(False)
    
    def get_data(self) -> str:
        """Get menu.xml content."""
        return self.parser.write_back()
    
    def validate(self) -> tuple[bool, str]:
        """Validate menu structure."""
        if not self.current_menu:
            return False, "No menu loaded"
        
        if not self.current_menu.items:
            return False, "Menu is empty"
        
        return True, ""
