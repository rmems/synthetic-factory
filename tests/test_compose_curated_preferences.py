#!/usr/bin/env python3
"""Preference-side routing through compose: trajectory and same-state gates."""

import copy
import json
import sys
import unittest
from pathlib import Path
from unittest import mock

TESTS = Path(__file__).resolve().parent
REPO = TESTS.parent
for _path in (TESTS, REPO / "pipelines"):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

import compose_curated  # noqa: E402
import curate_agentic  # noqa: E402
import curate_coding  # noqa: E402
import curate_preferences  # noqa: E402
from compose_curated_test_support import (  # noqa: E402
    trajectory,
    trajectory_preference_pair,
)


class ComposePreferenceGates(unittest.TestCase):
    """Split from test_compose_curated.py: the preferences lane branches."""

    @staticmethod
    def _compose_pair(pair, line=1, sha_digit="0"):
        return compose_curated.compose_record(
            pair,
            source_path="tool-use-preference-factory/batch-r01.jsonl",
            source_line=line,
            source_sha256=sha_digit * 64,
        )

    @staticmethod
    def _preference_stage(decision):
        return next(
            stage for stage in decision.stages if stage["lane"] == "preferences"
        )

    def test_episode_preference_pairs_are_retained(self):
        decision = self._compose_pair(trajectory_preference_pair())

        self.assertEqual(decision.action, compose_curated.ACTION_RETAINED)
        preference_stage = self._preference_stage(decision)
        self.assertEqual(preference_stage["side_kinds"], ["episode", "episode"])
        self.assertEqual(
            preference_stage["classification"], "trajectory_pair_gate_passed"
        )
        self.assertEqual(
            preference_stage["implementation"],
            (
                "reviewed_module"
                if compose_curated.curate_trajectory_preferences is not None
                else "compatible_core"
            ),
        )
        self.assertIn(
            compose_curated.REASON_TRAJECTORY_GATE_PASSED,
            preference_stage["reason_codes"],
        )

    def test_mixed_family_sides_are_excluded_with_the_explicit_reason(self):
        mixed = trajectory_preference_pair()
        mixed["rejected"] = trajectory(action="reject", domain="mixed")

        rejected = self._compose_pair(mixed, line=2, sha_digit="1")

        self.assertEqual(rejected.action, compose_curated.ACTION_EXCLUDED)
        self.assertEqual(
            rejected.reason_codes,
            (compose_curated.REASON_MIXED_PREFERENCE_FAMILIES,),
        )
        self.assertEqual(
            rejected.stages[0]["detail"]["preference_side_kinds"],
            ["episode", "thalamic"],
        )

    def test_a_missing_side_is_not_reported_as_a_family_mix(self):
        malformed = trajectory_preference_pair()
        malformed.pop("rejected")

        malformed_decision = self._compose_pair(malformed, line=3, sha_digit="2")

        self.assertEqual(malformed_decision.action, compose_curated.ACTION_EXCLUDED)
        self.assertNotIn(
            compose_curated.REASON_MIXED_PREFERENCE_FAMILIES,
            malformed_decision.reason_codes,
        )
        self.assertEqual(
            malformed_decision.stages[0]["detail"]["preference_side_kinds"],
            ["episode", "unknown"],
        )

    def test_whitespace_divergent_goals_are_normalized_as_a_repair(self):
        whitespace = trajectory_preference_pair()
        whitespace["goal"] = "Fix shared assertion"
        whitespace["chosen"]["goal"] = " Fix  shared assertion "
        whitespace["rejected"]["goal"] = "Fix\tshared assertion"

        repaired = self._compose_pair(whitespace, line=4, sha_digit="3")

        preference_stage = self._preference_stage(repaired)
        self.assertEqual(preference_stage["lane_action"], "repaired")
        self.assertIn(
            compose_curated.REASON_TRAJECTORY_GOAL_NORMALIZED,
            preference_stage["reason_codes"],
        )
        self.assertEqual(repaired.record["goal"], "Fix shared assertion")
        self.assertEqual(repaired.record["chosen"]["goal"], "Fix shared assertion")
        self.assertEqual(repaired.record["rejected"]["goal"], "Fix shared assertion")

    @staticmethod
    def _swap_bases_for_legacy_thought(pair):
        for side_name in ("chosen", "rejected"):
            for index, step in enumerate(pair[side_name]["steps"], 1):
                step.pop("decision_basis")
                step["thought"] = f"hidden {side_name} reasoning {index}"

    def _assert_side_steps_regrounded(self, decision, side_name):
        for step in decision.record[side_name]["steps"]:
            self.assertNotIn("thought", step)
            self.assertTrue(step["decision_basis"].startswith("Observation:"))

    def test_episode_preference_sides_migrate_legacy_thought_before_validation(self):
        pair = trajectory_preference_pair()
        self._swap_bases_for_legacy_thought(pair)
        source = copy.deepcopy(pair)

        decision = self._compose_pair(pair, sha_digit="6")

        self.assertEqual(decision.action, compose_curated.ACTION_RETAINED)
        self.assertEqual(pair, source)
        stage = self._preference_stage(decision)
        self.assertTrue(stage["side_curation_changed"])
        self.assertEqual(stage["lane_action"], "repaired")
        self.assertIn(curate_coding.REASON_HIDDEN_REASONING_REMOVED, stage["reason_codes"])
        self.assertIn(curate_coding.REASON_STEPS_MIGRATED, stage["reason_codes"])
        for side_name in ("chosen", "rejected"):
            self._assert_side_steps_regrounded(decision, side_name)
            self.assertEqual(stage["side_curation"][side_name]["action"], "modified")
            self.assertGreater(
                stage["side_curation"][side_name]["hidden_reasoning_fields_removed"], 0
            )

    @staticmethod
    def _impure_same_state_pair():
        impure = trajectory_preference_pair()
        impure["chosen"].update(
            {
                "state": {"tick": 1},
                "proposed_action": {"action": "chosen"},
            }
        )
        impure["rejected"].update(
            {
                "state": {"tick": 2},
                "proposed_action": {"action": "rejected"},
            }
        )
        return impure

    def test_same_state_schema_precedes_episode_fields_and_matches_pr93(self):
        impure = self._impure_same_state_pair()

        direct = curate_preferences.curate_preference_record(impure)
        decision = self._compose_pair(impure, sha_digit="4")

        self.assertIsNone(direct.record)
        self.assertEqual(decision.action, compose_curated.ACTION_EXCLUDED)
        self.assertEqual(decision.reason_codes, direct.reason_codes)
        preference_stage = self._preference_stage(decision)
        self.assertEqual(preference_stage["schema"], "same_state_pair")
        self.assertEqual(
            preference_stage["transform_name"], curate_preferences.TRANSFORM_NAME
        )
        self.assertEqual(
            preference_stage["classification"], direct.classification
        )
        self.assertNotIn("implementation", preference_stage)

    def test_a_pure_same_state_pair_is_retained_with_its_sides_repaired(self):
        pure = self._impure_same_state_pair()
        pure["rejected"]["state"] = copy.deepcopy(pure["chosen"]["state"])
        pure["rejected"]["proposed_action"] = copy.deepcopy(
            pure["chosen"]["proposed_action"]
        )
        for side_name in ("chosen", "rejected"):
            pure[side_name]["steps"][0]["thought"] = (
                f"hidden same-state reasoning on {side_name}"
            )

        retained = self._compose_pair(pure, line=2, sha_digit="5")

        retained_stage = self._preference_stage(retained)
        direct_pure = curate_preferences.curate_preference_record(pure)
        self.assertEqual(retained.action, compose_curated.ACTION_RETAINED)
        self.assertEqual(retained_stage["schema"], "same_state_pair")
        self.assertEqual(
            retained_stage["classification"], direct_pure.classification
        )
        self.assertTrue(retained_stage["side_curation_changed"])
        self.assertEqual(retained_stage["lane_action"], "repaired")
        self.assertIn(
            curate_coding.REASON_HIDDEN_REASONING_REMOVED,
            retained_stage["reason_codes"],
        )
        for side_name in ("chosen", "rejected"):
            self.assertNotIn("thought", retained.record[side_name]["steps"][0])
            self.assertTrue(
                retained.record[side_name]["steps"][0]["decision_basis"].strip()
            )

    def test_same_state_wrapper_hidden_reasoning_is_stripped(self):
        """Hidden fields on the retained wrapper are governed like its sides."""

        pure = self._impure_same_state_pair()
        pure["rejected"]["state"] = copy.deepcopy(pure["chosen"]["state"])
        pure["rejected"]["proposed_action"] = copy.deepcopy(
            pure["chosen"]["proposed_action"]
        )
        pure["internal_reasoning"] = "private wrapper rationale"

        retained = self._compose_pair(pure, line=3, sha_digit="a")

        self.assertEqual(retained.action, compose_curated.ACTION_RETAINED)
        self.assertNotIn("internal_reasoning", retained.record)
        coding_stage = next(
            stage for stage in retained.stages if stage["lane"] == "coding"
        )
        self.assertEqual(coding_stage["lane_action"], "modified")
        self.assertGreater(
            coding_stage["detail"]["hidden_reasoning_fields_removed"], 0
        )

    def test_compatibility_gate_rejects_an_inverted_preference_direction(self):
        """The fallback must bind chosen=success and rejected=failure."""

        inverted = trajectory_preference_pair()
        inverted["chosen"]["reward"]["success"] = False
        inverted["rejected"]["reward"]["success"] = True

        with mock.patch.object(
            compose_curated, "curate_trajectory_preferences", None
        ):
            rejected = self._compose_pair(inverted, line=4, sha_digit="b")

        self.assertEqual(rejected.action, compose_curated.ACTION_EXCLUDED)
        self.assertIn(
            "TRAJECTORY_PREFERENCE_DIRECTION_INVALID", rejected.reason_codes
        )

    def test_reviewed_trajectory_module_is_used_when_the_stack_provides_it(self):
        pair = trajectory_preference_pair()

        class ReviewedModule:
            TRANSFORM_NAME = "reviewed-trajectory-contract"
            TRANSFORM_VERSION = "reviewed-v1"

            @staticmethod
            def curate_trajectory_pair(record):
                return compose_curated._TrajectoryPreferenceDecision(
                    action="retained",
                    classification="reviewed_contract_called",
                    reason_codes=(compose_curated.REASON_TRAJECTORY_GATE_PASSED,),
                    record=copy.deepcopy(record),
                    shared_goal=True,
                    overlap={"shared_steps": 1},
                )

        with mock.patch.object(
            compose_curated, "curate_trajectory_preferences", ReviewedModule
        ):
            decision = compose_curated.compose_record(
                pair,
                source_path="tool-use-preference-factory/batch-r01.jsonl",
                source_line=1,
                source_sha256="0" * 64,
            )

        stage = next(item for item in decision.stages if item["lane"] == "preferences")
        self.assertEqual(stage["transform_name"], ReviewedModule.TRANSFORM_NAME)
        self.assertEqual(stage["transform_version"], ReviewedModule.TRANSFORM_VERSION)
        self.assertEqual(stage["implementation"], "reviewed_module")
        self.assertEqual(stage["classification"], "reviewed_contract_called")


