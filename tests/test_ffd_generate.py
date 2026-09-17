#!/usr/bin/env python3
"""Generated FFD rounds match the legacy mills and refuse raw/existing dests."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from ffd_test_support import FINDING_CODE_SET, FfdRefusal, REPO, catalog, generate, legacy_module
from ffd._contract import (
    FINDING_DESTINATION_EXISTS,
    FINDING_DESTINATION_UNDER_RAW,
    FINDING_ROUND_OUT_OF_DOMAIN,
    FINDING_SOURCE_UNKNOWN,
)


class LegacyFidelity(unittest.TestCase):
    def test_leftover3_r41_matches_the_legacy_mill(self):
        loaded = catalog.load_catalog()
        records, notes = generate.build_round(loaded, "leftover3", 41)
        mill = legacy_module("leftover3")
        ok, bad = mill.PAIRS[0]
        legacy_ok, legacy_bad, legacy_notes = mill.build_pair(mill.FACTORY, 41, ok, bad)
        self.assertEqual(records, [legacy_ok, legacy_bad])
        self.assertEqual(notes, legacy_notes)

    def test_lll_r61_matches_the_legacy_mill(self):
        loaded = catalog.load_catalog()
        records, notes = generate.build_round(loaded, "lll", 61)
        mill = legacy_module("lll")
        legacy_records, legacy_notes = mill.build_round(61)
        self.assertEqual(records, legacy_records)
        self.assertEqual(notes, legacy_notes)

    def test_hop_r102_pair0_matches_the_legacy_mill(self):
        loaded = catalog.load_catalog()
        records, notes = generate.build_round(loaded, "hop", 102, 0)
        mill = legacy_module("hop")
        legacy_records, legacy_notes, title = mill.emit_lhc(102, 0)
        self.assertEqual(title, "Split impressionsMode vs Optimizely pollInterval")
        self.assertEqual(records, legacy_records)
        self.assertEqual(notes, legacy_notes)


class Refusals(unittest.TestCase):
    def test_unknown_source_and_out_of_range_leftover3_round_are_coded(self):
        loaded = catalog.load_catalog()
        with self.assertRaises(FfdRefusal) as caught:
            generate.build_round(loaded, "not-a-source", 41)
        self.assertTrue(str(caught.exception).startswith(FINDING_SOURCE_UNKNOWN + ": "))
        with self.assertRaises(FfdRefusal) as caught:
            generate.build_round(loaded, "leftover3", 1)
        self.assertTrue(str(caught.exception).startswith(FINDING_ROUND_OUT_OF_DOMAIN + ": "))

    def test_run_refuses_raw_and_existing_destinations(self):
        catalog_dir = Path(REPO / "config" / "ffd")
        raw = REPO / "outputs" / "raw" / "ffd-should-refuse"
        with self.assertRaises(FfdRefusal) as caught:
            generate.run(generate.GenerateRequest(catalog_dir, raw, "lll", 61))
        self.assertTrue(str(caught.exception).startswith(FINDING_DESTINATION_UNDER_RAW + ": "))
        with tempfile.TemporaryDirectory(prefix="ffd-exists-") as tmp:
            existing = Path(tmp)
            with self.assertRaises(FfdRefusal) as caught:
                generate.run(generate.GenerateRequest(catalog_dir, existing, "lll", 61))
            self.assertTrue(str(caught.exception).startswith(FINDING_DESTINATION_EXISTS + ": "))
        self.assertEqual(FfdRefusal.CODES, FINDING_CODE_SET)


class WriteRound(unittest.TestCase):
    def test_run_writes_batch_and_notes_into_a_new_tree(self):
        catalog_dir = REPO / "config" / "ffd"
        with tempfile.TemporaryDirectory(prefix="ffd-out-") as tmp:
            out = Path(tmp) / "round"
            summary = generate.run(generate.GenerateRequest(catalog_dir, out, "lll", 61))
            self.assertTrue((out / "batch-r61.jsonl").is_file())
            self.assertTrue((out / "NOTES-r61.md").is_file())
            self.assertEqual(len(summary["ids"]), 2)
            self.assertTrue(all(item.startswith("ffd-r61-") for item in summary["ids"]))


if __name__ == "__main__":
    unittest.main()
