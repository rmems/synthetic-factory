#!/usr/bin/env python3
"""Pinned inventory of the nine EVH scripts on ``legacy-mill-lane``.

Blob SHAs are the preserve-commit objects (``vocabulary.PRESERVE_COMMIT``);
they are byte-identical on ``origin/legacy-mill-lane`` tip. Plant-gens and
the leftover loop are pinned so later PRs can bind them without vendoring
``scripts/eval_harness_unique_mill``.
"""

from __future__ import annotations

from dataclasses import dataclass

from .vocabulary import KIND_GEN, KIND_LOOP, MILL_DIR


@dataclass(frozen=True)
class MillSource:
    mill_id: str
    path: str
    blob_sha: str
    kind: str
    companion_mill_path: str | None = None


MILL_SOURCES: tuple[MillSource, ...] = (
    MillSource(
        "_gen_evh_plants_r801",
        "experiments/_gen_evh_plants_r801.py",
        "35b6a247fa9fbc012a75ed5fb8a4120b147121bd",
        KIND_GEN,
        MILL_DIR,
    ),
    MillSource(
        "_gen_evh_plants_r927",
        "experiments/_gen_evh_plants_r927.py",
        "75fb3c4b81b64f6e82c3e96db949ae030bd66a9e",
        KIND_GEN,
        MILL_DIR,
    ),
    MillSource(
        "_gen_evh_plants_r1161",
        "experiments/_gen_evh_plants_r1161.py",
        "09b452a36a6f4f582eab882cac4198ffa5df7a6b",
        KIND_GEN,
        MILL_DIR,
    ),
    MillSource(
        "_gen_evh_plants_r1357",
        "experiments/_gen_evh_plants_r1357.py",
        "59ba7f046fbf2c183abf34f0d4803ef3e8ca94c2",
        KIND_GEN,
        MILL_DIR,
    ),
    MillSource(
        "_gen_evh_plants_r1708",
        "experiments/_gen_evh_plants_r1708.py",
        "4124bbeb289f71fe789609a43e82a78e49bd192e",
        KIND_GEN,
        MILL_DIR,
    ),
    MillSource(
        "_gen_evh_plants_r2059",
        "experiments/_gen_evh_plants_r2059.py",
        "25a29ce2ac46a49b30df37d27dc427e2a77a1896",
        KIND_GEN,
        MILL_DIR,
    ),
    MillSource(
        "_gen_evh_plants_r2410",
        "experiments/_gen_evh_plants_r2410.py",
        "1aa03af210b47a8a8cd55b7d471e7b0ef97c942c",
        KIND_GEN,
        MILL_DIR,
    ),
    MillSource(
        "_gen_evh_plants_r2761",
        "experiments/_gen_evh_plants_r2761.py",
        "70bfcd9330343aaec8c36120450ad644bd2050dc",
        KIND_GEN,
        MILL_DIR,
    ),
    MillSource(
        "evh-loop-r2761",
        "experiments/evh-loop-r2761.py",
        "17a3ee968675dd5def9f3dbe3e79be7e152055f6",
        KIND_LOOP,
        MILL_DIR,
    ),
)


def catalog_sources() -> tuple[MillSource, ...]:
    return tuple(source for source in MILL_SOURCES if source.kind == KIND_GEN)


def loop_sources() -> tuple[MillSource, ...]:
    return tuple(source for source in MILL_SOURCES if source.kind == KIND_LOOP)


def source_by_id(mill_id: str) -> MillSource:
    for source in MILL_SOURCES:
        if source.mill_id == mill_id:
            return source
    raise KeyError(f"unknown evh mill source {mill_id!r}")
