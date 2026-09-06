#!/usr/bin/env python3
"""Tests for the distillation record contract built on the shared oracle envelope."""

import copy
import importlib
import json
import sys
import tempfile
import unittest
from unittest import mock
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "pipelines"))

from oracle_grounded import distill_contract as oc  # noqa: E402
from oracle_grounded import envelope  # noqa: E402

SCHEMA_PATH = REPO / "schemas" / "oracle-grounded-record.schema.json"


def minimal_record(**overrides):
    record = oc.build_record(
        identity=oc.RecordIdentity("rec-1", "neuromorphic-fault-recovery"),
        proposal=oc.Proposal(
            generator=oc.new_generator(oc.GeneratorIdentity("gen", version="1.0.0"), seed=3),
            scenario={"mission": "bounded fixture"},
            intervention={"kind": "sensor_loss", "parameters": {"channels": ["c0"]}},
            candidate_prediction={"predicted_outcome": "fallback", "confidence": 0.5},
        ),
        verdict=oc.Verdict(
            oracle=oc.new_oracle(
                oc.OracleIdentity(
                    "sim",
                    oracle_type="deterministic_simulator",
                    implementation="pipelines/fault_recovery.py:RelayReflexSimulator",
                    version="1.0.0",
                )
            ),
            result=oc.new_result(
                measurements=[
                    oc.new_measurement("recovery_latency_ms", 4.0, "simulator_clock")
                ],
                outcome="fallback",
                reason_codes=["FALLBACK_SOURCE_ENGAGED"],
            ),
        ),
        provenance=oc.new_provenance("unit-test"),
    )
    record.update(copy.deepcopy(overrides))
    return record


class EnvelopeShape(unittest.TestCase):
    def test_minimal_record_is_valid_and_digest_matches(self):
        record = minimal_record()
        self.assertEqual(oc.check_envelope(record, "x"), [])
        self.assertEqual(oc.check_digest(record, "x"), [])

    def test_unknown_family_is_rejected(self):
        record = minimal_record(family="not-a-family")
        self.assertTrue(
            any("family must be one of" in error for error in oc.check_envelope(record, "x"))
        )

    def test_schema_version_is_pinned(self):
        record = minimal_record(schema_version="oracle-grounded/0.9.0")
        self.assertTrue(
            any("schema_version must be" in error for error in oc.check_envelope(record, "x"))
        )

    def test_digest_detects_hand_editing(self):
        record = minimal_record()
        record["result"]["outcome"] = "continue"
        self.assertTrue(oc.check_digest(record, "x"))

    def test_digest_survives_a_validation_stamp(self):
        record = minimal_record()
        stamped = oc.stamp_validation(record, validator="v", version="1", findings=[])
        self.assertEqual(oc.check_digest(stamped, "x"), [])
        self.assertEqual(oc.record_digest(record), oc.record_digest(stamped))


class GeneratorNeverCertifies(unittest.TestCase):
    def test_generator_authority_is_pinned(self):
        record = minimal_record()
        record["generator"]["authority"] = "authoritative"
        errors = oc.check_envelope(record, "x")
        self.assertTrue(any("propose_only" in error for error in errors))

    def test_new_generator_refuses_an_unnamed_llm(self):
        with self.assertRaises(oc.ContractError):
            oc.new_generator(oc.GeneratorIdentity("g", version="1", kind="llm"))

    def test_oracle_key_inside_scenario_is_a_violation(self):
        record = minimal_record()
        record["scenario"]["measurements"] = [{"quantity": "energy_j"}]
        errors = oc.check_generator_oracle_separation(record, "x")
        self.assertTrue(
            any("ORACLE_FIELD_IN_GENERATOR_NAMESPACE" in error for error in errors)
        )

    def test_oracle_key_nested_deep_in_intervention_is_a_violation(self):
        record = minimal_record()
        record["intervention"]["parameters"]["expected"] = {"outcome": "quarantine"}
        errors = oc.check_generator_oracle_separation(record, "x")
        self.assertTrue(
            any("intervention.parameters.expected.outcome" in error for error in errors)
        )

    def test_prediction_keys_must_be_namespaced(self):
        record = minimal_record()
        record["candidate_prediction"]["expected_latency_ms"] = 3.0
        errors = oc.check_generator_oracle_separation(record, "x")
        self.assertTrue(any("predicted_*" in error for error in errors))

    def test_prediction_free_keys_are_allowed(self):
        record = minimal_record()
        record["candidate_prediction"]["rationale"] = "kind lookup"
        record["candidate_prediction"]["method"] = "lookup"
        self.assertEqual(oc.check_generator_oracle_separation(record, "x"), [])


