#!/usr/bin/env python3
"""AST-extracted dbm leftover family under ``pipelines/dbm``."""

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

from dbm import cli  # noqa: E402
from dbm import generate as gen  # noqa: E402
from dbm._contract import (  # noqa: E402
    DbmRefusal,
    FACTORY,
    FAMILY_PREFIX,
    FINDING_GENERATE_DEST_EXISTS,
    FINDING_GENERATE_RAW_TREE,
    GENERATOR,
    LEGACY_COMMIT,
    LEGACY_LEFTOVER3,
    LEGACY_LEFTOVER3_SHA256,
    LEGACY_PLANTS_GEN,
    MILL_COUNT,
    MILL_PAIRS,
    MILL_PLANTS,
    N_PAIRS,
    START_ROUND,
    SUCCESS_STEPS,
)
from dbm.catalog import catalog_check  # noqa: E402
from dbm.extract import (  # noqa: E402
    ast_extract_gen_slugs,
    ast_extract_leftover3_constants,
    ast_extract_leftover3_plants,
    ast_extract_mill_catalog,
    sha256_text,
)
from mill_reviewed_vocabulary import REVIEWED_MILL_PREFIX_HOMES  # noqa: E402
from raw_tree_guard import DEFAULT_RAW_OUTPUT_ROOT  # noqa: E402

DBM_DIR = REPO / "pipelines" / "dbm"
PACKAGE_FILES = (
    "__init__.py",
    "_contract.py",
    "catalog.py",
    "cli.py",
    "episode.py",
    "extract.py",
    "generate.py",
)


def _legacy_source(relpath: str) -> str | None:
    for spec in (f"{LEGACY_COMMIT}:{relpath}", f"origin/legacy-mill-lane:{relpath}"):
        try:
            return subprocess.check_output(["git", "show", spec], text=True, cwd=REPO)
        except subprocess.CalledProcessError:
            continue
    return None


class DbmFamilyLayoutTests(unittest.TestCase):
    def test_package_is_exactly_the_cleaned_modules(self):
        names = tuple(sorted(path.name for path in DBM_DIR.glob("*.py")))
        self.assertEqual(names, tuple(sorted(PACKAGE_FILES)))

    def test_leftover_mill_scripts_are_not_vendored(self):
        leftover = tuple(sorted(DBM_DIR.glob("*mill*.py"))) + tuple(
            sorted(DBM_DIR.glob("*plants*.py"))
        )
        self.assertEqual(leftover, ())
        self.assertFalse((DBM_DIR / "unique_dbm_leftover3_mill.py").exists())
        self.assertFalse((DBM_DIR / "unique_db_migration_repair_mill.py").exists())

    def test_package_never_execs_mill_source(self):
        banned = (
            "exec(",
            "eval(",
            "exec_module",
            "spec_from_file_location",
            "importlib",
        )
        for name in PACKAGE_FILES:
            text = (DBM_DIR / name).read_text(encoding="utf-8")
            for token in banned:
                self.assertNotIn(token, text, f"{name} contains {token}")


class DbmCatalogTests(unittest.TestCase):
    def test_reviewed_prefix_maps_to_factory(self):
        self.assertEqual(REVIEWED_MILL_PREFIX_HOMES[FAMILY_PREFIX], FACTORY)

    def test_catalog_check_pins_leftover3_and_sequential_mills(self):
        loaded = catalog_check(root=REPO)
        leftover3 = loaded.leftover3
        self.assertEqual(leftover3.factory, FACTORY)
        self.assertEqual(leftover3.generator, GENERATOR)
        self.assertEqual(leftover3.start_round, START_ROUND)
        self.assertEqual(len(leftover3.pairs), N_PAIRS)
        self.assertEqual(len(leftover3.plants), N_PAIRS * 2)
        self.assertEqual(
            [pair.round_n for pair in leftover3.pairs],
            list(range(START_ROUND, START_ROUND + N_PAIRS)),
        )
        self.assertEqual(leftover3.source["mill_sha256"], LEGACY_LEFTOVER3_SHA256)
        self.assertEqual(leftover3.source["commit"], LEGACY_COMMIT)
        self.assertEqual(len(loaded.mills), MILL_COUNT)
        self.assertEqual(sum(pin.pair_count for pin in loaded.mills), MILL_PAIRS)
        self.assertEqual(sum(pin.plant_count for pin in loaded.mills), MILL_PLANTS)

    def test_leftover3_matches_legacy_ast_extract(self):
        mill = _legacy_source(LEGACY_LEFTOVER3)
        if mill is None:
            self.skipTest("legacy-mill-lane leftover3 mill is not available")
        self.assertEqual(sha256_text(mill), LEGACY_LEFTOVER3_SHA256)
        plants = ast_extract_leftover3_plants(mill)
        loaded = catalog_check(root=REPO)
        self.assertEqual(len(plants), len(loaded.leftover3.plants))
        self.assertEqual(
            ast_extract_leftover3_constants(mill),
            {"FACTORY_SLUG": FACTORY, "GENERATOR": GENERATOR, "START_ROUND": START_ROUND},
        )
        for extracted, committed in zip(plants, loaded.leftover3.plants, strict=True):
            self.assertEqual(extracted, dict(committed))

    def test_sequential_mills_match_legacy_ast_extract(self):
        loaded = catalog_check(root=REPO)
        for pin in loaded.mills:
            source = _legacy_source(pin.path)
            if source is None:
                self.skipTest(f"legacy-mill-lane {pin.path} is not available")
            self.assertEqual(sha256_text(source), pin.sha256)
            extracted = ast_extract_mill_catalog(source)
            self.assertEqual(extracted["catalog_first"], pin.catalog_first)
            self.assertEqual(extracted["constructor"], pin.constructor)
            self.assertEqual(extracted["pair_count"], pin.pair_count)
            self.assertEqual(extracted["slugs"], pin.slugs)

    def test_r1340_gen_slugs_match_the_mill_pin(self):
        loaded = catalog_check(root=REPO)
        gen_src = _legacy_source(LEGACY_PLANTS_GEN)
        if gen_src is None:
            self.skipTest("legacy-mill-lane r1340 plant generator is not available")
        r1340 = next(pin for pin in loaded.mills if pin.path.endswith("dbm-mill-r1340.py"))
        self.assertEqual(ast_extract_gen_slugs(gen_src), r1340.slugs)


