#!/usr/bin/env python3
"""Direct tests of ``fault_simulator``: the boundary types and the vocabulary
gate on a verdict, the corruption phase and mechanics, the valid-disturbance
twin of every enforced D7 row, the held rows as accepted runs, row 9's
behaviour change, carried #138 behaviour, the tier tables on hand-built
observations, determinism, the detection and recovery invariant, and the
oracle block."""

import copy
import dataclasses
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from fault_test_support import (
    disturbance,
    fault_config,
    fault_oracle,
    fault_scenario,
    fault_simulator as fs,
    fault_vocabulary as fv,
    oc,
    refusal,
    run,
    scenario,
)

SYSTEM = fault_config.checked_system(scenario())
PHASES = (
    0.0, 0.919, 0.838, 0.757, 0.676, 0.595, 0.514, 0.433, 0.352, 0.271, 0.19, 0.109,
    0.028, 0.947, 0.866, 0.785, 0.704, 0.623, 0.542, 0.461, 0.38, 0.299, 0.218, 0.137,
)


def result(**overrides):
    fields = {
        "outcome": "continue", "reason_codes": ("WITHIN_TOLERANCE",), "detection_latency_ms": None,
        "recovery_latency_ms": 0.0, "worst_healthy_channels": 4, "dropped_events": 0,
        "corrupt_events": 0, "total_events": 0, "peak_temperature_c": 38.0, "max_staleness_ms": 0.0,
        "max_jitter_ms": 0.0, "saturated_ticks": 0, "integrity_violation": False, "result_delay_ms": 0.0,
    }
    fields.update(overrides)
    return fs.FaultResult(**fields)


def observe(**overrides):
    fields = {
        "worst_healthy": 4, "channel_count": 4, "integrity_violation": False, "corrupt": 0, "total": 96,
        "dropped": 0, "peak_temperature": 38.0, "saturated_ticks": 0, "max_staleness": 0.0,
        "max_jitter": 0.0, "result_delay_ms": 0.0, "fallback_ok": True, "detection_ms": None,
    }
    fields.update(overrides)
    return fs.Observation(**fields)


def select(**overrides):
    return fs.select_outcome(observe(**overrides), SYSTEM)


def thermal(peak, ramp=8.0, onset=6.0, **system):
    return run("thermal_excursion", system, onset_ms=onset, ramp_ms=ramp, peak_c=peak)


def burst(ratio, channels, window=(4.0, 10.0), **system):
    onset, duration = window
    return run("burst_corruption", system, channels=channels, onset_ms=onset, duration_ms=duration, corrupt_ratio=ratio)


def malformed(kind, count, channels, **system):
    return run("malformed_spike_burst", system, channels=channels, malformed_count=count, malformed_kind=kind)


def verdict(result):
    return result.outcome, result.reason_codes


