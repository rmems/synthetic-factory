#!/usr/bin/env python3
"""Pinned inventory of the 69 DBC scripts on ``legacy-mill-lane``.

Blob SHAs are the preserve-commit objects (``vocabulary.PRESERVE_COMMIT``);
they are byte-identical on ``origin/legacy-mill-lane`` tip. The r597/r600
hop launderers are pinned only as excluded sources so later PRs can see
the refusal without vendoring or extracting them.
"""

from __future__ import annotations

from dataclasses import dataclass

from .vocabulary import (
    KIND_GEN,
    KIND_HOP,
    KIND_LAUNDERER,
    KIND_LOOP,
    KIND_PAIRS,
    KIND_SLUGS,
)


@dataclass(frozen=True)
class MillSource:
    mill_id: str
    path: str
    blob_sha: str
    kind: str
    companion_mill_path: str | None = None


def _source(
    mill_id: str,
    path: str,
    blob_sha: str,
    kind: str,
    companion_mill_path: str | None = None,
) -> MillSource:
    return MillSource(mill_id, path, blob_sha, kind, companion_mill_path)


MILL_SOURCES: tuple[MillSource, ...] = (
    _source('.dbc-used-slugs', 'experiments/.dbc-used-slugs.txt', '35abd72180ce67e40e186dad5cdfbd861be39840', KIND_SLUGS),
    _source('dbc-chain-after-1125', 'experiments/dbc-chain-after-1125.py', '19976d9106e7434dbf56eef24b2baf33c5bdd26a', KIND_LOOP, 'experiments/dbc-loop-r1173.py'),
    _source('dbc-hop-loop', 'experiments/dbc-hop-loop.py', 'd3876d3fa808c50529b73202d88f17eabae47f0a', KIND_HOP, 'experiments/dbc-mill-r308.py'),
    _source('dbc-hop-qbp-r74', 'experiments/dbc-hop-qbp-r74.py', '59c92120dc6cd164f5343b95d8789fa6e83a6657', KIND_HOP, 'experiments/dbc-mill-r598.py'),
    _source('dbc-hop-wsr-r73', 'experiments/dbc-hop-wsr-r73.py', '9e6472afed039ca441e4fadb8d1e6e2e5ef343c0', KIND_HOP, 'experiments/dbc-mill-r598.py'),
    _source('dbc-loop-r1029', 'experiments/dbc-loop-r1029.py', '8ca77179cba60237a474a86c1e0076040217e933', KIND_LOOP, 'experiments/dbc-mill-r1029.py'),
    _source('dbc-loop-r1077', 'experiments/dbc-loop-r1077.py', '64b1d67b41af6431db219628c5bd8a4ae1922a5b', KIND_LOOP, 'experiments/dbc-mill-r1077.py'),
    _source('dbc-loop-r1125', 'experiments/dbc-loop-r1125.py', 'a42d89c154d234dc70563147c3c825e29ed378d7', KIND_LOOP, 'experiments/dbc-mill-r1125.py'),
    _source('dbc-loop-r1173', 'experiments/dbc-loop-r1173.py', 'b765f09a465645609102fe6c484cc3433b2a0988', KIND_LOOP, 'experiments/dbc-mill-r1173.py'),
    _source('dbc-loop-r1221', 'experiments/dbc-loop-r1221.py', 'ec66fbd9f5e587138345b3987036fcde2b9f081b', KIND_LOOP, 'experiments/dbc-mill-r1221.py'),
    _source('dbc-loop-r1269', 'experiments/dbc-loop-r1269.py', 'a684e6a0370b858651b899c3e8af79101e751459', KIND_LOOP, 'experiments/dbc-mill-r1269.py'),
    _source('dbc-loop-r1317', 'experiments/dbc-loop-r1317.py', 'f8f851bc09cbec5faa3deb1dd8985eb1cc0e1c08', KIND_LOOP, 'experiments/dbc-mill-r1317.py'),
    _source('dbc-loop-r1365', 'experiments/dbc-loop-r1365.py', 'd301f51484aa8a2c6db2e29e1b2009de263cf80d', KIND_LOOP, 'experiments/dbc-mill-r1365.py'),
    _source('dbc-loop-r1408', 'experiments/dbc-loop-r1408.py', '430873b1184b1d26cc4bb8bba8103e39c340ccaa', KIND_LOOP, 'experiments/dbc-mill-r1408.py'),
    _source('dbc-loop-r1456', 'experiments/dbc-loop-r1456.py', '30f28ca13471e9f6e23574ac26cd03c6ba3f1a5e', KIND_LOOP, 'experiments/dbc-mill-r1456.py'),
    _source('dbc-loop-r1504', 'experiments/dbc-loop-r1504.py', '8e76b04a077575ea8df213f6c9d995b7e24aedc6', KIND_LOOP, 'experiments/dbc-mill-r1504.py'),
    _source('dbc-loop-r193', 'experiments/dbc-loop-r193.py', 'cb865a2fea934fc400ff75694e651e805849aa6f', KIND_LOOP, 'experiments/dbc-mill-r193.py'),
    _source('dbc-loop-r338', 'experiments/dbc-loop-r338.py', 'e4e56cd7252313fa60e878890e764c4fa28f7c00', KIND_LOOP, 'experiments/dbc-mill-r338.py'),
    _source('dbc-loop-r550', 'experiments/dbc-loop-r550.py', 'dd30db4aadfa2bca462dc3388c3482f73bbc0c2f', KIND_LOOP, 'experiments/dbc-mill-r550.py'),
    _source('dbc-loop-r598', 'experiments/dbc-loop-r598.py', 'ba2b1f7da794013d2e1e52686ecc14531d5f4be8', KIND_LOOP, 'experiments/dbc-mill-r598.py'),
    _source('dbc-loop-r647', 'experiments/dbc-loop-r647.py', 'd2441d7ce7352c536e795d94b2e4e28537e42844', KIND_LOOP, 'experiments/dbc-mill-r647.py'),
    _source('dbc-loop-r719', 'experiments/dbc-loop-r719.py', '3a7bf28e26d291d08e415bb3118a10b965f5b029', KIND_LOOP, 'experiments/dbc-mill-r719.py'),
    _source('dbc-loop-r754', 'experiments/dbc-loop-r754.py', 'f8270ab99c0aa51bd7ad63426033895cd744bc7d', KIND_LOOP, 'experiments/dbc-mill-r754.py'),
    _source('dbc-loop-r778', 'experiments/dbc-loop-r778.py', 'd887678aef6defebc997c6eeeae0edae732dfb2c', KIND_LOOP, 'experiments/dbc-mill-r778.py'),
    _source('dbc-loop-r790', 'experiments/dbc-loop-r790.py', '8a499b8e0ad440c280c78ce9c6c984d546180927', KIND_LOOP, 'experiments/dbc-mill-r790.py'),
    _source('dbc-loop-r837', 'experiments/dbc-loop-r837.py', '881bb8ccf8911e9c54fae823a601f33a95c0aeb5', KIND_LOOP, 'experiments/dbc-mill-r837.py'),
    _source('dbc-loop-r885', 'experiments/dbc-loop-r885.py', 'f4a64baca41fe9fbfd5afc176c98929a4e6fc7b2', KIND_LOOP, 'experiments/dbc-mill-r885.py'),
    _source('dbc-loop-r933', 'experiments/dbc-loop-r933.py', '0a47e33136d7bb744ac83709dce02af3cb48f656', KIND_LOOP, 'experiments/dbc-mill-r933.py'),
    _source('dbc-loop-r981', 'experiments/dbc-loop-r981.py', '3967750f5ffa101d9ff83218319f4b5c7c6f7786', KIND_LOOP, 'experiments/dbc-mill-r981.py'),
    _source('dbc-loop-unique-r320', 'experiments/dbc-loop-unique-r320.py', '539b7ce3a6d633fcd0d42d7e5cd73cdc60cff08f', KIND_LOOP, 'experiments/dbc-mill-unique-r320.py'),
    _source('dbc-loop-unique-r396', 'experiments/dbc-loop-unique-r396.py', 'c429ef0c3a0bf42a83d935120add6652bee8c757', KIND_LOOP, 'experiments/dbc-mill-unique-r396.py'),
    _source('dbc-mill-hop-r647', 'experiments/dbc-mill-hop-r647.py', '8ac87d85bdd1ba41e818f27ae86e6cec677b23bc', KIND_HOP),
    _source('dbc-mill-r1029', 'experiments/dbc-mill-r1029.py', '03326feb7b556e512952d3ed8f12c1a8782de7d4', KIND_PAIRS),
    _source('dbc-mill-r1077', 'experiments/dbc-mill-r1077.py', 'f841ddd4ca63f810be4a31896344a4a7253cfb93', KIND_PAIRS),
    _source('dbc-mill-r1125', 'experiments/dbc-mill-r1125.py', '53ba5e08a246dd5300a69504cb305d7f79e88c1b', KIND_PAIRS),
    _source('dbc-mill-r1173', 'experiments/dbc-mill-r1173.py', '5d75b010aeebf5243b7ca517f60c695694ff2a4f', KIND_PAIRS),
    _source('dbc-mill-r1221', 'experiments/dbc-mill-r1221.py', 'fc866325feb5a944b0b75ca35297c6d545dbe424', KIND_PAIRS),
    _source('dbc-mill-r1269', 'experiments/dbc-mill-r1269.py', 'b1b01f23f06ff725e01902031ad0202153057b43', KIND_PAIRS),
    _source('dbc-mill-r1317', 'experiments/dbc-mill-r1317.py', '29dbf2d6fdc93877b7669acd235f9731b7a7cb4f', KIND_PAIRS),
    _source('dbc-mill-r1365', 'experiments/dbc-mill-r1365.py', '881efafc4cf6c02335fe93af4ce4f884dfdcdb3e', KIND_PAIRS),
    _source('dbc-mill-r1408', 'experiments/dbc-mill-r1408.py', '7b329731a627099f641d224bfcd8bdf84192fb59', KIND_PAIRS),
    _source('dbc-mill-r1456', 'experiments/dbc-mill-r1456.py', 'e3f498ba9c5b4606a6cba717b34772e34169d6d9', KIND_PAIRS),
    _source('dbc-mill-r1504', 'experiments/dbc-mill-r1504.py', '3ac1b6dbf97448b4e84af240cff010844d6e84b8', KIND_PAIRS),
    _source('dbc-mill-r193', 'experiments/dbc-mill-r193.py', '684816458d590fe29623308a07b77457578ee7f2', KIND_PAIRS),
    _source('dbc-mill-r233', 'experiments/dbc-mill-r233.py', '806962a5cb05f75adea73f569129fd3252730c64', KIND_PAIRS),
    _source('dbc-mill-r248', 'experiments/dbc-mill-r248.py', '39432ca530fc18a9f50dc9306e3dec379110154e', KIND_PAIRS),
    _source('dbc-mill-r268', 'experiments/dbc-mill-r268.py', 'b858e310d5c1df9729357f044b9faeb89971c225', KIND_PAIRS),
    _source('dbc-mill-r288', 'experiments/dbc-mill-r288.py', 'a54739c46073343ddab8778e58210e8b6a98db2e', KIND_PAIRS),
    _source('dbc-mill-r308', 'experiments/dbc-mill-r308.py', 'b53677109d294ff74048356ad0356e603e6a28dc', KIND_PAIRS),
    _source('dbc-mill-r338', 'experiments/dbc-mill-r338.py', 'b3c811c3be051735aa06b90d53a76db2ffc80b60', KIND_PAIRS),
    _source('dbc-mill-r402-plants', 'experiments/dbc-mill-r402-plants.py', '9517f7bcddf457fa3e1fd4e537a51ac39e72ce1c', KIND_GEN, 'experiments/dbc-mill-r338.py'),
    _source('dbc-mill-r470-plants', 'experiments/dbc-mill-r470-plants.py', '0e1f82bbec973a2a0ace82b34c7098cad84dd356', KIND_GEN, 'experiments/dbc-mill-r338.py'),
    _source('dbc-mill-r502-plants', 'experiments/dbc-mill-r502-plants.py', '92c6e1330d4b6bc0a425a9c01593a3a87bfa7a2f', KIND_GEN, 'experiments/dbc-mill-r338.py'),
    _source('dbc-mill-r550', 'experiments/dbc-mill-r550.py', '9bccb9528230d94a9748fe0c814ad1d16f878c51', KIND_PAIRS),
    _source('dbc-mill-r598', 'experiments/dbc-mill-r598.py', '2f7c22bf1d299d76f063be503c4b4e6238041fd4', KIND_PAIRS),
    _source('dbc-mill-r647', 'experiments/dbc-mill-r647.py', '5038db652c91fba0c015d623e04f8e42dde4dcc1', KIND_PAIRS),
    _source('dbc-mill-r719', 'experiments/dbc-mill-r719.py', '1301c6cccae73337a053f16c20dc7fb35b18b014', KIND_PAIRS),
    _source('dbc-mill-r754', 'experiments/dbc-mill-r754.py', '90fe48f5381ea929f42c542f0f986d618de1c9a7', KIND_PAIRS),
    _source('dbc-mill-r778', 'experiments/dbc-mill-r778.py', '480801192c1c6d8c5716ceea9acc67a57d8e0827', KIND_PAIRS),
    _source('dbc-mill-r790', 'experiments/dbc-mill-r790.py', '05dbda131b745d6ffcf1a0f4d08099b03b20fcf6', KIND_PAIRS),
    _source('dbc-mill-r837', 'experiments/dbc-mill-r837.py', '6d867bd7516cd650c4c53d7898b39e5cd18426ed', KIND_PAIRS),
    _source('dbc-mill-r885', 'experiments/dbc-mill-r885.py', '583739a54cfd2e953da98bb54f334f967334ee5b', KIND_PAIRS),
    _source('dbc-mill-r933', 'experiments/dbc-mill-r933.py', 'e312d1e0d105b358b0add515eec0a98fedbe9b4a', KIND_PAIRS),
    _source('dbc-mill-r981', 'experiments/dbc-mill-r981.py', 'e9c839b4288be8afd549748f2c0d436988b02ad5', KIND_PAIRS),
    _source('dbc-mill-unique-r320', 'experiments/dbc-mill-unique-r320.py', '3ed52efb7c297d37bcea0230d1b49c0b5fd4ed0c', KIND_PAIRS),
    _source('dbc-mill-unique-r396', 'experiments/dbc-mill-unique-r396.py', '01105203cd5b966832d7a444322993ee8373fa65', KIND_PAIRS),
    _source('dbc_leftover_lang_mill', 'experiments/dbc_leftover_lang_mill.py', 'cee394f9c3800e4744ae6dd5f9856a8f8a1aa2dc', KIND_PAIRS),
)


