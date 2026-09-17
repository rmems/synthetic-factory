#!/usr/bin/env python3
"""Pinned inventory of the 21 CST scripts on ``legacy-mill-lane``.

Blob SHAs are the preserve-commit objects (``vocabulary.PRESERVE_COMMIT``);
they are byte-identical on ``origin/legacy-mill-lane`` tip. Loop scripts are
pinned here so later PRs can bind them without vendoring mill publishers.
"""

from __future__ import annotations

from dataclasses import dataclass

from .catalog_extract import KIND_LOOP, KIND_PAIRS, KIND_PLANTS


@dataclass(frozen=True)
class MillSource:
    mill_id: str
    path: str
    blob_sha: str
    kind: str
    companion_mill_path: str | None = None


MILL_SOURCES: tuple[MillSource, ...] = (
    MillSource(
        "cst-loop-r1414",
        "experiments/cst-loop-r1414.py",
        "211a32d2224c2f9e10ab7ddd2c8e1fbde8e5fc93",
        KIND_LOOP,
        "experiments/cst-mill-r1414.py",
    ),
    MillSource(
        "cst-loop-r1446",
        "experiments/cst-loop-r1446.py",
        "f9aec7deea4b7076ebf5e37311a6cb0683b42f75",
        KIND_LOOP,
        # Filename is historical; the script loads the r2310 mill.
        "experiments/cst-mill-r2310.py",
    ),
    MillSource(
        "cst-mill-r1414",
        "experiments/cst-mill-r1414.py",
        "56b1eafd5a9b430fc41d9d94c46f99dede1f471c",
        KIND_PAIRS,
    ),
    MillSource(
        "cst-mill-r1446",
        "experiments/cst-mill-r1446.py",
        "a8cda5b3ccdff2cbd43610e16b7a48e250fd5493",
        KIND_PAIRS,
    ),
    MillSource(
        "cst-mill-r1491",
        "experiments/cst-mill-r1491.py",
        "a151514fc7bfbefa8500fa7f1b2d49f6d3a04635",
        KIND_PAIRS,
    ),
    MillSource(
        "cst-mill-r1531",
        "experiments/cst-mill-r1531.py",
        "aacc15b45edbab10f68ceffe08f124b5bf63a124",
        KIND_PAIRS,
    ),
    MillSource(
        "cst-mill-r1571",
        "experiments/cst-mill-r1571.py",
        "cccb32c55d63e0c228fd07fe1c1cd856c7835378",
        KIND_PAIRS,
    ),
    MillSource(
        "cst-mill-r1611",
        "experiments/cst-mill-r1611.py",
        "36f1e116a225fa4a71d813b6a7306939e8a400da",
        KIND_PAIRS,
    ),
    MillSource(
        "cst-mill-r1651",
        "experiments/cst-mill-r1651.py",
        "09cf08ee3cb0ca25f6f2be6d3ec6e94a92595edc",
        KIND_PAIRS,
    ),
    MillSource(
        "cst-mill-r1691",
        "experiments/cst-mill-r1691.py",
        "b955d2fb6180a08ff170475694ceb12e77d3d3b8",
        KIND_PAIRS,
    ),
    MillSource(
        "cst-mill-r1731",
        "experiments/cst-mill-r1731.py",
        "ffc0923c8265de0c85420691dd03b34c3674ed10",
        KIND_PAIRS,
    ),
    MillSource(
        "cst-mill-r1837",
        "experiments/cst-mill-r1837.py",
        "204a35436fb2c8150bc2d434982bb34011832994",
        KIND_PAIRS,
    ),
    MillSource(
        "cst-mill-r1947",
        "experiments/cst-mill-r1947.py",
        "094043aa1dd83b5fdfb32fba941a09b6112bbfba",
        KIND_PAIRS,
    ),
    MillSource(
        "cst-mill-r2059",
        "experiments/cst-mill-r2059.py",
        "9377ed3811c11931955cb609164f8f39b5f8173b",
        KIND_PAIRS,
    ),
    MillSource(
        "cst-mill-r2144",
        "experiments/cst-mill-r2144.py",
        "9fe75fbf237f191afcdd7dd1208417f401507f5b",
        KIND_PAIRS,
    ),
    MillSource(
        "cst-mill-r2198",
        "experiments/cst-mill-r2198.py",
        "1a46e978354006f7a967878c2bcea25611ed988d",
        KIND_PAIRS,
    ),
    MillSource(
        "cst-mill-r2310",
        "experiments/cst-mill-r2310.py",
        "8080194057434c70a21f17bbfe0d20e3f714103f",
        KIND_PAIRS,
    ),
    MillSource(
        "cst-mill-r2430",
        "experiments/cst-mill-r2430.py",
        "a6bcf9b107ed496c510cc86c8c4571246e910265",
        KIND_PAIRS,
    ),
    MillSource(
        "cst_r1369_leftover_mill",
        "experiments/cst_r1369_leftover_mill.py",
        "ea88459dcb4d61dd3ccdd12dc3d33f5eb44a3721",
        KIND_PLANTS,
    ),
    MillSource(
        "cst_r1385_leftover3_mill",
        "experiments/cst_r1385_leftover3_mill.py",
        "148def8d9470bebf642de77e4dae5ddd423d6d63",
        KIND_PLANTS,
    ),
    MillSource(
        "cst_r1405_leftover3_mill",
        "experiments/cst_r1405_leftover3_mill.py",
        "fb66db251aa475488c483b54e4fc8ae3f9e656db",
        KIND_PLANTS,
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
    raise KeyError(f"unknown cst mill source {mill_id!r}")