class Boundary(unittest.TestCase):
    def test_ratios_are_zero_without_events_and_derived_otherwise_and_the_result_is_frozen(self):
        empty = result()
        self.assertEqual((empty.realised_corrupt_ratio, empty.residual_error, empty.ticks), (0.0, 0.0, 0))
        busy = result(corrupt_events=3, dropped_events=1, total_events=8, trace=({"t_ms": 0.0},))
        self.assertEqual((busy.realised_corrupt_ratio, busy.residual_error, busy.ticks), (0.375, 0.5, 1))
        with self.assertRaises(dataclasses.FrozenInstanceError):
            empty.outcome = "fail_closed"

    def test_a_verdict_inconsistent_with_its_outcome_is_refused(self):
        """Codex findings: an injected oracle's verdict must keep the consistency the
        simulator keeps by construction, and a malformed reason entry is a refusal."""
        consistent = dict(
            outcome="degrade_gracefully", reason_codes=("EVENTS_DROPPED", "REDUCED_CHANNEL_SET"),
            detection_latency_ms=0.0, corrupt_events=0, dropped_events=5, total_events=96,
        )
        within = dict(outcome="continue", reason_codes=("WITHIN_TOLERANCE",), detection_latency_ms=None)
        checked = result(**consistent)
        self.assertIs(fs.checked_result(checked), checked)
        # A temperature may sit below zero; only durations are non-negative.
        self.assertEqual(fs.checked_result(result(**consistent, peak_temperature_c=-12.5)).peak_temperature_c, -12.5)
        for label, changes in (
            ("continue with a shutdown reason", dict(outcome="continue", reason_codes=("THERMAL_SHUTDOWN",), detection_latency_ms=None)),
            ("fail_closed with WITHIN_TOLERANCE", dict(outcome="fail_closed", reason_codes=("WITHIN_TOLERANCE",))),
            ("degrade without a detection", dict(detection_latency_ms=None)),
            ("continue with a detection", dict(outcome="continue", reason_codes=("WITHIN_TOLERANCE",), detection_latency_ms=3.0)),
            ("corrupt above total", dict(corrupt_events=200, total_events=1)),
            ("corrupt with no events", dict(corrupt_events=1, dropped_events=0, total_events=0)),
            ("unhashable reason entry", dict(reason_codes=(["EVENTS_DROPPED"],))),
            ("negative recovery", dict(recovery_latency_ms=-1.0)),
            ("negative staleness", dict(max_staleness_ms=-1.0)),
            ("negative jitter", dict(max_jitter_ms=-0.5)),
            ("negative result delay", dict(result_delay_ms=-2.0)),
            ("recovery before detection", dict(detection_latency_ms=10.0, recovery_latency_ms=1.0)),
            ("continue with a recovery", dict(outcome="continue", reason_codes=("WITHIN_TOLERANCE",), detection_latency_ms=None, recovery_latency_ms=2.0)),
            # Codex round 7: a continue verdict cannot carry evidence the tiers would never pass.
            ("continue with an integrity violation", dict(**within, dropped_events=0, integrity_violation=True)),
            ("continue with dropped events", dict(**within)),
            ("continue with corrupt events", dict(**within, dropped_events=0, corrupt_events=1)),
            # Codex round 8: a same-tier reason needs its evidence, and unconditional evidence its reason.
            ("a drop reason with no drops", dict(reason_codes=("EVENTS_DROPPED",), dropped_events=0)),
            ("drops in the degrade tier without the drop reason", dict(reason_codes=("REDUCED_CHANNEL_SET",))),
            ("a corruption reason with no corruption", dict(reason_codes=("CORRUPTION_BELOW_QUARANTINE_THRESHOLD",))),
            ("corruption in the degrade tier without its reason", dict(reason_codes=("EVENTS_DROPPED",), corrupt_events=2)),
            ("quarantine for a malformed stream that never was", dict(outcome="quarantine", reason_codes=("MALFORMED_STREAM_QUARANTINED",))),
            ("an integrity violation quarantined for another reason only", dict(outcome="quarantine", reason_codes=("CORRUPTION_ABOVE_QUARANTINE_THRESHOLD",), corrupt_events=50, integrity_violation=True)),
            ("quarantine above the threshold with no corruption", dict(outcome="quarantine", reason_codes=("CORRUPTION_ABOVE_QUARANTINE_THRESHOLD",))),
        ):
            with self.subTest(case=label), refusal(self, fv.FINDING_ORACLE_RESULT_OUT_OF_VOCABULARY, "oracle result"):
                fs.checked_result(result(**{**consistent, **changes}))

    def test_the_boundary_declares_identity_but_no_meters_and_no_engine(self):
        oracle = fs.FaultOracle()
        self.assertEqual((oracle.meter_clock, oracle.meter_state, oracle.meter_thermal), (None, None, None))
        self.assertEqual((oracle.implementation, oracle.authority), (fv.BOUNDARY_IMPLEMENTATION, oc.AUTHORITY_AUTHORITATIVE))
        with self.assertRaises(NotImplementedError):
            oracle.run({}, {})
        with self.assertRaises(NotImplementedError):
            oracle.oracle_block({})
        self.assertIs(fault_oracle.FaultOracle, fs.FaultOracle)
        self.assertIs(fault_oracle.FaultResult, fs.FaultResult)

    def test_a_verdict_outside_the_family_vocabulary_is_refused(self):
        """Whatever oracle returned it, a result becomes a label only when its
        type, outcome, reason codes, counts and readings fit the vocabulary."""
        cases = (
            ({"outcome": "explode"}, "outcome"),
            ({"reason_codes": ("BOGUS_CODE", "THERMAL_SHUTDOWN")}, "reason_codes"),
            ({"reason_codes": ()}, "reason_codes"),
            ({"reason_codes": ["WITHIN_TOLERANCE"]}, "reason_codes"),
            ({"worst_healthy_channels": -1}, "worst_healthy_channels"),
            ({"dropped_events": 2.5}, "dropped_events"),
            ({"total_events": True}, "total_events"),
            ({"recovery_latency_ms": float("nan")}, "recovery_latency_ms"),
            ({"detection_latency_ms": float("inf")}, "detection_latency_ms"),
            ({"integrity_violation": 0}, "integrity_violation"),
            # Codex round 7: a count too wide to print was a raw ValueError from the message.
            ({"total_events": 10**5000}, "total_events"),
            ({"saturated_ticks": fv.MAX_EVENT_COUNT + 1}, "saturated_ticks"),
        )
        for overrides, field in cases:
            with self.subTest(field=field), refusal(self, fv.FINDING_ORACLE_RESULT_OUT_OF_VOCABULARY, field):
                fs.checked_result(result(**overrides))
        for value in ({"outcome": "continue"}, 10**5000):
            with self.subTest(value=type(value).__name__), refusal(self, fv.FINDING_ORACLE_RESULT_OUT_OF_VOCABULARY, "FaultResult"):
                fs.checked_result(value)
        self.assertEqual(fs.checked_result(result(total_events=fv.MAX_EVENT_COUNT)).total_events, fv.MAX_EVENT_COUNT)

    def test_a_verdict_is_bounded_by_the_system_it_answers_when_that_system_is_given(self):
        """Codex round 8: 100 healthy channels on a four-channel relay, or more saturated
        ticks than the run has, passed the generic count bound and became a label.
        Greptile: sub-threshold saturation under continue is within tolerance."""
        self.assertEqual(fs.checked_result(result(saturated_ticks=2)).saturated_ticks, 2)
        self.assertEqual(fs.checked_result(result(saturated_ticks=3, total_events=96), SYSTEM).total_events, 96)
        for overrides, field in (
            ({"worst_healthy_channels": 5}, "worst_healthy_channels"),
            ({"saturated_ticks": 25}, "saturated_ticks"),
            ({"total_events": 97}, "total_events"),
        ):
            with self.subTest(field=field):
                self.assertEqual(fs.checked_result(result(**overrides)).outcome, "continue")
                with refusal(self, fv.FINDING_ORACLE_RESULT_OUT_OF_VOCABULARY, field, "exceeds"):
                    fs.checked_result(result(**overrides), SYSTEM)

    def test_with_the_system_the_verdict_must_be_what_the_tiers_select_for_its_readings(self):
        """Codex round 9 / CodeRabbit: with the effective system known, an injected
        verdict must be the tier table's own selection over the readings it reports,
        so continue at 100 C, continue past the hard deadline, or a quarantine whose
        corruption ratio sits below the threshold cannot become labels."""
        quarantined = dict(
            outcome="quarantine", reason_codes=("CORRUPTION_ABOVE_QUARANTINE_THRESHOLD",),
            detection_latency_ms=0.0, recovery_latency_ms=1.0, corrupt_events=30, total_events=96,
        )
        self.assertEqual(fs.checked_result(result(**quarantined), SYSTEM).outcome, "quarantine")
        fallback = dict(
            outcome="fallback", reason_codes=("FALLBACK_SOURCE_ENGAGED",), detection_latency_ms=0.0,
            recovery_latency_ms=4.0, worst_healthy_channels=2, total_events=96,
        )
        self.assertEqual(fs.checked_result(result(**fallback), SYSTEM).outcome, "fallback")
        for label, changes in (
            ("continue at 100 C", dict(peak_temperature_c=100.0)),
            ("continue past the hard deadline", dict(result_delay_ms=100.0)),
            ("continue with saturation at the reflex threshold", dict(saturated_ticks=4)),
            ("quarantine below the corruption threshold", {**quarantined, "corrupt_events": 1}),
            ("degrade reported where the tiers fail closed", dict(outcome="degrade_gracefully", reason_codes=("THERMAL_WARN",), detection_latency_ms=0.0, recovery_latency_ms=2.0, peak_temperature_c=100.0)),
            ("a fired threshold reason left unreported", dict(outcome="degrade_gracefully", reason_codes=("EVENTS_DROPPED",), detection_latency_ms=0.0, recovery_latency_ms=2.0, dropped_events=5, max_jitter_ms=3.0)),
        ):
            with self.subTest(case=label):
                fs.checked_result(result(**{**dict(total_events=96), **changes}))
                with refusal(self, fv.FINDING_ORACLE_RESULT_OUT_OF_VOCABULARY, "tier table yields"):
                    fs.checked_result(result(**{**dict(total_events=96), **changes}), SYSTEM)
        self.assertEqual(fs.checked_result(result()), result())
        self.assertEqual(fs.checked_result(thermal(96.0)).outcome, "fail_closed")


