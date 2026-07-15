"""
Parsers module for KosXER.

Contains parsers for various configuration file formats.
"""

from .xresources_parser import XResourcesParser, XResourceEntry
from .openbox_parser import OpenBoxMenuParser, OpenBoxRCParser, OpenBoxMenu, OpenBoxMenuItem, OpenBoxSeparator

__all__ = [
    'XResourcesParser', 'XResourceEntry',
    'OpenBoxMenuParser', 'OpenBoxRCParser', 
    'OpenBoxMenu', 'OpenBoxMenuItem', 'OpenBoxSeparator'
]
