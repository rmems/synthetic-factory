#!/usr/bin/env python3
"""Small shared predicates for validating decoded JSON values and identifiers."""

from __future__ import annotations

from ._contract import bind_import_twin

__all__ = ["is_count", "is_identifier", "is_int", "is_text"]


def is_text(value: object) -> bool:
    return isinstance(value, str)


def is_int(value: object) -> bool:
    """A genuine integer: ``bool`` is excluded."""

    return isinstance(value, int) and not isinstance(value, bool)


def is_count(value: object) -> bool:
    return is_int(value) and value >= 0


def _trimmed(value: str) -> bool:
    return bool(value) and value == value.strip()


def _clean(value: str) -> bool:
    return _trimmed(value) and value.isprintable()


def is_identifier(value: object) -> bool:
    """A non-empty, unpadded, printable string: a program id, function name or proposal id."""

    return is_text(value) and _clean(value)


bind_import_twin(__name__)
