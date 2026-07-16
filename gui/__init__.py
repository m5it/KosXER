"""
GUI package for KosXER.

Contains tkinter-based UI components.
"""

from .main_window import MainWindow
from .editor_base import EditorWidget, TextEditorWidget
from .file_browser import FileBrowser
from .xresources_editor import XResourcesEditor
from .openbox_editor import OpenBoxEditor
from .kv_editor import KVEditor

__all__ = [
    'MainWindow',
    'EditorWidget',
    'TextEditorWidget',
    'FileBrowser',
    'XResourcesEditor',
    'OpenBoxEditor',
    'KVEditor',
]
