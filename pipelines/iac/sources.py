#!/usr/bin/env python3
"""Pinned inventory of the 15 IAC scripts on ``legacy-mill-lane``.

Blob SHAs are the preserve-commit objects (``vocabulary.PRESERVE_COMMIT``);
they are byte-identical on ``origin/legacy-mill-lane`` tip. Loop and plant-gen
scripts are pinned so later PRs can bind them without vendoring publishers.
"""

from __future__ import annotations

from dataclasses import dataclass

from .vocabulary import KIND_GEN, KIND_LOOP, KIND_PAIRS


@dataclass(frozen=True)
class MillSource:
    mill_id: str
    path: str
    blob_sha: str
    kind: str
    companion_mill_path: str | None = None


MILL_SOURCES: tuple[MillSource, ...] = (
    MillSource(
        "iac-loop-r609",
        "experiments/iac-loop-r609.py",
        "e43e32f0366c786c5e8934229c052e317c03bc79",
        KIND_LOOP,
        "experiments/iac-mill-r609.py",
    ),
    MillSource(
        "iac-loop-r659",
        "experiments/iac-loop-r659.py",
        "4e374c91e846b29350494cb38cf62e4128c41598",
        KIND_LOOP,
        # Filename is historical; the script loads the r683 mill.
        "experiments/iac-mill-r683.py",
    ),
    MillSource(
        "iac-loop-r709",
        "experiments/iac-loop-r709.py",
        "bd0d5a5cf24165f455b747f9422af883c9a3bafc",
        KIND_LOOP,
        "experiments/iac-mill-r709.py",
    ),
    MillSource(
        "iac-loop-r777",
        "experiments/iac-loop-r777.py",
        "a17ba04998571f2dfc5942f6523ec0de56234207",
        KIND_LOOP,
        # Filename is historical; the script loads the r1514 mill.
        "experiments/iac-mill-r1514.py",
    ),
    MillSource(
        "iac-loop-r1132",
        "experiments/iac-loop-r1132.py",
        "a17ba04998571f2dfc5942f6523ec0de56234207",
        KIND_LOOP,
        "experiments/iac-mill-r1514.py",
    ),
    MillSource(
        "iac-loop-r1514",
        "experiments/iac-loop-r1514.py",
        "9375cc69666dc5eaa0b6686c8f0a37cc8304d4b7",
        KIND_LOOP,
        "experiments/iac-mill-r1514.py",
    ),
    MillSource(
        "_gen_iac_plants_r1132",
        "experiments/_gen_iac_plants_r1132.py",
        "d2f4b1f0da3712f45113036bccedb61d3362bb08",
        KIND_GEN,
        "experiments/iac-mill-r1132.py",
    ),
    MillSource(
        "_gen_iac_append_r1514",
        "experiments/_gen_iac_append_r1514.py",
        "388663537d3eb000eb12d164558bd7d8fb3f4fee",
        KIND_GEN,
        "experiments/iac-mill-r1514.py",
    ),
    MillSource(
        "iac-mill-r609",
        "experiments/iac-mill-r609.py",
        "c3f9db2b8047fde0ae8a5b839da89f1ace51c51a",
        KIND_PAIRS,
    ),
    MillSource(
        "iac-mill-r659",
        "experiments/iac-mill-r659.py",
        "af3baadfebf0b7cacdd8fe4d750da1e28dcec99f",
        KIND_PAIRS,
    ),
    MillSource(
        "iac-mill-r683",
        "experiments/iac-mill-r683.py",
        "aaceec5c235f462b3978bacfb27140c3da1909cf",
        KIND_PAIRS,
    ),
    MillSource(
        "iac-mill-r709",
        "experiments/iac-mill-r709.py",
        "1d93db28f222562e85aab5caada4238f7a3af63a",
        KIND_PAIRS,
    ),
    MillSource(
        "iac-mill-r777",
        "experiments/iac-mill-r777.py",
        "0cb6d90e80e44df952cab590e6440821c44a3f2d",
        KIND_PAIRS,
    ),
    MillSource(
        "iac-mill-r1132",
        "experiments/iac-mill-r1132.py",
        "9bbf8390a1581b6ec14e38acc641883a5127aec1",
        KIND_PAIRS,
    ),
    MillSource(
        "iac-mill-r1514",
        "experiments/iac-mill-r1514.py",
        "9efee7a5778e84a2174131a0f166a1cd67f4acfe",
        KIND_PAIRS,
    ),
)


def catalog_sources() -> tuple[MillSource, ...]:
    return tuple(source for source in MILL_SOURCES if source.kind == KIND_PAIRS)


def loop_sources() -> tuple[MillSource, ...]:
    return tuple(source for source in MILL_SOURCES if source.kind == KIND_LOOP)


def gen_sources() -> tuple[MillSource, ...]:
    return tuple(source for source in MILL_SOURCES if source.kind == KIND_GEN)


def source_by_id(mill_id: str) -> MillSource:
    for source in MILL_SOURCES:
        if source.mill_id == mill_id:
            return source
    raise KeyError(f"unknown iac mill source {mill_id!r}")
