#!/usr/bin/env python3
"""AST-extracted ewr leftover-event family under ``pipelines/ewr``."""

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

from ewr import cli  # noqa: E402
from ewr import generate as gen  # noqa: E402
from ewr._contract import (  # noqa: E402
    EwrRefusal,
    FACTORY,
    FAMILY_PREFIX,
    FINDING_GENERATE_DEST_EXISTS,
    FINDING_GENERATE_RAW_TREE,
    GENERATOR,
    HANDOFF_STEPS,
    LEGACY_COMMIT,
    LEGACY_MILL,
    LEGACY_MILL_SHA256,
    LEGACY_PLANTS,
    LEGACY_PLANTS_SHA256,
    N_ROUNDS,
    START_ROUND,
    SUCCESS_STEPS,
)
from ewr.catalog import (  # noqa: E402
    ast_extract_catalog,
    ast_extract_mill_constants,
    ast_extract_pairs,
    catalog_check,
    sha256_text,
)
from mill_reviewed_vocabulary import REVIEWED_MILL_PREFIX_HOMES  # noqa: E402
from raw_tree_guard import DEFAULT_RAW_OUTPUT_ROOT  # noqa: E402

EWR_DIR = REPO / "pipelines" / "ewr"
PACKAGE_FILES = ("__init__.py", "_contract.py", "catalog.py", "generate.py", "cli.py")


def _legacy_source(relpath: str) -> str | None:
    for spec in (f"{LEGACY_COMMIT}:{relpath}", f"origin/legacy-mill-lane:{relpath}"):
        try:
            return subprocess.check_output(["git", "show", spec], text=True, cwd=REPO)
        except subprocess.CalledProcessError:
            continue
    return None


class EwrFamilyLayoutTests(unittest.TestCase):
    def test_package_is_exactly_the_cleaned_modules(self):
        names = tuple(sorted(path.name for path in EWR_DIR.glob("*.py")))
        self.assertEqual(names, tuple(sorted(PACKAGE_FILES)))

    def test_leftover_mill_scripts_are_not_vendored(self):
        leftover = tuple(sorted(EWR_DIR.glob("ewr_*mill.py"))) + tuple(
            sorted(EWR_DIR.glob("ewr_*plants.py"))
        )
        self.assertEqual(leftover, ())
        self.assertFalse((EWR_DIR / "ewr_leftover3_mill.py").exists())
        self.assertFalse((EWR_DIR / "ewr_leftover3_plants.py").exists())


class EwrCatalogTests(unittest.TestCase):
    def test_reviewed_prefix_maps_to_factory(self):
        self.assertEqual(REVIEWED_MILL_PREFIX_HOMES[FAMILY_PREFIX], FACTORY)

    def test_catalog_check_pins_the_sixteen_leftover_pairs(self):
        loaded = catalog_check(root=REPO)
        self.assertEqual(loaded.factory, FACTORY)
        self.assertEqual(loaded.generator, GENERATOR)
        self.assertEqual(loaded.start_round, START_ROUND)
        self.assertEqual(len(loaded.pairs), N_ROUNDS)
        self.assertEqual(
            [pair.round_n for pair in loaded.pairs],
            list(range(START_ROUND, START_ROUND + N_ROUNDS)),
        )
        self.assertEqual(loaded.source["plants_sha256"], LEGACY_PLANTS_SHA256)
        self.assertEqual(loaded.source["mill_sha256"], LEGACY_MILL_SHA256)
        self.assertEqual(loaded.source["commit"], LEGACY_COMMIT)

    def test_catalog_matches_legacy_ast_extract(self):
        plants = _legacy_source(LEGACY_PLANTS)
        mill = _legacy_source(LEGACY_MILL)
        if plants is None or mill is None:
            self.skipTest("legacy-mill-lane ewr sources are not available")
        self.assertEqual(sha256_text(plants), LEGACY_PLANTS_SHA256)
        self.assertEqual(sha256_text(mill), LEGACY_MILL_SHA256)
        extracted = ast_extract_catalog(plants, mill)
        loaded = catalog_check(root=REPO)
        self.assertEqual(extracted["start_round"], loaded.start_round)
        self.assertEqual(len(extracted["pairs"]), len(loaded.pairs))
        self.assertEqual(
            ast_extract_mill_constants(mill),
            {"FACTORY": FACTORY, "START": START_ROUND, "N": N_ROUNDS},
        )
        for index, pair in enumerate(loaded.pairs):
            raw = extracted["pairs"][index]
            self.assertEqual(raw["round"], pair.round_n)
            self.assertEqual(raw["ok"]["slug"], pair.ok["slug"])
            self.assertEqual(raw["bad"]["slug"], pair.bad["slug"])
            self.assertEqual(dict(raw["ok"]), dict(pair.ok))
            self.assertEqual(dict(raw["bad"]), dict(pair.bad))
        self.assertEqual(len(ast_extract_pairs(plants)), N_ROUNDS)

    def test_catalog_rejects_banned_r39_clones(self):
        loaded = catalog_check(root=REPO)
        joined = " ".join(
            f"{pair.ok['slug']} {pair.bad['slug']}" for pair in loaded.pairs
        )
        self.assertNotIn("beehiiv", joined)
        self.assertNotIn("constant-contact", joined)
        self.assertNotIn("invoice-row-dup", joined)
        self.assertNotIn("streams", joined)


