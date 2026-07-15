#!/usr/bin/env python3
"""
OpenBox Configuration Parser Module for KosXER

Parses OpenBox configuration files:
- menu.xml - Application menus
- rc.xml - Window manager configuration

Supports full XML parsing with tree structure preservation.
"""

import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List, Dict, Optional, Union, Any
from dataclasses import dataclass, field
from copy import deepcopy
import re


@dataclass
class OpenBoxMenuItem:
    """Represents a menu item (action)."""
    id: str
    label: str
    action: str                          # Execute, Restart, Exit, etc.
    action_params: Dict[str, str] = field(default_factory=dict)
    icon: Optional[str] = None
    visible: bool = True
    parent_id: Optional[str] = None
    
    def to_xml(self) -> ET.Element:
        """Convert to XML element."""
        item = ET.Element('item')
        item.set('label', self.label)
        if self.icon:
            item.set('icon', self.icon)
        
        action_elem = ET.SubElement(item, 'action')
        action_elem.set('name', self.action)
        
        for key, value in self.action_params.items():
            param = ET.SubElement(action_elem, key)
            param.text = value
        
        return item


@dataclass
class OpenBoxMenu:
    """Represents a menu (can contain items and submenus)."""
    id: str
    label: str
    icon: Optional[str] = None
    items: List[Union[OpenBoxMenuItem, 'OpenBoxMenu']] = field(default_factory=list)
    parent_id: Optional[str] = None
    execute_script: Optional[str] = None  # For pipe menus
    
    def add_item(self, item: Union[OpenBoxMenuItem, 'OpenBoxMenu']):
        """Add an item to this menu."""
        item.parent_id = self.id
        self.items.append(item)
    
    def remove_item(self, item_id: str) -> bool:
        """Remove an item by ID."""
        for i, item in enumerate(self.items):
            if isinstance(item, OpenBoxMenuItem) and item.id == item_id:
                self.items.pop(i)
                return True
            elif isinstance(item, OpenBoxMenu) and item.id == item_id:
                self.items.pop(i)
                return True
        return False
    
    def to_xml(self) -> ET.Element:
        """Convert to XML element."""
        menu = ET.Element('menu')
        menu.set('id', self.id)
        menu.set('label', self.label)
        if self.icon:
            menu.set('icon', self.icon)
        if self.execute_script:
            menu.set('execute', self.execute_script)
        
        for item in self.items:
            menu.append(item.to_xml())
        
        return menu


@dataclass
class OpenBoxSeparator:
    """Represents a menu separator."""
    label: Optional[str] = None
    
    def to_xml(self) -> ET.Element:
        """Convert to XML element."""
        sep = ET.Element('separator')
        if self.label:
            sep.set('label', self.label)
        return sep


