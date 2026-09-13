#!/usr/bin/env python3
"""Focused tests for agentic turn-level curation and preference prefix purity."""

import copy
import json
import sys
import unittest
from pathlib import Path

TESTS = Path(__file__).resolve().parent
PIPELINES = TESTS.parent / "pipelines"
for _path in (TESTS, PIPELINES):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

from curate_agentic import (  # noqa: E402
    ACTION_EXCLUDED,
    ACTION_FLAGGED,
    ACTION_MODIFIED,
    ACTION_RETAINED,
    ACTION_SKIPPED,
    HIDDEN_THOUGHT_KEYS,
    INVALID_PREFERENCE_KIND,
    REASON_GOAL_DIVERGES,
    REASON_GOAL_MISSING,
    REASON_GOAL_NOT_TEXT,
    REASON_MISSING_BASIS,
    REASON_PREFERENCE_COLLAPSED,
    REASON_PREFIX_OVERLAP,
    REASON_SAFETY_CASE_TYPE_INVALID,
    REASON_SIDE_SHAPE_INVALID,
    REASON_SKIPPED_KIND,
    REASON_THOUGHT_REMOVED,
    classify_record,
    contains_hidden_thought_key,
    curate_record,
    missing_decision_basis_paths,
    prefix_overlap,
    shared_preference_goal,
)
from curate_agentic_fixtures import (  # noqa: E402
    episode_fixture,
    multi_agent_fixture,
    preference_fixture,
    safety_case_fixture,
    step,
    thalamic_fixture,
)
import training_audit  # noqa: E402


