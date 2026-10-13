"""Branches of the native and facade coding stages and the native reward stage.

``compose_curated_record.RecordServices`` selects the native
``compose_curated_coding`` stages, while the ``compose_curated`` facade
dispatches coding through ``compose_curated_record_dispatch``. The coding
behaviours run against both entry points so they cannot drift apart.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

TESTS = Path(__file__).resolve().parent
for _path in (TESTS, TESTS.parent / "pipelines"):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

import compose_curated
import compose_curated_coding as coding
import curate_agentic
import curate_coding
import curate_rewards
from compose_contract import ComposeDecision
from compose_curated_context import RecordContext, SourceCoordinates
from compose_curated_test_support import (
    bridge_pair,
    episode,
    multi_agent,
    preference_pair,
    thalamic,
)

SOURCE = SourceCoordinates("neuromorphic-event-language-bridge/batch-r01.jsonl", 3, "0" * 64)
CONTEXT = RecordContext(SOURCE)


def _bridge_with(trajectory) -> dict:
    record = bridge_pair()
    record["language_view"]["trajectory"] = trajectory
    return record


class CodingStageCase(unittest.TestCase):
    stage = staticmethod(coding._compose_coding_stage)

    def run_coding(self, record, registered_kind=None):
        stages: list = []
        outcome = self.stage(record, registered_kind, stages, CONTEXT)
        return outcome, stages

    def assert_not_applicable(self, record, registered_kind=None) -> None:
        outcome, stages = self.run_coding(record, registered_kind)

        self.assertIs(outcome, record)
        self.assertEqual(
            (stages[0]["action"], stages[0]["transform_name"]),
            ("not_applicable", curate_coding.TRANSFORM_NAME),
        )


class CuratorSelectionTests(unittest.TestCase):
    def test_registered_agentic_kinds_route_to_the_agentic_lane(self):
        self.assertIs(coding._coding_lane_curator(multi_agent(), "safety_case"), curate_agentic)

    def test_bridge_records_have_no_direct_coding_lane(self):
        self.assertIsNone(coding._coding_lane_curator(_bridge_with(episode()), "bridge_pair"))


class LaneRoutingTests(CodingStageCase):
    def test_plain_thalamic_record_is_not_applicable(self):
        self.assert_not_applicable(thalamic("a"), "thalamic")

    def test_bridge_without_a_mapping_view_is_not_applicable(self):
        record = bridge_pair()
        record["language_view"] = "plain text"

        self.assert_not_applicable(record, "bridge_pair")

    def test_bridge_view_without_steps_or_hidden_fields_is_not_applicable(self):
        self.assert_not_applicable(bridge_pair(), "bridge_pair")


class EmbeddedBridgeTests(CodingStageCase):
    def test_hidden_only_view_is_stripped_by_the_agentic_lane(self):
        record = bridge_pair()
        record["language_view"]["trajectory"]["proposed_action"]["internal_reasoning"] = "x"

        outcome, stages = self.run_coding(record, "bridge_pair")

        self.assertNotIn(
            "internal_reasoning", outcome["language_view"]["trajectory"]["proposed_action"]
        )
        self.assertEqual(stages[0]["transform_name"], curate_agentic.TRANSFORM_NAME)
        self.assertEqual(stages[0]["detail"]["embedded_at"], "language_view.trajectory")

    def test_embedded_episode_runs_the_coding_lane(self):
        outcome, stages = self.run_coding(_bridge_with(episode()), "bridge_pair")

        self.assertNotIn("thought", outcome["language_view"]["trajectory"]["steps"][0])
        self.assertEqual(stages[0]["transform_name"], curate_coding.TRANSFORM_NAME)
        self.assertNotIn("wrapper_hidden_reasoning_fields_removed", stages[0]["detail"])

    def test_unretainable_embedded_episode_excludes_the_bridge(self):
        trajectory = episode()
        trajectory["steps"] = []

        outcome, stages = self.run_coding(_bridge_with(trajectory), "bridge_pair")

        self.assertIsInstance(outcome, ComposeDecision)
        self.assertEqual(outcome.reason_codes, ("coding_no_retainable_steps",))
        self.assertEqual(stages[0]["detail"]["embedded_at"], "language_view.trajectory")


class WrapperStripTests(unittest.TestCase):
    def test_wrapper_without_hidden_fields_is_returned_unchanged(self):
        record = {"summary": "visible"}
        detail: dict = {}

        self.assertIs(coding._strip_bridge_wrapper(record, detail), record)
        self.assertEqual(detail, {})

    def test_wrapper_hidden_fields_merge_into_the_lane_evidence(self):
        detail = {"hidden_reasoning_fields_removed": 2, "reason_codes": ["a"], "action": "retained"}

        cleaned = coding._strip_bridge_wrapper({"summary": "s", "thought": "private"}, detail)

        self.assertEqual(cleaned, {"summary": "s"})
        self.assertEqual(detail["hidden_reasoning_fields_removed"], 3)
        self.assertEqual(detail["wrapper_hidden_reasoning_fields_removed"], 1)
        self.assertEqual(detail["action"], "modified")
        self.assertEqual(detail["reason_codes"], ["a", curate_agentic.REASON_THOUGHT_REMOVED])


class HiddenOnlyTests(CodingStageCase):
    def test_thalamic_hidden_reasoning_is_stripped(self):
        record = thalamic("a")
        record["proposed_action"]["internal_reasoning"] = "private"

        outcome, stages = self.run_coding(record, "thalamic")

        self.assertNotIn("internal_reasoning", outcome["proposed_action"])
        self.assertEqual(stages[0]["lane_action"], "modified")

    def test_preference_wrapper_hidden_reasoning_is_stripped(self):
        record = preference_pair()
        record["thought"] = "private"

        outcome, _stages = self.run_coding(record, "preference")

        self.assertNotIn("thought", outcome)


class DirectLaneTests(CodingStageCase):
    def test_registered_agentic_record_uses_the_agentic_curator(self):
        outcome, stages = self.run_coding(multi_agent(), "multi_agent")

        self.assertIsInstance(outcome, dict)
        self.assertEqual(stages[0]["transform_name"], curate_agentic.TRANSFORM_NAME)

    def test_unretainable_episode_is_excluded(self):
        record = episode()
        record["steps"] = []

        outcome, stages = self.run_coding(record, "episode")

        self.assertIsInstance(outcome, ComposeDecision)
        self.assertEqual(stages[0]["action"], "excluded")


FACADE_CODING_STAGE = staticmethod(compose_curated._compose_coding_stage)


class FacadeLaneRoutingTests(LaneRoutingTests):
    stage = FACADE_CODING_STAGE


class FacadeEmbeddedBridgeTests(EmbeddedBridgeTests):
    stage = FACADE_CODING_STAGE


class FacadeHiddenOnlyTests(HiddenOnlyTests):
    stage = FACADE_CODING_STAGE


class FacadeDirectLaneTests(DirectLaneTests):
    stage = FACADE_CODING_STAGE


class RewardStageTests(unittest.TestCase):
    def run_rewards(self, record):
        stages: list = []
        return coding._compose_rewards_stage(record, stages, CONTEXT), stages

    def test_record_with_rewards_keeps_its_annotation_and_sidecar(self):
        (annotated, sidecar), stages = self.run_rewards(episode())

        self.assertIn(curate_rewards.ANNOTATION_FIELD, annotated)
        self.assertIsNotNone(sidecar)
        self.assertEqual(stages[0]["action"], "retained")
        self.assertGreater(stages[0]["source_reward_count"], 0)

    def test_record_without_rewards_drops_the_annotation(self):
        record = {"goal": "g", "meta": {"round": 1}}

        (annotated, sidecar), stages = self.run_rewards(record)

        self.assertNotIn(curate_rewards.ANNOTATION_FIELD, annotated)
        self.assertIsNone(sidecar)
        self.assertEqual(
            (stages[0]["action"], stages[0]["source_reward_count"]), ("not_applicable", 0)
        )


if __name__ == "__main__":
    unittest.main()