class MeasurementContract(unittest.TestCase):
    def test_unknown_quantity_is_refused_at_build_time(self):
        with self.assertRaises(oc.ContractError):
            oc.new_measurement("vibes", 1.0, "simulator_state")

    def test_unit_must_match_the_registry(self):
        with self.assertRaises(oc.ContractError):
            oc.new_measurement("latency_ms", 1.0, "clock", unit="s")

    def test_non_finite_value_is_refused(self):
        with self.assertRaises(oc.ContractError):
            oc.new_measurement("latency_ms", float("inf"), "clock")

    def test_energy_requires_a_measured_energy_meter(self):
        with self.assertRaises(oc.ContractError):
            oc.new_measurement("energy_j", 8.0, "analytic_op_count")
        with self.assertRaises(oc.ContractError):
            oc.new_measurement("energy_j", 8.0, "intel_rapl_powercap", measured=False)
        reading = oc.new_measurement("energy_j", 8.0, "intel_rapl_powercap")
        self.assertEqual(reading["unit"], "J")

    def test_a_modelled_meter_never_claims_a_measured_reading(self):
        # `measured` follows the meter registry for every quantity, not only
        # energy: a modelled meter with measured: true used to satisfy the
        # curation gate's NO_MEASURED_READING check on the producer's say-so.
        reading = oc.new_measurement("latency_ms", 3.5, "analytic_op_count")
        self.assertFalse(reading["measured"])
        with self.assertRaises(oc.ContractError):
            oc.new_measurement("latency_ms", 3.5, "analytic_op_count", measured=True)
        self.assertTrue(oc.new_measurement("latency_ms", 3.5, "simulator_clock")["measured"])
        lowered = oc.new_measurement("latency_ms", 3.5, "simulator_clock", measured=False)
        self.assertFalse(lowered["measured"])

    def test_a_modelled_meter_claiming_measured_is_a_finding_that_blocks_curation(self):
        record = minimal_record()
        reading = oc.new_measurement("recovery_latency_ms", 4.0, "analytic_op_count")
        reading["measured"] = True  # the tamper: a model's output relabelled
        record["result"]["measurements"] = [reading]
        record["provenance"]["record_sha256"] = oc.record_digest(record)
        errors = oc.check_measurements(record, "x")
        self.assertTrue(any("MODELLED_METER_CLAIMS_MEASURED" in error for error in errors))
        eligible, _reasons = oc.curation_eligible(record, errors)
        self.assertFalse(eligible)
        # Honestly labelled, the same reading is structurally valid but still
        # not a measured result, so curation refuses it for that reason.
        reading["measured"] = False
        record["provenance"]["record_sha256"] = oc.record_digest(record)
        self.assertEqual(oc.check_measurements(record, "x"), [])
        eligible, reasons = oc.curation_eligible(record, [])
        self.assertFalse(eligible)
        self.assertIn("NO_MEASURED_READING", reasons)

    def test_measurements_must_declare_an_oracle_source(self):
        record = minimal_record()
        record["result"]["measurements"][0]["source"] = "generator"
        errors = oc.check_measurements(record, "x")
        self.assertTrue(any("source must be 'oracle'" in error for error in errors))


class NoTheoreticalEnergy(unittest.TestCase):
    def test_modelled_energy_measurement_is_rejected(self):
        record = minimal_record()
        record["result"]["measurements"].append(
            {
                "quantity": "energy_j",
                "value": 0.0000023,
                "unit": "J",
                "meter": "synops_model",
                "measured": True,
                "source": "oracle",
            }
        )
        errors = oc.check_no_theoretical_energy_claim(record, "x")
        self.assertTrue(any("THEORETICAL_ENERGY_CLAIM" in error for error in errors))

    def test_spike_count_energy_estimate_is_rejected(self):
        record = minimal_record()
        record["result"]["measurements"].append(
            {
                "quantity": "energy_j",
                "value": 0.001,
                "unit": "J",
                "meter": "spike_energy_model",
                "measured": True,
                "source": "oracle",
            }
        )
        self.assertTrue(oc.check_no_theoretical_energy_claim(record, "x"))

    def test_energy_denominated_preference_needs_measured_energy(self):
        record = minimal_record()
        record["result"]["preference"] = {
            "preferred": "a",
            "cost_quantity": "energy_j",
        }
        errors = oc.check_no_theoretical_energy_claim(record, "x")
        self.assertTrue(
            any("preference" in error and "THEORETICAL" in error for error in errors)
        )

    def test_measured_energy_backs_an_energy_preference(self):
        record = minimal_record()
        record["result"]["measurements"].append(
            oc.new_measurement("energy_j", 8.0, "intel_rapl_powercap")
        )
        record["result"]["preference"] = {
            "preferred": "a",
            "cost_quantity": "energy_j",
        }
        self.assertEqual(oc.check_no_theoretical_energy_claim(record, "x"), [])


def measured_energy_reading(value: float = 8.0) -> dict:
    return oc.new_measurement("energy_j", value, "intel_rapl_powercap")


