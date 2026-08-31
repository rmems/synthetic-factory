#!/usr/bin/env python3
"""Cohesive execution-verifier regression suite."""

import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "pipelines"))

from gate_fixtures import episode_side  # noqa: E402
import verify_execution  # noqa: E402
import verify_execution_shapes  # noqa: E402


class VerifyExecutionEnvelopes(unittest.TestCase):
    def test_missing_decision_basis_is_a_structural_episode_failure(self):
        episode = {
            "goal": "inspect a file safely",
            "steps": [
                {
                    "tool_call": {"name": "read_file", "args": {"path": "a.txt"}},
                    "observation": "file has three lines",
                }
            ],
            "outcome": "inspection completed",
            "reward": {"success": True},
        }

        status, reason = verify_execution.verify_record_execution(episode, "where")

        self.assertEqual(status, "failed")
        self.assertIn("missing 'decision_basis'", reason)


    def test_refusal_step_is_verifiable_evidence(self):
        status, _ = verify_execution_shapes.verify_episode_steps(
            [
                {
                    "n": 1,
                    "decision_basis": "the request asks for live secrets",
                    "tool_call": {"name": "refuse", "args": {"reason": "secrets"}},
                    "observation": "refused",
                }
            ],
            "where",
        )
        self.assertEqual(status, "verified")


    def test_shape_error_helpers_reject_unparseable_step_indexes(self):
        self.assertIsNone(
            verify_execution_shapes._step_index_from_shape_error("other step 0: missing", "where")
        )
        self.assertIsNone(
            verify_execution_shapes._step_index_from_shape_error("where step 0", "where")
        )
        self.assertIsNone(
            verify_execution_shapes._step_index_from_shape_error(
                "where step x: tool_call must be an object", "where"
            )
        )
        self.assertFalse(
            verify_execution_shapes._is_missing_execution_evidence(
                "where step 0: tool_call must be an object",
                "where",
                {"steps": []},
            )
        )
        self.assertFalse(
            verify_execution_shapes._is_missing_execution_evidence(
                "where step 0: tool_call must be an object",
                "where",
                {"steps": "not-a-list"},
            )
        )


    def test_episode_and_safety_fail_closed_without_shape_checkers(self):
        status, reason = verify_execution_shapes.verify_episode("not-an-object", "where")
        self.assertEqual(status, "failed")
        self.assertIn("not an object", reason)

        with mock.patch.object(verify_execution, "check_episode", None):
            status, reason = verify_execution_shapes.verify_episode(episode_side(), "where")
        self.assertEqual(status, "failed")
        self.assertIn("episode shape checker unavailable", reason)

        with mock.patch.object(verify_execution, "check_safety_case", None):
            status, reason = verify_execution_shapes.verify_safety_episode(
                {"case_type": "correct_refusal", "steps": []}, "where"
            )
        self.assertEqual(status, "failed")
        self.assertIn("safety-case shape checker unavailable", reason)

        with mock.patch.object(verify_execution, "check_line", None):
            status, reason = verify_execution.verify_record_execution(
                {"chosen": episode_side(), "rejected": episode_side()},
                "where",
            )
        self.assertEqual(status, "failed")
        self.assertIn("preference shape checker unavailable", reason)

        status, reason = verify_execution.verify_record_execution(
            {"note": "no executable shape"}, "where"
        )
        self.assertEqual(status, "inconclusive")
        self.assertIn("unrecognized shape", reason)


    def test_refusal_helpers_reject_malformed_inputs(self):
        self.assertEqual(verify_execution_shapes._tool_call_name("Refuse now"), "refuse")
        self.assertEqual(verify_execution_shapes._tool_call_name("   "), "")
        self.assertEqual(verify_execution_shapes._tool_call_name(None), "")
        self.assertFalse(verify_execution_shapes._step_records_refusal("not-a-step"))
        self.assertFalse(verify_execution_shapes._step_records_compliance("not-a-step"))
        self.assertIsNone(verify_execution_shapes._calibrated_outcome_kind("nope"))
        self.assertIsNone(
            verify_execution_shapes._calibrated_outcome_kind({"decision": 12})
        )
        self.assertEqual(
            verify_execution_shapes._calibrated_outcome_kind(
                {"case_type": "missed_refusal"}
            ),
            "compliance",
        )
        self.assertIsNone(
            verify_execution_shapes._safety_refusal_contradicts_calibrated_outcome(
                {"case_type": "missed_refusal", "steps": "not-a-list"},
                "where",
            )
        )


    def test_step_less_safety_case_is_a_structural_failure(self):
        record = {
            "goal": "decline the unsafe request",
            "case_type": "correct_refusal",
            "rationale": "the request seeks credentials",
            "decision": "refuse",
            "outcome": "refused safely",
            "reward": {"success": True},
        }

        status, reason = verify_execution.verify_record_execution(record, "where")

        self.assertEqual(status, "failed")
        self.assertIn("safety-case shape invalid", reason)


    def test_unhashable_preference_decision_returns_failed_verdict(self):
        record = {
            "chosen": {
                "state": {"sim_or_real": "designed"},
                "safety_decision": {"decision": [], "rationale": "valid"},
                "future_outcome": {"timeline": [{"event": "ok"}]},
            },
            "rejected": {
                "state": {"sim_or_real": "designed"},
                "safety_decision": {"decision": [], "rationale": "valid"},
                "future_outcome": {"timeline": [{"event": "ok"}]},
            },
        }
        status, reason = verify_execution.verify_record_execution(record, "where")
        self.assertEqual(status, "failed")



if __name__ == "__main__":
    unittest.main()
