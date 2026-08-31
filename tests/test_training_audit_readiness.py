#!/usr/bin/env python3
"""training_audit.py's corpus-level training_ready verdict and blockers.

A clean corpus reports training_ready; a gate error, reward-arithmetic
mismatch, non-standard JSON numeric constant, invalid UTF-8, duplicate id,
or legacy meta.id/thought warning must each surface in the report's
blockers/metrics without raising.
"""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

_TESTS = Path(__file__).resolve().parent
if str(_TESTS) not in sys.path:
    sys.path.insert(0, str(_TESTS))

from training_audit_test_helpers import (  # noqa: E402
    REPO,
    commit_marker_batch,
    thalamic,
    write,
)

import training_audit  # noqa: E402


class TrainingAuditReadinessReport(unittest.TestCase):
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

    def test_empty_corpus_is_not_training_ready(self):
        with tempfile.TemporaryDirectory() as td:
            report = training_audit.audit_run(Path(td))

        self.assertFalse(report["training_ready"])
        self.assertIn(
            "corpus contains 0 eligible training records",
            report["blockers"],
        )

    def test_marker_mode_hides_uncommitted_batches(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "run"
            factory = root / "agentic-factory"
            committed = factory / "batch-r01.jsonl"
            write(committed, [thalamic("committed")])
            commit_marker_batch(factory, committed)
            (factory / "batch-r02.jsonl").write_text("{not json}\n")
            (factory / "ROUND-r02.publishing.json").write_text("{}\n")
            report = training_audit.audit_run(root)

        self.assertEqual(report["totals"]["files"], 1)
        self.assertEqual(report["totals"]["records"], 1)
        self.assertEqual(report["totals"]["eligible_records"], 1)
        self.assertTrue(report["training_ready"], report["blockers"])

    def test_cli_bounds_unsafe_marker_mode_transaction_error(self):
        with tempfile.TemporaryDirectory() as td:
            factory = Path(td) / "thalamic-trajectory-factory"
            write(factory / "batch-r01.jsonl", [thalamic("unsafe-marker")])
            (factory / ".round-marker-mode.json").mkdir()
            result = subprocess.run(
                [
                    sys.executable,
                    str(REPO / "pipelines" / "training_audit.py"),
                    str(factory),
                ],
                capture_output=True,
                text=True,
                check=False,
            )

        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stdout, "")
        self.assertIn("training_audit failed: unsafe marker mode file", result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def test_suffixed_snapshot_root_keeps_factory_directories_distinct(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "pre-window-factory"
            write(
                root / "thalamic-trajectory-factory" / "batch-r01.jsonl",
                [thalamic("clean-1")],
            )
            write(
                root / "safety-calibration-factory" / "batch-r01.jsonl",
                [thalamic("clean-2")],
            )
            report = training_audit.audit_run(root)

        self.assertEqual(
            set(report["factories"]),
            {"safety-calibration-factory", "thalamic-trajectory-factory"},
        )
        self.assertNotIn("pre-window-factory", report["factories"])

    def test_off_registry_factory_root_keeps_nested_legacy_identity(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "custom-experiment-factory"
            write(root / "archive" / "batch-r01.jsonl", [thalamic("clean-1")])
            report = training_audit.audit_run(root)

        self.assertEqual(set(report["factories"]), {"custom-experiment-factory"})
        self.assertNotIn("archive", report["factories"])

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

    def test_nonstandard_json_numeric_constants_block_training(self):
        for value in (float("nan"), float("inf"), float("-inf")):
            with self.subTest(value=value), tempfile.TemporaryDirectory() as td:
                root = Path(td)
                record = thalamic("nonstandard-number")
                record["state"]["measurement"] = value
                write(root / "thalamic-trajectory-factory" / "batch-r01.jsonl", [record])

                report = training_audit.audit_run(root)

                self.assertFalse(report["training_ready"])
                self.assertTrue(
                    any(
                        "non-standard JSON numeric constant" in error
                        for error in report["record_invariants"]["error_examples"]
                    ),
                    report["record_invariants"],
                )

    def test_invalid_utf8_is_reported_without_crashing(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            path = root / "f" / "bad.jsonl"
            path.parent.mkdir(parents=True)
            valid = json.dumps(thalamic("valid-after-bad")).encode("utf-8")
            path.write_bytes(b'{"id":"bad-\xff"}\n' + valid + b"\n")
            report = training_audit.audit_run(root)

        self.assertFalse(report["training_ready"])
        self.assertEqual(report["totals"]["records"], 1)
        self.assertEqual(report["totals"]["eligible_records"], 1)
        self.assertTrue(
            any(
                "bad.jsonl:1: invalid UTF-8" in item
                for item in report["record_invariants"]["error_examples"]
            ),
            report["record_invariants"],
        )


if __name__ == "__main__":
    unittest.main()
