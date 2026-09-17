#!/usr/bin/env python3
"""Vocabulary for the ``evh`` mill family (eval-harness lane).

The reviewed mill prefix ``evh`` maps to ``eval-harness-trajectory-factory`` in
``mill_reviewed_vocabulary.REVIEWED_MILL_PREFIX_HOMES``. This package extracts
catalog identity from the nine ``legacy-mill-lane`` scripts without vendoring
``evh-loop*.py``, ``_gen_evh_*.py``, or ``scripts/eval_harness_unique_mill``.
"""

from __future__ import annotations

FAMILY_PREFIX = "evh"
FACTORY = "eval-harness-trajectory-factory"
GENERATOR = "grok-4.6"
RECORD_ID_PREFIX = FAMILY_PREFIX
QUOTA_PER_ROUND = 2
CATALOG_SCHEMA_ID = "evh-catalog-extract/v1"
SLICE_ID = "r801"
DEFAULT_RUN_LABEL = "2026-08-19-agentic"
LEGACY_REF = "origin/legacy-mill-lane"
PRESERVE_COMMIT = "66deb037890ec2b8177c3a07542bf623924037bb"
CATALOG_FILENAME = "CATALOG.json"
PAIRS_FILENAME = "pairs.jsonl"
PAIRS_N_ROWS = 1716
PAIRS_SHA256 = "4000c59b84031b00b41aa1cffc6563eb062830541faffbc105449ed6465ae2bb"
LEFTOVER_PLANTS_FILENAME = "leftover-plants.jsonl"
LEFTOVER_PLANTS_N_ROWS = 4
LEFTOVER_PLANTS_SHA256 = "a5aed8de6f90ca53acfd83830558ba2b39a7b104600be693c62b995c4feee398"
LEFTOVER_PLANTS_B_FILENAME = "leftover-plants-b.jsonl"
LEFTOVER_PLANTS_B_N_ROWS = 4
LEFTOVER_PLANTS_B_SHA256 = "ebbcd586ffd72960673a0d273dc87e363f3b8c140b05e96735f7ac86995b7779"
ARCHIVE_B_PATH = "scripts/eval_harness_unique_mill/mill_plants.py"
ARCHIVE_B_LEGACY_COMMIT = "813f93f1969c1c4421e5663492e9663739efa642"
ARCHIVE_B_BLOB_SHA = "223525842d259139ae027eb434168a5681628e2c"
ARCHIVE_C_PATH = "scripts/eval_harness_unique_mill/mill_plants_b.py"
ARCHIVE_C_LEGACY_COMMIT = "813f93f1969c1c4421e5663492e9663739efa642"
ARCHIVE_C_BLOB_SHA = "d1077301f4e9bfbc4516e63a55950c869ff54fe9"
ARCHIVE_C_SHA256 = "dfd7c0b4dd3ce74d61b5ba03ed6482f040900190ae6c96f2581a867a92a17d0d"
LEFTOVER_LETTERS_LANDED = "cdefghijklmn"
LEFTOVER_LETTERS_N_ROWS = 147
LEFTOVER_LETTER_PINS: dict[str, dict[str, object]] = {
    "c": {
        "path": "scripts/eval_harness_unique_mill/mill_plants_c.py",
        "blob_sha": "6ee994f52e10b85c3009947388f262f0e5cb0f96",
        "sha256": "888dfa58328f103c94eb312409c89ec901a1c8f995cdbfb561263cfed0a78ee3",
        "n_rows": 6,
        "plants_sha256": "b3ab495c2ebd9d67fc3b6d2c0c8b0f62245ad609e44ab5bcea03f97856ee4a7c",
        "filename": "leftover-plants-c.jsonl",
        "archive_key": "archive_d",
    },
    "d": {
        "path": "scripts/eval_harness_unique_mill/mill_plants_d.py",
        "blob_sha": "62bc6876d979d2c39ede8490f6ba31592dc8db55",
        "sha256": "c5f31bd8358a18d30473ac837acff8d95421db02e0b507066f8281d2fbcd54dc",
        "n_rows": 4,
        "plants_sha256": "9554d101049b05f811b4c4ef77be48b99002a688a3d7c74480d125789810d383",
        "filename": "leftover-plants-d.jsonl",
        "archive_key": "archive_e",
    },
    "e": {
        "path": "scripts/eval_harness_unique_mill/mill_plants_e.py",
        "blob_sha": "50c47f4c5f3fc31c82c465de09967cc75823c060",
        "sha256": "6708ce940943c1a65aed9afee2b054a1a1147d3afdb7a27847967bdd513851c9",
        "n_rows": 8,
        "plants_sha256": "fdc5c725703068092d83c7a91bc615732c12047eacb898b24ee87d5db65c87dc",
        "filename": "leftover-plants-e.jsonl",
        "archive_key": "archive_f",
    },
    "f": {
        "path": "scripts/eval_harness_unique_mill/mill_plants_f.py",
        "blob_sha": "0e1968b14e6eb654d72e5c3e3448b13bd0eb98b0",
        "sha256": "ab6bd80fa1678517add1eb58b0e97ed6bee6c653b78dba4bea4dc6cd585a92fb",
        "n_rows": 17,
        "plants_sha256": "8c3d4693da05ee32f9cd0c7718cd06843196b3eaf968c247b8c9780f28031b17",
        "filename": "leftover-plants-f.jsonl",
        "archive_key": "archive_g",
    },
    "g": {
        "path": "scripts/eval_harness_unique_mill/mill_plants_g.py",
        "blob_sha": "e1e9fe4e167589ebdc93ce00d538b33bc5c82aeb",
        "sha256": "1dc084e426924287d1a2312d90fc6699b56ff937be21270983b2ff29d3d4c481",
        "n_rows": 19,
        "plants_sha256": "3cb1ada439e9453710227e517cd0f28df8a89fbfeb14657ed5c34188ed0e7cd8",
        "filename": "leftover-plants-g.jsonl",
        "archive_key": "archive_h",
    },
    "h": {
        "path": "scripts/eval_harness_unique_mill/mill_plants_h.py",
        "blob_sha": "5234b704c7900e1cb8370bfcb38e138dd8101c97",
        "sha256": "46f9b4fa1bc77b7321fbb31de66b6c6156f7474e204d1ec85df3f2fbfc9d81df",
        "n_rows": 24,
        "plants_sha256": "d0cdc516b10aaa8e2c38ea609df33c9073b7fae95621384b258f4aae966bb795",
        "filename": "leftover-plants-h.jsonl",
        "archive_key": "archive_i",
    },
    "i": {
        "path": "scripts/eval_harness_unique_mill/mill_plants_i.py",
        "blob_sha": "d949f7e36fee070c34743b1a964f56f95a924aea",
        "sha256": "d39139296cb259452b62599b801d65fa63bfdbf7aa91ab273e30cb2823e51901",
        "n_rows": 16,
        "plants_sha256": "c6cf3e697981dc1277fd7fddc0aff54fd1e89777854bb9a6390e2a6b1009b11c",
        "filename": "leftover-plants-i.jsonl",
        "archive_key": "archive_j",
    },
    "j": {
        "path": "scripts/eval_harness_unique_mill/mill_plants_j.py",
        "blob_sha": "fbb139c8232ef185068eb54bbf897eaec8a630d6",
        "sha256": "aaca4714e23f2cd09f8b3f9cdb774140cd5fd54e8da484b3adb0579fd2ad8323",
        "n_rows": 16,
        "plants_sha256": "e4b629ae9a3aecb01e716263b1f4e4dc1f51a490b33dde600467cbf5dcaded66",
        "filename": "leftover-plants-j.jsonl",
        "archive_key": "archive_k",
    },
    "k": {
        "path": "scripts/eval_harness_unique_mill/mill_plants_k.py",
        "blob_sha": "e554a1c995f2f02ce6239baf1e9ecb2feb3efd6c",
        "sha256": "876e752d7d661a0f18441e43fe7c669718ad7527f2c382bf50db485e95f61079",
        "n_rows": 15,
        "plants_sha256": "3ecd4bec963daeb27b9220adec538cf7e9fa27d1bf63faaf5d893a21ef7a9b72",
        "filename": "leftover-plants-k.jsonl",
        "archive_key": "archive_l",
    },
    "l": {
        "path": "scripts/eval_harness_unique_mill/mill_plants_l.py",
        "blob_sha": "90b32ee2e671ee924842888d2b3aaddd311765e4",
        "sha256": "ccb8fed9000ba09eff8d5b5bd3a1ce707ff1582e3bdd1d8b8590ef8da88a070b",
        "n_rows": 12,
        "plants_sha256": "32dcda50d854aa7721601a10b61809cc336219f29f0453f31509e2764bd37056",
        "filename": "leftover-plants-l.jsonl",
        "archive_key": "archive_m",
    },
    "m": {
        "path": "scripts/eval_harness_unique_mill/mill_plants_m.py",
        "blob_sha": "5dcb67e6036ad80ab45a6f27359dfa6ff06e9609",
        "sha256": "05c14918fcfad8cb6aaea4a3ec7454e4f9b401d588013761363412a143f8ae15",
        "n_rows": 6,
        "plants_sha256": "9e8548c30788e7758814efbc3327d99344626f14cf5554da2cb2471e9173a907",
        "filename": "leftover-plants-m.jsonl",
        "archive_key": "archive_n",
    },
    "n": {
        "path": "scripts/eval_harness_unique_mill/mill_plants_n.py",
        "blob_sha": "2f8f32892af75f4a943815165c26a0945ae04da6",
        "sha256": "c48bd5d7742d8ea06a6c32a5a742b13238866f25149073ac6a3104a406927bb6",
        "n_rows": 4,
        "plants_sha256": "c8b65f0b0f84de3e3880da28d9888c4b3436da197898f8eb23aff494ca8bb72b",
        "filename": "leftover-plants-n.jsonl",
        "archive_key": "archive_o",
    },
}
LEFTOVER_PLANT_ROW_KEYS = (
    "index",
    "ok_slug",
    "ok_domain",
    "ok_kind",
    "bad_slug",
    "bad_domain",
    "bad_kind",
    "source",
)
FIRST_SLICE_MILL_ID = "_gen_evh_plants_r801"
MILL_DIR = "scripts/eval_harness_unique_mill"

KIND_PAIRS = "pairs"
KIND_LOOP = "loop"
KIND_GEN = "plant-gen"

SHAPE_ADD_TABLES = "catalog-add-tables"
SHAPE_RAW = "raw-literal"
SHAPE_FSTRING = "catalog-fstring"
SHAPE_PARAM = "catalog-param-fstring"

VENDOR_PREFIXES = (
    "evh-mill-",
    "evh-loop-",
    "_gen_evh_",
    "eval_harness_",
    "mill_plants",
)
FORBIDDEN_MILL_GLOBS = (
    "evh-mill*.py",
    "evh-loop*.py",
    "_gen_evh_*.py",
    "eval_harness_*mill*.py",
    "mill_plants*.py",
)
