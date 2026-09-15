#!/usr/bin/env python3
"""Refuse LHC mill / loop publishers so they stay on ``legacy-mill-lane``."""

from __future__ import annotations

from collections.abc import Iterable
from fnmatch import fnmatch
from pathlib import Path

from .vocabulary import FAMILY_PREFIX, FORBIDDEN_MILL_GLOBS, VENDOR_PREFIXES


def is_vendor_filename(name: str) -> bool:
    """True for ``lhc-mill*.py``, ``lhc-loop*.py``, and leftover mill publishers."""

    basename = Path(name).name
    if any(fnmatch(basename, glob) for glob in FORBIDDEN_MILL_GLOBS):
        return True
    leftover = basename.startswith("lhc_") and basename.endswith("_mill.py")
    return leftover or basename.startswith(VENDOR_PREFIXES)


def refuse_vendor_paths(paths: Iterable[Path | str]) -> None:
    """Fail closed if any path would vendor an LHC mill script onto this branch."""

    blocked = next((Path(raw).name for raw in paths if is_vendor_filename(str(raw))), None)
    if blocked is not None:
        raise SystemExit(f"refusing to vendor {blocked}")


def forbidden_globs() -> tuple[str, ...]:
    return FORBIDDEN_MILL_GLOBS


__all__ = [
    "FAMILY_PREFIX",
    "forbidden_globs",
    "is_vendor_filename",
    "refuse_vendor_paths",
]
