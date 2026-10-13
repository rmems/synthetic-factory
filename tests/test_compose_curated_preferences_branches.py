"""Branches of the native and facade preference stages.

``compose_curated_record.RecordServices`` selects the native
``compose_curated_preferences`` stage, while the ``compose_curated`` facade
dispatches the same pairs through ``compose_curated_record_dispatch``. The
shared behaviours run against both entry points so they cannot drift apart.
"""

from __future__ import annotations

import copy
import sys
import types
import unittest
from pathlib import Path

TESTS = Path(__file__).resolve().parent
for _path in (TESTS, TESTS.parent / "pipelines"):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

import compose_curated
import compose_curated_preferences as preferences
import curate_preferences
from compose_contract import (
    REASON_MIXED_PREFERENCE_FAMILIES,
    REASON_TRAJECTORY_SIDE_INVALID,
    ComposeDecision,
    TrajectoryPreferenceDecision,
)
from compose_curated_context import RecordContext, SourceCoordinates
from compose_curated_test_support import (
    episode,
    preference_pair,
    thalamic,
    trajectory_preference_pair,
)

SOURCE = SourceCoordinates("tool-use-preference-factory/batch-r01.jsonl", 1, "0" * 64)


def _with_side_steps(pair: dict, steps: list) -> dict:
    for side in ("chosen", "rejected"):
        pair[side]["steps"] = copy.deepcopy(steps)
    return pair


class ReviewedTrajectoryGate:
    """A reviewed trajectory module that retains every pair it is shown."""

    TRANSFORM_NAME = "reviewed-trajectory-gate"
    TRANSFORM_VERSION = "9.9.9"

    @staticmethod
    def curate_trajectory_pair(record):
        return TrajectoryPreferenceDecision(
            "retain", "reviewed_gate_passed", ("REVIEWED_PASS",), record, True, {"steps": 1}
        )


class PreferenceStageCase(unittest.TestCase):
    stage = staticmethod(preferences._compose_preferences_stage)

    def run_stage(self, record, trajectory_preferences=None):
        stages: list = []
        context = RecordContext(SOURCE, None, trajectory_preferences)
        outcome = self.stage(record, stages, context)
        return outcome, stages

    def excluded(self, record) -> ComposeDecision:
        outcome, _stages = self.run_stage(record)
        self.assertIsInstance(outcome, ComposeDecision)
        self.assertEqual((outcome.action, outcome.record), ("excluded", None))
        return outcome


class NotApplicableAndLegacyTests(PreferenceStageCase):
    def test_non_preference_record_passes_through_unchanged(self):
        record = episode()

        outcome, stages = self.run_stage(record)

        self.assertIs(outcome, record)
        self.assertEqual((stages[0]["action"], stages[0]["lane_action"]), ("not_applicable",) * 2)

    def test_legacy_pair_without_context_is_excluded(self):
        decision = self.excluded({"reward_delta": 1})

        self.assertEqual(decision.reason_codes, ("PREFERENCE_CONTEXT_MISSING_OR_INVALID",))
        evidence = decision.stages[-1]
        self.assertEqual(evidence["transform_name"], curate_preferences.TRANSFORM_NAME)
        self.assertEqual(evidence["classification"], "malformed_preference_context")
        self.assertEqual(evidence["side_kinds"], ["unknown", "unknown"])