class EnergyClaimScan(unittest.TestCase):
    """D3: energy numbers are legal only in explicitly supported structures."""

    def claims(self, record) -> list:
        return [
            e for e in oc.check_no_theoretical_energy_claim(record, "x")
            if "THEORETICAL_ENERGY_CLAIM" in e
        ]

    def test_the_energy_tokens_derive_from_the_registry(self):
        self.assertEqual(oc.ENERGY_UNITS, frozenset({"J", "W", "Wh"}))
        for token in ("j", "pj", "uj", "mw", "kwh", "energy", "joules", "watt"):
            self.assertIn(token, oc.ENERGY_TOKENS)
        for token in ("while", "when", "kops", "wall", "power"):
            self.assertNotIn(token, oc.ENERGY_TOKENS)

    def test_lists_under_energy_keys_are_claims(self):
        record = minimal_record()
        record["result"]["energy_j_samples"] = [1e-7, 2e-7]
        record["result"]["joules"] = [1e-7]
        claims = self.claims(record)
        self.assertEqual(len(claims), 1, claims)
        for path in ("result.energy_j_samples[0]", "result.energy_j_samples[1]", "result.joules[0]"):
            self.assertIn(path, claims[0])

    def test_a_nested_object_identified_by_its_unit_is_a_claim(self):
        record = minimal_record()
        record["result"]["derived"] = {"energy": {"value": 1e-7, "unit": "J"}}
        claims = self.claims(record)
        self.assertEqual(len(claims), 1, claims)
        self.assertIn("result.derived.energy (no measured energy_j/energy_per_op_j reading", claims[0])

    def test_a_relocated_measurement_object_needs_backing_and_a_measuring_meter(self):
        relocated = {"quantity": "energy_j", "value": 1e-7, "meter": "synops_model", "measured": False}
        record = minimal_record()
        record["result"]["modelled_energy"] = relocated
        self.assertIn("result.modelled_energy (modelled meter 'synops_model')", self.claims(record)[0])
        # Backed by a measured reading and naming the measuring meter: legal.
        record["result"]["measurements"].append(measured_energy_reading())
        record["result"]["modelled_energy"] = {
            "quantity": "energy_j", "value": 8.0, "meter": "intel_rapl_powercap", "measured": True,
        }
        self.assertEqual(self.claims(record), [])
        # Backing never launders a modelled meter or a declared-unmeasured value.
        record["result"]["modelled_energy"]["meter"] = "synops_model"
        self.assertIn("modelled meter", self.claims(record)[0])
        record["result"]["modelled_energy"] = {"quantity": "energy_j", "value": 8.0, "measured": False}
        self.assertIn("declared unmeasured", self.claims(record)[0])

    def test_unit_suffixed_keys_are_claims(self):
        record = minimal_record()
        record["result"].update(
            {"power_mw": 12.5, "pj_per_synop": 23.6, "uj_total": 1.2, "cost_j": 3e-9}
        )
        record["result"]["candidates"] = [{"id": "a", "est_pj": 23.6}]
        claims = self.claims(record)
        self.assertEqual(len(claims), 1, claims)
        for path in (
            "result.power_mw", "result.pj_per_synop", "result.uj_total", "result.cost_j",
            "result.candidates[0].est_pj",
        ):
            self.assertIn(path, claims[0])

    def test_false_positives_and_metadata_stay_legal(self):
        record = minimal_record()
        record["result"].update(
            {"ticks_while_degraded": 4, "quality_when_degraded": 0.9, "throughput_kops": 12}
        )
        record["result"]["meter_probe"] = {
            "cost_is_energy": True,
            "cost_quantity": "energy_j",
            "selected": "intel_rapl_powercap",
            "probed": [
                {"meter": "intel_rapl_powercap", "available": False,
                 "measures_energy": True, "detail": "/sys/class/powercap absent"},
            ],
        }
        self.assertEqual(self.claims(record), [])

    def test_relabelling_the_result_as_energy_needs_a_measured_reading(self):
        # ENERGY-METER-IDENTITY (b): result.cost_quantity flipped to energy_j
        # beside numeric content, with no measured energy reading behind it.
        record = minimal_record()
        record["result"].update({"cost_quantity": "energy_j", "reference_objective": 0.218})
        self.assertIn("result (no measured energy_j reading backs it)", self.claims(record)[0])
        record["result"]["measurements"].append(measured_energy_reading())
        self.assertEqual(self.claims(record), [])

    def test_preference_is_governed_by_the_backing_rule_once(self):
        record = minimal_record()
        record["result"]["preference"] = {
            "cost_quantity": "energy_j", "cost_value": 2.8e-6, "quality_floor": 0.98,
            "preferred": "analytic_kkt",
        }
        claims = self.claims(record)
        self.assertEqual(len(claims), 1, claims)
        self.assertIn("result.preference: THEORETICAL_ENERGY_CLAIM", claims[0])
        record["result"]["measurements"].append(measured_energy_reading())
        self.assertEqual(self.claims(record), [])

    def test_candidate_cost_objects_need_backing(self):
        candidate = {
            "id": "analytic_kkt", "cost_quantity": "energy_j", "cost_value": 1e-6,
            "cost_meter": "intel_rapl_powercap", "task_quality": 1.0, "safety_ok": True,
        }
        record = minimal_record()
        record["result"]["candidates"] = [candidate]
        self.assertIn("result.candidates[0] (no measured energy_j reading", self.claims(record)[0])
        record["result"]["candidates"] = {"analytic_kkt": dict(candidate)}
        self.assertIn("result.candidates.analytic_kkt (no measured", self.claims(record)[0])
        record["result"]["measurements"].append(measured_energy_reading())
        self.assertEqual(self.claims(record), [])

    def test_measurement_entries_stay_with_the_measurement_rule(self):
        record = minimal_record()
        record["result"]["measurements"].append(
            {"quantity": "energy_j", "value": 2.3e-6, "unit": "J", "meter": "synops_model",
             "measured": True, "source": "oracle"}
        )
        claims = self.claims(record)
        self.assertEqual(len(claims), 1, claims)  # reported once, by the measurement rule
        self.assertIn("result.measurements[1]", claims[0])
        record["result"]["measurements"][1] = measured_energy_reading()
        self.assertEqual(self.claims(record), [])

    def test_detail_of_a_measured_energy_reading_is_not_a_claim(self):
        record = minimal_record()
        record["result"]["measurements"].append(
            oc.new_measurement(
                "energy_j", 8.0, "intel_rapl_powercap",
                detail={"raw_counter_uj": 1000000, "samples_uj": [1.0, 2.0]},
            )
        )
        self.assertEqual(self.claims(record), [])

    def test_the_hit_cap_bounds_collected_findings_and_the_walk_is_flat(self):
        # The cap bounds how many findings are collected, not the work of
        # visiting the record or the length of a path; the listing stays
        # short here because each path is short.
        record = minimal_record()
        record["result"]["junk"] = [{"unit": "J", "value": index} for index in range(10_000)]
        claims = self.claims(record)
        self.assertEqual(len(claims), 1, claims)
        self.assertIn("scan capped", claims[0])
        self.assertLess(len(claims[0]), 4_000)
        deep: dict = {}
        cursor = deep
        for _ in range(5_000):
            cursor["k"] = {}
            cursor = cursor["k"]
        cursor["energy_j"] = 1e-7
        record = minimal_record()
        record["result"]["deep"] = deep
        self.assertEqual(len(self.claims(record)), 1)