EXCLUDED_LAUNDERERS: tuple[MillSource, ...] = (
    _source('dbc_r597_leftover3_mill', 'experiments/dbc_r597_leftover3_mill.py', '4c29a6ba5996c79fd68dc5719f7ebe0ebe5b0e9c', KIND_LAUNDERER),
    _source('dbc_r600_leftover3_cacheprod_mill', 'experiments/dbc_r600_leftover3_cacheprod_mill.py', 'd56b9be7af25515975c4f48f2dc125d0304d914f', KIND_LAUNDERER),
)


def catalog_sources() -> tuple[MillSource, ...]:
    return tuple(source for source in MILL_SOURCES if source.kind == KIND_PAIRS)


def loop_sources() -> tuple[MillSource, ...]:
    return tuple(source for source in MILL_SOURCES if source.kind == KIND_LOOP)


def gen_sources() -> tuple[MillSource, ...]:
    return tuple(source for source in MILL_SOURCES if source.kind == KIND_GEN)


def hop_sources() -> tuple[MillSource, ...]:
    return tuple(source for source in MILL_SOURCES if source.kind == KIND_HOP)


def slug_sources() -> tuple[MillSource, ...]:
    return tuple(source for source in MILL_SOURCES if source.kind == KIND_SLUGS)


def source_by_id(mill_id: str) -> MillSource:
    for source in (*MILL_SOURCES, *EXCLUDED_LAUNDERERS):
        if source.mill_id == mill_id:
            return source
    raise KeyError(f"unknown dbc mill source {mill_id!r}")

