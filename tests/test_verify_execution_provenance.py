#!/usr/bin/env python3
"""Cohesive execution-verifier regression suite."""

import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "pipelines"))

from gate_fixtures import thalamic  # noqa: E402
import verify_execution  # noqa: E402


class VerifyExecutionProvenance(unittest.TestCase):
    def test_unhashable_thalamic_provenance_returns_failed_verdict(self):
        record = thalamic("unhashable-provenance")
        record["state"]["sim_or_real"] = {}

        status, reason = verify_execution.verify_record_execution(record, "where")

        self.assertEqual(status, "failed")
        self.assertIn("sim_or_real", reason)


    def test_unknown_string_thalamic_provenance_remains_inconclusive(self):
        record = thalamic("unknown-provenance")
        record["state"]["sim_or_real"] = "unknown"

        status, reason = verify_execution.verify_record_execution(record, "where")

        self.assertEqual(status, "inconclusive")
        self.assertIn("non-training provenance", reason)


    def bridge_record(self, sim_or_real, tag="bridge-provenance"):
        base = json.loads(json.dumps(thalamic(tag)))
        base["state"] = {"sim_or_real": sim_or_real, "domain": "gate-test"}
        return {
            "language_view": {"trajectory": base},
            "spike_events": [{"t_ms": 0, "channel": "a", "amplitude": 1.0}],
        }


    def test_bridge_non_training_provenance_is_inconclusive_like_thalamic(self):
        # Bridge records delegate to language_view.trajectory, so the
        # delegated trajectory follows the standalone Thalamic provenance
        # taxonomy: non-training provenance is waivable cannot-verify.
        status, reason = verify_execution.verify_record_execution(
            self.bridge_record("unknown"), "where"
        )

        self.assertEqual(status, "inconclusive")
        self.assertIn("non-training provenance", reason)
        self.assertIn("language_view.trajectory", reason)


    def test_bridge_training_provenance_is_verified(self):
        status, reason = verify_execution.verify_record_execution(
            self.bridge_record("designed"), "where"
        )
        self.assertEqual(status, "verified", reason)


    def test_real_provenance_stays_failed_on_both_routes(self):
        # The provenance filter only drops the generic enum error; the
        # specific "must not be 'real'" envelope error is never filtered.
        thalamic_real = thalamic("real-provenance")
        thalamic_real["state"]["sim_or_real"] = "real"
        cases = (
            ("thalamic", thalamic_real),
            ("bridge", self.bridge_record("real", tag="real-bridge")),
        )
        for route, record in cases:
            with self.subTest(route=route):
                status, reason = verify_execution.verify_record_execution(
                    record, "where"
                )
                self.assertEqual(status, "failed")
                self.assertIn("state.sim_or_real must not be 'real'", reason)



if __name__ == "__main__":
    unittest.main()
