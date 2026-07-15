"""
Configuration package for KosXER.

Handles application settings and preferences.
"""

from .settings import Settings
from .constants import APP_NAME, VERSION, DEFAULT_CONFIG

__all__ = [
    'Settings',
    'APP_NAME',
    'VERSION',
    'DEFAULT_CONFIG',
]
