#!/usr/bin/env python3
"""Pinned inventory of the five sir pair mills on ``legacy-mill-lane``.

Blob SHAs are the preserve-commit objects (``vocabulary.PRESERVE_COMMIT``);
they are byte-identical on ``origin/legacy-mill-lane`` tip ``813f93f1``.
The leftover3 loop and the SourceFileLoader / leftover-mill publishers stay
off this branch.
"""

from __future__ import annotations

from dataclasses import dataclass

from .vocabulary import KIND_CATALOG_PAIRS, KIND_LEFTOVER_PAIRS


@dataclass(frozen=True)
class MillSource:
    mill_id: str
    path: str
    blob_sha: str
    kind: str
    catalog_first: int
    n_rows: int
    n_hops: int
    loads_sibling: str = ""


MILL_SOURCES: tuple[MillSource, ...] = (
    MillSource(
        "sir-mill-r31",
        "experiments/sir-mill-r31.py",
        "229a91d892fe12d19e21f0e25d5031bca348f51e",
        KIND_CATALOG_PAIRS,
        31,
        16,
        0,
    ),
    MillSource(
        "sir-mill-r52",
        "experiments/sir-mill-r52.py",
        "3dc95d6019dd2e193a431c6f60198d3875abbfd1",
        KIND_CATALOG_PAIRS,
        52,
        20,
        0,
        "experiments/sir-mill-r31.py",
    ),
    MillSource(
        "sir-mill-r72",
        "experiments/sir-mill-r72.py",
        "860ef89f276787201cc7ef76221bb41c339bcc76",
        KIND_CATALOG_PAIRS,
        72,
        20,
        0,
        "experiments/sir-mill-r31.py",
    ),
    MillSource(
        "sir-mill-leftover3-r72",
        "experiments/sir-mill-leftover3-r72.py",
        "79f88a0be841682c69c50052beee6fb0f84cd27e",
        KIND_LEFTOVER_PAIRS,
        72,
        16,
        0,
        "experiments/sir-mill-r31.py",
    ),
    MillSource(
        "sir_r108_leftover3d_mill",
        "experiments/sir_r108_leftover3d_mill.py",
        "9487f6605380f0d1ab01f9a90957f5aaabcb0438",
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
