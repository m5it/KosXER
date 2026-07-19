#!/usr/bin/env python3
"""
Tests for CommentPreservingJSON helper.

Run with: python parsers/test_comment_preserving_json.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from parsers.comment_preserving_json import CommentPreservingJSON


def test_basic_roundtrip():
    """Load and dump JSON with // comments."""
    print("TEST: basic roundtrip")
    text = """{
    // This is the menu title
    "title": "Network Connections",
    "windowScript": "lsof -nwli tcp"  // dynamic command
}
"""
    cpj = CommentPreservingJSON()
    data = cpj.load(text)

    assert data["title"] == "Network Connections"
    assert data["windowScript"] == "lsof -nwli tcp"

    out = cpj.dump(data)
    assert "// This is the menu title" in out
    assert "// dynamic command" in out
    assert '"title": "Network Connections"' in out

    print("  ✓ basic roundtrip passed")


def test_block_comment():
    """Preserve /* */ block comments."""
    print("TEST: block comment")
    text = """{
    /*
     * Auto-generated menu config.
     * Do not edit by hand.
     */
    "windowContent": "content.html"
}
"""
    cpj = CommentPreservingJSON()
    data = cpj.load(text)
    assert data["windowContent"] == "content.html"

    out = cpj.dump(data)
    assert "/*" in out
    assert "* Auto-generated menu config." in out
    assert "*/" in out
    print("  ✓ block comment passed")


def test_comment_in_string_is_preserved():
    """Comments inside JSON string literals are not stripped."""
    print("TEST: comment inside string literal")
    text = """{
    // real comment
    "command": "echo // not a comment"
}
"""
    cpj = CommentPreservingJSON()
    data = cpj.load(text)
    assert data["command"] == "echo // not a comment"
    assert "// real comment" in cpj.dump(data)
    print("  ✓ comment inside string preserved")


def test_url_string_preserved():
    """URL strings containing :// are preserved."""
    print("TEST: URL string")
    text = """{
    // fetch from remote
    "url": "https://example.com/api"
}
"""
    cpj = CommentPreservingJSON()
    data = cpj.load(text)
    assert data["url"] == "https://example.com/api"
    assert "// fetch from remote" in cpj.dump(data)
    print("  ✓ URL string preserved")


def test_no_comments():
    """Plain JSON still works and gets trailing newline."""
    print("TEST: no comments")
    text = '{"a": 1, "b": 2}'
    cpj = CommentPreservingJSON()
    data = cpj.load(text)
    assert data == {"a": 1, "b": 2}
    out = cpj.dump(data)
    assert out.endswith("\n")
    assert '"a": 1' in out
    print("  ✓ no comments passed")


def test_inline_and_block_together():
    """Mix inline and block comments on the same file."""
    print("TEST: inline + block")
    text = """{
    /* header block */
    "title": "Demo", // inline note
    // another line comment
    "loop": 5
}
"""
    cpj = CommentPreservingJSON()
    data = cpj.load(text)
    assert data["title"] == "Demo"
    assert data["loop"] == 5

    out = cpj.dump(data)
    assert "/* header block */" in out
    assert "// inline note" in out
    assert "// another line comment" in out
    print("  ✓ inline + block passed")


def test_multiline_block_comment():
    """Multi-line block comments survive round-trip."""
    print("TEST: multi-line block")
    text = """{
    /*
     * Line one
     * Line two
     */
    "looptype": "second"
}
"""
    cpj = CommentPreservingJSON()
    data = cpj.load(text)
    assert data["looptype"] == "second"

    out = cpj.dump(data)
    assert "Line one" in out
    assert "Line two" in out
    print("  ✓ multi-line block passed")


def run_all_tests():
    print("\n" + "=" * 60)
    print("COMMENT-PRESERVING JSON TEST SUITE")
    print("=" * 60 + "\n")

    tests = [
        test_basic_roundtrip,
        test_block_comment,
        test_comment_in_string_is_preserved,
        test_url_string_preserved,
        test_no_comments,
        test_inline_and_block_together,
        test_multiline_block_comment,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"  ✗ {test.__name__} failed: {e}")
            failed += 1
        except Exception as e:
            print(f"  ✗ {test.__name__} raised {type(e).__name__}: {e}")
            failed += 1

    print("\n" + "=" * 60)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("=" * 60)

    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
