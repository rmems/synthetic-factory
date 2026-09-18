#!/usr/bin/env python3
"""Pinned inventory of the LHC w4cl-r4605 mill on ``legacy-mill-lane``.

Blob SHA is the preserve-commit object (``vocabulary.PRESERVE_COMMIT``).
The blob is byte-identical on ``e1d2e7b4`` (family preserve) and ``813f93f1``
(``origin/legacy-mill-lane`` tip). ``e5206e72`` has no leftover-named LHC
mills. The publisher stays off this branch.
"""

from __future__ import annotations

from dataclasses import dataclass

from .vocabulary import KIND_PAIRS, SLICE_MILL_ID, SOURCE_COUNT


@dataclass(frozen=True)
class MillSource:
    mill_id: str
    path: str
    blob_sha: str
    kind: str
    catalog_first: int
    n_rows: int
    n_plants: int


MILL_SOURCES: tuple[MillSource, ...] = (
    MillSource(
        SLICE_MILL_ID,
        "experiments/lhc-mill-w4cl-r4605.py",
        "221cef84404e8249e80cdbb4bfb41ce1955a4c2f",
        KIND_PAIRS,
        4605,
        24,
        48,
    ),
)


def catalog_sources() -> tuple[MillSource, ...]:
    if len(MILL_SOURCES) != SOURCE_COUNT:
        raise ValueError(f"expected {SOURCE_COUNT} w4cl mill, found {len(MILL_SOURCES)}")
    return MILL_SOURCES


def source_by_id(mill_id: str) -> MillSource:
    for source in MILL_SOURCES:
        if source.mill_id == mill_id:
            return source
    raise KeyError(f"unknown lhc w4cl mill source {mill_id!r}")
