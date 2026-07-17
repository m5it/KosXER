#!/usr/bin/env python3
"""
File Browser Widget for KosXER

Provides a tree view of the file system with filtering
for configuration files, quick access to common configs,
bookmarks, and file watching.
"""

import os
import sys
import subprocess
import threading
from pathlib import Path
from typing import Optional, Callable, Dict, List
from dataclasses import dataclass

import tkinter as tk
from tkinter import ttk, messagebox

# Try to import watchdog for file watching
try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
    WATCHDOG_AVAILABLE = True
    
    class ConfigFileHandler(FileSystemEventHandler):
        """Handler for file system events."""
        
        def __init__(self, callback: Callable):
            self.callback = callback
        
        def on_modified(self, event):
            if not event.is_directory:
                self.callback(event.src_path)
        
        def on_created(self, event):
            if not event.is_directory:
                self.callback(event.src_path)
        
        def on_deleted(self, event):
            self.callback(event.src_path)
            
except ImportError:
    WATCHDOG_AVAILABLE = False
    Observer = None
    ConfigFileHandler = None


@dataclass
class Bookmark:
    """Represents a bookmarked location."""
    name: str
    path: str
    icon: str = "📁"


class FileBrowser(ttk.Frame):
    """
    File browser widget for navigating configuration files.
    
    Features:
    - Tree view of directories with config file filtering
    - Quick access to common config locations
    - Bookmark/favorites system
    - File watcher for external changes (optional)
    - Context menu with file operations
    """
    
    # Common config directories and files
    QUICK_ACCESS = [
        ("Home", Path.home(), "🏠"),
        (".Xresources", Path.home() / ".Xresources", "🎨"),
        (".Xdefaults", Path.home() / ".Xdefaults", "🎨"),
        ("OpenBox", Path.home() / ".config" / "openbox", "📦"),
        ("KosDWM", Path.home() / ".config" / "KosDWM", "📦"),
        ("i3", Path.home() / ".config" / "i3", "📦"),
        ("bspwm", Path.home() / ".config" / "bspwm", "📦"),
        ("sxhkd", Path.home() / ".config" / "sxhkd", "📦"),
        ("tint2", Path.home() / ".config" / "tint2", "📦"),
        ("picom", Path.home() / ".config" / "picom", "📦"),
        ("dunst", Path.home() / ".config" / "dunst", "📦"),
        (".bashrc", Path.home() / ".bashrc", "📝"),
        (".zshrc", Path.home() / ".zshrc", "📝"),
        (".profile", Path.home() / ".profile", "📝"),
        (".config", Path.home() / ".config", "📁"),
    ]
    
    def __init__(self, parent, 
                 on_file_select: Optional[Callable] = None,
                 on_file_change: Optional[Callable] = None,
                 **kwargs):
        super().__init__(parent, **kwargs)
        
        self.on_file_select = on_file_select
        self.on_file_change = on_file_change
        self.current_path = Path.home()
        self.bookmarks: List[Bookmark] = []
        self.observer = None
        self.watched_paths: set = set()
        
        self._create_widgets()
        self._load_bookmarks()
        self._populate_quick_access()
    
    def _create_widgets(self):
        """Create browser widgets."""
        # Notebook for tabs
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Quick Access tab
        self.quick_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.quick_frame, text="Quick Access")
        self._create_quick_access_panel()
        
        # File System tab
        self.fs_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.fs_frame, text="File System")
        self._create_filesystem_panel()
        
        # Bookmarks tab
        self.bookmark_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.bookmark_frame, text="Bookmarks")
        self._create_bookmarks_panel()
    
    def _create_quick_access_panel(self):
        """Create quick access panel."""
        ttk.Label(self.quick_frame, text="Common Config Locations", 
                 font=('Helvetica', 10, 'bold')).pack(pady=5)
        
        # Scrollable frame
        canvas = tk.Canvas(self.quick_frame)
        scrollbar = ttk.Scrollbar(self.quick_frame, orient=tk.VERTICAL, command=canvas.yview)
        self.quick_scrollable = ttk.Frame(canvas)
        
        self.quick_scrollable.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=self.quick_scrollable, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    
    def _create_filesystem_panel(self):
        """Create file system tree panel."""
        # Path bar
        path_frame = ttk.Frame(self.fs_frame)
        path_frame.pack(fill=tk.X, padx=5, pady=2)
        
        ttk.Button(path_frame, text="⬆ Up", command=self._go_up).pack(side=tk.LEFT, padx=2)
        self.path_var = tk.StringVar(value=str(self.current_path))
        path_entry = ttk.Entry(path_frame, textvariable=self.path_var)
        path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)
        ttk.Button(path_frame, text="Go", command=self._go_to_path).pack(side=tk.LEFT, padx=2)
        
        # Treeview
        tree_frame = ttk.Frame(self.fs_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.fs_tree = ttk.Treeview(tree_frame, columns=('type', 'size'), show='tree')
        self.fs_tree.heading('#0', text='Name')
        self.fs_tree.heading('type', text='Type')
        self.fs_tree.heading('size', text='Size')
        self.fs_tree.column('type', width=100)
        self.fs_tree.column('size', width=80)
        
        # Scrollbars
        y_scroll = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.fs_tree.yview)
        x_scroll = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL, command=self.fs_tree.xview)
        self.fs_tree.configure(yscrollcommand=y_scroll.set, xscrollcommand=x_scroll.set)
        
        y_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        x_scroll.pack(side=tk.BOTTOM, fill=tk.X)
        self.fs_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Bindings
        self.fs_tree.bind('<Double-1>', self._on_fs_double_click)
        self.fs_tree.bind('<Button-3>', self._show_context_menu)
    
    def _create_bookmarks_panel(self):
        """Create bookmarks panel."""
        ttk.Label(self.bookmark_frame, text="Bookmarks", 
                 font=('Helvetica', 10, 'bold')).pack(pady=5)
        
        # Bookmark list
        self.bookmark_list = ttk.Treeview(self.bookmark_frame, columns=('path',), show='tree')
        self.bookmark_list.heading('#0', text='Name')
        self.bookmark_list.heading('path', text='Path')
        self.bookmark_list.column('path', width=200)
        self.bookmark_list.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Buttons
        btn_frame = ttk.Frame(self.bookmark_frame)
        btn_frame.pack(fill=tk.X, padx=5, pady=5)
        ttk.Button(btn_frame, text="Add Current", command=self._add_bookmark).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Remove", command=self._remove_bookmark).pack(side=tk.LEFT, padx=2)
        
        # Bindings
        self.bookmark_list.bind('<Double-1>', self._on_bookmark_double_click)
    
    def _populate_quick_access(self):
        """Populate quick access buttons."""
        for name, path, icon in self.QUICK_ACCESS:
            if path.exists():
                btn_text = f"{icon} {name}"
                btn = ttk.Button(
                    self.quick_scrollable, 
                    text=btn_text,
                    command=lambda p=path: self._open_path(p)
                )
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
            node = self.fs_tree.insert('', 'end', text='..', values=('directory', ''), open=False)
            self.fs_tree.item(node, tags=('parent',))
        
        try:
            # Get directories first
            dirs = []
            files = []
            
            for item in sorted(self.current_path.iterdir(), key=lambda x: x.name.lower()):
                if item.name.startswith('.'):
                    continue
                
                if item.is_dir():
                    dirs.append(item)
                elif self._is_config_file(item):
                    files.append(item)
            
            # Add directories
            for d in dirs:
                size = len(list(d.iterdir())) if d.is_dir() else 0
                node = self.fs_tree.insert('', 'end', text=d.name,
                                          values=('directory', f'{size} items'), open=False)
                self.fs_tree.insert(node, 'end', text='')  # Dummy for expand
            
            # Add files
            for f in files:
                size = self._format_size(f.stat().st_size)
                self.fs_tree.insert('', 'end', text=f.name,
                                   values=('file', size))
        
        except PermissionError:
            messagebox.showerror("Error", f"Permission denied: {self.current_path}")
    
    def _is_config_file(self, path: Path) -> bool:
        """Check if file is a supported config file."""
        name = path.name.lower()
        extensions = {'.Xresources', '.Xdefaults', '.xml', '.conf', '.rc', 
                     '.cfg', '.env', '.ini', '.sh', '.bashrc', '.zshrc', '.json'}
        
        if any(name.endswith(ext) for ext in extensions):
            return True
        if name in {'menu.xml', 'rc.xml', 'tint2rc', 'picom.conf', 'config.json'}:
            return True
        return False
    
    def _format_size(self, size: int) -> str:
        """Format file size."""
        for unit in ['B', 'KB', 'MB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} GB"
    
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
        else:
            messagebox.showerror("Error", f"Path not found: {path}")
    
    def _on_fs_double_click(self, event):
        """Handle double click on tree."""
        item = self.fs_tree.identify_row(event.y)
        if not item:
            return
        
        values = self.fs_tree.item(item, 'values')
        text = self.fs_tree.item(item, 'text')
        
        if text == '..':
            self._go_up()
        elif values and values[0] == 'directory':
            new_path = self.current_path / text
            self._open_path(new_path)
        else:
            file_path = self.current_path / text
            if self.on_file_select:
                self.on_file_select(str(file_path))
    
    def _show_context_menu(self, event):
        """Show context menu."""
        item = self.fs_tree.identify_row(event.y)
        if not item:
            return
        
        self.fs_tree.selection_set(item)
        text = self.fs_tree.item(item, 'text')
        file_path = self.current_path / text
        
        menu = tk.Menu(self, tearoff=0)
        menu.add_command(label="Open", command=lambda: self._open_file(file_path))
        menu.add_command(label="Open With...", command=lambda: self._open_with(file_path))
        menu.add_separator()
        menu.add_command(label="Copy Path", command=lambda: self._copy_path(file_path))
        menu.add_command(label="Open in Terminal", command=lambda: self._open_terminal(file_path.parent))
        menu.add_separator()
        menu.add_command(label="Add to Bookmarks", command=lambda: self._add_bookmark_path(file_path))
        
        menu.post(event.x_root, event.y_root)
    
    def _open_file(self, path: Path):
        """Open file in editor."""
        if self.on_file_select:
            self.on_file_select(str(path))
    
    def _open_with(self, path: Path):
        """Open file with external application."""
        try:
            if sys.platform == 'linux':
                subprocess.run(['xdg-open', str(path)])
            elif sys.platform == 'darwin':
                subprocess.run(['open', str(path)])
            else:
                os.startfile(str(path))
        except Exception as e:
            messagebox.showerror("Error", f"Could not open file: {e}")
    
    def _copy_path(self, path: Path):
        """Copy path to clipboard."""
        self.clipboard_clear()
        self.clipboard_append(str(path))
    
    def _open_terminal(self, path: Path):
        """Open terminal at path."""
        try:
            if sys.platform == 'linux':
                subprocess.Popen(['x-terminal-emulator'], cwd=str(path))
            elif sys.platform == 'darwin':
                subprocess.Popen(['open', '-a', 'Terminal', str(path)])
        except Exception as e:
            messagebox.showerror("Error", f"Could not open terminal: {e}")
    
    def _load_bookmarks(self):
        """Load bookmarks from storage."""
        default_bookmarks = [
            Bookmark("Home", str(Path.home())),
            Bookmark(".config", str(Path.home() / ".config")),
        ]
        self.bookmarks = default_bookmarks
        self._populate_bookmarks()
    
    def _populate_bookmarks(self):
        """Populate bookmark list."""
        for item in self.bookmark_list.get_children():
            self.bookmark_list.delete(item)
        
        for bm in self.bookmarks:
            self.bookmark_list.insert('', 'end', text=f"📁 {bm.name}", values=(bm.path,))
    
    def _add_bookmark(self):
        """Add current directory to bookmarks."""
        self._add_bookmark_path(self.current_path)
    
    def _add_bookmark_path(self, path: Path):
        """Add path to bookmarks."""
        name = path.name if path.name else str(path)
        bm = Bookmark(name, str(path))
        self.bookmarks.append(bm)
        self._populate_bookmarks()
    
    def _remove_bookmark(self):
        """Remove selected bookmark."""
        selection = self.bookmark_list.selection()
        if selection:
            index = self.bookmark_list.index(selection[0])
            if 0 <= index < len(self.bookmarks):
                del self.bookmarks[index]
                self._populate_bookmarks()
    
    def _on_bookmark_double_click(self, event):
        """Open bookmark on double click."""
        selection = self.bookmark_list.selection()
        if selection:
            path = self.bookmark_list.item(selection[0], 'values')[0]
            self._open_path(Path(path))
    
    def set_status(self, message: str):
        """Update status."""
        pass
    
    def start_watching(self, path: str):
        """Start watching a file for changes."""
        if not WATCHDOG_AVAILABLE:
            return
        
        if self.observer is None and Observer is not None:
            self.observer = Observer()
        
        if self.observer and path not in self.watched_paths:
            handler = ConfigFileHandler(self._on_file_changed)
            self.observer.schedule(handler, path, recursive=False)
            self.watched_paths.add(path)
            self.observer.start()
    
    def _on_file_changed(self, filepath: str):
        """Handle file change event."""
        if self.on_file_change:
            self.on_file_change(filepath)
    
    def stop_watching(self):
        """Stop all file watchers."""
        if self.observer:
            self.observer.stop()
            self.observer.join()
            self.observer = None
        self.watched_paths.clear()
    
    def refresh(self):
        """Refresh current view."""
        self._populate_fs_tree()
