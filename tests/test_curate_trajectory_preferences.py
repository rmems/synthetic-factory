#!/usr/bin/env python3
"""Focused tests for the trajectory-pair preference gate.

Grok 4.6 preference dumps are shared-goal, shared-prefix trajectory pairs, not
Fable ``state``/``proposed_action`` pairs. These tests pin the keep / repair /
reject contract of ``pipelines/curate_trajectory_preferences.py`` and the
denominator boundary against ``pipelines/curate_preferences.py``.
"""

import copy
import io
import json
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PIPELINES = REPO / "pipelines"
if str(PIPELINES) not in sys.path:
    sys.path.insert(0, str(PIPELINES))

import curate_preferences  # noqa: E402
import curate_trajectory_preferences as ctp  # noqa: E402

FIXTURE_DIR = REPO / "tests" / "fixtures" / "grok-trajectory-preferences"
PURITY_FIXTURES = REPO / "tests" / "fixtures" / "preference-purity"


def step(n: int, basis: str, command: str = "ls -la", observation: str = "designed: ok"):
    return {
        "n": n,
        "decision_basis": basis,
        "tool_call": {"name": "bash", "args": {"command": command}},
        "observation": observation,
    }


def trajectory_pair(record_id: str = "tpf-1") -> dict:
    """A record shaped exactly like a published Grok preference pair."""

    shared = [step(1, "Observation: the operator asked for a crash-safe publish.")]
    return {
        "id": record_id,
        "goal": "Publish manifest.json so readers never observe a partial object.",
        "outcome": "Chosen renamed a temp file; rejected truncated in place.",
        "reward": {"delta": 0.7},
        "meta": {"round": 1},
        "chosen": {
            "steps": copy.deepcopy(shared)
            + [step(2, "Plan: fsync a temp file, then rename.")],
            "outcome": "Readers only ever see a complete object.",
            "reward": {"success": True, "process_quality": 0.9},
        },
        "rejected": {
            "steps": copy.deepcopy(shared)
            + [step(2, "Plan: truncate the destination in place.")],
            "outcome": "A half-written destination broke the harvest parser.",
            "reward": {"success": False, "process_quality": 0.2},
        },
        "critique": "One goal, one shared prefix, one fork.",
    }


def same_state_pair(record_id: str = "ffpc-1") -> dict:
    """A Fable FFPC pair, which this lane must defer rather than judge."""

    state = {"episode": "e1", "environment": {"queue_depth": 3}}
    proposal = {"action": "flush", "parameters": {"batch": 8}}
    return {
        "id": record_id,
        "chosen": {
            "state": copy.deepcopy(state),
            "proposed_action": copy.deepcopy(proposal),
            "future_outcome": {"ok": True},
        },
        "rejected": {
            "state": copy.deepcopy(state),
            "proposed_action": copy.deepcopy(proposal),
            "future_outcome": {"ok": False},
        },
        "reward_delta": {"total": 0.4},
    }


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

        self.assertEqual(
            ctp.curate_trajectory_pair(source).action, ctp.ACTION_RETAINED
        )

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
            any(
                "must be an object" in error
                for error in decision.side_validation_errors["chosen"]
            )
        )

    def test_empty_steps_are_excluded(self):
        source = trajectory_pair()
        source["chosen"]["steps"] = []

        self.assert_excluded(source, ctp.REASON_STEPS_EMPTY)

    def test_outcome_must_diverge(self):
        source = trajectory_pair()
        source["rejected"]["outcome"] = source["chosen"]["outcome"]

        self.assert_excluded(source, ctp.REASON_OUTCOME_NOT_DIVERGENT)

    def test_reward_must_diverge(self):
        source = trajectory_pair()
        source["rejected"]["reward"] = copy.deepcopy(source["chosen"]["reward"])

        self.assert_excluded(source, ctp.REASON_REWARD_NOT_DIVERGENT)

    def test_missing_outcome_or_reward_is_named(self):
        source = trajectory_pair()
        source["chosen"].pop("outcome")
        source["rejected"].pop("reward")

        self.assert_excluded(
            source, ctp.REASON_OUTCOME_MISSING, ctp.REASON_REWARD_MISSING
        )

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

        self.assertEqual(
            ctp.classify_pair_schema(source), "malformed_trajectory_pair"
        )
        self.assertIn("chosen", decision.side_validation_errors)

    def test_non_object_record_is_excluded(self):
        decision = ctp.curate_trajectory_pair(["not", "a", "record"])

        self.assertEqual(decision.action, ctp.ACTION_EXCLUDED)
        self.assertEqual(decision.reason_codes, (ctp.REASON_RECORD_NOT_OBJECT,))

    def test_every_reject_reason_is_reported_together(self):
        source = trajectory_pair()
        source.pop("goal")
        source["rejected"]["steps"][0] = step(1, "Plan: a different opening move.")
        source["rejected"]["outcome"] = source["chosen"]["outcome"]

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
        self.assertEqual(
            decision.record["rejected"]["goal"], decision.record["chosen"]["goal"]
        )

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


