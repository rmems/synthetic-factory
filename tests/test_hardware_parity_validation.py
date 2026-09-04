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
    def setUp(self):
        self.records = hp.generate_records(round_number=1, steps=6, repeats=2)
        self.mismatch = next(
            record
            for record in self.records
            if record["result"]["verdict"] == contract.VERDICT_MISMATCH
        )

    def test_fixture_validates(self):
        self.assertEqual(hp.validate_records(_fixture_records()), [])

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
        record = copy.deepcopy(
            next(
                item
                for item in self.records
                if item["oracle"]["deployment"]["quantization"][
                    "saturated_parameter_count"
                ]
            )
        )
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
        fixture_sha = oracle.digest(stimulus["events"])
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

    def setUp(self):
        self.records = hp.generate_records(round_number=1, steps=6, repeats=2)
        self.mismatch = next(
            record
            for record in self.records
            if record["result"]["verdict"] == contract.VERDICT_MISMATCH
        )

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


class DeterminismEvidence(unittest.TestCase):
    """`determinism` is a claim; `repeat_digests` is the evidence for it."""

    def setUp(self):
        self.record = hp.generate_records(round_number=1, steps=4, repeats=3)[0]

    def test_generated_record_is_internally_consistent(self):
        self.assertEqual(hp.validate_record(copy.deepcopy(self.record), WHERE), [])

    def test_repeatability_claim_must_match_its_digests(self):
        record = copy.deepcopy(self.record)
        record["oracle"]["deployment"]["repeat_digests"] = [
            "sha256:aa",
            "sha256:bb",
            "sha256:cc",
        ]
        errors = hp.validate_record(record, WHERE)
        self.assertTrue(any("REPEATABILITY_UNPROVEN" in error for error in errors))

    def test_repeat_digests_reject_non_strings_without_crashing(self):
        for value in (7, {"digest": "sha256:" + "1" * 64}):
            with self.subTest(value=value):
                record = copy.deepcopy(self.record)
                record["oracle"]["deployment"]["repeat_digests"][1] = value
                errors = hp.validate_record(record, WHERE)
                self.assertTrue(
                    any("canonical lowercase" in error for error in errors), errors
                )

    def test_repeat_count_must_match_the_digest_count(self):
        record = copy.deepcopy(self.record)
        record["oracle"]["deployment"]["repeats"] = 500
        errors = hp.validate_record(record, WHERE)
        self.assertTrue(any("REPEATABILITY_UNPROVEN" in error for error in errors))

    def test_boolean_cannot_impersonate_the_distinct_digest_count(self):
        # Python treats True == 1, and an unpaired record has no result.parity
        # to catch the substitution through a second strict comparison, so the
        # determinism check itself must require an exact non-Boolean integer.
        scenario = hp.build_scenarios(steps=4)[0]
        adapter = oracle.FpgaHardwareAdapter(env={})
        software, deployment, unavailable = hp.run_pair(scenario, adapter, repeats=2)
        record = hp.build_record(
            scenario,
            software,
            deployment,
            unavailable,
            1,
            oracle.availability_report(env={})["spikenaut_fpga"],
        )
        self.assertEqual(hp.validate_record(copy.deepcopy(record), WHERE), [])
        record["oracle"]["software"]["determinism"]["distinct_digests"] = True
        errors = hp.validate_record(record, WHERE)
        self.assertTrue(
            any(
                "distinct_digests" in error and "REPEATABILITY_UNPROVEN" in error
                for error in errors
            ),
            errors,
        )

    def test_output_digest_must_appear_among_the_repeats(self):
        record = copy.deepcopy(self.record)
        record["oracle"]["software"]["repeat_digests"] = ["sha256:" + "1" * 64] * 3
        errors = hp.validate_record(record, WHERE)
        self.assertTrue(any("REPEATABILITY_UNPROVEN" in error for error in errors))

    def test_reference_repeat_digests_are_rederived(self):
        record = copy.deepcopy(self.record)
        software = record["oracle"]["software"]
        forged = "sha256:" + "1" * 64
        software["repeat_digests"] = [software["output_digest"], forged, forged]
        software["determinism"]["distinct_digests"] = 2
        software["determinism"]["identical_repeats"] = False
        parity, verdict, codes = hp.compute_parity(
            record["scenario"],
            software,
            record["oracle"]["deployment"],
        )
        record["result"]["parity"] = parity
        record["result"]["verdict"] = verdict
        record["result"]["reason_codes"] = codes
        record["result"]["summary"] = hp._expected_summary(record)
        errors = hp.validate_record(record, WHERE)
        self.assertTrue(
            any("must repeat the re-derived output_digest" in error for error in errors),
            errors,
        )

    def test_repeatability_block_is_recomputed(self):
        record = copy.deepcopy(self.record)
        record["result"]["parity"]["repeatability"]["hardware_repeatability_measured"] = (
            True
        )
        errors = hp.validate_record(record, WHERE)
        self.assertTrue(any("PARITY_METRIC_MISMATCH" in error for error in errors))

    def test_astronomically_large_repeats_does_not_attempt_the_allocation(self):
        # A record-declared `repeats` this large must not reach
        # `[output_digest] * repeats`; the mismatch with the actual digest
        # count (already reported) must be bound before that multiplication.
        record = copy.deepcopy(self.record)
        record["oracle"]["deployment"]["repeats"] = 10**9
        errors = hp.validate_record(record, WHERE)
        self.assertTrue(any("REPEATABILITY_UNPROVEN" in error for error in errors))

    def test_software_determinism_meaning_is_bound_to_the_reference_adapter(self):
        # oracle.software is always a reference adapter (never a physical
        # capture), so its determinism.meaning cannot claim measured
        # hardware variability.
        record = copy.deepcopy(self.record)
        record["oracle"]["software"]["determinism"]["meaning"] = (
            "run-to-run variability observed during the recorded capture"
        )
        errors = hp.validate_record(record, WHERE)
        self.assertTrue(any("REPEATABILITY_UNPROVEN" in error for error in errors), errors)

    def test_deployment_determinism_meaning_is_bound_to_its_adapter(self):
        # A fixed-point reference deployment is a deterministic simulator.
        # Relabeling its repeats as measured hardware variability -- and
        # mirroring that text into result.parity.repeatability so the
        # recomputed mirror agrees with the claim -- must not validate a
        # simulator's repeats as a physical measurement.
        record = copy.deepcopy(self.record)
        lie = "run-to-run variability measured on the physical board"
        record["oracle"]["deployment"]["determinism"]["meaning"] = lie
        record["result"]["parity"]["repeatability"]["meaning"] = lie
        errors = hp.validate_record(record, WHERE)
        self.assertTrue(
            any("oracle.deployment.determinism.meaning" in error for error in errors),
            errors,
        )


