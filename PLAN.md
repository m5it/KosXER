# Plan: Add KosDWM Support to KosXER
## ID: 1784214754.9100733
## Created: 2026-07-16 15:12:34
## Status: in_progress

### Goal:
KosDWM is a dynamic window manager with:
- JSON config at ~/.config/KosDWM/config.json (colors, bar_height, layout_mode)
- Auto-generated menus from folder structure at ~/.config/KosDWM/Menus/
- Menu items are Python scripts that define menu entries
- UI theming with active/inactive button colors

Goal: Add full KosDWM support to KosXER including:
1. Parser for KosDWM config.json
2. Parser for the dynamic menu structure (folder-based menus)
3. Editor widgets for both config and menus
4. Integration with existing parser registry

### Tasks (5):
1. [pending] Create KosDWM config parser (parsers/kosdwm_config_parser.py)
   ID: 1784214762.1119437

2. [pending] Create KosDWM menu parser (parsers/kosdwm_menu_parser.py)
   ID: 1784214766.6056743

3. [pending] Create KosDWM config editor widget (gui/kosdwm_config_editor.py)
   ID: 1784214771.5438101

4. [pending] Create KosDWM menu editor widget (gui/kosdwm_menu_editor.py)
   ID: 1784214775.980242

5. [pending] Update parser registry for KosDWM support (parsers/__init__.py)
   ID: 1784214781.3090127

---

