#!/usr/bin/env python3
"""Pinned inventory of the 7 leftover scripts on ``legacy-mill-lane``.

Blob SHAs are the preserve-commit objects (``vocabulary.PRESERVE_COMMIT``);
they are byte-identical on ``origin/legacy-mill-lane`` tip. Loop scripts and
the used-slug listing are pinned so later PRs can bind them without
vendoring publishers.
"""

from __future__ import annotations

from dataclasses import dataclass

from .vocabulary import KIND_LOOP, KIND_SLUGS, KIND_STEMS, KIND_TABLES


@dataclass(frozen=True)
class MillSource:
    mill_id: str
    path: str
    blob_sha: str
    kind: str
    companion_mill_path: str | None = None


MILL_SOURCES: tuple[MillSource, ...] = (
    MillSource(
        "lef-loop-r629",
        "experiments/lef-loop-r629.py",
        "9382db9c6d91f8348daf351877738adb5ac7b3b5",
        KIND_LOOP,
        "experiments/lef-mill-r629.py",
    ),
    MillSource(
        "lef-loop-r728",
        "experiments/lef-loop-r728.py",
        "94fadd880eb1ede67e55c12188d3e3a80ff81c48",
        KIND_LOOP,
        "experiments/lef-mill-r728.py",
    ),
    MillSource(
        "lef-loop-r968",
        "experiments/lef-loop-r968.py",
        "127446e5d9227d3da053a767db602e12bb914a6b",
        KIND_LOOP,
        "experiments/lef-mill-r968.py",
    ),
    MillSource(
        "lef-mill-r629",
        "experiments/lef-mill-r629.py",
        "c469901aabd9c590c4e70ed15938973c1320c17d",
        KIND_TABLES,
    ),
    MillSource(
        "lef-mill-r728",
        "experiments/lef-mill-r728.py",
        "b8afb84386270b05c39d756fb6ac1ca48107faf1",
        KIND_TABLES,
    ),
    MillSource(
        "lef-mill-r968",
        "experiments/lef-mill-r968.py",
        "f08cb67f66a999d027730ad0587d08cea0943923",
        KIND_STEMS,
    ),
    MillSource(
        "lef-used-slugs",
        "experiments/.lef-used-slugs.txt",
        "f1fb1b7ce112f2ff997c7bc3c03b5dd35798bf5f",
        KIND_SLUGS,
    ),
)


def catalog_sources() -> tuple[MillSource, ...]:
    return tuple(
        source
        for source in MILL_SOURCES
        if source.kind in {KIND_TABLES, KIND_STEMS}
    )


def loop_sources() -> tuple[MillSource, ...]:
    return tuple(source for source in MILL_SOURCES if source.kind == KIND_LOOP)


def slug_sources() -> tuple[MillSource, ...]:
    return tuple(source for source in MILL_SOURCES if source.kind == KIND_SLUGS)


def source_by_id(mill_id: str) -> MillSource:
    for source in MILL_SOURCES:
        if source.mill_id == mill_id:
            return source
    raise KeyError(f"unknown leftover mill source {mill_id!r}")
