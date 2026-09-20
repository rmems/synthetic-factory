#!/usr/bin/env python3
"""Pinned identity and fail-closed vendor refusal for the IAC mill family."""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

from .vocabulary import FAMILY_PREFIX, FORBIDDEN_MILL_GLOBS, VENDOR_PREFIXES


def is_vendor_filename(name: str) -> bool:
    """True when ``name`` is an IAC mill / loop / plant-gen publisher script."""

    if not name.endswith(".py"):
        return False
    if name.startswith(VENDOR_PREFIXES):
        return True
    if name.startswith("mill_plants") and name.endswith(".py"):
        return True
    if name.startswith("infra_as_code_mill"):
        return True
    return name.startswith("iac_") and name.endswith("_mill.py")


def is_vendor_path(path: Path | str) -> bool:
    """True when any component of ``path`` belongs to a forbidden mill lane."""

    candidate = Path(path)
    if is_vendor_filename(candidate.name):
        return True
    return candidate.name.endswith(".py") and "infra_as_code_mill" in candidate.parts


def refuse_vendor_paths(paths: Iterable[Path | str]) -> None:
    """Fail closed if any path would vendor an ``iac-mill*.py`` script."""

    for raw in paths:
        if is_vendor_path(raw):
            raise SystemExit(f"refusing to vendor {raw}")


def forbidden_globs() -> tuple[str, ...]:
    return FORBIDDEN_MILL_GLOBS


__all__ = [
    "FAMILY_PREFIX",
    "forbidden_globs",
    "is_vendor_filename",
    "is_vendor_path",
    "refuse_vendor_paths",
]
