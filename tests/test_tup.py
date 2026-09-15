#!/usr/bin/env python3
"""TUP catalog package: pins, AST extract, generate, no vendored mills."""

from __future__ import annotations

import ast
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PIPELINES = REPO / "pipelines"
COMMITTED = REPO / "config" / "tup"

sys.path.insert(0, str(PIPELINES))
sys.path.insert(0, str(REPO))

from mill_family import REVIEWED_MILL_PREFIX_HOMES  # noqa: E402
from mill_signals import mill_prefix  # noqa: E402
from record_kind import classify_kind, preference_side_kinds  # noqa: E402
from tup import catalog, catalog_extract, cli, generate  # noqa: E402
from tup._contract import (  # noqa: E402
    FACTORY,
    FINDING_DESTINATION_EXISTS,
    FINDING_DESTINATION_UNDER_RAW,
    FINDING_DESTINATION_VENDOR,
    FINDING_PLANT_NOT_FOUND,
    FINDING_PLANTS_SHA_MISMATCH,
    FINDING_SOURCE_NOT_PARSEABLE,
    FINDING_USAGE,
    GENERATOR,
    MILL_PREFIX,
    SOURCE_COMMIT,
    SOURCE_PATH,
    SOURCE_SHA256,
    TupRefusal,
    refuse_vendor_path,
)


def invoke(argv: list[str]) -> tuple[int, str, str]:
    proc = subprocess.run(
        [sys.executable, "-m", "tup.cli", *argv],
        cwd=str(PIPELINES),
        capture_output=True,
        text=True,
        check=False,
    )
    return proc.returncode, proc.stdout, proc.stderr