class DbmGenerateTests(unittest.TestCase):
    def test_first_pair_is_sixteen_plus_sixteen(self):
        loaded = catalog_check(root=REPO)
        built = gen.build_pair(loaded.leftover3.pairs[0], loaded.leftover3)
        self.assertEqual(built.ok["id"], "dbm-r1260-flyway-undo-script-leftover3")
        self.assertEqual(built.bad["id"], "dbm-r1260-flyway-callback-leftover3")
        self.assertEqual(len(built.ok["steps"]), SUCCESS_STEPS)
        self.assertEqual(len(built.bad["steps"]), SUCCESS_STEPS)
        self.assertTrue(built.ok["reward"]["success"])
        self.assertTrue(built.bad["reward"]["success"])
        self.assertIn("Novel coverage: 52%", built.notes)
        self.assertEqual(built.ok["meta"]["factory"], FACTORY)
        self.assertEqual(built.ok["meta"]["generator"], GENERATOR)

    def test_every_leftover3_pair_builds(self):
        loaded = catalog_check(root=REPO)
        built = gen.build_catalog(loaded)
        self.assertEqual(len(built), N_PAIRS)
        ids = [item.ok["id"] for item in built] + [item.bad["id"] for item in built]
        self.assertEqual(len(set(ids)), 2 * N_PAIRS)
        self.assertTrue(all(item.ok["id"].startswith(f"dbm-r{item.round_n}-") for item in built))

    def test_generate_writes_a_new_tree_and_refuses_clobber(self):
        loaded = catalog_check(root=REPO)
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "dbm-out"
            written = gen.generate(dest, catalog=loaded, rounds=(1260,))
            self.assertEqual(len(written), 1)
            batch = dest / "batch-r1260.jsonl"
            notes = dest / "NOTES-r1260.md"
            self.assertTrue(batch.is_file())
            self.assertTrue(notes.is_file())
            lines = batch.read_text(encoding="utf-8").splitlines()
            self.assertEqual(len(lines), 2)
            self.assertEqual(json.loads(lines[0])["id"], written[0].ok["id"])
            with self.assertRaises(DbmRefusal) as raised:
                gen.generate(dest, catalog=loaded, rounds=(1260,))
            self.assertEqual(raised.exception.code, FINDING_GENERATE_DEST_EXISTS)

    def test_generate_refuses_the_raw_tree(self):
        loaded = catalog_check(root=REPO)
        with self.assertRaises(DbmRefusal) as raised:
            gen.generate(DEFAULT_RAW_OUTPUT_ROOT / "dbm-forbidden", catalog=loaded, rounds=(1260,))
        self.assertEqual(raised.exception.code, FINDING_GENERATE_RAW_TREE)


class DbmCliTests(unittest.TestCase):
    def test_catalog_check_cli(self):
        stdout = io.StringIO()
        stderr = io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            code = cli.run(["catalog-check", "--json"])
        self.assertEqual(code, 0)
        payload = json.loads(stdout.getvalue())
        self.assertEqual(payload["n_pairs"], N_PAIRS)
        self.assertEqual(payload["factory"], FACTORY)
        self.assertEqual(payload["mill_pairs"], MILL_PAIRS)
        self.assertEqual(stderr.getvalue(), "")

    def test_generate_cli_one_round(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "cli-out"
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                code = cli.run(["generate", "--out", str(dest), "--round", "1260", "--json"])
            self.assertEqual(code, 0)
            payload = json.loads(stdout.getvalue())
            self.assertEqual(payload["episodes"], 2)
            self.assertTrue((dest / "batch-r1260.jsonl").is_file())


if __name__ == "__main__":
    unittest.main()
