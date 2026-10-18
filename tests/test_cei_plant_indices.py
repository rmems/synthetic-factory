#!/usr/bin/env python3
"""CEI catalog plant index contiguity refusals."""

from __future__ import annotations

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
FIXTURE = REPO / "tests" / "fixtures" / "cei"

sys.path.insert(0, str(REPO / "pipelines"))

from cei import catalog  # noqa: E402
from cei._contract import CeiRefusal  # noqa: E402


def _fixture_catalog_copy() -> Path:
    root = Path(tempfile.mkdtemp(prefix="cei-index-"))
    dest = root / "catalog"
    shutil.copytree(FIXTURE, dest)
    return dest


def _two_plant_catalog_with_gapped_index() -> Path:
    copy = _fixture_catalog_copy()
    meta_path = copy / catalog.CATALOG_FILENAME
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    meta.update(plant_count=2)
    meta["mills"][0]["plant_count"] = 2
    plants_path = copy / catalog.PLANTS_FILENAME
    first = json.loads(plants_path.read_text(encoding="utf-8").splitlines()[0])
    second = json.loads(json.dumps(first))
    second["index"] = 2
    second["ok"] = dict(second["ok"], slug="gap-index-two-ok")
    second["plant_id"] = "cei_r0001:gap-index-two-ok"
    second["bad"] = dict(second["bad"], slug="gap-index-two-bad")
    payload = "".join(
        json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n"
        for row in (first, second)
    )
    plants_path.write_text(payload, encoding="utf-8")
    meta["plants_sha256"] = catalog.sha256_bytes(payload.encode("utf-8"))
    meta_path.write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    return copy


class PlantIndexRefusalTests(unittest.TestCase):
    def setUp(self):
        self.copy = _two_plant_catalog_with_gapped_index()
        self.addCleanup(shutil.rmtree, self.copy.parent, True)

    def test_catalog_refuses_gapped_per_mill_indices(self):
        with self.assertRaises(CeiRefusal) as caught:
            catalog.load_catalog(self.copy)
        self.assertEqual(caught.exception.code, catalog.FINDING_PLANT_FIELD_INVALID)
        self.assertIn(
            "cei_r0001 indices must be exactly 0..n-1 with no duplicates or gaps",
            str(caught.exception),
        )


if __name__ == "__main__":
    unittest.main()
