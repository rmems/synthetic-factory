#!/usr/bin/env python3
"""Keep / repair / reject contract of the trajectory-pair preference gate.

Grok 4.6 preference dumps are shared-goal, shared-prefix trajectory pairs, not
Fable ``state``/``proposed_action`` pairs. These tests pin the per-record
decision of ``pipelines/curate_trajectory_preferences.py``. The source scan,
the writer, the command line, and the denominator boundary against
``pipelines/curate_preferences.py`` live in
``test_curate_trajectory_preferences_sources``.
"""

import copy
import json
import unittest

from trajectory_preference_support import step, trajectory_pair

import curate_trajectory_preferences as ctp  # noqa: E402


class GateKeepPath(unittest.TestCase):
    def test_grok_shaped_pair_is_retained_with_prefix_evidence(self):
        decision = ctp.curate_trajectory_pair(trajectory_pair())

        self.assertEqual(decision.action, ctp.ACTION_RETAINED)
        self.assertEqual(decision.classification, "trajectory_pair_gate_passed")
        self.assertEqual(decision.reason_codes, (ctp.REASON_GATE_PASSED,))
        self.assertTrue(decision.shared_goal)
        self.assertEqual(decision.overlap["shared_steps"], 1)
        self.assertEqual(decision.overlap["chosen_steps"], 2)
        self.assertTrue(ctp.pair_passes_gate(decision.record))

    def test_side_goals_may_stand_in_for_a_missing_top_level_goal(self):
        source = trajectory_pair()
        goal = source.pop("goal")
        source["chosen"]["goal"] = goal
        source["rejected"]["goal"] = goal

        self.assertEqual(ctp.curate_trajectory_pair(source).action, ctp.ACTION_RETAINED)

    def test_truncated_rejected_branch_still_contrasts(self):
        source = trajectory_pair()
        source["rejected"]["steps"] = source["rejected"]["steps"][:1]

        decision = ctp.curate_trajectory_pair(source)

        self.assertEqual(decision.action, ctp.ACTION_RETAINED)
        self.assertEqual(decision.overlap["shared_steps"], 1)

    def test_curation_never_mutates_the_source_record(self):
        source = trajectory_pair()
        source["chosen"]["steps"][0]["thought"] = "hidden"
        before = copy.deepcopy(source)

        decision = ctp.curate_trajectory_pair(source)

        self.assertEqual(source, before)
        self.assertNotIn("thought", decision.record["chosen"]["steps"][0])