class OpenBoxMenuParser:
    """
    Parser for OpenBox menu.xml files.
    
    Supports:
    - Menu definitions with nested submenus
    - Menu items with actions
    - Separators
    - Pipe menus (dynamic menus)
    - Icons
    """
    
    def __init__(self):
        self.root_menu: Optional[OpenBoxMenu] = None
        self.menus: Dict[str, OpenBoxMenu] = {}
        self.items: Dict[str, OpenBoxMenuItem] = {}
        self.raw_xml: Optional[str] = None
        
    def parse(self, content: str) -> OpenBoxMenu:
        """
        Parse OpenBox menu.xml content.
        
        Args:
            content: XML content string
            
        Returns:
            Root OpenBoxMenu object
        """
        self.raw_xml = content
        self.menus = {}
        self.items = {}
        
        root = ET.fromstring(content)
        
        # OpenBox menu files have <openbox_menu> as root
        if root.tag != 'openbox_menu':
            raise ValueError(f"Expected root element 'openbox_menu', got '{root.tag}'")
        
        # Find the root menu (usually the first <menu> element)
        menu_elem = root.find('menu')
        if menu_elem is None:
            raise ValueError("No menu element found in openbox_menu")
        
        self.root_menu = self._parse_menu(menu_elem)
        return self.root_menu
    
    def _parse_menu(self, elem: ET.Element, parent_id: Optional[str] = None) -> OpenBoxMenu:
        """Parse a menu element."""
        menu_id = elem.get('id', '')
        label = elem.get('label', '')
        icon = elem.get('icon')
        execute = elem.get('execute')
        
        menu = OpenBoxMenu(
            id=menu_id,
            label=label,
            icon=icon,
            execute_script=execute,
            parent_id=parent_id
        )
        
        self.menus[menu_id] = menu
        
        # Parse children (items, submenus, separators)
        for child in elem:
            if child.tag == 'item':
                item = self._parse_item(child, menu_id)
                menu.add_item(item)
            elif child.tag == 'menu':
                submenu = self._parse_menu(child, menu_id)
                menu.add_item(submenu)
            elif child.tag == 'separator':
                sep = self._parse_separator(child)
                menu.add_item(sep)
        
        return menu
    
    def _parse_item(self, elem: ET.Element, parent_id: str) -> OpenBoxMenuItem:
        """Parse a menu item element."""
        item_id = elem.get('id', f"{parent_id}_item_{len(self.items)}")
        label = elem.get('label', '')
        icon = elem.get('icon')
        
        # Parse action
        action_elem = elem.find('action')
        if action_elem is None:
            action = 'Execute'
            action_params = {}
        else:
            action = action_elem.get('name', 'Execute')
            action_params = {}
            for param in action_elem:
                action_params[param.tag] = param.text or ''
        
        item = OpenBoxMenuItem(
            id=item_id,
            label=label,
            action=action,
            action_params=action_params,
            icon=icon,
            parent_id=parent_id
        )
        
        self.items[item_id] = item
        return item
    
    def _parse_separator(self, elem: ET.Element) -> OpenBoxSeparator:
        """Parse a separator element."""
        label = elem.get('label')
        return OpenBoxSeparator(label=label)
    
    def parse_file(self, filepath: Union[str, Path]) -> OpenBoxMenu:
        """
        Parse an OpenBox menu file from disk.
        
        Args:
            filepath: Path to menu.xml
            
        Returns:
            Root OpenBoxMenu object
        """
        filepath = Path(filepath)
        
        if not filepath.exists():
            raise FileNotFoundError(f"File not found: {filepath}")
        
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return self.parse(content)
    
    def get_menu_by_id(self, menu_id: str) -> Optional[OpenBoxMenu]:
        """Get a menu by its ID."""
        return self.menus.get(menu_id)
    
    def get_item_by_id(self, item_id: str) -> Optional[OpenBoxMenuItem]:
        """Get an item by its ID."""
        return self.items.get(item_id)
    
    def find_menu_by_label(self, label: str) -> Optional[OpenBoxMenu]:
        """Find a menu by its label."""
        for menu in self.menus.values():
            if menu.label == label:
                return menu
        return None
    
    def add_menu(self, parent_menu_id: str, menu: OpenBoxMenu) -> bool:
        """
        Add a submenu to an existing menu.
        
        Args:
            parent_menu_id: ID of parent menu
            menu: Menu to add
            
        Returns:
            True if added successfully
        """
        parent = self.menus.get(parent_menu_id)
        if parent:
            parent.add_item(menu)
            self.menus[menu.id] = menu
            return True
        return False
    
    def add_item(self, menu_id: str, item: OpenBoxMenuItem) -> bool:
        """
        Add an item to a menu.
        
        Args:
            menu_id: ID of menu
            item: Item to add
            
        Returns:
            True if added successfully
        """
        menu = self.menus.get(menu_id)
        if menu:
            menu.add_item(item)
            self.items[item.id] = item
            return True
        return False
    
    def remove_menu(self, menu_id: str) -> bool:
        """
        Remove a menu by ID.
        
        Args:
            menu_id: Menu ID to remove
            
        Returns:
            True if removed
        """
        if menu_id in self.menus:
            del self.menus[menu_id]
            # Also remove from parent's items list
            for menu in self.menus.values():
                menu.remove_item(menu_id)
            return True
        return False
    
    def remove_item(self, item_id: str) -> bool:
        """
        Remove an item by ID.
        
        Args:
            item_id: Item ID to remove
            
        Returns:
            True if removed
        """
        if item_id in self.items:
            del self.items[item_id]
            # Also remove from parent's items list
            for menu in self.menus.values():
                menu.remove_item(item_id)
            return True
        return False
    
    def write_back(self, filepath: Optional[Union[str, Path]] = None,
                  pretty: bool = True) -> str:
        """
        Generate XML content from parsed menu structure.
        
        Args:
            filepath: Optional path to write to
            pretty: Whether to format with indentation
            
        Returns:
            XML string
        """
        if self.root_menu is None:
            raise ValueError("No menu to write. Parse a file first.")
        
        # Create root element
        root = ET.Element('openbox_menu')
        root.set('xmlns', 'http://openbox.org/3.4/menu')
        
        # Add menu
        root.append(self.root_menu.to_xml())
        
        # Convert to string
        if pretty:
            xml_str = self._prettify_xml(root)
        else:
            xml_str = ET.tostring(root, encoding='unicode')
        
        # Write to file if path provided
        if filepath:
            filepath = Path(filepath)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(xml_str)
        
        return xml_str
    
    def _prettify_xml(self, elem: ET.Element, level: int = 0) -> str:
        """Convert XML element to pretty-printed string."""
        indent = '  ' * level
        lines = []
        
        # Opening tag with attributes
        attribs = ' '.join([f'{k}="{v}"' for k, v in elem.attrib.items()])
        if attribs:
            lines.append(f'{indent}<{elem.tag} {attribs}>')
        else:
            lines.append(f'{indent}<{elem.tag}>')
        
        # Text content
        if elem.text and elem.text.strip():
            lines.append(f'{indent}  {elem.text.strip()}')
        
        # Children
        has_children = len(elem) > 0
        for child in elem:
            child_str = self._prettify_xml(child, level + 1)
            lines.append(child_str)
        
        # Closing tag
        if has_children:
            lines.append(f'{indent}</{elem.tag}>')
        else:
            if lines[-1].endswith('>'):
                lines[-1] = lines[-1][:-1] + '/>'
            else:
                lines.append(f'{indent}</{elem.tag}>')
        
        return '\n'.join(lines)
    
    def get_menu_tree(self, menu: Optional[OpenBoxMenu] = None, 
                      level: int = 0) -> str:
        """
        Get a text representation of the menu tree structure.
        
        Args:
            menu: Menu to start from (defaults to root)
            level: Indentation level
            
        Returns:
            String representation of tree
        """
        if menu is None:
            menu = self.root_menu
        
        if menu is None:
            return ""
        
        indent = "  " * level
        lines = [f"{indent}[Menu] {menu.label} (ID: {menu.id})"]
        
        for item in menu.items:
            if isinstance(item, OpenBoxMenuItem):
                lines.append(f"{indent}  [Item] {item.label} -> {item.action}")
            elif isinstance(item, OpenBoxMenu):
                lines.append(self.get_menu_tree(item, level + 1))
            elif isinstance(item, OpenBoxSeparator):
                label_str = f" ({item.label})" if item.label else ""
                lines.append(f"{indent}  [Separator]{label_str}")
        
        return '\n'.join(lines)
    
    def __len__(self) -> int:
        """Return total number of menus."""
        return len(self.menus)
    
    def __iter__(self):
        """Iterate over menus."""
        return iter(self.menus.values())


