#!/usr/bin/env python3
"""
KosXER - X11 Configuration Editor
A GUI editor for .Xresources, OpenBox menu.xml, and other Unix desktop configs.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import sys

# Add src to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gui.main_window import MainWindow


def main():
    """Application entry point."""
    root = tk.Tk()
    root.title("KosXER - X11 Configuration Editor")
    root.geometry("1200x800")
    root.minsize(800, 600)
    
    # Set application icon if available
    # root.iconphoto(True, tk.PhotoImage(file="assets/icon.png"))
    
    # Create main application window
    app = MainWindow(root)
    
    # Start main loop
    root.mainloop()


if __name__ == "__main__":
    main()