class MalformedRecordsDoNotCrash(unittest.TestCase):
    """A bad record must be reported, not raise and abort the whole scan."""

    def setUp(self):
        self.record = hp.generate_records(round_number=1, steps=4, repeats=2)[0]

    def _assert_reports(self, mutate):
        record = copy.deepcopy(self.record)
        mutate(record)
        try:
            errors = hp.validate_record(record, WHERE)
        except Exception as exc:  # noqa: BLE001 - the point is that none escape
            self.fail(f"validation raised {type(exc).__name__}: {exc}")
        self.assertTrue(errors)

    def test_non_dict_deployment(self):
        self._assert_reports(
            lambda record: record["oracle"].__setitem__("deployment", "tampered")
        )

    def test_truthy_non_dict_oracle(self):
        self._assert_reports(lambda record: record.__setitem__("oracle", ["x"]))

    def test_ragged_spike_grid(self):
        def mutate(record):
            record["oracle"]["deployment"]["spikes"][0] = [1]

        self._assert_reports(mutate)

    def test_stimulus_steps_wildly_disagreeing_with_events_is_rejected(self):
        # A record-declared `steps` this large must be bound to the actual
        # event grid before it can reach build_scenario() as an allocation
        # bound.
        def mutate(record):
            record["scenario"]["stimulus"]["steps"] = 10**9

        self._assert_reports(mutate)

    def test_non_dict_software(self):
        self._assert_reports(
            lambda record: record["oracle"].__setitem__("software", 7)
        )

    def test_missing_model(self):
        self._assert_reports(lambda record: record["scenario"].pop("model_float"))

    def test_invalid_model_scalar_type(self):
        self._assert_reports(
            lambda record: record["scenario"]["model_float"].__setitem__(
                "neurons", None
            )
        )

    def test_nonfinite_model_and_stimulus_are_reported_not_raised(self):
        mutations = (
            lambda record: record["scenario"]["model_float"].__setitem__(
                "neurons", float("inf")
            ),
            lambda record: record["scenario"]["stimulus"]["events"][0].__setitem__(
                0, float("nan")
            ),
            lambda record: record["scenario"]["stimulus"]["events"][0].__setitem__(
                0, float("inf")
            ),
            lambda record: record["scenario"]["stimulus"]["events"][0].__setitem__(
                0, float("-inf")
            ),
        )
        for mutate in mutations:
            with self.subTest(mutation=mutate):
                self._assert_reports(mutate)

    def test_excessive_nesting_is_record_local(self):
        malformed = copy.deepcopy(self.record)
        nested = []
        for _ in range(1500):
            nested = [nested]
        malformed["scenario"]["model_float"]["hostile_nesting"] = nested
        errors = hp.validate_records([malformed, copy.deepcopy(self.record)])
        self.assertTrue(any("record:1" in error for error in errors), errors)
        self.assertFalse(any("record:2" in error for error in errors), errors)

    def test_json_shaped_nested_type_errors_are_record_local(self):
        mutations = (
            lambda record: record["scenario"].__setitem__("input_fixture", True),
            lambda record: record["oracle"].__setitem__("input_fixture", 1),
            lambda record: record["oracle"]["deployment"].__setitem__(
                "quantization", True
            ),
            lambda record: record["result"].__setitem__("parity", {}),
        )
        for mutate in mutations:
            with self.subTest(mutation=mutate):
                self._assert_reports(mutate)


if __name__ == "__main__":
    unittest.main()
