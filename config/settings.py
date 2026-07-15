"""Settings manager for KosXER."""

import json
import os
from .constants import CONFIG_DIR, DEFAULT_CONFIG


class Settings:
    """Manages application settings persistence."""
    
    _instance = None
    
    def __new__(cls):
        """Singleton pattern for settings."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialize settings manager."""
        if self._initialized:
            return
        self._initialized = True
        self._config_file = os.path.join(CONFIG_DIR, "settings.json")
        self._settings = self._load()
    
    def _load(self) -> dict:
        """Load settings from file or return defaults."""
        if os.path.exists(self._config_file):
            try:
                with open(self._config_file, 'r', encoding='utf-8') as f:
                    loaded = json.load(f)
                    # Merge with defaults to ensure all keys exist
                    settings = DEFAULT_CONFIG.copy()
                    settings.update(loaded)
                    return settings
            except (json.JSONDecodeError, IOError) as e:
                print(f"Warning: Could not load settings: {e}")
        return DEFAULT_CONFIG.copy()
    
    def save(self):
        """Save current settings to file."""
        try:
            with open(self._config_file, 'w', encoding='utf-8') as f:
                json.dump(self._settings, f, indent=2)
        except IOError as e:
            print(f"Warning: Could not save settings: {e}")
    
    def get(self, section: str, key: str = None, default=None):
        """Get a setting value."""
        if key is None:
            return self._settings.get(section, default)
        return self._settings.get(section, {}).get(key, default)
    
    def set(self, section: str, key: str, value):
        """Set a setting value."""
        if section not in self._settings:
            self._settings[section] = {}
        self._settings[section][key] = value
        self.save()
    
    def add_recent_file(self, filepath: str):
        """Add a file to recent files list."""
        recent = self.get("files", "recent_files", [])
        max_recent = self.get("files", "max_recent", 10)
        
        # Remove if exists and add to front
        if filepath in recent:
            recent.remove(filepath)
        recent.insert(0, filepath)
        
        # Trim to max
        self._settings["files"]["recent_files"] = recent[:max_recent]
        self.save()