class CurateAgenticTests(unittest.TestCase):
    def test_classifies_four_agentic_kinds(self):
        self.assertEqual(classify_record(episode_fixture()), "episode")
        self.assertEqual(classify_record(preference_fixture()), "preference")
        self.assertEqual(classify_record(multi_agent_fixture()), "multi_agent")
        self.assertEqual(classify_record(safety_case_fixture()), "safety_case")
        self.assertEqual(classify_record(thalamic_fixture()), "thalamic")

    def test_legacy_thalamic_preference_is_skipped_not_counted_as_goal_impure(self):
        side = thalamic_fixture()
        record = {
            "id": "legacy-pair",
            "chosen": side,
            "rejected": dict(side),
            "critique": "legacy Thalamic pair",
        }

        curated, decision = curate_record(record)

        self.assertEqual(classify_record(record), "legacy_preference")
        self.assertIsNone(curated)
        self.assertEqual(decision["action"], ACTION_SKIPPED)
        self.assertIn(REASON_SKIPPED_KIND, decision["reason_codes"])

    def test_mixed_preference_side_families_are_excluded(self):
        record = preference_fixture()
        record["chosen"] = thalamic_fixture()

        curated, decision = curate_record(record)

        self.assertEqual(classify_record(record), INVALID_PREFERENCE_KIND)
        self.assertIsNone(curated)
        self.assertEqual(decision["action"], ACTION_EXCLUDED)
        self.assertEqual(decision["reason_codes"], [REASON_SIDE_SHAPE_INVALID])

    def test_malformed_pairs_and_unhashable_safety_types_are_excluded(self):
        malformed_pair = {
            "id": "agentic-pair-without-steps",
            "chosen": {},
            "rejected": {},
            "meta": {"factory": "tool-use-preference-factory"},
        }
        curated, decision = curate_record(malformed_pair)
        self.assertIsNone(curated)
        self.assertEqual(decision["kind"], "preference")
        self.assertEqual(decision["action"], ACTION_EXCLUDED)
        self.assertIn(REASON_GOAL_MISSING, decision["reason_codes"])

        malformed_safety = {"case_type": []}
        curated, decision = curate_record(malformed_safety)
        self.assertIsNone(curated)
        self.assertEqual(decision["kind"], "safety_case")
        self.assertEqual(decision["action"], ACTION_EXCLUDED)
        self.assertIn(REASON_SAFETY_CASE_TYPE_INVALID, decision["reason_codes"])

    def test_strips_every_hidden_thought_key_recursively(self):
        source = episode_fixture(
            steps=[
                step(
                    1,
                    thought="private scratch",
                    chain_of_thought="longer private chain",
                    chainOfThought="camel private chain",
                    tool_call={
                        "name": "bash",
                        "args": {
                            "command": "true",
                            "scratch": "nested",
                            "chain-of-thought": "hyphenated private chain",
                        },
                        "inner_monologue": "still hidden",
                        "Chain_Of_Thought": "mixed-case private chain",
                    },
                )
            ]
        )

        self.assertTrue(contains_hidden_thought_key(source))
        curated, decision = curate_record(source)

        self.assertIsNotNone(curated)
        self.assertFalse(contains_hidden_thought_key(curated))
        self.assertEqual(curated["steps"][0]["tool_call"]["args"], {"command": "true"})
        self.assertEqual(decision["thought_fields_removed"], 7)
        self.assertIn(REASON_THOUGHT_REMOVED, decision["reason_codes"])
        self.assertEqual(decision["action"], ACTION_MODIFIED)
        for key in HIDDEN_THOUGHT_KEYS:
            self.assertNotIn(key, json.dumps(curated))
        for key in ("chainOfThought", "chain-of-thought", "Chain_Of_Thought"):
            self.assertNotIn(key, json.dumps(curated))

    def test_strips_the_coding_reasoning_key_and_internal_reasoning_family(self):
        """Codex #97 P2: this lane must refuse what training_audit refuses.

        ``HIDDEN_THOUGHT_KEYS`` alone (thought/chain_of_thought/scratch/
        inner_monologue) is narrower than ``training_audit``'s
        ``is_hidden_thought_key``, which also refuses the coding-factory key
        ``reasoning`` (exact match only -- ``reasoning_flaw`` stays visible)
        and the whole ``internal_reasoning*`` prefix family. A multi_agent or
        safety_case record carrying either was previously retained here with
        the private field intact, then rejected downstream with no way to
        repair it.
        """
        multi = multi_agent_fixture()
        multi["transcript"][1]["reasoning"] = "hidden coding-style reasoning"
        safety = safety_case_fixture()
        safety["steps"][0]["internal_reasoning_optimizer"] = "hidden optimizer trace"

        for source in (multi, safety):
            self.assertTrue(contains_hidden_thought_key(source))
            curated, decision = curate_record(source)
            self.assertIsNotNone(curated)
            self.assertFalse(contains_hidden_thought_key(curated))
            self.assertIn(REASON_THOUGHT_REMOVED, decision["reason_codes"])
            dumped = json.dumps(curated)
            self.assertNotIn("reasoning", dumped)
            self.assertNotIn("internal_reasoning_optimizer", dumped)
            for path in training_audit.hidden_thought_paths(curated):
                self.fail(f"training_audit still finds a hidden field: {path}")

        # "reasoning" is an exact-match refusal; a merely similar key survives.
        near_miss = multi_agent_fixture()
        near_miss["transcript"][1]["reasoning_flaw"] = "visible critique, not hidden CoT"
        self.assertFalse(contains_hidden_thought_key(near_miss))
        curated, _decision = curate_record(near_miss)
        self.assertIn("reasoning_flaw", json.dumps(curated))

    def test_output_does_not_depend_on_thought_content(self):
        first = episode_fixture(steps=[step(1, thought="secret A")])
        second = episode_fixture(steps=[step(1, thought="entirely different B")])

        first_out, _ = curate_record(first)
        second_out, _ = curate_record(second)

        self.assertEqual(first_out, second_out)

    def test_excludes_preference_collapsed_by_hidden_thought_stripping(self):
        source = preference_fixture()
        source["rejected"] = copy.deepcopy(source["chosen"])
        source["chosen"]["steps"][0]["thought"] = "private rationale A"
        source["rejected"]["steps"][0]["thought"] = "private rationale B"

        curated, decision = curate_record(source)

        self.assertIsNone(curated)
        self.assertEqual(decision["action"], ACTION_EXCLUDED)
        self.assertIn(REASON_THOUGHT_REMOVED, decision["reason_codes"])
        self.assertIn(REASON_PREFERENCE_COLLAPSED, decision["reason_codes"])

    def test_excludes_identical_visible_responses_with_different_reward_labels(self):
        source = preference_fixture()
        source["rejected"]["steps"] = copy.deepcopy(source["chosen"]["steps"])
        source["rejected"]["outcome"] = source["chosen"]["outcome"]

        curated, decision = curate_record(source)

        self.assertIsNone(curated)
        self.assertEqual(decision["action"], ACTION_EXCLUDED)
        self.assertIn(REASON_PREFERENCE_COLLAPSED, decision["reason_codes"])

    def test_flags_missing_decision_basis_without_inventing_one(self):
        source = episode_fixture(
            steps=[
                {
                    "n": 1,
                    "thought": "the only possible source",
                    "tool_call": {"name": "bash", "args": {"command": "true"}},
                    "observation": "ok",
                }
            ]
        )

        curated, decision = curate_record(source)

        self.assertIsNotNone(curated)
        self.assertNotIn("decision_basis", curated["steps"][0])
        self.assertEqual(decision["action"], ACTION_FLAGGED)
        self.assertIn(REASON_MISSING_BASIS, decision["reason_codes"])
        self.assertEqual(decision["missing_decision_basis"], ["steps[0]"])
        self.assertIn(REASON_THOUGHT_REMOVED, decision["reason_codes"])

    def test_flags_tool_turns_on_multi_agent_and_safety(self):
        multi = multi_agent_fixture()
        multi["transcript"][1].pop("decision_basis")
        _, multi_decision = curate_record(multi)
        self.assertEqual(multi_decision["action"], ACTION_FLAGGED)
        self.assertEqual(
            multi_decision["missing_decision_basis"], ["transcript[1]"]
        )

        safety = safety_case_fixture(
            steps=[{"n": 1, "tool_call": {"name": "refuse"}, "observation": "no"}]
        )
        _, safety_decision = curate_record(safety)
        self.assertIn("steps[0]", safety_decision["missing_decision_basis"])

    def test_preference_requires_shared_goal(self):
        ok, reason = shared_preference_goal(preference_fixture())
        self.assertTrue(ok)
        self.assertIsNone(reason)

        only_chosen_goal = preference_fixture(
            goal=None,
            chosen={"goal": "write output.json atomically"},
        )
        ok, reason = shared_preference_goal(only_chosen_goal)
        self.assertFalse(ok)
        self.assertEqual(reason, REASON_GOAL_MISSING)

        diverged = preference_fixture(
            chosen={"goal": "write output.json atomically"},
            rejected={"goal": "rewrite the scheduler instead"},
        )
        curated, decision = curate_record(diverged)
        self.assertIsNone(curated)
        self.assertEqual(decision["action"], ACTION_EXCLUDED)
        self.assertIn(REASON_GOAL_DIVERGES, decision["reason_codes"])

        missing = preference_fixture()
        missing.pop("goal")
        curated, decision = curate_record(missing)
        self.assertIsNone(curated)
        self.assertIn(REASON_GOAL_MISSING, decision["reason_codes"])

    def test_inherited_top_level_goal_counts_as_shared(self):
        record = preference_fixture()
        self.assertNotIn("goal", record["chosen"])
        self.assertNotIn("goal", record["rejected"])
        curated, decision = curate_record(record)
        self.assertIsNotNone(curated)
        self.assertEqual(decision["action"], ACTION_RETAINED)

    def test_preference_rejects_non_text_goals(self):
        for place, value in (
            ("goal", {"task": "write atomically"}),
            ("chosen.goal", ["write atomically"]),
            ("rejected.goal", 3),
            ("goal", "   "),
        ):
            with self.subTest(place=place, value=value):
                record = preference_fixture()
                if place == "goal":
                    record["goal"] = value
                else:
                    side, _field = place.split(".")
                    record[side]["goal"] = value
                curated, decision = curate_record(record)
                self.assertIsNone(curated)
                self.assertIn(REASON_GOAL_NOT_TEXT, decision["reason_codes"])

    def test_prefix_overlap_is_optional_note_not_a_fail(self):
        shared = step(1, "Plan: inspect lock file")
        record = preference_fixture(
            chosen={
                "steps": [shared, step(2, "Plan: write temp then rename")]
            },
            rejected={
                "steps": [
                    copy.deepcopy(shared),
                    step(2, "Plan: write destination in place"),
                ]
            },
        )

        overlap = prefix_overlap(record["chosen"], record["rejected"])
        self.assertEqual(overlap["shared_steps"], 1)
        self.assertTrue(overlap["noted"])

        curated, decision = curate_record(record)
        self.assertIsNotNone(curated)
        self.assertEqual(decision["prefix_overlap"]["shared_steps"], 1)
        self.assertIn(REASON_PREFIX_OVERLAP, decision["reason_codes"])
        self.assertNotEqual(decision["action"], ACTION_EXCLUDED)

        zero = preference_fixture()
        _, zero_decision = curate_record(zero)
        self.assertEqual(zero_decision["prefix_overlap"]["shared_steps"], 0)
        self.assertNotIn(REASON_PREFIX_OVERLAP, zero_decision["reason_codes"])

    def test_prefix_overlap_ignores_hidden_thought_text(self):
        left = step(1, "Plan: inspect", thought="secret A")
        right = step(1, "Plan: inspect", thought="secret B")
        overlap = prefix_overlap({"steps": [left]}, {"steps": [right]})
        self.assertEqual(overlap["shared_steps"], 1)

    def test_skips_thalamic_and_does_not_mutate_input(self):
        source = episode_fixture(steps=[step(1, thought="scratch")])
        original = copy.deepcopy(source)

        curate_record(source)
        self.assertEqual(source, original)

        skipped, decision = curate_record(thalamic_fixture())
        self.assertIsNone(skipped)
        self.assertEqual(decision["action"], ACTION_SKIPPED)
        self.assertIn(REASON_SKIPPED_KIND, decision["reason_codes"])

    def test_transform_is_output_idempotent(self):
        source = episode_fixture(steps=[step(1, thought="scratch")])
        once, _ = curate_record(source)
        twice, second = curate_record(once)
        self.assertEqual(once, twice)
        self.assertEqual(second["action"], ACTION_RETAINED)
        self.assertEqual(second["thought_fields_removed"], 0)

    def test_missing_basis_paths_cover_preference_sides(self):
        record = preference_fixture(
            chosen={
                "steps": [
                    {"n": 1, "tool_call": {"name": "x"}, "observation": "a"}
                ]
            },
            rejected={"steps": [step(1)]},
        )
        paths = missing_decision_basis_paths(record)
        self.assertEqual(paths, ["chosen.steps[0]"])

    def test_missing_basis_paths_include_non_object_steps(self):
        paths = missing_decision_basis_paths({"steps": [None, "not a turn", step(3)]})
        self.assertEqual(paths, ["steps[0]", "steps[1]"])


if __name__ == "__main__":
    unittest.main()
