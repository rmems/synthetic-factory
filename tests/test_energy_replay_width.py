"""Untrusted actuator dimensions must not trigger unbounded policy replay."""

import copy
import unittest

from test_energy_preferences import FakeMeter, ep, oc


class EnergyReplayWidth(unittest.TestCase):
    def test_oversized_actuator_state_is_a_finding_before_grid_replay(self):
        original = ep.build_records(7, 1, ep.MeterSpec(meter=FakeMeter(), repeats=2))[0]
        for width in (5, 1100):
            with self.subTest(width=width):
                record = copy.deepcopy(original)
                record["scenario"]["state"]["actuator_caps"] = [1.0] * width
                record["scenario"]["state"]["actuator_weights"] = [1.0] * width
                record["oracle"]["configuration"].update(fine_steps=1, coarse_steps=1)
                record["provenance"]["record_sha256"] = oc.record_digest(record)
                errors = ep.check_family(record, "test")
                self.assertTrue(any("actuator" in e and "at most 4" in e for e in errors), errors)
