#!/usr/bin/env python3
"""Raster, gate-SNN, and schema-parity tests for Bridge curation."""

from __future__ import annotations

import copy
import hashlib
import json
import re
import unittest

try:
    from tests.test_curate_bridge import (
        RASTER_SCHEMA,
        bridge,
        curate_bridge,
        decide,
        event,
        gate_snn_fixture,
    )
except ModuleNotFoundError:
    from test_curate_bridge import (  # type: ignore[no-redef]
        RASTER_SCHEMA,
        bridge,
        curate_bridge,
        decide,
        event,
        gate_snn_fixture,
    )


class RasterAndGateSnnCuration(unittest.TestCase):
    """The sidecar contract SNN distillation depends on.

    ``curate_bridge`` owns the spike arithmetic (20-50 ms window,
    ``spikes = round(neurons * rate * window_s)``, 23 pJ/spike) for every
    consumer, so these tests pin the reason codes and the shared summary the
    training audit and the distillation probe read.
    """

    def test_reference_record_curates_clean_with_full_raster_evidence(self):
        decision = decide(gate_snn_fixture())
        self.assertEqual(decision.action, "retain")
        evidence = decision.manifest["evidence"]["raster"]
        self.assertTrue(evidence["raster_spike_budget_valid"])
        self.assertTrue(evidence["raster_energy_pJ_valid"])
        self.assertTrue(evidence["raster_energy_uJ_valid"])
        self.assertEqual(evidence["raster_routing_table_entries"], 2)
        self.assertTrue(evidence["raster_third_factor_valid"])
        self.assertEqual(evidence["raster_third_factor_tau_e_s"], 2.0)
        self.assertTrue(evidence["gate_snn_valid"])
        self.assertEqual(evidence["gate_snn_total_neurons"], 128)

    def test_excerpt_uses_microseconds_and_the_declared_window_bound(self):
        record = gate_snn_fixture()
        record["raster"]["excerpt"][-1]["t_us"] = 40_000
        self.assertTrue(curate_bridge.raster_status(record)["raster_valid"])

        record["raster"]["excerpt"][-1]["t_us"] = 40_001
        status = curate_bridge.raster_status(record)
        self.assertFalse(status["raster_valid"])
        self.assertIn(curate_bridge.REASON_RASTER_EXCERPT, status["reason_codes"])

    def test_fractional_window_accepts_its_exact_integer_microsecond_endpoint(self):
        record = gate_snn_fixture()
        record["raster"].update(
            {
                "window_ms": 32.001,
                "window_s": 0.032001,
                "spikes": 98,
                "energy_pJ": 2254,
                "energy_uJ": 0.002254,
            }
        )
        record["raster"]["excerpt"][-1]["t_us"] = 32_001

        self.assertTrue(curate_bridge.raster_status(record)["raster_valid"])

        record["raster"]["excerpt"][-1]["t_us"] = 32_002
        status = curate_bridge.raster_status(record)
        self.assertFalse(status["raster_valid"])
        self.assertIn(curate_bridge.REASON_RASTER_EXCERPT, status["reason_codes"])

    def test_raster_window_schema_bounds_are_exact_in_both_units(self):
        for window_ms, window_s in (
            (50.0000000005, 0.0500000000005),
            (50, 0.0500000000005),
            (19.9999999995, 0.0199999999995),
        ):
            with self.subTest(window_ms=window_ms, window_s=window_s):
                record = gate_snn_fixture()
                record["raster"]["window_ms"] = window_ms
                record["raster"]["window_s"] = window_s

                status = curate_bridge.raster_status(record)

                self.assertFalse(status["raster_valid"])
                self.assertFalse(status["evidence"]["raster_window_valid"])
                self.assertIn(
                    curate_bridge.REASON_RASTER_WINDOW,
                    status["reason_codes"],
                )

    def test_integral_json_number_timestamp_matches_schema_integer_semantics(self):
        record = gate_snn_fixture()
        record["raster"]["excerpt"][0]["t_us"] = 800.0
        record["raster"]["excerpt"][0]["neuron_id"] = 7.0

        self.assertTrue(curate_bridge.raster_status(record)["raster_valid"])

        record = gate_snn_fixture()
        record["raster"]["excerpt"][0]["t_us"] = 800.4
        status = curate_bridge.raster_status(record)
        self.assertFalse(status["raster_valid"])
        self.assertIn(curate_bridge.REASON_RASTER_EXCERPT, status["reason_codes"])

    def test_every_schema_integer_budget_field_accepts_integral_json_numbers(self):
        record = gate_snn_fixture()
        record["raster"]["neurons"] = json.loads("2.56e2")
        record["raster"]["spikes"] = 123.0
        for population in record["gate_snn"]["populations"]:
            population["neurons"] = float(population["neurons"])
            population["spikes"] = float(population["spikes"])
        record["gate_compute"] = {
            "per_check": [
                {
                    "neurons": 2.0,
                    "mean_rate_hz": 10.0,
                    "window_s": 0.05,
                    "spikes": 1.0,
                }
            ],
            "total_energy_pJ": 23,
        }

        status = curate_bridge.raster_status(record)

        self.assertTrue(status["raster_valid"], status["reason_codes"])
        self.assertEqual(status["spikes"], 123)
        self.assertIsInstance(status["spikes"], int)
        self.assertEqual(status["evidence"]["gate_snn_total_neurons"], 128)
        self.assertIsInstance(status["evidence"]["gate_snn_total_neurons"], int)
        self.assertEqual(status["evidence"]["gate_compute_total_spikes"], 1)
        self.assertIsInstance(status["evidence"]["gate_compute_total_spikes"], int)

    def test_millisecond_only_raster_event_is_not_a_canonical_excerpt(self):
        record = gate_snn_fixture()
        record["raster"]["excerpt"][0] = {"t_ms": 0.8, "neuron_id": 7}

        status = curate_bridge.raster_status(record)

        self.assertFalse(status["raster_valid"])
        self.assertIn(curate_bridge.REASON_RASTER_EXCERPT, status["reason_codes"])

    def test_declared_excerpt_channel_must_be_a_string(self):
        for channel in (None, 3, False, {}):
            with self.subTest(channel=channel):
                record = gate_snn_fixture()
                record["raster"]["excerpt"][0]["channel"] = channel

                status = curate_bridge.raster_status(record)

                self.assertFalse(status["raster_valid"])
                self.assertIn(curate_bridge.REASON_RASTER_EXCERPT, status["reason_codes"])

        record = gate_snn_fixture()
        record["raster"]["excerpt"][0]["channel"] = ""
        self.assertTrue(curate_bridge.raster_status(record)["raster_valid"])

    def test_missing_raster_quarantines_only_when_required(self):
        record = bridge([event(1.0, "a"), event(2.0, "b")])
        self.assertEqual(decide(record).action, "retain")

        raw = json.dumps(record, ensure_ascii=False).encode("utf-8")
        strict = curate_bridge.curate_record(
            record,
            source_path="bridge/batch-r02.jsonl",
            source_line=1,
            source_hash=hashlib.sha256(raw).hexdigest(),
            require_raster=True,
        )
        self.assertEqual(strict.action, "quarantine")
        self.assertIn(curate_bridge.REASON_RASTER_MISSING, strict.manifest["reason_codes"])

    def test_spike_product_mismatch_is_quarantined(self):
        record = gate_snn_fixture()
        record["raster"]["spikes"] = 500
        decision = decide(record)
        self.assertEqual(decision.action, "quarantine")
        self.assertIn(curate_bridge.REASON_RASTER_SPIKE_BUDGET, decision.manifest["reason_codes"])

    def test_malformed_third_factor_routing_is_quarantined(self):
        for third_factor in (
            {"modulator": "dopamine"},
            {"modulator": "dopamine", "tau_e_s": 2.0},
            {"modulator": "", "tau_e_s": 2.0, "eligibility": "pre_post_stdp"},
            {"modulator": "dopamine", "tau_e_s": 0, "eligibility": "pre_post_stdp"},
            {"modulator": "dopamine", "tau_e_s": 2.0, "eligibility": ""},
            "dopamine",
        ):
            with self.subTest(third_factor=third_factor):
                record = gate_snn_fixture()
                record["raster"]["routing"]["third_factor"] = third_factor
                decision = decide(record)
                self.assertEqual(decision.action, "quarantine")
                self.assertIn(
                    curate_bridge.REASON_THIRD_FACTOR_INVALID,
                    decision.manifest["reason_codes"],
                )

    def test_missing_third_factor_routing_is_quarantined(self):
        record = gate_snn_fixture()
        del record["raster"]["routing"]["third_factor"]

        decision = decide(record)

        self.assertEqual(decision.action, "quarantine")
        self.assertIn(
            curate_bridge.REASON_THIRD_FACTOR_INVALID,
            decision.manifest["reason_codes"],
        )
        evidence = decision.manifest["evidence"]["raster"]
        self.assertFalse(evidence["raster_third_factor_present"])

    def test_only_valid_routing_objects_count_toward_coverage(self):
        record = gate_snn_fixture()
        record["raster"]["routing"]["table"].extend(["not-a-route", {"from": "", "to": "gate"}])

        decision = decide(record)

        self.assertEqual(decision.action, "quarantine")
        self.assertIn(curate_bridge.REASON_RASTER_ROUTING, decision.manifest["reason_codes"])
        evidence = decision.manifest["evidence"]["raster"]
        self.assertEqual(evidence["raster_routing_table_declared_entries"], 4)
        self.assertEqual(evidence["raster_routing_table_entries"], 2)
        self.assertEqual(evidence["raster_routing_table_invalid_indices"], [2, 3])

    def test_tau_e_ms_alias_is_accepted(self):
        record = gate_snn_fixture()
        record["raster"]["routing"]["third_factor"] = {
            "modulator": "dopamine",
            "tau_e_ms": 2000,
            "eligibility": "pre_post_stdp",
        }
        decision = decide(record)
        self.assertEqual(decision.action, "retain")
        evidence = decision.manifest["evidence"]["raster"]
        self.assertEqual(evidence["raster_third_factor_tau_e_s"], 2.0)

    def test_gate_snn_spec_defects_are_quarantined(self):
        broken = (
            {"decision_window_ms": 25, "populations": []},
            {
                "decision_window_ms": 25,
                "populations": [{"name": "g", "neurons": 0, "threshold": 1.0}],
            },
            {"decision_window_ms": 25, "populations": [{"name": "g", "neurons": 8}]},
            {"populations": [{"name": "g", "neurons": 8, "threshold": 1.0}]},
        )
        for spec in broken:
            with self.subTest(spec=spec):
                record = gate_snn_fixture()
                record["gate_snn"] = spec
                decision = decide(record)
                self.assertEqual(decision.action, "quarantine")
                self.assertIn(
                    curate_bridge.REASON_GATE_SNN_INVALID,
                    decision.manifest["reason_codes"],
                )

    def test_gate_snn_population_shape_stays_fail_closed(self):
        invalid_populations = (
            "not-an-object",
            {"name": "", "neurons": 8, "threshold": 1.0},
            {"name": "g", "neurons": None, "threshold": 1.0},
            {"name": "g", "neurons": True, "threshold": 1.0},
            {"name": "g", "neurons": 0, "threshold": 1.0},
            {"name": "g", "neurons": -1, "threshold": 1.0},
            {"name": "g", "neurons": 10**4097, "threshold": 1.0},
            {"name": "g", "neurons": 8},
            {"name": "g", "neurons": 8, "threshold": float("inf")},
        )
        for population in invalid_populations:
            with self.subTest(population=population):
                record = gate_snn_fixture()
                record["gate_snn"]["populations"][0] = population

                decision = decide(record)

                self.assertEqual(decision.action, "quarantine")
                self.assertIn(
                    curate_bridge.REASON_GATE_SNN_INVALID,
                    decision.manifest["reason_codes"],
                )
                self.assertEqual(
                    decision.manifest["evidence"]["raster"][
                        "gate_snn_invalid_population_indices"
                    ],
                    [0],
                )

        record = gate_snn_fixture()
        record["gate_snn"]["populations"][0]["neurons"] = 64.0
        self.assertEqual(decide(record).action, "retain")

    def test_gate_snn_population_spike_budget_is_enforced(self):
        record = gate_snn_fixture()
        record["gate_snn"]["populations"][0]["spikes"] = 999
        decision = decide(record)
        self.assertEqual(decision.action, "quarantine")
        self.assertIn(curate_bridge.REASON_RASTER_SPIKE_BUDGET, decision.manifest["reason_codes"])

    def test_gate_snn_window_aliases_must_agree(self):
        record = gate_snn_fixture()
        record["gate_snn"]["decision_window_s"] = 0.030

        decision = decide(record)

        self.assertEqual(decision.action, "quarantine")
        self.assertIn(curate_bridge.REASON_GATE_SNN_INVALID, decision.manifest["reason_codes"])
        evidence = decision.manifest["evidence"]["raster"]
        self.assertFalse(evidence["gate_snn_decision_window_consistent"])

    def test_declared_nonnumeric_raster_fields_are_quarantined(self):
        for field, value, reason in (
            ("window_s", "bogus", curate_bridge.REASON_RASTER_WINDOW),
            ("energy_uJ", "bogus", curate_bridge.REASON_RASTER_ENERGY),
            ("energy_pJ", "bogus", curate_bridge.REASON_RASTER_ENERGY),
        ):
            with self.subTest(field=field):
                record = gate_snn_fixture()
                record["raster"][field] = value
                decision = decide(record)
                self.assertEqual(decision.action, "quarantine")
                self.assertIn(reason, decision.manifest["reason_codes"])

    def test_overflowing_gate_spike_product_is_quarantined(self):
        record = gate_snn_fixture()
        record["gate_snn"]["decision_window_ms"] = 1e308
        record["gate_snn"]["decision_window_s"] = 1e308 / 1000.0
        record["gate_snn"]["populations"][0]["mean_rate_hz"] = 1e308
        record["gate_snn"]["populations"][0]["spikes"] = 1

        decision = decide(record)

        self.assertEqual(decision.action, "quarantine")
        self.assertIn(curate_bridge.REASON_GATE_SNN_INVALID, decision.manifest["reason_codes"])

    def test_gate_snn_population_budget_shape_rejects_nonpositive_values(self):
        mutations = (
            ("mean_rate_hz", 0),
            ("mean_rate_hz", -1),
            ("spikes", -1),
        )
        for key, value in mutations:
            with self.subTest(key=key, value=value):
                record = gate_snn_fixture()
                record["gate_snn"]["populations"][0][key] = value

                decision = decide(record)

                self.assertEqual(decision.action, "quarantine")
                self.assertIn(
                    curate_bridge.REASON_GATE_SNN_INVALID,
                    decision.manifest["reason_codes"],
                )

    def test_gate_snn_decision_is_required_and_matches_safety_decision(self):
        for decision in (None, "REJECT"):
            with self.subTest(decision=decision):
                record = gate_snn_fixture()
                if decision is None:
                    del record["gate_snn"]["decision"]
                else:
                    record["gate_snn"]["decision"] = decision

                result = decide(record)

                self.assertEqual(result.action, "quarantine")
                self.assertIn(
                    curate_bridge.REASON_GATE_SNN_INVALID,
                    result.manifest["reason_codes"],
                )
                evidence = result.manifest["evidence"]["raster"]
                self.assertFalse(evidence["gate_snn_decision_valid"])

    def test_bridge_gate_decision_ignores_a_conflicting_top_level_carrier(self):
        record = gate_snn_fixture()
        record["safety_decision"] = {"decision": "REJECT"}

        status = curate_bridge.raster_status(record)

        self.assertTrue(curate_bridge.is_bridge_record(record))
        self.assertFalse(curate_bridge.is_thalamic_record(record))
        self.assertTrue(status["raster_valid"], status["reason_codes"])
        self.assertEqual(status["evidence"]["gate_snn_expected_decision"], "ACCEPT")

    def test_thalamic_gate_decision_ignores_a_conflicting_nested_carrier(self):
        record = gate_snn_fixture()
        record.pop("spike_events")
        record["language_view"] = {"trajectory": {"safety_decision": {"decision": "ACCEPT"}}}
        record.update(
            {
                "state": {"sim_or_real": "designed"},
                "proposed_action": {"action": "noop"},
                "safety_decision": {"decision": "REJECT", "rationale": "blocked"},
                "executed_action": {"action": "noop"},
                "future_outcome": {"success": True},
                "reward_components": {"total": 1.0},
            }
        )
        record["gate_snn"]["decision"] = "REJECT"

        status = curate_bridge.raster_status(record)

        self.assertTrue(curate_bridge.is_thalamic_record(record))
        self.assertFalse(curate_bridge.is_bridge_record(record))
        self.assertTrue(status["raster_valid"], status["reason_codes"])
        self.assertEqual(status["evidence"]["gate_snn_expected_decision"], "REJECT")

    def test_gate_snn_is_found_under_every_supported_carrier(self):
        spec = gate_snn_fixture()["gate_snn"]
        carriers = {
            "gate_snn": lambda record: record,
            "meta.gate_snn": lambda record: record.setdefault("meta", {}),
            "language_view.trajectory.gate_snn": (
                lambda record: record["language_view"]["trajectory"]
            ),
            "language_view.trajectory.safety_decision.gate_snn": (
                lambda record: record["language_view"]["trajectory"]["safety_decision"]
            ),
        }
        for location, container in carriers.items():
            with self.subTest(location=location):
                record = gate_snn_fixture()
                del record["gate_snn"]
                container(record)["gate_snn"] = copy.deepcopy(spec)
                found_location, found = curate_bridge.gate_snn_sidecar(record)
                self.assertEqual(found_location, location)
                self.assertEqual(found, spec)

    def test_raster_status_summarizes_without_reading_prose(self):
        status = curate_bridge.raster_status(gate_snn_fixture())
        self.assertTrue(status["bridge_record"])
        self.assertTrue(status["raster_valid"])
        self.assertEqual(status["raster_location"], "raster")
        self.assertEqual(status["routing_table_entries"], 2)
        self.assertTrue(status["third_factor_present"])
        self.assertTrue(status["gate_snn_present"])
        self.assertTrue(status["gate_snn_valid"])
        self.assertEqual(status["spikes"], 123)
        self.assertEqual(status["reason_codes"], [])

    def test_raster_status_reports_a_non_bridge_record_as_out_of_scope(self):
        malformed = (
            {"id": "not-a-bridge"},
            {"spike_events": [], "language_view": "not-an-object"},
            {"spike_events": [], "language_view": {"trajectory": "not-an-object"}},
        )
        for record in malformed:
            with self.subTest(record=record):
                status = curate_bridge.raster_status(record)
                self.assertFalse(status["bridge_record"])
                self.assertFalse(status["raster_present"])
                self.assertEqual(status["reason_codes"], [])

    def test_raster_status_reports_missing_sidecars(self):
        status = curate_bridge.raster_status(bridge([event(1.0, "a")]))
        self.assertTrue(status["bridge_record"])
        self.assertFalse(status["raster_present"])
        self.assertFalse(status["gate_snn_present"])
        self.assertEqual(status["reason_codes"], [curate_bridge.REASON_RASTER_MISSING])


