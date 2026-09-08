#!/usr/bin/env python3
"""Direct tests of ``fault_parameters``: D7 row 2, every carried row-12
parameter check by code and fragment, the boundary acceptances, the
affected/declared narrowing and the refusal order."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from fault_test_support import (
    disturbance,
    fault_config,
    fault_parameters,
    fault_simulator,
    fault_vocabulary as fv,
    refusal,
    scenario,
)

SYSTEM = fault_config.checked_system(scenario())
NO_FALLBACK = fault_config.checked_system(scenario(fallback_source=None))
CHANNEL_REQUIRED = tuple(kind for kind in fv.DISTURBANCES if "channels" in fv.PARAMETER_SPEC[kind][0])


def check(kind, system=SYSTEM, **parameters):
    return fault_parameters.checked_disturbance(disturbance(kind, **parameters), system)


def loss(**overrides):
    parameters = {"channels": ["c0"], "onset_ms": 4.0, "duration_ms": 6.0}
    parameters.update(overrides)
    return parameters


def thermal(**overrides):
    parameters = {"onset_ms": 6.0, "ramp_ms": 8.0, "peak_c": 70.0}
    parameters.update(overrides)
    return parameters


class EnforcedRow2(unittest.TestCase):
    def test_a_thermal_peak_must_rise_above_ambient(self):
        for peak in (20.0, 38.0):
            with self.subTest(peak=peak), refusal(self, fv.FINDING_PEAK_NOT_ABOVE_AMBIENT, "ambient"):
                check("thermal_excursion", **thermal(peak_c=peak))
        self.assertEqual(check("thermal_excursion", **thermal(peak_c=58.0)).parameters["peak_c"], 58.0)

    def test_a_thermal_span_that_overflows_is_refused_before_the_ramp_runs(self):
        """Two finite controls whose difference is inf would otherwise give an
        infinite peak_temperature_c and trace from an accepted run()."""
        cold = fault_config.checked_system(
            scenario(ambient_c=-1.7e308, thermal_warn_c=-1e308, thermal_limit_c=0.0, thermal_shutdown_c=1.0)
        )
        with refusal(self, fv.FINDING_PARAMETER_OUT_OF_DOMAIN, "peak_c", "finite span"):
            check("thermal_excursion", cold, **thermal(peak_c=1.7e308))
        with refusal(self, fv.FINDING_PARAMETER_OUT_OF_DOMAIN, "finite span"):
            fault_simulator.RelayReflexSimulator().run(
                {"system": dict(cold)}, disturbance("thermal_excursion", **thermal(peak_c=1.7e308))
            )
        self.assertEqual(check("thermal_excursion", cold, **thermal(peak_c=0.5)).parameters["peak_c"], 0.5)


class CarriedRefusals(unittest.TestCase):
    def test_shape_and_kind_are_checked_first(self):
        for bad in ("x", {"kind": "sensor_loss", "parameters": "x"}):
            with self.subTest(bad=bad), refusal(self, fv.FINDING_INPUT_NOT_AN_OBJECT, "must be an object"):
                fault_parameters.checked_disturbance(bad, SYSTEM)
        for bad in ({"kind": "gremlins", "parameters": {"bogus": 1}}, {"parameters": {}}):
            with self.subTest(bad=bad), refusal(self, fv.FINDING_DISTURBANCE_KIND_UNKNOWN, "unknown disturbance kind"):
                fault_parameters.checked_disturbance(bad, SYSTEM)

    def test_missing_and_unknown_parameters_are_no_ops_and_refused(self):
        with refusal(self, fv.FINDING_PARAMETER_MISSING, "no-op", "duration_ms", "onset_ms"):
            check("sensor_loss", channels=["c0"])
        with refusal(self, fv.FINDING_PARAMETER_UNKNOWN, "stale_age_ms"):
            check("stale_sensor", **loss(stale_age_ms=3.0))

    def test_floors_refuse_values_that_cannot_open_the_window(self):
        cases = (
            ("sensor_loss", loss(duration_ms=-5.0)),
            ("sensor_loss", loss(duration_ms=0)),
            ("sensor_loss", loss(onset_ms=-1.0)),
            ("sensor_loss", loss(onset_ms=True)),
            ("event_jitter", loss(jitter_ms=0.0)),
            ("delayed_result", {"delay_ms": 0.0}),
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
                check(kind, **{**_full(kind), "channels": []})
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
                check(kind, **{**_full(kind), "channels": ["redundant_relay_b"]})
        both = check("sensor_loss", **loss(channels=["c0", "redundant_relay_b"]))
        self.assertEqual((both.affected, both.declared), (("c0",), ("c0", "redundant_relay_b")))
        self.assertEqual(check("sensor_loss", **loss(channels=["c0", "c0"])).affected, ("c0", "c0"))

    def test_the_onset_must_fall_on_or_before_the_last_tick(self):
        for onset in (1000.0, 100.0, 48.0):
            with self.subTest(onset=onset), refusal(self, fv.FINDING_ONSET_BEYOND_HORIZON, "never occur"):
                check("sensor_loss", **loss(onset_ms=onset))
        self.assertEqual(check("sensor_loss", **loss(onset_ms=46.0)).parameters["onset_ms"], 46.0)

    def test_refusal_order_kind_before_parameters_and_floors_before_horizon(self):
        with refusal(self, fv.FINDING_DISTURBANCE_KIND_UNKNOWN):
            check("gremlins", onset_ms="soon")
        with refusal(self, fv.FINDING_PARAMETER_OUT_OF_DOMAIN, "onset_ms"):
            check("sensor_loss", **loss(onset_ms="soon"))


def _full(kind):
    """A complete, valid parameter set for ``kind`` on the default relay."""

    return {
        "sensor_loss": loss(),
        "stale_sensor": loss(),
        "event_jitter": loss(jitter_ms=0.4),
        "burst_corruption": loss(corrupt_ratio=0.5),
        "missing_channel": {"channels": ["c3"]},
        "malformed_spike_burst": {"channels": ["c0"], "malformed_count": 1, "malformed_kind": "unknown_channel"},
        "temporary_saturation": loss(),
    }[kind]

