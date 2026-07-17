#!/usr/bin/env python3
"""
KosDWM Config Editor Widget for KosXER

Editor for KosDWM's config.json file with color pickers,
numeric inputs, and live preview.
"""

import tkinter as tk
from tkinter import ttk, colorchooser, messagebox
from typing import Optional

from gui.editor_base import EditorWidget
from parsers.kosdwm_config_parser import KosDWMConfigParser, KosDWMConfig


class KosDWMConfigEditor(EditorWidget):
    """
    Editor widget for KosDWM config.json.
    
    Features:
    - Color pickers for button backgrounds
    - Spinboxes for height values
    - Dropdown for layout mode
    - Live color preview
    - Real-time validation
    """
    
    VALID_LAYOUT_MODES = ["buttons", "comboboxes"]
    
    def __init__(self, parent, main_window=None, filepath: Optional[str] = None, **kwargs):
        self.parser = KosDWMConfigParser()
        self.config: Optional[KosDWMConfig] = None
        super().__init__(parent, main_window, filepath, **kwargs)
    
    def _create_editor_widgets(self):
        """Create the KosDWM config editor UI."""
        # Main frame with padding
        main_frame = ttk.Frame(self.editor_frame, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        ttk.Label(main_frame, text="KosDWM Configuration", 
                 font=('Helvetica', 14, 'bold')).pack(pady=(0, 20))
        
        # Create sections
        self._create_colors_section(main_frame)
        ttk.Separator(main_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=15)
        
        self._create_dimensions_section(main_frame)
        ttk.Separator(main_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=15)
        
        self._create_layout_section(main_frame)
        ttk.Separator(main_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=15)
        
        self._create_preview_section(main_frame)
        
        # Bind change events
        self._bind_changes()
    
    def _create_colors_section(self, parent):
        """Create color configuration section."""
        section = ttk.LabelFrame(parent, text="Colors", padding=10)
        section.pack(fill=tk.X, pady=5)
        
        # Active button color
        active_frame = ttk.Frame(section)
        active_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(active_frame, text="Active Button BG:", width=20).pack(side=tk.LEFT)
        self.active_color_var = tk.StringVar(value="#4a90d9")
        self.active_color_entry = ttk.Entry(active_frame, textvariable=self.active_color_var, width=10)
        self.active_color_entry.pack(side=tk.LEFT, padx=5)
        
        self.active_preview = tk.Label(active_frame, text="   ", bg="#4a90d9", relief=tk.RIDGE, bd=2)
        self.active_preview.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(active_frame, text="Pick...", command=lambda: self._pick_color('active')).pack(side=tk.LEFT, padx=5)
        
        # Inactive button color
        inactive_frame = ttk.Frame(section)
        inactive_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(inactive_frame, text="Inactive Button BG:", width=20).pack(side=tk.LEFT)
        self.inactive_color_var = tk.StringVar(value="#606060")
        self.inactive_color_entry = ttk.Entry(inactive_frame, textvariable=self.inactive_color_var, width=10)
        self.inactive_color_entry.pack(side=tk.LEFT, padx=5)
        
        self.inactive_preview = tk.Label(inactive_frame, text="   ", bg="#606060", relief=tk.RIDGE, bd=2)
        self.inactive_preview.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(inactive_frame, text="Pick...", command=lambda: self._pick_color('inactive')).pack(side=tk.LEFT, padx=5)
        
        # Bind color changes to preview updates
        self.active_color_var.trace('w', lambda *args: self._update_color_preview('active'))
        self.inactive_color_var.trace('w', lambda *args: self._update_color_preview('inactive'))
    
    def _create_dimensions_section(self, parent):
        """Create dimensions section."""
        section = ttk.LabelFrame(parent, text="Dimensions", padding=10)
        section.pack(fill=tk.X, pady=5)
        
        # Bar height
        bar_frame = ttk.Frame(section)
        bar_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(bar_frame, text="Bar Height:", width=20).pack(side=tk.LEFT)
        self.bar_height_var = tk.IntVar(value=50)
        ttk.Spinbox(bar_frame, from_=20, to=200, textvariable=self.bar_height_var, width=10).pack(side=tk.LEFT, padx=5)
        ttk.Label(bar_frame, text="pixels").pack(side=tk.LEFT)
        
        # Button height
        btn_frame = ttk.Frame(section)
        btn_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(btn_frame, text="Button Height:", width=20).pack(side=tk.LEFT)
        self.button_height_var = tk.IntVar(value=1)
        ttk.Spinbox(btn_frame, from_=1, to=10, textvariable=self.button_height_var, width=10).pack(side=tk.LEFT, padx=5)
        ttk.Label(btn_frame, text="(1-10)").pack(side=tk.LEFT)
        
        # Combobox padding
        combo_frame = ttk.Frame(section)
        combo_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(combo_frame, text="Combobox Padding:", width=20).pack(side=tk.LEFT)
        self.combobox_pad_var = tk.IntVar(value=1)
        ttk.Spinbox(combo_frame, from_=0, to=20, textvariable=self.combobox_pad_var, width=10).pack(side=tk.LEFT, padx=5)
        ttk.Label(combo_frame, text="pixels").pack(side=tk.LEFT)
    
    def _create_layout_section(self, parent):
        """Create layout mode section."""
        section = ttk.LabelFrame(parent, text="Layout Mode", padding=10)
        section.pack(fill=tk.X, pady=5)
        
        ttk.Label(section, text="Mode:").pack(side=tk.LEFT)
        self.layout_mode_var = tk.StringVar(value="buttons")
        
        mode_combo = ttk.Combobox(section, textvariable=self.layout_mode_var, 
                                  values=self.VALID_LAYOUT_MODES, 
                                  state="readonly", width=15)
        mode_combo.pack(side=tk.LEFT, padx=5)
        
        # Description label
        self.layout_desc_var = tk.StringVar()
        ttk.Label(section, textvariable=self.layout_desc_var, 
                 foreground="gray").pack(side=tk.LEFT, padx=10)
        
        self._update_layout_desc()
        self.layout_mode_var.trace('w', lambda *args: self._update_layout_desc())
    
    def _create_preview_section(self, parent):
        """Create preview section."""
        section = ttk.LabelFrame(parent, text="Preview", padding=10)
        section.pack(fill=tk.X, pady=5)
        
        # Preview frame simulating the bar
        self.preview_bar = tk.Frame(section, height=50, bg="#1a1a1a")
        self.preview_bar.pack(fill=tk.X, pady=10)
        self.preview_bar.pack_propagate(False)
        
        # Preview buttons
        self.preview_active_btn = tk.Label(self.preview_bar, text="Active", 
                                          bg="#4a90d9", fg="white",
                                          padx=10, pady=2)
        self.preview_active_btn.pack(side=tk.LEFT, padx=5, pady=5)
        
        self.preview_inactive_btn = tk.Label(self.preview_bar, text="Inactive", 
                                            bg="#606060", fg="white",
                                            padx=10, pady=2)
        self.preview_inactive_btn.pack(side=tk.LEFT, padx=5, pady=5)
        
        # Update preview when values change
        self.bar_height_var.trace('w', lambda *args: self._update_preview())
    
    def _pick_color(self, color_type: str):
        """Open color picker."""
        if color_type == 'active':
            current = self.active_color_var.get()
            var = self.active_color_var
        else:
            current = self.inactive_color_var.get()
            var = self.inactive_color_var
        
        # Ask for color
        color = colorchooser.askcolor(initialcolor=current, 
                                      title=f"Choose {color_type} button color")
        
        if color and color[1]:  # color is (rgb_tuple, hex_string)
            var.set(color[1])
            self.mark_dirty(True)
    
    def _update_color_preview(self, color_type: str):
        """Update color preview swatch."""
        try:
            if color_type == 'active':
                color = self.active_color_var.get()
                self.active_preview.config(bg=color)
                self.preview_active_btn.config(bg=color)
            else:
                color = self.inactive_color_var.get()
                self.inactive_preview.config(bg=color)
                self.preview_inactive_btn.config(bg=color)
        except tk.TclError:
            # Invalid color, ignore
            pass
    
    def _update_layout_desc(self):
        """Update layout mode description."""
        mode = self.layout_mode_var.get()
        if mode == "buttons":
            self.layout_desc_var.set("Buttons + all windows combobox")
        else:
            self.layout_desc_var.set("4 desktop window comboboxes")
    
    def _update_preview(self):
        """Update preview dimensions."""
        try:
            height = self.bar_height_var.get()
            self.preview_bar.config(height=height)
        except tk.TclError:
            pass
    
    def _bind_changes(self):
        """Bind all variables to mark dirty on change."""
        vars_to_watch = [
            self.active_color_var, self.inactive_color_var,
            self.bar_height_var, self.button_height_var,
            self.combobox_pad_var, self.layout_mode_var
        ]
        
        for var in vars_to_watch:
            var.trace('w', lambda *args: self.mark_dirty(True))
    
    def _validate_hex_color(self, color: str) -> bool:
        """Validate hex color format."""
        import re
        pattern = r'^#[0-9a-fA-F]{6}$'
        return bool(re.match(pattern, color))
    
    # Required abstract methods
    
    def load_data(self, data: str):
        """Load KosDWM config."""
        self.config = self.parser.parse(data)
        
        # Update UI
        self.active_color_var.set(self.config.active_button_bg)
        self.inactive_color_var.set(self.config.inactive_button_bg)
        self.bar_height_var.set(self.config.bar_height)
        self.button_height_var.set(self.config.button_height)
        self.combobox_pad_var.set(self.config.combobox_ipady)
        self.layout_mode_var.set(self.config.layout_mode)
        
        self._original_data = data
        self.mark_dirty(False)
        self.set_status(f"Loaded KosDWM config")
    
    def get_data(self) -> str:
        """Get KosDWM config as JSON."""
        # Update config from UI
        self.config.active_button_bg = self.active_color_var.get()
        self.config.inactive_button_bg = self.inactive_color_var.get()
        self.config.bar_height = self.bar_height_var.get()
        self.config.button_height = self.button_height_var.get()
        self.config.combobox_ipady = self.combobox_pad_var.get()
        self.config.layout_mode = self.layout_mode_var.get()
        
        return self.parser.write_back()
    
    def validate(self) -> tuple[bool, str]:
        """Validate KosDWM config."""
        # Validate colors
        if not self._validate_hex_color(self.active_color_var.get()):
            return False, f"Invalid active button color: {self.active_color_var.get()}"
        
        if not self._validate_hex_color(self.inactive_color_var.get()):
            return False, f"Invalid inactive button color: {self.inactive_color_var.get()}"
        
        # Validate layout mode
        if self.layout_mode_var.get() not in self.VALID_LAYOUT_MODES:
            return False, f"Invalid layout mode: {self.layout_mode_var.get()}"
        
        # Validate numeric values
        try:
            if self.bar_height_var.get() < 0:
                return False, "Bar height must be non-negative"
            if self.button_height_var.get() < 0:
                return False, "Button height must be non-negative"
            if self.combobox_pad_var.get() < 0:
                return False, "Combobox padding must be non-negative"
        except tk.TclError:
            return False, "Invalid numeric value"
        
        return True, ""
