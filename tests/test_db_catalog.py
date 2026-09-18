#!/usr/bin/env python3
"""Plant catalog load and uniqueness for the cleaned db mill."""

from __future__ import annotations

import contextlib
import io
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from pipelines.db import config as cfg  # noqa: E402
from pipelines.db.check import self_check  # noqa: E402
from pipelines.db.plant import REQUIRED_KEYS  # noqa: E402
from pipelines.db.plants import N_PAIRS, PLANTS  # noqa: E402
from pipelines.db.plants_01 import PLANTS_01  # noqa: E402
from pipelines.db.plants_02 import PLANTS_02  # noqa: E402
from pipelines.db.plants_03 import PLANTS_03  # noqa: E402


class CatalogLoad(unittest.TestCase):
    def test_assembled_catalog_loads_eighty_eight_plants(self):
        self.assertEqual((len(PLANTS_01), len(PLANTS_02), len(PLANTS_03)), (30, 30, 28))
        self.assertEqual(PLANTS, [*PLANTS_01, *PLANTS_02, *PLANTS_03])
        self.assertEqual((len(PLANTS), N_PAIRS), (88, 44))

    def test_every_plant_has_required_keys_and_a_known_engine(self):
        for plant in PLANTS:
            with self.subTest(slug=plant["slug"]):
                for key in REQUIRED_KEYS:
                    self.assertTrue(plant[key], key)
                self.assertIn(plant["engine"], cfg.ENGINES)
                eid = f"dbm-r{cfg.START_ROUND}-{plant['slug']}"
                self.assertIsNone(cfg.RECYCLE_SUFFIX.search(eid))
                for frag in cfg.BANNED_FRAGMENTS:
                    self.assertNotIn(frag, plant["slug"])


class CatalogUniqueness(unittest.TestCase):
    def test_slugs_plants_tables_surfaces_and_leftover_names_are_unique(self):
        slugs = [plant["slug"] for plant in PLANTS]
        names = [plant["plant"] for plant in PLANTS]
        tables = [plant["table"] for plant in PLANTS]
        surfaces = [plant["surface"] for plant in PLANTS]
        leftovers = [
            name for plant in PLANTS for name in (plant["leftover"], plant["leftover2"])
        ]
        self.assertEqual(len(set(slugs)), 88)
        self.assertEqual(len(set(names)), 88)
        self.assertEqual(len(set(tables)), 88)
        self.assertEqual(len(set(surfaces)), 88)
        self.assertEqual(len(set(leftovers)), 176)

    def test_self_check_accepts_the_assembled_catalog(self):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            self_check()
        self.assertIn("self_check ok: 44 pairs r845-r888", buf.getvalue())


if __name__ == "__main__":
    unittest.main()
