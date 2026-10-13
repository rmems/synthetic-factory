"""Branches of deferred downstream-lane repair for identity-only refusals."""

from __future__ import annotations

import sys
import types
import unittest
from pathlib import Path

TESTS = Path(__file__).resolve().parent
for _path in (TESTS, TESTS.parent / "pipelines"):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

import compose_curated_identity_deferral as deferral
from compose_curated_context import SourceCoordinates
from compose_curated_test_support import episode

SOURCE = SourceCoordinates("agentic-coding-trajectory-factory/batch-r01.jsonl", 1, "0" * 64)
REFUSED = types.SimpleNamespace(action="excluded", mapping={})


def _lane(name: str, applies: bool, repaired):
    return deferral.DeferredLaneRepair(name, applies, lambda _record: repaired)


class IdentityRetryTests(unittest.TestCase):
    def test_missing_repair_is_not_retried(self):
        self.assertIsNone(deferral.identity_retry_with_source(None, SOURCE))

    def test_identity_valid_repair_is_returned(self):
        retry = deferral.identity_retry_with_source(episode(), SOURCE)

        self.assertEqual(retry.action, "retained")
        self.assertIsInstance(retry.record, dict)

    def test_identity_invalid_repair_is_discarded(self):
        self.assertIsNone(deferral.identity_retry_with_source({"goal": "g"}, SOURCE))

    def test_inapplicable_lane_is_not_tried(self):
        self.assertIsNone(deferral.lane_retry(False, None, episode(), SOURCE))

    def test_applicable_lane_repairs_then_revalidates(self):
        seen: list = []

        def repair(record, source):
            seen.append(source)
            return record

        retry = deferral.lane_retry(True, repair, episode(), SOURCE)

        self.assertEqual(seen, [SOURCE])
        self.assertEqual(retry.action, "retained")


class DeferredLaneOrderTests(unittest.TestCase):
    @staticmethod
    def run_lanes(record, result, lanes):
        return deferral.run_deferred_lane_repairs(record, result, lanes, lambda repaired: repaired)

    def test_retained_identity_needs_no_repair(self):
        retained = types.SimpleNamespace(action="retained", mapping={})

        self.assertEqual(self.run_lanes({}, retained, ()), (retained, None))

    def test_non_mapping_record_is_not_repaired(self):
        self.assertEqual(self.run_lanes(["not", "a", "mapping"], REFUSED, ()), (REFUSED, None))

    def test_first_applicable_successful_lane_wins(self):
        lanes = (
            _lane("bridge", False, {"from": "bridge"}),
            _lane("coding", True, None),
            _lane("preferences", True, {"from": "preferences"}),
        )

        self.assertEqual(
            self.run_lanes({}, REFUSED, lanes), ({"from": "preferences"}, "preferences")
        )

    def test_no_successful_lane_keeps_the_refusal(self):
        lanes = (_lane("coding", True, None),)

        self.assertEqual(self.run_lanes({}, REFUSED, lanes), (REFUSED, None))

    def test_source_bound_entry_point_skips_retained_identity(self):
        retained = types.SimpleNamespace(action="retained", mapping={})

        self.assertEqual(
            deferral.deferred_lane_repair_with_source(episode(), retained, SOURCE), (retained, None)
        )

    def test_source_bound_entry_point_keeps_an_unrepairable_refusal(self):
        self.assertEqual(
            deferral.deferred_lane_repair_with_source({"goal": "g"}, REFUSED, SOURCE),
            (REFUSED, None),
        )


if __name__ == "__main__":
    unittest.main()
