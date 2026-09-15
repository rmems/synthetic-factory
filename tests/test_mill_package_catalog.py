#!/usr/bin/env python3
"""Pinned mill catalog: load, digest, uniqueness, leftover-script refusal."""

import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from mill_package_test_support import (  # noqa: E402
    FIXTURE_CATALOG,
    catalog_load,
    refusal,
    vocabulary as cv,
)


class Load(unittest.TestCase):
    def test_committed_catalog_loads_sixty_unique_plants(self):
        loaded = catalog_load.load_catalog(FIXTURE_CATALOG)
        self.assertEqual(loaded.catalog_id, cv.CATALOG_ID)
        self.assertEqual(loaded.family, cv.FAMILY)
        self.assertEqual(loaded.plant_count, 60)
        self.assertEqual(len(loaded.plants), 60)
        self.assertEqual(loaded.plants_sha256, catalog_load.sha256_bytes(
            (FIXTURE_CATALOG / "plants.jsonl").read_bytes()
        ))
        self.assertEqual(loaded.plants[0].plant_id, "pm-serverid-bind")
        self.assertEqual(loaded.plants[0].provider, "Postmark")
        self.assertEqual(loaded.plants[0].identity_field, "MessageID")
        self.assertEqual(loaded.plants[0].event_field, "ServerID")

    def test_catalog_does_not_vendor_leftover_mill_scripts(self):
        text = (FIXTURE_CATALOG / "plants.jsonl").read_text(encoding="utf-8")
        header = (FIXTURE_CATALOG / "CATALOG.json").read_text(encoding="utf-8")
        for banned in cv.BANNED_SUBSTRINGS:
            self.assertNotIn(banned, text)
            self.assertNotIn(banned, header)
        repo = FIXTURE_CATALOG.parents[1]
        leftover = list(repo.glob("experiments/mill_leftover_leftover_leftover_*.py"))
        packaged = list((repo / "pipelines" / "mill").glob("*leftover*"))
        self.assertEqual(leftover, [])
        self.assertEqual(packaged, [])


class Refusals(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="mill-catalog-"))
        self.addCleanup(shutil.rmtree, self.root, True)

    def test_missing_dir_and_drifted_digest_are_refused(self):
        with refusal(self, cv.FINDING_CATALOG_FILE_MISSING):
            catalog_load.load_catalog(self.root / "missing")
        dest = self.root / "catalog"
        shutil.copytree(FIXTURE_CATALOG, dest)
        plants = dest / "plants.jsonl"
        plants.write_text(plants.read_text(encoding="utf-8") + "\n", encoding="utf-8")
        with refusal(self, cv.FINDING_PLANTS_SHA_MISMATCH, "digest"):
            catalog_load.load_catalog(dest)

    def test_a_leftover_token_in_a_plant_row_is_refused(self):
        dest = self.root / "catalog"
        shutil.copytree(FIXTURE_CATALOG, dest)
        plants = dest / "plants.jsonl"
        rows = plants.read_text(encoding="utf-8").splitlines()
        rows[0] = rows[0].replace("Postmark", "leftover leftover leftover")
        plants.write_text("\n".join(rows) + "\n", encoding="utf-8")
        header = dest / "CATALOG.json"
        payload = header.read_text(encoding="utf-8").replace(
            catalog_load.sha256_bytes((FIXTURE_CATALOG / "plants.jsonl").read_bytes()),
            catalog_load.sha256_bytes(plants.read_bytes()),
        )
        header.write_text(payload, encoding="utf-8")
        with refusal(self, cv.FINDING_BANNED_SUBSTRING, "leftover leftover leftover"):
            catalog_load.load_catalog(dest)


if __name__ == "__main__":
    unittest.main()
