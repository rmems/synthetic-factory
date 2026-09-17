#!/usr/bin/env python3
"""Pinned inventory of the 77 SSR scripts on ``legacy-mill-lane``.

Blob SHAs are the preserve-commit objects (``vocabulary.PRESERVE_COMMIT``).
Paths, loop companions, and sidecar catalog names follow the mill-id
convention so later PRs can bind them without vendoring publishers.
"""

from __future__ import annotations

from dataclasses import dataclass

from .vocabulary import KIND_FAST, KIND_LOOP, KIND_PAIRS, SOURCE_FILE_COUNT

_CATALOG_JSON_FROM = 1142
_DECODER_COMPANION = "experiments/ssr-mill-decoder.py"


@dataclass(frozen=True)
class MillSource:
    mill_id: str
    path: str
    blob_sha: str
    kind: str
    companion_mill_path: str | None = None
    catalog_json: str | None = None


# mill_id -> preserve-commit blob SHA. Paths and companions are derived.
_PIN_SHAS: tuple[tuple[str, str], ...] = (
    ("ssr-loop-decoder", "1e257abf80d739528c02f8ebd5bff2273275ae90"),
    ("ssr-loop-r1025", "f452f2c62877cc71e264d0d1590378db83ed296c"),
    ("ssr-loop-r1065", "64c13b82024d6be7e1f513b3fccaa52841cce8e0"),
    ("ssr-loop-r1105", "cb4c2d03c0d1a099abba33e2a459bb3c34603e53"),
    ("ssr-loop-r1142", "75bda4ac94031453b461fc50bf6f986466b38746"),
    ("ssr-loop-r1182", "89702e9f22895e4e639d4782e8f345130ea84d02"),
    ("ssr-loop-r1222", "e4b357f7c73d6bee12b161d796a3fbeab21abdbf"),
    ("ssr-loop-r1262", "fe5660352b4555ab20d0677fadc033fea3aaa300"),
    ("ssr-loop-r1302", "debffad91dab42006a9afd8ac7e9e32f7a96efc3"),
    ("ssr-loop-r1342", "6c6ecb47a223ef847cb9b6e0d6a59ac033b7e743"),
    ("ssr-loop-r1382", "11366878fcce983a57a6fa181df0be7f37b8627d"),
    ("ssr-loop-r1422", "271d58c8adc39670ae8bb99fad6d405cda82e00a"),
    ("ssr-loop-r1462", "031c7eeb366df647e358ec1706c812af097e57f8"),
    ("ssr-loop-r1502", "3405d1d13b93c2781893933c4c1ad5704f2206f5"),
    ("ssr-loop-r1542", "7891f642e9749bd51e0dfbdb291e643e7acd45c1"),
    ("ssr-loop-r1582", "2c5d29f86c4c76fe3d53f9e3e554b485a0417ccb"),
    ("ssr-loop-r1622", "cc56df067d3a30141f023bb88198b15239344340"),
    ("ssr-loop-r1662", "9a25e07d3be3189bae598722ff8e50b43333a3ec"),
    ("ssr-loop-r1702", "7bd270bed86d277fa5d95baeffa9278f37e8a8b6"),
    ("ssr-loop-r181", "b738a4f1ed8351c37e472a1aaf71dc1e0f93a61a"),
    ("ssr-loop-r197", "2a2bdb1ed231460db3a511a859a2a95086e21229"),
    ("ssr-loop-r232", "97868debd75928ac6a2bd3cff54c7a95dd7c7f31"),
    ("ssr-loop-r252", "9b18827204fba61bcccb64da6e0088c35150b346"),
    ("ssr-loop-r300", "7e354bf5df6f8a13fa6116a4dad018f9f27e72e6"),
    ("ssr-loop-r332", "db4f8b8d58774d444390877a8cb3ed5ba61a3dfa"),
    ("ssr-loop-r436", "59096d3a6e692c7deb015d7ff21c6a5e6b15c72f"),
    ("ssr-loop-r554", "0311e7e968fb4440fc69a537919c4e6ad1b90b60"),
    ("ssr-loop-r670", "86bd2da42634747b3342dd80b5813cd8c63e53d6"),
    ("ssr-loop-r710", "9dae392b71733f5f8f6ba66b824c21e6415beca6"),
    ("ssr-loop-r750", "d0116e48785b98724c363aae7d7f4cae8086f6ea"),
    ("ssr-loop-r790", "4993054839b14343adec5809c478cf7b881e0bcb"),
    ("ssr-loop-r830", "97661474041c312afecf20b196e9b60cc21a160f"),
    ("ssr-loop-r869", "404cf65a46eb7688b77067557f42e54039180319"),
    ("ssr-loop-r909", "2114cb94268b531bea7943aba5448f6ad91a8dac"),
    ("ssr-loop-r949", "a3da10420f9aa4a36397aa664e66d9e68aedf4fa"),
    ("ssr-loop-r986", "de56bcd86e1cc38371854d4f08a7734bc498c1d7"),
    ("ssr-mill-decoder", "7643895f32c8bcdf4193701b1381254e383d3ece"),
    ("ssr-mill-lll-r494", "fd0e63a89df4018cae36285700ff3c534c33bbb1"),
    ("ssr-mill-r1025", "51c55d6ddbe9dfcbde7acb7b105ad5bd3133e397"),
    ("ssr-mill-r1065", "b990b282d7a87ecbaa411637a4606ed36ad73db0"),
    ("ssr-mill-r1105", "9d5a9bcd388d538ae418ff5683dce870fdec35c2"),
    ("ssr-mill-r1142", "ff2aeb1dbd8a99a305ff33429701cd7e792bfa23"),
    ("ssr-mill-r1182", "bb988f6c8c3ffd9cd587b23718cb675d98fb5971"),
    ("ssr-mill-r1222", "2641bd8ace41fbe9be6f3f759ebc6c7ea903fb47"),
    ("ssr-mill-r1262", "6c59509d121d05305ff162144800dc6dc1e71ff6"),
    ("ssr-mill-r1302", "76b3d931aa3feb59167c6e2e7866881f058fb4bb"),
    ("ssr-mill-r1342", "c06fba2f4f2a645fb62cdc6d5936f683722f9151"),
    ("ssr-mill-r1382", "8a9358eb9f5a53bc79cdd2450de520551e87ff26"),
    ("ssr-mill-r1422", "6e8fd2f1bc087ad2460911d46ec5b948e5b45ea6"),
    ("ssr-mill-r1462", "8d27b143cb455e3cfe0ccd32ed5de0e061c86572"),
    ("ssr-mill-r1502", "f9eb80b82b5463c1e764e94bc2120d466e05bfe8"),
    ("ssr-mill-r1542", "a39b42ccc73031f08531797c9670a001365c66d9"),
    ("ssr-mill-r1582", "1e74b82da166f16a474563b684208332576f8048"),
    ("ssr-mill-r1622", "2314d7bf433dfe94bc7357004727e6b371a43d1d"),
    ("ssr-mill-r1662", "0921feb21a74ba80b5d92e078e2c831129c8717c"),
    ("ssr-mill-r1702", "186d45c5cc8bc8f899e2040dcfc2a7baa61a2154"),
    ("ssr-mill-r181", "df632782cde588cb73d1de7d610636c31e2d0397"),
    ("ssr-mill-r197", "46f84eca2e76fd43a34cdfcd1f5355a259a51584"),
    ("ssr-mill-r232", "a875e1ecf6f5a52b0d4e757782a7dcba975fdc13"),
    ("ssr-mill-r252", "44625e63e5825b34be7ea6e70cd86c947af83da9"),
    ("ssr-mill-r268", "0a06f4a32a86b311f1f5e83f41fd0ce84e6f5e39"),
    ("ssr-mill-r280", "417d0a2996300ae346f8a7aa04966eb7b871e59d"),
    ("ssr-mill-r288", "eee686964f00a00bb3007f6448d2291ca9902532"),
    ("ssr-mill-r300", "da3e7e732f269cf15747dae6df36c089d02212ed"),
    ("ssr-mill-r332", "a2b8cbeb080a6042ef4f21199bd6c0eaf5537607"),
    ("ssr-mill-r436", "d89ba67c9d306015857c38bfcb0c93e9519e51a1"),
    ("ssr-mill-r554", "3f207a588dde358d28804aec798c30248c378d97"),
    ("ssr-mill-r670", "e3956478f13f3b872fa86eda2dd3a517a2b069b7"),
    ("ssr-mill-r710", "616c1d714c53666e9f4165adea8e89f98e8b19a9"),
    ("ssr-mill-r750", "e3d5d221c3978254226c786136c2114ccebd4f58"),
    ("ssr-mill-r790", "5c752bd02636af57dd1769a30c22a8908524b821"),
    ("ssr-mill-r830", "a5ff7faa8e9e79ae9156dadbfc0f80aee9299872"),
    ("ssr-mill-r869", "f141ecf940ed81911e82a6f18f80f9e21103541d"),
    ("ssr-mill-r909", "0c21352cd148639cb9644d8070179cd363d18ce4"),
    ("ssr-mill-r949", "8ed503390d87de34c6604f1cdab933430d5cebdf"),
    ("ssr-mill-r986", "ccba61724367f21b835200e7d610b8ae604b5b03"),
    ("ssr_mill_fast", "bc5a13ff516492478a3092d66c8269d906c03013"),
)


