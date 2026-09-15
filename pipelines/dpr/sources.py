#!/usr/bin/env python3
"""Pinned inventory of DPR scripts on ``legacy-mill-lane``.

Blob SHAs are the preserve-commit objects (``vocabulary.PRESERVE_COMMIT``);
they are byte-identical on ``origin/legacy-mill-lane`` tip. Loop scripts and
lrd hoppers are pinned so later PRs can bind them without vendoring mill
publishers. Hoppers stay out of the catalog extract.
"""

from __future__ import annotations

from dataclasses import dataclass

from .vocabulary import KIND_GEN, KIND_HOPPER, KIND_LOOP, KIND_PAIRS, KIND_PLANTS


@dataclass(frozen=True)
class MillSource:
    mill_id: str
    path: str
    blob_sha: str
    kind: str
    companion_mill_path: str | None = None
    lrd_mill_path: str | None = None


MILL_SOURCES: tuple[MillSource, ...] = (
    MillSource(
        "mill_dpr_leftover_r2631",
        "experiments/mill_dpr_leftover_r2631.py",
        "e9d8a4fe09f49699c8738a7f8a010e034698245b",
        KIND_PLANTS,
    ),
    MillSource(
        "dpr-mill-leftover3-r2475",
        "experiments/dpr-mill-leftover3-r2475.py",
        "2a8145231ffc3003a627cdb6ffc6a91c1bd60c12",
        KIND_PAIRS,
    ),
    MillSource(
        "dpr-mill-r2631",
        "experiments/dpr-mill-r2631.py",
        "13ef732a2787082fc130f13c864cd19e1819fd4f",
        KIND_PAIRS,
    ),
    MillSource(
        "dpr-mill-r2758",
        "experiments/dpr-mill-r2758.py",
        "951d7f449750df1b8758cd5022396cc1fdc054ef",
        KIND_PAIRS,
    ),
    MillSource(
        "dpr-mill-r2811",
        "experiments/dpr-mill-r2811.py",
        "96a31dff68e72018fe798f8b9edec3b7aa94c947",
        KIND_PAIRS,
    ),
    MillSource(
        "dpr-mill-r2836",
        "experiments/dpr-mill-r2836.py",
        "e1b9d73999d145cade60ec1cda0f41f65ce6806e",
        KIND_PAIRS,
    ),
    MillSource(
        "dpr-mill-r3332",
        "experiments/dpr-mill-r3332.py",
        "0c288038d2a9bc6fb7f8b77af0cb77ed315ca971",
        KIND_PAIRS,
    ),
    MillSource(
        "dpr_mill_r2850",
        "experiments/dpr_mill_r2850.py",
        "a4fb2518a4ddfefb3e0c72c4de64222fd11b97cf",
        KIND_PAIRS,
    ),
    MillSource(
        "dpr_mill_r2865",
        "experiments/dpr_mill_r2865.py",
        "e3324011c61c85750bcae348d111255ffaf16013",
        KIND_PAIRS,
    ),
    MillSource(
        "dpr_mill_r2880",
        "experiments/dpr_mill_r2880.py",
        "80b501af844cf64930049b8ac16a7bb6f6da4f09",
        KIND_PAIRS,
    ),
    MillSource(
        "dpr_mill_r2959",
        "experiments/dpr_mill_r2959.py",
        "bfc9d7ab36c849d1de1e12a33f66b716f452daa0",
        KIND_PAIRS,
    ),
    MillSource(
        "dpr_mill_r3039",
        "experiments/dpr_mill_r3039.py",
        "d30bce1a0f0b1ef134962a7c17ad3643a3d0cb16",
        KIND_PAIRS,
    ),
    MillSource(
        "dpr_mill_r3119",
        "experiments/dpr_mill_r3119.py",
        "92d2ca1938b8fc8b09425f62b209ab669dba3657",
        KIND_PAIRS,
    ),
    MillSource(
        "dpr_mill_r3182",
        "experiments/dpr_mill_r3182.py",
        "d7298f0882b5b84e821b2a81bc12f06bc48b699a",
        KIND_PAIRS,
    ),
    MillSource(
        "dpr_mill_r3219",
        "experiments/dpr_mill_r3219.py",
        "651e8a74cf17ebb69b2f5c3113d95a5c5a0c4bda",
        KIND_PAIRS,
    ),
    MillSource(
        "dpr_mill_r3257",
        "experiments/dpr_mill_r3257.py",
        "a53cd8532689355c1d103664c9fc0dc04ab0772c",
        KIND_PAIRS,
    ),
    MillSource(
        "dpr_mill_r3287",
        "experiments/dpr_mill_r3287.py",
        "e8e05185bd114a276b14a6e8c189078b7d7be895",
        KIND_PAIRS,
    ),
    MillSource(
        "dpr_mill_r3302",
        "experiments/dpr_mill_r3302.py",
        "72f39a2c5f1b968b12e8e1806018844d2f1398af",
        KIND_PAIRS,
    ),
    MillSource(
        "dpr_mill_r3317",
        "experiments/dpr_mill_r3317.py",
        "68f6fd4b0bf429c4b707506f5993e63c4cae5a1d",
        KIND_PAIRS,
    ),
    MillSource(
        "dpr-loop-leftover3-r2475",
        "experiments/dpr-loop-leftover3-r2475.py",
        "52b91ce38171177c13aee88a954ab0987be37f8f",
        KIND_LOOP,
        "experiments/dpr-mill-leftover3-r2475.py",
    ),
    MillSource(
        "dpr-loop-r2631",
        "experiments/dpr-loop-r2631.py",
        "c428cab6d44308b8c61cdaab1401c9d0c643e957",
        KIND_LOOP,
        "experiments/dpr-mill-r2631.py",
    ),
    MillSource(
        "dpr-loop-r2758",
        "experiments/dpr-loop-r2758.py",
        "263d378ae3e33577b33899c3bde26bc8e943fe0a",
        KIND_LOOP,
        "experiments/dpr-mill-r2758.py",
    ),
    MillSource(
        "dpr-loop-r2811",
        "experiments/dpr-loop-r2811.py",
        "23b925b877606aa78ebf1c5087762a274ed19400",
        KIND_LOOP,
        "experiments/dpr-mill-r2811.py",
    ),
    MillSource(
        "dpr-loop-r2836",
        "experiments/dpr-loop-r2836.py",
        "abf46720a85615bebd426222dcb2f72d74d9b860",
        KIND_LOOP,
        "experiments/dpr-mill-r2836.py",
    ),
    MillSource(
        "dpr_loop_r2850",
        "experiments/dpr_loop_r2850.py",
        "ec29db08f01e238767490a62ffa7fcfafa8b4d13",
        KIND_LOOP,
        "experiments/dpr_mill_r2850.py",
    ),
    MillSource(
        "dpr_loop_r2865",
        "experiments/dpr_loop_r2865.py",
        "fa6ccb737f2ed169d1235646661c6f405011f704",
        KIND_LOOP,
        "experiments/dpr_mill_r2865.py",
    ),
    MillSource(
        "dpr_loop_r2880",
        "experiments/dpr_loop_r2880.py",
        "3ea238cde7e15aa76963fe9689be4f1d5512c700",
        KIND_LOOP,
        "experiments/dpr_mill_r2880.py",
    ),
    MillSource(
        "dpr_loop_r2959",
        "experiments/dpr_loop_r2959.py",
        "67d8793e9d0c38ee48e919aeb49116db0a1fee79",
        KIND_LOOP,
        "experiments/dpr_mill_r2959.py",
    ),
    MillSource(
        "dpr_loop_r3039",
        "experiments/dpr_loop_r3039.py",
        "45db3fe7d2c0292d5855748a80c5a54db922b070",
        KIND_LOOP,
        "experiments/dpr_mill_r3039.py",
    ),
    MillSource(
        "dpr_loop_r3119",
        "experiments/dpr_loop_r3119.py",
        "98901a247709e4e8cd2c2cf47bb06a734d3f66f3",
        KIND_LOOP,
        "experiments/dpr_mill_r3119.py",
    ),
    MillSource(
        "dpr_loop_r3182",
        "experiments/dpr_loop_r3182.py",
        "0bd5dd8915c1bd298a77ad70f77c33144afe64ac",
        KIND_LOOP,
        "experiments/dpr_mill_r3182.py",
    ),
    MillSource(
        "dpr_loop_r3219",
        "experiments/dpr_loop_r3219.py",
        "67159c63b734d694ddf3f530b0224511cbc40519",
        KIND_LOOP,
        "experiments/dpr_mill_r3219.py",
    ),
    MillSource(
        "dpr_loop_r3257",
        "experiments/dpr_loop_r3257.py",
        "16c21eae1aa5d7c7cba5277ff71644aaab4a1573",
        KIND_LOOP,
        "experiments/dpr_mill_r3257.py",
    ),
    MillSource(
        "dpr_loop_r3287",
        "experiments/dpr_loop_r3287.py",
        "89103204c94c518215d2be55ae1d40715caaea12",
        KIND_LOOP,
        "experiments/dpr_mill_r3287.py",
    ),
    MillSource(
        "dpr_loop_r3302",
        "experiments/dpr_loop_r3302.py",
        "8d23ee447f065016257af9c77f6a152029663902",
        KIND_LOOP,
        "experiments/dpr_mill_r3302.py",
    ),
    MillSource(
        "dpr_loop_r3317",
        "experiments/dpr_loop_r3317.py",
        "4e0ffa0a7b85891dcfd04f584fd5ac61f7adf213",
        KIND_LOOP,
        "experiments/dpr_mill_r3317.py",
    ),
    MillSource(
        "dpr-lrd-hopper-leftover3",
        "experiments/dpr-lrd-hopper-leftover3.py",
        "9aec4dc0c1314697de026bfbfd1038216dfac9d5",
        KIND_HOPPER,
        "experiments/dpr-mill-leftover3-r2475.py",
        "experiments/lrd-mill-leftover3-r67.py",
    ),
    MillSource(
        "dpr-lrd-hopper-leftover3b",
        "experiments/dpr-lrd-hopper-leftover3b.py",
        "20adc6164c4cde4e4a5c7bbbf20df0a90f2c4643",
        KIND_HOPPER,
        "experiments/dpr-mill-leftover3-r2475.py",
        "experiments/lrd-mill-leftover3b-r75.py",
    ),
    MillSource(
        "_gen_dpr_r2880",
        "experiments/_gen_dpr_r2880.py",
        "2074cdebc5237c3edb1518ee9e24613c7d3c7bfe",
        KIND_GEN,
    ),
)


def catalog_sources() -> tuple[MillSource, ...]:
    return tuple(source for source in MILL_SOURCES if source.kind in {KIND_PAIRS, KIND_PLANTS})


def loop_sources() -> tuple[MillSource, ...]:
    return tuple(source for source in MILL_SOURCES if source.kind == KIND_LOOP)


def hopper_sources() -> tuple[MillSource, ...]:
    return tuple(source for source in MILL_SOURCES if source.kind == KIND_HOPPER)


def gen_sources() -> tuple[MillSource, ...]:
    return tuple(source for source in MILL_SOURCES if source.kind == KIND_GEN)


def source_by_id(mill_id: str) -> MillSource:
    for source in MILL_SOURCES:
        if source.mill_id == mill_id:
            return source
    raise KeyError(f"unknown dpr mill source {mill_id!r}")
