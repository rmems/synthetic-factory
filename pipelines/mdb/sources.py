#!/usr/bin/env python3
"""Pinned inventory of the 41 MDB scripts on ``legacy-mill-lane``.

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
        "mdb-hop-loop",
        "experiments/mdb-hop-loop.py",
        "08698c83216f39ef35258e41a13a5840d1891fc4",
        KIND_LOOP,
        "experiments/mdb-mill-r840.py",
    ),
    MillSource(
        "mdb-loop-r1068",
        "experiments/mdb-loop-r1068.py",
        "4888c1dd4768a6bc8ef90ebfbd791028761ae963",
        KIND_LOOP,
        "experiments/mdb-mill-r1068.py",
    ),
    MillSource(
        "mdb-loop-r1084",
        "experiments/mdb-loop-r1084.py",
        "0138549b23e1e1db53de8114c8355303172c2166",
        KIND_LOOP,
        # Filename is historical; the script loads the r1148 mill.
        "experiments/mdb-mill-r1148.py",
    ),
    MillSource(
        "mdb-loop-r1208",
        "experiments/mdb-loop-r1208.py",
        "eb8dd5b51d1ad94a14f31ef398333b4d03b247a0",
        KIND_LOOP,
        "experiments/mdb-mill-r1208.py",
    ),
    MillSource(
        "mdb-loop-r1351",
        "experiments/mdb-loop-r1351.py",
        "cf4383b1e59e1c48a913f61a58c6e3dd11ae92a0",
        KIND_LOOP,
        "experiments/mdb-mill-r1351.py",
    ),
    MillSource(
        "mdb-loop-r1407",
        "experiments/mdb-loop-r1407.py",
        "23f63b25bb0f3e8dfd10cfeda2386d6a7edaa60f",
        KIND_LOOP,
        "experiments/mdb-mill-r1407.py",
    ),
    MillSource(
        "mdb-loop-r1454",
        "experiments/mdb-loop-r1454.py",
        "1cc9e1d4c6e78aca89381b0719a4084c12db6fe7",
        KIND_LOOP,
        "experiments/mdb-mill-r1454.py",
    ),
    MillSource(
        "mdb-loop-r1534",
        "experiments/mdb-loop-r1534.py",
        "0409914c9bb6250ba7df09f4cfe070b0bac3647a",
        KIND_LOOP,
        "experiments/mdb-mill-r1534.py",
    ),
    MillSource(
        "mdb-loop-r1614",
        "experiments/mdb-loop-r1614.py",
        "9a83c37ee861c9960fb4a2440c17d87e2d0f9d9d",
        KIND_LOOP,
        "experiments/mdb-mill-r1614.py",
    ),
    MillSource(
        "mdb-loop-r1694",
        "experiments/mdb-loop-r1694.py",
        "02d7191bf1d9a860e9157be14faf04abcee26221",
        KIND_LOOP,
        "experiments/mdb-mill-r1694.py",
    ),
    MillSource(
        "mdb-loop-r1774",
        "experiments/mdb-loop-r1774.py",
        "3f79fe26db7441e5f3e370ab81ada5e5db9ebe23",
        KIND_LOOP,
        "experiments/mdb-mill-r1774.py",
    ),
    MillSource(
        "mdb-loop-r1854",
        "experiments/mdb-loop-r1854.py",
        "3638d81142f86d13e3b515a39f0d0b86d107240f",
        KIND_LOOP,
        "experiments/mdb-mill-r1854.py",
    ),
    MillSource(
        "mdb-loop-r1934",
        "experiments/mdb-loop-r1934.py",
        "cdbb27df7176cb42375a410922f2680b86218287",
        KIND_LOOP,
        "experiments/mdb-mill-r1934.py",
    ),
    MillSource(
        "mdb-loop-r709",
        "experiments/mdb-loop-r709.py",
        "655557e5f68ca8f6421afa0046652766dda25e91",
        KIND_LOOP,
        "experiments/mdb-mill-r709.py",
    ),
    MillSource(
        "mdb-loop-r746",
        "experiments/mdb-loop-r746.py",
        "44935097bc8cb4d0c3987902062cdddb4e372ffb",
        KIND_LOOP,
        "experiments/mdb-mill-r746.py",
    ),
    MillSource(
        "mdb-loop-r762",
        "experiments/mdb-loop-r762.py",
        "b4750e937cd8e48358a31e3bd7b84eb996083f11",
        KIND_LOOP,
        "experiments/mdb-mill-r762.py",
    ),
    MillSource(
        "mdb-loop-r776",
        "experiments/mdb-loop-r776.py",
        "2d5730f03f20d02703c1e8c9ac7292415e41d036",
        KIND_LOOP,
        # Filename is historical; the script loads the r840 mill.
        "experiments/mdb-mill-r840.py",
    ),
    MillSource(
        "mdb-loop-r840-race",
        "experiments/mdb-loop-r840-race.py",
        "21142045874c8b46c0d53aa18d796f858240786d",
        KIND_LOOP,
        "experiments/mdb-mill-r840.py",
    ),
    MillSource(
        "mdb-loop-r918",
        "experiments/mdb-loop-r918.py",
        "27e254d9186271ee8030a3d8f58f088b3d5bd788",
        KIND_LOOP,
        "experiments/mdb-mill-r918.py",
    ),
    MillSource(
        "mdb-loop-r961",
        "experiments/mdb-loop-r961.py",
        "75f46e1d68c12e5d3ae21a4cb78b7c32465124a2",
        KIND_LOOP,
        "experiments/mdb-mill-r961.py",
    ),
    MillSource(
        "_gen_mdb_r1208",
        "experiments/_gen_mdb_r1208.py",
        "4f470715b2c569d8d3dc11de87e20e865a210897",
        KIND_GEN,
        "experiments/mdb-mill-r1208.py",
    ),
    MillSource(
        "mdb-mill-r709",
        "experiments/mdb-mill-r709.py",
        "a752758de25114250ffe8b578065edd8b37da800",
        KIND_PAIRS,
    ),
    MillSource(
        "mdb-mill-r746",
        "experiments/mdb-mill-r746.py",
        "25604a3edf00b76d8918a58b3c524296222f5f09",
        KIND_PAIRS,
    ),
    MillSource(
        "mdb-mill-r762",
        "experiments/mdb-mill-r762.py",
        "07ddb4bc60a11143033176e29da80911ba6d2ccc",
        KIND_PAIRS,
    ),
    MillSource(
        "mdb-mill-r776",
        "experiments/mdb-mill-r776.py",
        "99603c7b2ccc63099727190526dc919fbd950ba1",
        KIND_PAIRS,
    ),
    MillSource(
        "mdb-mill-r840",
        "experiments/mdb-mill-r840.py",
        "68a827f955c0905e2022c8c090fd5381c1eb24e4",
        KIND_PAIRS,
    ),
    MillSource(
        "mdb-mill-r918",
        "experiments/mdb-mill-r918.py",
        "c092461609e365ac88e27bc202aee2e00286897f",
        KIND_PAIRS,
    ),
    MillSource(
        "mdb-mill-r961",
        "experiments/mdb-mill-r961.py",
        "55c1a48a33b6f157b19f63604096f1a936d332bc",
        KIND_PAIRS,
    ),
    MillSource(
        "mdb-mill-r1068",
        "experiments/mdb-mill-r1068.py",
        "63f128c09dd1f40f528358a7e38a7a1ff86bfac7",
        KIND_PAIRS,
    ),
    MillSource(
        "mdb-mill-r1084",
        "experiments/mdb-mill-r1084.py",
        "abad43532355ada251a029653b07efd45db19f6e",
        KIND_PAIRS,
    ),
    MillSource(
        "mdb-mill-r1148",
        "experiments/mdb-mill-r1148.py",
        "43650553ee597c65abcc0db3859395299691f51a",
        KIND_PAIRS,
    ),
    MillSource(
        "mdb-mill-r1208",
        "experiments/mdb-mill-r1208.py",
        "59dd2fad3150a6d99d3913dcfbb1ff0308be7f6a",
        KIND_PAIRS,
    ),
    MillSource(
        "mdb-mill-r1351",
        "experiments/mdb-mill-r1351.py",
        "2bf9037485ff40bf7574f6e8949612c90ee2babc",
        KIND_PAIRS,
    ),
    MillSource(
        "mdb-mill-r1407",
        "experiments/mdb-mill-r1407.py",
        "80a51e96193385c9e38862a599f3615e98e2a505",
        KIND_PAIRS,
    ),
    MillSource(
        "mdb-mill-r1454",
        "experiments/mdb-mill-r1454.py",
        "1e0a4c30ce935aa4b640cdde2e00dd90eefe129a",
        KIND_PAIRS,
    ),
    MillSource(
        "mdb-mill-r1534",
        "experiments/mdb-mill-r1534.py",
        "62a66e45f193becf0b239d1625ce060c1d5243a8",
        KIND_PAIRS,
    ),
    MillSource(
        "mdb-mill-r1614",
        "experiments/mdb-mill-r1614.py",
        "44e43b88724f99dd439c16e23cbebbb3ab3044c3",
        KIND_PAIRS,
    ),
    MillSource(
        "mdb-mill-r1694",
        "experiments/mdb-mill-r1694.py",
        "2fb658e531d084c9ca6f81d290a8df5039e21653",
        KIND_PAIRS,
    ),
    MillSource(
        "mdb-mill-r1774",
        "experiments/mdb-mill-r1774.py",
        "35398a3ac62c2a5195d7a27b00da5cb25691e8a4",
        KIND_PAIRS,
    ),
    MillSource(
        "mdb-mill-r1854",
        "experiments/mdb-mill-r1854.py",
        "b89c27da7078574ec7cb6d34abfe95e3f42bfde4",
        KIND_PAIRS,
    ),
    MillSource(
        "mdb-mill-r1934",
        "experiments/mdb-mill-r1934.py",
        "896cd06aaebaed6217a40c50c0f53f29cfbb7075",
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
    raise KeyError(f"unknown mdb mill source {mill_id!r}")
