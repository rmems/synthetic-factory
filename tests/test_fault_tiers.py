#!/usr/bin/env python3
"""Direct tests of ``fault_tiers`` on hand-built observations, no tick loop:
tier order, code coverage, boundary directions, precedence, row 6 at the
table level, fallback availability and the latency arithmetic."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from fault_test_support import fault_config, fault_tiers as tiers, fault_vocabulary as fv, scenario

SYSTEM = fault_config.checked_system(scenario())


def observe(**overrides):
    fields = {
        "worst_healthy": 4,
        "channel_count": 4,
        "integrity_violation": False,
        "corrupt": 0,
        "total": 96,
        "dropped": 0,
        "peak_temperature": 38.0,
        "saturated_ticks": 0,
        "max_staleness": 0.0,
        "max_jitter": 0.0,
        "result_delay_ms": 0.0,
        "fallback_ok": True,
        "detection_ms": None,
    }
    fields.update(overrides)
    return tiers.Observation(**fields)


def select(**overrides):
    return tiers.select_outcome(observe(**overrides), SYSTEM)


class Tables(unittest.TestCase):
    def test_tiers_follow_the_precedence_and_cover_every_reason_once(self):
        self.assertEqual(tuple(outcome for outcome, _ in tiers.TIERS), fv.OUTCOME_PRECEDENCE[:-1])
        codes = [code for _, rules in tiers.TIERS for code, _ in rules] + list(tiers.CONTINUE_REASONS)
        self.assertEqual(len(codes), len(set(codes)))
        self.assertEqual(set(codes), fv.REASON_CODE_SET)
        self.assertEqual(set(tiers.RECOVERY_EXTRA), set(fv.OUTCOMES) - {"continue"})

    def test_boundary_directions(self):
        cases = (
            ({"result_delay_ms": 40.0}, "fail_closed", "NO_TIMELY_INPUT"),
            ({"result_delay_ms": 12.0}, "continue", "WITHIN_TOLERANCE"),
            ({"result_delay_ms": 12.5}, "degrade_gracefully", "RESULT_PAST_DEADLINE"),
            ({"peak_temperature": 62.0}, "degrade_gracefully", "THERMAL_WARN"),
            ({"peak_temperature": 78.0}, "reflex_action", "THERMAL_LIMIT_REFLEX"),
            ({"peak_temperature": 92.0}, "fail_closed", "THERMAL_SHUTDOWN"),
            ({"max_staleness": 8.0}, "continue", "WITHIN_TOLERANCE"),
            ({"max_staleness": 8.5}, "degrade_gracefully", "STALE_BEYOND_THRESHOLD"),
            ({"max_jitter": 1.5}, "continue", "WITHIN_TOLERANCE"),
            ({"max_jitter": 1.6}, "degrade_gracefully", "JITTER_BEYOND_TOLERANCE"),
            ({"saturated_ticks": 4}, "reflex_action", "SATURATION_REFLEX"),
            ({"saturated_ticks": 3}, "continue", "WITHIN_TOLERANCE"),
            ({"worst_healthy": 3}, "degrade_gracefully", "REDUCED_CHANNEL_SET"),
            ({"worst_healthy": 2}, "fallback", "FALLBACK_SOURCE_ENGAGED"),
            ({"worst_healthy": 2, "fallback_ok": False}, "fail_closed", "INSUFFICIENT_HEALTHY_CHANNELS_NO_FALLBACK"),
            ({"integrity_violation": True}, "quarantine", "MALFORMED_STREAM_QUARANTINED"),
            ({"corrupt": 24}, "quarantine", "CORRUPTION_ABOVE_QUARANTINE_THRESHOLD"),
            ({"corrupt": 23}, "degrade_gracefully", "CORRUPTION_BELOW_QUARANTINE_THRESHOLD"),
            ({"dropped": 1}, "degrade_gracefully", "EVENTS_DROPPED"),
        )
        for overrides, outcome, reason in cases:
            with self.subTest(overrides=overrides):
                self.assertEqual(select(**overrides), (outcome, (reason,)))

    def test_a_higher_tier_hides_lower_reasons_and_a_tier_reports_all_of_its_own(self):
        self.assertEqual(
            select(result_delay_ms=44.0, peak_temperature=70.0, dropped=3), ("fail_closed", ("NO_TIMELY_INPUT",))
        )
        self.assertEqual(
            select(max_staleness=14.0, dropped=7, worst_healthy=3),
            ("degrade_gracefully", ("STALE_BEYOND_THRESHOLD", "EVENTS_DROPPED", "REDUCED_CHANNEL_SET")),
        )

    def test_row_6_a_zero_threshold_needs_actual_corruption(self):
        strict = fault_config.checked_system(scenario(corruption_quarantine_ratio=0.0))
        self.assertEqual(tiers.select_outcome(observe(), strict), ("continue", ("WITHIN_TOLERANCE",)))
        self.assertEqual(
            tiers.select_outcome(observe(corrupt=1), strict),
            ("quarantine", ("CORRUPTION_ABOVE_QUARANTINE_THRESHOLD",)),
        )
        self.assertEqual(observe(corrupt=1, total=0).corrupt_ratio, 0.0)

    def test_fallback_availability(self):
        self.assertFalse(tiers.fallback_available({"fallback_source": None}, set(), ()))
        self.assertFalse(tiers.fallback_available(SYSTEM, {"redundant_relay_b"}, ()))
        self.assertFalse(tiers.fallback_available(SYSTEM, set(), ("c0", "redundant_relay_b")))
        self.assertTrue(tiers.fallback_available(SYSTEM, {"c3"}, ("c0",)))


class Latencies(unittest.TestCase):
    def test_detection_is_onset_relative_clamped_rounded_and_synthesised_for_late_results(self):
        self.assertEqual(tiers.detection_latency_ms(observe(detection_ms=10.0004), 4.0, SYSTEM), 6.0)
        self.assertEqual(tiers.detection_latency_ms(observe(detection_ms=2.0), 6.0, SYSTEM), 0.0)
        self.assertEqual(tiers.detection_latency_ms(observe(result_delay_ms=18.0), 0.0, SYSTEM), 12.0)
        self.assertIsNone(tiers.detection_latency_ms(observe(result_delay_ms=12.0), 0.0, SYSTEM))

    def test_recovery_adds_the_tier_latency_or_is_zero_for_continue(self):
        self.assertEqual(tiers.recovery_latency_ms(SYSTEM, "continue", 3.0), 0.0)
        self.assertEqual(tiers.recovery_latency_ms(SYSTEM, "fallback", None), 0.0)
        for outcome, extra in (("fallback", 4.0), ("degrade_gracefully", 2.0), ("fail_closed", 1.0)):
            with self.subTest(outcome=outcome):
                self.assertEqual(tiers.recovery_latency_ms(SYSTEM, outcome, 6.0), 6.0 + extra)

    def test_decide_composes_outcome_and_both_latencies(self):
        decision = tiers.decide(observe(dropped=2, detection_ms=8.0), SYSTEM, 4.0)
        self.assertEqual(decision, tiers.Decision("degrade_gracefully", ("EVENTS_DROPPED",), 4.0, 6.0))

