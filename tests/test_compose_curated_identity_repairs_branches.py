"""Pin the narrow identity refusals compose hands to a downstream lane repair.

Identity defers a record to the bridge, coding, or preference lane only when
every diagnostic it raised belongs to that lane. The probes return a repaired
copy or ``None`` and never raise; ``replace_coding_steps`` and
``restore_deferred_payload`` move only the lane-owned data.
"""

from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path

TESTS = Path(__file__).resolve().parent
for entry in (TESTS, TESTS.parent / "pipelines"):
    if str(entry) not in sys.path:
        sys.path.insert(0, str(entry))

import compose_curated_identity_repairs as repairs
from compose_curated_context import SourceCoordinates
from compose_curated_test_support import bridge_pair
from trajectory_preference_support import trajectory_pair

_SOURCE = SourceCoordinates("factory/batch-r01.jsonl", 1, "a" * 64)
_SHAPE = repairs.REASON_IDENTITY_INVALID_PAYLOAD_SHAPE


def _rejection(*details, reasons=(_SHAPE,)) -> dict:
    return {"reason_codes": list(reasons), "details": list(details)}


def _thalamic_wrap(steps: list) -> dict:
    wrap = {key: {} for key in ("state", "proposed_action", "safety_decision", "future_outcome")}
    wrap["reward_components"] = {}
    wrap["executed_action"] = {"steps": steps}
    return wrap


class NarrowRejectionClassifiers(unittest.TestCase):
    def test_only_identity_shape_details_requires_one_reason_and_matching_details(self):
        cases = (
            ("another reason code", _rejection("x", reasons=("identity.other",)), False),
            ("details are not a list", {"reason_codes": [_SHAPE], "details": "x"}, False),
            ("no details", _rejection(), False),
            ("a detail is not text", _rejection("x", 5), False),
            ("a detail does not match", _rejection("x", "y"), False),
            ("every detail matches", _rejection("x", "x"), True),
        )
        for label, mapping, expected in cases:
            with self.subTest(label):
                self.assertIs(
                    repairs.only_identity_shape_details(mapping, lambda d: d == "x"), expected
                )

    def test_lane_classifiers_match_only_their_own_diagnostics(self):
        bridge = "record: spike_events not globally non-decreasing at index 2"
        coding = "record step 3: decision_basis is not grounded"
        preference = "record/chosen step 1: tool_call is missing"
        cases = (
            (repairs.is_bridge_order_only_rejection, bridge, coding),
            (repairs.is_coding_step_only_rejection, coding, preference),
            (repairs.is_preference_step_only_rejection, preference, coding),
        )
        for classify, own, foreign in cases:
            with self.subTest(classify.__name__):
                self.assertTrue(classify(_rejection(own)))
                self.assertFalse(classify(_rejection(own, foreign)))


class LaneRepairProbes(unittest.TestCase):
    def test_bridge_probe_returns_the_stable_sorted_copy(self):
        repaired = repairs.bridge_order_repaired_copy_with_source(
            bridge_pair(unsorted=True), _SOURCE
        )
        times = [event["t_rel_ms"] for event in repaired["spike_events"]]
        self.assertEqual(times, sorted(times))

    def test_probes_that_cannot_repair_return_none(self):
        cases = (
            (
                "ordered bridge record",
                repairs.bridge_order_repaired_copy_with_source,
                bridge_pair(),
            ),
            ("bridge lane raises", repairs.bridge_order_repaired_copy_with_source, None),
            ("coding lane raises", repairs.coding_steps_repaired_copy_with_source, []),
        )
        for label, probe, record in cases:
            with self.subTest(label):
                self.assertIsNone(probe(record, _SOURCE))

    def test_preference_probe_copies_only_side_steps(self):
        source = trajectory_pair()
        repaired = repairs.preference_steps_repaired_copy_with_source(source, _SOURCE)
        self.assertEqual(source, trajectory_pair())
        for side in ("chosen", "rejected"):
            self.assertEqual(
                {k: v for k, v in repaired[side].items() if k != "steps"},
                {k: v for k, v in source[side].items() if k != "steps"},
            )
        self.assertEqual(
            repaired["chosen"]["steps"][0]["decision_basis"], ("Observation: designed: ok")
        )

    def test_preference_probe_refuses_sides_it_cannot_rewrite(self):
        not_an_object = trajectory_pair()
        not_an_object["rejected"] = "rejected side"
        without_steps = trajectory_pair()
        without_steps["rejected"] = {"outcome": "no steps"}
        for label, record in (("side is text", not_an_object), ("side lacks steps", without_steps)):
            with self.subTest(label):
                self.assertIsNone(
                    repairs.preference_steps_repaired_copy_with_source(record, _SOURCE)
                )


class StepReplacement(unittest.TestCase):
    def test_replace_coding_steps_follows_the_lane_steps_path(self):
        wrap = _thalamic_wrap([{"n": 1}])
        cases = (
            ("root steps", {}, {"steps": [1]}, True, {"steps": [1]}),
            (
                "wrapped steps",
                {"executed_action": {"steps": []}},
                wrap,
                True,
                {"executed_action": {"steps": [{"n": 1}]}},
            ),
            (
                "target action is not an object",
                {"executed_action": "x"},
                wrap,
                False,
                {"executed_action": "x"},
            ),
            ("no steps anywhere", {}, {}, False, {}),
        )
        for label, target, curated, replaced, expected in cases:
            with self.subTest(label):
                self.assertIs(repairs.replace_coding_steps(target, curated), replaced)
                self.assertEqual(target, expected)

    def test_restore_deferred_payload_restores_only_the_deferred_lane(self):
        source = {
            "spike_events": [{"t": 1}],
            "steps": [{"n": 1}],
            "chosen": {"steps": [{"n": 2}]},
            "rejected": "rejected side",
        }
        cases = (
            ("bridge", {"spike_events": [{"t": 1}]}),
            ("coding", {"steps": [{"n": 1}]}),
            ("preferences", {"chosen": {"steps": [{"n": 2}]}, "rejected": {}}),
            (None, {}),
        )
        for lane, restored in cases:
            current = {"chosen": {}, "rejected": {}} if lane == "preferences" else {}
            with self.subTest(lane=lane):
                repairs.restore_deferred_payload(current, copy.deepcopy(source), lane)
                self.assertEqual(current, restored)


if __name__ == "__main__":
    unittest.main()