class EnergyIdentityAcrossContainers(unittest.TestCase):
    """Energy identity survives containers, checked through the public contract API.

    An object that identifies energy through its own fields, or a container
    under an energy-identifying key, is a claim whenever any number sits
    beneath it, however many lists or dicts deep. Cases A to D are the
    owner's reproducers on 766f06fe, where only A was reported.
    """

    CASES = {
        "A object with a numeric value": {"quantity": "energy_j", "unit": "J", "value": 5.0},
        "B object whose value is a list": {"quantity": "energy_j", "unit": "J", "value": [5.0]},
        "C object whose value is a dict": {
            "quantity": "energy_j", "unit": "J", "value": {"sample": 5.0},
        },
        "D energy-keyed container": {"energy_j": {"value": 5.0}},
        "E object whose value is a nested list": {
            "quantity": "energy_j", "unit": "J", "value": [[5.0]],
        },
        "F energy-keyed list of objects": {"energy_j": [{"sample": 5.0}]},
    }
    IDENTIFIED_OBJECTS = (
        "A object with a numeric value",
        "B object whose value is a list",
        "C object whose value is a dict",
        "E object whose value is a nested list",
    )
    ENERGY_KEYED = ("D energy-keyed container", "F energy-keyed list of objects")

    def findings(self, extra, backed: bool = False) -> list:
        record = minimal_record()
        if backed:
            record["result"]["measurements"].append(measured_energy_reading())
        record["result"]["extra"] = extra
        return [
            e for e in oc.check_no_theoretical_energy_claim(record, "x")
            if "THEORETICAL_ENERGY_CLAIM" in e
        ]

    def test_unbacked_energy_identity_is_a_claim_through_any_container(self):
        for name, extra in self.CASES.items():
            with self.subTest(case=name):
                findings = self.findings(extra)
                self.assertEqual(len(findings), 1, findings)
                self.assertIn("result.extra", findings[0])

    def test_backing_makes_identified_objects_legal_but_not_bare_energy_keys(self):
        for name in self.IDENTIFIED_OBJECTS:
            with self.subTest(case=name):
                self.assertEqual(self.findings(self.CASES[name], backed=True), [])
        # A container under a bare energy key names no meter and no quantity
        # of its own, so no reading can back it (R2 has no backing exemption).
        for name in self.ENERGY_KEYED:
            with self.subTest(case=name):
                self.assertEqual(len(self.findings(self.CASES[name], backed=True)), 1)

    def test_nonnumeric_metadata_under_an_energy_identity_is_not_a_claim(self):
        for extra in (
            {"quantity": "energy_j", "unit": "J", "note": "planned", "tags": ["draft"]},
            {"energy_j": {"unit": "J", "meter": "intel_rapl_powercap", "available": False}},
            {"quantity": "energy_j", "unit": "J", "value": {"note": "none", "flags": [True]}},
        ):
            with self.subTest(extra=extra):
                self.assertEqual(self.findings(extra), [])


class ResultFailsClosed(unittest.TestCase):
    def test_measured_result_needs_a_measurement(self):
        with self.assertRaises(oc.ContractError):
            oc.new_result(measurements=[])

    def test_abstained_result_needs_a_reason(self):
        with self.assertRaises(oc.ContractError):
            oc.new_result(status=oc.RESULT_ABSTAINED, measurements=[])

    def test_empty_measured_result_is_reported_as_missing(self):
        record = minimal_record()
        record["result"]["measurements"] = []
        errors = oc.check_envelope(record, "x")
        self.assertTrue(any("ORACLE_RESULT_MISSING" in error for error in errors))

    def test_abstained_result_is_structurally_valid(self):
        record = minimal_record()
        record["result"] = oc.new_result(
            status=oc.RESULT_ABSTAINED,
            measurements=[],
            abstention_reason="meter unavailable",
        )
        record["provenance"]["record_sha256"] = oc.record_digest(record)
        self.assertEqual(oc.check_envelope(record, "x"), [])


class ValidationIsNotSelfCertified(unittest.TestCase):
    def test_a_passed_status_with_no_validator_is_rejected(self):
        record = minimal_record()
        record["validation"] = {"status": "passed", "validator": None, "findings": []}
        errors = oc.check_envelope(record, "x")
        self.assertTrue(any("validator must be an object" in error for error in errors))

    def test_a_self_named_validator_is_structurally_valid_but_not_trusted(self):
        # check_envelope cannot tell who wrote a validation block — nothing on
        # disk can. The defence is that curation_eligible ignores it entirely,
        # which CurationFailsClosed asserts.
        record = minimal_record()
        record["validation"] = {
            "status": "passed",
            "validator": {
                "name": "the-producer-itself",
                "version": "1.0.0",
                "checked_at": oc.utc_now_iso(),
            },
            "findings": [],
        }
        self.assertEqual(oc.check_envelope(record, "x"), [])
        self.assertFalse(oc.stamp_is_bound_to_content(record))
        eligible, _ = oc.curation_eligible(record, ["found a problem"])
        self.assertFalse(eligible)

    def test_unvalidated_record_may_not_name_a_validator(self):
        record = minimal_record()
        record["validation"] = {
            "status": "unvalidated",
            "validator": {"name": "me", "version": "1"},
            "findings": [],
        }
        errors = oc.check_envelope(record, "x")
        self.assertTrue(
            any("must not name a validator" in error for error in errors)
        )

    def test_stamp_records_findings_as_failed(self):
        record = minimal_record()
        stamped = oc.stamp_validation(
            record, validator="validate_distill", version="1.0.0", findings=["boom"]
        )
        self.assertEqual(stamped["validation"]["status"], "failed")
        self.assertEqual(stamped["validation"]["findings"], ["boom"])
        self.assertEqual(oc.check_envelope(stamped, "x"), [])

    def test_stamp_does_not_mutate_the_input(self):
        record = minimal_record()
        oc.stamp_validation(record, validator="v", version="1", findings=[])
        self.assertEqual(record["validation"]["status"], "unvalidated")


