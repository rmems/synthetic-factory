"""Validation gates for pipelines/hardware_parity.py.

Covers record validation, the re-simulation gate, determinism evidence, and
the rule that a malformed record is rejected rather than crashing.
"""

import copy
import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from hardware_parity_support import (  # noqa: E402
    WHERE,
    fixture_records as _fixture_records,
)

import hardware_parity as hp  # noqa: E402
import neuro_oracle as oracle  # noqa: E402
from oracle_grounded import parity_contract as contract  # noqa: E402

class Validation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Deterministic corpus; every test mutates a deep copy of a record.
        cls.records = hp.generate_records(round_number=1, steps=6, repeats=2)
        cls.mismatch = next(
            (record for record in cls.records
             if record["result"]["verdict"] == contract.VERDICT_MISMATCH),
            None,
        )

    def setUp(self):
        self.assertIsNotNone(self.mismatch, "generated parity fixtures must include a mismatch")

    def test_fixture_validates(self):
        self.assertEqual(hp.validate_records(_fixture_records()), [])

    def test_omitted_catalog_provenance_stamps_are_rejected(self):
        record = copy.deepcopy(_fixture_records()[0])
        for key in (
            "generator",
            "generator_version",
            "catalog_digest",
            "catalog_authorship",
        ):
            record["provenance"].pop(key, None)
        errors = hp.validate_record(record, WHERE)
        self.assertTrue(
            any("provenance identity" in error for error in errors),
            errors,
        )

    def test_falsified_catalog_digest_is_rejected(self):
        record = copy.deepcopy(_fixture_records()[0])
        record["provenance"]["catalog_digest"] = "sha256:" + ("0" * 64)
        errors = hp.validate_record(record, WHERE)
        self.assertTrue(
            any("provenance identity" in error for error in errors),
            errors,
        )

    def test_fixture_carries_both_verdicts(self):
        verdicts = {record["result"]["verdict"] for record in _fixture_records()}
        self.assertIn(contract.VERDICT_MATCH, verdicts)
        self.assertIn(contract.VERDICT_MISMATCH, verdicts)

    def test_a_mismatch_cannot_be_relabelled_as_a_match(self):
        record = copy.deepcopy(self.mismatch)
        record["result"]["verdict"] = contract.VERDICT_MATCH
        errors = hp.validate_record(record, WHERE)
        self.assertTrue(
            any("PARITY_VERDICT_INCONSISTENT" in error for error in errors), errors
        )

    def test_inflated_agreement_is_caught(self):
        record = copy.deepcopy(self.mismatch)
        record["result"]["parity"]["spike_bitmap"]["agreement"] = 1.0
        record["result"]["parity"]["spike_bitmap"]["hamming_distance"] = 0
        errors = hp.validate_record(record, WHERE)
        self.assertTrue(any("PARITY_METRIC_MISMATCH" in error for error in errors))

    def test_verdict_rule_is_bound_to_compute_parity(self):
        record = copy.deepcopy(self.records[0])
        record["result"]["parity"]["verdict_rule"] = "all records match"
        errors = hp.validate_record(record, WHERE)
        self.assertTrue(
            any(
                "verdict_rule" in error and "PARITY_METRIC_MISMATCH" in error
                for error in errors
            ),
            errors,
        )

    def test_edited_spike_trace_moves_the_verdict(self):
        record = copy.deepcopy(self.records[0])
        record["oracle"]["deployment"]["spikes"][0][0] ^= 1
        errors = hp.validate_record(record, WHERE)
        self.assertTrue(errors)

    def test_tampered_input_fixture_is_caught(self):
        record = copy.deepcopy(self.records[0])
        record["scenario"]["stimulus"]["events"][0][0] ^= 1
        errors = hp.validate_record(record, WHERE)
        self.assertTrue(any("INPUT_FIXTURE_MISMATCH" in error for error in errors))

    def test_oracle_fixture_must_match_the_complete_scenario_fixture(self):
        record = copy.deepcopy(self.records[0])
        record["oracle"]["input_fixture"]["channels"] += 1
        errors = hp.validate_record(record, WHERE)
        self.assertTrue(
            any(
                "oracle.input_fixture must exactly match" in error
                and "INPUT_FIXTURE_MISMATCH" in error
                for error in errors
            ),
            errors,
        )

    def test_falsified_quantization_provenance_is_caught(self):
        record = copy.deepcopy(self.records[0])
        record["oracle"]["deployment"]["quantization"]["parameters"][0]["q88_raw"] += 1
        errors = hp.validate_record(record, WHERE)
        self.assertTrue(any("Q88_PROVENANCE_MISMATCH" in error for error in errors))

    def test_every_quantization_provenance_field_is_bound_to_the_model(self):
        mutations = (
            lambda block: block.__setitem__("max_abs_error", 123.0),
            lambda block: block.__setitem__("mean_abs_error", 123.0),
            lambda block: block.__setitem__("source_model_sha256", "sha256:" + "0" * 64),
            lambda block: block["parameters"][0].__setitem__("float", 123.0),
            lambda block: block["parameters"][0].__setitem__("q88_value", 123.0),
            lambda block: block["parameters"][0].__setitem__("abs_error", 123.0),
        )
        for mutate in mutations:
            with self.subTest(mutation=mutate):
                record = copy.deepcopy(self.records[0])
                mutate(record["oracle"]["deployment"]["quantization"])
                errors = hp.validate_record(record, WHERE)
                self.assertTrue(
                    any("Q88_PROVENANCE_MISMATCH" in error for error in errors),
                    errors,
                )

    def test_missing_quantization_provenance_is_caught(self):
        record = copy.deepcopy(self.records[0])
        del record["oracle"]["deployment"]["quantization"]
        errors = hp.validate_record(record, WHERE)
        self.assertTrue(any("Q88_PROVENANCE_MISSING" in error for error in errors))

    def test_hidden_saturation_count_is_caught(self):
        saturated = next(
            (item for item in self.records
             if item["oracle"]["deployment"]["quantization"]["saturated_parameter_count"]),
            None,
        )
        self.assertIsNotNone(saturated, "generated parity fixtures must include saturated parameters")
        record = copy.deepcopy(saturated)
        record["oracle"]["deployment"]["quantization"]["saturated_parameter_count"] = 0
        errors = hp.validate_record(record, WHERE)
        self.assertTrue(any("Q88_PROVENANCE_MISMATCH" in error for error in errors))

    def test_generator_prediction_cannot_stand_in_for_parity(self):
        record = copy.deepcopy(self.records[0])
        record["candidate_prediction"]["parity"] = {"agreement": 1.0}
        errors = hp.validate_record(record, WHERE)
        self.assertTrue(
            any("GENERATOR_SUBSTITUTED_FOR_ORACLE" in error for error in errors)
        )

    def test_extra_reason_code_is_rejected(self):
        record = copy.deepcopy(self.records[0])
        record["result"]["reason_codes"].append("QUANTIZATION_SATURATION")
        errors = hp.validate_record(record, WHERE)
        self.assertTrue(any("PARITY_VERDICT_INCONSISTENT" in error for error in errors))

    def test_fabricated_summary_is_rejected(self):
        record = copy.deepcopy(self.records[0])
        record["result"]["summary"] = "the outputs matched perfectly"
        errors = hp.validate_record(record, WHERE)
        self.assertTrue(any("result.summary" in error for error in errors), errors)

    def test_provenance_digest_is_bound_to_model_and_stimulus(self):
        record = copy.deepcopy(self.records[0])
        record["provenance"]["scenario_sha256"] = "sha256:" + "0" * 64
        errors = hp.validate_record(record, WHERE)
        self.assertTrue(any("scenario_sha256" in error for error in errors), errors)

    def test_family_identity_and_validator_provenance_are_bound(self):
        mutations = (
            lambda record: record.__setitem__("id", "another-scenario-r01"),
            lambda record: record["meta"].__setitem__("factory", "another-factory"),
            lambda record: record["generator"].__setitem__("name", "another-generator"),
            lambda record: record["provenance"].__setitem__("tool", "another-tool"),
            lambda record: record["validation"].__setitem__(
                "validator", "another-validator"
            ),
        )
        for mutate in mutations:
            with self.subTest(mutation=mutate):
                record = copy.deepcopy(self.records[0])
                mutate(record)
                errors = hp.validate_record(record, WHERE)
                self.assertTrue(
                    any("ENVELOPE_MALFORMED" in error for error in errors), errors
                )

    def test_model_digest_is_bound_to_the_catalog_model(self):
        record = copy.deepcopy(self.records[0])
        record["scenario"]["model_sha256"] = "sha256:" + "0" * 64
        errors = hp.validate_record(record, WHERE)
        self.assertTrue(
            any("scenario.model_sha256" in error for error in errors), errors
        )

    def test_expected_verdict_is_bound_to_the_catalog_scenario(self):
        record = copy.deepcopy(self.records[0])
        record["candidate_prediction"]["expected_verdict"] = (
            contract.VERDICT_MISMATCH
        )
        errors = hp.validate_record(record, WHERE)
        self.assertTrue(
            any("candidate_prediction.expected_verdict" in error for error in errors),
            errors,
        )

    def test_stress_label_is_bound_to_catalog_scenario(self):
        record = copy.deepcopy(self.records[0])
        record["scenario"]["stress"] = "fabricated_stress"
        errors = hp.validate_record(record, WHERE)
        self.assertTrue(
            any("SCENARIO_LABEL_MISMATCH" in error for error in errors), errors
        )

    def test_prompt_facing_name_is_bound_to_catalog_scenario(self):
        record = copy.deepcopy(self.records[0])
        record["scenario"]["name"] = "fabricated scenario identity"
        errors = hp.validate_record(record, WHERE)
        self.assertTrue(
            any("scenario.name" in error and "SCENARIO_LABEL_MISMATCH" in error
                for error in errors),
            errors,
        )

    def test_stimulus_is_bound_to_catalog_scenario(self):
        record = copy.deepcopy(self.records[0])
        record["scenario"]["stimulus"]["events"][0][0] ^= 1
        stimulus = record["scenario"]["stimulus"]
        fixture_sha = oracle.stimulus_fixture(stimulus)["sha256"]
        record["scenario"]["input_fixture"]["sha256"] = fixture_sha
        record["oracle"]["input_fixture"]["sha256"] = fixture_sha
        errors = hp.validate_record(record, WHERE)
        self.assertTrue(
            any("scenario.stimulus" in error and "SCENARIO_LABEL_MISMATCH" in error
                for error in errors),
            errors,
        )

    def test_nonfinite_float_metric_is_rejected(self):
        record = copy.deepcopy(self.records[0])
        record["result"]["parity"]["spike_bitmap"]["agreement"] = float("nan")
        errors = hp.validate_record(record, WHERE)
        self.assertTrue(any("finite float" in error for error in errors), errors)

    def test_boolean_cannot_impersonate_an_integer_metric(self):
        record = copy.deepcopy(self.records[0])
        record["result"]["parity"]["spike_bitmap"]["hamming_distance"] = False
        errors = hp.validate_record(record, WHERE)
        self.assertTrue(any("PARITY_METRIC_MISMATCH" in error for error in errors), errors)

    def test_nested_boolean_cannot_impersonate_an_integer_metric(self):
        record = copy.deepcopy(self.records[0])
        counts = record["result"]["parity"]["action"]["deployment_counts"]
        index = next((i for i, value in enumerate(counts) if value == 1), None)
        self.assertIsNotNone(index, f"no unit action count to replace: {counts}")
        counts[index] = True
        errors = hp.validate_record(record, WHERE)
        self.assertTrue(any("PARITY_METRIC_MISMATCH" in error for error in errors), errors)

    def test_paired_record_requires_an_empty_unavailable_list(self):
        # A validated record must never simultaneously claim a completed
        # deployment and an unavailable oracle, and consumers rely on the
        # documented array shape.
        fabricated = [
            {
                "adapter": "spikenaut_fpga",
                "execution_target": "fpga_hardware",
                "reason_code": "NO_BOARD",
                "detail": "fabricated diagnostic on a paired record",
            }
        ]
        for value in (fabricated, "not-an-array", None):
            with self.subTest(value=value):
                record = copy.deepcopy(self.records[0])
                record["oracle"]["unavailable"] = value
                errors = hp.validate_record(record, WHERE)
                self.assertTrue(
                    any(
                        "oracle.unavailable" in error
                        and "ENVELOPE_MALFORMED" in error
                        for error in errors
                    ),
                    errors,
                )

    def test_oracle_pairing_is_bound_to_the_canonical_value(self):
        # `pairing` is execution-facing oracle metadata: free text here could
        # advertise an execution the checked adapter legs never ran.
        record = copy.deepcopy(self.records[0])
        record["oracle"]["pairing"] = "an FPGA physically executed this network"
        errors = hp.validate_record(record, WHERE)
        self.assertTrue(
            any(
                "oracle.pairing" in error and "ENVELOPE_MALFORMED" in error
                for error in errors
            ),
            errors,
        )


