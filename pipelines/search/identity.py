#!/usr/bin/env python3
"""Pinned identity and fail-closed vendor refusal for the search mill family."""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

from .vocabulary import (
    CATALOGED_LEFTOVER_STEMS,
    FAMILY_PREFIX,
    FORBIDDEN_MILL_GLOBS,
    LEFTOVER_MARKERS,
    VENDOR_PREFIXES,
)


def leftover_marker_in(text: str) -> bool:
    """True when ``text`` names a leftover3 / leftover-lll mill or slug."""

    return any(marker in text for marker in LEFTOVER_MARKERS)


def is_vendor_filename(name: str) -> bool:
    """True when ``name`` is a leftover3 / leftover-lll search mill publisher."""

    if not name.endswith(".py"):
        return False
    if name.startswith(VENDOR_PREFIXES):
        return True
    if name.startswith("sir-mill-leftover") or name.startswith("sir-loop-leftover"):
        return True
    if name.startswith("sir_r") and "leftover" in name and name.endswith("_mill.py"):
        return True
    return leftover_marker_in(Path(name).stem)


def refuse_vendor_paths(paths: Iterable[Path | str]) -> None:
    """Fail closed if any path would vendor a leftover3 search mill script."""

    for raw in paths:
        name = Path(raw).name
        if is_vendor_filename(name):
            raise SystemExit(f"refusing to vendor {name}")


def refuse_cataloged_leftover_mill(path: Path | str) -> None:
    """Refuse leftover3 / leftover-lll mills already cataloged in slice leftover-mills."""

    refuse_vendor_paths([path])
    stem = Path(path).stem
    if stem in CATALOGED_LEFTOVER_STEMS or leftover_marker_in(stem):
        raise SystemExit(f"refusing leftover mill already cataloged: {Path(path).name}")


def forbidden_globs() -> tuple[str, ...]:
    return FORBIDDEN_MILL_GLOBS


__all__ = [
    "FAMILY_PREFIX",
    "forbidden_globs",
    "is_vendor_filename",
    "leftover_marker_in",
    "refuse_cataloged_leftover_mill",
    "refuse_vendor_paths",
]
