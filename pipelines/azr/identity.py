#!/usr/bin/env python3
"""Pinned identity and fail-closed vendor refusal for the AZR mill family."""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

from .vocabulary import FAMILY_PREFIX, FORBIDDEN_MILL_GLOBS, VENDOR_PREFIXES


def is_vendor_filename(name: str) -> bool:
    """True when ``name`` is an AZR mill / loop / plant / plant-gen script."""

    if not name.endswith(".py"):
        return False
    if name.startswith(VENDOR_PREFIXES):
        return True
    return name.startswith("azr_") and name.endswith("_mill.py")


def refuse_vendor_paths(paths: Iterable[Path | str]) -> None:
    """Fail closed if any path would vendor an ``azr-mill*.py`` script."""

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