class Mechanics(unittest.TestCase):
    def test_the_corruption_phase_is_the_pinned_integer_sequence(self):
        self.assertEqual(tuple(fs.corruption_phase(tick) for tick in range(24)), PHASES)

    def test_the_thermal_trace_is_a_heating_only_running_max(self):
        result = thermal(70.0)
        self.assertEqual([e["temperature_c"] for e in result.trace][:9], [38.0, 38.0, 38.0, 38.0, 46.0, 54.0, 62.0, 70.0, 70.0])
        self.assertEqual(result.ticks, 24)

    def test_total_events_are_ticks_times_live_channels(self):
        self.assertEqual(thermal(58.0).total_events, 96)
        missing = run("missing_channel", channels=["c3"])
        self.assertEqual((missing.total_events, missing.worst_healthy_channels), (72, 3))
        self.assertEqual(verdict(missing), ("degrade_gracefully", ("REDUCED_CHANNEL_SET",)))


class EnforcedRowTwins(unittest.TestCase):
    def test_rows_1_and_2_a_valid_excursion_still_walks_the_ladder(self):
        cases = ((58.0, "continue"), (70.0, "degrade_gracefully"), (84.0, "reflex_action"), (96.0, "fail_closed"), (200.0, "fail_closed"))
        for peak, outcome in cases:
            with self.subTest(peak=peak):
                self.assertEqual(thermal(peak).outcome, outcome)
        self.assertEqual(verdict(thermal(96.0)), ("fail_closed", ("THERMAL_SHUTDOWN",)))
        self.assertEqual(verdict(thermal(84.0)), ("reflex_action", ("THERMAL_LIMIT_REFLEX",)))

    def test_row_4_twin_losing_two_of_four_below_the_budget(self):
        engaged = run("missing_channel", {"min_healthy_channels": 3}, channels=["c0", "c1"])
        self.assertEqual(verdict(engaged), ("fallback", ("FALLBACK_SOURCE_ENGAGED",)))
        closed = run("missing_channel", {"min_healthy_channels": 3, "fallback_source": None}, channels=["c0", "c1"])
        self.assertEqual(verdict(closed), ("fail_closed", ("INSUFFICIENT_HEALTHY_CHANNELS_NO_FALLBACK",)))

    def test_row_5_twins_the_deadline_tiers_in_order(self):
        cases = (
            (44.0, "fail_closed", "NO_TIMELY_INPUT", 12.0, 13.0),
            (50.0, "fail_closed", "NO_TIMELY_INPUT", 12.0, 13.0),
            (18.0, "degrade_gracefully", "RESULT_PAST_DEADLINE", 12.0, 14.0),
            (20.0, "degrade_gracefully", "RESULT_PAST_DEADLINE", 12.0, 14.0),
            (12.0, "continue", "WITHIN_TOLERANCE", None, 0.0),
        )
        for delay, outcome, reason, detection, recovery in cases:
            with self.subTest(delay=delay):
                result = run("delayed_result", delay_ms=delay)
                self.assertEqual(verdict(result), (outcome, (reason,)))
                self.assertEqual((result.detection_latency_ms, result.recovery_latency_ms), (detection, recovery))

    def test_row_6_a_zero_threshold_is_a_policy_not_a_verdict(self):
        clean = run("event_jitter", {"corruption_quarantine_ratio": 0.0}, channels=["c0"], onset_ms=2.0, duration_ms=20.0, jitter_ms=0.4)
        self.assertEqual(verdict(clean), ("continue", ("WITHIN_TOLERANCE",)))
        self.assertEqual(clean.corrupt_events, 0)
        strict = burst(0.8, ["c0", "c1"], corruption_quarantine_ratio=0.0)
        self.assertEqual(verdict(strict), ("quarantine", ("CORRUPTION_ABOVE_QUARANTINE_THRESHOLD",)))
        self.assertEqual(strict.corrupt_events, 8)
        below = burst(0.3, ["c0"], window=(0.0, 48.0))
        self.assertEqual(verdict(below), ("degrade_gracefully", ("CORRUPTION_BELOW_QUARANTINE_THRESHOLD",)))
        # The generator's onset-4 / duration-10 window is ticks 2-6, whose
        # phases all sit above 0.2: a faithful within-tolerance negative.
        self.assertEqual(verdict(burst(0.2, ["c0"])), ("continue", ("WITHIN_TOLERANCE",)))

    def test_the_realised_corruption_tracks_the_request(self):
        for ratio in (0.2, 0.4, 0.6, 0.8):
            with self.subTest(ratio=ratio):
                result = burst(ratio, ["c0", "c1", "c2", "c3"], window=(0.0, 1000.0), ticks=500)
                self.assertLess(abs(result.realised_corrupt_ratio - ratio), 0.12)


