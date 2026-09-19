#!/usr/bin/env python3
"""ACTF compact mill catalog: pinned JSONL and live recover-grok re-extract."""

from __future__ import annotations

import subprocess
import unittest
from pathlib import Path

from actf_test_support import REPO, cv
from actf import catalog as cat

ACTF_DIR = REPO / "pipelines" / "actf"
RECOVER_REF = "origin/codex/recover-grok-01a06111"
RECOVER_COMMIT = "e5206e72fa829931162944648e1e180949baaf0b"
RECOVER_TREE = (
    "recovery/grok-session-01a06111-1b84-7250-aec4-9d120db6c1a4/"
    "recovered_sources/by-original-path"
)


class CatalogPinned(unittest.TestCase):
    def test_committed_catalog_loads_and_checks(self):
        loaded = cat.load_catalog()
        summary = cat.catalog_check(loaded)
        self.assertEqual(summary["status"], "ok")
        self.assertEqual(summary["catalog_id"], cv.CATALOG_ID)
        self.assertEqual(summary["lineages"], 63)
        self.assertEqual(summary["recovery_lineages"], 68)
        self.assertEqual(summary["helper_lineages_excluded"], 5)
        self.assertEqual(summary["excluded"], 7)
        self.assertEqual(summary["exact_kept"], 43)

    def test_catalog_dir_has_no_vendored_mill_scripts(self):
        names = {path.name for path in ACTF_DIR.iterdir()}
        self.assertIn("CATALOG.json", names)
        self.assertIn("lineages.jsonl", names)
        self.assertEqual(list(ACTF_DIR.glob("*mill*.py")), [])
        self.assertFalse(any("mill" in name for name in names if name.endswith(".py")))

    def test_pinned_catalog_includes_recovered_r10(self):
        pinned = cat.load_catalog().lineage("actf-r10--fd6829e8acef")
        self.assertEqual(pinned.classification, cv.CLASSIFICATION_EXACT)
        self.assertFalse(pinned.excluded)
        self.assertEqual(pinned.canonical_version, "v0001")
        self.assertEqual(len(pinned.source_sha256 or ""), 64)


class CatalogLiveExtract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._have_ref = subprocess.run(
            ["git", "rev-parse", "--verify", RECOVER_REF],
            cwd=REPO,
            capture_output=True,
            check=False,
        ).returncode == 0

    def test_live_recover_tree_matches_the_committed_row_set(self):
        if not self._have_ref:
            self.skipTest(f"{RECOVER_REF} is not available locally")
        listing = subprocess.run(
            [
                "git",
                "ls-tree",
                "-d",
                "--name-only",
                RECOVER_COMMIT,
                f"{RECOVER_TREE}/",
            ],
            cwd=REPO,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.splitlines()
        actf_dirs = sorted(
            Path(name).name for name in listing if Path(name).name.startswith("actf-")
        )
        self.assertEqual(len(actf_dirs), 68)
        pinned = {row.path_key for row in cat.load_catalog().lineages}
        helper_keys = set(cat.load_catalog().meta["helper_path_keys"])
        self.assertFalse(pinned & helper_keys)
        self.assertEqual(pinned | helper_keys, set(actf_dirs))

    def test_git_show_canonical_row_matches_fixture_r10_shape(self):
        if not self._have_ref:
            self.skipTest(f"{RECOVER_REF} is not available locally")
        source = subprocess.run(
            [
                "git",
                "show",
                f"{RECOVER_COMMIT}:{RECOVER_TREE}/actf-r10--fd6829e8acef/versions/v0001/gen.py",
            ],
            cwd=REPO,
            capture_output=True,
            text=True,
            check=True,
        ).stdout
        from actf import ast_scan

        result = ast_scan.scan_source(source, filename="gen.py")
        self.assertEqual(result.syntax_status, cv.SYNTAX_OK)
        self.assertIn(cv.FACTORY, result.features.factory_literals if result.features else ())
        pinned = cat.load_catalog().lineage("actf-r10--fd6829e8acef")
        self.assertEqual(pinned.canonical_version, "v0001")
        self.assertEqual(pinned.source_sha256, result.source_sha256)
        self.assertFalse(pinned.excluded)
        self.assertIn("ep1", pinned.episode_functions)


class CatalogContract(unittest.TestCase):
    def test_source_and_legacy_pins(self):
        self.assertEqual(cv.SOURCE_REF, RECOVER_REF)
        self.assertEqual(cv.SOURCE_COMMIT, RECOVER_COMMIT)
        self.assertEqual(cv.LEGACY_COMMIT, "813f93f1969c1c4421e5663492e9663739efa642")
        self.assertEqual(cv.LEGACY_REF, "origin/legacy-mill-lane")

    def test_helper_basenames_are_refused_as_mill_catalog(self):
        self.assertFalse(cv.is_mill_catalog_basename("gen_hold.py"))
        self.assertFalse(cv.is_mill_catalog_basename("_eps.py"))
        self.assertTrue(cv.is_mill_catalog_basename("gen.py"))
        self.assertTrue(cv.is_mill_catalog_basename("gen_r62.py"))


if __name__ == "__main__":
    unittest.main()
