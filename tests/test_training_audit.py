#!/usr/bin/env python3
"""Tests for corpus-level training readiness metrics."""

import json
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "pipelines"))

import training_audit  # noqa: E402


def thalamic(record_id, provenance="designed", decision="ACCEPT"):
    return {
        "id": record_id,
        "state": {"sim_or_real": provenance, "domain": "audit-test"},
        "proposed_action": {"action": "noop", "decision_basis": "fixture"},
        "safety_decision": {"decision": decision, "rationale": "bounded fixture"},
        "executed_action": {"action": "noop"},
        "future_outcome": {"success": True},
        "reward_components": {"task_progress": 0.5, "safety": 0.5, "total": 1.0},
        "meta": {"tags": ["audit", "fixture"], "round": 1},
    }


def write(path, records):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(record) + "\n" for record in records))


def episode_preference(record_id, *, pair_goal=None, chosen_goal=None, rejected_goal=None):
    def side(goal):
        record = {
            "steps": [
                {
                    "decision_basis": "fixture observation",
                    "tool_call": {"name": "inspect", "args": {}},
                    "observation": "fixture result",
                }
            ],
            "outcome": "fixture complete",
            "reward": {"success": True},
        }
        if goal is not None:
            record["goal"] = goal
        return record

    record = {
        "id": record_id,
        "chosen": side(chosen_goal),
        "rejected": side(rejected_goal),
        "critique": "chosen path is safer",
        "reward": {"success": True},
    }
    if pair_goal is not None:
        record["goal"] = pair_goal
    return record