class RasterSchemaParity(unittest.TestCase):
    """Every runtime-supported sidecar carrier shares one schema definition."""

    def setUp(self):
        self.schema = json.loads(RASTER_SCHEMA.read_text(encoding="utf-8"))

    def test_excerpt_schema_uses_bounded_microsecond_timestamps(self):
        event = self.schema["$defs"]["raster"]["properties"]["excerpt"]["items"]
        self.assertEqual(event["required"], ["t_us", "neuron_id"])
        self.assertEqual(event["properties"]["t_us"]["type"], "integer")
        self.assertEqual(event["properties"]["t_us"]["minimum"], 0)
        self.assertEqual(event["properties"]["t_us"]["maximum"], 50_000)
        self.assertNotIn("t_ms", event["properties"])

    def test_nested_gate_snn_carriers_reference_the_canonical_definition(self):
        trajectory = self.schema["properties"]["language_view"]["properties"]["trajectory"][
            "properties"
        ]

        self.assertEqual(trajectory["gate_snn"], {"$ref": "#/$defs/gate_snn"})
        self.assertEqual(
            trajectory["safety_decision"]["properties"]["gate_snn"],
            {"$ref": "#/$defs/gate_snn"},
        )

    def test_nested_gate_compute_carriers_reference_the_canonical_definition(self):
        """Every carrier ``_gate_compute_sidecar`` accepts is schema-constrained.

        The nested carriers used to be unconstrained: ``additionalProperties``
        is enabled on the trajectory objects, so a malformed nested compute
        block passed the published schema and was only rejected later by the
        runtime publication validator.
        """

        ref = {"$ref": "#/$defs/gate_compute"}
        trajectory = self.schema["properties"]["language_view"]["properties"]["trajectory"][
            "properties"
        ]

        self.assertEqual(self.schema["properties"]["gate_compute"], ref)
        self.assertEqual(trajectory["gate_compute"], ref)
        self.assertEqual(trajectory["safety_decision"]["properties"]["gate_compute"], ref)
        self.assertIn("per_check", self.schema["$defs"]["gate_compute"]["properties"])

        # The definition must cover exactly the carriers the runtime resolves.
        for location in (
            "gate_compute",
            "language_view.trajectory.gate_compute",
            "language_view.trajectory.safety_decision.gate_compute",
        ):
            with self.subTest(location=location):
                record = gate_snn_fixture()
                record.pop("gate_compute", None)
                target = record
                for key in location.split(".")[:-1]:
                    target = target.setdefault(key, {})
                target["gate_compute"] = {"per_check": []}

                found, _value = curate_bridge._gate_compute_sidecar(record)

                self.assertEqual(found, location)
                node = self.schema["properties"]
                for key in location.split("."):
                    node = node[key]
                    node = node.get("properties", node)
                self.assertEqual(node, ref)

    def test_schema_requires_nonblank_routing_endpoints_like_the_validator(self):
        """A blank ``from``/``to`` must fail the schema, not just the runtime.

        ``_validate_raster`` rejects an entry whose endpoints are blank after
        trimming, so a producer that validated against this schema and then
        failed publication would have followed every documented instruction.
        """

        table_entry = self.schema["$defs"]["raster"]["properties"]["routing"]["properties"][
            "table"
        ]["items"]

        # minLength alone stops "" but not "   ", and the runtime trims before
        # it checks, so the endpoints carry the same \S pattern the gate
        # decision uses.  Checked through the schema's own keywords: this
        # suite runs on the standard library alone.
        for endpoint in ("from", "to"):
            for blank in ("", "   ", "\t\n"):
                with self.subTest(endpoint=endpoint, value=repr(blank)):
                    keywords = table_entry["properties"][endpoint]
                    record = gate_snn_fixture()
                    entry = {"from": "a", "to": "b"}
                    entry[endpoint] = blank
                    record["raster"]["routing"]["table"] = [entry]

                    status = curate_bridge.raster_status(record)

                    self.assertFalse(status["raster_valid"])
                    self.assertIn(curate_bridge.REASON_RASTER_ROUTING, status["reason_codes"])
                    self.assertTrue(
                        len(blank) < keywords["minLength"]
                        or re.compile(keywords["pattern"]).search(blank) is None,
                        "schema must reject what the runtime validator rejects",
                    )

        for endpoint in ("from", "to"):
            with self.subTest(endpoint=endpoint, value="accepted"):
                keywords = table_entry["properties"][endpoint]
                self.assertGreaterEqual(len("thalamus"), keywords["minLength"])
                self.assertIsNotNone(re.compile(keywords["pattern"]).search("thalamus"))

    def test_schema_pins_the_runtime_gate_and_routing_requirements(self):
        gate = self.schema["$defs"]["gate_snn"]
        raster = self.schema["$defs"]["raster"]
        routing = raster["properties"]["routing"]
        table_entry = routing["properties"]["table"]["items"]

        self.assertEqual(gate["required"], ["decision", "populations"])
        self.assertIn("third_factor", routing["required"])
        self.assertEqual(
            routing["properties"]["third_factor"]["required"],
            ["modulator", "eligibility"],
        )
        # ``weight`` joined the required set: the producer contract is a
        # {from, to, weight} triple and the runtime rejects an entry without
        # a finite weight.
        self.assertEqual(table_entry["required"], ["from", "to", "weight"])
        self.assertEqual(table_entry["properties"]["weight"]["type"], "number")
        population = gate["properties"]["populations"]["items"]
        self.assertTrue(population["allOf"])

    def test_schema_rejects_a_blank_gate_decision_like_the_validator_does(self):
        """The published schema is the producer contract; it must not be looser.

        ``_validate_gate_snn`` refuses a blank or whitespace-only decision, so
        a producer that validated against this schema and then failed
        publication would have followed every documented instruction.  Checked
        against the schema's own keywords rather than through a JSON Schema
        library: this suite runs on the standard library alone.
        """

        decision = self.schema["$defs"]["gate_snn"]["properties"]["decision"]
        self.assertEqual(decision["type"], "string")
        self.assertGreaterEqual(decision["minLength"], 1)
        # JSON Schema "pattern" is an unanchored search, like re.search.
        pattern = re.compile(decision["pattern"])
        gate = {
            "decision_window_ms": 10,
            "populations": [{"name": "p", "neurons": 4, "threshold": 0.5}],
        }

        for blank in ("", "   ", "\t\n"):
            with self.subTest(decision=repr(blank)):
                reason_codes: list[str] = []
                curate_bridge._validate_gate_snn(
                    {**gate, "decision": blank},
                    reason_codes=reason_codes,
                    evidence={},
                )
                self.assertIn(curate_bridge.REASON_GATE_SNN_INVALID, reason_codes)
                self.assertTrue(
                    len(blank) < decision["minLength"] or pattern.search(blank) is None,
                    "schema must reject what the runtime validator rejects",
                )

        accepted: list[str] = []
        curate_bridge._validate_gate_snn(
            {**gate, "decision": "ACCEPT"}, reason_codes=accepted, evidence={}
        )
        self.assertEqual(accepted, [])
        self.assertGreaterEqual(len("ACCEPT"), decision["minLength"])
        self.assertIsNotNone(pattern.search("ACCEPT"))
