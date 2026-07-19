#!/usr/bin/env python3
"""
KosDWM Auto-Generative Menu Editor Widget for KosXER

Treeview-based editor for KosDWM's auto-generative menu folders.
Each leaf folder under Menus/ is a generated window entry with:
  - config.json (title, windowContent, windowScript, loop, looptype)
  - content.html (static body)
  - ok.py (confirm callback)
"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog
from pathlib import Path
from typing import Optional

from gui.editor_base import EditorWidget
from parsers.kosdwm_autogen_menu_parser import (
    KosDWMMenuAutoGenParser,
    AutoGenMenuConfig,
    AutoGenMenuItem,
    VALID_LOOPTYPES,
)


class KosDWMAutogenMenuEditor(EditorWidget):
    """
    Editor widget for KosDWM auto-generative menus.

    Features:
    - Treeview of auto-gen menu folders
    - Properties panel for config.json fields
    - Text editor for content.html
    - Python editor for ok.py
    - Add/Remove menu entries
    - Validation of loop/looptype and required fields
    """

    LOOPTYPES = sorted(VALID_LOOPTYPES)

    def __init__(self, parent, main_window=None, filepath: Optional[str] = None, **kwargs):
        self.parser = KosDWMMenuAutoGenParser()
        self.menus_dir: Optional[str] = None
        self._current_item: Optional[AutoGenMenuItem] = None
        super().__init__(parent, main_window, filepath, **kwargs)

    def _create_editor_widgets(self):
        """Create the auto-gen menu editor UI."""
        # Main paned window: tree | notebook
        paned = ttk.PanedWindow(self.editor_frame, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Left: Treeview + buttons
        left_frame = ttk.Frame(paned)
        paned.add(left_frame, weight=1)

        tree_frame = ttk.Frame(left_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True)

        self.tree = ttk.Treeview(
            tree_frame,
            columns=("type",),
            show="tree headings",
            selectmode="browse",
        )
        self.tree.heading("#0", text="Auto-Gen Menus")
        self.tree.heading("type", text="Type")
        self.tree.column("type", width=80, anchor=tk.CENTER)

        y_scroll = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=y_scroll.set)
        y_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        btn_frame = ttk.Frame(left_frame)
        btn_frame.pack(fill=tk.X, pady=5)
        ttk.Button(btn_frame, text="Add", command=self._add_menu).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Delete", command=self._delete_menu).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Refresh", command=self._populate_tree).pack(side=tk.LEFT, padx=2)

        # Right: Notebook with Properties / Content / Script
        right_notebook = ttk.Notebook(paned)
        paned.add(right_notebook, weight=3)

        props_frame = ttk.Frame(right_notebook, padding=10)
        right_notebook.add(props_frame, text="Properties")
        self._create_properties_panel(props_frame)

        content_frame = ttk.Frame(right_notebook, padding=10)
        right_notebook.add(content_frame, text="content.html")
        self._create_content_editor(content_frame)

        script_frame = ttk.Frame(right_notebook, padding=10)
        right_notebook.add(script_frame, text="ok.py")
        self._create_script_editor(script_frame)

        # Bindings
        self.tree.bind("<<TreeviewSelect>>", self._on_select)

    def _create_properties_panel(self, parent):
        """Create config.json properties panel."""
        # Name (read-only, derived from folder)
        ttk.Label(parent, text="Name:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.prop_name_var = tk.StringVar()
        ttk.Entry(parent, textvariable=self.prop_name_var, state="readonly").grid(
            row=0, column=1, sticky=tk.EW, pady=2, padx=5
        )

        # Title
        ttk.Label(parent, text="Title:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.prop_title_var = tk.StringVar()
        ttk.Entry(parent, textvariable=self.prop_title_var).grid(
            row=1, column=1, sticky=tk.EW, pady=2, padx=5
        )

        # windowContent
        ttk.Label(parent, text="windowContent:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.prop_content_file_var = tk.StringVar()
        ttk.Entry(parent, textvariable=self.prop_content_file_var).grid(
            row=2, column=1, sticky=tk.EW, pady=2, padx=5
        )

        # windowScript
        ttk.Label(parent, text="windowScript:").grid(row=3, column=0, sticky=tk.W, pady=2)
        self.prop_script_var = tk.StringVar()
        ttk.Entry(parent, textvariable=self.prop_script_var).grid(
            row=3, column=1, sticky=tk.EW, pady=2, padx=5
        )

        # loop
        ttk.Label(parent, text="Loop:").grid(row=4, column=0, sticky=tk.W, pady=2)
        self.prop_loop_var = tk.StringVar()
        ttk.Entry(parent, textvariable=self.prop_loop_var, width=10).grid(
            row=4, column=1, sticky=tk.W, pady=2, padx=5
        )

        # looptype
        ttk.Label(parent, text="Loop Type:").grid(row=5, column=0, sticky=tk.W, pady=2)
        self.prop_looptype_var = tk.StringVar()
        combo = ttk.Combobox(
            parent,
            textvariable=self.prop_looptype_var,
            values=self.LOOPTYPES,
            state="readonly",
            width=12,
        )
        combo.grid(row=5, column=1, sticky=tk.W, pady=2, padx=5)

        # Apply button
        apply_btn = ttk.Button(parent, text="Apply Properties", command=self._apply_properties)
        apply_btn.grid(row=6, column=0, columnspan=2, sticky=tk.EW, pady=15)

        # Validation feedback label
        self.prop_feedback_var = tk.StringVar()
        feedback_label = ttk.Label(parent, textvariable=self.prop_feedback_var, foreground="red")
        feedback_label.grid(row=7, column=0, columnspan=2, sticky=tk.EW, pady=5)

        parent.columnconfigure(1, weight=1)

    def _create_content_editor(self, parent):
        """Create text editor for content.html."""
        self.content_text = tk.Text(parent, wrap=tk.WORD, undo=True, font=("Courier", 10))
        self.content_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        y_scroll = ttk.Scrollbar(parent, orient=tk.VERTICAL, command=self.content_text.yview)
        self.content_text.configure(yscrollcommand=y_scroll.set)
        y_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.content_text.bind("<<Modified>>", self._on_text_modified)

    def _create_script_editor(self, parent):
        """Create Python editor for ok.py."""
        self.script_text = tk.Text(parent, wrap=tk.NONE, undo=True, font=("Courier", 10))
        self.script_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        y_scroll = ttk.Scrollbar(parent, orient=tk.VERTICAL, command=self.script_text.yview)
        self.script_text.configure(yscrollcommand=y_scroll.set)
        y_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.script_text.bind("<<Modified>>", self._on_text_modified)

    def _on_text_modified(self, event=None):
        """Mark editor dirty when text widgets change."""
        widget = event.widget if event else self.content_text
        if widget.edit_modified():
            self.mark_dirty(True)
            widget.edit_modified(False)

    def _populate_tree(self):
        """Populate treeview with auto-gen menu items."""
        for child in self.tree.get_children():
            self.tree.delete(child)

        if not self.parser.items:
            return

        root_node = self.tree.insert("", "end", text="Menus", values=("root",), open=True)
        for item in sorted(self.parser.items.values(), key=lambda i: i.name):
            rel = Path(item.folder_path).name
            self.tree.insert(root_node, "end", text=rel, values=("menu",), tags=(item.name,))

    def _on_select(self, event=None):
        """Load selected item into editors."""
        selection = self.tree.selection()
        if not selection:
            return

        tags = self.tree.item(selection[0], "tags")
        if not tags:
            return

        name = tags[0]
        item = self.parser.get_item(name)
        if item is None:
            return

        self._current_item = item
        cfg = item.config

        self.prop_name_var.set(item.name)
        self.prop_title_var.set(cfg.title or "")
        self.prop_content_file_var.set(cfg.window_content or "")
        self.prop_script_var.set(cfg.window_script or "")
        self.prop_loop_var.set(str(cfg.loop) if cfg.loop is not None else "")
        self.prop_looptype_var.set(cfg.looptype or "")
        self.prop_feedback_var.set("")

        self.content_text.delete("1.0", tk.END)
        if item.content_body is not None:
            self.content_text.insert("1.0", item.content_body)
        self.content_text.edit_modified(False)

        self.script_text.delete("1.0", tk.END)
        if item.ok_script is not None:
            self.script_text.insert("1.0", item.ok_script)
        self.script_text.edit_modified(False)

    def _apply_properties(self):
        """Apply property panel changes to current item."""
        if self._current_item is None:
            return

        item = self._current_item
        cfg = item.config

        cfg.title = self.prop_title_var.get() or None
        cfg.window_content = self.prop_content_file_var.get() or None
        cfg.window_script = self.prop_script_var.get() or None

        loop_text = self.prop_loop_var.get().strip()
        if loop_text:
            try:
                cfg.loop = int(loop_text)
            except ValueError:
                self.prop_feedback_var.set("Loop must be an integer")
                return
        else:
            cfg.loop = None

        looptype = self.prop_looptype_var.get()
        cfg.looptype = looptype if looptype else None

        # Update content/script bodies from text widgets
        item.content_body = self.content_text.get("1.0", tk.END + "-1c")
        item.ok_script = self.script_text.get("1.0", tk.END + "-1c")

        # Validate
        errors = item.validate()
        if errors:
            self.prop_feedback_var.set("; ".join(errors))
            return

        self.prop_feedback_var.set("")
        self.mark_dirty(True)
        self._populate_tree()
        self.set_status(f"Updated {item.name}")

    def _add_menu(self):
        """Add a new auto-gen menu entry."""
        name = simpledialog.askstring("New Menu", "Enter menu folder name:")
        if not name:
            return

        if self.parser.get_item(name):
            messagebox.showerror("Error", f"Menu '{name}' already exists.")
            return

        if self.menus_dir is None:
            messagebox.showerror("Error", "No menus directory loaded.")
            return

        folder_path = Path(self.menus_dir) / name
        folder_path.mkdir(parents=True, exist_ok=True)

        new_item = AutoGenMenuItem(
            name=name,
            folder_path=str(folder_path),
            config=AutoGenMenuConfig(window_content="content.html"),
            content_body="",
            ok_script="def run(window):\n    pass\n",
        )
        self.parser.add_item(new_item)
        self.mark_dirty(True)
        self._populate_tree()

    def _delete_menu(self):
        """Delete selected auto-gen menu entry."""
        selection = self.tree.selection()
        if not selection:
            return

        tags = self.tree.item(selection[0], "tags")
        if not tags:
            return

        name = tags[0]
        if messagebox.askyesno("Confirm", f"Delete menu '{name}'?"):
            self.parser.remove_item(name)
            self._current_item = None
            self.mark_dirty(True)
            self._populate_tree()
            self._clear_editors()

    def _clear_editors(self):
        """Clear all editor fields."""
        self.prop_name_var.set("")
        self.prop_title_var.set("")
        self.prop_content_file_var.set("")
        self.prop_script_var.set("")
        self.prop_loop_var.set("")
        self.prop_looptype_var.set("")
        self.prop_feedback_var.set("")
        self.content_text.delete("1.0", tk.END)
        self.script_text.delete("1.0", tk.END)

    # Required EditorWidget methods

    def load_data(self, data: str):
        """Load an auto-generative menu directory."""
        self.menus_dir = data
        self.parser.parse(data)
        self._original_data = data
        self._populate_tree()
        self._clear_editors()
        self.mark_dirty(False)
        self.set_status(f"Loaded auto-gen menus from {data}")

    def get_data(self) -> str:
        """Return the menus directory path."""
        return self.menus_dir or ""

    def validate(self) -> tuple[bool, str]:
        """Validate all auto-gen menu items."""
        if not self.parser.items:
            return False, "No auto-gen menus loaded"

        is_valid, errors = self.parser.validate()
        if not is_valid:
            return False, "\n".join(errors)

        return True, ""