class CatalogPins(unittest.TestCase):
    def test_committed_catalog_loads_and_matches_registry(self):
        loaded = catalog.load_catalog(COMMITTED)
        self.assertEqual(loaded.catalog_id, "tup-v2")
        self.assertEqual(loaded.factory, FACTORY)
        self.assertEqual(loaded.meta["generator"], GENERATOR)
        self.assertNotEqual(GENERATOR, "grok-4.6")
        self.assertEqual(len(loaded.families), 138)
        self.assertEqual(len(loaded.plants), 3237)
        self.assertEqual(loaded.meta["source_commit"], catalog_extract.PRESERVE_COMMIT)
        r1349_plants = tuple(p for p in loaded.plants if p.mill_id == catalog.SLICE_MILL)
        self.assertEqual(len(r1349_plants), 414)
        self.assertEqual(r1349_plants[0].slug, "xsltproc-xinclude")
        self.assertEqual(r1349_plants[-1].slug, "liquibase-changelog-sync-sql")
        self.assertEqual(REVIEWED_MILL_PREFIX_HOMES[MILL_PREFIX], FACTORY)

    def test_families_pin_matches_bytes(self):
        payload = (COMMITTED / "families.jsonl").read_bytes()
        digest = hashlib.sha256(payload).hexdigest()
        loaded = catalog.load_catalog(COMMITTED)
        self.assertEqual(digest, loaded.families_sha256)
        self.assertEqual(digest, loaded.meta["families_sha256"])

    def test_pin_mismatch_is_a_coded_refusal(self):
        root = Path(tempfile.mkdtemp(prefix="tup-pin-"))
        self.addCleanup(shutil.rmtree, root, True)
        dest = root / "catalog"
        shutil.copytree(COMMITTED, dest)
        meta_path = dest / catalog.CATALOG_FILENAME
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        meta["families_sha256"] = "0" * 64
        meta_path.write_text(json.dumps(meta, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        with self.assertRaises(TupRefusal) as caught:
            catalog.load_catalog(dest)
        self.assertEqual(caught.exception.code, FINDING_PLANTS_SHA_MISMATCH)

    def test_unknown_plant_is_a_coded_refusal(self):
        loaded = catalog.load_catalog(COMMITTED)
        with self.assertRaises(TupRefusal) as caught:
            loaded.plant("missing-slug")
        self.assertEqual(caught.exception.code, FINDING_PLANT_NOT_FOUND)


class FourthSliceExtract(unittest.TestCase):
    def _mill_source_or_skip(self, path: str) -> str:
        try:
            return catalog_extract.git_show_mill(path)
        except TupRefusal as exc:
            if exc.code == FINDING_SOURCE_NOT_PARSEABLE and "not fetchable" in str(exc):
                self.skipTest(f"legacy-mill-lane mill source is not fetchable: {path}")
            raise

    def test_r1743_rows_extract_count(self):
        source = self._mill_source_or_skip("experiments/tup-mill-r1743.py")
        rows = catalog_extract.plant_rows_from_source(source, mill_id="tup_r1743")
        self.assertEqual(len(rows), 118)

    def test_leftover_triples_rounds_extract_count(self):
        source = self._mill_source_or_skip("experiments/tup-mill-leftover-triples.py")
        rows = catalog_extract.round_plants_from_source(source, mill_id="tup_leftover_triples")
        self.assertEqual(len(rows), 48)

    def test_leftover4_plants_extract_count(self):
        source = self._mill_source_or_skip("experiments/tup-mill-leftover4-r1576.py")
        rows = catalog_extract.leftover_plants_from_source(source, mill_id="tup_leftover4_r1576")
        self.assertEqual(len(rows), 36)

    def test_committed_fourth_slice_mill_plant_totals(self):
        loaded = catalog.load_catalog(COMMITTED)
        fourth_ids = {
            "tup_r1743",
            "tup_r1782",
            "tup_r1810",
            "tup_r1830",
            "tup_r1848",
            "tup_r2106",
            "tup_r2133",
            "tup_r2153",
            "tup_r2335",
            "tup_leftover_triples",
            "tup_leftover4_r1576",
            "tup_leftover_lll_r1594",
        }
        by_mill = {
            row["mill_id"]: row["plants"]
            for row in loaded.meta["mills"]
            if isinstance(row, dict) and row.get("mill_id") in fourth_ids
        }
        expected = {
            "tup_r1743": 99,
            "tup_r1782": 76,
            "tup_r1810": 60,
            "tup_r1830": 56,
            "tup_r1848": 58,
            "tup_r2106": 82,
            "tup_r2133": 63,
            "tup_r2153": 52,
            "tup_r2335": 68,
            "tup_leftover_triples": 48,
            "tup_leftover4_r1576": 36,
            "tup_leftover_lll_r1594": 46,
        }
        self.assertEqual(by_mill, expected)
        self.assertEqual(loaded.meta["slice"], "tup-fourth-slice")


class SecondSliceExtract(unittest.TestCase):
    def _mill_source_or_skip(self, path: str) -> str:
        try:
            return catalog_extract.git_show_mill(path)
        except TupRefusal as exc:
            if exc.code == FINDING_SOURCE_NOT_PARSEABLE and "not fetchable" in str(exc):
                self.skipTest(f"legacy-mill-lane mill source is not fetchable: {path}")
            raise

    def test_r1485_family_extract_matches_committed_file(self):
        source = self._mill_source_or_skip("experiments/tup-mill-r1485.py")
        rows = catalog_extract.family_rows_from_source(source)
        committed = [
            json.loads(line)
            for line in (COMMITTED / "families-r1485.jsonl").read_text(encoding="utf-8").splitlines()
            if line
        ]
        self.assertEqual(len(rows), len(committed))
        self.assertEqual(rows, committed)

    def test_r2170_specs_extract_count(self):
        source = self._mill_source_or_skip("experiments/tup-mill-r2170.py")
        rows = catalog_extract.plant_rows_from_source(source, mill_id="tup_r2170")
        self.assertEqual(len(rows), 263)


class AstExtract(unittest.TestCase):
    def test_families_from_source_reads_extra_catalog(self):
        source = (
            "def extra_catalog():\n"
            "    families = [\n"
            "        ('htmlq', '/plant/htmlq/page.html', 'article', [\n"
            "            ('text', \"-t 'article' page.html | head\", 'rm -f page.html'),\n"
            "        ]),\n"
            "    ]\n"
        )
        families = catalog.families_from_source(source)
        self.assertEqual(len(families), 1)
        self.assertEqual(families[0].bin, "htmlq")
        plants = catalog.expand_families(families, banned_slugs=(), banned_prefix=())
        self.assertEqual(plants[0].slug, "htmlq-text")
        self.assertEqual(plants[0].verify, "htmlq -t 'article' page.html | head")
        self.assertEqual(plants[0].wait, 3)

    def test_families_from_source_refuses_a_non_literal(self):
        source = (
            "def extra_catalog():\n"
            "    families = [(other(), '/p', 'g', [('t', 'v', 'd')])]\n"
        )
        with self.assertRaises(TupRefusal) as caught:
            catalog.families_from_source(source)
        self.assertEqual(caught.exception.code, FINDING_SOURCE_NOT_PARSEABLE)

    def test_expand_applies_r1349_bans(self):
        families = catalog.families_from_source(
            "def extra_catalog():\n"
            "    families = [\n"
            "        ('yq', '/plant/yq/f', 'k', [('eval', '-e .', 'rm -f /plant/yq/f')]),\n"
            "        ('htmlq', '/plant/htmlq/p', 'a', [('text', '-t a p', 'rm -f p')]),\n"
            "    ]\n"
        )
        plants = catalog.expand_families(
            families, banned_slugs=(), banned_prefix=("yq-",)
        )
        self.assertEqual([plant.slug for plant in plants], ["htmlq-text"])

    def test_committed_catalog_matches_legacy_ast(self):
        try:
            text = catalog.git_show_source(SOURCE_PATH)
        except TupRefusal as exc:
            if exc.code == FINDING_SOURCE_NOT_PARSEABLE and "not fetchable" in str(exc):
                self.skipTest("legacy-mill-lane pin is not fetchable")
            raise
        families = catalog.families_from_source(text)
        loaded = catalog.load_catalog(COMMITTED)
        self.assertEqual(len(families), 138)
        self.assertEqual(
            [(fam.bin, fam.keep, fam.grep, fam.cmds) for fam in families],
            [(fam.bin, fam.keep, fam.grep, fam.cmds) for fam in loaded.families],
        )
        plants = catalog.expand_families(
            families,
            banned_slugs=loaded.meta["banned_slugs"],
            banned_prefix=loaded.meta["banned_prefix"],
        )
        loaded_r1349 = tuple(p for p in loaded.plants if p.mill_id == catalog.SLICE_MILL)
        self.assertEqual([plant.slug for plant in plants], [plant.slug for plant in loaded_r1349])
        self.assertIn("Never", catalog.git_show_source.__doc__ or "")
        self.assertEqual(SOURCE_COMMIT, "dba9f9a1d0e984e58fc14c992228f09534c26d57")
        self.assertEqual(SOURCE_SHA256, hashlib.sha256(text.encode("utf-8")).hexdigest())

    def test_package_tree_has_no_vendored_mill_scripts(self):
        package = PIPELINES / "tup"
        hits = list(package.rglob("tup-mill*.py"))
        hits.extend(package.rglob("tup-loop*.py"))
        hits.extend(COMMITTED.rglob("*mill*.py"))
        self.assertEqual(hits, [])
        names = tuple(sorted(path.name for path in package.iterdir() if path.suffix == ".py"))
        self.assertEqual(
            names,
            (
                "__init__.py",
                "_contract.py",
                "catalog.py",
                "catalog_extract.py",
                "cli.py",
                "generate.py",
            ),
        )

    def test_package_has_no_exec_eval_compile(self):
        for path in (PIPELINES / "tup").glob("*.py"):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            calls = [
                node.func.id
                for node in ast.walk(tree)
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
            ]
            self.assertNotIn("exec", calls, path.name)
            self.assertNotIn("eval", calls, path.name)
            self.assertNotIn("compile", calls, path.name)


class GeneratePairs(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="tup-gen-"))
        self.addCleanup(shutil.rmtree, self.root, True)

    def test_one_plant_is_a_preference_and_not_hosted_grok(self):
        dest = self.root / "out"
        summary = generate.run(
            generate.GenerateRequest(COMMITTED, dest, plant_id="xsltproc-xinclude", round=1349)
        )
        self.assertEqual(summary["records"], 1)
        self.assertEqual(summary["generator"], GENERATOR)
        self.assertNotEqual(GENERATOR, "grok-4.6")
        record = json.loads((dest / generate.RECORDS_FILENAME).read_text(encoding="utf-8"))
        self.assertEqual(record["id"], "tup-r1349-xsltproc-xinclude")
        self.assertEqual(classify_kind(record), "preference")
        self.assertEqual(preference_side_kinds(record), ("episode", "episode"))
        self.assertEqual(mill_prefix(record), "tup")
        self.assertEqual(record["meta"]["factory"], FACTORY)
        self.assertEqual(record["meta"]["generator"], GENERATOR)
        self.assertNotEqual(record["meta"]["generator"], "grok-4.6")
        self.assertEqual(len(record["chosen"]["steps"]), 8)
        self.assertEqual(len(record["rejected"]["steps"]), 8)
        self.assertTrue(record["chosen"]["reward"]["success"])
        self.assertFalse(record["rejected"]["reward"]["success"])
        self.assertNotIn("Check designed checkout", record["goal"])
        notes = (dest / generate.NOTES_FILENAME).read_text(encoding="utf-8")
        self.assertIn("not grok-4.6", notes)

    def test_raw_destination_is_refused(self):
        dest = REPO / "outputs" / "raw" / "tup-should-not-write"
        with self.assertRaises(TupRefusal) as caught:
            generate.run(generate.GenerateRequest(COMMITTED, dest, plant_id="xsltproc-xinclude"))
        self.assertEqual(caught.exception.code, FINDING_DESTINATION_UNDER_RAW)
        self.assertFalse(dest.exists())

    def test_existing_destination_is_refused(self):
        dest = self.root / "exists"
        dest.mkdir()
        with self.assertRaises(TupRefusal) as caught:
            generate.run(generate.GenerateRequest(COMMITTED, dest, plant_id="xsltproc-xinclude"))
        self.assertEqual(caught.exception.code, FINDING_DESTINATION_EXISTS)

    def test_vendor_destination_is_refused(self):
        dest = self.root / "tup-mill-r1349.py"
        with self.assertRaises(TupRefusal) as caught:
            refuse_vendor_path(dest)
        self.assertEqual(caught.exception.code, FINDING_DESTINATION_VENDOR)

    def test_usage_requires_plant_or_all(self):
        dest = self.root / "usage"
        with self.assertRaises(TupRefusal) as caught:
            generate.run(generate.GenerateRequest(COMMITTED, dest))
        self.assertEqual(caught.exception.code, FINDING_USAGE)


class CliTests(unittest.TestCase):
    def test_catalog_check_json(self):
        code, stdout, stderr = invoke(["catalog-check", "--json"])
        self.assertEqual(code, 0, stderr)
        payload = json.loads(stdout)
        self.assertEqual(payload["status"], "ok")
        self.assertEqual(payload["plants"], 3237)
        self.assertEqual(payload["families"], 138)

    def test_generate_one_plant_json(self):
        root = Path(tempfile.mkdtemp(prefix="tup-cli-"))
        self.addCleanup(shutil.rmtree, root, True)
        dest = root / "fresh"
        code, stdout, stderr = invoke(
            ["generate", "--out", str(dest), "--plant", "htmlq-text", "--round", "1349", "--json"]
        )
        self.assertEqual(code, 0, stderr)
        payload = json.loads(stdout)
        self.assertEqual(payload["status"], "ok")
        self.assertEqual(payload["summary"]["records"], 1)
        self.assertEqual(payload["summary"]["generator"], GENERATOR)

    def test_package_and_flat_imports_are_one_object(self):
        import tup as flat
        from pipelines import tup as packaged

        self.assertIs(packaged, flat)
        self.assertIs(packaged.catalog, catalog)


if __name__ == "__main__":
    unittest.main()
