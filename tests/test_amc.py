#!/usr/bin/env python3
"""Contracts for the AST-extracted, non-executable AMC catalog."""

import ast
import json
import tempfile
import unittest
from pathlib import Path

from pipelines.amc import (
    CATALOG,
    FACTORY,
    FAMILY_PREFIX,
    FORBIDDEN_MILL_GLOBS,
    GENERATOR,
    PRESERVE_COMMIT,
    QUOTA_PER_ROUND,
    SUCCESS_STEPS,
    CatalogError,
    is_vendor_filename,
    load_catalog,
    refuse_vendor_paths,
)
from pipelines.mill_reviewed_vocabulary import REVIEWED_MILL_PREFIX_HOMES

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "pipelines" / "amc"
CONFIG_DIR = ROOT / "config" / "amc"
CATALOG_JSON = CONFIG_DIR / "CATALOG.json"
PAIRS_JSONL = CONFIG_DIR / "pairs.jsonl"

EXTRACTED_COUNTS = {
    "amc-mill-r170": 59,
    "amc-mill-r229": 51,
    "amc-mill-r280": 36,
    "amc-mill-r316": 36,
    "amc-mill-r352": 72,
    "amc-mill-r424": 999,
    "amc-mill-r592": 16,
    "amc-mill-r608": 42,
    "amc-mill-r650": 38,
    "amc-mill-r688": 16,
    "amc-mill-r704": 20,
    "mill_amc_leftover_r688": 16,
}

FIRST_SLUGS = {
    "amc-mill-r170": "zeigarnik-drops-unfinished-pin",
    "amc-mill-r229": "state-dependent-tag-stripped",
    "amc-mill-r280": "state-dependent-tag-stripped",
    "amc-mill-r316": "cache-control-ephemeral-drops-pin",
    "amc-mill-r352": "marksweep-gc-drops-pin",
    "amc-mill-r424": "shenandoah-satb-drops-pin",
    "amc-mill-r592": "redis-volatile-ttl-leftover",
    "amc-mill-r608": "rocksdb-tombstone-seq-leftover",
    "amc-mill-r650": "alpine-apk-index-leftover",
    "amc-mill-r688": "mem0-entity-merge-leftover",
    "amc-mill-r704": "chromadb-where-doc-leftover",
    "mill_amc_leftover_r688": "airflow-xcom-backend-leftover-vs-drop-task",
}