class ReSimulationGate(unittest.TestCase):
    """The traces themselves must be re-derivable, not merely self-consistent.

    Recomputing parity from a record's own traces is not enough on its own:
    copying one side's traces onto the other yields a perfectly self-consistent
    record asserting a match that never happened.
    """

    @classmethod
    def setUpClass(cls):
        # Deterministic corpus; every test mutates a deep copy of a record.
        cls.records = hp.generate_records(round_number=1, steps=6, repeats=2)
        cls.mismatch = next(
            (record for record in cls.records
             if record["result"]["verdict"] == contract.VERDICT_MISMATCH),
            None,
        )

    def setUp(self):
        self.assertIsNotNone(self.mismatch, "generated parity fixtures must include a mismatch")

    def _forge_match(self):
        """Copy the software traces onto the deployment side and recompute."""
        record = copy.deepcopy(self.mismatch)
        software = record["oracle"]["software"]
        deployment = record["oracle"]["deployment"]
        deployment["spikes"] = copy.deepcopy(software["spikes"])
        deployment["action"] = copy.deepcopy(software["action"])
        deployment["membrane"]["trace"] = copy.deepcopy(software["membrane"]["trace"])
        parity, verdict, codes = hp.compute_parity(
            record["scenario"], software, deployment
        )
        record["result"]["parity"] = parity
        record["result"]["verdict"] = verdict
        record["result"]["reason_codes"] = codes
        return record

    def test_a_self_consistent_forged_match_is_rejected(self):
        forged = self._forge_match()
        # The forgery really does look internally consistent...
        self.assertEqual(forged["result"]["verdict"], contract.VERDICT_MATCH)
        # ...and re-simulation still catches it.
        errors = hp.validate_record(forged, WHERE)
        self.assertTrue(any("re-simulation" in error for error in errors), errors)

    def test_forged_match_is_caught_through_the_deep_layer_too(self):
        import check_records

        errors, _warnings, _kind, _id = check_records.check_record(
            self._forge_match(), WHERE
        )
        self.assertTrue(any("re-simulation" in error for error in errors))

    def test_edited_software_trace_is_caught(self):
        record = copy.deepcopy(self.records[0])
        record["oracle"]["software"]["spikes"][0][0] ^= 1
        errors = hp.validate_record(record, WHERE)
        self.assertTrue(any("re-simulation" in error for error in errors))

    def test_edited_spike_events_are_caught(self):
        record = copy.deepcopy(self.records[0])
        record["oracle"]["deployment"]["spike_events"][0]["neuron_id"] += 1
        errors = hp.validate_record(record, WHERE)
        self.assertTrue(any("spike_events" in error for error in errors), errors)

    def test_edited_raw_q88_membrane_trace_is_caught(self):
        record = copy.deepcopy(self.records[0])
        record["oracle"]["deployment"]["membrane"]["trace_q88_raw"][0][0] += 1
        errors = hp.validate_record(record, WHERE)
        self.assertTrue(any("membrane" in error for error in errors), errors)

    def test_edited_arithmetic_observation_is_caught(self):
        record = copy.deepcopy(self.records[0])
        record["oracle"]["deployment"]["arithmetic"]["saturation_events"] += 1
        parity, verdict, codes = hp.compute_parity(
            record["scenario"],
            record["oracle"]["software"],
            record["oracle"]["deployment"],
        )
        record["result"]["parity"] = parity
        record["result"]["verdict"] = verdict
        record["result"]["reason_codes"] = codes
        errors = hp.validate_record(record, WHERE)
        self.assertTrue(any("arithmetic" in error for error in errors), errors)

    def test_boolean_cannot_impersonate_an_arithmetic_counter(self):
        record = copy.deepcopy(self.records[0])
        record["oracle"]["deployment"]["arithmetic"]["saturation_events"] = False
        parity, verdict, codes = hp.compute_parity(
            record["scenario"],
            record["oracle"]["software"],
            record["oracle"]["deployment"],
        )
        record["result"]["parity"] = parity
        record["result"]["verdict"] = verdict
        record["result"]["reason_codes"] = codes
        record["result"]["summary"] = hp._expected_summary(record)
        errors = hp.validate_record(record, WHERE)
        self.assertTrue(any("arithmetic" in error for error in errors), errors)

    def test_forged_output_digest_is_caught(self):
        record = copy.deepcopy(self.records[0])
        record["oracle"]["deployment"]["output_digest"] = "sha256:" + "0" * 64
        errors = hp.validate_record(record, WHERE)
        self.assertTrue(any("output_digest" in error for error in errors))

    def test_software_side_must_declare_the_float_target(self):
        record = copy.deepcopy(self.records[0])
        record["oracle"]["software"]["execution_target"] = oracle.TARGET_FPGA_HARDWARE
        errors = hp.validate_record(record, WHERE)
        self.assertTrue(any("HW_TARGET_UNKNOWN" in error for error in errors))

    def test_reference_identity_tuple_is_adapter_owned(self):
        mutations = (
            ("software", "adapter"),
            ("software", "runtime_class"),
            ("deployment", "adapter"),
            ("deployment", "runtime_class"),
        )
        for side, key in mutations:
            with self.subTest(side=side, key=key):
                record = copy.deepcopy(self.records[0])
                record["oracle"][side][key] = "forged_reference_identity"
                errors = hp.validate_record(record, WHERE)
                self.assertTrue(
                    any(
                        f"oracle.{side}.{key}" in error
                        and "HW_PROVENANCE_MISSING" in error
                        for error in errors
                    ),
                    errors,
                )

    def test_software_latency_is_rederived(self):
        record = copy.deepcopy(self.records[0])
        record["oracle"]["software"]["latency"]["detail"] = "forged latency"
        errors = hp.validate_record(record, WHERE)
        self.assertTrue(
            any("oracle.software.latency" in error for error in errors), errors
        )

    def test_reference_latency_is_rederived(self):
        record = copy.deepcopy(self.records[0])
        record["oracle"]["deployment"]["latency"]["modeled_steps"] += 1
        errors = hp.validate_record(record, WHERE)
        self.assertTrue(
            any("oracle.deployment.latency" in error for error in errors), errors
        )

    def test_membrane_shape_mismatch_still_carries_a_reason_code(self):
        # Deleting evidence must never be quieter than reporting it.
        metrics = hp.membrane_metrics(
            {"observable": True, "units": hp.MEMBRANE_UNITS, "trace": [[0.0], [0.0]]},
            {"observable": True, "units": hp.MEMBRANE_UNITS, "trace": [[0.0]]},
        )
        self.assertEqual(metrics["reason_code"], "MEMBRANE_DIVERGENCE")

    def test_truncated_membrane_trace_is_caught(self):
        record = copy.deepcopy(self.mismatch)
        del record["oracle"]["deployment"]["membrane"]["trace"][-1]
        errors = hp.validate_record(record, WHERE)
        self.assertTrue(errors)


if __name__ == "__main__":
    unittest.main()
