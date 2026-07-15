#!/usr/bin/env python3
"""
KosXER - X11 Configuration Editor

A GUI editor for .Xresources, OpenBox menu.xml, and other Unix desktop configs.
"""

import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any

import tkinter as tk
from tkinter import ttk, messagebox, filedialog

# Ensure we can import our modules
sys.path.insert(0, str(Path(__file__).parent))

from config.constants import APP_NAME, VERSION
from config.settings import Settings

from parsers import (
    detect_parser, get_file_type_info, create_parser_for_file,
    ParserRegistry, XResourcesParser, OpenBoxMenuParser, GenericKVParser
)

from gui.file_browser import FileBrowser
from gui.xresources_editor import XResourcesEditor
from gui.openbox_editor import OpenBoxEditor
from gui.kv_editor import KVEditor


class KosXERApp:
    """
    Main application class for KosXER.
    
    Integrates all components: file browser, editors, menus, and status bar.
    """
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title(f"{APP_NAME} v{VERSION}")
        self.root.geometry("1400x900")
        self.root.minsize(1000, 700)
        
        self.settings = Settings()
        self.registry = ParserRegistry()
        
        # Track open files
        self.open_files: Dict[str, Any] = {}  # path -> editor
        self.current_file: Optional[str] = None
        self.recent_files: list = []
        
        # Create UI
        self._create_menu()
        self._create_toolbar()
        self._create_main_layout()
        self._create_statusbar()
        
        # Bind events
        self._bind_shortcuts()
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        
        # Center window
        self._center_window()
    
    def _center_window(self):
        """Center window on screen."""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
    
    def _create_menu(self):
        """Create menu bar."""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="New", command=self._file_new, 
                             accelerator="Ctrl+N")
        file_menu.add_command(label="Open...", command=self._file_open,
                             accelerator="Ctrl+O")
        file_menu.add_command(label="Save", command=self._file_save,
                             accelerator="Ctrl+S")
        file_menu.add_command(label="Save As...", command=self._file_save_as,
                             accelerator="Ctrl+Shift+S")
        file_menu.add_separator()
        
        # Recent files submenu
        self.recent_menu = tk.Menu(file_menu, tearoff=0)
        file_menu.add_cascade(label="Recent Files", menu=self.recent_menu)
        self._update_recent_menu()
        
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self._on_close,
                             accelerator="Alt+F4")
        
        # Edit menu
        edit_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Edit", menu=edit_menu)
        edit_menu.add_command(label="Undo", command=self._edit_undo,
                             accelerator="Ctrl+Z")
        edit_menu.add_command(label="Redo", command=self._edit_redo,
                             accelerator="Ctrl+Y")
        edit_menu.add_separator()
        edit_menu.add_command(label="Cut", command=self._edit_cut,
                             accelerator="Ctrl+X")
        edit_menu.add_command(label="Copy", command=self._edit_copy,
                             accelerator="Ctrl+C")
        edit_menu.add_command(label="Paste", command=self._edit_paste,
                             accelerator="Ctrl+V")
        
        # View menu
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="View", menu=view_menu)
        view_menu.add_command(label="Toggle File Browser", 
                             command=self._toggle_file_browser,
                             accelerator="Ctrl+B")
        view_menu.add_separator()
        view_menu.add_command(label="Next Tab", command=self._next_tab,
                             accelerator="Ctrl+Tab")
        view_menu.add_command(label="Previous Tab", command=self._prev_tab,
                             accelerator="Ctrl+Shift+Tab")
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self._show_about)
    
    def _create_toolbar(self):
        """Create toolbar."""
        toolbar = ttk.Frame(self.root, relief=tk.RAISED, borderwidth=1)
        toolbar.pack(side=tk.TOP, fill=tk.X)
        
        # File operations
        ttk.Button(toolbar, text="New", command=self._file_new, width=8).pack(side=tk.LEFT, padx=2, pady=2)
        ttk.Button(toolbar, text="Open", command=self._file_open, width=8).pack(side=tk.LEFT, padx=2, pady=2)
        ttk.Button(toolbar, text="Save", command=self._file_save, width=8).pack(side=tk.LEFT, padx=2, pady=2)
        
        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=2)
        
        # Navigation
        ttk.Button(toolbar, text="←", command=self._prev_tab, width=3).pack(side=tk.LEFT, padx=2, pady=2)
        ttk.Button(toolbar, text="→", command=self._next_tab, width=3).pack(side=tk.LEFT, padx=2, pady=2)
        
        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=2)
        
        # File browser toggle
        self.fb_btn = ttk.Button(toolbar, text="Hide Browser", command=self._toggle_file_browser, width=12)
        self.fb_btn.pack(side=tk.LEFT, padx=2, pady=2)
        
        # Spacer
        ttk.Frame(toolbar).pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # About
        ttk.Button(toolbar, text="About", command=self._show_about, width=8).pack(side=tk.RIGHT, padx=2, pady=2)
    
    def _create_main_layout(self):
        """Create main layout with file browser and editor area."""
        # Main paned window
        self.main_paned = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        self.main_paned.pack(fill=tk.BOTH, expand=True)
        
        # Left: File browser
        self.browser_frame = ttk.Frame(self.main_paned, width=250)
        self.main_paned.add(self.browser_frame, weight=0)
        
        self.file_browser = FileBrowser(
            self.browser_frame,
            on_file_select=self._open_file,
            on_file_change=self._on_external_change
        )
        self.file_browser.pack(fill=tk.BOTH, expand=True)
        
        # Right: Editor area with notebook (tabs)
        self.editor_frame = ttk.Frame(self.main_paned)
        self.main_paned.add(self.editor_frame, weight=1)
        
        # Notebook for tabs
        self.notebook = ttk.Notebook(self.editor_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Bind tab change
        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)
        
        # Welcome tab
        self.welcome_frame = ttk.Frame(self.notebook)
        self._create_welcome_content(self.welcome_frame)
        self.notebook.add(self.welcome_frame, text="Welcome")
    
    def _create_welcome_content(self, parent):
        """Create welcome screen content."""
        text = tk.Text(parent, wrap=tk.WORD, padx=20, pady=20, 
                      font=('Courier', 12))
        text.pack(fill=tk.BOTH, expand=True)
        text.insert('1.0', f"""
Welcome to {APP_NAME} v{VERSION}

A GUI editor for X11 configuration files.

Supported Formats:
  • .Xresources / .Xdefaults  - X11 resource definitions
  • menu.xml / rc.xml          - OpenBox configuration
  • .conf / .env / .rc         - Generic key-value configs
  • .bashrc / .zshrc           - Shell environment files

Getting Started:
  1. Use File > Open or Ctrl+O to open a config file
  2. Browse Quick Access for common config locations
  3. Edit values directly in the appropriate editor
  4. Save with Ctrl+S

Keyboard Shortcuts:
  Ctrl+O    Open file
  Ctrl+S    Save current file
  Ctrl+Shift+S  Save as
  Ctrl+W    Close current tab
  Ctrl+B    Toggle file browser
  Ctrl+Tab  Next tab
  Ctrl+Shift+Tab  Previous tab
  Ctrl+Q    Quit

For more information, visit the Help menu.
""")
        text.config(state=tk.DISABLED)
    
    def _create_statusbar(self):
        """Create status bar."""
        self.statusbar = ttk.Frame(self.root, relief=tk.SUNKEN, borderwidth=1)
        self.statusbar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # File info
        self.status_file = ttk.Label(self.statusbar, text="No file open", 
                                    anchor=tk.W, width=40)
        self.status_file.pack(side=tk.LEFT, padx=5)
        
        ttk.Separator(self.statusbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=5)
        
        # Parser type
        self.status_parser = ttk.Label(self.statusbar, text="", width=20)
        self.status_parser.pack(side=tk.LEFT, padx=5)
        
        ttk.Separator(self.statusbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=5)
        
        # Modified indicator
        self.status_modified = ttk.Label(self.statusbar, text="", foreground="red", width=10)
        self.status_modified.pack(side=tk.LEFT, padx=5)
        
        # Position
        self.status_pos = ttk.Label(self.statusbar, text="", anchor=tk.E, width=20)
        self.status_pos.pack(side=tk.RIGHT, padx=5)
    
    def _bind_shortcuts(self):
        """Bind keyboard shortcuts."""
        self.root.bind("<Control-n>", lambda e: self._file_new())
        self.root.bind("<Control-o>", lambda e: self._file_open())
        self.root.bind("<Control-s>", lambda e: self._file_save())
        self.root.bind("<Control-S>", lambda e: self._file_save_as())  # Shift+S
        self.root.bind("<Control-w>", lambda e: self._close_current_tab())
        self.root.bind("<Control-b>", lambda e: self._toggle_file_browser())
        self.root.bind("<Control-q>", lambda e: self._on_close())
        self.root.bind("<Control-Tab>", lambda e: self._next_tab())
        self.root.bind("<Control-ISO_Left_Tab>", lambda e: self._prev_tab())  # Shift+Tab
    
    def _open_file(self, filepath: str):
        """Open a file in the editor."""
        filepath = str(filepath)
        
        # Check if already open
        if filepath in self.open_files:
            # Switch to that tab
            for i, tab in enumerate(self.notebook.tabs()):
                if self.notebook.tab(tab, "text") == Path(filepath).name:
                    self.notebook.select(i)
                    return
        
        try:
            # Detect file type and create appropriate editor
            parser_class = detect_parser(filepath)
            if not parser_class:
                messagebox.showerror("Error", f"Cannot determine file type: {filepath}")
                return
            
            # Create editor based on parser type
            if parser_class == XResourcesParser:
                editor = XResourcesEditor(self.notebook, self, filepath)
            elif parser_class == OpenBoxMenuParser:
                editor = OpenBoxEditor(self.notebook, self, filepath)
            elif parser_class == GenericKVParser:
                editor = KVEditor(self.notebook, self, filepath)
            else:
                messagebox.showerror("Error", f"No editor available for: {filepath}")
                return
            
            # Load file content
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            editor.load_data(content)
            
            # Add to notebook
            tab_text = Path(filepath).name
            if len(tab_text) > 20:
                tab_text = tab_text[:17] + "..."
            
            editor.pack(fill=tk.BOTH, expand=True)
            self.notebook.add(editor, text=tab_text)
            self.notebook.select(editor)
            
            # Track
            self.open_files[filepath] = editor
            self.current_file = filepath
            self._add_recent_file(filepath)
            
            # Update status
            desc, icon, _ = get_file_type_info(filepath)
            self._update_status(filepath, desc)
            
            # Start watching for external changes
            self.file_browser.start_watching(filepath)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open file:\n{str(e)}")
    
    def _update_status(self, filepath: str, parser_desc: str):
        """Update status bar."""
        self.status_file.config(text=f"📄 {Path(filepath).name}")
        self.status_parser.config(text=f"🔧 {parser_desc}")
        self.root.title(f"{Path(filepath).name} - {APP_NAME} v{VERSION}")
    
    def _on_tab_changed(self, event=None):
        """Handle tab change."""
        current = self.notebook.select()
        if not current:
            return
        
        # Find which file this tab represents
        for filepath, editor in self.open_files.items():
            if str(editor) == str(current):
                self.current_file = filepath
                desc, _, _ = get_file_type_info(filepath)
                self._update_status(filepath, desc)
                break
    
    def _file_new(self):
        """Create new file."""
        # For now, just show a message
        messagebox.showinfo("New File", "Select file type from File > Open\nDirect creation coming soon!")
    
    def _file_open(self):
        """Open file dialog."""
        filetypes = [
            ("All Config Files", "*.Xresources *.Xdefaults *.xml *.conf *.rc *.env *.sh"),
            ("X Resources", "*.Xresources *.Xdefaults"),
            ("OpenBox", "menu.xml rc.xml"),
            ("Config Files", "*.conf *.rc *.cfg *.env"),
            ("Shell Scripts", "*.sh .bashrc .zshrc"),
            ("All Files", "*.*")
        ]
        
        filepath = filedialog.askopenfilename(
            title="Open Configuration File",
            filetypes=filetypes
        )
        
        if filepath:
            self._open_file(filepath)
    
    def _file_save(self):
        """Save current file."""
        if not self.current_file:
            self._file_save_as()
            return
        
        editor = self.open_files.get(self.current_file)
        if not editor:
            return
        
        try:
            content = editor.get_data()
            with open(self.current_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            editor.mark_dirty(False)
            self._update_modified_indicator()
            self.status_modified.config(text="✓ Saved")
            self.root.after(2000, lambda: self.status_modified.config(text=""))
            
        except Exception as e:
            messagebox.showerror("Save Error", str(e))
    
    def _file_save_as(self):
        """Save as dialog."""
        if not self.current_file:
            return
        
        filepath = filedialog.asksaveasfilename(
            title="Save Configuration File",
            defaultextension=".Xresources",
            initialfile=Path(self.current_file).name
        )
        
        if filepath:
            old_path = self.current_file
            self.current_file = filepath
            
            # Update editor
            editor = self.open_files.pop(old_path)
            self.open_files[filepath] = editor
            editor.set_filepath(filepath)
            
            # Rename tab
            for i, tab in enumerate(self.notebook.tabs()):
                if self.notebook.tab(tab, "text") == Path(old_path).name:
                    tab_text = Path(filepath).name
                    if len(tab_text) > 20:
                        tab_text = tab_text[:17] + "..."
                    self.notebook.tab(tab, text=tab_text)
                    break
            
            self._file_save()
    
    def _close_current_tab(self):
        """Close current tab."""
        current = self.notebook.select()
        if current:
            # Check if modified
            for filepath, editor in list(self.open_files.items()):
                if str(editor) == str(current):
                    if editor.has_changes():
                        response = messagebox.askyesnocancel(
                            "Unsaved Changes",
                            f"{Path(filepath).name} has unsaved changes. Save?"
                        )
                        if response is True:
                            self._file_save()
                        elif response is False:
                            pass
                        else:
                            return
                    
                    del self.open_files[filepath]
                    self.file_browser.stop_watching()
                    break
            
            self.notebook.forget(current)
            
            # If no tabs left, show welcome
            if len(self.notebook.tabs()) == 0:
                self.notebook.add(self.welcome_frame, text="Welcome")
                self.current_file = None
                self.status_file.config(text="No file open")
                self.status_parser.config(text="")
                self.root.title(f"{APP_NAME} v{VERSION}")
    
    def _edit_undo(self):
        """Undo in current editor."""
        editor = self.open_files.get(self.current_file)
        if editor:
            editor.undo()
    
    def _edit_redo(self):
        """Redo in current editor."""
        editor = self.open_files.get(self.current_file)
        if editor:
            editor.redo()
    
    def _edit_cut(self):
        """Cut in current editor."""
        self.root.focus_get().event_generate("<<Cut>>")
    
    def _edit_copy(self):
        """Copy in current editor."""
        self.root.focus_get().event_generate("<<Copy>>")
    
    def _edit_paste(self):
        """Paste in current editor."""
        self.root.focus_get().event_generate("<<Paste>>")
    
    def _toggle_file_browser(self):
        """Toggle file browser visibility."""
        if self.browser_frame.winfo_viewable():
            self.browser_frame.pack_forget()
            self.fb_btn.config(text="Show Browser")
        else:
            self.browser_frame.pack(side=tk.LEFT, fill=tk.Y)
            self.fb_btn.config(text="Hide Browser")
    
    def _next_tab(self):
        """Switch to next tab."""
        tabs = self.notebook.tabs()
        if len(tabs) < 2:
            return
        
        current = self.notebook.index(self.notebook.select())
        next_tab = (current + 1) % len(tabs)
        self.notebook.select(next_tab)
    
    def _prev_tab(self):
        """Switch to previous tab."""
        tabs = self.notebook.tabs()
        if len(tabs) < 2:
            return
        
        current = self.notebook.index(self.notebook.select())
        prev_tab = (current - 1) % len(tabs)
        self.notebook.select(prev_tab)
    
    def _add_recent_file(self, filepath: str):
        """Add file to recent files list."""
        if filepath in self.recent_files:
            self.recent_files.remove(filepath)
        self.recent_files.insert(0, filepath)
        self.recent_files = self.recent_files[:10]  # Keep last 10
        self._update_recent_menu()
    
    def _update_recent_menu(self):
        """Update recent files menu."""
        self.recent_menu.delete(0, tk.END)
        
        if not self.recent_files:
            self.recent_menu.add_command(label="No recent files", state=tk.DISABLED)
            return
        
        for filepath in self.recent_files:
            display = filepath
            if len(display) > 50:
                display = "..." + display[-47:]
            self.recent_menu.add_command(
                label=display,
                command=lambda p=filepath: self._open_file(p)
            )
        
        self.recent_menu.add_separator()
        self.recent_menu.add_command(label="Clear History", command=self._clear_recent)
    
    def _clear_recent(self):
        """Clear recent files list."""
        self.recent_files.clear()
        self._update_recent_menu()
    
    def _on_external_change(self, filepath: str):
        """Handle external file change."""
        if filepath in self.open_files:
            response = messagebox.askyesno(
                "File Changed",
                f"{Path(filepath).name} was modified externally. Reload?"
            )
            if response:
                editor = self.open_files[filepath]
                with open(filepath, 'r', encoding='utf-8') as f:
                    editor.load_data(f.read())
    
    def _update_modified_indicator(self):
        """Update modified indicator in status bar."""
        editor = self.open_files.get(self.current_file)
        if editor and editor.has_changes():
            self.status_modified.config(text="● Modified")
        else:
            self.status_modified.config(text="")
    
    def _show_about(self):
        """Show about dialog."""
        messagebox.showinfo(
            f"About {APP_NAME}",
            f"{APP_NAME} v{VERSION}\n\n"
            "A GUI editor for X11 configuration files.\n\n"
            "Supports:\n"
            "• .Xresources / .Xdefaults\n"
            "• OpenBox menu.xml and rc.xml\n"
            "• Generic key-value configs\n\n"
            "MIT License\n\n"
            "https://github.com/yourusername/kosxer"
        )
    
    def _on_close(self):
        """Handle application close."""
        # Check for unsaved changes
        unsaved = []
        for filepath, editor in self.open_files.items():
            if editor.has_changes():
                unsaved.append(filepath)
        
        if unsaved:
            files = "\n".join([f"  • {Path(f).name}" for f in unsaved])
            response = messagebox.askyesnocancel(
                "Unsaved Changes",
                f"The following files have unsaved changes:\n{files}\n\n"
                "Save all before closing?"
            )
            
            if response is True:
                for filepath in unsaved:
                    self.current_file = filepath
                    self._file_save()
            elif response is False:
                pass  # Don't save
            else:
                return  # Cancel
        
        # Stop file watching
        self.file_browser.stop_watching()
        
        self.root.destroy()
    
    def run(self):
        """Start the application."""
        self.root.mainloop()


def main():
    """Entry point."""
    app = KosXERApp()
    app.run()


if __name__ == "__main__":
    main()
