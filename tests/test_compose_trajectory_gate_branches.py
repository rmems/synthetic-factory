"""Pin the compatibility trajectory-preference gate and its goal repair.

``compose_trajectory_gate.compat_trajectory_preference`` is the fail-closed
core that runs when the reviewed sibling gate is absent. Each case changes one
property of a published-shape pair; the decision, classification and the
gate-ordered reason codes are asserted exactly as the code produces them.
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

import compose_trajectory_gate as gate
import compose_trajectory_goals as goals
import validate_run
from trajectory_preference_support import step, trajectory_pair

_PASSED = "TRAJECTORY_PAIR_SHARED_GOAL_AND_PREFIX"
_DIRECTION = "TRAJECTORY_PREFERENCE_DIRECTION_INVALID"


def _set(side: str, key: str, value):
    def mutate(record):
        record[side][key] = value

    return mutate


def _rejected_copies_chosen(record):
    record["rejected"] = copy.deepcopy(record["chosen"])


def _rejected_first_step_differs(record):
    record["rejected"]["steps"][0] = step(1, "Observation: something else entirely.")


def _rejected_outcome_removed(record):
    record["rejected"].pop("outcome")


def _rejected_reward_matches(record):
    record["rejected"]["reward"] = copy.deepcopy(record["chosen"]["reward"])


def _rejected_not_an_object(record):
    record["rejected"] = "rejected side"


_EXCLUSIONS = (
    (
        "chosen steps are not a list",
        _set("chosen", "steps", "ls"),
        ("TRAJECTORY_PAIR_SIDE_EPISODE_INVALID", "TRAJECTORY_STEPS_MISSING_OR_INVALID"),
        {"chosen": ("chosen: steps must be a non-empty array",)},
    ),
    (
        "rejected steps are empty",
        _set("rejected", "steps", []),
        ("TRAJECTORY_PAIR_SIDE_EPISODE_INVALID", "TRAJECTORY_STEPS_EMPTY"),
        {"rejected": ("rejected: steps must be a non-empty array",)},
    ),
    (
        "identical trajectories",
        _rejected_copies_chosen,
        (
            "TRAJECTORY_PAIR_IDENTICAL",
            "TRAJECTORY_OUTCOME_DOES_NOT_DIVERGE",
            "TRAJECTORY_REWARD_DOES_NOT_DIVERGE",
            _DIRECTION,
        ),
        None,
    ),
    (
        "no shared step prefix",
        _rejected_first_step_differs,
        ("TRAJECTORY_PREFIX_OVERLAP_ABSENT",),
        None,
    ),
    (
        "rejected outcome missing",
        _rejected_outcome_removed,
        ("TRAJECTORY_PAIR_SIDE_EPISODE_INVALID", "TRAJECTORY_OUTCOME_MISSING"),
        {"rejected": ("rejected: episode missing 'outcome'",)},
    ),
    (
        "rewards do not diverge",
        _rejected_reward_matches,
        ("TRAJECTORY_REWARD_DOES_NOT_DIVERGE", _DIRECTION),
        None,
    ),
    (
        "rejected side is not an object",
        _rejected_not_an_object,
        ("PREFERENCE_SIDES_NOT_OBJECTS", "TRAJECTORY_STEPS_MISSING_OR_INVALID", _DIRECTION),
        None,
    ),
    (
        "side goal diverges",
        _set("chosen", "goal", "Rotate the edge certificates."),
        ("PREFERENCE_GOAL_DIVERGES",),
        None,
    ),
)


def _decide(mutate):
    record = trajectory_pair()
    mutate(record)
    return gate.compat_trajectory_preference(record)


class CompatTrajectoryGateDecisions(unittest.TestCase):
    def test_clean_pair_is_retained_unchanged(self):
        source = trajectory_pair()
        decision = gate.compat_trajectory_preference(source)
        self.assertEqual(decision.action, gate.ACTION_RETAINED)
        self.assertEqual(decision.classification, "trajectory_pair_gate_passed")
        self.assertEqual(decision.reason_codes, (_PASSED,))
        self.assertEqual(decision.record, source)

    def test_failing_pairs_are_excluded_in_gate_order(self):
        for label, mutate, reasons, side_errors in _EXCLUSIONS:
            with self.subTest(label):
                decision = _decide(mutate)
                self.assertEqual(decision.action, gate.ACTION_EXCLUDED)
                self.assertEqual(decision.classification, "unsupported_trajectory_pair")
                self.assertEqual(decision.reason_codes, reasons)
                self.assertIsNone(decision.record)
                self.assertEqual(decision.side_validation_errors, side_errors)

    def test_whitespace_only_goal_drift_is_repaired(self):
        source = trajectory_pair()
        source["chosen"]["goal"] = "  " + source["goal"].replace(" ", "\t")
        decision = gate.compat_trajectory_preference(source)
        self.assertEqual(decision.action, "repaired")
        self.assertEqual(decision.classification, "trajectory_pair_repaired")
        self.assertEqual(decision.reason_codes, ("TRAJECTORY_GOAL_WHITESPACE_NORMALIZED", _PASSED))
        self.assertEqual(decision.record["chosen"]["goal"], trajectory_pair()["goal"])

    def test_hidden_thoughts_are_stripped_as_a_repair(self):
        source = trajectory_pair()
        source["chosen"]["steps"][1]["thought"] = "private chain of thought"
        decision = gate.compat_trajectory_preference(source)
        self.assertEqual(decision.action, "repaired")
        self.assertEqual(decision.reason_codes, ("HIDDEN_THOUGHT_REMOVED", _PASSED))
        self.assertNotIn("thought", decision.record["chosen"]["steps"][1])


class TrajectoryGateHelpers(unittest.TestCase):
    def test_divergence_reasons_need_two_object_sides(self):
        self.assertEqual(gate.trajectory_divergence_reasons({"outcome": "a"}, None), [])

    def test_step_shape_reasons_in_gate_order(self):
        cases = (
            (None, [{"n": 1}], gate.REASON_TRAJECTORY_STEPS_INVALID),
            ([{"n": 1}], [], gate.REASON_TRAJECTORY_STEPS_EMPTY),
            ([{"n": 1}], [{"n": 1}], None),
        )
        for chosen_steps, rejected_steps, expected in cases:
            with self.subTest(chosen=chosen_steps, rejected=rejected_steps):
                self.assertEqual(
                    gate.trajectory_step_shape_reason(chosen_steps, rejected_steps), expected
                )


class TrajectoryGoalRepair(unittest.TestCase):
    def test_thalamic_side_is_not_an_episode_and_non_objects_are_skipped(self):
        record = trajectory_pair()
        for key in validate_run.THALAMIC_CORE_KEYS:
            record["chosen"].setdefault(key, {})
        record["rejected"] = "rejected side"
        self.assertEqual(
            goals.trajectory_side_validation_errors(record),
            {"chosen": ("chosen: Thalamic trajectory side is not an episode",)},
        )

    def test_whitespace_only_goal_refuses_to_invent_evidence(self):
        cases = (
            ("one goal", ["a  b"], None),
            ("goals already agree", ["a b", "a b"], None),
            ("goals differ in words", ["a b", "a c"], None),
            ("goals collapse to nothing", ["  ", " "], None),
            ("goals differ only in whitespace", ["a  b", "a\tb"], "a b"),
        )
        paths = (("goal",), ("chosen", "goal"))
        for label, values, expected in cases:
            with self.subTest(label):
                present = list(zip(paths, values))
                self.assertEqual(goals.whitespace_only_goal(present), expected)

    def test_repair_skips_goal_locations_without_an_owner(self):
        record = {"goal": "a  b", "chosen": "chosen side", "rejected": {"goal": "a b"}}
        self.assertEqual(
            goals.present_trajectory_goals(record),
            [(("goal",), "a  b"), (("rejected", "goal"), "a b")],
        )
        repaired = goals.normalize_trajectory_goal_whitespace(record)
        self.assertEqual(
            repaired, {"goal": "a b", "chosen": "chosen side", "rejected": {"goal": "a b"}}
        )
        self.assertEqual(record["goal"], "a  b")


if __name__ == "__main__":
    unittest.main()
