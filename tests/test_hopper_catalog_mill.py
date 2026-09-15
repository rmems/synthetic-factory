#!/usr/bin/env python3
"""AST-extracted ssl hopper mill catalog under ``pipelines/hopper``."""

from __future__ import annotations

import ast
import json
import subprocess
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "pipelines"))

from hopper.catalog_mill import (  # noqa: E402
    CATALOG_FILENAME,
    DEFAULT_MILL_CATALOG_DIR,
    MILL_SOURCE_PATHS,
    PAIRS_FILENAME,
    ast_extract_mill_pairs,
    catalog_mill_check,
    load_mill_catalog,
    sha256_bytes,
)

LEGACY_COMMIT = "813f93f1969c1c4421e5663492e9663739efa642"
BANNED_QBP_SLUGS = frozenset({"disruptor-buffer-vs-timeout", "chronicle-cycle-handoff"})


def _legacy_source(relpath: str) -> str | None:
    for spec in (f"{LEGACY_COMMIT}:{relpath}", f"origin/legacy-mill-lane:{relpath}"):
        try:
            return subprocess.check_output(["git", "show", spec], text=True, cwd=REPO)
        except subprocess.CalledProcessError:
            continue
    return None


class HopperMillCatalogLayoutTests(unittest.TestCase):
    def test_ssl_mill_scripts_are_not_vendored(self):
        vendored = tuple(sorted(DEFAULT_MILL_CATALOG_DIR.glob("ssl-mill*.py")))
        self.assertEqual(vendored, ())
        for path in MILL_SOURCE_PATHS:
            self.assertFalse((REPO / path).exists(), path)

    def test_pairs_jsonl_is_one_object_per_line(self):
        payload = (DEFAULT_MILL_CATALOG_DIR / PAIRS_FILENAME).read_bytes()
        lines = payload.splitlines()
        self.assertEqual(len(lines), 111)
        for index, line in enumerate(lines, start=1):
            self.assertFalse(line.startswith(b" "), f"line {index} has leading whitespace")
            self.assertFalse(line.endswith(b"\r"), f"line {index} has CR")
            row = json.loads(line)
            self.assertIn("ok", row)
            self.assertIn("bad", row)

    def test_catalog_check_loads_committed_slice(self):
        meta = catalog_mill_check()
        self.assertEqual(meta["n_pair_rows_committed"], 111)
        self.assertEqual(meta["n_pair_rows_extracted"], 111)
        self.assertEqual(len(meta["mills"]), 3)


class HopperMillNeverExec(unittest.TestCase):
    BANNED_IMPORTS = frozenset({"subprocess", "importlib"})

    def test_catalog_mill_module_has_no_banned_imports(self):
        path = DEFAULT_MILL_CATALOG_DIR / "catalog_mill.py"
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    root = alias.name.split(".")[0]
                    self.assertNotIn(root, self.BANNED_IMPORTS, alias.name)
            elif isinstance(node, ast.ImportFrom) and node.module:
                root = node.module.split(".")[0]
                self.assertNotIn(root, self.BANNED_IMPORTS, node.module)


class HopperMillReextractTests(unittest.TestCase):
    def test_r35_pairs_are_new_vs_wave1_ssl_plants(self):
        wave1 = {
            json.loads(line)["slug"]
            for line in (REPO / "config" / "hopper" / "plants.jsonl").read_text(encoding="utf-8").splitlines()
            if line
        }
        source = _legacy_source("experiments/ssl-mill-r35.py")
        if source is None:
            self.skipTest("legacy ssl-mill-r35 blob is not fetched")
        extracted = ast_extract_mill_pairs(source, source_path="experiments/ssl-mill-r35.py")
        self.assertEqual(len(extracted), 71)
        slugs = {row["ok"]["slug"] for row in extracted} | {row["bad"]["slug"] for row in extracted}
        self.assertFalse(slugs & wave1)

    def test_committed_rows_match_legacy_reextract(self):
        _, committed = load_mill_catalog()
        live: list[dict] = []
        for path in MILL_SOURCE_PATHS:
            source = _legacy_source(path)
            if source is None:
                self.skipTest(f"legacy blob missing for {path}")
            live.extend(ast_extract_mill_pairs(source, source_path=path))
        self.assertEqual(live, list(committed))

    def test_banned_qbp_slugs_are_absent(self):
        _, rows = load_mill_catalog()
        slugs = {row[side]["slug"] for row in rows for side in ("ok", "bad")}
        self.assertFalse(slugs & BANNED_QBP_SLUGS)

    def test_pairs_sha256_matches_file_bytes(self):
        meta, _ = load_mill_catalog()
        payload = (DEFAULT_MILL_CATALOG_DIR / PAIRS_FILENAME).read_bytes()
        self.assertEqual(meta["pairs_sha256"], sha256_bytes(payload))

    def test_header_lists_three_mills_with_expected_counts(self):
        meta, _ = load_mill_catalog()
        by_id = {item["mill_id"]: item for item in meta["mills"]}
        self.assertEqual(by_id["ssl-mill-r35"]["n_rows"], 71)
        self.assertEqual(by_id["ssl-mill-r112"]["n_rows"], 20)
        self.assertEqual(by_id["ssl-mill-r132"]["n_rows"], 20)


if __name__ == "__main__":
    unittest.main()