class TrajectorySideGroundingScope(unittest.TestCase):
    """Every side carrying steps runs the coding lane, grounded or not."""

    @staticmethod
    def _overwrite_every_decision_basis(pair, text):
        # Nonblank, so the old "does any step lack a basis?" probe
        # skipped the lane entirely and shipped this text verbatim.
        for side_name in ("chosen", "rejected"):
            for step in pair[side_name]["steps"]:
                step["decision_basis"] = text

    def _assert_side_regrounded(self, decision, side_name):
        for step in decision.record[side_name]["steps"]:
            self.assertNotIn("Private hunch", step["decision_basis"])
            self.assertTrue(step["decision_basis"].startswith("Observation:"))

    def test_nonblank_but_ungrounded_decision_basis_is_regrounded(self):
        pair = trajectory_preference_pair()
        self._overwrite_every_decision_basis(
            pair, "Private hunch, no visible evidence."
        )

        decision = compose_curated.compose_record(
            pair,
            source_path="tool-use-preference-factory/batch-r01.jsonl",
            source_line=1,
            source_sha256="8" * 64,
        )

        self.assertEqual(decision.action, compose_curated.ACTION_RETAINED)
        stage = next(item for item in decision.stages if item["lane"] == "preferences")
        for side_name in ("chosen", "rejected"):
            self._assert_side_regrounded(decision, side_name)
            side_manifest = stage["side_curation"][side_name]
            self.assertEqual(side_manifest["action"], "modified")
            self.assertNotEqual(
                side_manifest["action"], compose_curated.ACTION_NOT_APPLICABLE
            )

    def test_an_already_grounded_side_is_retained_byte_for_byte(self):
        # The lane is idempotent: running it on a side whose basis is already
        # derived from visible evidence must not perturb the payload.
        pair = trajectory_preference_pair()
        first = compose_curated.compose_record(
            pair,
            source_path="tool-use-preference-factory/batch-r01.jsonl",
            source_line=1,
            source_sha256="9" * 64,
        )
        second = compose_curated.compose_record(
            copy.deepcopy(first.record),
            source_path="tool-use-preference-factory/batch-r01.jsonl",
            source_line=1,
            source_sha256="9" * 64,
        )

        for side_name in ("chosen", "rejected"):
            self.assertEqual(
                first.record[side_name]["steps"], second.record[side_name]["steps"]
            )