class HeldRows(unittest.TestCase):
    def test_row_3_an_excursion_that_never_crosses_warn_is_a_valid_continue(self):
        self.assertEqual((thermal(58.0).outcome, thermal(58.0).peak_temperature_c), ("continue", 58.0))
        self.assertEqual((thermal(70.0, ramp=1e9).outcome, thermal(70.0, ramp=1e9).peak_temperature_c), ("continue", 38.0))

    def test_row_7_a_tick_longer_than_the_staleness_threshold_runs(self):
        result = run("event_jitter", {"tick_ms": 10.0, "stale_threshold_ms": 8.0}, channels=["c0"], onset_ms=20.0, duration_ms=20.0, jitter_ms=0.4)
        self.assertEqual(verdict(result), ("continue", ("WITHIN_TOLERANCE",)))

    def test_row_10_a_reflex_threshold_beyond_the_horizon_reports_without_a_reflex(self):
        result = run("temporary_saturation", {"reflex_saturation_ticks": 30}, channels=["c0"], onset_ms=0.0, duration_ms=48.0)
        self.assertEqual((verdict(result), result.saturated_ticks), (("degrade_gracefully", ("REDUCED_CHANNEL_SET",)), 24))
        reflex = run("temporary_saturation", {"min_healthy_channels": 2}, channels=["c0"], onset_ms=2.0, duration_ms=16.0)
        self.assertEqual((verdict(reflex), reflex.saturated_ticks), (("reflex_action", ("SATURATION_REFLEX",)), 8))
        self.assertEqual(run("temporary_saturation", channels=["c0"], onset_ms=2.0, duration_ms=4.0).saturated_ticks, 2)

    def test_readings_are_decided_at_the_precision_the_record_emits(self):
        """Codex round 7: a peak of 61.9996 was decided as below warn (62.0) and then
        emitted as 62.0, so the record contradicted its own outcome. The state keeps
        the three readings at 3 dp, so the signs, the tiers and the label agree."""
        warm, cool = thermal(61.9996), thermal(61.9994)
        self.assertEqual((verdict(warm), warm.peak_temperature_c), (("degrade_gracefully", ("THERMAL_WARN",)), 62.0))
        self.assertEqual((warm.detection_latency_ms, warm.recovery_latency_ms), (8.0, 10.0))
        self.assertEqual((verdict(cool), cool.peak_temperature_c), (("continue", ("WITHIN_TOLERANCE",)), 61.999))
        self.assertEqual([entry["temperature_c"] for entry in warm.trace][7:9], [62.0, 62.0])
        quiet = run("event_jitter", channels=["c0"], onset_ms=2.0, duration_ms=20.0, jitter_ms=1.5004)
        loud = run("event_jitter", channels=["c0"], onset_ms=2.0, duration_ms=20.0, jitter_ms=1.5006)
        self.assertEqual((verdict(quiet), quiet.max_jitter_ms), (("continue", ("WITHIN_TOLERANCE",)), 1.5))
        self.assertEqual((verdict(loud), loud.max_jitter_ms), (("degrade_gracefully", ("JITTER_BEYOND_TOLERANCE",)), 1.501))
        stale = run("stale_sensor", {"stale_threshold_ms": 8.0004, "tick_ms": 2.0001}, channels=["c0"], onset_ms=2.0001, duration_ms=8.0004)
        self.assertEqual((verdict(stale), stale.max_staleness_ms), (("continue", ("WITHIN_TOLERANCE",)), 8.0))
        for outcome in (warm, cool, quiet, loud, stale):
            self.assertIs(fs.checked_result(outcome), outcome)

    def test_row_11_jitter_within_tolerance_is_exactly_within_tolerance(self):
        for jitter in (0.4, 1.5):
            with self.subTest(jitter=jitter):
                result = run("event_jitter", channels=["c0"], onset_ms=2.0, duration_ms=20.0, jitter_ms=jitter)
                self.assertEqual(verdict(result), ("continue", ("WITHIN_TOLERANCE",)))
                self.assertIsNone(result.detection_latency_ms)
        loud = run("event_jitter", channels=["c0"], onset_ms=2.0, duration_ms=20.0, jitter_ms=3.0)
        self.assertEqual(verdict(loud), ("degrade_gracefully", ("JITTER_BEYOND_TOLERANCE",)))


