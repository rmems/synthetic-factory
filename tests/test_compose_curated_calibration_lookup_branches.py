"""Pin how compose looks up reward calibration by pre-identity source ids.

The lookup walks the identity lane's legacy id vocabulary in a fixed order:
the record itself, then its ``meta`` and ``state`` containers, then the same
three containers on the ``chosen`` and ``rejected`` sides. Blank and
non-string ids are skipped, ids are stripped, and the catalog is keyed by
``str.lower``.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

PIPELINES = Path(__file__).resolve().parents[1] / "pipelines"
if str(PIPELINES) not in sys.path:
    sys.path.insert(0, str(PIPELINES))

import compose_curated_calibration_lookup as lookup

_LAYERED = {
    "id": "   ",
    "record_id": 7,
    "meta": {"trajectory_id": " Meta-1 "},
    "state": {"episode_id": "state-1"},
    "chosen": {"pair_id": "chosen-1", "meta": {"id": "chosen-meta"}},
    "rejected": "not an owner",
}


class CalibrationCandidates(unittest.TestCase):
    def test_candidates_follow_the_identity_vocabulary_order(self):
        self.assertEqual(
            list(lookup.calibration_id_candidates(_LAYERED)),
            ["Meta-1", "state-1", "chosen-1", "chosen-meta"],
        )

    def test_unusable_ids_normalize_to_none(self):
        for value in (None, 7, "", "   "):
            with self.subTest(value=value):
                self.assertIsNone(lookup.usable_calibration_id(value))
        self.assertEqual(lookup.usable_calibration_id("  r1 "), "r1")


class CalibrationLookup(unittest.TestCase):
    def test_missing_catalog_or_record_yields_no_calibration(self):
        cases = (
            ("no catalog", {"id": "r1"}, None),
            ("empty catalog", {"id": "r1"}, {}),
            ("record is not a mapping", ["r1"], {"r1": "calibration"}),
            ("no candidate matches", {"id": "r2"}, {"r1": "calibration"}),
        )
        for label, record, catalog in cases:
            with self.subTest(label):
                self.assertIsNone(lookup.calibration_for(record, catalog))

    def test_first_matching_candidate_wins_with_lowercased_keys(self):
        catalog = {"chosen-1": "side calibration", "meta-1": "meta calibration"}
        self.assertEqual(lookup.calibration_for(_LAYERED, catalog), "meta calibration")

    def test_side_identifiers_are_consulted_after_the_record(self):
        record = {"chosen": {"state": {"episode_id": "EP-9"}}}
        self.assertEqual(lookup.calibration_for(record, {"ep-9": "episode"}), "episode")


if __name__ == "__main__":
    unittest.main()
