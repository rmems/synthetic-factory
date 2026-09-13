#!/usr/bin/env python3
"""Behavioral coverage for the extracted curated-record lane owners."""

from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path


TESTS = Path(__file__).resolve().parent
PIPELINES = TESTS.parent / "pipelines"
for _path in (TESTS, PIPELINES):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

import compose_curated_coding  # noqa: E402
import compose_curated_preferences  # noqa: E402
from compose_contract import (  # noqa: E402
    ACTION_EXCLUDED,
    ACTION_RETAINED,
    REASON_MIXED_PREFERENCE_FAMILIES,
    REASON_REWARD_ONTOLOGY,
    REASON_TRAJECTORY_SIDE_INVALID,
)
from compose_curated_context import RecordContext, SourceCoordinates  # noqa: E402
from compose_curated_record import compose_record  # noqa: E402
from compose_curated_test_support import (  # noqa: E402
    bridge_pair,
    episode,
    trajectory,
    trajectory_preference_pair,
)


def record_context(factory: str, line: int = 1) -> RecordContext:
    return RecordContext(
        SourceCoordinates(
            f"{factory}/batch-r01.jsonl",
            line,
            "a" * 64,
            "b" * 64,
        )
    )


class DeferredIdentityRepairs(unittest.TestCase):
    def test_owning_lanes_repair_narrow_identity_shape_refusals(self):
        """Bridge, coding, and preference defects remain owned by their lanes."""

        unsorted_bridge = bridge_pair(unsorted=True)
        malformed_episode = episode("deferred")
        malformed_episode["steps"].append(None)
        malformed_preference = trajectory_preference_pair()
        malformed_preference["chosen"]["steps"].append(None)
        cases = (
            (
                "bridge_order_deferred_to_bridge_lane",
                unsorted_bridge,
                "neuromorphic-event-language-bridge",
            ),
            (
                "coding_steps_deferred_to_coding_lane",
                malformed_episode,
                "agentic-coding-trajectory-factory",
            ),
            (
                "preference_steps_deferred_to_preferences_lane",
                malformed_preference,
                "tool-use-preference-factory",
            ),
        )
        decisions = {}

        for marker, source, factory in cases:
            with self.subTest(marker=marker):
                original = copy.deepcopy(source)

                decision = compose_record(source, record_context(factory))
                decisions[marker] = decision

                self.assertEqual(decision.action, ACTION_RETAINED)
                self.assertEqual(source, original)
                self.assertEqual(
                    [item["lane"] for item in decision.stages],
                    ["identity", "bridge", "preferences", "coding", "rewards"],
                )
                identity = decision.stages[0]
                self.assertEqual(identity["lane_action"], ACTION_RETAINED)
                self.assertIs(identity["detail"][marker], True)

        self.assertEqual(
            [
                event["t_rel_ms"]
                for event in decisions["bridge_order_deferred_to_bridge_lane"].record[
                    "spike_events"
                ]
            ],
            [1.0, 2.0, 3.0],
        )


class CodingLaneBoundaries(unittest.TestCase):
    def test_embedded_bridge_coding_strips_step_and_wrapper_reasoning(self):
        source = bridge_pair()
        source["thought"] = "private wrapper reasoning"
        trajectory_record = source["language_view"]["trajectory"]
        trajectory_record["executed_action"]["steps"] = [
            {
                "thought": "private step reasoning",
                "plan": "inspect the visible state",
                "tool_call": {"name": "read", "args": {"path": "state.json"}},
                "observation": "state is visible",
            }
        ]
        original = copy.deepcopy(source)
        stages = []

        curated = compose_curated_coding._compose_coding_stage(
            source,
            "bridge_pair",
            stages,
            record_context("neuromorphic-event-language-bridge", line=2),
        )

        self.assertEqual(source, original)
        self.assertNotIn("thought", curated)
        curated_step = curated["language_view"]["trajectory"]["executed_action"]["steps"][0]
        self.assertNotIn("thought", curated_step)
        self.assertEqual(curated_step["decision_basis"], "Plan: inspect the visible state")
        self.assertEqual(stages[0]["lane"], "coding")
        self.assertEqual(stages[0]["action"], ACTION_RETAINED)
        self.assertEqual(stages[0]["detail"]["wrapper_hidden_reasoning_fields_removed"], 1)
        self.assertEqual(stages[0]["detail"]["hidden_reasoning_fields_removed"], 2)

    def test_unknown_reward_annotation_version_is_fail_closed(self):
        stages = []

        decision = compose_curated_coding._compose_rewards_stage(
            {"reward_training": {"source_reward_count": 1}},
            stages,
            record_context("thalamic-trajectory-factory"),
        )

        self.assertEqual(decision.action, ACTION_EXCLUDED)
        self.assertEqual(decision.reason_codes, (REASON_REWARD_ONTOLOGY,))
        self.assertIsNone(decision.record)
        self.assertEqual(stages[0]["lane"], "rewards")
        self.assertEqual(stages[0]["action"], ACTION_EXCLUDED)
        self.assertIn("unknown reward ontology version", stages[0]["detail"]["error"])


class PreferenceLaneBoundaries(unittest.TestCase):
    def test_mixed_record_families_are_refused_before_preference_curation(self):
        source = trajectory_preference_pair()
        source["rejected"] = trajectory(action="different")
        stages = []

        decision = compose_curated_preferences._compose_preferences_stage(
            source,
            stages,
            record_context("tool-use-preference-factory"),
        )

        self.assertEqual(decision.action, ACTION_EXCLUDED)
        self.assertEqual(decision.reason_codes, (REASON_MIXED_PREFERENCE_FAMILIES,))
        self.assertIsNone(decision.record)
        self.assertEqual(stages[0]["classification"], "mixed_preference_side_families")
        self.assertEqual(stages[0]["side_kinds"], ["episode", "thalamic"])

    def test_empty_episode_side_is_refused_with_side_curation_evidence(self):
        source = trajectory_preference_pair()
        source["chosen"]["steps"] = []
        original = copy.deepcopy(source)
        stages = []

        decision = compose_curated_preferences._compose_preferences_stage(
            source,
            stages,
            record_context("tool-use-preference-factory", line=4),
        )

        self.assertEqual(source, original)
        self.assertEqual(decision.action, ACTION_EXCLUDED)
        self.assertIn(REASON_TRAJECTORY_SIDE_INVALID, decision.reason_codes)
        self.assertIsNone(decision.record)
        evidence = stages[0]
        self.assertEqual(evidence["classification"], "trajectory_side_curation_failed")
        self.assertEqual(evidence["side_kinds"], ["episode", "episode"])
        self.assertEqual(evidence["side_curation"]["chosen"]["action"], "excluded")
        self.assertIs(evidence["side_curation_changed"], True)


if __name__ == "__main__":
    unittest.main()
