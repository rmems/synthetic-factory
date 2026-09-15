#!/usr/bin/env python3
"""Pinned inventory of the 23 AMC scripts on ``legacy-mill-lane``.

Blob SHAs are the preserve-commit objects (``vocabulary.PRESERVE_COMMIT``);
they are byte-identical on ``origin/legacy-mill-lane`` tip. Loop scripts are
pinned here so later PRs can bind them without vendoring mill publishers.
"""

from __future__ import annotations

from dataclasses import dataclass

from .vocabulary import KIND_LEFTOVER, KIND_LOOP, KIND_PAIRS


@dataclass(frozen=True)
class MillSource:
    mill_id: str
    path: str
    blob_sha: str
    kind: str
    companion_mill_path: str | None = None


MILL_SOURCES: tuple[MillSource, ...] = (
    MillSource(
        "amc-loop-r170",
        "experiments/amc-loop-r170.py",
        "784a9dd009cafdbe939c9bd6e5d25cabb5c1fed2",
        KIND_LOOP,
        "experiments/amc-mill-r170.py",
    ),
    MillSource(
        "amc-loop-r229",
        "experiments/amc-loop-r229.py",
        "b936bc089cfea6036a14b8991011f40676704c18",
        KIND_LOOP,
        "experiments/amc-mill-r229.py",
    ),
    MillSource(
        "amc-loop-r280",
        "experiments/amc-loop-r280.py",
        "5bb02eaaf8c5d37e336a003d7284a181f4fe3a8a",
        KIND_LOOP,
        "experiments/amc-mill-r280.py",
    ),
    MillSource(
        "amc-loop-r316",
        "experiments/amc-loop-r316.py",
        "562e773b6683a4d5c20573f33e9bb500fe9dcd60",
        KIND_LOOP,
        "experiments/amc-mill-r316.py",
    ),
    MillSource(
        "amc-loop-r352",
        "experiments/amc-loop-r352.py",
        "54633d91f2e48d14990b4e37921d096127553cc9",
        KIND_LOOP,
        "experiments/amc-mill-r352.py",
    ),
    MillSource(
        "amc-loop-r424",
        "experiments/amc-loop-r424.py",
        "05653a2a88daa8f7dbff9839940556c7dc748067",
        KIND_LOOP,
        "experiments/amc-mill-r424.py",
    ),
    MillSource(
        "amc-loop-r592",
        "experiments/amc-loop-r592.py",
        "010667e4669569c4bbc972543e28eda9080b6a3d",
        KIND_LOOP,
        "experiments/amc-mill-r592.py",
    ),
    MillSource(
        "amc-loop-r608",
        "experiments/amc-loop-r608.py",
        "11ea36c9787f0eafe4869679fb3a23188c6e6408",
        KIND_LOOP,
        "experiments/amc-mill-r608.py",
    ),
    MillSource(
        "amc-loop-r650",
        "experiments/amc-loop-r650.py",
        "22ca9d59ebd58b21e94eecdaf56a497632234501",
        KIND_LOOP,
        "experiments/amc-mill-r650.py",
    ),
    MillSource(
        "amc-loop-r688",
        "experiments/amc-loop-r688.py",
        "3fb08af739e92ea497b8316dfaa2f9d7467bf306",
        KIND_LOOP,
        "experiments/amc-mill-r688.py",
    ),
    MillSource(
        "amc-loop-r704",
        "experiments/amc-loop-r704.py",
        "2aeca6d83001d0f466568ca8e35fdab54c704716",
        KIND_LOOP,
        "experiments/amc-mill-r704.py",
    ),
    MillSource(
        "amc-mill-r170",
        "experiments/amc-mill-r170.py",
        "aa251ffc322df4f8c62141adc32d7db42d3be5e7",
        KIND_PAIRS,
    ),
    MillSource(
        "amc-mill-r229",
        "experiments/amc-mill-r229.py",
        "0a4de1557fd1d0da1f3a27d9170af461f372483b",
        KIND_PAIRS,
    ),
    MillSource(
        "amc-mill-r280",
        "experiments/amc-mill-r280.py",
        "52d8d05b79c4ede9f990631fc55bfee9e8eccc0d",
        KIND_PAIRS,
    ),
    MillSource(
        "amc-mill-r316",
        "experiments/amc-mill-r316.py",
        "0fd0228c9653aab8b6e47e90e85567c2b4e606d8",
        KIND_PAIRS,
    ),
    MillSource(
        "amc-mill-r352",
        "experiments/amc-mill-r352.py",
        "209976e370396858316f3473ed1f858067e755f1",
        KIND_PAIRS,
    ),
    MillSource(
        "amc-mill-r424",
        "experiments/amc-mill-r424.py",
        "b11c814e837860820356f6c2ce8f76ae1e3b2e3e",
        KIND_PAIRS,
    ),
    MillSource(
        "amc-mill-r592",
        "experiments/amc-mill-r592.py",
        "8340770e13151047bfabdf2d5b19ddd24816b22f",
        KIND_PAIRS,
    ),
    MillSource(
        "amc-mill-r608",
        "experiments/amc-mill-r608.py",
        "bd6e9d4899ac92c44cb030154eafa036b36d1932",
        KIND_PAIRS,
    ),
    MillSource(
        "amc-mill-r650",
        "experiments/amc-mill-r650.py",
        "4998009758bd32e4cc1b7b980faa0047f570cfee",
        KIND_PAIRS,
    ),
    MillSource(
        "amc-mill-r688",
        "experiments/amc-mill-r688.py",
        "a278d6c60b174301229ca48f9295893065ffc34b",
        KIND_PAIRS,
    ),
    MillSource(
        "amc-mill-r704",
        "experiments/amc-mill-r704.py",
        "3e8a36e36f0666ca899119a84cdbcd0b1ce8af1d",
        KIND_PAIRS,
    ),
    MillSource(
        "mill_amc_leftover_r688",
        "experiments/mill_amc_leftover_r688.py",
        "96f1d03b9eff8bfcaeea4d16b44ed7f641ed58f8",
        KIND_LEFTOVER,
    ),
)


def catalog_sources() -> tuple[MillSource, ...]:
    return tuple(source for source in MILL_SOURCES if source.kind != KIND_LOOP)


def loop_sources() -> tuple[MillSource, ...]:
    return tuple(source for source in MILL_SOURCES if source.kind == KIND_LOOP)


def source_by_id(mill_id: str) -> MillSource:
    for source in MILL_SOURCES:
        if source.mill_id == mill_id:
            return source
    raise KeyError(f"unknown amc mill source {mill_id!r}")
