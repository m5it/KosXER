#!/usr/bin/env python3
"""
File Browser Widget for KosXER
"""

import os
import sys
import subprocess
from pathlib import Path
from typing import Optional, Callable, List
from dataclasses import dataclass

import tkinter as tk
from tkinter import ttk, messagebox

# Optional watchdog import
try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False
    Observer = None


@dataclass
class Bookmark:
    name: str
    path: str
    icon: str = "📁"


class FileBrowser(ttk.Frame):
    QUICK_ACCESS = [
        ("Home", Path.home(), "🏠"),
        (".Xresources", Path.home() / ".Xresources", "🎨"),
        (".Xdefaults", Path.home() / ".Xdefaults", "🎨"),
        ("OpenBox", Path.home() / ".config" / "openbox", "📦"),
        ("KosDWM", Path.home() / ".config" / "KosDWM", "📦"),
        (".config", Path.home() / ".config", "📁"),
        (".bashrc", Path.home() / ".bashrc", "📝"),
        (".zshrc", Path.home() / ".zshrc", "📝"),
    ]
    
    def __init__(self, parent, on_file_select: Optional[Callable] = None, **kwargs):
        super().__init__(parent, **kwargs)
        
        self.on_file_select = on_file_select
        self.current_path = Path.home()
        self.bookmarks: List[Bookmark] = []
        self.observer = None
        self.show_hidden = tk.BooleanVar(value=False)  # Default: hide hidden files
        
        self._create_widgets()
    
    def _create_widgets(self):
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Quick Access
        self.quick_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.quick_frame, text="Quick Access")
        
        ttk.Label(self.quick_frame, text="Common Config Locations", 
                 font=('Helvetica', 10, 'bold')).pack(pady=5)
        
        self.quick_scrollable = ttk.Frame(self.quick_frame)
        self.quick_scrollable.pack(fill=tk.BOTH, expand=True)
        
        # File System
        self.fs_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.fs_frame, text="File System")
        
        # Controls frame with hidden files checkbox
        controls_frame = ttk.Frame(self.fs_frame)
        controls_frame.pack(fill=tk.X, padx=5, pady=2)
        
        ttk.Button(controls_frame, text="⬆ Up", command=self._go_up).pack(side=tk.LEFT, padx=2)
        self.path_var = tk.StringVar(value=str(self.current_path))
        ttk.Entry(controls_frame, textvariable=self.path_var).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)
        ttk.Button(controls_frame, text="Go", command=self._go_to_path).pack(side=tk.LEFT, padx=2)
        
        # Show Hidden Files checkbox
        self.hidden_checkbox = ttk.Checkbutton(
            controls_frame, 
            text="Show Hidden",
            variable=self.show_hidden,
            command=self._on_hidden_toggled
        )
        self.hidden_checkbox.pack(side=tk.RIGHT, padx=5)
        
        tree_frame = ttk.Frame(self.fs_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.fs_tree = ttk.Treeview(tree_frame, columns=('type',), show='tree')
        self.fs_tree.heading('#0', text='Name')
        self.fs_tree.heading('type', text='Type')
        self.fs_tree.column('type', width=100)
        
        y_scroll = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.fs_tree.yview)
        self.fs_tree.configure(yscrollcommand=y_scroll.set)
        y_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.fs_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.fs_tree.bind('<Double-1>', self._on_fs_double_click)
        
        # Populate
        self._populate_quick_access()
        self._populate_fs_tree()
    
    def _on_hidden_toggled(self):
        """Handle show/hide hidden files toggle."""
        self._populate_fs_tree()
    
    def _populate_quick_access(self):
        for name, path, icon in self.QUICK_ACCESS:
            if path.exists():
                btn = ttk.Button(self.quick_scrollable, text=f"{icon} {name}",
                                command=lambda p=path: self._open_path(p))
                btn.pack(fill=tk.X, padx=5, pady=1)
    
    def _populate_fs_tree(self, path: Optional[Path] = None):
        """Populate file system tree."""
        if path:
            self.current_path = path
        
        # Clear tree
        for item in self.fs_tree.get_children():
            self.fs_tree.delete(item)
        
        # Add parent directory
        parent = self.current_path.parent
        if parent != self.current_path:
            self.fs_tree.insert('', 'end', text='..', values=('directory',))
        
        try:
            # Get directories first
            dirs = []
            files = []
            
            for item in sorted(self.current_path.iterdir(), key=lambda x: x.name.lower()):
                # Skip hidden files unless show_hidden is True
                if item.name.startswith('.') and not self.show_hidden.get():
                    continue
                
                if item.is_dir():
                    dirs.append(item)
                elif self._is_config_file(item):
                    files.append(item)
            
            # Add directories
            for d in dirs:
                self.fs_tree.insert('', 'end', text=d.name, values=('directory',))
            
            # Add files
            for f in files:
                self.fs_tree.insert('', 'end', text=f.name, values=('file',))
        
        except PermissionError:
            pass
    
    def _is_config_file(self, path: Path) -> bool:
        """Check if file is a supported config file."""
        name = path.name.lower()
        exts = {'.Xresources', '.Xdefaults', '.xml', '.conf', '.rc', 
                '.cfg', '.env', '.ini', '.sh', '.bashrc', '.zshrc', '.json'}
        
        if any(name.endswith(ext) for ext in exts):
            return True
        if name in {'menu.xml', 'rc.xml', 'tint2rc', 'picom.conf', 'config.json'}:
            return True
        return False
    
    def _open_path(self, path: Path):
        """Open a path."""
        if path.is_dir():
            self.current_path = path
            self.path_var.set(str(path))
            self._populate_fs_tree()
        elif path.is_file() and self.on_file_select:
            self.on_file_select(str(path))
    
    def _go_up(self):
        """Go to parent directory."""
        parent = self.current_path.parent
        if parent != self.current_path:
            self._open_path(parent)
    
    def _go_to_path(self):
        """Go to entered path."""
        path = Path(self.path_var.get())
        if path.exists():
            self._open_path(path)
    
    def _on_fs_double_click(self, event):
        """Handle double click on tree."""
        item = self.fs_tree.identify_row(event.y)
        if not item:
            return
        
        text = self.fs_tree.item(item, 'text')
        
        if text == '..':
            self._go_up()
        elif self.fs_tree.item(item, 'values')[0] == 'directory':
            self._open_path(self.current_path / text)
        else:
            if self.on_file_select:
                self.on_file_select(str(self.current_path / text))
    
    def set_show_hidden(self, show: bool):
        """Programmatically set show hidden files."""
        self.show_hidden.set(show)
        self._populate_fs_tree()
    
    def get_show_hidden(self) -> bool:
        """Get current show hidden state."""
        return self.show_hidden.get()
    
    def toggle_hidden(self):
        """Toggle hidden files display."""
        self.show_hidden.set(not self.show_hidden.get())
        self._populate_fs_tree()
    
    def refresh(self):
        """Refresh current view."""
        self._populate_fs_tree()
