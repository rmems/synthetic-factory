#!/usr/bin/env python3
"""Hopper catalog schema, uniqueness, and START/PAIRS-by-factory."""

from __future__ import annotations

import hashlib
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from hopper_test_support import CATALOG, refusal  # noqa: E402

import hopper
from hopper import plants as hp
from hopper._contract import FINDING_PLANTS_SHA_MISMATCH, FINDING_UNKNOWN_WAVE


class HopperPlantsTests(unittest.TestCase):
    def test_catalog_counts_include_g46c(self):
        catalog = hp.load_catalog()
        self.assertEqual(catalog.meta["plants"], 152)
        self.assertEqual(len(catalog.pairs), 76)
        g46c = [row for row in catalog.pairs if row.wave == "g46c"]
        self.assertEqual(len(g46c), 16)
        self.assertEqual(sum(1 for row in catalog.pairs if row.wave == "g46"), 24)
        self.assertEqual(sum(1 for row in catalog.pairs if row.wave == "g46b"), 16)
        self.assertEqual(sum(1 for row in catalog.pairs if row.wave == "g46d"), 20)

    def test_plants_pin_matches_bytes(self):
        payload = (CATALOG / "plants.jsonl").read_bytes()
        digest = hashlib.sha256(payload).hexdigest()
        self.assertEqual(digest, hp._CATALOG.plants_sha256)
        self.assertEqual(digest, hp._CATALOG.meta["plants_sha256"])

    def test_uniqueness_and_first_old(self):
        slugs, mods, domains, tickets = [], [], [], []
        for factory, ok, bad in hp.all_pairs():
            for plant in (ok, bad):
                slugs.append(plant["slug"])
                mods.append(plant["mod"])
                domains.append(plant["domain"])
                self.assertIn(plant["first_old"], plant["src_body"])
            tickets.append(bad["ticket"])
        self.assertEqual(len(slugs), 152)
        self.assertEqual(len(set(slugs)), 152)
        self.assertEqual(len(set(mods)), 152)
        self.assertEqual(len(set(domains)), 152)
        self.assertEqual(len(set(tickets)), 76)

    def test_start_and_pairs_by_factory(self):
        self.assertIn("rate-limit-backoff-factory", hp.START)
        self.assertIn("rate-limit-backoff-factory", hp.PAIRS)
        self.assertEqual(hp.START["rate-limit-backoff-factory"], 53)
        self.assertEqual(hp.PREFIX["rate-limit-backoff-factory"], "rlb")
        g46c_start = hp.start_by_factory("g46c")
        g46c_pairs = hp.pairs_by_factory("g46c")
        self.assertEqual(g46c_start["search-index-rebuild-factory"], 49)
        self.assertEqual(len(g46c_pairs["search-index-rebuild-factory"]), 2)
        self.assertEqual(g46c_pairs["search-index-rebuild-factory"][1][0]["slug"], "zombodb-refresh-vs-truncate")

    def test_p_is_identity(self):
        plant = hp._p(slug="x", goal="Honor the header.")
        self.assertEqual(plant, {"slug": "x", "goal": "Honor the header."})
        self.assertEqual(hopper._p(slug="y"), {"slug": "y"})

    def test_unknown_wave_is_coded(self):
        with refusal(self, FINDING_UNKNOWN_WAVE, "g46z"):
            hp.start_by_factory("g46z")

    def test_sha_mismatch_raises_at_load(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp)
            dest.joinpath("CATALOG.json").write_text(
                (CATALOG / "CATALOG.json").read_text(encoding="utf-8"),
                encoding="utf-8",
            )
            dest.joinpath("plants.jsonl").write_text("{}\n", encoding="utf-8")
            with refusal(self, FINDING_PLANTS_SHA_MISMATCH, "sha256"):
                hp.load_catalog(dest)

    def test_package_and_flat_imports_are_one_object(self):
        from pipelines import hopper as packaged
        self.assertIs(packaged, hopper)
        self.assertIs(packaged.plants, hp)


if __name__ == "__main__":
    unittest.main()
