# KosDWM Auto-Generative Menu Parser Design

## Decision: Create a new parser

The existing `KosDWMMenuParser` models **dynamic script menus**:
- Folders = submenus
- `.py` scripts = executable menu items
- `config.json` fields: `label`, `icon`, `description`, `sort`

The auto-generative menus under `~/.config/KosDWM/Menus/` are a **different model**:
- Leaf folders = individual generated windows
- `config.json` fields: `windowContent`, `windowScript`, `title`, `loop`, `looptype`
- Companion files: `content.html` (static body), `ok.py` (confirm callback)

Therefore we create `KosDWMMenuAutoGenParser` rather than extending the old parser. They share only the `CommentPreservingJSON` helper for round-tripping `config.json` comments.

## Dataclasses

```python
@dataclass
class AutoGenMenuConfig:
    windowContent: Optional[str] = None   # filename, e.g. "content.html"
    windowScript: Optional[str] = None    # shell command
    title: Optional[str] = None           # window title
    loop: Optional[int] = None            # refresh interval
    looptype: Optional[str] = None        # "second", "minute", etc.
    # unknown keys are kept in _extra for forward compatibility

@dataclass
class AutoGenMenuItem:
    name: str                    # folder name
    folder_path: str             # absolute path to leaf folder
    config: AutoGenMenuConfig  # parsed config.json
    content_body: Optional[str] = None   # raw content.html text
    ok_script: Optional[str] = None      # raw ok.py text
```

## Comment-Preserving JSON

Use `CommentPreservingJSON` helper:
1. Extract `//` and `/* */` comments with line numbers before parsing.
2. Strip comments and pass clean JSON to `json.loads`.
3. On write, dump JSON with `json.dumps` and re-insert comments at original line numbers.

## Companion File Strategy

- `content.html`: read/write as raw text. Created/updated only when `windowContent` is set.
- `ok.py`: read/write as raw text. Optional; created only if user adds an OK callback.
- The parser never executes these files; it only preserves their content.

## Validation

- At least one of `windowContent` or `windowScript` must be present.
- `loop` must be a positive integer if present.
- `looptype` must be one of: `second`, `minute`, `hour`, `millisecond` (case-insensitive).
- `windowContent` filename must exist in the folder or be creatable.
