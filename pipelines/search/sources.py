#!/usr/bin/env python3
"""Pinned inventory of the search leftover mills and the r72 home mill.

Leftover blob SHAs are the preserve-commit objects (``vocabulary.PRESERVE_COMMIT``);
they are byte-identical on ``origin/legacy-mill-lane`` tip. The leftover3 and
leftover-lll publishers hop destinations; they stay off this branch.
``R72_SOURCE`` pins ``experiments/sir-mill-r72.py`` from
``vocabulary.R72_PRESERVE_COMMIT`` (also byte-identical on the legacy tip).
"""

from __future__ import annotations

from dataclasses import dataclass

from .vocabulary import (
    KIND_HOME_PAIRS,
    KIND_LEFTOVER_PAIRS,
    R72_BLOB_SHA,
    R72_CATALOG_FIRST,
    R72_MILL_ID,
    R72_PATH,
)


@dataclass(frozen=True)
class MillSource:
    mill_id: str
    path: str
    blob_sha: str
    kind: str
    catalog_first: int
    n_hops: int


MILL_SOURCES: tuple[MillSource, ...] = (
    MillSource(
        "search_index_rebuild_leftover3_mill",
        "experiments/search_index_rebuild_leftover3_mill.py",
        "029b28f311e9da41576f8e06e1db3a8d713eb4ce",
        KIND_LEFTOVER_PAIRS,
        88,
        8,
    ),
    MillSource(
        "search_index_rebuild_leftover_lll_mill",
        "experiments/search_index_rebuild_leftover_lll_mill.py",
        "ccd668f3475403a97680b13e5486d975a2d370e4",
        KIND_LEFTOVER_PAIRS,
        108,
        11,
    ),
)


R72_SOURCE = MillSource(
    R72_MILL_ID,
    R72_PATH,
    R72_BLOB_SHA,
    KIND_HOME_PAIRS,
    R72_CATALOG_FIRST,
    0,
)


def catalog_sources() -> tuple[MillSource, ...]:
    return MILL_SOURCES


def r72_source() -> MillSource:
    return R72_SOURCE


def source_by_id(mill_id: str) -> MillSource:
    if mill_id == R72_SOURCE.mill_id:
        return R72_SOURCE
    for source in MILL_SOURCES:
        if source.mill_id == mill_id:
            return source
    raise KeyError(f"unknown search mill source {mill_id!r}")
