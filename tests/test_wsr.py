#!/usr/bin/env python3
"""AST-extracted wsr family under ``pipelines/wsr``."""

from __future__ import annotations

import io
import json
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "pipelines"))

from mill_reviewed_vocabulary import REVIEWED_MILL_PREFIX_HOMES  # noqa: E402
from raw_tree_guard import DEFAULT_RAW_OUTPUT_ROOT  # noqa: E402
from wsr import cli  # noqa: E402
from wsr import generate as gen  # noqa: E402
from wsr._contract import (  # noqa: E402
    FACTORY,
    FAMILY_PREFIX,
    FINDING_GENERATE_DEST_EXISTS,
    FINDING_GENERATE_RAW_TREE,
    GENERATOR,
    HANDOFF_STEPS,
    LEFTOVER3_N_ROUNDS,
    LEFTOVER3_START_ROUND,
    LEGACY_COMMIT,
    LEGACY_MILL,
    LEGACY_MILL_SHA256,
    LEGACY_PLANTS,
    LEGACY_PLANTS_SHA256,
    LLL_COMMIT,
    LLL_MILL,
    LLL_MILL_SHA256,
    LLL_N_ROUNDS,
    LLL_START_ROUND,
    N_ROUNDS,
    PAIRS_SHA256,
    REFUSED_MILL,
    START_ROUND,
    SUCCESS_STEPS,
    WsrRefusal,
)
from wsr.catalog import (  # noqa: E402
    ast_extract_catalog,
    ast_extract_mapping_pairs,
    ast_extract_mill_constants,
    ast_extract_pairs,
    catalog_check,
    sha256_text,
)

WSR_DIR = REPO / "pipelines" / "wsr"
PACKAGE_FILES = (
    "__init__.py",
    "_contract.py",
    "catalog.py",
    "generate.py",
    "generate_lll.py",
    "cli.py",
)


def _legacy_source(relpath: str, commit: str | None = None) -> str | None:
    specs = []
    if commit:
        specs.append(f"{commit}:{relpath}")
    specs.append(f"origin/legacy-mill-lane:{relpath}")
    for spec in specs:
        try:
            return subprocess.check_output(["git", "show", spec], text=True, cwd=REPO)
        except subprocess.CalledProcessError:
            continue
    return None


class WsrFamilyLayoutTests(unittest.TestCase):
    def test_package_is_exactly_the_cleaned_modules(self):
        names = tuple(sorted(path.name for path in WSR_DIR.glob("*.py")))
        self.assertEqual(names, tuple(sorted(PACKAGE_FILES)))

    def test_leftover_mill_scripts_are_not_vendored(self):
        leftover = tuple(sorted(WSR_DIR.glob("*mill*.py"))) + tuple(
            sorted(WSR_DIR.glob("*plants*.py"))
        )
        self.assertEqual(leftover, ())
        self.assertFalse((WSR_DIR / "wsr-mill-leftover3-r41.py").exists())
        self.assertFalse((WSR_DIR / "wsr-plants-r73.py").exists())
        self.assertFalse((WSR_DIR / REFUSED_MILL.split("/")[-1]).exists())

    def test_pairs_jsonl_is_compact_and_pinned(self):
        pairs_path = WSR_DIR / "pairs.jsonl"
        self.assertTrue(pairs_path.is_file())
        self.assertEqual(sha256_text(pairs_path.read_text(encoding="utf-8")), PAIRS_SHA256)
        lines = [line for line in pairs_path.read_text(encoding="utf-8").splitlines() if line.strip()]
        self.assertEqual(len(lines), N_ROUNDS)
        self.assertTrue(all(not line.startswith(" ") for line in lines))


class WsrCatalogTests(unittest.TestCase):
    def test_reviewed_prefix_maps_to_factory(self):
        self.assertEqual(REVIEWED_MILL_PREFIX_HOMES[FAMILY_PREFIX], FACTORY)

    def test_catalog_check_pins_thirty_two_pairs(self):
        loaded = catalog_check(root=REPO)
        self.assertEqual(loaded.factory, FACTORY)
        self.assertEqual(loaded.generator, GENERATOR)
        self.assertEqual(loaded.start_round, START_ROUND)
        self.assertEqual(len(loaded.pairs), N_ROUNDS)
        self.assertEqual([pair.round_n for pair in loaded.pairs], list(range(41, 57)) + list(range(89, 105)))

    def test_leftover3_slice_matches_legacy_ast_extract(self):
        source = _legacy_source(LEGACY_PLANTS, LEGACY_COMMIT)
        if source is None:
            self.skipTest("legacy-mill-lane wsr leftover3 source is not available")
        self.assertEqual(sha256_text(source), LEGACY_PLANTS_SHA256)
        extracted = ast_extract_catalog(source, source)
        loaded = catalog_check(root=REPO)
        leftover3 = [pair for pair in loaded.pairs if pair.source_format == "leftover3-v1"]
        self.assertEqual(len(leftover3), LEFTOVER3_N_ROUNDS)
        self.assertEqual(extracted["start_round"], LEFTOVER3_START_ROUND)
        self.assertEqual(len(extracted["pairs"]), LEFTOVER3_N_ROUNDS)
        constants = ast_extract_mill_constants(source)
        self.assertEqual(constants["FACTORY"], FACTORY)
        self.assertEqual(constants["PREFIX"], FAMILY_PREFIX)
        self.assertEqual(constants["GENERATOR"], GENERATOR)
        for index, pair in enumerate(leftover3):
            raw = extracted["pairs"][index]
            self.assertEqual(raw["round"], pair.round_n)
            self.assertEqual(dict(raw["ok"]), dict(pair.ok))
            self.assertEqual(dict(raw["bad"]), dict(pair.bad))

    def test_r89_slice_matches_legacy_ast_extract(self):
        source = _legacy_source(LLL_MILL, LLL_COMMIT)
        if source is None:
            self.skipTest("legacy-mill-lane wsr r89 source is not available")
        self.assertEqual(sha256_text(source), LLL_MILL_SHA256)
        plants = ast_extract_mapping_pairs(source)
        self.assertEqual(len(plants), LLL_N_ROUNDS)
        loaded = catalog_check(root=REPO)
        mapping = [pair for pair in loaded.pairs if pair.source_format == "mapping-v1"]
        self.assertEqual(len(mapping), LLL_N_ROUNDS)
        self.assertEqual(mapping[0].round_n, LLL_START_ROUND)
        for index, pair in enumerate(mapping):
            self.assertEqual(dict(pair.plant or {}), dict(plants[index]))

    def test_catalog_rejects_banned_r40_clones(self):
        loaded = catalog_check(root=REPO)
        joined = " ".join(
            f"{pair.ok.get('slug', '')} {pair.bad.get('slug', '')} "
            f"{(pair.plant or {}).get('slug', '')} {(pair.plant or {}).get('fail', '')}"
            for pair in loaded.pairs
        )
        self.assertNotIn("anycable", joined)
        self.assertNotIn("reverb", joined)
        self.assertNotIn("cookie-replay", joined)


