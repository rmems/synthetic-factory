#!/usr/bin/env python3
"""Direct tests of ``fault_config``: the enforced D7 system rows as coded
refusals, the held rows as accepted configurations, the carried row-12
system checks, the effective-system contract, D7 row 2, every carried
row-12 parameter check by code and fragment, the window, capacity and
narrowing rules and the refusal order."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from fault_test_support import disturbance, fault_config, fault_simulator, fault_vocabulary as fv, refusal, scenario

checked = fault_config.checked_system
SYSTEM = checked(scenario())
NO_FALLBACK = checked(scenario(fallback_source=None))
CHANNEL_REQUIRED = tuple(kind for kind in fv.DISTURBANCES if "channels" in fv.PARAMETER_SPEC[kind][0])


def check(kind, system=SYSTEM, **parameters):
    return fault_config.checked_disturbance(disturbance(kind, **parameters), system)


def loss(**overrides):
    return {"channels": ["c0"], "onset_ms": 4.0, "duration_ms": 6.0, **overrides}


def thermal(**overrides):
    return {"onset_ms": 6.0, "ramp_ms": 8.0, "peak_c": 70.0, **overrides}


def full(kind):
    """A complete, valid parameter set for ``kind`` on the default relay."""
    return {
        "sensor_loss": loss(), "stale_sensor": loss(), "event_jitter": loss(jitter_ms=0.4),
        "burst_corruption": loss(corrupt_ratio=0.5), "missing_channel": {"channels": ["c3"]},
        "malformed_spike_burst": {"channels": ["c0"], "malformed_count": 1, "malformed_kind": "unknown_channel"},
        "temporary_saturation": loss(),
    }[kind]


class EnforcedSystemRows(unittest.TestCase):
    def test_row_1_the_thermal_ladder_starts_at_ambient(self):
        for controls in ({"ambient_c": 100.0}, {"ambient_c": 62.0}, {"thermal_shutdown_c": 10.0}):
            with self.subTest(controls=controls), refusal(self, fv.FINDING_THERMAL_LADDER_UNORDERED, "thermal ladder"):
                checked(scenario(**controls))
        self.assertEqual(checked(scenario())["ambient_c"], 38.0)

    def test_row_4_the_healthy_budget_stays_within_the_channel_count(self):
        with refusal(self, fv.FINDING_HEALTHY_BUDGET_EXCEEDS_CHANNELS, "min_healthy_channels"):
            checked(scenario(min_healthy_channels=10))
        with refusal(self, fv.FINDING_SYSTEM_CONTROL_OUT_OF_DOMAIN, "min_healthy_channels", ">= 0"):
            checked(scenario(min_healthy_channels=-1))
        for budget in (0, 4):
            with self.subTest(budget=budget):
                self.assertEqual(checked(scenario(min_healthy_channels=budget))["min_healthy_channels"], budget)

    def test_row_5_the_soft_deadline_precedes_the_hard_one(self):
        for controls in ({"hard_deadline_ms": 5.0}, {"hard_deadline_ms": 12.0}):
            with self.subTest(controls=controls), refusal(self, fv.FINDING_DEADLINE_ORDER_INVERTED, "deadline_ms"):
                checked(scenario(**controls))

    def test_row_7_the_horizon_is_finite_but_tick_versus_staleness_is_held(self):
        with refusal(self, fv.FINDING_HORIZON_NOT_FINITE, "tick_ms"):
            checked(scenario(tick_ms=1e308))
        self.assertEqual(checked(scenario(tick_ms=10.0, stale_threshold_ms=8.0))["tick_ms"], 10.0)

    def test_the_recovery_horizon_is_finite_like_the_tick_horizon(self):
        """Codex finding: accepted controls whose last tick plus a tier latency overflow
        made a valid configuration yield an infinite recovery reading."""
        huge = dict(tick_ms=8e307, ticks=2, stale_threshold_ms=1e307, deadline_ms=1e306, hard_deadline_ms=2e306)
        with refusal(self, fv.FINDING_SYSTEM_CONTROL_OUT_OF_DOMAIN, "recovery horizon"):
            checked(scenario(**huge, fallback_latency_ms=1e308, min_healthy_channels=4))
        with refusal(self, fv.FINDING_SYSTEM_CONTROL_OUT_OF_DOMAIN, "recovery horizon"):
            checked(scenario(**huge, reflex_latency_ms=1e308))
        self.assertEqual(checked(scenario(**huge))["tick_ms"], 8e307)

    def test_the_thermal_span_from_ambient_to_shutdown_is_finite_like_the_horizon(self):
        ladder = {"ambient_c": -1.7e308, "thermal_warn_c": -1e308, "thermal_limit_c": 0.0}
        with refusal(self, fv.FINDING_SYSTEM_CONTROL_OUT_OF_DOMAIN, "thermal span", "ambient_c"):
            checked(scenario(**ladder, thermal_shutdown_c=1.7e308))
        self.assertEqual(checked(scenario(**ladder, thermal_shutdown_c=1.0))["thermal_shutdown_c"], 1.0)

    def test_row_8_unknown_system_keys_are_refused_before_the_merge(self):
        with refusal(self, fv.FINDING_SYSTEM_UNKNOWN_KEY, "hard_deadline", "min_healthy_channel"):
            checked({"system": {"hard_deadline": 1.0, "min_healthy_channel": 4}})

    def test_missing_keys_are_filled_from_the_defaults(self):
        partial = checked({"system": {"ticks": 5}})
        self.assertEqual((set(partial), partial["ticks"]), (fv.SYSTEM_KEYS, 5))
        self.assertEqual(checked({"mission": "x"}), fv.DEFAULT_SYSTEM)


class CarriedSystemRefusals(unittest.TestCase):
    def test_row_12_control_domains_name_the_key(self):
        cases = (
            ("corruption_quarantine_ratio", -1), ("ticks", 0), ("ticks", 1001), ("ticks", True), ("tick_ms", 0),
            ("min_healthy_channels", True), ("thermal_warn_c", "hot"), ("jitter_tolerance_ms", -0.1),
        )
        for key, value in cases:
            with self.subTest(key=key, value=value), refusal(self, fv.FINDING_SYSTEM_CONTROL_OUT_OF_DOMAIN, key):
                checked(scenario(**{key: value}))
        with refusal(self, fv.FINDING_SYSTEM_CONTROL_OUT_OF_DOMAIN, "tick_ms"):
            fault_config.check_system({})

    def test_row_12_the_channel_list_is_bounded_unique_and_named(self):
        cases = ([f"c{i}" for i in range(33)], ["c0", "c0"], [], ["c0", ""], ["c0", 1], "c0")
        for channels in cases:
            with self.subTest(channels=channels), refusal(self, fv.FINDING_CHANNEL_LIST_INVALID, "channel", "unique"):
                checked(scenario(channels=channels))
        wide = [f"c{i}" for i in range(32)]
        self.assertEqual(checked(scenario(channels=wide))["channels"], wide)

    def test_row_12_the_fallback_source_is_null_or_a_redundant_name(self):
        for fallback in (123, "  "):
            with self.subTest(fallback=fallback), refusal(self, fv.FINDING_FALLBACK_SOURCE_INVALID, "fallback_source"):
                checked(scenario(fallback_source=fallback))
        with refusal(self, fv.FINDING_FALLBACK_SOURCE_IS_PRIMARY, "redundant source"):
            checked(scenario(fallback_source="c0"))
        self.assertIsNone(checked(scenario(fallback_source=None))["fallback_source"])

    def test_non_objects_are_coded_refusals_never_bare_type_errors(self):
        for bad in (None, "x", {"system": "x"}, {"system": None}):
            with self.subTest(bad=bad), refusal(self, fv.FINDING_INPUT_NOT_AN_OBJECT, "must be an object"):
                checked(bad)

    def test_the_effective_system_aliases_neither_input_nor_defaults(self):
        proposal = scenario()
        effective = checked(proposal)
        self.assertIsNot(effective["channels"], proposal["system"]["channels"])
        self.assertIsNot(effective["channels"], fv.DEFAULT_SYSTEM["channels"])
        effective["channels"].append("ghost")
        self.assertEqual(fv.DEFAULT_SYSTEM["channels"], ["c0", "c1", "c2", "c3"])
        self.assertEqual(proposal["system"]["channels"], ["c0", "c1", "c2", "c3"])


class EnforcedDisturbanceRow2(unittest.TestCase):
    def test_a_thermal_peak_must_rise_above_ambient(self):
        for peak in (20.0, 38.0):
            with self.subTest(peak=peak), refusal(self, fv.FINDING_PEAK_NOT_ABOVE_AMBIENT, "ambient"):
                check("thermal_excursion", **thermal(peak_c=peak))
        self.assertEqual(check("thermal_excursion", **thermal(peak_c=58.0)).parameters["peak_c"], 58.0)

    def test_a_thermal_span_that_overflows_is_refused_before_the_ramp_runs(self):
        """Two finite controls whose difference is inf would otherwise give an
        infinite peak_temperature_c and trace from an accepted run()."""
        cold = checked(scenario(ambient_c=-1.7e308, thermal_warn_c=-1e308, thermal_limit_c=0.0, thermal_shutdown_c=1.0))
        with refusal(self, fv.FINDING_PARAMETER_OUT_OF_DOMAIN, "peak_c", "finite span"):
            check("thermal_excursion", cold, **thermal(peak_c=1.7e308))
        with refusal(self, fv.FINDING_PARAMETER_OUT_OF_DOMAIN, "finite span"):
            fault_simulator.RelayReflexSimulator().run(
                {"system": dict(cold)}, disturbance("thermal_excursion", **thermal(peak_c=1.7e308))
            )
        self.assertEqual(check("thermal_excursion", cold, **thermal(peak_c=0.5)).parameters["peak_c"], 0.5)


class CarriedDisturbanceRefusals(unittest.TestCase):
    def test_shape_kind_and_the_effective_system_are_checked_first(self):
        for bad in ("x", {"kind": "sensor_loss", "parameters": "x"}):
            with self.subTest(bad=bad), refusal(self, fv.FINDING_INPUT_NOT_AN_OBJECT, "must be an object"):
                fault_config.checked_disturbance(bad, SYSTEM)
        for bad in ({"kind": "gremlins", "parameters": {"bogus": 1}}, {"parameters": {}}):
            with self.subTest(bad=bad), refusal(self, fv.FINDING_DISTURBANCE_KIND_UNKNOWN, "unknown disturbance kind"):
                fault_config.checked_disturbance(bad, SYSTEM)
        for system in (None, {}, {"ticks": 24}, {**SYSTEM, "extra": 1}):
            with self.subTest(system=str(system)[:24]), refusal(self, fv.FINDING_INPUT_NOT_AN_OBJECT, "checked_system"):
                check("sensor_loss", system, **loss())
        # A full-key dict is re-checked control by control, not trusted for its keys.
        with refusal(self, fv.FINDING_SYSTEM_CONTROL_OUT_OF_DOMAIN, "ticks"):
            check("missing_channel", {**SYSTEM, "ticks": "bad"}, channels=["c3"])

    def test_missing_and_unknown_parameters_are_no_ops_and_refused(self):
        with refusal(self, fv.FINDING_PARAMETER_MISSING, "no-op", "duration_ms", "onset_ms"):
            check("sensor_loss", channels=["c0"])
        with refusal(self, fv.FINDING_PARAMETER_UNKNOWN, "stale_age_ms"):
            check("stale_sensor", **loss(stale_age_ms=3.0))

    def test_floors_refuse_values_that_cannot_open_the_window(self):
        cases = (
            ("sensor_loss", loss(duration_ms=-5.0)), ("sensor_loss", loss(duration_ms=0)),
            ("sensor_loss", loss(onset_ms=-1.0)), ("sensor_loss", loss(onset_ms=True)),
            ("event_jitter", loss(jitter_ms=0.0)), ("delayed_result", {"delay_ms": 0.0}),
            ("thermal_excursion", thermal(ramp_ms=-8.0)),
        )
        for kind, parameters in cases:
            with self.subTest(kind=kind, parameters=parameters), refusal(self, fv.FINDING_PARAMETER_OUT_OF_DOMAIN, kind):
                check(kind, **parameters)
        self.assertEqual(check("sensor_loss", **loss(onset_ms=0.0)).parameters["onset_ms"], 0.0)

    def test_value_rules_name_the_offending_key(self):
        burst = {"channels": ["c1"], "malformed_count": 2, "malformed_kind": "negative_amplitude"}
        cases = [("thermal_excursion", "peak_c", value) for value in (float("nan"), float("inf"), "70")]
        cases += [("malformed_spike_burst", "malformed_count", value) for value in (0, True)]
        cases += [("malformed_spike_burst", "malformed_kind", "negative_amplitdue")]
        cases += [
            ("burst_corruption", "corrupt_ratio", value)
            for value in (-0.5, 1.5, float("nan"), float("inf"), "0.4", None, True)
        ]
        for kind, key, value in cases:
            base = {"thermal_excursion": thermal(), "malformed_spike_burst": burst}.get(kind, loss(corrupt_ratio=0.5))
            with self.subTest(kind=kind, key=key, value=value), refusal(self, fv.FINDING_PARAMETER_OUT_OF_DOMAIN, key):
                check(kind, **{**base, key: value})
        for ratio in (0.0, 1.0):
            with self.subTest(ratio=ratio):
                self.assertEqual(check("burst_corruption", **loss(corrupt_ratio=ratio)).kind, "burst_corruption")

    def test_channels_must_be_a_list_and_non_empty_where_required(self):
        with refusal(self, fv.FINDING_CHANNELS_NOT_A_LIST, "must be a list"):
            check("sensor_loss", **loss(channels="c0"))
        for kind in CHANNEL_REQUIRED:
            with self.subTest(kind=kind), refusal(self, fv.FINDING_CHANNELS_EMPTY, "no-op"):
                check(kind, **{**full(kind), "channels": []})
        self.assertEqual(check("thermal_excursion", **thermal(channels=[])).declared, ())
        self.assertEqual(check("delayed_result", delay_ms=6.0, channels=[]).affected, ())

    def test_declared_names_are_relay_channels_or_the_fallback_source(self):
        cases = ((["typo"], SYSTEM), ([1], SYSTEM), (["redundant_relay_b"], NO_FALLBACK))
        for channels, system in cases:
            with self.subTest(channels=channels), refusal(self, fv.FINDING_CHANNEL_UNKNOWN, "unknown channels"):
                check("sensor_loss", system, **loss(channels=channels))

    def test_a_required_list_naming_only_the_fallback_is_a_no_op(self):
        for kind in CHANNEL_REQUIRED:
            with self.subTest(kind=kind), refusal(self, fv.FINDING_CHANNELS_NO_RELAY_CHANNEL, "fallback source"):
                check(kind, **{**full(kind), "channels": ["redundant_relay_b"]})
        both = check("sensor_loss", **loss(channels=["c0", "redundant_relay_b"]))
        self.assertEqual((both.affected, both.declared), (("c0",), ("c0", "redundant_relay_b")))
        self.assertEqual(check("sensor_loss", **loss(channels=["c0", "c0"])).affected, ("c0", "c0"))

    def test_the_onset_must_fall_on_or_before_the_last_tick(self):
        for onset in (1000.0, 100.0, 48.0):
            with self.subTest(onset=onset), refusal(self, fv.FINDING_ONSET_BEYOND_HORIZON, "never occur"):
                check("sensor_loss", **loss(onset_ms=onset))
        self.assertEqual(check("sensor_loss", **loss(onset_ms=46.0)).parameters["onset_ms"], 46.0)

    def test_a_window_that_contains_no_simulated_tick_is_refused(self):
        """Reviewer finding: [45, 46) on the 2 ms grid misses both adjacent ticks, so the
        loss would run as a no-op and be labelled ``continue``; [45, 47) holds tick 46."""
        for onset, duration in ((45.0, 1.0), (1.0, 0.5), (43.0, 0.9)):
            with self.subTest(onset=onset, duration=duration), refusal(
                self, fv.FINDING_DISTURBANCE_WINDOW_EMPTY, "contains no simulated tick"
            ):
                check("sensor_loss", **loss(onset_ms=onset, duration_ms=duration))
        self.assertEqual(check("sensor_loss", **loss(onset_ms=45.0, duration_ms=2.0)).parameters["onset_ms"], 45.0)
        self.assertEqual(check("sensor_loss", **loss(onset_ms=46.0, duration_ms=0.5)).parameters["duration_ms"], 0.5)

    def test_a_malformed_burst_cannot_exceed_one_event_per_channel_per_tick(self):
        """Reviewer finding: a count above ticks x affected channels was silently truncated."""
        burst = {"channels": ["c0"], "malformed_kind": "unknown_channel"}
        with refusal(self, fv.FINDING_PARAMETER_OUT_OF_DOMAIN, "exceeds the run's capacity of 24 events"):
            check("malformed_spike_burst", malformed_count=25, **burst)
        with refusal(self, fv.FINDING_PARAMETER_OUT_OF_DOMAIN, "capacity of 48 events"):
            check("malformed_spike_burst", channels=["c0", "c1"], malformed_count=49, malformed_kind="unknown_channel")
        self.assertEqual(check("malformed_spike_burst", malformed_count=24, **burst).parameters["malformed_count"], 24)
        # A name declared twice adds no capacity: the simulator visits c0 once per tick.
        with refusal(self, fv.FINDING_PARAMETER_OUT_OF_DOMAIN, "capacity of 24 events", "1 distinct"):
            check("malformed_spike_burst", channels=["c0", "c0"], malformed_count=25, malformed_kind="unknown_channel")
        twice = fault_simulator.RelayReflexSimulator().run(
            scenario(),
            disturbance("malformed_spike_burst", channels=["c0", "c0"], malformed_count=24, malformed_kind="unknown_channel"),
        )
        self.assertEqual(twice.dropped_events, 24)
        result = fault_simulator.RelayReflexSimulator().run(
            scenario(), disturbance("malformed_spike_burst", malformed_count=24, **burst)
        )
        self.assertEqual(result.dropped_events, 24)

    def test_refusal_order_kind_before_parameters_and_floors_before_horizon(self):
        with refusal(self, fv.FINDING_DISTURBANCE_KIND_UNKNOWN):
            check("gremlins", onset_ms="soon")
        with refusal(self, fv.FINDING_PARAMETER_OUT_OF_DOMAIN, "onset_ms"):
            check("sensor_loss", **loss(onset_ms="soon"))
