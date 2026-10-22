"""Translate one gitignore glob into the regular expression Git matches it with."""

from __future__ import annotations

import re
import sys

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("mill_script_inventory_gitglob")
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "mill_script_inventory_gitglob"
    )


def _class_skip(pattern: str, index: int, chars: str) -> int:
    return index + int(index < len(pattern) and pattern[index] in chars)


def _escaped(text: str, index: int) -> bool:
    """Whether a backslash at ``index`` escapes a following character."""

    return text.startswith("\\", index) and index + 1 < len(text)


def _escape_width(pattern: str, index: int) -> int:
    return 2 if _escaped(pattern, index) else 1


def _class_close(pattern: str, start: int) -> int | None:
    index = _class_skip(pattern, _class_skip(pattern, start, "!^"), "]")
    while index < len(pattern):
        if pattern[index] == "]":
            return index
        index += _escape_width(pattern, index)
    return None


def _class_range(body: str, atom: str, index: int) -> tuple[str, int] | None:
    if index + 1 >= len(body) or body[index] != "-":
        return None
    end = body[index + 1]
    if len(atom) != 1 or len(end) != 1:
        return None
    return f"{re.escape(atom)}-{re.escape(end)}", index + 2


def _class_regex(body: str) -> str:
    parts: list[str] = []
    index = 0
    while index < len(body):
        if _escaped(body, index):
            parts.append(re.escape(body[index + 1]))
            index += 2
            continue
        atom = body[index]
        index += 1
        ranged = _class_range(body, atom, index)
        if ranged is None:
            parts.append(re.escape(atom))
            continue
        token, index = ranged
        parts.append(token)
    return "".join(parts)


def _character_class(pattern: str, index: int) -> tuple[str, int]:
    close = _class_close(pattern, index + 1)
    inner = pattern[index + 1 : close] if close is not None else ""
    negated = inner[:1] in "!^"
    body = inner[1:] if negated else inner
    if close is None or not body:
        return re.escape("["), index + 1
    translated = _class_regex(body)
    if negated:
        return f"[^{translated}/]", close + 1
    return f"(?:(?!/)[{translated}])", close + 1


def _glob_star(pattern: str, index: int) -> tuple[str, int] | None:
    if pattern.startswith("**", index) and pattern[index + 2 : index + 3] in ("", "/"):
        skip = 3 if pattern.startswith("**/", index) else 2
        return ".*", index + skip
    if pattern[index] == "*":
        return "[^/]*", index + 1
    if pattern[index] == "?":
        return "[^/]", index + 1
    return None


def _wildcard_token(pattern: str, index: int) -> tuple[str, int]:
    starred = _glob_star(pattern, index)
    if starred is not None:
        return starred
    if _escaped(pattern, index):
        return re.escape(pattern[index + 1]), index + 2
    if pattern[index] == "[":
        return _character_class(pattern, index)
    return re.escape(pattern[index]), index + 1


def wildcard_regex(pattern: str, flags: int = 0) -> re.Pattern[str]:
    pattern = pattern.removesuffix("/")
    anchored = pattern.startswith("/") or "/" in pattern
    pattern = pattern.removeprefix("/")
    chunks: list[str] = []
    index = 0
    while index < len(pattern):
        token, index = _wildcard_token(pattern, index)
        chunks.append(token)
    prefix = "^" if anchored else "(?:^|/)"
    return re.compile(prefix + "".join(chunks) + "$", flags)


if __package__:
    _expose_package_sibling(__name__)
