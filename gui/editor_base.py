#!/usr/bin/env python3
"""
Base Editor Widget for KosXER

Abstract base class for all editor widgets. Provides common functionality
including toolbar, status area, change tracking, and file operations.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from abc import ABC, abstractmethod
from typing import Optional, Callable, Any, Dict


class EditorWidget(ABC, ttk.Frame):
    """
    Abstract base class for all editor widgets.
    
    Subclasses must implement:
    - _create_editor_widgets(): Create the specific editor UI
    - load_data(data): Load data into the editor
    - get_data(): Get data from the editor
    - validate(): Validate the current data
    
    Features:
    - Common toolbar with Save, Reload, Validate buttons
    - Status area for messages
    - Change tracking (dirty flag)
    - Integration with main window for file operations
    """
    
    def __init__(self, parent, main_window=None, filepath: Optional[str] = None, 
                 *args, **kwargs):
        """
        Initialize the editor widget.
        
        Args:
            parent: Parent widget
            main_window: Reference to main window for callbacks
            filepath: Path to the file being edited
        """
        super().__init__(parent, *args, **kwargs)
        
        self.main_window = main_window
        self.filepath = filepath
        self._dirty = False
        self._data: Any = None
        self._original_data: Any = None
        
        # Callbacks
        self._on_save_callback: Optional[Callable] = None
        self._on_change_callback: Optional[Callable] = None
        
        # Create UI
        self._create_toolbar()
        self._create_editor_area()
        self._create_statusbar()
        
        # Layout
        self.toolbar.pack(fill=tk.X, padx=5, pady=2)
        self.editor_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.statusbar.pack(fill=tk.X, padx=5, pady=2)
    
    def _create_toolbar(self):
        """Create the common toolbar."""
        self.toolbar = ttk.Frame(self)
        
        # Save button
        self.save_btn = ttk.Button(
            self.toolbar, 
            text="💾 Save", 
            command=self._on_save,
            state=tk.DISABLED
        )
        self.save_btn.pack(side=tk.LEFT, padx=2)
        
        # Reload button
        self.reload_btn = ttk.Button(
            self.toolbar,
            text="🔄 Reload",
            command=self._on_reload
        )
        self.reload_btn.pack(side=tk.LEFT, padx=2)
        
        # Validate button
        self.validate_btn = ttk.Button(
            self.toolbar,
            text="✓ Validate",
            command=self._on_validate
        )
        self.validate_btn.pack(side=tk.LEFT, padx=2)
        
        ttk.Separator(self.toolbar, orient=tk.VERTICAL).pack(
            side=tk.LEFT, fill=tk.Y, padx=10
        )
        
        # File info label
        self.file_label = ttk.Label(self.toolbar, text="No file")
        self.file_label.pack(side=tk.LEFT, padx=5)
        
        # Dirty indicator
        self.dirty_indicator = ttk.Label(
            self.toolbar, 
            text="",
            foreground="red",
            font=('Helvetica', 10, 'bold')
        )
        self.dirty_indicator.pack(side=tk.RIGHT, padx=5)
    
    def _create_editor_area(self):
        """Create the main editor area. Subclasses implement actual editor."""
        self.editor_frame = ttk.Frame(self, relief=tk.SUNKEN, borderwidth=1)
        
        # This will be filled by subclass _create_editor_widgets()
        self._create_editor_widgets()
    
    def _create_statusbar(self):
        """Create the status bar."""
        self.statusbar = ttk.Frame(self, relief=tk.SUNKEN, borderwidth=1)
        
        self.status_label = ttk.Label(
            self.statusbar,
            text="Ready",
            anchor=tk.W
        )
        self.status_label.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        self.position_label = ttk.Label(
            self.statusbar,
            text="",
            anchor=tk.E
        )
        self.position_label.pack(side=tk.RIGHT, padx=5)
    
    @abstractmethod
    def _create_editor_widgets(self):
        """
        Create editor-specific widgets.
        
        Must be implemented by subclasses to create their specific UI
        within self.editor_frame.
        """
        pass
    
    # Required abstract methods
    
    @abstractmethod
    def load_data(self, data: Any):
        """
        Load data into the editor.
        
        Args:
            data: Data to load (format depends on parser)
        """
        pass
    
    @abstractmethod
    def get_data(self) -> Any:
        """
        Get current data from the editor.
        
        Returns:
            Current editor data
        """
        pass
    
    @abstractmethod
    def validate(self) -> tuple[bool, str]:
        """
        Validate the current data.
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        pass
    
    # Common methods
    
    def has_changes(self) -> bool:
        """Check if editor has unsaved changes."""
        return self._dirty
    
    def mark_dirty(self, dirty: bool = True):
        """
        Mark the editor as dirty (has changes).
        
        Args:
            dirty: True if has changes, False if clean
        """
        self._dirty = dirty
        
        # Update UI
        if dirty:
            self.dirty_indicator.config(text="● Modified")
            self.save_btn.config(state=tk.NORMAL)
        else:
            self.dirty_indicator.config(text="")
            self.save_btn.config(state=tk.DISABLED)
        
        # Notify callback
        if self._on_change_callback:
            self._on_change_callback(dirty)
    
    def set_filepath(self, filepath: str):
        """
        Set the file path being edited.
        
        Args:
            filepath: Path to file
        """
        self.filepath = filepath
        display_path = filepath if len(filepath) < 50 else "..." + filepath[-47:]
        self.file_label.config(text=display_path)
    
    def set_status(self, message: str, message_type: str = "info"):
        """
        Set status bar message.
        
        Args:
            message: Message to display
            message_type: 'info', 'warning', or 'error'
        """
        colors = {
            "info": "black",
            "warning": "orange",
            "error": "red"
        }
        self.status_label.config(
            text=message,
            foreground=colors.get(message_type, "black")
        )
    
    def set_position(self, position: str):
        """
        Set position indicator (e.g., line/column).
        
        Args:
            position: Position string to display
        """
        self.position_label.config(text=position)
    
    def set_on_save_callback(self, callback: Callable):
        """
        Set callback for save operation.
        
        Args:
            callback: Function to call on save
        """
        self._on_save_callback = callback
    
    def set_on_change_callback(self, callback: Callable[[bool], None]):
        """
        Set callback for change events.
        
        Args:
            callback: Function(bool) called when dirty state changes
        """
        self._on_change_callback = callback
    
    def _on_save(self):
        """Handle save button click."""
        # Validate first
        is_valid, error = self.validate()
        if not is_valid:
            messagebox.showerror("Validation Error", error)
            self.set_status(f"Validation failed: {error}", "error")
            return
        
        # Get current data
        data = self.get_data()
        
        # Call save callback if set
        if self._on_save_callback:
            try:
                self._on_save_callback(data)
                self._original_data = data
                self.mark_dirty(False)
                self.set_status("Saved successfully", "info")
            except Exception as e:
                messagebox.showerror("Save Error", str(e))
                self.set_status(f"Save failed: {str(e)}", "error")
        elif self.main_window:
            # Use main window's save method
            self.main_window.file_save()
    
    def _on_reload(self):
        """Handle reload button click."""
        if self.has_changes():
            response = messagebox.askyesnocancel(
                "Unsaved Changes",
                "You have unsaved changes. Save before reloading?"
            )
            if response is True:
                self._on_save()
                if self.has_changes():  # Still dirty, save failed
                    return
            elif response is False:
                pass  # Discard changes
            else:  # Cancel
                return
        
        # Reload original data
        if self._original_data is not None:
            self.load_data(self._original_data)
            self.mark_dirty(False)
            self.set_status("Reloaded from disk", "info")
    
    def _on_validate(self):
        """Handle validate button click."""
        is_valid, error = self.validate()
        if is_valid:
            self.set_status("✓ Validation passed", "info")
            messagebox.showinfo("Validation", "Content is valid!")
        else:
            self.set_status(f"✗ Validation failed: {error}", "error")
            messagebox.showerror("Validation Error", error)
    
    def reset(self):
        """Reset editor to empty state."""
        self._dirty = False
        self._data = None
        self._original_data = None
        self.mark_dirty(False)
        self.set_status("Ready")
    
    def get_filepath(self) -> Optional[str]:
        """Get current file path."""
        return self.filepath
    
    def is_dirty(self) -> bool:
        """Alias for has_changes()."""
        return self._dirty