class Row9DropsStartDetection(unittest.TestCase):
    """Fixture fr-20260823-0015 (#138) carried no detection and recovery 0.0 here."""

    def test_a_drop_caused_degrade_has_a_detection_time(self):
        cases = ((3, ["c0"], 3), (1, ["c0", "c1", "c2"], 2))
        for count, channels, budget in cases:
            with self.subTest(count=count):
                result = malformed("unknown_channel", count, channels, min_healthy_channels=budget)
                self.assertEqual(verdict(result), ("degrade_gracefully", ("EVENTS_DROPPED",)))
                self.assertEqual((result.integrity_violation, result.dropped_events), (False, count))
                self.assertEqual((result.detection_latency_ms, result.recovery_latency_ms), (0.0, 2.0))

    def test_integrity_kinds_quarantine_at_the_first_tick(self):
        for kind in fv.MALFORMED_INTEGRITY_KINDS:
            with self.subTest(kind=kind):
                result = malformed(kind, 2, ["c1"])
                self.assertEqual(verdict(result), ("quarantine", ("MALFORMED_STREAM_QUARANTINED",)))
                self.assertEqual((result.integrity_violation, result.detection_latency_ms), (True, 0.0))


class CarriedBehaviour(unittest.TestCase):
    def test_a_long_sensor_loss_co_fires_staleness_in_table_order(self):
        long = run("sensor_loss", {"min_healthy_channels": 2}, channels=["c0"], onset_ms=4.0, duration_ms=14.0)
        self.assertEqual(long.reason_codes, ("STALE_BEYOND_THRESHOLD", "EVENTS_DROPPED", "REDUCED_CHANNEL_SET"))
        short = run("sensor_loss", {"min_healthy_channels": 2}, channels=["c0"], onset_ms=4.0, duration_ms=6.0)
        self.assertEqual(short.reason_codes, ("EVENTS_DROPPED", "REDUCED_CHANNEL_SET"))

    def test_naming_the_fallback_among_the_lost_channels_fails_closed(self):
        result = run("sensor_loss", channels=["c0", "c1", "redundant_relay_b"], onset_ms=4.0, duration_ms=14.0)
        self.assertEqual(verdict(result), ("fail_closed", ("INSUFFICIENT_HEALTHY_CHANNELS_NO_FALLBACK",)))

    def test_a_stale_sensor_accrues_staleness_past_the_threshold(self):
        result = run("stale_sensor", {"min_healthy_channels": 2}, channels=["c0"], onset_ms=2.0, duration_ms=22.0)
        self.assertGreater(result.max_staleness_ms, 8.0)
        self.assertEqual(result.outcome, "degrade_gracefully")

    def test_latencies_are_onset_relative(self):
        labels = {(thermal(84.0, onset=onset).detection_latency_ms, thermal(84.0, onset=onset).recovery_latency_ms) for onset in (2.0, 12.0, 20.0)}
        self.assertEqual(labels, {(6.0, 7.0)})

    def test_two_fresh_simulators_agree_including_the_trace(self):
        proposal = fault_scenario.propose_scenarios(7, 3)[2]
        first = fs.RelayReflexSimulator().run(copy.deepcopy(proposal["scenario"]), copy.deepcopy(proposal["intervention"]))
        second = fs.RelayReflexSimulator().run(copy.deepcopy(proposal["scenario"]), copy.deepcopy(proposal["intervention"]))
        self.assertEqual(first, second)
        self.assertEqual(first.trace, second.trace)


