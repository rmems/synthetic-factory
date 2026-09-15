#!/usr/bin/env python3
"""Pinned identity and fail-closed vendor refusal for the leftover mill family."""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

from .vocabulary import FAMILY_PREFIX, FORBIDDEN_MILL_GLOBS, SLUGS_FILENAME, VENDOR_PREFIXES


def is_vendor_filename(name: str) -> bool:
    """True when ``name`` is a leftover mill / loop publisher or used-slug list."""

    if name == SLUGS_FILENAME:
        return True
    if not name.endswith(".py"):
        return False
    return name.startswith(VENDOR_PREFIXES)


def refuse_vendor_paths(paths: Iterable[Path | str]) -> None:
    """Fail closed if any path would vendor a leftover mill publisher."""

    for raw in paths:
        name = Path(raw).name
        if is_vendor_filename(name):
            raise SystemExit(f"refusing to vendor {name}")


def forbidden_globs() -> tuple[str, ...]:
    return FORBIDDEN_MILL_GLOBS


__all__ = [
    "FAMILY_PREFIX",
    "forbidden_globs",
    "is_vendor_filename",
    "refuse_vendor_paths",
]