class GateRejectPath(unittest.TestCase):
    def assert_excluded(self, record, *expected_codes):
        decision = ctp.curate_trajectory_pair(record)
        self.assertEqual(decision.action, ctp.ACTION_EXCLUDED)
        self.assertIsNone(decision.record)
        for code in expected_codes:
            self.assertIn(code, decision.reason_codes)
        return decision

    def test_absent_prefix_is_excluded_and_branch_label_leak_is_disclosed(self):
        # The 36 published tool-use pairs with prefix length 0 differ at step 1
        # only by the words "chosen"/"rejected". They are rejected here, and the
        # native impurity is named rather than silently averaged away.
        source = trajectory_pair()
        source["chosen"]["steps"][0]["decision_basis"] = (
            "Plan: locate the target. — chosen policy starts by locating it."
        )
        source["rejected"]["steps"][0]["decision_basis"] = (
            "Plan: locate the target. — rejected policy starts by locating it."
        )

        decision = self.assert_excluded(
            source, ctp.REASON_PREFIX_ABSENT, ctp.REASON_BRANCH_LABEL_ONLY
        )
        self.assertEqual(decision.overlap["shared_steps"], 0)

    def test_absent_prefix_without_a_label_leak_reports_only_the_prefix(self):
        source = trajectory_pair()
        source["rejected"]["steps"][0] = step(1, "Plan: skip the inspection entirely.")

        decision = self.assert_excluded(source, ctp.REASON_PREFIX_ABSENT)
        self.assertNotIn(ctp.REASON_BRANCH_LABEL_ONLY, decision.reason_codes)

    def test_identical_trajectories_carry_no_contrast(self):
        source = trajectory_pair()
        source["rejected"]["steps"] = copy.deepcopy(source["chosen"]["steps"])

        self.assert_excluded(source, ctp.REASON_PAIR_IDENTICAL)

    def test_divergent_goal_is_excluded(self):
        source = trajectory_pair()
        source["chosen"]["goal"] = "Publish manifest.json atomically."
        source["rejected"]["goal"] = "Delete the build directory."

        self.assert_excluded(source, ctp.REASON_GOAL_DIVERGES)

    def test_missing_goal_is_excluded(self):
        source = trajectory_pair()
        source.pop("goal")

        self.assert_excluded(source, ctp.REASON_GOAL_MISSING)

    def test_non_text_goal_is_excluded(self):
        source = trajectory_pair()
        source["goal"] = {"text": "not a string"}

        self.assert_excluded(source, ctp.REASON_GOAL_NOT_TEXT)

    def test_steps_must_be_lists(self):
        source = trajectory_pair()
        source["rejected"]["steps"] = "three steps"

        self.assert_excluded(source, ctp.REASON_STEPS_INVALID)

    def test_step_elements_must_satisfy_the_episode_contract(self):
        source = trajectory_pair()
        source["chosen"]["steps"] = ["shared", "chosen"]
        source["rejected"]["steps"] = ["shared", "rejected"]

        decision = self.assert_excluded(
            source,
            ctp.REASON_SIDE_EPISODE_INVALID,
            ctp.REASON_STEPS_INVALID,
        )

        self.assertIn("chosen", decision.side_validation_errors)
        self.assertIn("rejected", decision.side_validation_errors)
        self.assertTrue(
            any("must be an object" in error for error in decision.side_validation_errors["chosen"])
        )

    def test_observable_step_field_types_are_enforced(self):
        mutations = (
            ("decision_basis", False, "decision_basis must be a non-empty string"),
            ("tool_call", "bash --version", "tool_call must be an object"),
            ("observation", 42, "observation must be a non-empty string"),
        )
        for field, value, expected_error in mutations:
            with self.subTest(field=field):
                source = trajectory_pair()
                source["chosen"]["steps"][0][field] = value

                decision = self.assert_excluded(
                    source,
                    ctp.REASON_SIDE_EPISODE_INVALID,
                    ctp.REASON_STEPS_INVALID,
                )

                self.assertTrue(
                    any(
                        expected_error in error
                        for error in decision.side_validation_errors["chosen"]
                    )
                )

    def test_step_ordinals_are_exact_one_based_integers(self):
        mutations = (
            ("missing", lambda steps: steps[0].pop("n")),
            ("boolean", lambda steps: steps[0].__setitem__("n", False)),
            ("string", lambda steps: steps[0].__setitem__("n", "1")),
            ("list", lambda steps: steps[0].__setitem__("n", [1])),
            ("gap", lambda steps: steps[0].__setitem__("n", 99)),
            ("duplicate", lambda steps: steps[1].__setitem__("n", 1)),
        )
        for label, mutate in mutations:
            with self.subTest(label=label):
                source = trajectory_pair()
                mutate(source["chosen"]["steps"])

                decision = self.assert_excluded(
                    source,
                    ctp.REASON_SIDE_EPISODE_INVALID,
                    ctp.REASON_STEPS_INVALID,
                )

                self.assertTrue(
                    any(
                        "n must be the integer" in error
                        for error in decision.side_validation_errors["chosen"]
                    )
                )

    def test_pair_envelope_fields_are_validated_before_emission(self):
        mutations = (
            ("id", {"not": "text"}, "id must be a non-empty string"),
            ("outcome", ["not", "text"], "outcome must be a non-empty string"),
            ("reward", "not-an-object", "reward must be an object"),
            ("meta", "not-an-object", "meta must be an object"),
            ("critique", 42, "critique must be a non-empty string"),
        )
        for field, value, expected_error in mutations:
            with self.subTest(field=field):
                source = trajectory_pair()
                source[field] = value

                decision = self.assert_excluded(source, ctp.REASON_PAIR_ENVELOPE_INVALID)

                self.assertTrue(
                    any(expected_error in error for error in decision.pair_validation_errors)
                )

    def test_empty_steps_are_excluded(self):
        source = trajectory_pair()
        source["chosen"]["steps"] = []

        self.assert_excluded(source, ctp.REASON_STEPS_EMPTY)

    def test_outcome_must_diverge(self):
        source = trajectory_pair()
        neutral_outcome = "The operation produced an observed terminal state."
        source["chosen"]["outcome"] = neutral_outcome
        source["rejected"]["outcome"] = neutral_outcome

        self.assert_excluded(source, ctp.REASON_OUTCOME_NOT_DIVERGENT)

    def test_reward_must_diverge(self):
        source = trajectory_pair()
        source["rejected"]["reward"] = copy.deepcopy(source["chosen"]["reward"])

        self.assert_excluded(source, ctp.REASON_REWARD_NOT_DIVERGENT)

    def test_inverted_preference_direction_is_excluded(self):
        source = trajectory_pair()
        source["chosen"]["reward"]["success"] = False
        source["chosen"]["outcome"] = "The publish failed and remained broken."
        source["rejected"]["reward"]["success"] = True
        source["rejected"]["outcome"] = "The publish completed and passed verification."

        decision = self.assert_excluded(source, ctp.REASON_PREFERENCE_DIRECTION_INVALID)

        self.assertNotIn(ctp.REASON_SIDE_EPISODE_INVALID, decision.reason_codes)

    def test_outcome_agreement_is_opt_in_and_rejects_reversed_prose(self):
        # Orientation is correct here; only the prose is reversed. Enforcing
        # agreement is the same invariant round_txn applies at publication
        # time, but terminal_outcome_agrees is lexical and misfires badly on
        # external corpora, so this lane offers it rather than imposing it.
        source = trajectory_pair()
        source["chosen"]["outcome"] = "The publish failed and remained broken."
        source["rejected"]["outcome"] = "The publish completed and passed verification."

        default = ctp.curate_trajectory_pair(source)
        self.assertEqual(default.action, ctp.ACTION_RETAINED)

        strict = ctp.curate_trajectory_pair(
            source, ctp.GatePolicy(enforce_outcome_agreement=True)
        )

        self.assertEqual(strict.action, ctp.ACTION_EXCLUDED)
        self.assertIsNone(strict.record)
        self.assertEqual(strict.classification, "malformed_trajectory_pair")
        self.assertIn(ctp.REASON_SIDE_EPISODE_INVALID, strict.reason_codes)
        self.assertIn(ctp.REASON_OUTCOME_INVALID, strict.reason_codes)
        for side_name in ("chosen", "rejected"):
            self.assertTrue(
                any(
                    "outcome must agree with reward.success" in error
                    for error in strict.side_validation_errors[side_name]
                ),
                side_name,
            )

    def test_outcome_agreement_leaves_a_consistently_labelled_pair_alone(self):
        # The published corpora describe outcomes in vocabulary the heuristic
        # does not own; a sound pair must survive the strict policy too.
        strict = ctp.curate_trajectory_pair(
            trajectory_pair(), ctp.GatePolicy(enforce_outcome_agreement=True)
        )

        self.assertEqual(strict.action, ctp.ACTION_RETAINED)

    def test_side_success_labels_are_required_exact_booleans(self):
        mutations = (("chosen", None), ("chosen", 1), ("rejected", None), ("rejected", 0))
        for side_name, value in mutations:
            with self.subTest(side=side_name, value=value):
                source = trajectory_pair()
                if value is None:
                    source[side_name]["reward"].pop("success")
                else:
                    source[side_name]["reward"]["success"] = value

                self.assert_excluded(source, ctp.REASON_PREFERENCE_DIRECTION_INVALID)

    def test_pair_level_direction_metadata_must_agree_with_labels(self):
        mutations = (
            ("success", False),
            ("preference_margin", 0.0),
            ("preference_margin", -0.7),
            ("preference_margin", float("nan")),
            ("preference_margin", float("inf")),
            ("same_goal", 0.0),
            ("same_goal", False),
            ("delta", -0.7),
        )
        for field, value in mutations:
            with self.subTest(field=field, value=value):
                source = trajectory_pair()
                source["reward"][field] = value

                self.assert_excluded(source, ctp.REASON_PREFERENCE_DIRECTION_INVALID)

    def test_direction_metadata_handles_arbitrarily_large_json_integers(self):
        huge = 10**400
        cases = (
            ("preference_margin", huge, ctp.ACTION_RETAINED),
            ("delta", huge, ctp.ACTION_RETAINED),
            ("preference_margin", -huge, ctp.ACTION_EXCLUDED),
            ("delta", -huge, ctp.ACTION_EXCLUDED),
            ("same_goal", huge, ctp.ACTION_EXCLUDED),
        )
        for field, value, expected_action in cases:
            with self.subTest(field=field, positive=value > 0):
                source = trajectory_pair(f"large-integer-{field}")
                source["reward"][field] = value
                parsed = json.loads(json.dumps(source))

                decision = ctp.curate_trajectory_pair(parsed)

                self.assertEqual(decision.action, expected_action)
                if expected_action == ctp.ACTION_EXCLUDED:
                    self.assertIn(
                        ctp.REASON_PREFERENCE_DIRECTION_INVALID,
                        decision.reason_codes,
                    )

    def test_missing_outcome_or_reward_is_named(self):
        source = trajectory_pair()
        source["chosen"].pop("outcome")
        source["rejected"].pop("reward")

        self.assert_excluded(source, ctp.REASON_OUTCOME_MISSING, ctp.REASON_REWARD_MISSING)

    def test_invalid_outcome_and_reward_types_are_rejected(self):
        source = trajectory_pair()
        source["chosen"]["outcome"] = 1
        source["rejected"]["outcome"] = 2
        source["chosen"]["reward"] = ["high"]
        source["rejected"]["reward"] = ["low"]

        decision = self.assert_excluded(
            source,
            ctp.REASON_SIDE_EPISODE_INVALID,
            ctp.REASON_OUTCOME_INVALID,
            ctp.REASON_REWARD_INVALID,
        )

        self.assertTrue(
            any(
                "outcome must be a non-empty string" in error
                for error in decision.side_validation_errors["chosen"]
            )
        )
        self.assertTrue(
            any(
                "reward must be an object" in error
                for error in decision.side_validation_errors["chosen"]
            )
        )

    def test_sides_must_be_objects(self):
        self.assert_excluded(
            {"id": "x", "chosen": ["steps"], "rejected": {"steps": []}},
            ctp.REASON_SIDES_NOT_OBJECTS,
        )

    def test_mixed_thalamic_and_episode_sides_are_not_routed_as_dpo(self):
        source = trajectory_pair()
        source["chosen"] = {
            "state": {},
            "proposed_action": {},
            "safety_decision": {},
            "executed_action": {},
            "future_outcome": {},
            "reward_components": {},
        }

        decision = self.assert_excluded(
            source,
            ctp.REASON_SIDE_EPISODE_INVALID,
            ctp.REASON_STEPS_INVALID,
            ctp.REASON_OUTCOME_MISSING,
            ctp.REASON_REWARD_MISSING,
        )

        self.assertEqual(ctp.classify_pair_schema(source), "malformed_trajectory_pair")
        self.assertIn("chosen", decision.side_validation_errors)

    def test_non_object_record_is_excluded(self):
        decision = ctp.curate_trajectory_pair(["not", "a", "record"])

        self.assertEqual(decision.action, ctp.ACTION_EXCLUDED)
        self.assertEqual(decision.reason_codes, (ctp.REASON_RECORD_NOT_OBJECT,))

    def test_every_reject_reason_is_reported_together(self):
        source = trajectory_pair()
        source.pop("goal")
        source["rejected"]["steps"][0] = step(1, "Plan: a different opening move.")
        neutral_outcome = "The operation produced an observed terminal state."
        source["chosen"]["outcome"] = neutral_outcome
        source["rejected"]["outcome"] = neutral_outcome

        decision = ctp.curate_trajectory_pair(source)

        self.assertEqual(
            decision.reason_codes,
            (
                ctp.REASON_GOAL_MISSING,
                ctp.REASON_PREFIX_ABSENT,
                ctp.REASON_OUTCOME_NOT_DIVERGENT,
            ),
        )

    def test_bad_steps_do_not_hide_independent_missing_fields(self):
        source = trajectory_pair()
        source["chosen"]["steps"] = "bad"
        source["chosen"].pop("outcome")
        source["rejected"].pop("reward")

        decision = self.assert_excluded(
            source,
            ctp.REASON_SIDE_EPISODE_INVALID,
            ctp.REASON_STEPS_INVALID,
            ctp.REASON_OUTCOME_MISSING,
            ctp.REASON_REWARD_MISSING,
        )

        self.assertEqual(decision.reason_codes.count(ctp.REASON_STEPS_INVALID), 1)


