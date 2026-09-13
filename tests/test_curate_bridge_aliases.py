#!/usr/bin/env python3
"""Presence-aware raster aliases and runtime/schema parity regressions."""

from __future__ import annotations

import json
import re
import unittest

try:
    from tests.test_curate_bridge import RASTER_SCHEMA, curate_bridge, gate_snn_fixture
except ModuleNotFoundError:
    from test_curate_bridge import (  # type: ignore[no-redef]
        RASTER_SCHEMA,
        curate_bridge,
        gate_snn_fixture,
    )


def status(record):
    return curate_bridge.raster_status(record)


def gate_compute_check(**updates):
    check = {
        "neurons": 4,
        "mean_rate_hz": 10.0,
        "window_s": 0.05,
        "spikes": 2,
    }
    check.update(updates)
    return check


class PresenceAwareAliases(unittest.TestCase):
    def assert_invalid(self, record, reason):
        result = status(record)
        self.assertFalse(result["raster_valid"])
        self.assertIn(reason, result["reason_codes"])

    def test_explicitly_null_gate_window_aliases_are_not_absent(self):
        mutations = (
            {"decision_window_ms": None, "decision_window_s": 0.025},
            {"decision_window_ms": 25, "decision_window_s": None},
        )
        for values in mutations:
            with self.subTest(values=values):
                record = gate_snn_fixture()
                record["gate_snn"].update(values)
                self.assert_invalid(record, curate_bridge.REASON_GATE_SNN_INVALID)

    def test_population_and_third_factor_aliases_must_be_valid_and_agree(self):
        population_mutations = (
            {"mean_rate_hz": None, "rate_hz": 40},
            {"mean_rate_hz": 40, "rate_hz": None},
            {"mean_rate_hz": 40, "rate_hz": 41},
        )
        for values in population_mutations:
            with self.subTest(carrier="population", values=values):
                record = gate_snn_fixture()
                record["gate_snn"]["populations"][0].update(values)
                self.assert_invalid(record, curate_bridge.REASON_GATE_SNN_INVALID)

        record = gate_snn_fixture()
        record["gate_snn"]["populations"][0]["rate_hz"] = 40
        self.assertTrue(status(record)["raster_valid"])

        third_factor_mutations = (
            {"tau_e_s": None, "tau_e_ms": 2000},
            {"tau_e_s": 2.0, "tau_e_ms": None},
            {"tau_e_s": 2.0, "tau_e_ms": 1000},
        )
        for values in third_factor_mutations:
            with self.subTest(carrier="third_factor", values=values):
                record = gate_snn_fixture()
                record["raster"]["routing"]["third_factor"].update(values)
                self.assert_invalid(record, curate_bridge.REASON_THIRD_FACTOR_INVALID)

        record = gate_snn_fixture()
        record["raster"]["routing"]["third_factor"]["tau_e_ms"] = 2000
        self.assertTrue(status(record)["raster_valid"])

    def test_gate_compute_aliases_must_be_valid_and_agree(self):
        mutations = (
            {"mean_rate_hz": None, "rate_hz": 10.0},
            {"mean_rate_hz": 10.0, "rate_hz": None},
            {"mean_rate_hz": 10.0, "rate_hz": 11.0},
            {"window_s": None, "window_ms": 50},
            {"window_s": 0.05, "window_ms": None},
            {"window_s": 0.05, "window_ms": 60},
        )
        for values in mutations:
            with self.subTest(values=values):
                record = gate_snn_fixture()
                record["gate_compute"] = {"per_check": [gate_compute_check(**values)]}
                self.assert_invalid(record, curate_bridge.REASON_RASTER_SPIKE_BUDGET)

        for values in (
            {"rate_hz": 10.0, "window_ms": 50},
            {"rate_hz": 10.0, "window_ms": 50, "mean_rate_hz": 10.0},
            {"window_ms": 50, "window_s": 0.05},
        ):
            with self.subTest(accepted=values):
                record = gate_snn_fixture()
                check = gate_compute_check(**values)
                if "rate_hz" in values and "mean_rate_hz" not in values:
                    check.pop("mean_rate_hz")
                if "window_ms" in values and "window_s" not in values:
                    check.pop("window_s")
                record["gate_compute"] = {"per_check": [check]}
                self.assertTrue(status(record)["raster_valid"])


class DeclaredGateComputeTotals(unittest.TestCase):
    def test_totals_are_validated_without_per_check_entries(self):
        for per_check in (None, []):
            for key, value in (
                ("total_energy_pJ", -1),
                ("total_energy_pJ", "bad"),
                ("total_energy_pJ", 1),
                ("total_energy_uJ", -1),
                ("total_energy_uJ", "bad"),
                ("total_energy_uJ", 1),
            ):
                with self.subTest(per_check=per_check, key=key, value=value):
                    record = gate_snn_fixture()
                    gate_compute = {key: value}
                    if per_check is not None:
                        gate_compute["per_check"] = per_check
                    record["gate_compute"] = gate_compute
                    result = status(record)
                    self.assertFalse(result["raster_valid"])
                    self.assertIn(
                        curate_bridge.REASON_RASTER_ENERGY,
                        result["reason_codes"],
                    )

    def test_zero_totals_match_an_absent_or_empty_check_set(self):
        for gate_compute in (
            {"total_energy_pJ": 0, "total_energy_uJ": 0},
            {
                "per_check": [],
                "total_energy_pJ": 0,
                "total_energy_uJ": 0,
            },
        ):
            with self.subTest(gate_compute=gate_compute):
                record = gate_snn_fixture()
                record["gate_compute"] = gate_compute
                result = status(record)
                self.assertTrue(result["raster_valid"], result["reason_codes"])
                self.assertTrue(result["evidence"]["gate_compute_energy_valid"])


class NonblankSchemaParity(unittest.TestCase):
    def setUp(self):
        self.schema = json.loads(RASTER_SCHEMA.read_text(encoding="utf-8"))

    def test_runtime_trimmed_labels_have_nonwhitespace_schema_patterns(self):
        raster = self.schema["$defs"]["raster"]["properties"]
        routing = raster["routing"]["properties"]
        population = self.schema["$defs"]["gate_snn"]["properties"]["populations"]["items"][
            "properties"
        ]["name"]
        fields = (
            population,
            routing["source"],
            routing["target"],
            routing["table"]["items"]["properties"]["from"],
            routing["table"]["items"]["properties"]["to"],
            routing["third_factor"]["properties"]["modulator"],
            routing["third_factor"]["properties"]["eligibility"],
        )
        for field in fields:
            with self.subTest(field=field):
                pattern = re.compile(field["pattern"])
                self.assertGreaterEqual(field["minLength"], 1)
                self.assertIsNone(pattern.search("   \t"))
                self.assertIsNotNone(pattern.search("population"))