class AmcCatalogTests(unittest.TestCase):
    def test_reviewed_prefix_maps_to_factory(self):
        self.assertEqual(REVIEWED_MILL_PREFIX_HOMES[FAMILY_PREFIX], FACTORY)
        self.assertEqual(FACTORY, "agent-memory-compaction-factory")
        self.assertEqual(GENERATOR, "grok-4.6")
        self.assertEqual(PRESERVE_COMMIT, "bb0775859c86d4692112c4845790fa1623ab8abb")
        self.assertEqual(QUOTA_PER_ROUND, 2)
        self.assertEqual(SUCCESS_STEPS, 16)

    def test_catalog_pins_extracted_counts_and_committed_identities(self):
        pairs = list(CATALOG.pairs())
        self.assertEqual(len(CATALOG.catalogs), 12)
        self.assertEqual(len(CATALOG.loops), 11)
        self.assertEqual(CATALOG.n_pair_rows_extracted, 1401)
        self.assertEqual(CATALOG.n_pair_rows_committed, 1401)
        self.assertEqual(len(pairs), 1401)
        self.assertEqual(sum(1 for pair in pairs if pair.role == "deferred"), 1377)
        self.assertEqual(sum(1 for pair in pairs if pair.role == "first"), 12)
        self.assertEqual(sum(1 for pair in pairs if pair.role == "last"), 12)
        self.assertEqual(
            {mill.mill_id: mill.n_rows_extracted for mill in CATALOG.catalogs},
            EXTRACTED_COUNTS,
        )
        self.assertEqual(
            {mill.mill_id: mill.first_slug for mill in CATALOG.catalogs},
            FIRST_SLUGS,
        )
        self.assertEqual(
            {mill.mill_id: len(mill.pairs) for mill in CATALOG.catalogs},
            EXTRACTED_COUNTS,
        )
        r280 = CATALOG.mills["amc-mill-r280"]
        self.assertEqual(r280.shape, "pairs-prefix-new")
        self.assertEqual(r280.n_prefix, 16)
        self.assertEqual(r280.n_new, 20)
        self.assertEqual(r280.prefix_mill, "amc-mill-r229")
        self.assertEqual(r280.last_slug, "korsakoff-drops-recent-pin")
        r424 = CATALOG.mills["amc-mill-r424"]
        self.assertEqual(r424.shape, "pairs-table-zip")
        self.assertEqual(r424.n_rows_extracted, 999)
        self.assertEqual(sum(1 for pair in r424.pairs if pair.role == "deferred"), 997)
        leftover = CATALOG.mills["mill_amc_leftover_r688"]
        self.assertEqual(leftover.shape, "leftover-dict")
        self.assertEqual(leftover.max_rounds, 16)
        self.assertIn("1377 deferred", CATALOG.extraction)

    def test_each_mill_keeps_bookends_and_unique_deferred_identities(self):
        for mill in CATALOG.catalogs:
            first_n = sum(1 for pair in mill.pairs if pair.role == "first")
            last_n = sum(1 for pair in mill.pairs if pair.role == "last")
            deferred_n = sum(1 for pair in mill.pairs if pair.role == "deferred")
            self.assertEqual(first_n, 1, mill.mill_id)
            self.assertEqual(last_n, 1, mill.mill_id)
            self.assertEqual(deferred_n, mill.n_rows_extracted - 2, mill.mill_id)
            identities = {(pair.fail_slug, pair.success_slug) for pair in mill.pairs}
            self.assertEqual(len(identities), mill.n_rows_extracted, mill.mill_id)
            first = next(pair for pair in mill.pairs if pair.role == "first")
            last = next(pair for pair in mill.pairs if pair.role == "last")
            if mill.kind == "leftover":
                self.assertEqual(first.success_slug, mill.first_slug)
                self.assertEqual(last.success_slug, mill.last_slug)
            else:
                self.assertEqual(first.fail_slug, mill.first_slug)
                self.assertEqual(last.fail_slug, mill.last_slug)

    def test_loop_pins_name_companion_mills(self):
        companions = {loop.companion_mill_path for loop in CATALOG.loops}
        expected = {f"experiments/amc-mill-r{n}.py" for n in (
            170, 229, 280, 316, 352, 424, 592, 608, 650, 688, 704,
        )}
        self.assertEqual(companions, expected)
        self.assertEqual({loop.mill_id for loop in CATALOG.loops}, {
            f"amc-loop-r{n}" for n in (170, 229, 280, 316, 352, 424, 592, 608, 650, 688, 704)
        })

    def test_no_vendored_mill_scripts(self):
        hits = []
        for pattern in FORBIDDEN_MILL_GLOBS:
            hits.extend(
                path for path in ROOT.rglob(pattern) if "legacy-mill-lane" not in str(path)
            )
        self.assertEqual(hits, [])
        self.assertTrue(is_vendor_filename("amc-mill-r170.py"))
        self.assertTrue(is_vendor_filename("amc-loop-r170.py"))
        self.assertTrue(is_vendor_filename("mill_amc_leftover_r688.py"))
        self.assertFalse(is_vendor_filename("catalog.py"))
        with self.assertRaises(SystemExit):
            refuse_vendor_paths([Path("experiments/amc-mill-r170.py")])

    def test_legacy_mills_are_not_vendored_or_executable(self):
        package_files = {path.name for path in PACKAGE.iterdir() if path.is_file()}
        self.assertEqual(package_files, {"__init__.py", "catalog.py"})
        forbidden_functions = {"main", "run_loop", "emit_stage", "publish_round"}
        for path in PACKAGE.glob("*.py"):
            source = path.read_text(encoding="utf-8")
            tree = ast.parse(source, filename=str(path))
            functions = {
                node.name
                for node in ast.walk(tree)
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            }
            imports = {
                alias.name
                for node in ast.walk(tree)
                if isinstance(node, (ast.Import, ast.ImportFrom))
                for alias in node.names
            }
            self.assertTrue(functions.isdisjoint(forbidden_functions))
            self.assertNotIn("subprocess", imports)
            self.assertNotIn("round_txn", imports)
            self.assertNotIn("outputs/raw", source)
            self.assertNotIn("exec(", source)
            self.assertNotIn("eval(", source)

    def test_pairs_jsonl_stays_compact(self):
        text = PAIRS_JSONL.read_text(encoding="utf-8")
        lines = text.splitlines()
        self.assertEqual(len(lines), 1401)
        self.assertTrue(text.endswith("\n"))
        self.assertNotIn("\r", text)
        bookend_roles = {json.loads(line)["role"] for line in lines[:24]}
        deferred_roles = {json.loads(line)["role"] for line in lines[24:]}
        self.assertEqual(bookend_roles, {"first", "last"})
        self.assertEqual(deferred_roles, {"deferred"})
        self.assertEqual(sum(1 for line in lines if '"amc-mill-r424"' in line), 999)
        for line in lines:
            self.assertFalse(line.startswith((" ", "\t")))
            self.assertNotIn("  ", line)
            json.loads(line)

    def test_loader_fails_closed_when_deferred_identities_are_dropped(self):
        header = json.loads(CATALOG_JSON.read_text(encoding="utf-8"))
        bookends = PAIRS_JSONL.read_text(encoding="utf-8").splitlines()[:24]
        with tempfile.TemporaryDirectory() as temp_dir:
            dest = Path(temp_dir)
            (dest / "CATALOG.json").write_text(json.dumps(header), encoding="utf-8")
            (dest / "pairs.jsonl").write_text("\n".join(bookends) + "\n", encoding="utf-8")
            with self.assertRaisesRegex(CatalogError, "committed 2 identities"):
                load_catalog(dest)

    def test_loader_fails_closed_on_a_missing_case_field(self):
        header = json.loads(CATALOG_JSON.read_text(encoding="utf-8"))
        lines = PAIRS_JSONL.read_text(encoding="utf-8").splitlines()
        first = json.loads(lines[0])
        del first["fail_slug"]
        lines[0] = json.dumps(first, separators=(",", ":"))
        with tempfile.TemporaryDirectory() as temp_dir:
            dest = Path(temp_dir)
            (dest / "CATALOG.json").write_text(json.dumps(header), encoding="utf-8")
            (dest / "pairs.jsonl").write_text("\n".join(lines) + "\n", encoding="utf-8")
            with self.assertRaisesRegex(CatalogError, "keys differ"):
                load_catalog(dest)


if __name__ == "__main__":
    unittest.main()
