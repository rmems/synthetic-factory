#!/usr/bin/env python3
"""Pinned identity and fail-closed vendor refusal for the search mill family."""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

from .vocabulary import FAMILY_PREFIX, FORBIDDEN_MILL_GLOBS, VENDOR_PREFIXES


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
    return False


def refuse_vendor_paths(paths: Iterable[Path | str]) -> None:
    """Fail closed if any path would vendor a leftover3 search mill script."""

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