def _kind_of(mill_id: str) -> str:
    if mill_id == "ssr_mill_fast":
        return KIND_FAST
    if mill_id.startswith("ssr-loop-"):
        return KIND_LOOP
    return KIND_PAIRS


def _round_of(mill_id: str) -> int | None:
    marker = mill_id.rfind("-r")
    if marker < 0:
        return None
    tail = mill_id[marker + 2 :]
    return int(tail) if tail.isdigit() else None


def _companion_of(mill_id: str, kind: str) -> str | None:
    if kind != KIND_LOOP:
        return None
    if mill_id == "ssr-loop-decoder":
        return _DECODER_COMPANION
    return f"experiments/ssr-mill-{mill_id.removeprefix('ssr-loop-')}.py"


def _catalog_json_of(mill_id: str, kind: str) -> str | None:
    if kind != KIND_LOOP:
        return None
    catalog_first = _round_of(mill_id)
    if catalog_first is None or catalog_first < _CATALOG_JSON_FROM:
        return None
    return f".ssr-catalog-r{catalog_first}.json"


def _source(mill_id: str, blob_sha: str) -> MillSource:
    kind = _kind_of(mill_id)
    return MillSource(
        mill_id,
        f"experiments/{mill_id}.py",
        blob_sha,
        kind,
        _companion_of(mill_id, kind),
        _catalog_json_of(mill_id, kind),
    )


MILL_SOURCES: tuple[MillSource, ...] = tuple(
    _source(mill_id, blob_sha) for mill_id, blob_sha in _PIN_SHAS
)


def catalog_sources() -> tuple[MillSource, ...]:
    return tuple(source for source in MILL_SOURCES if source.kind == KIND_PAIRS)


def loop_sources() -> tuple[MillSource, ...]:
    return tuple(source for source in MILL_SOURCES if source.kind == KIND_LOOP)


def fast_sources() -> tuple[MillSource, ...]:
    return tuple(source for source in MILL_SOURCES if source.kind == KIND_FAST)


def source_by_id(mill_id: str) -> MillSource:
    for source in MILL_SOURCES:
        if source.mill_id == mill_id:
            return source
    raise KeyError(f"unknown ssr mill source {mill_id!r}")


def assert_source_count() -> None:
    if len(MILL_SOURCES) != SOURCE_FILE_COUNT:
        raise ValueError(
            f"expected {SOURCE_FILE_COUNT} SSR sources, found {len(MILL_SOURCES)}"
        )
