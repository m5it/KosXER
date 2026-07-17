# Plan: Add KosDWM Support to KosXER
## ID: 1784214754.9100733
## Created: 2026-07-16 15:12:34
## Status: completed

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
1. [completed] Create a parser for KosDWM's config.json file:
- Parse JSON 
   ID: 1784214762.1119437
   Progress logs: 1 entries

2. [completed] Create a parser for KosDWM's dynamic menu structure:
- Parse
   ID: 1784214766.6056743

3. [completed] Create editor widget for KosDWM config.json:
- Extend Editor
   ID: 1784214771.5438101

4. [completed] Create editor widget for KosDWM dynamic menus:
- Extend Edit
   ID: 1784214775.980242

5. [completed] Update the parser registry to include KosDWM:
- Register Kos
   ID: 1784214781.3090127

---