class LaneBoundary(unittest.TestCase):
    def test_same_state_pairs_are_skipped_not_judged(self):
        decision = ctp.curate_trajectory_pair(same_state_pair())

        self.assertEqual(decision.action, ctp.ACTION_SKIPPED)
        self.assertEqual(decision.reason_codes, (ctp.REASON_SAME_STATE_SCHEMA,))
        self.assertIsNone(decision.record)

    def test_non_preference_records_are_skipped(self):
        episode = {"id": "mill-1", "goal": "Rebuild the index.", "steps": [step(1, "b")]}

        decision = ctp.curate_trajectory_pair(episode)

        self.assertEqual(decision.action, ctp.ACTION_SKIPPED)
        self.assertEqual(decision.reason_codes, (ctp.REASON_NOT_A_PAIR,))

    def test_committed_fable_corpus_is_entirely_out_of_scope_here(self):
        # The Fable FFPC corpus must never land in this lane's denominator.
        run = ctp.curate_source(PURITY_FIXTURES)

        self.assertEqual(run.summary["trajectory_pairs_considered"], 0)
        self.assertEqual(run.records, ())
        self.assertEqual(
            run.summary["skipped_same_state_pairs"], run.summary["json_records_seen"]
        )

    def test_same_state_gate_names_trajectory_pairs_out_of_scope(self):
        # Lives here because it pins the boundary this lane depends on: the
        # Fable gate must report a schema mismatch, not a malformed record.
        decision = curate_preferences.curate_preference_record(trajectory_pair())

        self.assertEqual(decision.action, curate_preferences.ACTION_EXCLUDED)
        self.assertEqual(
            decision.classification,
            curate_preferences.CLASSIFICATION_TRAJECTORY_PAIR,
        )
        self.assertEqual(
            decision.reason_codes, (curate_preferences.REASON_TRAJECTORY_PAIR,)
        )

    def test_same_state_gate_still_flags_genuinely_malformed_pairs(self):
        decision = curate_preferences.curate_preference_record(
            {"id": "bad", "chosen": {}, "rejected": {}, "reward_delta": {}}
        )

        self.assertEqual(
            decision.reason_codes, ("PREFERENCE_CONTEXT_MISSING_OR_INVALID",)
        )


class SourceScan(unittest.TestCase):
    def test_fixture_corpus_summary_separates_every_bucket(self):
        run = ctp.curate_source(FIXTURE_DIR)
        summary = run.summary

        self.assertEqual(summary["json_records_seen"], 3)
        self.assertEqual(summary["trajectory_pairs_considered"], 2)
        self.assertEqual(summary["retained_pairs"], 1)
        self.assertEqual(summary["excluded_pairs"], 1)
        self.assertEqual(summary["prefix_overlap_absent_pairs"], 1)
        self.assertEqual(summary["branch_label_only_first_step_pairs"], 1)
        self.assertEqual(summary["skipped_non_preference_records"], 1)
        self.assertEqual(summary["skipped_same_state_pairs"], 0)
        self.assertEqual(summary["retained_gate_pass_pct"], 50.0)
        self.assertEqual(len(run.records), 1)
        self.assertEqual(len(run.manifest), 3)

    def test_manifest_entries_carry_source_and_output_provenance(self):
        run = ctp.curate_source(FIXTURE_DIR)
        retained = run.manifest[0]

        self.assertEqual(retained["source_path"], "batch-r01.jsonl")
        self.assertEqual(retained["source_line"], 1)
        self.assertEqual(retained["action"], ctp.ACTION_RETAINED)
        self.assertEqual(retained["transform"]["name"], ctp.TRANSFORM_NAME)
        self.assertEqual(retained["output_id"], retained["source_record_id"])
        self.assertEqual(len(retained["source_sha256"]), 64)
        self.assertEqual(len(retained["output_sha256"]), 64)
        self.assertEqual(retained["prefix_overlap"]["shared_steps"], 2)
        self.assertEqual(retained["side_validation_errors"], {})

    def test_manifest_surfaces_each_side_episode_shape_error(self):
        source_record = trajectory_pair("malformed-sides")
        source_record["chosen"]["outcome"] = 1
        source_record["rejected"]["steps"] = ["not-a-step"]
        with tempfile.TemporaryDirectory() as td:
            source = Path(td) / "batch-r01.jsonl"
            source.write_text(json.dumps(source_record) + "\n")

            entry = ctp.curate_source(source).manifest[0]

        self.assertEqual(entry["action"], ctp.ACTION_EXCLUDED)
        self.assertIn("chosen", entry["side_validation_errors"])
        self.assertIn("rejected", entry["side_validation_errors"])
        self.assertTrue(
            any(
                "outcome must be a non-empty string" in error
                for error in entry["side_validation_errors"]["chosen"]
            )
        )
        self.assertTrue(
            any(
                "must be an object" in error
                for error in entry["side_validation_errors"]["rejected"]
            )
        )

    def test_scan_does_not_touch_the_source_corpus(self):
        path = FIXTURE_DIR / "batch-r01.jsonl"
        before = path.read_bytes()

        ctp.curate_source(FIXTURE_DIR)

        self.assertEqual(path.read_bytes(), before)

    def test_malformed_json_fails_loudly(self):
        with tempfile.TemporaryDirectory() as td:
            source = Path(td) / "batch-r01.jsonl"
            source.write_text('{"id": "x"}\nnot json\n')

            with self.assertRaises(ctp.TrajectoryCurationError):
                ctp.curate_source(source)

    def test_nan_is_rejected_at_parse_time(self):
        with tempfile.TemporaryDirectory() as td:
            source = Path(td) / "batch-r01.jsonl"
            source.write_text('{"id": "x", "reward": NaN}\n')

            with self.assertRaises(ctp.TrajectoryCurationError):
                ctp.curate_source(source)

    def test_non_jsonl_source_file_is_refused(self):
        with tempfile.TemporaryDirectory() as td:
            source = Path(td) / "batch-r01.json"
            source.write_text("{}\n")

            with self.assertRaises(ctp.TrajectoryCurationError):
                ctp.curate_source(source)


