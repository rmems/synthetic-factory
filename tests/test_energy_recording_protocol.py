"""Recorded costs cannot be relabeled with a different measurement protocol."""

import unittest

from test_energy_preferences import ep, oc


def recorded_meter(**protocol):
    scenario = ep.propose_scenarios(21, 1)[0]["scenario"]
    return ep.RecordedEnergyMeter({
        "meter": "external_power_meter", "cost_quantity": "energy_j",
        "observations": {
            ep.workload_key(policy, scenario, ep.MeterProtocol(**protocol)): {"cost_value": 1.0}
            for policy in ep.POLICY_DESCRIPTIONS
        },
    })


class RecordingProtocol(unittest.TestCase):
    def test_changed_repeat_or_warmup_protocol_is_not_replayed(self):
        meter = recorded_meter()
        for protocol in ({"repeats": 6}, {"warmup": 2}):
            spec = ep.MeterSpec(meter=meter, **protocol)
            with self.subTest(protocol=protocol), self.assertRaises(oc.OracleUnavailable):
                ep.build_records(21, 1, spec)

    def test_matching_nondefault_protocol_replays_and_reports_original_settings(self):
        meter = recorded_meter(repeats=3, warmup=0)
        record = ep.build_records(21, 1, ep.MeterSpec(meter=meter, repeats=3, warmup=0))[0]
        self.assertEqual(record["oracle"]["configuration"]["repeats"], 3)
        self.assertEqual(record["oracle"]["configuration"]["warmup"], 0)
        self.assertEqual(ep.check_family(record, "test"), [])
