#!/usr/bin/env python3
"""Direct tests of ``fault_config``: the enforced D7 system rows as coded
refusals, the held rows as accepted configurations, the carried row-12 checks
and the effective-system contract."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from fault_test_support import fault_config, fault_vocabulary as fv, refusal, scenario

checked = fault_config.checked_system


class EnforcedRows(unittest.TestCase):
    def test_row_1_the_thermal_ladder_starts_at_ambient(self):
        for controls in ({"ambient_c": 100.0}, {"ambient_c": 62.0}, {"thermal_shutdown_c": 10.0}):
            with self.subTest(controls=controls), refusal(self, fv.FINDING_THERMAL_LADDER_UNORDERED, "thermal ladder"):
                checked(scenario(**controls))
        self.assertEqual(checked(scenario())["ambient_c"], 38.0)

    def test_row_4_the_healthy_budget_stays_within_the_channel_count(self):
        with refusal(self, fv.FINDING_HEALTHY_BUDGET_EXCEEDS_CHANNELS, "min_healthy_channels"):
            checked(scenario(min_healthy_channels=10))
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
        self.assertEqual(set(partial), fv.SYSTEM_KEYS)
        self.assertEqual(partial["ticks"], 5)
        self.assertEqual(checked({"mission": "x"}), fv.DEFAULT_SYSTEM)


class CarriedRefusals(unittest.TestCase):
    def test_row_12_control_domains_name_the_key(self):
        cases = (
            ("corruption_quarantine_ratio", -1),
            ("ticks", 0),
            ("ticks", 1001),
            ("ticks", True),
            ("tick_ms", 0),
            ("min_healthy_channels", True),
            ("thermal_warn_c", "hot"),
            ("jitter_tolerance_ms", -0.1),
        )
        for key, value in cases:
            with self.subTest(key=key, value=value), refusal(self, fv.FINDING_SYSTEM_CONTROL_OUT_OF_DOMAIN, key):
                checked(scenario(**{key: value}))

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


class EffectiveSystem(unittest.TestCase):
    def test_the_effective_system_aliases_neither_input_nor_defaults(self):
        proposal = scenario()
        effective = checked(proposal)
        self.assertIsNot(effective["channels"], proposal["system"]["channels"])
        self.assertIsNot(effective["channels"], fv.DEFAULT_SYSTEM["channels"])
        effective["channels"].append("ghost")
        self.assertEqual(fv.DEFAULT_SYSTEM["channels"], ["c0", "c1", "c2", "c3"])
        self.assertEqual(proposal["system"]["channels"], ["c0", "c1", "c2", "c3"])

    def test_check_system_reports_a_missing_control_as_out_of_domain(self):
        with refusal(self, fv.FINDING_SYSTEM_CONTROL_OUT_OF_DOMAIN, "tick_ms"):
            fault_config.check_system({})

