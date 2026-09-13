#!/usr/bin/env python3
"""Cohesive execution-verifier regression suite."""

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "pipelines"))

from gate_fixtures import episode_side, thalamic  # noqa: E402
import verify_execution  # noqa: E402
import verify_execution_shapes  # noqa: E402


class VerifyExecutionInputs(unittest.TestCase):
    def test_jsonl_keeps_unicode_line_separators_inside_one_record(self):
        record = thalamic("line-separator")
        record["future_outcome"]["timeline"][0]["event"] = (
            "noop accepted\u2028still one record"
        )
        with tempfile.TemporaryDirectory() as td:
            batch = Path(td) / "batch-r01.jsonl"
            batch.write_text(json.dumps(record, ensure_ascii=False) + "\n")
            counts, findings, blocked = verify_execution.verify_batch_for_frontier(
                batch, strict=True
            )
        self.assertFalse(blocked, findings)
        self.assertEqual(counts["verified"], 1)
        self.assertEqual(counts["failed"], 0)
        self.assertEqual(counts["total"], 1)


    def test_non_object_trajectory_returns_verdict(self):
        status, reason = verify_execution_shapes.verify_thalamic("a string", "where")
        self.assertEqual(status, "inconclusive")
        self.assertIn("not an object", reason)


    def test_non_string_rationale_does_not_raise(self):
        status, _ = verify_execution_shapes.verify_thalamic(
            {
                "state": {"sim_or_real": "designed"},
                "safety_decision": {"rationale": {"nested": "object"}},
                "future_outcome": {},
            },
            "where",
        )
        self.assertEqual(status, "failed")


    def test_non_string_observation_is_a_structural_failure(self):
        episode = episode_side()
        episode["goal"] = "inspect a file safely"
        episode["steps"][0]["observation"] = {}

        status, reason = verify_execution.verify_record_execution(episode, "where")

        self.assertEqual(status, "failed")
        self.assertIn("observation must be", reason)


    def test_non_string_observation_without_tool_call_is_a_structural_failure(self):
        episode = episode_side()
        episode["goal"] = "inspect a file safely"
        episode["steps"][0].pop("tool_call")
        episode["steps"][0]["observation"] = {}

        status, reason = verify_execution.verify_record_execution(episode, "where")

        self.assertEqual(status, "failed")
        self.assertIn("observation must be", reason)


    def test_non_string_tool_name_is_a_structural_failure(self):
        episode = episode_side()
        episode["goal"] = "inspect a file safely"
        episode["steps"][0]["tool_call"]["name"] = []

        status, reason = verify_execution.verify_record_execution(episode, "where")

        self.assertEqual(status, "failed")
        self.assertIn("tool_call.name must be a string", reason)


    def test_bridge_with_non_object_trajectory_returns_verdict(self):
        status, reason = verify_execution.verify_record_execution(
            {"language_view": {"trajectory": "oops"}, "spike_events": [1]},
            "where",
        )
        self.assertEqual(status, "failed")
        self.assertIn("record envelope invalid", reason)


    def test_invalid_utf8_batch_returns_failed_verdict(self):
        with tempfile.TemporaryDirectory() as td:
            batch = Path(td) / "batch-r01.jsonl"
            batch.write_bytes(b"{\x80abc: 123}\n")
            counts, findings, blocked = verify_execution.verify_batch_for_frontier(
                batch, strict=True
            )
        self.assertTrue(blocked)
        self.assertEqual(counts["failed"], 1)
        self.assertEqual(counts["total"], 1)


    def test_invalid_utf8_run_and_record_modes_return_failed_verdicts(self):
        with tempfile.TemporaryDirectory() as td:
            batch = Path(td) / "batch-r01.jsonl"
            batch.write_bytes(b"{\x80abc: 123}\n")

            counts, findings, blocked = verify_execution.audit_run(Path(td))
            self.assertTrue(blocked)
            self.assertEqual(counts["failed"], 1)
            self.assertEqual(counts["total"], 1)
            self.assertEqual(findings[0]["status"], "failed")

            with mock.patch("builtins.print") as printed, self.assertRaises(
                SystemExit
            ) as raised:
                verify_execution.main(["--record", str(batch)])
            self.assertEqual(raised.exception.code, 1)
            self.assertTrue(printed.called)



if __name__ == "__main__":
    unittest.main()
