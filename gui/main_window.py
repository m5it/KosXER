#!/usr/bin/env python3
"""
Main Window for KosXER

Primary application window with menu bar, status bar,
and main content area for editors.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
from pathlib import Path

from config.constants import APP_NAME, VERSION
from config.settings import Settings


class MainWindow:
    """Main application window."""
    
    def __init__(self, root=None):
        if root is None:
            self.root = tk.Tk()
        else:
            self.root = root
            
        self.root.title(f"{APP_NAME} v{VERSION}")
        self.root.geometry("1200x800")
        self.root.minsize(800, 600)
        
        self.settings = Settings()
        self.current_file = None
        self.modified = False
        
        self._create_menu()
        self._create_toolbar()
        self._create_main_content()
        self._create_statusbar()
        
        # Center window
        self._center_window()
        
        # Bind events
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.root.bind("<Control-o>", lambda e: self.file_open())
        self.root.bind("<Control-s>", lambda e: self.file_save())
        self.root.bind("<Control-q>", lambda e: self.on_close())
    
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
        file_menu.add_command(label="New", command=self.file_new, accelerator="Ctrl+N")
        file_menu.add_command(label="Open...", command=self.file_open, accelerator="Ctrl+O")
        file_menu.add_command(label="Save", command=self.file_save, accelerator="Ctrl+S")
        file_menu.add_command(label="Save As...", command=self.file_save_as)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.on_close, accelerator="Alt+F4")
        
        # Edit menu
        edit_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Edit", menu=edit_menu)
        edit_menu.add_command(label="Undo", command=self.edit_undo, accelerator="Ctrl+Z")
        edit_menu.add_command(label="Redo", command=self.edit_redo, accelerator="Ctrl+Y")
        edit_menu.add_separator()
        edit_menu.add_command(label="Cut", command=self.edit_cut, accelerator="Ctrl+X")
        edit_menu.add_command(label="Copy", command=self.edit_copy, accelerator="Ctrl+C")
        edit_menu.add_command(label="Paste", command=self.edit_paste, accelerator="Ctrl+V")
        
        # View menu
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="View", menu=view_menu)
        view_menu.add_command(label="Toggle File Browser", command=self.toggle_file_browser)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self.show_about)
    
    def _create_toolbar(self):
        """Create toolbar."""
        toolbar = ttk.Frame(self.root, relief=tk.RAISED, borderwidth=1)
        toolbar.pack(side=tk.TOP, fill=tk.X)
        
        # New button
        new_btn = ttk.Button(toolbar, text="New", command=self.file_new, width=8)
        new_btn.pack(side=tk.LEFT, padx=2, pady=2)
        
        # Open button
        open_btn = ttk.Button(toolbar, text="Open", command=self.file_open, width=8)
        open_btn.pack(side=tk.LEFT, padx=2, pady=2)
        
        # Save button
        save_btn = ttk.Button(toolbar, text="Save", command=self.file_save, width=8)
        save_btn.pack(side=tk.LEFT, padx=2, pady=2)
        
        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=2)
        
        # About button
        about_btn = ttk.Button(toolbar, text="About", command=self.show_about, width=8)
        about_btn.pack(side=tk.RIGHT, padx=2, pady=2)
    
    def _create_main_content(self):
        """Create main content area with paned windows."""
        # Main paned window
        self.main_paned = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        self.main_paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Left panel - File browser (placeholder)
        self.left_frame = ttk.Frame(self.main_paned, width=250)
        self.main_paned.add(self.left_frame, weight=0)
        
        ttk.Label(self.left_frame, text="File Browser", font=('Helvetica', 10, 'bold')).pack(pady=5)
        ttk.Label(self.left_frame, text="(Not yet implemented)").pack(pady=20)
        
        # Right panel - Editor area
        self.right_frame = ttk.Frame(self.main_paned)
        self.main_paned.add(self.right_frame, weight=1)
        
        # Welcome message
        self.welcome_frame = ttk.Frame(self.right_frame)
        self.welcome_frame.pack(fill=tk.BOTH, expand=True)
        
        welcome_text = f"""