class TextEditorWidget(EditorWidget):
    """
    Example concrete implementation using a text widget.
    Can be used for simple text-based configs.
    """
    
    def _create_editor_widgets(self):
        """Create text editor widgets."""
        # Text widget with scrollbars
        text_frame = ttk.Frame(self.editor_frame)
        text_frame.pack(fill=tk.BOTH, expand=True)
        
        self.text_widget = tk.Text(
            text_frame,
            wrap=tk.NONE,
            undo=True,
            maxundo=50
        )
        
        # Scrollbars
        y_scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL)
        x_scrollbar = ttk.Scrollbar(self.editor_frame, orient=tk.HORIZONTAL)
        
        self.text_widget.config(yscrollcommand=y_scrollbar.set,
                               xscrollcommand=x_scrollbar.set)
        y_scrollbar.config(command=self.text_widget.yview)
        x_scrollbar.config(command=self.text_widget.xview)
        
        # Layout
        y_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        x_scrollbar.pack(fill=tk.X)
        
        # Bind change events
        self.text_widget.bind("<<Modified>>", self._on_text_modified)
        self.text_widget.bind("<KeyRelease>", self._on_cursor_move)
        self.text_widget.bind("<ButtonRelease>", self._on_cursor_move)
    
    def _on_text_modified(self, event=None):
        """Handle text modification."""
        if self.text_widget.edit_modified():
            self.mark_dirty(True)
            self.text_widget.edit_modified(False)
    
    def _on_cursor_move(self, event=None):
        """Update position indicator."""
        index = self.text_widget.index(tk.INSERT)
        line, col = index.split('.')
        self.set_position(f"Line {line}, Col {col}")
    
    def load_data(self, data: str):
        """Load text data."""
        self.text_widget.delete('1.0', tk.END)
        self.text_widget.insert('1.0', data)
        self._original_data = data
        self.mark_dirty(False)
    
    def get_data(self) -> str:
        """Get text data."""
        return self.text_widget.get('1.0', tk.END + '-1c')
    
    def validate(self) -> tuple[bool, str]:
        """Validate text content."""
        content = self.get_data()
        if not content.strip():
            return False, "Content is empty"
        return True, ""