class Tiers(unittest.TestCase):
    """The decision tables on hand-built observations, no tick loop."""

    def test_tiers_follow_the_precedence_and_cover_every_reason_once(self):
        self.assertEqual(tuple(outcome for outcome, _ in fs.TIERS), fv.OUTCOME_PRECEDENCE[:-1])
        codes = [code for _, rules in fs.TIERS for code, _ in rules] + list(fs.CONTINUE_REASONS)
        self.assertEqual(len(codes), len(set(codes)))
        self.assertEqual(set(codes), fv.REASON_CODE_SET)
        self.assertEqual(set(fs.RECOVERY_EXTRA), set(fv.OUTCOMES) - {"continue"})

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
        self.assertEqual(select(result_delay_ms=44.0, peak_temperature=70.0, dropped=3), ("fail_closed", ("NO_TIMELY_INPUT",)))
        self.assertEqual(
            select(max_staleness=14.0, dropped=7, worst_healthy=3),
            ("degrade_gracefully", ("STALE_BEYOND_THRESHOLD", "EVENTS_DROPPED", "REDUCED_CHANNEL_SET")),
        )

    def test_row_6_a_zero_threshold_needs_actual_corruption(self):
        strict = fault_config.checked_system(scenario(corruption_quarantine_ratio=0.0))
        self.assertEqual(fs.select_outcome(observe(), strict), ("continue", ("WITHIN_TOLERANCE",)))
        self.assertEqual(fs.select_outcome(observe(corrupt=1), strict), ("quarantine", ("CORRUPTION_ABOVE_QUARANTINE_THRESHOLD",)))
        self.assertEqual(observe(corrupt=1, total=0).corrupt_ratio, 0.0)

    def test_fallback_availability(self):
        self.assertFalse(fs.fallback_available({"fallback_source": None}, set(), ()))
        self.assertFalse(fs.fallback_available(SYSTEM, {"redundant_relay_b"}, ()))
        self.assertFalse(fs.fallback_available(SYSTEM, set(), ("c0", "redundant_relay_b")))
        self.assertTrue(fs.fallback_available(SYSTEM, {"c3"}, ("c0",)))

    def test_latencies_are_onset_relative_clamped_rounded_synthesised_and_composed(self):
        self.assertEqual(fs.detection_latency_ms(observe(detection_ms=10.0004), 4.0, SYSTEM), 6.0)
        self.assertEqual(fs.detection_latency_ms(observe(detection_ms=2.0), 6.0, SYSTEM), 0.0)
        self.assertEqual(fs.detection_latency_ms(observe(result_delay_ms=18.0), 0.0, SYSTEM), 12.0)
        self.assertIsNone(fs.detection_latency_ms(observe(result_delay_ms=12.0), 0.0, SYSTEM))
        self.assertEqual(fs.recovery_latency_ms(SYSTEM, "continue", 3.0), 0.0)
        self.assertEqual(fs.recovery_latency_ms(SYSTEM, "fallback", None), 0.0)
        for outcome, extra in (("fallback", 4.0), ("degrade_gracefully", 2.0), ("fail_closed", 1.0)):
            with self.subTest(outcome=outcome):
                self.assertEqual(fs.recovery_latency_ms(SYSTEM, outcome, 6.0), 6.0 + extra)
        decision = fs.decide(observe(dropped=2, detection_ms=8.0), SYSTEM, 4.0)
        self.assertEqual(decision, fs.Decision("degrade_gracefully", ("EVENTS_DROPPED",), 4.0, 6.0))


