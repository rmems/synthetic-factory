#!/usr/bin/env python3
"""Direct tests of ``fault_boundary``: the frozen result's derived ratios and
the abstract oracle."""

import dataclasses
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from fault_test_support import fault_boundary, fault_oracle, fault_vocabulary as fv, oc


def result(**overrides):
    fields = {
        "outcome": "continue",
        "reason_codes": ("WITHIN_TOLERANCE",),
        "detection_latency_ms": None,
        "recovery_latency_ms": 0.0,
        "worst_healthy_channels": 4,
        "dropped_events": 0,
        "corrupt_events": 0,
        "total_events": 0,
        "peak_temperature_c": 38.0,
        "max_staleness_ms": 0.0,
        "max_jitter_ms": 0.0,
        "saturated_ticks": 0,
        "integrity_violation": False,
        "result_delay_ms": 0.0,
    }
    fields.update(overrides)
    return fault_boundary.FaultResult(**fields)


class FrozenResult(unittest.TestCase):
    def test_ratios_are_zero_without_events_and_derived_otherwise(self):
        empty = result()
        self.assertEqual((empty.realised_corrupt_ratio, empty.residual_error, empty.ticks), (0.0, 0.0, 0))
        busy = result(corrupt_events=3, dropped_events=1, total_events=8, trace=({"t_ms": 0.0},))
        self.assertEqual((busy.realised_corrupt_ratio, busy.residual_error, busy.ticks), (0.375, 0.5, 1))

    def test_a_result_is_frozen(self):
        with self.assertRaises(dataclasses.FrozenInstanceError):
            result().outcome = "fail_closed"


class AbstractOracle(unittest.TestCase):
    def test_the_boundary_declares_identity_but_no_meters_and_no_engine(self):
        oracle = fault_boundary.FaultOracle()
        self.assertEqual((oracle.meter_clock, oracle.meter_state, oracle.meter_thermal), (None, None, None))
        self.assertEqual(oracle.implementation, fv.BOUNDARY_IMPLEMENTATION)
        self.assertEqual(oracle.authority, oc.AUTHORITY_AUTHORITATIVE)
        with self.assertRaises(NotImplementedError):
            oracle.run({}, {})
        with self.assertRaises(NotImplementedError):
            oracle.oracle_block({})

    def test_fault_oracle_re_exports_the_boundary_classes(self):
        self.assertIs(fault_oracle.FaultOracle, fault_boundary.FaultOracle)
        self.assertIs(fault_oracle.FaultResult, fault_boundary.FaultResult)

