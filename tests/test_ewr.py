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
    LEGACY_MAPPING_MILL,
    LEGACY_MAPPING_MILL_R59,
    LEGACY_MAPPING_MILL_R75,
    LEGACY_MAPPING_MILL_R91,
    LEGACY_MAPPING_MILL_SHA256,
    LEGACY_MILL,
    LEGACY_MILL_SHA256,
    LEGACY_PLANTS,
    LEGACY_PLANTS_SHA256,
    MAPPING_MILL_ID,
    N_MAPPING_PAIRS,
    N_PAIRS,
    N_PLANT_PAIRS,
    PAIRS_SHA256,
    PLANTS_MILL_ID,
    START_ROUND,
    SUCCESS_STEPS,
)
from ewr.catalog import (  # noqa: E402
    ast_extract_catalog_rows,
    ast_extract_mapping_pairs,
    ast_extract_mill_constants,
    ast_extract_plant_pairs,
    catalog_check,
    sha256_text,
)
from mill_reviewed_vocabulary import REVIEWED_MILL_PREFIX_HOMES  # noqa: E402
from raw_tree_guard import DEFAULT_RAW_OUTPUT_ROOT  # noqa: E402

EWR_DIR = REPO / "pipelines" / "ewr"
PACKAGE_FILES = (
    "__init__.py",
    "_contract.py",
    "catalog.py",
    "catalog_ast.py",
    "generate.py",
    "cli.py",
)


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

    def test_catalog_check_pins_thirty_two_pairs(self):
        loaded = catalog_check(root=REPO)
        self.assertEqual(loaded.factory, FACTORY)
        self.assertEqual(loaded.generator, GENERATOR)
        self.assertEqual(len(loaded.pairs), N_PLANT_PAIRS)
        self.assertEqual(len(loaded.mapping_pairs), N_MAPPING_PAIRS)
        self.assertEqual(loaded.pairs_sha256, PAIRS_SHA256)
        self.assertEqual(
            [pair.round_n for pair in loaded.pairs],
            list(range(START_ROUND, START_ROUND + N_PLANT_PAIRS)),
        )
        mapping_rounds = [pair.round_n for pair in loaded.mapping_pairs]
        self.assertEqual(len(mapping_rounds), N_MAPPING_PAIRS)
        self.assertEqual(mapping_rounds[:16], list(range(56, 72)))
        self.assertEqual(mapping_rounds[16:19], [72, 73, 74])
        self.assertEqual(mapping_rounds[19:35], list(range(75, 91)))
        self.assertEqual(mapping_rounds[35:], list(range(91, 107)))
        self.assertEqual(loaded.mills[0].mill_id, PLANTS_MILL_ID)
        self.assertEqual(loaded.mills[1].mill_id, MAPPING_MILL_ID)
        self.assertEqual(len(loaded.mills), 5)
        self.assertEqual(loaded.source["commit"], LEGACY_COMMIT)

    def test_pairs_jsonl_is_one_object_per_line(self):
        pairs_path = REPO / "config" / "ewr" / "pairs.jsonl"
        lines = pairs_path.read_text(encoding="utf-8").splitlines()
        self.assertEqual(len(lines), N_PAIRS)
        for line in lines:
            self.assertFalse(line[:1].isspace())
            self.assertIsInstance(json.loads(line), dict)

    def test_catalog_matches_legacy_ast_extract(self):
        plants = _legacy_source(LEGACY_PLANTS)
        mill = _legacy_source(LEGACY_MILL)
        mapping_paths = (
            LEGACY_MAPPING_MILL,
            LEGACY_MAPPING_MILL_R59,
            LEGACY_MAPPING_MILL_R75,
            LEGACY_MAPPING_MILL_R91,
        )
        mapping_sources = {path: _legacy_source(path) for path in mapping_paths}
        if plants is None or mill is None or any(mapping_sources[path] is None for path in mapping_paths):
            self.skipTest("legacy-mill-lane ewr sources are not available")
        self.assertEqual(sha256_text(plants), LEGACY_PLANTS_SHA256)
        self.assertEqual(sha256_text(mill), LEGACY_MILL_SHA256)
        self.assertEqual(sha256_text(mapping_sources[LEGACY_MAPPING_MILL]), LEGACY_MAPPING_MILL_SHA256)
        extracted = ast_extract_catalog_rows(plants, mill, mapping_sources)
        loaded = catalog_check(root=REPO)
        self.assertEqual(len(extracted), N_PAIRS)
        self.assertEqual(
            ast_extract_mill_constants(mill),
            {"FACTORY": FACTORY, "START": START_ROUND, "N": N_PLANT_PAIRS},
        )
        self.assertEqual(len(ast_extract_plant_pairs(plants)), N_PLANT_PAIRS)
        self.assertEqual(len(ast_extract_mapping_pairs(mapping_sources[LEGACY_MAPPING_MILL])), 16)
        pairs_path = REPO / "config" / "ewr" / "pairs.jsonl"
        committed = [json.loads(line) for line in pairs_path.read_text(encoding="utf-8").splitlines()]
        self.assertEqual(len(committed), len(extracted))
        for index, (raw, expected) in enumerate(zip(committed, extracted, strict=True)):
            self.assertEqual(raw["mill_id"], expected["mill_id"])
            self.assertEqual(raw["round"], expected["round"])
            if "ok" in expected:
                self.assertEqual(raw["ok"]["slug"], expected["ok"]["slug"])
                self.assertEqual(raw["bad"]["slug"], expected["bad"]["slug"])
                pair = loaded.pairs[index]
                self.assertEqual(dict(raw["ok"]), dict(pair.ok))
                self.assertEqual(dict(raw["bad"]), dict(pair.bad))
            else:
                self.assertEqual(raw["mapping"]["slug"], expected["mapping"]["slug"])
                mapping = loaded.mapping_pairs[index - N_PLANT_PAIRS]
                self.assertEqual(dict(raw["mapping"]), dict(mapping.mapping))
                self.assertEqual(raw["mapping"]["drop"], expected["mapping"]["drop"])

    def test_catalog_rejects_banned_r39_clones(self):
        loaded = catalog_check(root=REPO)
        joined = " ".join(
            f"{pair.ok['slug']} {pair.bad['slug']}" for pair in loaded.pairs
        )
        joined += " " + " ".join(
            f"{pair.mapping['slug']} {pair.mapping['fail']}" for pair in loaded.mapping_pairs
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

    def test_every_plant_pair_builds(self):
        loaded = catalog_check(root=REPO)
        built = gen.build_catalog(loaded)
        self.assertEqual(len(built), N_PLANT_PAIRS)
        ids = [item.ok["id"] for item in built] + [item.bad["id"] for item in built]
        self.assertEqual(len(set(ids)), 2 * N_PLANT_PAIRS)
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
        self.assertEqual(payload["pair_count"], N_PLANT_PAIRS)
        self.assertEqual(payload["mapping_pair_count"], N_MAPPING_PAIRS)
        self.assertEqual(payload["total_pairs"], N_PAIRS)
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
