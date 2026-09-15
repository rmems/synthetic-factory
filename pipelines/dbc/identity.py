#!/usr/bin/env python3
"""Pinned identity and fail-closed vendor refusal for the DBC mill family."""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

from .vocabulary import (
    EXCLUDED_LAUNDERER_PATHS,
    FAMILY_PREFIX,
    FORBIDDEN_MILL_GLOBS,
    VENDOR_PREFIXES,
)


def is_vendor_filename(name: str) -> bool:
    """True when ``name`` is a DBC mill / loop / hop / leftover publisher script."""

    if name == ".dbc-used-slugs.txt":
        return True
    if not name.endswith(".py"):
        return False
    if name.startswith(VENDOR_PREFIXES):
        return True
    if name == "dbc_leftover_lang_mill.py":
        return True
    return name.startswith("dbc_") and name.endswith("_mill.py")


def is_excluded_launderer_path(path: Path | str) -> bool:
    raw = Path(path).as_posix()
    return raw.endswith(EXCLUDED_LAUNDERER_PATHS) or Path(path).name in {
        Path(item).name for item in EXCLUDED_LAUNDERER_PATHS
    }


def refuse_vendor_paths(paths: Iterable[Path | str]) -> None:
    """Fail closed if any path would vendor a ``dbc-mill*.py`` script."""

    for raw in paths:
        name = Path(raw).name
        if is_vendor_filename(name):
            raise SystemExit(f"refusing to vendor {name}")


def forbidden_globs() -> tuple[str, ...]:
    return FORBIDDEN_MILL_GLOBS


__all__ = [
    "FAMILY_PREFIX",
    "forbidden_globs",
    "is_excluded_launderer_path",
    "is_vendor_filename",
    "refuse_vendor_paths",
]