class OpenBoxRCParser:
    """
    Parser for OpenBox rc.xml configuration files.
    
    Parses window manager settings, keybindings, mouse bindings,
    themes, and other configuration.
    """
    
    def __init__(self):
        self.config: Dict[str, Any] = {}
        self.keybindings: List[Dict[str, str]] = []
        self.mousebindings: List[Dict[str, str]] = []
        
    def parse(self, content: str) -> Dict[str, Any]:
        """
        Parse rc.xml content.
        
        Args:
            content: XML content string
            
        Returns:
            Dictionary with configuration
        """
        root = ET.fromstring(content)
        
        if root.tag != 'openbox_config':
            raise ValueError(f"Expected root element 'openbox_config', got '{root.tag}'")
        
        self.config = self._parse_config(root)
        return self.config
    
    def _parse_config(self, elem: ET.Element) -> Dict[str, Any]:
        """Parse configuration elements."""
        config = {}
        
        for child in elem:
            if child.tag == 'theme':
                config['theme'] = self._parse_theme(child)
            elif child.tag == 'desktops':
                config['desktops'] = self._parse_desktops(child)
            elif child.tag == 'resize':
                config['resize'] = self._parse_resize(child)
            elif child.tag == 'focus':
                config['focus'] = self._parse_focus(child)
            elif child.tag == 'placement':
                config['placement'] = self._parse_placement(child)
            elif child.tag == 'menu':
                config['menu'] = self._parse_menu_settings(child)
            elif child.tag == 'applications':
                config['applications'] = self._parse_applications(child)
            elif child.tag == 'keyboard':
                config['keyboard'] = self._parse_keyboard(child)
            elif child.tag == 'mouse':
                config['mouse'] = self._parse_mouse(child)
        
        return config
    
    def _parse_theme(self, elem: ET.Element) -> Dict[str, Any]:
        """Parse theme settings."""
        theme = {}
        for child in elem:
            if child.tag in ('name', 'titleLayout', 'animateIconify', 'font'):
                theme[child.tag] = child.text or ''
        return theme
    
    def _parse_desktops(self, elem: ET.Element) -> Dict[str, Any]:
        """Parse desktop settings."""
        desktops = {}
        for child in elem:
            if child.tag in ('number', 'firstdesk', 'popupTime', 'names'):
                if child.tag == 'names':
                    desktops['names'] = [name.text for name in child.findall('name') if name.text]
                else:
                    desktops[child.tag] = child.text or ''
        return desktops
    
    def _parse_resize(self, elem: ET.Element) -> Dict[str, Any]:
        """Parse resize settings."""
        return {child.tag: child.text for child in elem if child.text}
    
    def _parse_focus(self, elem: ET.Element) -> Dict[str, Any]:
        """Parse focus settings."""
        return {child.tag: child.text for child in elem if child.text}
    
    def _parse_placement(self, elem: ET.Element) -> Dict[str, Any]:
        """Parse window placement settings."""
        return {child.tag: child.text for child in elem if child.text}
    
    def _parse_menu_settings(self, elem: ET.Element) -> Dict[str, Any]:
        """Parse menu settings."""
        return {child.tag: child.text for child in elem if child.text}
    
    def _parse_applications(self, elem: ET.Element) -> List[Dict[str, Any]]:
        """Parse application-specific settings."""
        apps = []
        for app in elem.findall('application'):
            app_config = {
                'class': app.get('class', ''),
                'name': app.get('name', ''),
                'role': app.get('role', ''),
                'type': app.get('type', ''),
                'settings': {child.tag: child.text for child in app if child.text}
            }
            apps.append(app_config)
        return apps
    
    def _parse_keyboard(self, elem: ET.Element) -> Dict[str, Any]:
        """Parse keyboard settings and keybindings."""
        keyboard = {
            'chainQuitKey': elem.findtext('chainQuitKey', ''),
            'keybindings': []
        }
        
        for keybind in elem.findall('keybind'):
            binding = {
                'key': keybind.get('key', ''),
                'chroot': keybind.get('chroot'),
                'actions': []
            }
            for action in keybind.findall('action'):
                action_dict = {'name': action.get('name', '')}
                for param in action:
                    action_dict[param.tag] = param.text or ''
                binding['actions'].append(action_dict)
            keyboard['keybindings'].append(binding)
            self.keybindings.append(binding)
        
        return keyboard
    
    def _parse_mouse(self, elem: ET.Element) -> Dict[str, Any]:
        """Parse mouse settings and bindings."""
        mouse = {
            'dragThreshold': elem.findtext('dragThreshold', ''),
            'doubleClickTime': elem.findtext('doubleClickTime', ''),
            'screenEdgeWarpTime': elem.findtext('screenEdgeWarpTime', ''),
            'bindings': []
        }
        
        for context in elem.findall('context'):
            ctx_name = context.get('name', '')
            for mousebind in context.findall('mousebind'):
                binding = {
                    'context': ctx_name,
                    'button': mousebind.get('button', ''),
                    'action': mousebind.get('action', ''),
                    'commands': []
                }
                for action in mousebind.findall('action'):
                    cmd = {'name': action.get('name', '')}
                    for param in action:
                        cmd[param.tag] = param.text or ''
                    binding['commands'].append(cmd)
                mouse['bindings'].append(binding)
                self.mousebindings.append(binding)
        
        return mouse
    
    def parse_file(self, filepath: Union[str, Path]) -> Dict[str, Any]:
        """
        Parse an rc.xml file from disk.
        
        Args:
            filepath: Path to rc.xml
            
        Returns:
            Configuration dictionary
        """
        filepath = Path(filepath)
        
        if not filepath.exists():
            raise FileNotFoundError(f"File not found: {filepath}")
        
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return self.parse(content)
    
    def get_keybinding(self, key: str) -> Optional[Dict[str, str]]:
        """Get keybinding for a specific key combination."""
        for binding in self.keybindings:
            if binding['key'] == key:
                return binding
        return None
    
    def add_keybinding(self, key: str, action: str, action_params: Dict[str, str] = None):
        """
        Add a new keybinding.
        
        Args:
            key: Key combination (e.g., 'C-A-t' for Ctrl+Alt+t)
            action: Action name
            action_params: Optional action parameters
        """
        binding = {
            'key': key,
            'actions': [{'name': action, **(action_params or {})}]
        }
        self.keybindings.append(binding)
        if 'keyboard' in self.config:
            self.config['keyboard']['keybindings'].append(binding)
    
    def remove_keybinding(self, key: str) -> bool:
        """Remove a keybinding by key combination."""
        for i, binding in enumerate(self.keybindings):
            if binding['key'] == key:
                self.keybindings.pop(i)
                return True
        return False
