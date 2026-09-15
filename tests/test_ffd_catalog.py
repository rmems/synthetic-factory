#!/usr/bin/env python3
"""AST extract fidelity and the committed FFD catalog pins."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from ffd_test_support import REPO, catalog, legacy_source


class NoVendor(unittest.TestCase):
    def test_the_tree_does_not_vendor_ffd_mill_scripts(self):
        hits = []
        for folder in (REPO / "pipelines", REPO / "config", REPO / "tests"):
            hits.extend(path for path in folder.rglob("ffd-mill*.py") if path.is_file())
        self.assertEqual(hits, [])


class ExtractFidelity(unittest.TestCase):
    def test_leftover3_pairs_match_ast_extract_from_legacy_commit(self):
        loaded = catalog.load_catalog()
        extracted = catalog.extract_leftover3(legacy_source("leftover3"))
        self.assertEqual(len(loaded.leftover3), 39)
        self.assertEqual([dict(row) for row in loaded.leftover3], extracted)
        self.assertEqual(extracted[0]["ok"]["slug"], "unleash-leftover-strategy-vs-pct")

    def test_lll_pairs_match_ast_extract_from_legacy_commit(self):
        loaded = catalog.load_catalog()
        extracted = catalog.extract_lll(legacy_source("lll"))
        self.assertEqual(len(loaded.lll), 16)
        self.assertEqual([dict(row) for row in loaded.lll], extracted)

    def test_hop_plants_and_pairs_match_ast_extract_from_legacy_commit(self):
        loaded = catalog.load_catalog()
        plants, pairs, banned = catalog.extract_hop(legacy_source("hop"))
        self.assertEqual(dict(loaded.hop_plants), plants)
        self.assertEqual([dict(row) for row in loaded.hop_pairs], pairs)
        self.assertEqual(loaded.banned_sub, banned)
        self.assertEqual(len(plants), 18)
        self.assertEqual(len(pairs), 9)

    def test_committed_source_pins_match_legacy_blobs(self):
        loaded = catalog.load_catalog()
        for source_id, path in catalog.SOURCE_PATHS.items():
            meta = loaded.meta["sources"][source_id]
            self.assertEqual(meta["path"], path)
            self.assertEqual(meta["sha256"], catalog.sha256_text(legacy_source(source_id)))


class CatalogCheck(unittest.TestCase):
    def test_committed_catalog_has_no_structural_findings(self):
        self.assertEqual(catalog.catalog_check(catalog.load_catalog()), [])


if __name__ == "__main__":
    unittest.main()