class CurationFailsClosed(unittest.TestCase):
    def test_a_record_with_findings_is_not_eligible(self):
        eligible, reasons = oc.curation_eligible(minimal_record(), ["something wrong"])
        self.assertFalse(eligible)
        self.assertIn("VALIDATION_FINDINGS:1", reasons)

    def test_a_self_stamped_passed_verdict_does_not_make_a_record_eligible(self):
        # The whole point of the gate: a producer can write any validation
        # block it likes, so eligibility must come from the caller's own run.
        record = minimal_record()
        record["validation"] = {
            "status": oc.VALIDATION_PASSED,
            "validator": {
                "name": "the-producer-itself",
                "version": "1.0.0",
                "checked_at": oc.utc_now_iso(),
            },
            "findings": [],
        }
        eligible, reasons = oc.curation_eligible(record, ["a real finding"])
        self.assertFalse(eligible)
        self.assertIn("VALIDATION_FINDINGS:1", reasons)

    def test_reference_only_oracle_is_never_eligible(self):
        record = minimal_record()
        record["oracle"]["authority"] = oc.AUTHORITY_REFERENCE_ONLY
        record["provenance"]["record_sha256"] = oc.record_digest(record)
        eligible, reasons = oc.curation_eligible(record, [])
        self.assertFalse(eligible)
        self.assertIn("ORACLE_NOT_AUTHORITATIVE:'reference_only'", reasons)

    def test_abstained_result_is_never_eligible(self):
        record = minimal_record()
        record["result"] = oc.new_result(
            status=oc.RESULT_ABSTAINED,
            measurements=[],
            abstention_reason="no meter",
        )
        record["provenance"]["record_sha256"] = oc.record_digest(record)
        eligible, reasons = oc.curation_eligible(record, [])
        self.assertFalse(eligible)
        self.assertTrue(
            any(reason.startswith("ORACLE_RESULT_NOT_MEASURED") for reason in reasons)
        )

    def test_a_tampered_record_is_never_eligible(self):
        record = minimal_record()
        record["result"]["outcome"] = "continue"
        eligible, reasons = oc.curation_eligible(record, [])
        self.assertFalse(eligible)
        self.assertIn("RECORD_DIGEST_MISMATCH", reasons)

    def test_a_result_of_only_unmeasured_readings_is_not_eligible(self):
        # `measured: false` throughout is a modelled result wearing a measured
        # status. A non-empty measurements array is not enough.
        record = minimal_record()
        for item in record["result"]["measurements"]:
            item["measured"] = False
        record["provenance"]["record_sha256"] = oc.record_digest(record)
        eligible, reasons = oc.curation_eligible(record, [])
        self.assertFalse(eligible)
        self.assertIn("NO_MEASURED_READING", reasons)

    def test_a_record_with_no_digest_at_all_is_not_eligible(self):
        record = minimal_record()
        del record["provenance"]["record_sha256"]
        eligible, reasons = oc.curation_eligible(record, [])
        self.assertFalse(eligible)
        self.assertIn("RECORD_DIGEST_MISSING", reasons)

    def test_an_authoritative_measured_record_that_validated_clean_is_eligible(self):
        self.assertEqual(oc.curation_eligible(minimal_record(), []), (True, []))


class StampBinding(unittest.TestCase):
    def test_a_stamp_is_bound_to_the_content_it_was_formed_over(self):
        stamped = oc.stamp_validation(
            minimal_record(), validator="v", version="1", findings=[]
        )
        self.assertTrue(oc.stamp_is_bound_to_content(stamped))

    def test_a_stamp_lifted_onto_other_content_is_detected(self):
        stamped = oc.stamp_validation(
            minimal_record(), validator="v", version="1", findings=[]
        )
        other = minimal_record(id="rec-2")
        other["provenance"]["record_sha256"] = oc.record_digest(other)
        other["validation"] = stamped["validation"]
        self.assertFalse(oc.stamp_is_bound_to_content(other))

    def test_an_unstamped_record_is_not_bound(self):
        self.assertFalse(oc.stamp_is_bound_to_content(minimal_record()))


class JsonlHelpers(unittest.TestCase):
    def test_write_refuses_to_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "out.jsonl"
            oc.write_jsonl(path, [minimal_record()])
            with self.assertRaises(oc.ContractError):
                oc.write_jsonl(path, [minimal_record()])

    def test_a_non_finite_constant_is_a_parse_failure_not_a_value(self):
        # json.loads accepts bare NaN. Letting one through means the first
        # canonical re-serialisation raises and takes down the whole run.
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "nan.jsonl"
            path.write_text('{"id": "x", "value": NaN}\n{"id": "y"}\n')
            entries = oc.read_jsonl(path)
            self.assertEqual(len(entries), 2)
            self.assertIsNone(entries[0][1])
            self.assertEqual(entries[1][1], {"id": "y"})

    def test_infinity_is_also_a_parse_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "inf.jsonl"
            path.write_text('{"id": "x", "value": Infinity}\n')
            self.assertIsNone(oc.read_jsonl(path)[0][1])

    def test_round_trip_and_parse_failure_is_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "out.jsonl"
            oc.write_jsonl(path, [minimal_record()])
            with path.open("a", encoding="utf-8") as handle:
                handle.write("{not json\n")
            entries = oc.read_jsonl(path)
            self.assertEqual(len(entries), 2)
            self.assertIsInstance(entries[0][1], dict)
            self.assertIsNone(entries[1][1])