class WriteDestinations(unittest.TestCase):
    def test_curate_writes_pairs_and_manifest_without_clobbering(self):
        with tempfile.TemporaryDirectory() as td:
            destination = Path(td)
            output = destination / "pairs.jsonl"
            manifest = destination / "manifest.jsonl"

            with redirect_stdout(io.StringIO()):
                code = ctp.main(
                    [
                        "curate",
                        str(FIXTURE_DIR),
                        "--output",
                        str(output),
                        "--manifest",
                        str(manifest),
                    ]
                )

            self.assertEqual(code, 0)
            written = output.read_text().splitlines()
            self.assertEqual(len(written), 1)
            emitted = json.loads(written[0])
            self.assertTrue(ctp.pair_passes_gate(emitted))
            self.assertEqual(len(manifest.read_text().splitlines()), 3)

            # Second run must refuse rather than overwrite.
            with redirect_stdout(io.StringIO()):
                rerun = ctp.main(
                    [
                        "curate",
                        str(FIXTURE_DIR),
                        "--output",
                        str(output),
                        "--manifest",
                        str(manifest),
                    ]
                )
            self.assertEqual(rerun, 1)

    def test_output_hash_matches_the_written_line(self):
        with tempfile.TemporaryDirectory() as td:
            destination = Path(td)
            output = destination / "pairs.jsonl"
            manifest = destination / "manifest.jsonl"
            with redirect_stdout(io.StringIO()):
                ctp.main(
                    [
                        "curate",
                        str(FIXTURE_DIR),
                        "--output",
                        str(output),
                        "--manifest",
                        str(manifest),
                    ]
                )
            entry = next(
                json.loads(line)
                for line in manifest.read_text().splitlines()
                if json.loads(line)["output_sha256"]
            )

            self.assertEqual(
                ctp._sha256(output.read_text().splitlines()[0].encode("utf-8")),
                entry["output_sha256"],
            )

    def test_destinations_under_outputs_raw_are_refused(self):
        with tempfile.TemporaryDirectory() as td:
            raw = Path(td) / "outputs" / "raw" / "2026-08-19-agentic"
            raw.mkdir(parents=True)
            output = raw / "pairs.jsonl"
            manifest = Path(td) / "manifest.jsonl"

            with redirect_stdout(io.StringIO()):
                code = ctp.main(
                    [
                        "curate",
                        str(FIXTURE_DIR),
                        "--output",
                        str(output),
                        "--manifest",
                        str(manifest),
                    ]
                )

            self.assertEqual(code, 1)
            self.assertFalse(output.exists())
            self.assertFalse(manifest.exists())


class CommandLine(unittest.TestCase):
    def test_scan_json_reports_summary_and_decisions(self):
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            code = ctp.main(["scan", str(FIXTURE_DIR), "--json"])
        payload = json.loads(buffer.getvalue())

        self.assertEqual(code, 0)
        self.assertEqual(payload["summary"]["retained_pairs"], 1)
        self.assertEqual(len(payload["decisions"]), 3)

    def test_scan_human_output_names_every_decision(self):
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            ctp.main(["scan", str(FIXTURE_DIR)])
        text = buffer.getvalue()

        self.assertIn(ctp.REASON_PREFIX_ABSENT, text)
        self.assertIn(ctp.REASON_BRANCH_LABEL_ONLY, text)
        self.assertIn("Skipped non-preference records: 1", text)

    def test_missing_source_exits_nonzero(self):
        proc = subprocess.run(
            [
                sys.executable,
                str(PIPELINES / "curate_trajectory_preferences.py"),
                "scan",
                str(FIXTURE_DIR / "absent"),
            ],
            capture_output=True,
            text=True,
        )

        self.assertEqual(proc.returncode, 1)
        self.assertIn("source does not exist", proc.stderr)


if __name__ == "__main__":
    unittest.main()