class EwrGenerateTests(unittest.TestCase):
    def test_first_pair_is_sixteen_plus_seventeen(self):
        loaded = catalog_check(root=REPO)
        built = gen.build_pair(loaded.pairs[0])
        self.assertEqual(built.ok["id"], "ewr-r40-sendgrid-leftover-event-bind")
        self.assertEqual(built.bad["id"], "ewr-r40-sendgrid-drop-event-handoff")
        self.assertEqual(len(built.ok["steps"]), SUCCESS_STEPS)
        self.assertEqual(len(built.bad["steps"]), HANDOFF_STEPS)
        self.assertTrue(built.ok["reward"]["success"])
        self.assertFalse(built.bad["reward"]["success"])
        self.assertIn("Novel coverage: 86%", built.notes)
        self.assertEqual(built.ok["meta"]["factory"], FACTORY)
        self.assertEqual(built.ok["meta"]["generator"], GENERATOR)

    def test_every_catalog_pair_builds(self):
        loaded = catalog_check(root=REPO)
        built = gen.build_catalog(loaded)
        self.assertEqual(len(built), N_ROUNDS)
        ids = [item.ok["id"] for item in built] + [item.bad["id"] for item in built]
        self.assertEqual(len(set(ids)), 2 * N_ROUNDS)
        self.assertTrue(all(item.ok["id"].startswith(f"ewr-r{item.round_n}-") for item in built))

    def test_generate_writes_a_new_tree_and_refuses_clobber(self):
        loaded = catalog_check(root=REPO)
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "ewr-out"
            written = gen.generate(dest, catalog=loaded, rounds=(40,))
            self.assertEqual(len(written), 1)
            batch = dest / "batch-r40.jsonl"
            notes = dest / "NOTES-r40.md"
            self.assertTrue(batch.is_file())
            self.assertTrue(notes.is_file())
            lines = batch.read_text(encoding="utf-8").splitlines()
            self.assertEqual(len(lines), 2)
            self.assertEqual(json.loads(lines[0])["id"], written[0].ok["id"])
            with self.assertRaises(EwrRefusal) as raised:
                gen.generate(dest, catalog=loaded, rounds=(40,))
            self.assertEqual(raised.exception.code, FINDING_GENERATE_DEST_EXISTS)

    def test_generate_refuses_the_raw_tree(self):
        loaded = catalog_check(root=REPO)
        with self.assertRaises(EwrRefusal) as raised:
            gen.generate(DEFAULT_RAW_OUTPUT_ROOT / "ewr-forbidden", catalog=loaded, rounds=(40,))
        self.assertEqual(raised.exception.code, FINDING_GENERATE_RAW_TREE)


class EwrCliTests(unittest.TestCase):
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
                code = cli.run(["generate", "--out", str(dest), "--round", "40", "--json"])
            self.assertEqual(code, 0)
            payload = json.loads(stdout.getvalue())
            self.assertEqual(payload["episodes"], 2)
            self.assertTrue((dest / "batch-r40.jsonl").is_file())


if __name__ == "__main__":
    unittest.main()
