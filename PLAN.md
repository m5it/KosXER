# Plan: KosDWM Auto-Generative Menu Support
## ID: 1784417134.5953996
## Created: 2026-07-18 23:25:34
## Status: in_progress

### Goal:
Add full read/write/editor support for KosDWM's auto-generative menu folders. These menus live under ~/.config/KosDWM/Menus/ and each subfolder contains a config.json (with fields like windowContent, windowScript, loop, looptype) plus companion files such as content.html and ok.py. Preserve structure and comments on round-trip. Extend the KosXER GUI so users can browse, edit, validate, and save these auto-generative menu entries.

### Tasks (10):
1. [completed] Inspect all auto-generative menu files
   ID: 1784417875.0247803
   Progress logs: 1 entries

2. [completed] Design parser architecture
   ID: 1784417875.0249612

3. [completed] Implement comment-preserving JSON helper
   ID: 1784417875.0632682

4. [completed] Implement auto-generative menu parser
   ID: 1784417875.063413

5. [completed] Extend KosDWM menu editor for auto-gen menus
   ID: 1784417875.0635374

6. [in_progress] Register parser and editor in main app
   ID: 1784417875.063657

7. [pending] Test end-to-end and document
   ID: 1784417875.0637774

8. [pending] Wire auto-gen editor into main.py
   ID: 1784420824.1908677

9. [pending] Enable file browser to open auto-gen menu folders
   ID: 1784420824.1910958

10. [pending] Test end-to-end and document
   ID: 1784420824.192427

---

