#!/usr/bin/env python3
"""Training-audit coverage for curated hidden-reasoning removal."""

import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path

TESTS = Path(__file__).resolve().parent
sys.path.insert(0, str(TESTS))
from test_training_audit import curate_coding, thalamic, training_audit, write


def coding_wrap(record_id):
    """A Thalamic gate record that wraps a coding episode, as published."""
    record = thalamic(record_id)
    record["proposed_action"]["internal_reasoning"] = "private gate rationale"
    record["proposed_action"]["internal_reasoning_verbatim"] = "verbatim rationale"
    record["executed_action"] = {
        "action": "noop",
        "goal": "Diagnose the failing build.",
        "steps": [
            {
                "n": 1,
                "thought": "private step scratch",
                "tool_call": {"name": "bash", "args": {"command": "pytest -q"}},
                "observation": "Two tests failed with a timezone mismatch.",
                "reflection": "The failure is deterministic outside UTC.",
            }
        ],
        "outcome": "The visible evidence isolated the defect.",
        "reward": {"success": True},
    }
    return record


class CuratedViewHasNoHiddenReasoning(unittest.TestCase):
    """`training_audit --strict` is the gate that keeps published CoT out."""

    def test_wrap_record_hidden_reasoning_blocks_training(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            write(
                root / "agentic-coding-trajectory-factory" / "batch-r02.jsonl",
                [coding_wrap("wrap-1")],
            )
            report = training_audit.audit_run(root)

        self.assertEqual(report["episodes"]["hidden_thought_fields"], 3)
        self.assertEqual(
            sorted(path.split(":", 2)[2] for path in report["hidden_thought_examples"]),
            [
                "executed_action.steps[0].thought",
                "proposed_action.internal_reasoning",
                "proposed_action.internal_reasoning_verbatim",
            ],
        )
        self.assertTrue(
            any("internal_reasoning*" in item for item in report["blockers"]),
            report["blockers"],
        )
        self.assertFalse(report["training_ready"])

    def test_strict_cli_fails_on_a_curated_file_that_keeps_the_keys(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            curated = root / "curated" / "agentic-coding-trajectory-factory"
            write(curated / "batch-r02.jsonl", [coding_wrap("wrap-cli-1")])

            captured = io.StringIO()
            with contextlib.redirect_stdout(captured):
                code = training_audit.main(["--strict", str(root / "curated")])

        self.assertEqual(code, 1)
        self.assertIn("internal_reasoning*", captured.getvalue())

    def test_wrap_steps_receive_strict_agentic_structural_validation(self):
        source = coding_wrap("wrap-structural-1")
        source["executed_action"]["steps"][0]["tool_call"] = "not-object"
        curated, _manifest = curate_coding.curate_episode(source)
        self.assertIsNotNone(curated)

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            write(
                root / "agentic-coding-trajectory-factory" / "batch-r02.jsonl",
                [curated],
            )
            report = training_audit.audit_run(root)

        self.assertEqual(report["episodes"]["steps"], 1)
        self.assertTrue(
            any(
                "executed_action step 0: tool_call must be an object" in error
                for error in report["record_invariants"]["error_examples"]
            ),
            report["record_invariants"],
        )
        self.assertFalse(report["training_ready"])

    def test_non_array_wrap_steps_receive_structural_validation(self):
        for malformed_steps in (None, "not-an-array", {"n": 1}):
            with self.subTest(malformed_steps=malformed_steps):
                source = coding_wrap("wrap-structural-container")
                source["proposed_action"].pop("internal_reasoning")
                source["proposed_action"].pop("internal_reasoning_verbatim")
                source["executed_action"]["steps"] = malformed_steps

                with tempfile.TemporaryDirectory() as td:
                    root = Path(td)
                    write(
                        root
                        / "agentic-coding-trajectory-factory"
                        / "batch-r02.jsonl",
                        [source],
                    )
                    report = training_audit.audit_run(root)

                self.assertIn(
                    "agentic-coding-trajectory-factory/batch-r02.jsonl:1."
                    "executed_action: steps must be a non-empty array",
                    report["record_invariants"]["error_examples"],
                )
                self.assertFalse(report["training_ready"])

    def test_wrap_episode_missing_steps_receives_structural_validation(self):
        source = coding_wrap("wrap-missing-steps")
        source["proposed_action"].pop("internal_reasoning")
        source["proposed_action"].pop("internal_reasoning_verbatim")
        source["executed_action"].pop("steps")

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            write(
                root / "agentic-coding-trajectory-factory" / "batch-r02.jsonl",
                [source],
            )
            report = training_audit.audit_run(root)

        self.assertIn(
            "agentic-coding-trajectory-factory/batch-r02.jsonl:1."
            "executed_action: episode missing 'steps'",
            report["record_invariants"]["error_examples"],
        )
        self.assertIn(
            "agentic-coding-trajectory-factory/batch-r02.jsonl:1."
            "executed_action: steps must be a non-empty array",
            report["record_invariants"]["error_examples"],
        )
        self.assertFalse(report["training_ready"])

    def test_wrap_reasoning_key_blocks_training(self):
        source = coding_wrap("wrap-reasoning-key")
        source["proposed_action"].pop("internal_reasoning")
        source["proposed_action"].pop("internal_reasoning_verbatim")
        source["executed_action"]["steps"][0].pop("thought")
        source["proposed_action"]["reasoning"] = "private gate trace"
        source["executed_action"]["steps"][0]["reasoning"] = "private step trace"

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            write(
                root / "agentic-coding-trajectory-factory" / "batch-r02.jsonl",
                [source],
            )
            report = training_audit.audit_run(root)

        self.assertEqual(report["episodes"]["hidden_thought_fields"], 2)
        self.assertEqual(
            sorted(path.split(":", 2)[2] for path in report["hidden_thought_examples"]),
            [
                "executed_action.steps[0].reasoning",
                "proposed_action.reasoning",
            ],
        )
        self.assertFalse(report["training_ready"])

    def test_strict_audit_passes_after_curation_strips_reasoning(self):
        source = coding_wrap("wrap-reasoning-curated")
        source["proposed_action"]["reasoning"] = "private gate trace"
        source["executed_action"]["steps"][0]["reasoning"] = "private step trace"
        curated, manifest = curate_coding.curate_episode(source)
        self.assertIsNotNone(curated)
        self.assertNotIn("reasoning", curated["proposed_action"])
        self.assertNotIn("reasoning", curated["executed_action"]["steps"][0])
        self.assertEqual(manifest["hidden_reasoning_fields_removed"], 5)

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            write(
                root / "agentic-coding-trajectory-factory" / "batch-r02.jsonl",
                [curated],
            )
            report = training_audit.audit_run(root)

        self.assertEqual(report["episodes"].get("hidden_thought_fields", 0), 0)
        self.assertEqual(report["hidden_thought_examples"], [])
        self.assertEqual(report["blockers"], [])
        self.assertTrue(report["training_ready"])

    def test_undelimited_internal_reasoning_suffixes_block_training(self):
        source = thalamic("wrap-reasoning-prefix")
        source["proposed_action"]["internal_reasoning2"] = "private numbered trace"
        source["proposed_action"]["internal_reasoningverbatim"] = "private verbatim trace"

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            write(
                root / "agentic-coding-trajectory-factory" / "batch-r02.jsonl",
                [source],
            )
            report = training_audit.audit_run(root)

        self.assertEqual(report["episodes"]["hidden_thought_fields"], 2)
        self.assertEqual(
            sorted(path.split(":", 2)[2] for path in report["hidden_thought_examples"]),
            [
                "proposed_action.internal_reasoning2",
                "proposed_action.internal_reasoningverbatim",
            ],
        )
        self.assertFalse(report["training_ready"])

    def test_strict_cli_passes_once_curate_coding_has_run(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root / "source.jsonl"
            source.write_text(json.dumps(coding_wrap("wrap-cli-2")) + "\n")

            result = curate_coding.curate_jsonl(source)
            self.assertEqual(result["summary"]["output_records"], 1)
            self.assertEqual(result["summary"]["wrap_records"], 1)
            self.assertEqual(result["summary"]["hidden_reasoning_fields_removed"], 3)

            curated = root / "curated" / "agentic-coding-trajectory-factory"
            write(curated / "batch-r02.jsonl", result["records"])
            report = training_audit.audit_run(root / "curated")

        self.assertEqual(report["episodes"].get("hidden_thought_fields", 0), 0)
        self.assertEqual(report["episodes"]["steps"], 1)
        self.assertEqual(report["hidden_thought_examples"], [])
        self.assertEqual(report["blockers"], [])
        self.assertTrue(report["training_ready"])


