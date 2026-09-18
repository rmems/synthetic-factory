#!/usr/bin/env python3
"""Bind archived family names to tracked, cleaned production package owners."""

from __future__ import annotations

import re
import sys
from collections.abc import Iterable, Mapping, Sequence
from pathlib import PurePosixPath

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("mill_script_inventory_families")
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "mill_script_inventory_families"
    )

# The reviewed search package owns the sir home mills; sir is the source prefix.
CANONICAL_PACKAGES = {"sir": "search"}


def _archive_family(path: str) -> str:
    name = PurePosixPath(path).name
    for prefix in ("_gen_", "mill_", "unique_"):
        name = name.removeprefix(prefix)
    family = re.split(r"[-_.]", name, maxsplit=1)[0]
    return CANONICAL_PACKAGES.get(family, family)


def expected_family_owners(archived: Iterable[str], tracked: Sequence[str]) -> dict[str, str]:
    """Require owners only for families with a tracked production package."""

    tracked_set = frozenset(tracked)
    families = {_archive_family(path) for path in archived}
    return {
        family: f"pipelines/{family}"
        for family in sorted(families)
        if f"pipelines/{family}/__init__.py" in tracked_set
    }


def family_owner_findings(rows: Sequence[Mapping], expected: Mapping[str, str]) -> tuple:
    declared = {row["family"]: row for row in rows}
    return tuple(
        (family, owner)
        for family, owner in expected.items()
        if not _matches_owner(declared.get(family), owner)
    )


def _matches_owner(row: Mapping | None, owner: str) -> bool:
    if row is None:
        return False
    return (row["owner"], row["classification"]) == (owner, "production")


if __package__:
    _expose_package_sibling(__name__)