class JsonlDuplicateKeys(unittest.TestCase):
    """A duplicated object key is a per-line parse failure, never last-wins."""

    def read(self, payload: bytes) -> list:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "batch.jsonl"
            path.write_bytes(payload)
            return oc.read_jsonl(path)

    def test_a_duplicated_top_level_key_is_a_parse_failure(self):
        # json.loads keeps the last value silently, so a line carrying two
        # `result` objects used to validate, and be digested, as whichever
        # came last, while main's strict loaders reject the same bytes.
        self.assertEqual(self.read(b'{"a": 1, "a": 2}\n{"b": 3}\n'), [(1, None), (2, {"b": 3})])

    def test_a_duplicated_key_at_any_depth_is_a_parse_failure(self):
        payload = b'{"result": {"outcome": "fallback", "outcome": "fail_closed"}}\n'
        self.assertEqual(self.read(payload), [(1, None)])

    def test_the_reader_uses_the_shared_duplicate_key_rejector(self):
        # The hook is the repository's existing strict-parsing primitive
        # (export_contract, training_audit, load_strict_json), not a private
        # copy grown inside the reader.
        from oracle_grounded import distill_jsonl

        hook = distill_jsonl._reject_duplicate_object_keys
        self.assertEqual(hook.__name__, "reject_duplicate_object_keys")
        self.assertTrue(hook.__module__.endswith("tag_jsonutil"), hook.__module__)

    def test_the_parse_dialect_is_otherwise_unchanged(self):
        rows = self.read(b'{"x": 1.5, "n": 2, "s": "\xc3\xa9", "t": true}\n{"y": NaN}\n')
        self.assertEqual(rows[0], (1, {"x": 1.5, "n": 2, "s": "\u00e9", "t": True}))
        self.assertIsInstance(rows[0][1]["x"], float)
        self.assertEqual(rows[1], (2, None))


class JsonlPerLineBoundary(unittest.TestCase):
    """The reader fails per line, never per file, for a pathological line too."""

    def test_a_pathologically_nested_line_is_a_parse_failure_not_an_abort(self):
        # json.loads raises RecursionError on 200,000 '[', a RuntimeError,
        # so it escaped the reader's ValueError boundary and took the whole
        # file down instead of being reported as the one bad line it is.
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "batch.jsonl"
            path.write_bytes(b"[" * 200_000 + b"\n" + b'{"ok": 1}\n')
            self.assertEqual(oc.read_jsonl(path), [(1, None), (2, {"ok": 1})])


ENERGY_LABELS = frozenset(
    {"preferred", "feasible", "over", "cost_value", "decision_rule",
     "cheaper_but_constraint_violating"}
)
FAULT_LABELS = frozenset({"trace_summary", "max_staleness_ms", "saturated_ticks"})


