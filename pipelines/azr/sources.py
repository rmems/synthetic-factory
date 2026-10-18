#!/usr/bin/env python3
"""Pinned inventory of the 76 AZR scripts on ``legacy-mill-lane``.

Blob SHAs are the preserve-commit objects (``vocabulary.PRESERVE_COMMIT``);
they are byte-identical on ``origin/legacy-mill-lane`` tip. Loops, plants,
and plant-gens are pinned so later PRs can bind them without vendoring
publishers.
"""

from __future__ import annotations

from dataclasses import dataclass

from .vocabulary import KIND_GEN, KIND_LOOP, KIND_PAIRS, KIND_PLANTS, N_SOURCES


@dataclass(frozen=True)
class MillSource:
    mill_id: str
    path: str
    blob_sha: str
    kind: str
    companion_path: str | None = None


def _row(
    mill_id: str,
    blob_sha: str,
    kind: str,
    companion: str | None = None,
) -> MillSource:
    """Pin one script; every script file is named after its mill id."""

    companion_path = f"experiments/{companion}" if companion else None
    return MillSource(mill_id, f"experiments/{mill_id}.py", blob_sha, kind, companion_path)


MILL_SOURCES: tuple[MillSource, ...] = (
    _row("azr-loop-r1181", "53967cfd8cca8590ef6a731d69d85a8c7a86314a", KIND_LOOP, "azr-mill-r1181.py"),
    _row("azr-loop-r1193", "957b435c93a0cc0b836ca6156500d64a9e040fbf", KIND_LOOP, "azr-mill-r1193.py"),
    _row("azr-loop-r1205", "e6c8eaaa265db74a0c619defdb6d82e0327e2ae0", KIND_LOOP, "azr-mill-r1205.py"),
    _row("azr-loop-r1245", "b64bfa462f9f17a20829a7bb9948effd863a963b", KIND_LOOP, "azr-mill-r1245.py"),
    _row("azr-loop-r1285", "7b836d098785e44b6226cf643e73ddf8a0fb3fcc", KIND_LOOP, "azr-mill-r1285.py"),
    _row("azr-loop-r1365", "6a7a5be3047b53940a12af4ef883c134b3056f8d", KIND_LOOP, "azr-mill-r1365.py"),
    _row(
        "azr-loop-r1415-leftover3",
        "c1ecc46782ac30dc8508e0806857f8f8da7e86cc",
        KIND_LOOP,
        "azr-mill-r1415-leftover3.py",
    ),
    _row("azr-loop-r1464", "92b6536e1b41351437586e3aae63c4b33018404a", KIND_LOOP, "azr-mill-r1464.py"),
    _row("azr-loop-r1504", "e12730dcac888ed9ce7df41f9a68e4feb0037178", KIND_LOOP, "azr-mill-r1504.py"),
    _row(
        "azr-loop-r1506-leftover3",
        "3b3858ed4b8522b6165c35e4c31ff67e6a9d8422",
        KIND_LOOP,
        "azr-mill-r1506-leftover3.py",
    ),
    _row(
        "azr-loop-r1544-leftover3",
        "31e35e79b9e8de0005bd04dbf96a35e7720db5a9",
        KIND_LOOP,
        "azr-mill-r1544-leftover3.py",
    ),
    _row("azr-loop-r1544", "8990547f106640d5a861f053c22c316c4bf99389", KIND_LOOP, "azr-mill-r1544.py"),
    _row("azr-loop-r1640", "acdedca38bcd7b4716c0b2b35d5258853f0acb04", KIND_LOOP, "azr-mill-r1640.py"),
    _row("azr-loop-r1720", "3401ff3e223675d01c66c61bd636d474658a0976", KIND_LOOP, "azr-mill-r1720.py"),
    _row("azr-loop-r1760", "0224cd1af03b7cb968cb25c7aca452d1b4aeebbc", KIND_LOOP, "azr-mill-r1760.py"),
    _row("azr-loop-r1840", "69f51708753b2b53cd8229c9bd403764dc61a61c", KIND_LOOP, "azr-mill-r1840.py"),
    _row("azr-loop-r1920", "40a731109fe2f553bbd1a276b2271280033bbd40", KIND_LOOP, "azr-mill-r1920.py"),
    _row("azr-loop-r2000", "50f188907b6e0f25982f70155beff09557176a8c", KIND_LOOP, "azr-mill-r2000.py"),
    _row("azr-loop-r2080", "10004dd80bb8a70d27e1891260c3dc139f1a4969", KIND_LOOP, "azr-mill-r2080.py"),
    _row("azr-loop-r2160", "df14bc76ed2faaa37928850739cbab15d19006db", KIND_LOOP, "azr-mill-r2160.py"),
    _row("azr-loop-r2240", "1fbc8051691e421ddc9a5b24bfa524e2f0c212ce", KIND_LOOP, "azr-mill-r2240.py"),
    _row("azr-loop-r2320", "a34a1814bc299ea3bfd8e066438ee91adfff9a17", KIND_LOOP, "azr-mill-r2320.py"),
    _row(
        "_gen_azr_plants_r1365",
        "c280bbe7de2f2ccf09143443f874bd47cc2e47e0",
        KIND_GEN,
        "azr-plants-r1365.py",
    ),
    _row(
        "_gen_azr_plants_r1544",
        "8936200604fef0c3c382f66257806751847997ae",
        KIND_GEN,
        "azr-plants-r1544.py",
    ),
    _row(
        "_gen_azr_plants_r1640",
        "07432b47fc058e661f859189721f387d00b2ea13",
        KIND_GEN,
        "azr-plants-r1640.py",
    ),
    _row(
        "_gen_azr_plants_r1720",
        "776a7b0004d6258a9e90d32c1bcf67db4013e2ad",
        KIND_GEN,
        "azr-plants-r1720.py",
    ),
    _row(
        "_gen_azr_plants_r1760",
        "5fafc8e9a7f5e3422f22d9b537a9943852caedb9",
        KIND_GEN,
        "azr-plants-r1760.py",
    ),
    _row(
        "_gen_azr_plants_r1840",
        "693226594a26c6843e502df921157753173d90fe",
        KIND_GEN,
        "azr-plants-r1840.py",
    ),
    _row(
        "_gen_azr_plants_r1920",
        "75d424906bdc2d907abf66068235fb43b178fc73",
        KIND_GEN,
        "azr-plants-r1920.py",
    ),
    _row(
        "_gen_azr_plants_r2000",
        "191dac26f27634ebe836a38da03c1feddf1e94eb",
        KIND_GEN,
        "azr-plants-r2000.py",
    ),
    _row(
        "_gen_azr_plants_r2080",
        "23bc056de952a767d45afb98cf464f487cdd104b",
        KIND_GEN,
        "azr-plants-r2080.py",
    ),
    _row(
        "_gen_azr_plants_r2160",
        "f0a7a8c35cf6b162f490b0db52b1040dcd16774a",
        KIND_GEN,
        "azr-plants-r2160.py",
    ),
    _row(
        "_gen_azr_plants_r2240",
        "fca522f83d698113030243bbf2d47379535dc415",
        KIND_GEN,
        "azr-plants-r2240.py",
    ),
    _row(
        "_gen_azr_plants_r2320",
        "437e3acff980c65146d3dfd68c09c411fc5caf31",
        KIND_GEN,
        "azr-plants-r2320.py",
    ),
    _row("azr-plants-r1245", "65b23ef75c94992212d6509b158b16c539d0b60a", KIND_PLANTS),
    _row("azr-plants-r1269", "23017cf38d3e2df23690ffff2df35d108f488fbe", KIND_PLANTS),
    _row("azr-plants-r1285", "8fe3b18d91244e7128664599b5172de46c28c29f", KIND_PLANTS),
    _row("azr-plants-r1365", "c3d88aa6498a64cc27748332bd6284616b66770f", KIND_PLANTS),
    _row(
        "azr-plants-r1415-leftover3",
        "1289ea8f0191270bbddde40116d9a55e147229d6",
        KIND_PLANTS,
    ),
    _row("azr-plants-r1464", "1fb0125125b9ef2df14bad7b44efb80f2462d1fd", KIND_PLANTS),
    _row("azr-plants-r1504", "b13d42cc04c725e7c3642b8dc79a7c51c4504f76", KIND_PLANTS),
    _row(
        "azr-plants-r1506-leftover3",
        "27a43ee35300a121818f26348d1bbcba1afd65fb",
        KIND_PLANTS,
    ),
    _row(
        "azr-plants-r1544-leftover3",
        "860a8f6d7bf2fbbe59f88e0b26bd653e37a19494",
        KIND_PLANTS,
    ),
    _row("azr-plants-r1544", "10aefac41b33196cf64faf2f27e8e69ff18dfcfe", KIND_PLANTS),
    _row("azr-plants-r1640", "c533f1194fa8d30e959f96fa1bb591358f7f2c63", KIND_PLANTS),
    _row("azr-plants-r1720", "5f8c1aef7cb807f99f29606a7d19cdc4a52bf6f5", KIND_PLANTS),
    _row("azr-plants-r1760", "542941e5e00d73cfb1fe908fa5e2cb30f41ef818", KIND_PLANTS),
    _row("azr-plants-r1840", "5281f6cd3e0151326aaeaca8c5c297a2de560a38", KIND_PLANTS),
    _row("azr-plants-r1920", "ae7a23bb6a7bf96d6b82333f80e3f5d5b9061377", KIND_PLANTS),
    _row("azr-plants-r2000", "07cac16f0fdc70c06ec913545368cf3635188b77", KIND_PLANTS),
    _row("azr-plants-r2080", "e0216b78978d9f2208fb2b33276ba158af1026ea", KIND_PLANTS),
    _row("azr-plants-r2160", "525ed40bdd081074ba00a839670e114ccf88ffdd", KIND_PLANTS),
    _row("azr-plants-r2240", "65d38c1e6d189b6b16dd806b0dfc2bb612ff3db1", KIND_PLANTS),
    _row("azr-plants-r2320", "965ad49d8b68425b49cff957db3edfc6f88fddd7", KIND_PLANTS),
    _row("azr-mill-r1181", "a2dc3e067e4b40feb99686122108d90c429ad592", KIND_PAIRS),
    _row("azr-mill-r1193", "cbe17495042da93480904d69673b93df8e21b0cf", KIND_PAIRS),
    _row(
        "azr-mill-r1205",
        "d459688a433d04a094c1a344bb83e0e0c81acd83",
        KIND_PAIRS,
        "azr-plants-r1285.py",
    ),
    _row("azr-mill-r1245", "960322afe0283eeb51ad7c476f34f46ff33bece0", KIND_PAIRS),
    _row(
        "azr-mill-r1285",
        "0548a591e184a9e841e6594f087530097d74f984",
        KIND_PAIRS,
        "azr-plants-r1285.py",
    ),
    _row(
        "azr-mill-r1365",
        "5fef941bf9a52c98fae9ce6dc3c2b134d06ca709",
        KIND_PAIRS,
        "azr-plants-r1365.py",
    ),
    _row(
        "azr-mill-r1415-leftover3",
        "0f94bd0e9df79220cdd9b8876abc6eb0fd51d637",
        KIND_PAIRS,
        "azr-plants-r1415-leftover3.py",
    ),
    _row(
        "azr-mill-r1464",
        "01292e04703a724804c34eb5771615b5fe54c824",
        KIND_PAIRS,
        "azr-plants-r1464.py",
    ),
    _row(
        "azr-mill-r1504",
        "6e1072de7798860444842efd01bbf9e2e4d054af",
        KIND_PAIRS,
        "azr-plants-r1504.py",
    ),
    _row(
        "azr-mill-r1506-leftover3",
        "4f73170f2ccf92ba098f6ec020d9f2463364f8ae",
        KIND_PAIRS,
        "azr-plants-r1506-leftover3.py",
    ),
    _row(
        "azr-mill-r1544-leftover3",
        "54a3132b1fd8dd2e231294d31370ceea427f2a1a",
        KIND_PAIRS,
        "azr-plants-r1544-leftover3.py",
    ),
    _row(
        "azr-mill-r1544",
        "af19cc45b7ac97c7748dfd8b296de464c7a1cb36",
        KIND_PAIRS,
        "azr-plants-r1544.py",
    ),
    _row(
        "azr-mill-r1640",
        "a15b583a9223198d833c45d95d94175b060c8802",
        KIND_PAIRS,
        "azr-plants-r1640.py",
    ),
    _row(
        "azr-mill-r1720",
        "8e1d8976285b47210c450f1de1b843fd9db7ab83",
        KIND_PAIRS,
        "azr-plants-r1720.py",
    ),
    _row(
        "azr-mill-r1760",
        "036bfdb8bb9e6c2e034e0d30cd32dbfed4286a4c",
        KIND_PAIRS,
        "azr-plants-r1760.py",
    ),
    _row(
        "azr-mill-r1840",
        "5450c74aebf51ad66a0186a4e495c3459d2f91f4",
        KIND_PAIRS,
        "azr-plants-r1840.py",
    ),
    _row(
        "azr-mill-r1920",
        "6b340edcb92ae7867216f1ed91079c5bd1768ee3",
        KIND_PAIRS,
        "azr-plants-r1920.py",
    ),
    _row(
        "azr-mill-r2000",
        "ea8364131e0ee05e7362bc0fe6f6d3d25f2f7b39",
        KIND_PAIRS,
        "azr-plants-r2000.py",
    ),
    _row(
        "azr-mill-r2080",
        "a583aa9bf1a27158ad6e67df852dfd7cd43e3e92",
        KIND_PAIRS,
        "azr-plants-r2080.py",
    ),
    _row(
        "azr-mill-r2160",
        "79994d524fe028202562c7ea0c48301fc9c787f1",
        KIND_PAIRS,
        "azr-plants-r2160.py",
    ),
    _row(
        "azr-mill-r2240",
        "112c948c8e76179f722c0ab636531f15c0c0441f",
        KIND_PAIRS,
        "azr-plants-r2240.py",
    ),
    _row(
        "azr-mill-r2320",
        "7029686ab3f8da0de7f59525aa7aae2b92ef23d6",
        KIND_PAIRS,
        "azr-plants-r2320.py",
    ),
)


def catalog_sources() -> tuple[MillSource, ...]:
    return tuple(source for source in MILL_SOURCES if source.kind == KIND_PAIRS)


def plant_sources() -> tuple[MillSource, ...]:
    return tuple(source for source in MILL_SOURCES if source.kind == KIND_PLANTS)


def loop_sources() -> tuple[MillSource, ...]:
    return tuple(source for source in MILL_SOURCES if source.kind == KIND_LOOP)


def gen_sources() -> tuple[MillSource, ...]:
    return tuple(source for source in MILL_SOURCES if source.kind == KIND_GEN)


def source_by_id(mill_id: str) -> MillSource:
    for source in MILL_SOURCES:
        if source.mill_id == mill_id:
            return source
    raise KeyError(f"unknown azr mill source {mill_id!r}")


if len(MILL_SOURCES) != N_SOURCES:
    raise RuntimeError(f"expected {N_SOURCES} AZR sources, found {len(MILL_SOURCES)}")
