"""Declared faults and relay health requirements must be realizable."""

import unittest

from test_fault_recovery import disturbance, fr, oc, scenario


class SampledFaultWindows(unittest.TestCase):
    def test_duration_window_must_include_a_sampled_tick(self):
        simulator = fr.RelayReflexSimulator()
        state = scenario()
        for kind in ("sensor_loss", "stale_sensor", "event_jitter", "temporary_saturation"):
            for duration in (0.1, 1.0):
                params = dict(channels=["c0"], onset_ms=1.0, duration_ms=duration)
                if kind == "event_jitter":
                    params["jitter_ms"] = 3.0
                fault = disturbance(kind, **params)
                with self.subTest(kind=kind, duration=duration), self.assertRaisesRegex(oc.ContractError, "sampled tick"):
                    simulator.run(state, fault)

    def test_window_crossing_a_tick_remains_valid(self):
        result = fr.RelayReflexSimulator().run(
            scenario(), disturbance("sensor_loss", channels=["c0"], onset_ms=1.0, duration_ms=1.1)
        )
        self.assertEqual(result.worst_healthy_channels, 3)

    def test_health_requirement_cannot_exceed_primary_channel_count(self):
        simulator = fr.RelayReflexSimulator()
        state = scenario(min_healthy_channels=5)
        fault = disturbance("event_jitter", channels=["c0"], onset_ms=2.0, duration_ms=4.0, jitter_ms=1.0)
        with self.assertRaisesRegex(oc.ContractError, "min_healthy_channels"):
            simulator.run(state, fault)