class FamilyOracleLabels(unittest.TestCase):
    """D2: family-owned oracle-label declarations, never taken from the record."""

    FAULT = "neuromorphic-fault-recovery"
    ENERGY = "snn-energy-routing-preferences"

    def setUp(self):
        from oracle_grounded import distill_labels

        self.labels = distill_labels
        patcher = mock.patch.dict(distill_labels._POLICIES, {}, clear=True)
        patcher.start()
        self.addCleanup(patcher.stop)

    def leak_findings(self, errors):
        return [e for e in errors if oc.LABEL_IN_GENERATOR_NAMESPACE in e]

    def test_a_missing_family_policy_is_a_finding_not_a_skip(self):
        record = minimal_record()
        errors = oc.check_oracle_label_leak(record, "x")
        self.assertEqual(len(errors), 1, errors)
        self.assertIn(oc.POLICY_MISSING, errors[0])
        # Structural validation is unchanged by the missing policy, and the
        # finding still refuses curation through the caller's own findings.
        self.assertFalse(any(oc.POLICY_MISSING in e for e in oc.check_envelope(record, "x")))
        eligible, reasons = oc.curation_eligible(record, errors)
        self.assertFalse(eligible)
        self.assertIn("VALIDATION_FINDINGS:1", reasons)

    def test_declarations_are_trusted_code_never_record_content(self):
        record = minimal_record()
        record["scenario"]["trace_summary"] = {"ticks": 3}
        # A record cannot supply its own policy: neither an empty declaration
        # nor a wider one inside the record changes what is checked.
        record["oracle"]["label_keys"] = []
        record["scenario"]["oracle_label_keys"] = []
        record["oracle_label_policy"] = {"family": self.FAULT, "label_keys": []}
        self.assertIn(oc.POLICY_MISSING, oc.check_oracle_label_leak(record, "x")[0])
        oc.declare_oracle_labels(self.FAULT, FAULT_LABELS)
        errors = oc.check_oracle_label_leak(record, "x")
        self.assertEqual(len(self.leak_findings(errors)), 1, errors)
        self.assertIn("scenario.trace_summary", errors[0])

    def test_labels_are_refused_at_any_depth_in_dicts_and_lists(self):
        policy = oc.OracleLabelPolicy(self.ENERGY, ENERGY_LABELS)
        record = minimal_record(family=self.ENERGY)
        record["scenario"]["nested"] = {"deeper": {"preferred": "analytic_kkt"}}
        record["scenario"]["candidate_actions"] = [{"id": "a"}, {"id": "b", "preferred": True}]
        record["intervention"]["steps"] = [[{"cost_value": 2.81e-06}]]
        errors = oc.check_oracle_label_leak(record, "x", policy=policy)
        self.assertEqual(len(errors), 1, errors)
        for path in (
            "scenario.nested.deeper.preferred",
            "scenario.candidate_actions[1].preferred",
            "intervention.steps[0][0].cost_value",
        ):
            with self.subTest(path=path):
                self.assertIn(path, errors[0])

    def test_every_generator_owned_section_is_scanned(self):
        policy = oc.OracleLabelPolicy(self.FAULT, FAULT_LABELS)
        for section in oc.GENERATOR_SECTIONS:
            with self.subTest(section=section):
                record = minimal_record()
                record[section]["max_staleness_ms"] = 12.0
                errors = oc.check_oracle_label_leak(record, "x", policy=policy)
                self.assertEqual(len(errors), 1, errors)
                self.assertIn(f"{section}.max_staleness_ms", errors[0])
        clean = oc.check_oracle_label_leak(minimal_record(), "x", policy=policy)
        self.assertEqual(clean, [])

    def test_valid_prediction_fields_are_not_labels(self):
        # `outcome` is the fault oracle's verdict; `predicted_outcome` and
        # `confidence` are the generator's namespaced guess and stay legal.
        policy = oc.OracleLabelPolicy(self.FAULT, frozenset({"outcome", "reason_codes"}))
        record = minimal_record()
        record["candidate_prediction"] = {"predicted_outcome": "fallback", "confidence": 0.5}
        self.assertEqual(oc.check_oracle_label_leak(record, "x", policy=policy), [])
        record["candidate_prediction"]["outcome"] = "fallback"
        errors = oc.check_oracle_label_leak(record, "x", policy=policy)
        self.assertIn("candidate_prediction.outcome", errors[0])
        self.assertNotIn("predicted_outcome", errors[0])

    def test_an_explicit_policy_must_be_the_records_family(self):
        energy = oc.OracleLabelPolicy(self.ENERGY, ENERGY_LABELS)
        errors = oc.check_oracle_label_leak(minimal_record(), "x", policy=energy)
        self.assertEqual(len(errors), 1, errors)
        self.assertIn(oc.POLICY_MISMATCH, errors[0])

    def test_the_declaration_api_refuses_bad_declarations(self):
        with self.assertRaises(oc.ContractError):
            oc.declare_oracle_labels("no-such-family", {"x"})
        with self.assertRaises(oc.ContractError):
            oc.declare_oracle_labels(self.FAULT, ())
        with self.assertRaises(oc.ContractError):
            oc.declare_oracle_labels(self.FAULT, {"trace_summary", ""})
        first = oc.declare_oracle_labels(self.FAULT, FAULT_LABELS)
        self.assertEqual(oc.declare_oracle_labels(self.FAULT, sorted(FAULT_LABELS)), first)
        with self.assertRaises(oc.ContractError):
            oc.declare_oracle_labels(self.FAULT, FAULT_LABELS | {"outcome"})
        self.assertEqual(oc.declared_families(), (self.FAULT,))
        self.assertIs(oc.oracle_label_policy(self.FAULT), first)
        self.assertIsNone(oc.oracle_label_policy(self.ENERGY))
        self.assertIsNone(oc.oracle_label_policy(None))

    def test_the_review_reproducers_are_caught(self):
        # ORACLE-LABEL-LEAK-SCENARIO: the energy verdict copied into the
        # student-visible scenario, and the fault trace into the scenario.
        oc.declare_oracle_labels(self.ENERGY, ENERGY_LABELS)
        oc.declare_oracle_labels(self.FAULT, FAULT_LABELS)
        energy = minimal_record(family=self.ENERGY)
        energy["scenario"]["preferred"] = "analytic_kkt"
        energy["scenario"]["cost_value"] = 2.81e-06
        energy["scenario"]["decision_rule"] = "cheapest_feasible"
        energy["generator"]["preferred"] = "analytic_kkt"
        errors = oc.check_oracle_label_leak(energy, "x")
        self.assertEqual(len(errors), 1, errors)
        for path in ("scenario.preferred", "scenario.cost_value", "scenario.decision_rule",
                     "generator.preferred"):
            self.assertIn(path, errors[0])
        fault = minimal_record()
        fault["scenario"]["trace_summary"] = {"max_staleness_ms": 40}
        errors = oc.check_oracle_label_leak(fault, "x")
        self.assertIn("scenario.trace_summary", errors[0])
        self.assertIn("scenario.trace_summary.max_staleness_ms", errors[0])

    def test_the_scan_is_the_envelopes_bounded_walker(self):
        policy = oc.OracleLabelPolicy(self.FAULT, FAULT_LABELS)
        record = minimal_record()
        record["scenario"]["junk"] = [{"saturated_ticks": index} for index in range(10_000)]
        errors = oc.check_oracle_label_leak(record, "x", policy=policy)
        self.assertEqual(len(errors), 1, errors)
        self.assertIn("scan capped", errors[0])
        self.assertLess(len(errors[0]), 4_000)

    def test_structural_validation_stays_distinct_from_the_family_check(self):
        oc.declare_oracle_labels(self.FAULT, FAULT_LABELS)
        record = minimal_record()
        record["scenario"]["saturated_ticks"] = 4
        record["provenance"]["record_sha256"] = oc.record_digest(record)
        # The structural checks know nothing about the family's labels ...
        self.assertEqual(oc.check_envelope(record, "x"), [])
        # ... the family check refuses the leak, and curation only ever sees
        # it through the findings the composing validator hands over.
        leak = oc.check_oracle_label_leak(record, "x")
        self.assertEqual(len(self.leak_findings(leak)), 1, leak)
        self.assertTrue(oc.curation_eligible(record, [])[0])
        self.assertFalse(oc.curation_eligible(record, leak)[0])


