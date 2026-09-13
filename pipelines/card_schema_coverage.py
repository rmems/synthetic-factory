#!/usr/bin/env python3
"""Glob-based payload coverage checks for card declarations.

Confirms a declaration's ``data_files`` glob patterns and a factory's actual
published payload file names agree exactly -- every published file is
claimed by some pattern, and every pattern claims at least one published
file. Both directions are reported rather than tolerated (see
``payload_coverage_errors``).
"""

from __future__ import annotations

from fnmatch import fnmatchcase

__all__ = ("payload_coverage_errors",)


def _glob_initial_row(pattern_parts: list[str]) -> list[bool]:
    row = [False] * (len(pattern_parts) + 1)
    row[0] = True
    for pattern_index, glob in enumerate(pattern_parts, 1):
        if glob == "**":
            row[pattern_index] = row[pattern_index - 1]
    return row


def _glob_advance_row(
    previous: list[bool], pattern_parts: list[str], part: str
) -> list[bool]:
    current = [False] * (len(pattern_parts) + 1)
    for pattern_index, glob in enumerate(pattern_parts, 1):
        if glob == "**":
            current[pattern_index] = current[pattern_index - 1] or previous[pattern_index]
        else:
            current[pattern_index] = previous[pattern_index - 1] and fnmatchcase(part, glob)
    return current


def _glob_matches(path: str, pattern: str) -> bool:
    """Match one repo-relative path with case-sensitive Hub-style glob semantics.

    ``*`` and ``?`` match within one path segment only. A segment consisting
    of ``**`` may consume zero or more complete segments. This prevents a
    declaration such as ``data/raw/*.jsonl`` from covering a nested payload
    that the Hub globber would not select.
    """
    path_parts = path.split("/")
    pattern_parts = pattern.split("/")
    previous = _glob_initial_row(pattern_parts)
    for part in path_parts:
        previous = _glob_advance_row(previous, pattern_parts, part)
    return previous[-1]


def _uncovered_payload_paths(paths: list[str], patterns: list[str]) -> list[str]:
    return [
        path
        for path in paths
        if not any(_glob_matches(path, pattern) for pattern in patterns)
    ]


def _unused_data_file_patterns(paths: list[str], patterns: list[str]) -> list[str]:
    return [
        pattern
        for pattern in patterns
        if not any(_glob_matches(path, pattern) for path in paths)
    ]


def payload_coverage_errors(declaration: dict, payload_names: list[str]) -> list[str]:
    """Return every mismatch between declared globs and published payload files.

    A payload file no glob matches would silently vanish from the viewer while
    the card still counts it; a glob matching nothing would advertise a config
    over an empty file set. Both are reported rather than tolerated.
    """
    if not declaration["features"]:
        return []
    patterns = declaration["data_files"]
    paths = [f"data/raw/{name}" for name in payload_names]
    errors = []
    uncovered = _uncovered_payload_paths(paths, patterns)
    if uncovered:
        errors.append(
            "published payload not matched by any declared data_files pattern: "
            + ", ".join(sorted(uncovered))
        )
    unused = _unused_data_file_patterns(paths, patterns)
    if unused:
        errors.append(
            "declared data_files pattern matches no published payload: "
            + ", ".join(unused)
        )
    return errors
