#!/usr/bin/env python3
"""
Comment-Preserving JSON Helper for KosXER

Reads and writes JSON files that contain // and /* */ comments.
Comments are stripped during parsing, remembered with their line
positions, and re-inserted on write-back so that hand-written notes
in auto-generative menu config files survive editing.
"""

import json
import re
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple


@dataclass
class Comment:
    """Represents a single preserved comment."""
    text: str
    line: int          # 1-based line number in the original file
    column: int = 0    # character offset on that line
    inline: bool = False  # True for // comments, False for /* */ blocks


class CommentPreservingJSON:
    """
    JSON loader/dumper that preserves // and /* */ comments.

    The extractor uses a small state machine so that comments inside
    JSON string literals are not treated as comments. Multi-line block
    comments are stored at their starting line and re-inserted there.

    Limitations:
    - Comments are re-attached by original line number, so adding or
      removing JSON keys may shift a comment relative to the key it
      originally described. For config headers and inline end-of-line
      notes this is usually acceptable.
    - Line/column tracking is 1-based for lines and 0-based for columns.
    """

    def __init__(self, indent: int = 4):
        self.indent = indent
        self.comments: List[Comment] = []

    def load(self, text: str) -> Dict[str, Any]:
        """Parse JSON text, remembering any comments."""
        self.comments = self._extract_comments(text)
        clean = self._strip_comments(text)
        return json.loads(clean)

    def dump(self, data: Dict[str, Any]) -> str:
        """Serialize data back to JSON with preserved comments."""
        base = json.dumps(data, indent=self.indent, ensure_ascii=False)
        return self._reinsert_comments(base)

    def _extract_comments(self, text: str) -> List[Comment]:
        """Collect all // and /* */ comments with line positions."""
        comments: List[Comment] = []
        lines = text.splitlines()

        in_block = False
        block_text = ""
        block_start_line = 0
        block_start_col = 0

        for line_no, raw_line in enumerate(lines, start=1):
            line = raw_line

            # Continue an ongoing multi-line block comment.
            if in_block:
                end = line.find("*/")
                if end == -1:
                    block_text += "\n" + line
                    continue
                block_text += "\n" + line[:end + 2]
                comments.append(Comment(
                    text=block_text,
                    line=block_start_line,
                    column=block_start_col,
                    inline=False
                ))
                in_block = False
                block_text = ""
                line = line[end + 2:]

            i = 0
            in_string = False
            escape = False

            while i < len(line):
                ch = line[i]

                if in_string:
                    if escape:
                        escape = False
                        i += 1
                        continue
                    if ch == "\\":
                        escape = True
                        i += 1
                        continue
                    if ch == '"':
                        in_string = False
                    i += 1
                    continue

                # Start of string literal.
                if ch == '"':
                    in_string = True
                    i += 1
                    continue

                # Single-line // comment.
                if ch == "/" and i + 1 < len(line) and line[i + 1] == "/":
                    comment_text = line[i:]
                    comments.append(Comment(
                        text=comment_text,
                        line=line_no,
                        column=i,
                        inline=True
                    ))
                    break  # rest of line is comment

                # Block comment starting.
                if ch == "/" and i + 1 < len(line) and line[i + 1] == "*":
                    block_start_line = line_no
                    block_start_col = i
                    end = line.find("*/", i + 2)
                    if end == -1:
                        in_block = True
                        block_text = line[i:]
                        break
                    block_text = line[i:end + 2]
                    comments.append(Comment(
                        text=block_text,
                        line=line_no,
                        column=i,
                        inline=False
                    ))
                    i = end + 2
                    continue

                i += 1

        # Handle unterminated block comment at EOF (preserve it anyway).
        if in_block and block_text:
            comments.append(Comment(
                text=block_text,
                line=block_start_line,
                column=block_start_col,
                inline=False
            ))

        return comments

    def _strip_comments(self, text: str) -> str:
        """Return text with all // and /* */ comments removed."""
        lines = text.splitlines()
        result: List[str] = []
        in_block = False

        for raw_line in lines:
            line = raw_line
            if in_block:
                end = line.find("*/")
                if end == -1:
                    result.append("")
                    continue
                in_block = False
                line = line[end + 2:]

            i = 0
            out_chars: List[str] = []
            in_string = False
            escape = False

            while i < len(line):
                ch = line[i]

                if in_string:
                    out_chars.append(ch)
                    if escape:
                        escape = False
                        i += 1
                        continue
                    if ch == "\\":
                        escape = True
                    elif ch == '"':
                        in_string = False
                    i += 1
                    continue

                if ch == '"':
                    in_string = True
                    out_chars.append(ch)
                    i += 1
                    continue

                if ch == "/" and i + 1 < len(line):
                    if line[i + 1] == "/":
                        break  # discard rest of line
                    if line[i + 1] == "*":
                        end = line.find("*/", i + 2)
                        if end == -1:
                            in_block = True
                            break
                        i = end + 2
                        continue

                out_chars.append(ch)
                i += 1

            result.append("".join(out_chars))

        return "\n".join(result)

    def _reinsert_comments(self, json_text: str) -> str:
        """Re-insert preserved comments into freshly serialized JSON."""
        if not self.comments:
            return json_text + "\n"

        # Group comments by target line number.
        by_line: Dict[int, List[Comment]] = {}
        for c in self.comments:
            by_line.setdefault(c.line, []).append(c)

        # Sort each line's comments by column so order is stable.
        for line_comments in by_line.values():
            line_comments.sort(key=lambda c: c.column)

        lines = json_text.splitlines()
        result: List[str] = []

        # Prepend any comments that were on line 0 or before line 1.
        if 0 in by_line:
            for c in by_line[0]:
                result.append(c.text)
            del by_line[0]

        for line_no, line in enumerate(lines, start=1):
            if line_no in by_line:
                line_comments = by_line[line_no]
                block_comments = [c for c in line_comments if not c.inline]
                inline_comments = [c for c in line_comments if c.inline]

                # Block comments go on their own line above the JSON line.
                for bc in block_comments:
                    result.append(bc.text)

                # Inline comments are appended to the end of the JSON line.
                if inline_comments:
                    stripped = line.rstrip()
                    suffix = "  " + " ".join(c.text for c in inline_comments)
                    line = stripped + suffix

            result.append(line)

        # Append any comments that were beyond the new last line.
        max_original = max(c.line for c in self.comments)
        for extra_line in range(len(lines) + 1, max_original + 1):
            if extra_line in by_line:
                for c in by_line[extra_line]:
                    result.append(c.text)

        return "\n".join(result) + "\n"
