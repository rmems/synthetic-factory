#!/usr/bin/env python3
"""Execution-verifier tests for Thalamic, episode, and outcome evidence."""

import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "pipelines"))

from gate_fixtures import episode_side, thalamic  # noqa: E402
import verify_execution  # noqa: E402


class VerifyExecution(unittest.TestCase):
    def test_non_object_trajectory_returns_verdict(self):
        status, reason = verify_execution.verify_thalamic("a string", "where")
        self.assertEqual(status, "inconclusive")
        self.assertIn("not an object", reason)

    def test_non_string_rationale_does_not_raise(self):
        status, _ = verify_execution.verify_thalamic(
            {
                "state": {"sim_or_real": "designed"},
                "safety_decision": {"rationale": {"nested": "object"}},
                "future_outcome": {},
            },
            "where",
        )
        self.assertEqual(status, "failed")

    def test_malformed_observable_fields_are_not_verified(self):
        for field, value in (
            ("timeline", "narrative"),
            ("new_state", True),
            ("state_delta", True),
            ("surprises", {"not": "an array"}),
            ("latency_ms", True),
        ):
            with self.subTest(field=field):
                record = thalamic(f"malformed-{field}")
                record["future_outcome"] = {field: value}
                status, reason = verify_execution.verify_record_execution(
                    record, "where"
                )
                self.assertEqual(status, "failed")
                self.assertIn(f"future_outcome.{field} must be", reason)

    def test_factory_outcome_vocabulary_is_observable_evidence(self):
        outcomes = (
            {
                "state_delta": {"position_m": [1.0, 1.2]},
                "surprises": [{"delay_ms": 50, "effect": "thermal rise"}],
                "reward_inflection_t_us": 123456,
            },
            {"latency_ms": 41.0},
            {"hazard_avoided": "sensor_blind_advance"},
            {"incident": "guard tripped downstream"},
        )
        for index, outcome in enumerate(outcomes):
            with self.subTest(outcome=outcome):
                record = thalamic(f"outcome-vocabulary-{index}")
                record["future_outcome"] = outcome
                status, _reason = verify_execution.verify_record_execution(
                    record, "where"
                )
                self.assertEqual(status, "verified")

    def test_negative_timing_metrics_are_not_observable_evidence(self):
        for field in (
            "divergence_detected_ms",
            "latency_ms",
            "reward_inflection_t_us",
            "slip_arrested_ms",
        ):
            with self.subTest(field=field):
                record = thalamic(f"negative-{field}")
                record["future_outcome"] = {field: -1}

                status, reason = verify_execution.verify_record_execution(
                    record, "where"
                )

                self.assertEqual(status, "failed")
                self.assertIn("must be a non-negative finite number", reason)

    def test_oversized_integer_metric_returns_a_failed_verdict(self):
        record = thalamic("oversized-latency")
        record["future_outcome"] = {"latency_ms": 10**1000}

        status, reason = verify_execution.verify_record_execution(record, "where")

        self.assertEqual(status, "failed")
        self.assertIn("future_outcome.latency_ms must be a finite number", reason)

    def test_bridge_with_non_object_trajectory_returns_verdict(self):
        status, reason = verify_execution.verify_record_execution(
            {"language_view": {"trajectory": "oops"}, "spike_events": [1]},
            "where",
        )
        self.assertEqual(status, "inconclusive")
        self.assertIn("not an object", reason)

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
        status, _ = verify_execution.verify_episode_steps(
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
            verify_execution._step_index_from_shape_error("other step 0: missing", "where")
        )
        self.assertIsNone(
            verify_execution._step_index_from_shape_error("where step 0", "where")
        )
        self.assertIsNone(
            verify_execution._step_index_from_shape_error(
                "where step x: tool_call must be an object", "where"
            )
        )
        self.assertFalse(
            verify_execution._is_missing_execution_evidence(
                "where step 0: tool_call must be an object",
                "where",
                {"steps": []},
            )
        )
        self.assertFalse(
            verify_execution._is_missing_execution_evidence(
                "where step 0: tool_call must be an object",
                "where",
                {"steps": "not-a-list"},
            )
        )

    def test_episode_and_safety_fail_closed_without_shape_checkers(self):
        status, reason = verify_execution.verify_episode("not-an-object", "where")
        self.assertEqual(status, "failed")
        self.assertIn("not an object", reason)

        with mock.patch.object(verify_execution, "check_episode", None):
            status, reason = verify_execution.verify_episode(episode_side(), "where")
        self.assertEqual(status, "failed")
        self.assertIn("episode shape checker unavailable", reason)

        with mock.patch.object(verify_execution, "check_safety_case", None):
            status, reason = verify_execution.verify_safety_episode(
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
        self.assertEqual(verify_execution._tool_call_name("Refuse now"), "refuse")
        self.assertEqual(verify_execution._tool_call_name("   "), "")
        self.assertEqual(verify_execution._tool_call_name(None), "")
        self.assertFalse(verify_execution._step_records_refusal("not-a-step"))
        self.assertFalse(verify_execution._step_records_compliance("not-a-step"))
        self.assertFalse(verify_execution._calibrated_outcome_is_refusal("nope"))
        self.assertFalse(
            verify_execution._calibrated_outcome_is_compliance_or_leakage("nope")
        )
        self.assertFalse(
            verify_execution._calibrated_outcome_is_compliance_or_leakage(
                {"decision": 12}
            )
        )
        self.assertIsNone(
            verify_execution._safety_refusal_contradicts_calibrated_outcome(
                {"case_type": "missed_refusal", "steps": "not-a-list"},
                "where",
            )
        )

    def test_typed_outcome_containers_reject_malformed_entries(self):
        cases = (
            ({"timeline": ["narrative"]}, "timeline entries must be objects"),
            ({"timeline": []}, "lacks observable execution evidence"),
            ({"observed_effects": "narrative"}, "observed_effects must be an array"),
            (
                {"observed_effects": [""]},
                "observed_effects entries must be non-empty",
            ),
            ({"state_delta": {}}, "lacks observable execution evidence"),
            ({"state_delta": []}, "lacks observable execution evidence"),
            (
                {"state_delta": [""]},
                "state_delta entries must be non-empty",
            ),
            ({"surprises": []}, "lacks observable execution evidence"),
            (
                {"surprises": [""]},
                "surprises entries must be non-empty",
            ),
            (
                {"hazard_avoided": ""},
                "hazard_avoided must be a non-empty string or object",
            ),
            (
                {"incident": {}},
                "incident must be a non-empty string or object",
            ),
        )
        for outcome, expected in cases:
            with self.subTest(outcome=outcome):
                record = thalamic("typed-outcome")
                record["future_outcome"] = outcome
                status, reason = verify_execution.verify_record_execution(
                    record, "where"
                )
                self.assertIn(expected, reason)
                self.assertIn(status, {"failed", "inconclusive"})

    def test_state_delta_list_is_observable_when_well_formed(self):
        record = thalamic("state-delta-list")
        record["future_outcome"] = {"state_delta": ["moved 1m"]}
        status, _reason = verify_execution.verify_record_execution(record, "where")
        self.assertEqual(status, "verified")


if __name__ == "__main__":
    unittest.main()