class SameStatePreferenceTests(PreferenceStageCase):
    def test_pure_pair_is_retained_without_side_repair(self):
        outcome, stages = self.run_stage(preference_pair(pure=True))

        self.assertIsInstance(outcome, dict)
        self.assertEqual(stages[-1]["schema"], "same_state_pair")
        self.assertEqual(stages[-1]["lane_action"], "retained")
        self.assertIs(stages[-1]["side_curation_changed"], False)

    def test_repaired_sides_are_reported_as_repaired(self):
        pair = _with_side_steps(preference_pair(pure=True), episode()["steps"])

        outcome, stages = self.run_stage(pair)

        self.assertIsInstance(outcome, dict)
        self.assertEqual(stages[-1]["lane_action"], "repaired")
        self.assertIs(stages[-1]["side_curation_changed"], True)

    def test_divergent_proposals_are_excluded(self):
        decision = self.excluded(preference_pair(pure=False))

        self.assertEqual(decision.reason_codes, ("PROPOSED_ACTION_CONTEXT_DIVERGES",))
        self.assertEqual(decision.stages[-1]["schema"], "same_state_pair")

    def test_unrepairable_sides_are_excluded_with_side_evidence(self):
        decision = self.excluded(_with_side_steps(preference_pair(pure=True), []))

        self.assertEqual(decision.reason_codes[0], REASON_TRAJECTORY_SIDE_INVALID)
        evidence = decision.stages[-1]
        self.assertEqual(evidence["classification"], "same_state_side_curation_failed")
        self.assertEqual(evidence["schema"], "same_state_pair")
        self.assertEqual(set(evidence["side_curation"]), {"chosen", "rejected"})


class EpisodePreferenceTests(PreferenceStageCase):
    def test_compatible_core_retains_a_divergent_pair(self):
        outcome, stages = self.run_stage(trajectory_preference_pair())

        self.assertIsInstance(outcome, dict)
        self.assertEqual(stages[-1]["implementation"], "compatible_core")
        self.assertEqual(stages[-1]["lane_action"], "repaired")

    def test_reviewed_module_owns_the_stage_identity(self):
        outcome, stages = self.run_stage(trajectory_preference_pair(), ReviewedTrajectoryGate)

        self.assertIsInstance(outcome, dict)
        self.assertEqual(
            (stages[-1]["transform_name"], stages[-1]["transform_version"]),
            ("reviewed-trajectory-gate", "9.9.9"),
        )
        self.assertEqual(stages[-1]["implementation"], "reviewed_module")
        self.assertIn("REVIEWED_PASS", stages[-1]["reason_codes"])

    def test_identical_sides_are_excluded(self):
        pair = trajectory_preference_pair()
        pair["rejected"] = copy.deepcopy(pair["chosen"])

        decision = self.excluded(pair)

        self.assertIn("TRAJECTORY_PAIR_IDENTICAL", decision.reason_codes)
        self.assertEqual(decision.stages[-1]["classification"], "unsupported_trajectory_pair")

    def test_unrepairable_side_is_excluded_without_a_schema(self):
        pair = trajectory_preference_pair()
        pair["rejected"]["steps"] = []

        decision = self.excluded(pair)

        evidence = decision.stages[-1]
        self.assertEqual(evidence["classification"], "trajectory_side_curation_failed")
        self.assertNotIn("schema", evidence)


class FacadeNotApplicableAndLegacyTests(NotApplicableAndLegacyTests):
    stage = staticmethod(compose_curated._compose_preferences_stage)

    def test_mixed_side_families_are_excluded_before_curation(self):
        pair = trajectory_preference_pair()
        pair["rejected"] = thalamic("x")

        decision = self.excluded(pair)

        self.assertEqual(decision.reason_codes, (REASON_MIXED_PREFERENCE_FAMILIES,))
        self.assertEqual(decision.stages[-1]["side_kinds"], ["episode", "thalamic"])


class FacadeSameStatePreferenceTests(SameStatePreferenceTests):
    stage = staticmethod(compose_curated._compose_preferences_stage)


class SideFailureEvidenceTests(unittest.TestCase):
    def test_extra_failure_evidence_is_merged_into_the_stage(self):
        curation = preferences.SideCuration(None, {"chosen": {}}, ("coding_x", "coding_x"), False)
        failure = preferences.SideFailure(
            ("episode", "episode"), "custom_failure", extra=types.MappingProxyType({"hint": 1})
        )
        stages: list = []

        decision = preferences._side_curation_failed_decision(stages, curation, failure)

        self.assertEqual(decision.reason_codes, (REASON_TRAJECTORY_SIDE_INVALID, "coding_x"))
        self.assertEqual(stages[-1]["hint"], 1)
        self.assertNotIn("schema", stages[-1])


if __name__ == "__main__":
    unittest.main()