class GateRepairPath(unittest.TestCase):
    def test_hidden_thought_keys_are_stripped_and_the_pair_is_repaired(self):
        source = trajectory_pair()
        source["chosen"]["steps"][1]["chain_of_thought"] = "hidden reasoning"

        decision = ctp.curate_trajectory_pair(source)

        self.assertEqual(decision.action, ctp.ACTION_REPAIRED)
        self.assertIn("HIDDEN_THOUGHT_REMOVED", decision.reason_codes)
        self.assertIn(ctp.REASON_GATE_PASSED, decision.reason_codes)
        self.assertEqual(decision.changed_fields, ("chosen",))
        self.assertNotIn("chain_of_thought", decision.record["chosen"]["steps"][1])

    def test_goal_whitespace_is_normalized_only_when_it_is_the_sole_drift(self):
        source = trajectory_pair()
        source["chosen"]["goal"] = source["goal"]
        source["rejected"]["goal"] = source["goal"].replace(" ", "  ")

        decision = ctp.curate_trajectory_pair(source)

        self.assertEqual(decision.action, ctp.ACTION_REPAIRED)
        self.assertIn(ctp.REASON_GOAL_WHITESPACE_NORMALIZED, decision.reason_codes)
        self.assertEqual(decision.changed_fields, ("rejected",))
        self.assertEqual(decision.record["rejected"]["goal"], decision.record["chosen"]["goal"])

    def test_a_single_goal_string_is_left_alone(self):
        source = trajectory_pair()
        source["goal"] = source["goal"].replace(" ", "  ")

        decision = ctp.curate_trajectory_pair(source)

        self.assertEqual(decision.action, ctp.ACTION_RETAINED)
        self.assertEqual(decision.record["goal"], source["goal"])

    def test_repair_is_idempotent(self):
        source = trajectory_pair()
        source["chosen"]["steps"][0]["scratch"] = "hidden"

        first = ctp.curate_trajectory_pair(source)
        second = ctp.curate_trajectory_pair(first.record)

        self.assertEqual(first.action, ctp.ACTION_REPAIRED)
        self.assertEqual(second.action, ctp.ACTION_RETAINED)
        self.assertEqual(first.record, second.record)


