"""Positive corruption requests affect real ticks within their declared window."""

import unittest

from test_fault_recovery import disturbance, fr, scenario


class CorruptionWindow(unittest.TestCase):
    def test_short_positive_burst_cannot_be_a_noop(self):
        for ratio in (0.2, 0.000001):
            with self.subTest(ratio=ratio):
                result = fr.RelayReflexSimulator().run(
                    scenario(),
                    disturbance(
                        "burst_corruption",
                        channels=["c0"],
                        onset_ms=4.0,
                        duration_ms=10.0,
                        corrupt_ratio=ratio,
                    ),
                )
                self.assertGreater(result.corrupt_events, 0)
                self.assertNotEqual(result.outcome, "continue")
                self.assertIsNotNone(result.detection_latency_ms)

    def test_zero_requested_ratio_stays_uncorrupted(self):
        result = fr.RelayReflexSimulator().run(
            scenario(),
            disturbance(
                "burst_corruption", channels=["c0"], onset_ms=4.0, duration_ms=10.0, corrupt_ratio=0
            ),
        )
        self.assertEqual(result.corrupt_events, 0)

    def test_existing_realised_corruption_counts_are_preserved(self):
        for ratio, duration, count in ((0.8, 10.0, 8), (0.2, 40.0, 6)):
            with self.subTest(ratio=ratio):
                result = fr.RelayReflexSimulator().run(
                    scenario(),
                    disturbance(
                        "burst_corruption",
                        channels=["c0", "c3"],
                        onset_ms=4.0,
                        duration_ms=duration,
                        corrupt_ratio=ratio,
                    ),
                )
                self.assertEqual(result.corrupt_events, count)
