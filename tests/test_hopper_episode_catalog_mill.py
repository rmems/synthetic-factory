#!/usr/bin/env python3
"""AST-extracted ssl-mill-lll episode P() catalog under ``pipelines/hopper``."""

from __future__ import annotations

import ast
import json
import subprocess
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "pipelines"))

from hopper.catalog_episode_mill import (  # noqa: E402
    DEFAULT_MILL_CATALOG_DIR,
    EPISODE_MILL_SOURCE_PATHS,
    EPISODE_PAIRS_FILENAME,
    EPISODE_SHAPE,
    ast_extract_episode_mill_pairs,
    catalog_episode_mill_check,
    load_episode_mill_catalog,
)
from hopper.catalog_mill import (  # noqa: E402
    load_mill_catalog,
    sha256_bytes,
)

LEGACY_COMMIT = "813f93f1969c1c4421e5663492e9663739efa642"


def _legacy_source(relpath: str) -> str | None:
    for spec in (f"{LEGACY_COMMIT}:{relpath}", f"origin/legacy-mill-lane:{relpath}"):
        try:
            return subprocess.check_output(["git", "show", spec], text=True, cwd=REPO)
        except subprocess.CalledProcessError:
            continue
    return None


class HopperEpisodeCatalogLayoutTests(unittest.TestCase):
    def test_lll_mill_scripts_are_not_vendored(self):
        vendored = tuple(sorted(DEFAULT_MILL_CATALOG_DIR.glob("ssl-mill-lll*.py")))
        self.assertEqual(vendored, ())
        for path in EPISODE_MILL_SOURCE_PATHS:
            self.assertFalse((REPO / path).exists(), path)

    def test_episode_pairs_jsonl_is_one_object_per_line(self):
        payload = (DEFAULT_MILL_CATALOG_DIR / EPISODE_PAIRS_FILENAME).read_bytes()
        lines = payload.splitlines()
        self.assertEqual(len(lines), 192)
        for index, line in enumerate(lines, start=1):
            self.assertFalse(line.startswith(b" "), f"line {index} has leading whitespace")
            row = json.loads(line)
            self.assertEqual(row["shape"], EPISODE_SHAPE)
            self.assertIn("sdk", row["ok"])
            self.assertIn("leftover", row["ok"])

    def test_episode_catalog_check_loads_committed_slice(self):
        meta = catalog_episode_mill_check()
        self.assertEqual(meta["n_episode_pair_rows_committed"], 192)
        self.assertEqual(meta["n_episode_pair_rows_extracted"], 192)


class HopperEpisodeMillNeverExec(unittest.TestCase):
    BANNED_IMPORTS = frozenset({"subprocess", "importlib"})

    def test_catalog_episode_mill_module_has_no_banned_imports(self):
        path = DEFAULT_MILL_CATALOG_DIR / "catalog_episode_mill.py"
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    root = alias.name.split(".")[0]
                    self.assertNotIn(root, self.BANNED_IMPORTS, alias.name)
            elif isinstance(node, ast.ImportFrom) and node.module:
                root = node.module.split(".")[0]
                self.assertNotIn(root, self.BANNED_IMPORTS, node.module)


class HopperEpisodeMillReextractTests(unittest.TestCase):
    def test_committed_episode_rows_match_legacy_reextract(self):
        _, committed = load_episode_mill_catalog()
        live: list[dict] = []
        for path in EPISODE_MILL_SOURCE_PATHS:
            source = _legacy_source(path)
            if source is None:
                self.skipTest(f"legacy blob missing for {path}")
            live.extend(ast_extract_episode_mill_pairs(source, source_path=path))
        self.assertEqual(live, list(committed))

    def test_episode_slugs_do_not_overlap_tuple_pairs(self):
        _, tuple_rows = load_mill_catalog()
        _, episode_rows = load_episode_mill_catalog()
        tuple_slugs = {row[side]["slug"] for row in tuple_rows for side in ("ok", "bad")}
        episode_slugs = {row[side]["slug"] for row in episode_rows for side in ("ok", "bad")}
        self.assertFalse(tuple_slugs & episode_slugs)

    def test_episode_pairs_sha256_matches_file_bytes(self):
        meta, _ = load_episode_mill_catalog()
        payload = (DEFAULT_MILL_CATALOG_DIR / EPISODE_PAIRS_FILENAME).read_bytes()
        self.assertEqual(meta["episode_pairs_sha256"], sha256_bytes(payload))

    def test_header_lists_episode_mills_with_expected_counts(self):
        meta, _ = load_episode_mill_catalog()
        by_id = {item["mill_id"]: item for item in meta["mills"] if item["shape"] == EPISODE_SHAPE}
        self.assertEqual(by_id["ssl-mill-lll-r182"]["n_rows"], 16)
        self.assertEqual(by_id["ssl-mill-lll-r190"]["n_rows"], 16)
        self.assertEqual(by_id["ssl-mill-lll-r206"]["n_rows"], 80)
        self.assertEqual(by_id["ssl-mill-lll-r286"]["n_rows"], 80)


if __name__ == "__main__":
    unittest.main()
