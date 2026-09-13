#!/usr/bin/env python3
"""Cohesive execution-verifier regression suite."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "pipelines"))

from gate_fixtures import thalamic  # noqa: E402
import verify_execution  # noqa: E402


class VerifyExecutionOutcomes(unittest.TestCase):
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


    def test_explicit_null_outcome_fields_are_structural_failures(self):
        for field in ("state_delta", "surprises", "incident", "hazard_avoided"):
            with self.subTest(field=field):
                record = thalamic(f"null-{field}")
                record["future_outcome"] = {field: None}

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


    def test_numeric_state_delta_vector_is_observable_when_finite(self):
        record = thalamic("numeric-state-delta")
        record["future_outcome"] = {"state_delta": [1, -0.5, 0.0]}
        self.assertEqual(
            verify_execution.verify_record_execution(record, "where")[0],
            "verified",
        )

        record["future_outcome"] = {"state_delta": [1, float("inf")]}
        status, reason = verify_execution.verify_record_execution(record, "where")
        self.assertEqual(status, "failed")
        self.assertIn("finite numbers", reason)



if __name__ == "__main__":
    unittest.main()
