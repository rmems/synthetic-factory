#!/usr/bin/env python3
"""Direct unit coverage for census's record-kind and sim/real classifiers."""

import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


class CensusBuckets(unittest.TestCase):
    def setUp(self):
        pipeline_path = str(REPO / "pipelines")
        self._inserted_pipeline_path = pipeline_path not in sys.path
        if self._inserted_pipeline_path:
            sys.path.insert(0, pipeline_path)
        import census

        self.census = census

    def tearDown(self):
        if self._inserted_pipeline_path:
            sys.path.remove(str(REPO / "pipelines"))
        sys.modules.pop("census", None)

    def test_kind_routing(self):
        six = {
            "state": {},
            "proposed_action": {},
            "safety_decision": {},
            "executed_action": {},
            "future_outcome": {},
            "reward_components": {},
        }
        self.assertEqual(self.census.classify_kind(six), "thalamic")
        self.assertEqual(
            self.census.classify_kind({"chosen": {}, "rejected": {}}),
            "preference",
        )
        self.assertEqual(
            self.census.classify_kind({"language_view": {}, "spike_events": []}),
            "bridge_pair",
        )
        self.assertEqual(
            self.census.classify_kind({"agents": [], "transcript": []}),
            "multi_agent",
        )
        self.assertEqual(self.census.classify_kind({"case_type": "correct_refusal"}), "safety_case")
        self.assertEqual(
            self.census.classify_kind({"goal": "x", "steps": []}),
            "episode",
        )
        self.assertEqual(
            self.census.classify_kind({"family": "neuromorphic-fault-recovery"}),
            "fault_recovery",
        )
        self.assertEqual(
            self.census.classify_kind(
                {
                    "family": "neuromorphic-fault-recovery",
                    "state": {},
                    "proposed_action": {},
                    "safety_decision": {},
                    "executed_action": {},
                    "future_outcome": {},
                    "reward_components": {},
                }
            ),
            "fault_recovery",
        )
        self.assertEqual(self.census.classify_kind({"meta": {}}), "unknown")

    def test_unhashable_declared_kind_is_unknown_instead_of_crashing(self):
        for malformed in ([], {}):
            with self.subTest(malformed=malformed):
                self.assertEqual(
                    self.census.classify_kind({"record_kind": malformed}),
                    "unknown",
                )

    def test_reader_does_not_treat_bare_cr_as_a_jsonl_record_boundary(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "batch.jsonl"
            path.write_bytes(b'{"id":"first"}\r{"id":"second"}\n')

            decoded, parse_failures, unreadable = self.census._read_census_records(
                path,
                "batch.jsonl",
            )

        self.assertEqual(decoded, [])
        self.assertEqual(parse_failures, 1)
        self.assertEqual(unreadable, [])

    def test_overlapping_keys_follow_census_agentic_order(self):
        six = {
            "state": {},
            "proposed_action": {},
            "safety_decision": {},
            "executed_action": {},
            "future_outcome": {},
            "reward_components": {},
        }
        self.assertEqual(
            self.census.classify_kind({**six, "goal": "x", "steps": []}),
            "thalamic",
        )
        self.assertEqual(
            self.census.classify_kind(
                {"case_type": "correct_refusal", "goal": "x", "steps": []}
            ),
            "safety_case",
        )
        self.assertEqual(
            self.census.classify_kind(
                {"transcript": [], "agents": [], "goal": "x", "steps": []}
            ),
            "multi_agent",
        )
        self.assertEqual(
            self.census.classify_kind({**six, "chosen": {}, "rejected": {}}),
            "thalamic",
        )
        self.assertEqual(
            self.census.classify_kind({"chosen": dict(six), "rejected": dict(six)}),
            "preference",
        )

    def test_sim_or_real_buckets(self):
        bucket = self.census.bucket_sim_or_real
        self.assertEqual(bucket("real"), "real")
        self.assertEqual(bucket("real (production, actions live)"), "real*")
        self.assertEqual(bucket("live allocation; arbiter writes schedules"), "real*")
        self.assertEqual(
            bucket("high-fidelity plant simulation calibrated on telemetry"),
            "sim*",
        )
        self.assertEqual(
            bucket("hardware-in-the-loop (flight SPAD array)"),
            "hil*",
        )
        self.assertEqual(bucket("hil-rig-3"), "hil*")
        self.assertEqual(
            bucket(
                "operations-grade simulation calibrated on HIL valve testbench"
            ),
            "sim*",
        )
        self.assertEqual(
            bucket(
                "decision-support in live IOC; the relay's disposition drives recovery"
            ),
            "other",
        )


if __name__ == "__main__":
    unittest.main()