class TrainingAudit(unittest.TestCase):
    def test_clean_corpus_is_training_ready(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            write(root / "thalamic-trajectory-factory" / "batch-r01.jsonl", [thalamic("clean-1")])
            report = training_audit.audit_run(root)

        self.assertTrue(report["training_ready"], report["blockers"])
        self.assertEqual(report["totals"]["records"], 1)
        self.assertEqual(report["identity"]["coverage_pct"], 100.0)
        self.assertEqual(report["provenance"]["canonical_pct"], 100.0)
        self.assertEqual(report["rewards"]["unique_shapes"], 1)
        self.assertGreater(report["totals"]["approx_tokens"], 0)

    def test_marked_gate_errors_are_counted(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            wrong = thalamic("gate-err-1", decision="MODIFY")
            wrong["safety_decision"]["correctness"] = "incorrect"
            wrong["meta"]["supervisor_error_type"] = "wrong-modify"
            clean = thalamic("gate-ok-1")
            write(root / "thalamic-trajectory-factory" / "batch-r01.jsonl", [wrong, clean])
            report = training_audit.audit_run(root)
            markdown = training_audit.render_markdown(report)

        self.assertEqual(report["gate_errors"]["marked"], 1)
        self.assertEqual(report["gate_errors"]["by_type"], {"wrong-modify": 1})
        self.assertTrue(report["gate_errors"]["examples"])
        self.assertIn("Intentional gate-error records", markdown)

    def test_legacy_meta_id_and_thought_are_reported_separately(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            episode = {
                "goal": "legacy",
                "steps": [
                    {
                        "thought": "scratch",
                        "tool_call": {"name": "rg", "args": {}},
                        "observation": "none",
                    }
                ],
                "outcome": "done",
                "reward": {"success": True},
                "meta": {"id": "legacy-meta"},
            }
            write(root / "coding" / "legacy.jsonl", [episode])
            report = training_audit.audit_run(root)

        self.assertEqual(report["identity"]["coverage_pct"], 0.0)
        self.assertEqual(report["identity"]["legacy_meta_fallback_records"], 1)
        self.assertEqual(report["episodes"]["legacy_thought_only_steps"], 1)
        self.assertFalse(report["training_ready"])

    def test_reports_preference_and_bridge_training_blockers(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            chosen = thalamic("chosen", decision="MODIFY")
            rejected = thalamic("rejected", decision="ACCEPT")
            rejected["state"]["domain"] = "changed-problem"
            pair = {
                "id": "pref-1",
                "chosen": chosen,
                "rejected": rejected,
                "critique": "same proposal but changed state",
            }
            bridge_trajectory = thalamic("bridge-inner", provenance="real")
            bridge = {
                "id": "bridge-1",
                "spike_events": [
                    {"channel": "a", "t_rel_ms": 2.0, "amplitude": 0.5},
                    {"channel": "b", "t_rel_ms": 1.0, "amplitude": 0.4},
                ],
                "language_view": {"trajectory": bridge_trajectory},
            }
            write(root / "failure-as-fuel-preference-cascade" / "batch-r01.jsonl", [pair])
            write(root / "neuromorphic-event-language-bridge" / "batch-r01.jsonl", [bridge])

            report = training_audit.audit_run(root)
            markdown = training_audit.render_markdown(report)

        self.assertFalse(report["training_ready"])
        self.assertEqual(report["preferences"]["pairs"], 1)
        self.assertEqual(report["preferences"]["same_context"], 0)
        self.assertEqual(report["preferences"]["chosen_decisions"], {"MODIFY": 1})
        self.assertEqual(report["bridge"].get("sorted_pairs", 0), 0)
        self.assertEqual(report["bridge"]["unsorted_pairs"], 1)
        self.assertEqual(report["provenance"]["counts"]["non_training"], 1)
        self.assertIn("preference pairs", " ".join(report["blockers"]))
        self.assertIn("bridge pairs", " ".join(report["blockers"]))
        self.assertIn("Training blockers", markdown)

    def test_missing_bridge_stream_is_not_mislabeled_unsorted(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            bridge = {
                "id": "missing-stream",
                "spike_events": [],
                "language_view": {"trajectory": thalamic("inner")},
            }
            write(root / "bridge" / "batch.jsonl", [bridge])
            report = training_audit.audit_run(root)

        self.assertEqual(report["bridge"]["missing_pairs"], 1)
        self.assertEqual(report["bridge"].get("unsorted_pairs", 0), 0)
        self.assertTrue(any("lack event streams" in item for item in report["blockers"]))

    def test_malformed_preference_does_not_crash_audit(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            malformed = {
                "id": "bad-pref",
                "chosen": "not-an-object",
                "rejected": thalamic("rejected"),
                "critique": "malformed fixture",
            }
            write(root / "prefs" / "batch.jsonl", [malformed])
            report = training_audit.audit_run(root)

        self.assertEqual(report["preferences"]["pairs"], 1)
        self.assertEqual(report["preferences"]["same_context"], 0)
        self.assertGreater(report["record_invariants"]["errors"], 0)

    def test_episode_preference_uses_shared_goal_not_thalamic_context(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            valid = episode_preference("episode-pref", pair_goal="repair the cache")
            write(root / "tool-use-preference-factory" / "batch-r01.jsonl", [valid])

            report = training_audit.audit_run(root)

        self.assertTrue(report["training_ready"], report["blockers"])
        self.assertEqual(report["preferences"]["episode_pairs"], 1)
        self.assertEqual(report["preferences"]["same_goal"], 1)
        self.assertEqual(report["preferences"]["same_context"], 1)
        self.assertEqual(report["preferences"]["same_state"], 0)
        self.assertEqual(report["preferences"]["same_proposal"], 0)

    def test_episode_preference_with_mismatched_side_goals_blocks_training(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            invalid = episode_preference(
                "episode-pref-mismatch",
                chosen_goal="repair the cache",
                rejected_goal="rotate credentials",
            )
            write(root / "tool-use-preference-factory" / "batch-r01.jsonl", [invalid])

            report = training_audit.audit_run(root)

        self.assertFalse(report["training_ready"])
        self.assertEqual(report["preferences"]["same_goal"], 0)
        self.assertTrue(any("shared-goal" in item for item in report["blockers"]))

    def test_episode_preference_legacy_thought_blocks_training(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            record = episode_preference("episode-pref-hidden-thought", pair_goal="repair the cache")
            step = record["chosen"]["steps"][0]
            step.pop("decision_basis")
            step["thought"] = "private reasoning must not become training data"
            write(root / "tool-use-preference-factory" / "batch-r01.jsonl", [record])

            report = training_audit.audit_run(root)

        self.assertEqual(report["episodes"]["legacy_thought_only_steps"], 1)
        self.assertFalse(report["training_ready"])
        self.assertTrue(any("hidden-thought" in item for item in report["blockers"]))

    def test_audit_rejects_recursive_hidden_thought_fields_with_basis(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            record = episode_preference("episode-pref-recursive-thought", pair_goal="repair the cache")
            record["rejected"]["steps"][0]["tool_call"]["args"]["scratch"] = "private"
            write(root / "tool-use-preference-factory" / "batch-r01.jsonl", [record])

            report = training_audit.audit_run(root)

        self.assertEqual(report["episodes"]["hidden_thought_fields"], 1)
        self.assertFalse(report["training_ready"])

    def test_episode_preference_does_not_let_wrapper_goal_mask_side_conflict(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            conflicting = episode_preference(
                "episode-pref-wrapper-conflict",
                pair_goal="repair the cache",
                chosen_goal="repair the cache",
                rejected_goal="rotate credentials",
            )
            write(root / "tool-use-preference-factory" / "batch-r01.jsonl", [conflicting])

            report = training_audit.audit_run(root)

        self.assertFalse(report["training_ready"])
        self.assertEqual(report["preferences"]["same_goal"], 0)

    def test_exact_duplicate_and_global_id_duplicate_are_distinct_metrics(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            record = thalamic("dup")
            write(root / "a" / "one.jsonl", [record])
            write(root / "b" / "two.jsonl", [record])
            report = training_audit.audit_run(root)

        self.assertEqual(len(report["identity"]["duplicates"]), 1)
        self.assertEqual(len(report["exact_duplicates"]), 1)
        self.assertFalse(report["training_ready"])

    def test_reward_arithmetic_error_blocks_training(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            record = thalamic("bad-reward")
            record["reward_components"]["total"] = 99.0
            write(root / "f" / "bad.jsonl", [record])
            report = training_audit.audit_run(root)

        self.assertEqual(report["record_invariants"]["errors"], 1)
        self.assertIn("recomputed", report["record_invariants"]["error_examples"][0])
        self.assertFalse(report["training_ready"])

    def test_invalid_utf8_is_reported_without_crashing(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            path = root / "f" / "bad.jsonl"
            path.parent.mkdir(parents=True)
            path.write_bytes(b'{"id":"bad-\xff"}\n')
            report = training_audit.audit_run(root)

        self.assertFalse(report["training_ready"])
        self.assertTrue(
            any("invalid UTF-8" in item for item in report["record_invariants"]["error_examples"]),
            report["record_invariants"],
        )


if __name__ == "__main__":
    unittest.main()
