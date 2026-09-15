#!/usr/bin/env python3
"""Contracts for the AST-extracted, non-executable RLB catalog."""

import ast
import json
import tempfile
import unittest
from pathlib import Path

from pipelines.rlb import CATALOG, CatalogError, load_catalog

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "pipelines" / "rlb"
CONFIG_DIR = ROOT / "config" / "rlb"
CATALOG_JSON = CONFIG_DIR / "CATALOG.json"
PAIRS_JSONL = CONFIG_DIR / "pairs.jsonl"

SOURCE_PROVENANCE = {
    "experiments/rlb_leftover3_mill.py": (
        82,
        97,
        1120,
        "0c5849e3fa3aff254e6088f797330d24e6de5c9e",
        "9a8385e5aeb33d722ca9371c72532e157f7e9cf2e5f0cf87fc84b9f4a07c17d2",
    ),
    "experiments/rlb_r98_leftover3_mill.py": (
        98,
        113,
        745,
        "357a0a113389063b5b3e4192d633da69265c2ad9",
        "537e88cb1defbb1680065878db346c84d156fb0b5b07f9fb5bb5f958d94cde32",
    ),
    "experiments/rlb_r114_leftover3_mill.py": (
        119,
        134,
        741,
        "8c0de1c544c6022227eadaf836f7d8fac0ddb85b",
        "5ff569d7863446d58be133ecfa974a30570eddabff1fbd0dfc2f4c6d09c5163c",
    ),
    "experiments/rlb-mill-lll-r141.py": (
        141,
        156,
        1129,
        "70523e27577fab5a1486b2ec49092a030cd58128",
        "3de87e900098a33c7b10562654048c1c991ab8d2db82020de1a6cd3bdc7947be",
    ),
}


class RlbCatalogTests(unittest.TestCase):
    def test_catalog_preserves_all_ast_extracted_case_counts(self):
        pairs = list(CATALOG.pairs())
        record_ids = list(CATALOG.record_ids())

        self.assertEqual(len(CATALOG.catalogs), 4)
        self.assertEqual(len(pairs), 64)
        self.assertEqual(len(record_ids), 128)
        self.assertEqual(len(record_ids), len(set(record_ids)))
        self.assertEqual(sum(source.source_lines for source in CATALOG.catalogs), 3735)

    def test_source_ranges_and_hashes_pin_the_legacy_ast_inputs(self):
        observed = {
            source.source_path: (
                source.start_round,
                source.end_round,
                source.source_lines,
                source.source_blob_sha1,
                source.source_sha256,
            )
            for source in CATALOG.catalogs
        }
        self.assertEqual(observed, SOURCE_PROVENANCE)
        self.assertEqual(
            CATALOG.source_commit,
            "5c0d98a161e5b3f5df89042fd23dfa872b6bac5b",
        )
        self.assertIn("never imported or executed", CATALOG.extraction)

    def test_each_round_has_one_success_and_one_handoff_case(self):
        rounds = set()
        tickets = set()
        for pair in CATALOG.pairs():
            rounds.add(pair.round)
            self.assertNotEqual(pair.success.slug, pair.handoff.slug)
            self.assertTrue(pair.success.docs[0].startswith("https://"))
            self.assertTrue(pair.handoff.docs[1].startswith("https://"))
            self.assertGreaterEqual(pair.success.coverage, 0)
            self.assertLessEqual(pair.handoff.coverage, 100)
            self.assertNotIn(pair.handoff.ticket, tickets)
            tickets.add(pair.handoff.ticket)

        self.assertEqual(len(rounds), 64)
        self.assertEqual(len(tickets), 64)
        self.assertTrue(rounds.isdisjoint({114, 115, 116, 117, 118, 135, 136, 137, 138, 139, 140}))

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

    def test_pairs_jsonl_stays_compact(self):
        text = PAIRS_JSONL.read_text(encoding="utf-8")
        lines = text.splitlines()
        self.assertEqual(len(lines), 64)
        self.assertTrue(text.endswith("\n"))
        self.assertNotIn("\r", text)
        for line in lines:
            self.assertFalse(line.startswith((" ", "\t")))
            json.loads(line)

    def test_loader_fails_closed_on_a_missing_case_field(self):
        header = json.loads(CATALOG_JSON.read_text(encoding="utf-8"))
        lines = PAIRS_JSONL.read_text(encoding="utf-8").splitlines()
        first = json.loads(lines[0])
        del first["success"]["header"]
        lines[0] = json.dumps(first, separators=(",", ":"))

        with tempfile.TemporaryDirectory() as temp_dir:
            dest = Path(temp_dir)
            (dest / "CATALOG.json").write_text(json.dumps(header), encoding="utf-8")
            (dest / "pairs.jsonl").write_text("\n".join(lines) + "\n", encoding="utf-8")
            with self.assertRaisesRegex(CatalogError, "keys differ"):
                load_catalog(dest)


if __name__ == "__main__":
    unittest.main()