class WsrGenerateTests(unittest.TestCase):
    def test_first_leftover3_pair_is_sixteen_plus_seventeen(self):
        loaded = catalog_check(root=REPO)
        pair = loaded.pairs[0]
        built = gen.build_pair(pair)
        self.assertEqual(built.ok["id"], "wsr-r41-socketio-leftover-sid")
        self.assertEqual(built.bad["id"], "wsr-r41-socketio-drop-sid-handoff")
        self.assertEqual(len(built.ok["steps"]), SUCCESS_STEPS)
        self.assertEqual(len(built.bad["steps"]), HANDOFF_STEPS)
        self.assertTrue(built.ok["reward"]["success"])
        self.assertFalse(built.bad["reward"]["success"])
        self.assertIn("Novel coverage: 87%", built.notes)
        self.assertEqual(built.ok["meta"]["factory"], FACTORY)
        self.assertEqual(built.ok["meta"]["generator"], GENERATOR)

    def test_first_r89_pair_is_sixteen_plus_seventeen(self):
        loaded = catalog_check(root=REPO)
        pair = next(item for item in loaded.pairs if item.round_n == LLL_START_ROUND)
        built = gen.build_pair(pair)
        self.assertEqual(built.ok["id"], "wsr-r89-mercure-last-event-id-leftover-vs-drop-topic")
        self.assertEqual(built.bad["id"], "wsr-r89-mercure-drop-last-event-id-handoff")
        self.assertEqual(len(built.ok["steps"]), SUCCESS_STEPS)
        self.assertEqual(len(built.bad["steps"]), HANDOFF_STEPS)

    def test_every_catalog_pair_builds(self):
        loaded = catalog_check(root=REPO)
        built = gen.build_catalog(loaded)
        self.assertEqual(len(built), N_ROUNDS)
        ids = [item.ok["id"] for item in built] + [item.bad["id"] for item in built]
        self.assertEqual(len(set(ids)), 2 * N_ROUNDS)
        self.assertTrue(all(item.ok["id"].startswith(f"wsr-r{item.round_n}-") for item in built))

    def test_generate_writes_a_new_tree_and_refuses_clobber(self):
        loaded = catalog_check(root=REPO)
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "wsr-out"
            written = gen.generate(dest, catalog=loaded, rounds=(41,))
            self.assertEqual(len(written), 1)
            batch = dest / "batch-r41.jsonl"
            notes = dest / "NOTES-r41.md"
            self.assertTrue(batch.is_file())
            self.assertTrue(notes.is_file())
            lines = batch.read_text(encoding="utf-8").splitlines()
            self.assertEqual(len(lines), 2)
            self.assertEqual(json.loads(lines[0])["id"], written[0].ok["id"])
            with self.assertRaises(WsrRefusal) as raised:
                gen.generate(dest, catalog=loaded, rounds=(41,))
            self.assertEqual(raised.exception.code, FINDING_GENERATE_DEST_EXISTS)

    def test_generate_refuses_the_raw_tree(self):
        loaded = catalog_check(root=REPO)
        with self.assertRaises(WsrRefusal) as raised:
            gen.generate(DEFAULT_RAW_OUTPUT_ROOT / "wsr-forbidden", catalog=loaded, rounds=(41,))
        self.assertEqual(raised.exception.code, FINDING_GENERATE_RAW_TREE)


class WsrCliTests(unittest.TestCase):
    def test_catalog_check_cli(self):
        stdout = io.StringIO()
        stderr = io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            code = cli.run(["catalog-check", "--json"])
        self.assertEqual(code, 0)
        payload = json.loads(stdout.getvalue())
        self.assertEqual(payload["pair_count"], N_ROUNDS)
        self.assertEqual(payload["factory"], FACTORY)
        self.assertEqual(stderr.getvalue(), "")

    def test_generate_cli_one_round(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "cli-out"
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                code = cli.run(["generate", "--out", str(dest), "--round", "89", "--json"])
            self.assertEqual(code, 0)
            payload = json.loads(stdout.getvalue())
            self.assertEqual(payload["episodes"], 2)
            self.assertTrue((dest / "batch-r89.jsonl").is_file())


if __name__ == "__main__":
    unittest.main()
