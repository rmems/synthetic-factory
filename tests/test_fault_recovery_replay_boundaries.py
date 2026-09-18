"""Simulator controls and summaries must describe the replayed experiment."""

import copy
import unittest

from test_fault_recovery import disturbance, fr, oc, scenario


class ReplayBoundaries(unittest.TestCase):
    def test_hard_deadline_must_follow_soft_deadline(self):
        for hard in (5.0, 10.0):
            with self.subTest(hard=hard), self.assertRaisesRegex(oc.ContractError, "deadline"):
                fr.RelayReflexSimulator().run(
                    scenario(deadline_ms=10.0, hard_deadline_ms=hard),
                    disturbance("delayed_result", delay_ms=7.0),
                )

    def test_zero_quarantine_threshold_requires_positive_corruption(self):
        result = fr.RelayReflexSimulator().run(
            scenario(corruption_quarantine_ratio=0),
            disturbance(
                "event_jitter", channels=["c0"], onset_ms=2.0, duration_ms=20.0, jitter_ms=0.4
            ),
        )
        self.assertEqual(result.outcome, "continue")
        self.assertNotIn("CORRUPTION_ABOVE_QUARANTINE_THRESHOLD", result.reason_codes)

    def test_rehashed_trace_summary_tampering_is_refused(self):
        original = fr.build_records(3, 1)[0]
        for field in original["result"]["trace_summary"]:
            changed = copy.deepcopy(original)
            changed["result"]["trace_summary"][field] += 1
            changed["provenance"]["record_sha256"] = oc.record_digest(changed)
            with self.subTest(field=field):
                self.assertTrue(any("trace_summary" in e for e in fr.check_family(changed, "test")))
