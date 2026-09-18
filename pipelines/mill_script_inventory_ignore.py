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


def _class_close(pattern: str, start: int) -> int | None:
    index = start + int(start < len(pattern) and pattern[start] in "!^")
    index += int(index < len(pattern) and pattern[index] == "]")
    while index < len(pattern):
        if pattern[index] == "]":
            return index
        index += 2 if pattern.startswith("\\", index) and index + 1 < len(pattern) else 1
    return None


def _class_regex(body: str) -> str:
    parts: list[str] = []
    index = 0
    while index < len(body):
        if body.startswith("\\", index) and index + 1 < len(body):
            parts.append(re.escape(body[index + 1]))
            index += 2
            continue
        atom = body[index]
        index += 1
        if index + 1 < len(body) and body[index] == "-" and len(atom) == 1:
            end = body[index + 1]
            parts.append(f"{re.escape(atom)}-{re.escape(end)}")
            index += 2
            continue
        parts.append(re.escape(atom))
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


def _wildcard_token(pattern: str, index: int) -> tuple[str, int]:
    if pattern.startswith("**", index) and pattern[index + 2 : index + 3] in ("", "/"):
        skip = 3 if pattern.startswith("**/", index) else 2
        return ".*", index + skip
    char = pattern[index]
    if char in "*?":
        return "[^/]*" if char == "*" else "[^/]", index + 1
    if char == "\\" and index + 1 < len(pattern):
        return re.escape(pattern[index + 1]), index + 2
    if char == "[":
        return _character_class(pattern, index)
    return re.escape(char), index + 1


def _wildcard_regex(pattern: str) -> re.Pattern[str]:
    directory_only = pattern.endswith("/")
    pattern = pattern.removesuffix("/")
    anchored = pattern.startswith("/") or "/" in pattern
    pattern = pattern.removeprefix("/")
    chunks: list[str] = []
    index = 0
    while index < len(pattern):
        token, index = _wildcard_token(pattern, index)
        chunks.append(token)
    prefix = "^" if anchored else "(?:^|/)"
    suffix = "(?:/|$)" if directory_only else "$"
    return re.compile(prefix + "".join(chunks) + suffix)


def _load_ignore_rules(root: Path) -> tuple[tuple[str, str, str, re.Pattern[str]], ...]:
    path = Path(root) / GITIGNORE_NAME
    if not path.is_file():
        return ()
    rules = []
    for number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw.strip()
        if line and not line.startswith("#"):
            pattern = line[1:] if line.startswith("!") else line
            rules.append((GITIGNORE_NAME, str(number), line, _wildcard_regex(pattern)))
    return tuple(rules)


def gitignore_matches(root: Path, paths: Iterable[str]) -> dict[str, tuple[str, str, str]]:
    """Use Git's effective ignore rules, including negation and ancestor rules."""

    rules = _load_ignore_rules(root)
    matches: dict[str, tuple[str, str, str]] = {}
    for candidate in paths:
        last = None
        for source, line, original, regex in rules:
            if regex.search(candidate.replace("\\", "/")):
                last = (source, line, original)
        if last is not None:
            matches[candidate] = last
    return matches


def _ignored_paths(matches: Mapping[str, tuple[str, str, str]]) -> frozenset[str]:
    return frozenset(
        path for path, (_source, _line, rule) in matches.items() if not rule.startswith("!")
    )


if __package__:
    _expose_package_sibling(__name__)