class SchemaFileAgreesWithTheModule(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))

    def test_family_enum_matches(self):
        enum = self.schema["properties"]["family"]["enum"]
        self.assertEqual(sorted(enum), sorted(oc.FAMILIES))

    def test_schema_version_const_matches(self):
        self.assertEqual(
            self.schema["properties"]["schema_version"]["const"], oc.SCHEMA_VERSION
        )

    def test_oracle_type_enum_matches(self):
        enum = self.schema["$defs"]["oracle"]["properties"]["type"]["enum"]
        self.assertEqual(set(enum), set(oc.ORACLE_TYPES))

    def test_generator_authority_const_matches(self):
        const = self.schema["$defs"]["generator"]["properties"]["authority"]["const"]
        self.assertEqual(const, oc.GENERATOR_AUTHORITY)

    def test_oracle_authority_enum_matches(self):
        enum = self.schema["$defs"]["oracle"]["properties"]["authority"]["enum"]
        self.assertEqual(set(enum), set(oc.ORACLE_AUTHORITIES))


class BuiltOnTheSharedEnvelope(unittest.TestCase):
    """The domain-neutral primitives are the envelope's own objects (#172)."""

    MOVED = (
        "GENERATOR_SECTIONS",
        "SHA256_RE",
        "ISO_8601_RE",
        "ContractError",
        "OracleUnavailable",
        "canonical_json",
        "utc_now_iso",
        "is_number",
        "is_enum_value",
        "record_digest",
    )

    def test_the_moved_primitives_are_the_envelopes_objects(self):
        for name in self.MOVED:
            with self.subTest(name=name):
                self.assertIs(getattr(oc, name), getattr(envelope, name))

    def test_the_reserved_key_scan_is_the_envelopes_bounded_walker(self):
        record = minimal_record()
        record["scenario"]["junk"] = [{"outcome": index} for index in range(10_000)]
        errors = oc.check_generator_oracle_separation(record, "x")
        reserved = [e for e in errors if "ORACLE_FIELD_IN_GENERATOR_NAMESPACE" in e]
        self.assertEqual(len(reserved), 1, errors)
        self.assertLess(len(reserved[0]), 4_000, len(reserved[0]))
        self.assertIn("scan capped", reserved[0])

    def test_the_prediction_naming_rule_runs_after_the_shared_scan(self):
        record = minimal_record()
        record["scenario"]["outcome"] = "leaked"
        record["candidate_prediction"]["expected_latency_ms"] = 3.0
        errors = oc.check_generator_oracle_separation(record, "x")
        shared = envelope.check_generator_oracle_separation(record, oc.ORACLE_ONLY_KEYS, "x")
        self.assertEqual(errors[: len(shared)], shared)
        self.assertEqual(len(errors), len(shared) + 1, errors)
        self.assertIn("predicted_*", errors[-1])

    def test_read_jsonl_uses_the_envelopes_parse_hooks(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "overflow.jsonl"
            path.write_text('{"id": "x", "value": 1e999}\n{"id": "y", "value": 0.5}\n')
            entries = oc.read_jsonl(path)
            self.assertIsNone(entries[0][1])
            self.assertEqual(entries[1][1], {"id": "y", "value": 0.5})

    def test_both_import_forms_are_one_module_object(self):
        if str(REPO) not in sys.path:
            sys.path.append(str(REPO))
        module = importlib.import_module("pipelines.oracle_grounded.distill_contract")
        self.assertIs(module, oc)
        self.assertIs(module.ContractError, envelope.ContractError)


class SplitByResponsibility(unittest.TestCase):
    """The contract is a facade over sibling modules that bind both import forms."""

    SIBLINGS = (
        "import_twins",
        "distill_vocabulary",
        "distill_builders",
        "distill_measurements",
        "distill_blocks",
        "distill_curation",
        "distill_jsonl",
        "distill_labels",
    )

    def test_every_sibling_binds_both_import_forms_to_one_module_object(self):
        if str(REPO) not in sys.path:
            sys.path.append(str(REPO))
        for name in self.SIBLINGS:
            with self.subTest(name=name):
                direct = importlib.import_module(f"oracle_grounded.{name}")
                packaged = importlib.import_module(f"pipelines.oracle_grounded.{name}")
                self.assertIs(direct, packaged)

    def test_the_facade_exports_every_declared_name(self):
        for name in oc.__all__:
            with self.subTest(name=name):
                self.assertTrue(hasattr(oc, name), name)

    def test_the_facade_names_are_the_siblings_objects(self):
        from oracle_grounded import distill_builders, distill_vocabulary

        self.assertIs(oc.build_record, distill_builders.build_record)
        self.assertIs(oc.FAMILIES, distill_vocabulary.FAMILIES)
        self.assertIs(oc.ContractError, envelope.ContractError)

    def test_an_unknown_measurement_option_is_refused(self):
        with self.assertRaises(TypeError):
            oc.new_measurement("latency_ms", 1.0, "clock", bogus=True)


if __name__ == "__main__":
    unittest.main()
