#!/usr/bin/env python3
"""
KosXER - X11 Configuration Editor

A GUI editor for .Xresources, OpenBox menu.xml, KosDWM, and other Unix desktop configs.
"""

import os
import sys
import shutil
import argparse
import logging
from pathlib import Path
from typing import Optional, Dict, Any

import tkinter as tk
from tkinter import ttk, messagebox, filedialog

# Import version from AUTOVERSION (single source of truth)
from AUTOVERSION import VERSION
from config.constants import APP_NAME
from config.settings import Settings
from utils.logging_config import setup_logging, log_operation, log_error, log_file_operation

# Setup logging before other imports
logger = setup_logging(level=logging.INFO)
from parsers import (
    detect_parser, get_file_type_info,
    XResourcesParser, OpenBoxMenuParser, GenericKVParser,
    KosDWMConfigParser, KosDWMMenuParser
)

from gui.file_browser import FileBrowser
from gui.xresources_editor import XResourcesEditor
from gui.openbox_editor import OpenBoxEditor
from gui.kv_editor import KVEditor
from gui.kosdwm_config_editor import KosDWMConfigEditor
from gui.kosdwm_menu_editor import KosDWMMenuEditor


class KosXERApp:
    """Main application class for KosXER."""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title(f"{APP_NAME} v{VERSION}")
        self.root.geometry("1400x900")
        self.root.minsize(1000, 700)
        
        self.settings = Settings()
        
        # Track open files
        self.open_files: Dict[str, Any] = {}
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
        file_menu.add_command(label="New", command=self._file_new, accelerator="Ctrl+N")
        file_menu.add_command(label="Open...", command=self._file_open, accelerator="Ctrl+O")
        file_menu.add_command(label="Save", command=self._file_save, accelerator="Ctrl+S")
        file_menu.add_command(label="Save As...", command=self._file_save_as)
        file_menu.add_separator()
        
        # Recent files
        self.recent_menu = tk.Menu(file_menu, tearoff=0)
        file_menu.add_cascade(label="Recent Files", menu=self.recent_menu)
        self._update_recent_menu()
        
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self._on_close, accelerator="Ctrl+Q")
        
        # Edit menu
        edit_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Edit", menu=edit_menu)
        edit_menu.add_command(label="Undo", command=self._edit_undo, accelerator="Ctrl+Z")
        edit_menu.add_command(label="Redo", command=self._edit_redo, accelerator="Ctrl+Y")
        edit_menu.add_separator()
        edit_menu.add_command(label="Cut", command=self._edit_cut, accelerator="Ctrl+X")
        edit_menu.add_command(label="Copy", command=self._edit_copy, accelerator="Ctrl+C")
        edit_menu.add_command(label="Paste", command=self._edit_paste, accelerator="Ctrl+V")
        
        # View menu
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="View", menu=view_menu)
        view_menu.add_command(label="Toggle File Browser", command=self._toggle_file_browser, accelerator="Ctrl+B")
        view_menu.add_separator()
        self.show_hidden_var = tk.BooleanVar(value=False)
        view_menu.add_checkbutton(label="Show Hidden Files", variable=self.show_hidden_var, 
                                  command=self._toggle_hidden_files, accelerator="Ctrl+H")
        view_menu.add_separator()
        view_menu.add_command(label="Refresh", command=self._refresh_browser, accelerator="F5")
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self._show_about)
    
    def _create_toolbar(self):
        """Create toolbar."""
        toolbar = ttk.Frame(self.root, relief=tk.RAISED, borderwidth=1)
        toolbar.pack(side=tk.TOP, fill=tk.X)
        
        ttk.Button(toolbar, text="New", command=self._file_new, width=8).pack(side=tk.LEFT, padx=2, pady=2)
        ttk.Button(toolbar, text="Open", command=self._file_open, width=8).pack(side=tk.LEFT, padx=2, pady=2)
        ttk.Button(toolbar, text="Save", command=self._file_save, width=8).pack(side=tk.LEFT, padx=2, pady=2)
        
        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=2)
        
        self.fb_btn = ttk.Button(toolbar, text="Hide Browser", command=self._toggle_file_browser, width=12)
        self.fb_btn.pack(side=tk.LEFT, padx=2, pady=2)
        
        ttk.Frame(toolbar).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(toolbar, text="About", command=self._show_about, width=8).pack(side=tk.RIGHT, padx=2, pady=2)
    
    def _create_main_layout(self):
        """Create main layout."""
        self.main_paned = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        self.main_paned.pack(fill=tk.BOTH, expand=True)
        
        # Left: File browser
        self.browser_frame = ttk.Frame(self.main_paned, width=250)
        self.main_paned.add(self.browser_frame, weight=0)
        
        self.file_browser = FileBrowser(self.browser_frame, on_file_select=self._open_file)
        self.file_browser.pack(fill=tk.BOTH, expand=True)
        
        # Right: Editor area
        self.editor_frame = ttk.Frame(self.main_paned)
        self.main_paned.add(self.editor_frame, weight=1)
        
        # Notebook for tabs
        self.notebook = ttk.Notebook(self.editor_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Welcome tab
        self.welcome_frame = ttk.Frame(self.notebook)
        self._create_welcome_content(self.welcome_frame)
        self.notebook.add(self.welcome_frame, text="Welcome")
    
    def _create_welcome_content(self, parent):
        """Create welcome content."""
        text = tk.Text(parent, wrap=tk.WORD, padx=20, pady=20, font=('Courier', 11))
        text.pack(fill=tk.BOTH, expand=True)
        text.insert('1.0', f"""Welcome to {APP_NAME} v{VERSION}

A GUI editor for X11 configuration files.

Supported Formats:
  • .Xresources / .Xdefaults  - X11 resources
  • menu.xml / rc.xml          - OpenBox
  • KosDWM config & menus     - Dynamic window manager
  • .conf / .env / .rc        - Key-value configs
  • .bashrc / .zshrc          - Shell configs

Keyboard Shortcuts:
  Ctrl+O  Open file
  Ctrl+S  Save
  Ctrl+Q  Quit
  Ctrl+B  Toggle file browser
  Ctrl+H  Toggle hidden files
  F5      Refresh
""")
        text.config(state=tk.DISABLED)
    
    def _create_statusbar(self):
        """Create status bar."""
        self.statusbar = ttk.Frame(self.root, relief=tk.SUNKEN, borderwidth=1)
        self.statusbar.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.status_file = ttk.Label(self.statusbar, text="No file open", anchor=tk.W, width=40)
        self.status_file.pack(side=tk.LEFT, padx=5)
    def _open_file(self, filepath: str):
        """Open a file."""
        filepath = str(filepath)
        logger.info(f"Opening file: {filepath}")
        
        # Check if already open
        if filepath in self.open_files:
            logger.debug(f"File already open: {filepath}")
            for i, tab in enumerate(self.notebook.tabs()):
                if self.notebook.tab(tab, "text") == Path(filepath).name:
                    self.notebook.select(i)
                    return
        
        try:
            # Detect file type
            parser_class = detect_parser(filepath)
            if not parser_class:
                logger.warning(f"Cannot determine file type: {filepath}")
                messagebox.showerror("Error", f"Cannot determine file type: {filepath}")
                return
            
            logger.info(f"Detected parser: {parser_class.__name__} for {filepath}")
            
            # Create appropriate editor
            if parser_class == XResourcesParser:
                editor = XResourcesEditor(self.notebook, self, filepath)
            elif parser_class == OpenBoxMenuParser:
                editor = OpenBoxEditor(self.notebook, self, filepath)
            elif parser_class == GenericKVParser:
                editor = KVEditor(self.notebook, self, filepath)
            elif parser_class == KosDWMConfigParser:
                editor = KosDWMConfigEditor(self.notebook, self, filepath)
            elif parser_class == KosDWMMenuParser:
                editor = KosDWMMenuEditor(self.notebook, self, filepath)
            else:
                logger.error(f"No editor for parser: {parser_class.__name__}")
                messagebox.showerror("Error", f"No editor for: {filepath}")
                return
            
            # Load file
            self.set_status(f"Saved: {Path(self.current_file).name}")
            
            log_file_operation(logger, "SAVE", self.current_file, True)
            
        except Exception as e:
            log_error(logger, "_file_save", e, f"filepath={self.current_file}")
            messagebox.showerror("Save Error", f"Failed to save file:\n{str(e)}")
            self.set_status(f"Save failed: {str(e)[:50]}")
    
    def set_status(self, message: str):
            self._file_save_as()
            return
        
        editor = self.open_files.get(self.current_file)
        if not editor:
            logger.error(f"No editor found for: {self.current_file}")
            messagebox.showerror("Save Error", "No editor found for current file")
            return
        
        try:
            # Get content from editor
            content = editor.get_data()
            if content is None:
                logger.error("Editor returned None for get_data()")
                messagebox.showerror("Save Error", "Editor returned no data")
                return
            
            logger.debug(f"Got {len(content)} bytes from editor")
            
            # Create backup if file exists
            if os.path.exists(self.current_file):
                backup_path = self.current_file + '.bak'
                try:
                    shutil.copy2(self.current_file, backup_path)
                    logger.debug(f"Created backup: {backup_path}")
                except Exception as e:
                    logger.warning(f"Could not create backup: {e}")
            
            # Write file
            with open(self.current_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # Verify write
            if not os.path.exists(self.current_file):
                raise IOError("File was not created after write")
            
            file_size = os.path.getsize(self.current_file)
            logger.info(f"Saved {file_size} bytes to: {self.current_file}")
            
            # Update editor state
            editor.mark_dirty(False)
            editor.set_filepath(self.current_file)
            
            # Update UI
            self.status_modified.config(text="✓ Saved")
            self.root.after(2000, lambda: self.status_modified.config(text=""))
            self.set_status(f"Saved: {Path(self.current_file).name}")
            
            log_file_operation(logger, "SAVE", self.current_file, True)
            
        except Exception as e:
            log_error(logger, "_file_save", e, f"filepath={self.current_file}")
            messagebox.showerror("Save Error", f"Failed to save file:\n{str(e)}")
            self.set_status(f"Save failed: {str(e)[:50]}")
        # Check if already open
        if filepath in self.open_files:
            for i, tab in enumerate(self.notebook.tabs()):
                if self.notebook.tab(tab, "text") == Path(filepath).name:
                    self.notebook.select(i)
                    return
        
        try:
            # Detect file type
            parser_class = detect_parser(filepath)
            if not parser_class:
                messagebox.showerror("Error", f"Cannot determine file type: {filepath}")
                return
            
            # Create appropriate editor
            if parser_class == XResourcesParser:
                editor = XResourcesEditor(self.notebook, self, filepath)
            elif parser_class == OpenBoxMenuParser:
                editor = OpenBoxEditor(self.notebook, self, filepath)
            elif parser_class == GenericKVParser:
                editor = KVEditor(self.notebook, self, filepath)
            elif parser_class == KosDWMConfigParser:
                editor = KosDWMConfigEditor(self.notebook, self, filepath)
            elif parser_class == KosDWMMenuParser:
                editor = KosDWMMenuEditor(self.notebook, self, filepath)
            else:
                messagebox.showerror("Error", f"No editor for: {filepath}")
                return
            
            # Load file
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            editor.load_data(content)
            
            # Add tab
            tab_text = Path(filepath).name
            if len(tab_text) > 20:
                tab_text = tab_text[:17] + "..."
            
            self.notebook.add(editor, text=tab_text)
            self.notebook.select(editor)
            
            self.open_files[filepath] = editor
            self.current_file = filepath
            self._add_recent_file(filepath)
            
            desc, _, _ = get_file_type_info(filepath)
            self._update_status(filepath, desc)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open:\n{str(e)}")
    
    def _update_status(self, filepath: str, parser_desc: str):
        """Update status bar."""
        self.status_file.config(text=f"📄 {Path(filepath).name}")
        self.status_parser.config(text=f"🔧 {parser_desc}")
        self.root.title(f"{Path(filepath).name} - {APP_NAME} v{VERSION}")
    
    def _file_new(self):
        """Create new file."""
        messagebox.showinfo("New", "Select file type from File > Open")
    
    def _file_open(self):
        """Open file dialog."""
        filetypes = [
            ("All Configs", "*.Xresources *.Xdefaults *.xml *.conf *.json"),
            ("X Resources", "*.Xresources *.Xdefaults"),
            ("OpenBox", "menu.xml rc.xml"),
            ("KosDWM", "config.json"),
            ("All", "*.*")
        ]
        
        filepath = filedialog.askopenfilename(title="Open File", filetypes=filetypes)
        if filepath:
            self._open_file(filepath)
    
    def _file_save(self):
        """Save current file with backup."""
        if not self.current_file:
            self._file_save_as()
            return
        
        editor = self.open_files.get(self.current_file)
        if not editor:
            messagebox.showerror("Save Error", "No editor found for current file")
            return
        
        try:
            # Get content from editor
            content = editor.get_data()
            if content is None:
                messagebox.showerror("Save Error", "Editor returned no data")
                return
            
            # Create backup if file exists
            if os.path.exists(self.current_file):
                backup_path = self.current_file + '.bak'
                try:
                    shutil.copy2(self.current_file, backup_path)
                except Exception as e:
                    print(f"Warning: Could not create backup: {e}")
            
            # Write file
            with open(self.current_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # Verify write
            if not os.path.exists(self.current_file):
                raise IOError("File was not created")
            
            # Update editor state
            editor.mark_dirty(False)
            editor.set_filepath(self.current_file)
            
            # Update UI
            self.status_modified.config(text="✓ Saved")
            self.root.after(2000, lambda: self.status_modified.config(text=""))
            self.set_status(f"Saved: {Path(self.current_file).name}")
            
        except Exception as e:
            messagebox.showerror("Save Error", f"Failed to save file:\n{str(e)}")
            self.set_status(f"Save failed: {str(e)[:50]}")
    
    def set_status(self, message: str):
        """Set status bar message."""
        if hasattr(self, 'status_file'):
            self.status_file.config(text=f"📄 {message}")
        self.root.update_idletasks()
    
    def _file_save_as(self):
        """Save as dialog."""
        if not self.current_file:
            return
        
        filepath = filedialog.asksaveasfilename(
            title="Save As",
            defaultextension=".Xresources",
            initialfile=Path(self.current_file).name
        )
        
        if filepath:
            self.current_file = filepath
            self._file_save()
    
    def _close_current_tab(self):
        """Close current tab."""
        current = self.notebook.select()
        if current:
            self.notebook.forget(current)
    
    def _edit_undo(self):
        """Undo."""
        editor = self.open_files.get(self.current_file)
        if editor and hasattr(editor, 'undo'):
            editor.undo()
    
    def _edit_redo(self):
        """Redo."""
        editor = self.open_files.get(self.current_file)
        if editor and hasattr(editor, 'redo'):
            editor.redo()
    
    def _edit_cut(self):
        """Cut."""
        self.root.focus_get().event_generate("<<Cut>>")
    
    def _edit_copy(self):
        """Copy."""
        self.root.focus_get().event_generate("<<Copy>>")
    
    def _edit_paste(self):
        """Paste."""
        self.root.focus_get().event_generate("<<Paste>>")
    
    def _toggle_file_browser(self):
        """Toggle file browser."""
        if self.browser_frame.winfo_viewable():
            self.browser_frame.pack_forget()
            self.fb_btn.config(text="Show Browser")
        else:
            self.browser_frame.pack(side=tk.LEFT, fill=tk.Y)
            self.fb_btn.config(text="Hide Browser")
    
    def _add_recent_file(self, filepath: str):
        """Add to recent files."""
        if filepath in self.recent_files:
            self.recent_files.remove(filepath)
        self.recent_files.insert(0, filepath)
        self.recent_files = self.recent_files[:10]
        self._update_recent_menu()
    
    def _update_recent_menu(self):
        """Update recent menu."""
        self.recent_menu.delete(0, tk.END)
        
        if not self.recent_files:
            self.recent_menu.add_command(label="No recent files", state=tk.DISABLED)
            return
        
        for filepath in self.recent_files:
            display = filepath if len(filepath) < 50 else "..." + filepath[-47:]
            self.recent_menu.add_command(label=display, command=lambda p=filepath: self._open_file(p))
        
        self.recent_menu.add_separator()
        self.recent_menu.add_command(label="Clear", command=self._clear_recent)
    
    def _clear_recent(self):
        """Clear recent files."""
        self.recent_files.clear()
        self._update_recent_menu()
    
    def _show_about(self):
        """Show about dialog."""
        messagebox.showinfo(
            f"About {APP_NAME}",
            f"{APP_NAME} v{VERSION}\n\n"
            "GUI editor for X11 configs:\n"
            "• XResources\n"
            "• OpenBox\n"
            "• KosDWM\n"
            "• Key-value files\n\n"
            "MIT License"
        )
    
    def _on_close(self):
        """Handle close."""
        # Check for unsaved changes
        unsaved = []
        for filepath, editor in self.open_files.items():
            if hasattr(editor, 'has_changes') and editor.has_changes():
                unsaved.append(filepath)
        
        if unsaved:
            files = "\n".join([f"  • {Path(f).name}" for f in unsaved])
            response = messagebox.askyesnocancel(
                "Unsaved Changes",
                f"Unsaved changes in:\n{files}\n\nSave before closing?"
            )
            
            if response is True:
                for filepath in unsaved:
                    self.current_file = filepath
                    self._file_save()
            elif response is False:
                pass
            else:
                return
        
        self.root.destroy()
    
    def run(self):
        """Start application."""
        self.root.mainloop()


def main():
    """Entry point."""
    app = KosXERApp()
    app.run()


if __name__ == "__main__":
    main()
