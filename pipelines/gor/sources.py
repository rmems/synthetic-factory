#!/usr/bin/env python3
"""Pinned inventory of the 33 GOR scripts on ``legacy-mill-lane``.

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
        "gor-loop-r946",
        "experiments/gor-loop-r946.py",
        "a9242bce20eebcc9b557e8a8ed526eaf4cd2336a",
        KIND_LOOP,
        "experiments/gor-mill-r946.py",
    ),
    MillSource(
        "gor-loop-r973",
        "experiments/gor-loop-r973.py",
        "2694c267e147a93a946c94e899f9c545831f907c",
        KIND_LOOP,
        "experiments/gor-mill-r973.py",
    ),
    MillSource(
        "gor-loop-r1003",
        "experiments/gor-loop-r1003.py",
        "a64656aeb220c64bdd111e9605aa322379ad10ad",
        KIND_LOOP,
        "experiments/gor-mill-r1003.py",
    ),
    MillSource(
        "gor-loop-r1044",
        "experiments/gor-loop-r1044.py",
        "61c1e5c7e01cacd0f632e5ab9a91aa4ec74ba9c7",
        KIND_LOOP,
        "experiments/gor-mill-r1044.py",
    ),
    MillSource(
        "gor-loop-r1046",
        "experiments/gor-loop-r1046.py",
        "741f08cdf3c35c7e5c839231596c445038725d47",
        KIND_LOOP,
        "experiments/gor-mill-r1046.py",
    ),
    MillSource(
        "gor-loop-r1111",
        "experiments/gor-loop-r1111.py",
        "065dcebeebdfb543ea394be80a53a4073b564299",
        KIND_LOOP,
        "experiments/gor-mill-r1111.py",
    ),
    MillSource(
        "gor-loop-r1127",
        "experiments/gor-loop-r1127.py",
        "bffbf5fb0aeaee56d60f26aec9839f4150d88109",
        KIND_LOOP,
        "experiments/gor-mill-r1127.py",
    ),
    MillSource(
        "gor-loop-r1196",
        "experiments/gor-loop-r1196.py",
        "53fc30fe70eba9572ccf986e9da1635c09e612e8",
        KIND_LOOP,
        # Filename is historical; the script loads the r1214 mill.
        "experiments/gor-mill-r1214.py",
    ),
    MillSource(
        "gor-loop-r1278",
        "experiments/gor-loop-r1278.py",
        "6a5c3d55e08a0b30a1ee255e2d0ddf7ae0142eb0",
        KIND_LOOP,
        "experiments/gor-mill-r1278.py",
    ),
    MillSource(
        "gor-loop-r1371",
        "experiments/gor-loop-r1371.py",
        "795f8ec56e9862537c97579d67397ccbe10661c1",
        KIND_LOOP,
        "experiments/gor-mill-r1371.py",
    ),
    MillSource(
        "gor-loop-r1405",
        "experiments/gor-loop-r1405.py",
        "f6dfafbe002233f33a794f916c2e9ed5a686b921",
        KIND_LOOP,
        "experiments/gor-mill-r1405.py",
    ),
    MillSource(
        "gor-loop-r1417",
        "experiments/gor-loop-r1417.py",
        "8acecd2162b091783cf6911a7414d3fadd348f8e",
        KIND_LOOP,
        "experiments/gor-mill-r1417.py",
    ),
    MillSource(
        "gor-loop-r1460",
        "experiments/gor-loop-r1460.py",
        "a125cda28c435a3a4ad7f4c8b35084d986a98e7f",
        KIND_LOOP,
        "experiments/gor-mill-r1460.py",
    ),
    MillSource(
        "_gen_gor_plants_r1725",
        "experiments/_gen_gor_plants_r1725.py",
        "f90a1163419aa307a3bfe072bcfec53a58461965",
        KIND_GEN,
        "experiments/gor-mill-r1460.py",
    ),
    MillSource(
        "_gen_gor_plants_w10",
        "experiments/_gen_gor_plants_w10.py",
        "8cd9a2d5adeea8679e20f22536008dfe96877e47",
        KIND_GEN,
        "experiments/gor-mill-r1460.py",
    ),
    MillSource(
        "_gen_gor_plants_w11",
        "experiments/_gen_gor_plants_w11.py",
        "12b4532077451c184fda70ff5a87991e1777c88d",
        KIND_GEN,
        "experiments/gor-mill-r1460.py",
    ),
    MillSource(
        "_gen_gor_plants_w12",
        "experiments/_gen_gor_plants_w12.py",
        "a0fa8c1bb5ee5da78a86e613f78774af3435251a",
        KIND_GEN,
        "experiments/gor-mill-r1460.py",
    ),
    MillSource(
        "gor-mill-r946",
        "experiments/gor-mill-r946.py",
        "603a68437986df9dfea02bde2921902dd188e371",
        KIND_PAIRS,
    ),
    MillSource(
        "gor-mill-r973",
        "experiments/gor-mill-r973.py",
        "e148808103bf2676ac7bd4748914868b6a348705",
        KIND_PAIRS,
    ),
    MillSource(
        "gor-mill-r1003",
        "experiments/gor-mill-r1003.py",
        "4943041583ef3f85064635b426203e2e1925fa46",
        KIND_PAIRS,
    ),
    MillSource(
        "gor-mill-r1044",
        "experiments/gor-mill-r1044.py",
        "d6b4c87661f68d2f1c0e3885cf23df00ed993f7f",
        KIND_PAIRS,
    ),
    MillSource(
        "gor-mill-r1046",
        "experiments/gor-mill-r1046.py",
        "dba142fd64f557c997fb11f7a3213aa4ea91a95c",
        KIND_PAIRS,
    ),
    MillSource(
        "gor-mill-r1111",
        "experiments/gor-mill-r1111.py",
        "6d95ccea46e868dbcc142c7295911e48368c2386",
        KIND_PAIRS,
    ),
    MillSource(
        "gor-mill-r1127",
        "experiments/gor-mill-r1127.py",
        "aaafe3b6d68acb540db50c93b4873062bc58ecb7",
        KIND_PAIRS,
    ),
    MillSource(
        "gor-mill-r1131",
        "experiments/gor-mill-r1131.py",
        "343053c44ec2801c68ecd34bfd743dee9a5c6b17",
        KIND_PAIRS,
    ),
    MillSource(
        "gor-mill-r1196",
        "experiments/gor-mill-r1196.py",
        "a608c0452d88ddb5124159b3c1d31c44a6b0d5d0",
        KIND_PAIRS,
    ),
    MillSource(
        "gor-mill-r1214",
        "experiments/gor-mill-r1214.py",
        "e2bad248487ffcb5ec7dc9cf7420003c516da111",
        KIND_PAIRS,
    ),
    MillSource(
        "gor-mill-r1230",
        "experiments/gor-mill-r1230.py",
        "cba6d6a8638d15409110ee4f88d973218c9a7aae",
        KIND_PAIRS,
    ),
    MillSource(
        "gor-mill-r1278",
        "experiments/gor-mill-r1278.py",
        "7351ca16184e4de9a5c26c02c8b074fba229f943",
        KIND_PAIRS,
    ),
    MillSource(
        "gor-mill-r1371",
        "experiments/gor-mill-r1371.py",
        "5880de0e4547fdc52bac2a0dc692371151e06d8b",
        KIND_PAIRS,
    ),
    MillSource(
        "gor-mill-r1405",
        "experiments/gor-mill-r1405.py",
        "6ffc1127d079a86606e25d492731f023c8c378a1",
        KIND_PAIRS,
    ),
    MillSource(
        "gor-mill-r1417",
        "experiments/gor-mill-r1417.py",
        "193cad92b76f4fc0093ccc2ad1d8dbab04723ccc",
        KIND_PAIRS,
    ),
    MillSource(
        "gor-mill-r1460",
        "experiments/gor-mill-r1460.py",
        "a38ad92340a902e8a5365976f27963c2d61c401b",
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
    raise KeyError(f"unknown gor mill source {mill_id!r}")
