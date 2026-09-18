#!/usr/bin/env python3
"""Root .gitignore wildcards, including git character classes."""

from __future__ import annotations

import re
import sys
from collections.abc import Iterable, Mapping
from pathlib import Path

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("mill_script_inventory_ignore")
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "mill_script_inventory_ignore"
    )

GITIGNORE_NAME = ".gitignore"


def _class_prefix(pattern: str, start: int) -> int:
    index = start
    if index < len(pattern) and pattern[index] in "!^":
        index += 1
    if index < len(pattern) and pattern[index] == "]":
        index += 1
    return index


def _class_close(pattern: str, start: int) -> int | None:
    index = _class_prefix(pattern, start)
    while index < len(pattern):
        if pattern[index] == "]":
            return index
        if pattern.startswith("\\", index) and index + 1 < len(pattern):
            index += 2
            continue
        index += 1
    return None


def _class_atom(body: str, index: int) -> tuple[str, int]:
    if body.startswith("\\", index) and index + 1 < len(body):
        return body[index + 1], index + 2
    return body[index], index + 1


def _class_range(body: str, atom: str, index: int) -> tuple[str, int] | None:
    if index + 1 >= len(body) or body[index] != "-":
        return None
    end, next_index = _class_atom(body, index + 1)
    if len(atom) != 1 or len(end) != 1:
        return None
    return f"{re.escape(atom)}-{re.escape(end)}", next_index


def _class_regex(body: str) -> str:
    parts: list[str] = []
    index = 0
    while index < len(body):
        atom, index = _class_atom(body, index)
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
    if pattern.startswith("\\", index) and index + 1 < len(pattern):
        return re.escape(pattern[index + 1]), index + 2
    if pattern[index] == "[":
        return _character_class(pattern, index)
    return re.escape(pattern[index]), index + 1


def _wildcard_regex(pattern: str) -> re.Pattern[str]:
    directory_only = pattern.endswith("/")
    pattern = pattern.removesuffix("/")
    anchored = pattern.startswith("/") or "/" in pattern
    pattern = pattern.removeprefix("/")
    body = ""
    index = 0
    while index < len(pattern):
        token, index = _wildcard_token(pattern, index)
        body += token
    prefix = "^" if anchored else "(?:^|/)"
    suffix = "(?:/|$)" if directory_only else "$"
    return re.compile(prefix + body + suffix)


def _gitignore_rules(root: Path) -> tuple[tuple[str, str, str, bool, re.Pattern[str]], ...]:
    path = Path(root) / GITIGNORE_NAME
    if not path.is_file():
        return ()
    rules = []
    for number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        negated = line.startswith("!")
        pattern = line[1:] if negated else line
        rules.append((GITIGNORE_NAME, str(number), line, negated, _wildcard_regex(pattern)))
    return tuple(rules)


def gitignore_matches(root: Path, paths: Iterable[str]) -> dict[str, tuple[str, str, str]]:
    """Use Git's effective ignore rules, including negation and ancestor rules."""

    rules = _gitignore_rules(root)
    matches: dict[str, tuple[str, str, str]] = {}
    for path in paths:
        last: tuple[str, str, str] | None = None
        for source, line, original, _negated, regex in rules:
            if regex.search(path.replace("\\", "/")):
                last = (source, line, original)
        if last is not None:
            matches[path] = last
    return matches


def _ignored_paths(matches: Mapping[str, tuple[str, str, str]]) -> frozenset[str]:
    return frozenset(
        path for path, (_source, _line, rule) in matches.items() if not rule.startswith("!")
    )


if __package__:
    _expose_package_sibling(__name__)