class Invariants(unittest.TestCase):
    def test_continue_iff_no_detection_and_recovery_follows_detection(self):
        engine = fs.RelayReflexSimulator()
        seen = set()
        for seed in range(1, 11):
            for proposal in fault_scenario.propose_scenarios(seed, 36):
                result = engine.run(proposal["scenario"], proposal["intervention"])
                seen.update(result.reason_codes)
                with self.subTest(seed=seed, index=proposal["index"]):
                    # Every rule checked_result requires of an injected oracle holds for the simulator's own verdicts.
                    self.assertIs(fs.checked_result(result, fault_config.checked_system(proposal["scenario"])), result)
                    self.assertEqual(result.outcome == "continue", result.detection_latency_ms is None)
                    if result.outcome == "continue":
                        self.assertEqual((result.integrity_violation, result.dropped_events, result.corrupt_events, result.saturated_ticks), (False, 0, 0, 0))
                    self.assertLessEqual(set(result.reason_codes), fv.REASON_CODE_SET)
                    if result.outcome != "continue":
                        self.assertGreater(result.recovery_latency_ms, result.detection_latency_ms)
                        self.assertGreaterEqual(result.detection_latency_ms, 0.0)
        self.assertEqual(seen, fv.REASON_CODE_SET)


class OracleBlock(unittest.TestCase):
    def test_the_block_records_identity_and_the_effective_system(self):
        block = fs.RelayReflexSimulator().oracle_block({"system": {"ticks": 5}})
        self.assertEqual((block["name"], block["type"], block["version"]), (fv.ORACLE_NAME, fv.ORACLE_TYPE, fv.ORACLE_VERSION))
        self.assertEqual((block["implementation"], block["authority"]), (fv.ORACLE_IMPLEMENTATION, "authoritative"))
        self.assertEqual(block["configuration"]["system"], fault_config.checked_system({"system": {"ticks": 5}}))
        self.assertEqual(block["configuration"]["precedence"], list(fv.OUTCOME_PRECEDENCE))
        self.assertEqual((block["seed"], block["commit"]), (None, None))
        full = scenario()
        self.assertEqual(fs.RelayReflexSimulator().oracle_block(full)["configuration"]["system"], full["system"])

    def test_the_configuration_recorded_is_the_configuration_run(self):
        partial = {"system": {"ticks": 5}}
        result = fs.RelayReflexSimulator().run(partial, disturbance("missing_channel", channels=["c1"]))
        recorded = fs.RelayReflexSimulator().oracle_block(partial)["configuration"]["system"]
        self.assertEqual((result.total_events, recorded["ticks"], len(recorded)), (15, 5, 17))