class TrajectorySideRouting(unittest.TestCase):
    """Each side runs the transform that owns its shape, never a wrong lane."""

    @staticmethod
    def _wrap_side(success=True):
        return {
            "state": {"sim_or_real": "designed"},
            "proposed_action": {"action": "noop", "decision_basis": "fixture"},
            "executed_action": {
                "steps": [
                    {
                        "n": 1,
                        "tool_call": {"name": "inspect", "args": {}},
                        "observation": "fixture result",
                    }
                ],
                "goal": "fixture goal",
                "outcome": "fixture outcome",
                "reward": {"success": success},
            },
        }

    def test_wrapped_steps_route_to_the_coding_lane(self):
        """Codex #97 P2: steps at executed_action.steps must not skip coding.

        The wrap contract keeps coding steps one level down; probing only a
        top-level ``steps`` array let a repairable missing ``decision_basis``
        reach the strict audit unchanged and block composition.
        """
        side = self._wrap_side()
        self.assertTrue(compose_curated._trajectory_side_needs_coding(side))

        record = {"chosen": self._wrap_side(True), "rejected": self._wrap_side(False)}
        curated, manifests, _reasons, changed = compose_curated._curate_trajectory_sides(
            record, source_path="p", source_line=1
        )

        self.assertIsNotNone(curated)
        self.assertTrue(changed)
        for side_name in ("chosen", "rejected"):
            self.assertEqual(
                manifests[side_name]["transform_name"], curate_coding.TRANSFORM_NAME
            )
            step = curated[side_name]["executed_action"]["steps"][0]
            self.assertTrue(step["decision_basis"].startswith("Observation:"))

    def test_hidden_only_non_coding_sides_use_the_generic_stripper(self):
        """Codex #97 P2: a stepless Thalamic side with a private field repairs.

        Routing it through curate_coding.curate_episode could only fail
        (coding_steps_not_array) and excluded the whole pair; the generic
        recursive stripper removes exactly what the audit refuses.
        """
        hidden = {
            "state": {"sim_or_real": "designed"},
            "proposed_action": {
                "action": "noop",
                "decision_basis": "fixture",
                "internal_reasoning": "hidden",
            },
            "future_outcome": {"success": True},
        }
        clean = {
            "state": {"sim_or_real": "designed"},
            "proposed_action": {"action": "noop", "decision_basis": "fixture"},
            "future_outcome": {"success": False},
        }
        record = {"chosen": hidden, "rejected": clean}

        curated, manifests, reasons, changed = compose_curated._curate_trajectory_sides(
            record, source_path="p", source_line=1
        )

        self.assertIsNotNone(curated)
        self.assertTrue(changed)
        self.assertNotIn("internal_reasoning", json.dumps(curated))
        chosen_manifest = manifests["chosen"]
        self.assertEqual(
            chosen_manifest["transform_name"], curate_agentic.TRANSFORM_NAME
        )
        self.assertEqual(chosen_manifest["action"], "modified")
        self.assertGreater(chosen_manifest["hidden_reasoning_fields_removed"], 0)
        self.assertIn(curate_agentic.REASON_THOUGHT_REMOVED, reasons)
        self.assertEqual(manifests["rejected"]["action"], "not_applicable")


if __name__ == "__main__":
    unittest.main()
