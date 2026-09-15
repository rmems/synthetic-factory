#!/usr/bin/env python3
"""Fail-closed checks over an ACM catalog payload."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from . import _contract
from . import identity

# Wrap-mill cartesian leftovers. Historical plant needles stay in the catalog
# bans table but must not convict a later distinct slug that happens to overlap.
WRAP_NEEDLES = ("w131", "422-vs-400", "207-multistatus")

__all__ = ["WRAP_NEEDLES", "check_catalog", "check_tree_has_no_vendor"]


def check_tree_has_no_vendor(root: Path) -> None:
    """Refuse a tree that contains a vendored ``acm-mill*.py`` file."""

    identity.refuse_vendor_paths(root.rglob("acm-mill-*.py"))


def check_catalog(payload: Mapping[str, Any]) -> None:
    """Refuse a catalog that drifted from identity or pair shape."""

    if payload.get("factory") != identity.FACTORY_NAME:
        raise ValueError("catalog factory is not api-contract-migration-factory")
    if payload.get("family") != identity.FAMILY:
        raise ValueError("catalog family is not acm")
    if payload.get("quota") != identity.QUOTA:
        raise ValueError("catalog quota must be 2")
    if payload.get("steps") != identity.STEPS:
        raise ValueError("catalog steps must be 16")
    rows = payload.get("rows")
    if not isinstance(rows, list) or not rows:
        raise ValueError("catalog rows are missing")
    slugs: set[str] = set()
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("catalog row is not an object")
        success = row.get("success_slug")
        fail = row.get("fail_slug")
        if not isinstance(success, str) or not isinstance(fail, str):
            raise ValueError("catalog row is missing slugs")
        if success == fail:
            raise ValueError(f"pair slugs are not distinct: {success}")
        for slug in (success, fail):
            if slug in slugs:
                raise ValueError(f"duplicate slug {slug}")
            slugs.add(slug)
            for needle in WRAP_NEEDLES:
                if needle in slug:
                    raise ValueError(f"banned needle {needle!r} in {slug}")


_contract.bind_import_twin(__name__)
