#!/usr/bin/env python3
"""Contract tests for the shared oracle-grounded record envelope."""

import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "pipelines"))

import oracle_contract as oc  # noqa: E402

SCHEMA_PATH = REPO / "schemas" / "oracle-grounded-record.schema.json"


def minimal_record(**overrides):
    record = oc.build_record(
        record_id="rec-1",
        family="neuromorphic-fault-recovery",
        generator=oc.new_generator("gen", version="1.0.0", seed=3),
        scenario={"mission": "bounded fixture"},
        intervention={"kind": "sensor_loss", "parameters": {"channels": ["c0"]}},
        candidate_prediction={"predicted_outcome": "fallback", "confidence": 0.5},
        oracle=oc.new_oracle(
            "sim",
            oracle_type="deterministic_simulator",
            implementation="pipelines/fault_recovery.py:RelayReflexSimulator",
            version="1.0.0",
        ),
        result=oc.new_result(
            measurements=[
                oc.new_measurement("recovery_latency_ms", 4.0, "simulator_clock")
            ],
            outcome="fallback",
            reason_codes=["FALLBACK_SOURCE_ENGAGED"],
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
            oc.new_generator("g", version="1", kind="llm")

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
    def test_producer_may_not_claim_passed(self):
        record = minimal_record()
        record["validation"] = {"status": "passed", "validator": None, "findings": []}
        errors = oc.check_envelope(record, "x")
        self.assertTrue(any("validator must be an object" in error for error in errors))

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
    def test_unvalidated_record_is_not_eligible(self):
        eligible, reasons = oc.curation_eligible(minimal_record())
        self.assertFalse(eligible)
        self.assertTrue(any(reason.startswith("NOT_VALIDATED") for reason in reasons))

    def test_reference_only_oracle_is_never_eligible(self):
        record = minimal_record()
        record["oracle"]["authority"] = oc.AUTHORITY_REFERENCE_ONLY
        stamped = oc.stamp_validation(record, validator="v", version="1", findings=[])
        eligible, reasons = oc.curation_eligible(stamped)
        self.assertFalse(eligible)
        self.assertIn("ORACLE_NOT_AUTHORITATIVE:'reference_only'", reasons)

    def test_abstained_result_is_never_eligible(self):
        record = minimal_record()
        record["result"] = oc.new_result(
            status=oc.RESULT_ABSTAINED,
            measurements=[],
            abstention_reason="no meter",
        )
        stamped = oc.stamp_validation(record, validator="v", version="1", findings=[])
        eligible, reasons = oc.curation_eligible(stamped)
        self.assertFalse(eligible)
        self.assertTrue(
            any(reason.startswith("ORACLE_RESULT_NOT_MEASURED") for reason in reasons)
        )

    def test_validated_authoritative_measured_record_is_eligible(self):
        stamped = oc.stamp_validation(
            minimal_record(), validator="v", version="1", findings=[]
        )
        self.assertEqual(oc.curation_eligible(stamped), (True, []))


class JsonlHelpers(unittest.TestCase):
    def test_write_refuses_to_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "out.jsonl"
            oc.write_jsonl(path, [minimal_record()])
            with self.assertRaises(oc.ContractError):
                oc.write_jsonl(path, [minimal_record()])

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


if __name__ == "__main__":
    unittest.main()
