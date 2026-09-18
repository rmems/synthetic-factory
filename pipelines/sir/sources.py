#!/usr/bin/env python3
"""Pinned inventory of two additional sir leftover mills on ``legacy-mill-lane``.

Blob SHAs are the preserve-commit objects (``vocabulary.PRESERVE_COMMIT``);
they are byte-identical on ``origin/legacy-mill-lane`` tip ``813f93f1``.
The leftover3 loop and the SourceFileLoader / leftover-mill publishers stay
off this branch.
The r31/r52/r72 home mills belong to ``search``; sibling identity comes
from that canonical inventory rather than duplicating its source pins.
"""

from __future__ import annotations

from dataclasses import dataclass

if __name__.startswith("pipelines."):
    from ..search.sources import R31_SOURCE
else:
    from search.sources import R31_SOURCE

from .vocabulary import KIND_LEFTOVER_PAIRS


@dataclass(frozen=True)
class MillSource:
    mill_id: str
    path: str
    blob_sha: str
    sha256: str
    kind: str
    catalog_first: int
    n_rows: int
    n_hops: int
    loads_sibling: str = ""


MILL_SOURCES: tuple[MillSource, ...] = (
    MillSource(
        "sir-mill-leftover3-r72",
        "experiments/sir-mill-leftover3-r72.py",
        "79f88a0be841682c69c50052beee6fb0f84cd27e",
        "cb86edcbae8eace3cadd14bf897f09bc67e840d1ab495134e6e230af661d8a2d",
        KIND_LEFTOVER_PAIRS,
        72,
        16,
        0,
        R31_SOURCE.path,
    ),
    MillSource(
        "sir_r108_leftover3d_mill",
        "experiments/sir_r108_leftover3d_mill.py",
        "9487f6605380f0d1ab01f9a90957f5aaabcb0438",
        "6df7f79faabfbc307f7a77c16da555e597fd6f5115f2206f8338a19d28099252",
        KIND_LEFTOVER_PAIRS,
        108,
        16,
        11,
    ),
)


def catalog_sources() -> tuple[MillSource, ...]:
    return MILL_SOURCES


def source_by_id(mill_id: str) -> MillSource:
    for source in MILL_SOURCES:
        if source.mill_id == mill_id:
            return source
    raise KeyError(f"unknown sir mill source {mill_id!r}")