Welcome to {APP_NAME} v{VERSION}

A GUI editor for X11 configuration files.

Supported formats:
  • .Xresources / .Xdefaults
  • OpenBox menu.xml and rc.xml
  • Generic key-value configs

Keyboard shortcuts:
  Ctrl+O  Open file
  Ctrl+S  Save
  Ctrl+Q  Quit

Click File > Open to get started.
        """
        
        ttk.Label(
            self.welcome_frame, 
            text=welcome_text,
            justify=tk.LEFT,
            font=('Courier', 11)
        ).pack(expand=True)
    
    def _create_statusbar(self):
        """Create status bar."""
        self.statusbar = ttk.Label(
            self.root, 
            text="Ready", 
            relief=tk.SUNKEN, 
            anchor=tk.W
        )
        self.statusbar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def set_status(self, message: str):
        """Update status bar message."""
        self.statusbar.config(text=message)
        self.root.update_idletasks()
    
    def file_new(self):
        """Create new file."""
        self.current_file = None
        self.modified = False
        self.set_status("New file created")
    
    def file_open(self):
        """Open file dialog."""
        filetypes = [
            ("X Resources", "*.Xresources *.Xdefaults"),
            ("OpenBox Menu", "menu.xml"),
            ("OpenBox Config", "rc.xml"),
            ("All Config Files", "*.conf *.rc *.cfg"),
            ("All Files", "*.*")
        ]
        
        filepath = filedialog.askopenfilename(
            title="Open Configuration File",
            filetypes=filetypes
        )
        
        if filepath:
            self.current_file = filepath
            self.set_status(f"Opened: {filepath}")
    
    def file_save(self):
        """Save current file."""
        if self.current_file:
            self.set_status(f"Saved: {self.current_file}")
            self.modified = False
        else:
            self.file_save_as()
    
    def file_save_as(self):
        """Save as dialog."""
        filepath = filedialog.asksaveasfilename(
            title="Save Configuration File",
            defaultextension=".Xresources"
        )
        if filepath:
            self.current_file = filepath
            self.set_status(f"Saved: {filepath}")
            self.modified = False
    
    def edit_undo(self):
        """Undo last action."""
        self.set_status("Undo (not implemented)")
    
    def edit_redo(self):
        """Redo last action."""
        self.set_status("Redo (not implemented)")
    
    def edit_cut(self):
        """Cut selection."""
        self.set_status("Cut (not implemented)")
    
    def edit_copy(self):
        """Copy selection."""
        self.set_status("Copy (not implemented)")
    
    def edit_paste(self):
        """Paste from clipboard."""
        self.set_status("Paste (not implemented)")
    
    def toggle_file_browser(self):
        """Toggle file browser visibility."""
        self.set_status("Toggle file browser (not implemented)")
    
    def show_about(self):
        """Show about dialog."""
        messagebox.showinfo(
            f"About {APP_NAME}",
            f"{APP_NAME} v{VERSION}\n\n"
            "A GUI editor for X11 configuration files.\n\n"
            "Supports:\n"
            "• .Xresources / .Xdefaults\n"
            "• OpenBox menu.xml and rc.xml\n"
            "• Generic key-value configs\n\n"
            "MIT License"
        )
    
    def on_close(self):
        """Handle window close."""
        if self.modified:
            response = messagebox.askyesnocancel(
                "Unsaved Changes",
                "You have unsaved changes. Save before closing?"
            )
            if response is True:
                self.file_save()
                if self.modified:
                    return
            elif response is False:
                pass
            else:
                return
        
        self.root.destroy()
    
    def run(self):
        """Start the main loop."""
        self.root.mainloop()


def main():
    """Entry point."""
    app = MainWindow()
    app.run()


if __name__ == "__main__":
    main()
