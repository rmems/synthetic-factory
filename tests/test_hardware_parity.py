"""Tests for pipelines/hardware_parity.py."""

import copy
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PIPELINES = REPO / "pipelines"
FIXTURE = (
    REPO
    / "tests"
    / "fixtures"
    / "parity-run"
    / "hardware-parity-spike-trajectories"
    / "batch-r01.jsonl"
)
sys.path.insert(0, str(PIPELINES))

import hardware_parity as hp  # noqa: E402
import neuro_oracle as oracle  # noqa: E402
import oracle_contract as contract  # noqa: E402

WHERE = "unit:1"


def _fixture_records():
    return [
        json.loads(line)
        for line in FIXTURE.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _cli(args):
    return subprocess.run(
        [sys.executable, str(PIPELINES / "hardware_parity.py"), *args],
        capture_output=True,
        text=True,
    )


class ScenarioCatalog(unittest.TestCase):
    def test_scenario_ids_are_unique(self):
        ids = [scenario["id"] for scenario in hp.build_scenarios()]
        self.assertEqual(len(ids), len(set(ids)))

    def test_every_scenario_is_simulable(self):
        for scenario in hp.build_scenarios():
            with self.subTest(scenario=scenario["id"]):
                run = oracle.simulate_float(scenario["model_float"], scenario["stimulus"])
                self.assertEqual(len(run["spikes"]), scenario["stimulus"]["steps"])

    def test_input_fixture_digest_matches_the_event_grid(self):
        for scenario in hp.build_scenarios():
            with self.subTest(scenario=scenario["id"]):
                self.assertEqual(
                    scenario["input_fixture"]["sha256"],
                    oracle.digest(scenario["stimulus"]["events"]),
                )

    def test_the_control_scenario_actually_spikes(self):
        # A control that never fires would prove nothing about parity.
        scenario = next(
            item for item in hp.build_scenarios() if item["stress"] == "none"
        )
        run = oracle.simulate_float(scenario["model_float"], scenario["stimulus"])
        self.assertGreater(sum(sum(row) for row in run["spikes"]), 0)


class ParityMetrics(unittest.TestCase):
    def test_identical_bitmaps_agree_perfectly(self):
        grid = [[1, 0], [0, 1]]
        metrics = hp.spike_bitmap_metrics(grid, copy.deepcopy(grid))
        self.assertEqual(metrics["agreement"], 1.0)
        self.assertEqual(metrics["hamming_distance"], 0)
        self.assertEqual(metrics["jaccard"], 1.0)

    def test_missing_and_extra_spikes_are_counted_separately(self):
        software = [[1, 0], [0, 0]]
        hardware = [[0, 0], [0, 1]]
        metrics = hp.spike_bitmap_metrics(software, hardware)
        self.assertEqual(metrics["software_only_spikes"], 1)
        self.assertEqual(metrics["hardware_only_spikes"], 1)
        self.assertEqual(metrics["hamming_distance"], 2)
        self.assertEqual(metrics["jaccard"], 0.0)

    def test_shape_mismatch_is_not_comparable(self):
        metrics = hp.spike_bitmap_metrics([[1, 0]], [[1, 0], [0, 1]])
        self.assertFalse(metrics["comparable"])

    def test_timing_error_uses_first_spike(self):
        software = [[1, 0], [0, 0], [0, 1]]
        hardware = [[0, 0], [1, 0], [0, 1]]
        metrics = hp.timing_metrics(software, hardware, dt_ms=2.0)
        self.assertEqual(metrics["max_abs_step_error"], 1)
        self.assertEqual(metrics["max_abs_ms_error"], 2.0)
        self.assertEqual(metrics["compared_neurons"], 2)

    def test_timing_rejects_unequal_execution_windows(self):
        metrics = hp.timing_metrics(
            [[1, 0]],
            [[1, 0], [0, 0]],
            dt_ms=1.0,
        )
        self.assertFalse(metrics["comparable"])
        self.assertEqual(metrics["reason"], "spike grids have different shapes")

    def test_timing_counts_neurons_that_fire_on_one_side_only(self):
        metrics = hp.timing_metrics([[1, 1]], [[1, 0]], dt_ms=1.0)
        self.assertEqual(metrics["neurons_firing_software_only"], 1)
        self.assertEqual(metrics["neurons_firing_hardware_only"], 0)

    def test_membrane_within_tolerance(self):
        metrics = hp.membrane_metrics(
            {"observable": True, "units": hp.MEMBRANE_UNITS, "trace": [[0.0, 1.0]]},
            {"observable": True, "units": hp.MEMBRANE_UNITS, "trace": [[0.0, 1.0]]},
        )
        self.assertTrue(metrics["within_tolerance"])
        self.assertEqual(metrics["max_abs_error"], 0.0)

    def test_membrane_beyond_tolerance_is_flagged(self):
        metrics = hp.membrane_metrics(
            {"observable": True, "units": hp.MEMBRANE_UNITS, "trace": [[0.0]]},
            {"observable": True, "units": hp.MEMBRANE_UNITS, "trace": [[1.0]]},
        )
        self.assertFalse(metrics["within_tolerance"])

    def test_membrane_unit_mismatch_is_not_silently_compared(self):
        # A recorded capture is untrusted input and may label its trace with
        # another unit (or omit it); comparing raw numbers across units would
        # be numerically valid but dimensionally meaningless.
        metrics = hp.membrane_metrics(
            {"observable": True, "units": hp.MEMBRANE_UNITS, "trace": [[0.0]]},
            {"observable": True, "units": "volts", "trace": [[0.0]]},
        )
        self.assertEqual(metrics["reason_code"], "MEMBRANE_DIVERGENCE")
        self.assertFalse(metrics["observable"])
        metrics = hp.membrane_metrics(
            {"observable": True, "units": hp.MEMBRANE_UNITS, "trace": [[0.0]]},
            {"observable": True, "trace": [[0.0]]},  # units omitted entirely
        )
        self.assertEqual(metrics["reason_code"], "MEMBRANE_DIVERGENCE")
        self.assertFalse(metrics["observable"])

    def test_unobservable_membrane_carries_a_reason_code(self):
        metrics = hp.membrane_metrics(
            {"observable": True, "trace": [[0.0]]}, {"observable": False, "trace": None}
        )
        self.assertEqual(metrics["reason_code"], "MEMBRANE_DIVERGENCE")

    def test_runtime_saturation_is_reported_even_with_clean_parameters(self):
        metrics = hp.quantization_metrics(
            {
                "quantization": {"saturated_parameter_count": 0, "format": "Q8.8"},
                "arithmetic": {"saturation_events": 7},
            }
        )
        self.assertEqual(metrics["saturated_parameter_count"], 0)
        self.assertEqual(metrics["runtime_saturation_events"], 7)

    def test_reference_model_does_not_claim_hardware_repeatability(self):
        metrics = hp.repeatability_metrics(
            {"repeats": 3, "determinism": {"distinct_digests": 1}},
            {
                "repeats": 3,
                "determinism": {"distinct_digests": 1},
                "execution_target": oracle.TARGET_FIXED_POINT_MODEL,
            },
        )
        self.assertFalse(metrics["hardware_repeatability_measured"])

    def test_physical_target_does_claim_hardware_repeatability(self):
        metrics = hp.repeatability_metrics(
            {"repeats": 3, "determinism": {}},
            {"repeats": 3, "determinism": {}, "execution_target": oracle.TARGET_FPGA_HARDWARE},
        )
        self.assertTrue(metrics["hardware_repeatability_measured"])


class Generation(unittest.TestCase):
    def test_generated_records_validate(self):
        records = hp.generate_records(round_number=1, steps=6, repeats=2)
        self.assertEqual(hp.validate_records(records), [])

    def test_generation_is_deterministic(self):
        first = hp.generate_records(round_number=1, steps=6, repeats=2)
        second = hp.generate_records(round_number=1, steps=6, repeats=2)
        self.assertEqual(json.dumps(first, sort_keys=True),
                         json.dumps(second, sort_keys=True))

    def test_catalog_produces_both_matches_and_mismatches(self):
        # A parity corpus in which nothing ever disagrees is not testing parity.
        verdicts = {
            record["result"]["verdict"]
            for record in hp.generate_records(round_number=1, steps=12)
        }
        self.assertIn(contract.VERDICT_MATCH, verdicts)
        self.assertIn(contract.VERDICT_MISMATCH, verdicts)

    def test_every_record_declares_the_fpga_probe(self):
        for record in hp.generate_records(round_number=1, steps=4, repeats=2):
            probe = record["oracle"]["environment"]["fpga_hardware"]
            self.assertFalse(probe["available"])
            self.assertTrue(probe["reason_code"])

    def test_paired_reference_record_keeps_recorded_fpga_probe(self):
        record = copy.deepcopy(
            hp.generate_records(round_number=1, steps=4, repeats=2)[0]
        )
        probe = record["oracle"]["environment"]["fpga_hardware"]
        probe["detail"] = "stale availability assertion"
        probe["reason_code"] = "FPGA_DEVICE_ABSENT"
        self.assertEqual(hp.validate_record(record, WHERE), [])

    def test_malformed_fpga_environment_is_rejected(self):
        record = copy.deepcopy(
            hp.generate_records(round_number=1, steps=4, repeats=2)[0]
        )
        record["oracle"]["environment"]["fpga_hardware"] = []
        errors = hp.validate_record(record, WHERE)
        self.assertTrue(
            any("fpga_hardware must be an object" in error for error in errors),
            errors,
        )

    def test_live_fpga_deployment_requires_current_probe_available(self):
        record = copy.deepcopy(
            hp.generate_records(round_number=1, steps=4, repeats=2)[0]
        )
        record["oracle"]["deployment"]["adapter"] = oracle.FpgaHardwareAdapter.name
        record["oracle"]["deployment"]["runtime_class"] = (
            oracle.FpgaHardwareAdapter.runtime_class
        )
        record["oracle"]["deployment"]["execution_target"] = oracle.TARGET_FPGA_HARDWARE
        errors = hp.validate_record(record, WHERE)
        self.assertTrue(
            any("current adapter probe to report available" in error for error in errors),
            errors,
        )

    def test_unavailable_deployment_oracle_yields_inconclusive(self):
        scenario = hp.build_scenarios(steps=4)[0]
        adapter = oracle.FpgaHardwareAdapter(env={})
        software, deployment, unavailable = hp.run_pair(scenario, adapter, repeats=2)
        self.assertIsNone(deployment)
        self.assertEqual(unavailable["reason_code"], "FPGA_DEVICE_NOT_DECLARED")
        record = hp.build_record(
            scenario, software, deployment, unavailable, 1,
            oracle.availability_report(env={})["spikenaut_fpga"],
        )
        self.assertEqual(record["result"]["verdict"], contract.VERDICT_INCONCLUSIVE)
        self.assertIsNone(record["result"]["parity"])
        self.assertIn("ORACLE_UNAVAILABLE", record["result"]["reason_codes"])
        self.assertEqual(hp.validate_record(record, WHERE), [])

    def test_unavailable_diagnostic_is_a_required_lineage_item(self):
        scenario = hp.build_scenarios(steps=4)[0]
        adapter = oracle.FpgaHardwareAdapter(env={})
        software, deployment, unavailable = hp.run_pair(
            scenario, adapter, repeats=2
        )
        record = hp.build_record(
            scenario,
            software,
            deployment,
            unavailable,
            1,
            oracle.availability_report(env={})["spikenaut_fpga"],
        )
        expected = hp._unavailable_evidence_digest(
            record["oracle"]["unavailable"][0]
        )
        self.assertEqual(
            record["result"]["derived_from"],
            [record["oracle"]["software"]["output_digest"], expected],
        )
        self.assertEqual(
            hp.training_view(record)["evidence_digests"],
            record["result"]["derived_from"],
        )

        record["result"]["derived_from"].pop()
        errors = hp.validate_record(record, WHERE)
        self.assertTrue(
            any("RESULT_DIGEST_UNLINKED" in error for error in errors), errors
        )

    def test_unavailable_diagnostic_cannot_be_forged_and_resealed(self):
        scenario = hp.build_scenarios(steps=4)[0]
        adapter = oracle.FpgaHardwareAdapter(env={})
        software, deployment, unavailable = hp.run_pair(
            scenario, adapter, repeats=2
        )
        record = hp.build_record(
            scenario,
            software,
            deployment,
            unavailable,
            1,
            oracle.availability_report(env={})["spikenaut_fpga"],
        )
        diagnostic = record["oracle"]["unavailable"][0]
        diagnostic["detail"] = "fabricated unavailability evidence"
        record["result"]["derived_from"][1] = hp._unavailable_evidence_digest(
            diagnostic
        )
        record["result"]["summary"] = hp._expected_summary(record)

        errors = hp.validate_record(record, WHERE)
        self.assertTrue(
            any(
                "adapter 'spikenaut_fpga' reports" in error
                and "ORACLE_UNAVAILABLE" in error
                for error in errors
            ),
            errors,
        )

    def test_unpaired_record_still_reexecutes_the_software_leg(self):
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
        record["oracle"]["software"]["spikes"][0][0] ^= 1
        errors = hp.validate_record(record, WHERE)
        self.assertTrue(any("re-simulation" in error for error in errors), errors)

    def test_unavailable_deployment_diagnostic_matches_the_selected_adapter(self):
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
        with tempfile.TemporaryDirectory() as tmp:
            missing_capture = Path(tmp) / "fabricated-capture.json"
            capture_adapter = oracle.RecordedCaptureAdapter(missing_capture)
            probe = capture_adapter.availability()
            record["oracle"]["unavailable"][0] = {
                "adapter": capture_adapter.name,
                "adapter_config": {"capture_path": str(missing_capture)},
                "execution_target": capture_adapter.execution_target,
                "reason_code": probe["reason_code"],
                "detail": probe["detail"],
            }
            record["result"]["summary"] = hp._expected_summary(record)
            errors = hp.validate_record(record, WHERE)
            self.assertTrue(
                any("selected adapter" in error for error in errors), errors
            )


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
        index = next(i for i, value in enumerate(counts) if value == 1)
        counts[index] = True
        errors = hp.validate_record(record, WHERE)
        self.assertTrue(any("PARITY_METRIC_MISMATCH" in error for error in errors), errors)


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


class RecordedCapturePath(unittest.TestCase):
    """The `--capture` route must actually produce validatable records.

    It is also the one place where the deployment traces are *not*
    re-derivable, so these tests pin how that limitation is surfaced.
    """

    @unittest.skipUnless(hasattr(os, "mkfifo"), "FIFO test requires POSIX mkfifo")
    def test_capture_reader_rejects_fifo_without_blocking(self):
        with tempfile.TemporaryDirectory() as tmp:
            fifo = Path(tmp) / "capture.fifo"
            os.mkfifo(fifo)
            script = (
                "import json,sys;"
                f"sys.path.insert(0, {str(PIPELINES)!r});"
                "from neuro_oracle import RecordedCaptureAdapter;"
                f"print(json.dumps(RecordedCaptureAdapter({str(fifo)!r}).availability()))"
            )
            result = subprocess.run(
                [sys.executable, "-c", script],
                capture_output=True,
                text=True,
                timeout=3,
                check=False,
            )

        self.assertEqual(result.returncode, 0, result.stderr)
        status = json.loads(result.stdout)
        self.assertFalse(status["available"])
        self.assertEqual(status["reason_code"], "CAPTURE_UNREADABLE")
        self.assertIn("not a regular file", status["detail"])

    def test_capture_reader_does_not_follow_symlinks(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / "capture-target.json"
            target.write_text(
                json.dumps({"execution_target": oracle.TARGET_FPGA_HARDWARE}),
                encoding="utf-8",
            )
            link = root / "capture-link.json"
            link.symlink_to(target)
            status = oracle.RecordedCaptureAdapter(link).availability()

        self.assertFalse(status["available"])
        self.assertEqual(status["reason_code"], "CAPTURE_UNREADABLE")
        self.assertIn("not a regular file", status["detail"])

    def test_capture_reader_refuses_oversized_regular_files_before_parsing(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "capture.json"
            with path.open("wb") as handle:
                handle.truncate(oracle.MAX_CAPTURE_BYTES + 1)
            status = oracle.RecordedCaptureAdapter(path).availability()

        self.assertFalse(status["available"])
        self.assertEqual(status["reason_code"], "CAPTURE_UNREADABLE")
        self.assertIn("limit", status["detail"])

    def _capture_adapter(
        self,
        tmp,
        scenario,
        *,
        bitstream_sha256=None,
        truncate_spikes=False,
        narrow_spikes=False,
        invalid_spike_cell=None,
        narrow_membrane=False,
    ):
        software = oracle.simulate_float(
            scenario["model_float"], scenario["stimulus"]
        )
        _, quantization = oracle.quantize_model(scenario["model_float"])
        spikes = copy.deepcopy(software["spikes"])
        if truncate_spikes:
            spikes = spikes[:-1]
        if narrow_spikes:
            spikes = [row[:-1] for row in spikes]
        if invalid_spike_cell is not None:
            spikes[0][0] = invalid_spike_cell
        membrane = copy.deepcopy(software["membrane"])
        if narrow_membrane:
            membrane["trace"] = [row[:-1] for row in membrane["trace"]]
        payload = {
            "spikes": spikes,
            "spike_events": oracle._spike_events(
                spikes, scenario["model_float"]["dt_ms"]
            ),
            "action": oracle._decode_action(
                spikes, scenario["model_float"]["action_labels"]
            ),
            "membrane": membrane,
            "arithmetic": {"format": "Q8.8", "saturation_events": 0},
            "latency": {"measured": True, "value_ms": 0.31},
        }
        repeat_output = {
            key: copy.deepcopy(payload[key])
            for key in (
                "spikes",
                "spike_events",
                "action",
                "membrane",
                "arithmetic",
            )
        }
        payload["repeat_outputs"] = [copy.deepcopy(repeat_output) for _ in range(3)]
        payload["repeat_digests"] = [
            oracle.run_digest(repeat) for repeat in payload["repeat_outputs"]
        ]
        capture = {
            "execution_target": oracle.TARGET_FPGA_HARDWARE,
            "quantization": quantization,
            "hardware": {"revision": "rev-b", "board_serial": "SN-9"},
            "bitstream": {
                "sha256": bitstream_sha256 or "sha256:" + "b" * 64,
                "toolchain": "vendor 1.2",
            },
            "manifest": {
                "payload_sha256": oracle.digest(payload),
                "input_fixture_sha256": scenario["input_fixture"]["sha256"],
                "recorded_at": "2026-01-01T00:00:00Z",
            },
            "payload": payload,
        }
        path = Path(tmp) / "capture.json"
        path.write_text(json.dumps(capture), encoding="utf-8")
        return oracle.RecordedCaptureAdapter(path)

    def _record(self, tmp, **capture_kwargs):
        scenario = hp.build_scenarios(steps=6)[0]
        return hp.generate_records(
            round_number=1,
            steps=6,
            deployment_adapter=self._capture_adapter(
                tmp, scenario, **capture_kwargs
            ),
            repeats=3,
        )[0]

    def test_capture_derived_records_validate(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(hp.validate_record(self._record(tmp), WHERE), [])

    def test_capture_derived_record_declares_hil_provenance(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(self._record(tmp)["provenance"]["kind"], "hil")

    def test_capture_evidence_cannot_be_relabelled_as_an_unknown_adapter(self):
        with tempfile.TemporaryDirectory() as tmp:
            record = self._record(tmp)
            deployment = record["oracle"]["deployment"]
            deployment["adapter"] = "plausible_vendor_driver"
            deployment["runtime_class"] = "physical_hardware"
            errors = hp.validate_record(record, WHERE)
            self.assertTrue(
                any("unsupported adapter identity" in error for error in errors), errors
            )

    def test_capture_digest_chain_is_rechecked_from_stored_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            record = self._record(tmp)
            record["oracle"]["deployment"]["capture"]["source"]["payload"][
                "spikes"
            ][0][0] ^= 1
            errors = hp.validate_record(record, WHERE)
            self.assertTrue(any("capture" in error.lower() for error in errors), errors)

    def test_capture_recorded_at_is_bound_to_the_manifest(self):
        with tempfile.TemporaryDirectory() as tmp:
            record = self._record(tmp)
            record["oracle"]["deployment"]["capture"]["recorded_at"] = (
                "1999-01-01T00:00:00Z"
            )
            errors = hp.validate_record(record, WHERE)
            self.assertTrue(
                any(
                    "recorded_at" in error and "HW_PROVENANCE_MISSING" in error
                    for error in errors
                ),
                errors,
            )

    def test_missing_capture_recorded_at_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            record = self._record(tmp)
            record["oracle"]["deployment"]["capture"].pop("recorded_at", None)
            errors = hp.validate_record(record, WHERE)
            self.assertTrue(
                any(
                    "recorded_at" in error and "HW_PROVENANCE_MISSING" in error
                    for error in errors
                ),
                errors,
            )

    def test_whitespace_only_recorded_at_does_not_bind(self):
        # A whitespace-only value matched on both sides must not validate as
        # bound provenance; `not recorded_at` alone only rejects "".
        with tempfile.TemporaryDirectory() as tmp:
            record = self._record(tmp)
            record["oracle"]["deployment"]["capture"]["recorded_at"] = "   "
            record["oracle"]["deployment"]["capture"]["source"]["manifest"][
                "recorded_at"
            ] = "   "
            errors = hp.validate_record(record, WHERE)
            self.assertTrue(
                any(
                    "recorded_at" in error and "HW_PROVENANCE_MISSING" in error
                    for error in errors
                ),
                errors,
            )

    def test_capture_lineage_includes_physical_provenance_digest(self):
        # Two captures with identical behavioural output but different
        # physical provenance must not collapse to the same result lineage.
        with tempfile.TemporaryDirectory() as tmp:
            record = self._record(tmp)
            derived = record["result"]["derived_from"]
            self.assertEqual(len(derived), 3, derived)
            record["result"]["derived_from"] = derived[:2]
            errors = hp.validate_record(record, WHERE)
            self.assertTrue(
                any("RESULT_DIGEST_UNLINKED" in error for error in errors), errors
            )

    def test_physical_bitstream_requires_canonical_sha256(self):
        with tempfile.TemporaryDirectory() as tmp:
            record = self._record(tmp, bitstream_sha256="sha256:" + "A" * 64)
            errors = hp.validate_record(record, WHERE)
            self.assertTrue(
                any("canonical lowercase" in error for error in errors), errors
            )

    def test_truncated_capture_window_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            record = self._record(tmp, truncate_spikes=True)
            self.assertFalse(record["result"]["parity"]["timing"]["comparable"])
            errors = hp.validate_record(record, WHERE)
            self.assertTrue(
                any(
                    "spikes must have exactly 6 rows" in error
                    and "ENVELOPE_MALFORMED" in error
                    for error in errors
                ),
                errors,
            )

    def test_capture_spike_width_is_bound_to_neuron_count(self):
        with tempfile.TemporaryDirectory() as tmp:
            record = self._record(tmp, narrow_spikes=True)
            errors = hp.validate_record(record, WHERE)
            self.assertTrue(
                any("spikes[0]" in error and "exactly 4 cells" in error for error in errors),
                errors,
            )

    def test_capture_spike_cells_are_exact_binary_integers(self):
        for cell in (True, 2, 0.5):
            with self.subTest(cell=cell), tempfile.TemporaryDirectory() as tmp:
                record = self._record(tmp, invalid_spike_cell=cell)
                errors = hp.validate_record(record, WHERE)
                self.assertTrue(
                    any("exact integer 0 or 1" in error for error in errors), errors
                )

    def test_capture_membrane_width_is_bound_to_neuron_count(self):
        with tempfile.TemporaryDirectory() as tmp:
            record = self._record(tmp, narrow_membrane=True)
            errors = hp.validate_record(record, WHERE)
            self.assertTrue(
                any(
                    "membrane.trace[0]" in error and "exactly 4 cells" in error
                    for error in errors
                ),
                errors,
            )

    def test_capture_action_and_events_must_encode_the_spike_grid(self):
        with tempfile.TemporaryDirectory() as tmp:
            record = self._record(tmp)
            deployment = record["oracle"]["deployment"]
            deployment["action"]["counts"][0] += 1
            deployment["spike_events"][0]["neuron_id"] += 1
            errors = hp.validate_record(record, WHERE)
            self.assertTrue(any(".action does not decode" in error for error in errors), errors)
            self.assertTrue(
                any(".spike_events does not exactly" in error for error in errors),
                errors,
            )

    def test_capture_arithmetic_attestation_is_strict_and_nonnegative(self):
        malformed_values = (
            None,
            {"format": "Q7.9", "saturation_events": 0},
            {"format": "Q8.8", "saturation_events": -1},
            {"format": "Q8.8", "saturation_events": False},
            {"format": "Q8.8", "saturation_events": 0.0},
        )
        for malformed in malformed_values:
            with self.subTest(
                arithmetic=malformed
            ), tempfile.TemporaryDirectory() as tmp:
                record = self._record(tmp)
                deployment = record["oracle"]["deployment"]
                capture = deployment["capture"]
                source = capture["source"]
                payload = source["payload"]
                deployment["arithmetic"] = copy.deepcopy(malformed)
                payload["arithmetic"] = copy.deepcopy(malformed)
                for repeat in payload["repeat_outputs"]:
                    repeat["arithmetic"] = copy.deepcopy(malformed)
                payload_sha = oracle.digest(payload)
                source["manifest"]["payload_sha256"] = payload_sha
                capture["payload_sha256"] = payload_sha
                capture["manifest_sha256"] = oracle.digest(source["manifest"])
                capture["source_sha256"] = oracle.digest(source)

                errors = hp.validate_record(record, WHERE)
                self.assertTrue(
                    any(
                        "arithmetic must declare Q8.8" in error
                        and "ENVELOPE_MALFORMED" in error
                        for error in errors
                    ),
                    errors,
                )

    def test_physical_provenance_values_must_be_nonempty_strings(self):
        mutations = (
            ("hardware", "revision", True),
            ("hardware", "board_serial", 9),
            ("bitstream", "sha256", False),
            ("bitstream", "toolchain", "   "),
            ("capture", "manifest_sha256", ["sha256:bb"]),
        )
        for section, key, value in mutations:
            with self.subTest(
                path=f"{section}.{key}"
            ), tempfile.TemporaryDirectory() as tmp:
                record = self._record(tmp)
                record["oracle"]["deployment"][section][key] = value
                errors = hp.validate_record(record, WHERE)
                self.assertTrue(
                    any(
                        f"oracle.deployment.{section}.{key}" in error
                        and "HW_PROVENANCE_MISSING" in error
                        for error in errors
                    ),
                    errors,
                )

    def test_live_fpga_identity_requires_an_available_transport(self):
        with tempfile.TemporaryDirectory() as tmp:
            record = self._record(tmp)
            deployment = record["oracle"]["deployment"]
            deployment["adapter"] = oracle.FpgaHardwareAdapter.name
            deployment["runtime_class"] = oracle.FpgaHardwareAdapter.runtime_class
            source = deployment["capture"]["source"]
            source["adapter"] = oracle.FpgaHardwareAdapter.name
            source["runtime_class"] = oracle.FpgaHardwareAdapter.runtime_class
            deployment["capture"]["source_sha256"] = oracle.digest(source)
            errors = hp.validate_record(record, WHERE)
            self.assertTrue(
                any(
                    "current adapter probe to report available" in error
                    for error in errors
                ),
                errors,
            )

    def test_recorded_capture_cannot_be_relabelled_as_a_live_board(self):
        with tempfile.TemporaryDirectory() as tmp:
            record = self._record(tmp)
            deployment = record["oracle"]["deployment"]
            deployment["adapter"] = oracle.FpgaHardwareAdapter.name
            deployment["runtime_class"] = oracle.FpgaHardwareAdapter.runtime_class
            errors = hp.validate_record(record, WHERE)
            self.assertTrue(
                any("live FPGA evidence must bind" in error for error in errors),
                errors,
            )

    def test_repeat_digest_binds_the_complete_retained_observation(self):
        with tempfile.TemporaryDirectory() as tmp:
            record = self._record(tmp)
            capture = record["oracle"]["deployment"]["capture"]
            source = capture["source"]
            payload = source["payload"]
            payload["repeat_outputs"][1]["membrane"]["trace"][0][0] += 0.25
            payload_sha = oracle.digest(payload)
            source["manifest"]["payload_sha256"] = payload_sha
            capture["payload_sha256"] = payload_sha
            capture["manifest_sha256"] = oracle.digest(source["manifest"])
            capture["source_sha256"] = oracle.digest(source)

            errors = hp.validate_record(record, WHERE)
            self.assertTrue(
                any("repeat_digests[1] is not derived" in error for error in errors),
                errors,
            )

    def test_repeat_digest_includes_arithmetic_observations(self):
        with tempfile.TemporaryDirectory() as tmp:
            record = self._record(tmp)
            capture = record["oracle"]["deployment"]["capture"]
            source = capture["source"]
            payload = source["payload"]
            payload["repeat_outputs"][1]["arithmetic"]["saturation_events"] += 1
            payload_sha = oracle.digest(payload)
            source["manifest"]["payload_sha256"] = payload_sha
            capture["payload_sha256"] = payload_sha
            capture["manifest_sha256"] = oracle.digest(source["manifest"])
            capture["source_sha256"] = oracle.digest(source)

            errors = hp.validate_record(record, WHERE)
            self.assertTrue(
                any("repeat_digests[1] is not derived" in error for error in errors),
                errors,
            )

    def _with_q88_raw(self, record, raw_value):
        deployment = record["oracle"]["deployment"]
        payload = deployment["capture"]["source"]["payload"]

        def stamp(membrane):
            raw = [
                [int(round(cell * oracle.Q88_SCALE)) for cell in row]
                for row in membrane["trace"]
            ]
            raw[0][0] = raw_value
            membrane["trace_q88_raw"] = raw

        stamp(payload["membrane"])
        for repeat in payload["repeat_outputs"]:
            stamp(repeat["membrane"])
        stamp(deployment["membrane"])
        payload["repeat_digests"] = [
            oracle.run_digest(repeat) for repeat in payload["repeat_outputs"]
        ]
        payload_sha = oracle.digest(payload)
        source = deployment["capture"]["source"]
        source["manifest"]["payload_sha256"] = payload_sha
        deployment["capture"]["payload_sha256"] = payload_sha
        deployment["capture"]["manifest_sha256"] = oracle.digest(source["manifest"])
        deployment["capture"]["source_sha256"] = oracle.digest(source)
        deployment["output_digest"] = oracle.run_digest(payload)
        deployment["repeat_digests"] = list(payload["repeat_digests"])
        return record

    def test_captured_q88_raw_must_correspond_to_the_float_trace(self):
        with tempfile.TemporaryDirectory() as tmp:
            record = self._with_q88_raw(self._record(tmp), 65)
            errors = hp.validate_record(record, WHERE)
            self.assertTrue(any("raw/256" in error for error in errors), errors)

    def test_captured_q88_raw_outside_int16_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            record = self._with_q88_raw(self._record(tmp), 999999)
            errors = hp.validate_record(record, WHERE)
            self.assertTrue(
                any("signed Q8.8 int16 range" in error for error in errors),
                errors,
            )

    def test_malformed_nested_environment_and_bitstream_report_without_crashing(self):
        with tempfile.TemporaryDirectory() as tmp:
            for mutate in (
                lambda record: record["oracle"].__setitem__("environment", "bad"),
                lambda record: record["oracle"]["deployment"].__setitem__(
                    "bitstream", "bad"
                ),
            ):
                with self.subTest(mutate=mutate):
                    record = self._record(tmp)
                    mutate(record)
                    errors = hp.validate_record(record, WHERE)
                    self.assertTrue(errors)

    def test_a_hardware_claim_is_never_unqualified(self):
        # The deployment traces of a physical run cannot be re-derived, so the
        # record must say so rather than reading as fully corroborated.
        with tempfile.TemporaryDirectory() as tmp:
            record = self._record(tmp)
            self.assertIn(
                "DEPLOYMENT_TRACE_NOT_REDERIVABLE", record["result"]["reason_codes"]
            )
            view = hp.training_view(record)
            self.assertIn(
                "DEPLOYMENT_TRACE_NOT_REDERIVABLE", view["reason_codes"]
            )
            self.assertFalse(view["oracle_complete"])
            self.assertFalse(view["parity_failed"])

    def test_reference_model_records_are_not_marked_unrederivable(self):
        for record in hp.generate_records(round_number=1, steps=4, repeats=2):
            self.assertNotIn(
                "DEPLOYMENT_TRACE_NOT_REDERIVABLE", record["result"]["reason_codes"]
            )

    def test_capture_taken_against_another_input_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            scenario = hp.build_scenarios(steps=6)[0]
            adapter = self._capture_adapter(tmp, scenario)
            # Generating with a different window changes the input fixture.
            records = hp.generate_records(
                round_number=1, steps=8, deployment_adapter=adapter, repeats=3
            )
            self.assertTrue(
                all(record["oracle"]["deployment"] is None for record in records)
            )
            self.assertEqual(hp.validate_records(records), [])


class PhysicalTargetClaims(unittest.TestCase):
    def _promoted(self, hil=True, **deployment_overrides):
        """A reference-model record relabelled as if it came from a board."""
        record = copy.deepcopy(hp.generate_records(round_number=1, steps=4, repeats=2)[0])
        deployment = record["oracle"]["deployment"]
        deployment["execution_target"] = oracle.TARGET_FPGA_HARDWARE
        deployment.update(copy.deepcopy(deployment_overrides))
        if hil:
            record["provenance"]["kind"] = "hil"
        return record

    def test_bare_fpga_claim_is_rejected(self):
        errors = hp.validate_record(self._promoted(), WHERE)
        self.assertTrue(any("HW_PROVENANCE_MISSING" in error for error in errors))

    def test_hardware_claim_must_declare_hil_provenance(self):
        # A record claiming a board while still calling itself `simulated` is
        # not describing one execution consistently.
        errors = hp.validate_record(self._promoted(hil=False), WHERE)
        self.assertTrue(any("provenance.kind 'hil'" in error for error in errors))

    def _fully_attributed(self):
        """Everything the physical-target gate demands, and nothing more."""
        return {
            "hardware": {"revision": "rev-b", "board_serial": "SN-1"},
            "bitstream": {"sha256": "sha256:aa", "toolchain": "vendor 1.2"},
            "capture": {"manifest_sha256": "sha256:bb"},
            "latency": {"measured": True, "value_ms": 0.4},
            "repeats": 3,
            "repeat_digests": ["sha256:cc"] * 3,
            "determinism": {"distinct_digests": 1, "identical_repeats": True},
            "output_digest": "sha256:cc",
        }

    def test_each_required_field_is_individually_load_bearing(self):
        # Drop exactly one field from an otherwise complete claim, so the test
        # cannot pass merely because everything is missing at once.
        for section, key in hp.REQUIRED_HARDWARE_FIELDS:
            with self.subTest(field=f"{section}.{key}"):
                attributed = self._fully_attributed()
                del attributed[section][key]
                errors = hp.validate_record(self._promoted(**attributed), WHERE)
                self.assertTrue(
                    any(f"{section}.{key}" in error for error in errors),
                    f"{section}.{key} was not demanded",
                )

    def test_labels_alone_cannot_turn_a_reference_run_into_hardware(self):
        # Even a fully decorated reference-model record lacks the capture
        # source bytes and adapter binding needed for a physical claim.
        errors = hp.validate_record(self._promoted(**self._fully_attributed()), WHERE)
        self.assertTrue(
            any("capture.source" in error or "cannot come from adapter" in error
                for error in errors),
            errors,
        )

    def test_unmeasured_latency_blocks_a_hardware_claim(self):
        record = self._promoted(
            hardware={"revision": "rev-b", "board_serial": "SN-1"},
            bitstream={"sha256": "sha256:aa", "toolchain": "vendor 1.2"},
            capture={"manifest_sha256": "sha256:bb"},
        )
        errors = hp.validate_record(record, WHERE)
        self.assertTrue(any("measured latency" in error for error in errors))

    def test_physical_latency_must_be_finite_nonnegative_and_not_boolean(self):
        for value in (True, -0.1, float("nan"), float("inf")):
            with self.subTest(value=value):
                attributed = self._fully_attributed()
                attributed["latency"]["value_ms"] = value
                errors = hp.validate_record(self._promoted(**attributed), WHERE)
                self.assertTrue(
                    any("measured latency" in error for error in errors), errors
                )

    def test_single_run_cannot_prove_determinism(self):
        record = self._promoted(
            hardware={"revision": "rev-b", "board_serial": "SN-1"},
            bitstream={"sha256": "sha256:aa", "toolchain": "vendor 1.2"},
            capture={"manifest_sha256": "sha256:bb"},
            latency={"measured": True, "value_ms": 0.4},
            repeats=1,
        )
        errors = hp.validate_record(record, WHERE)
        self.assertTrue(any("REPEATABILITY_UNPROVEN" in error for error in errors))

    def test_unknown_execution_target_is_rejected(self):
        record = self._promoted()
        record["oracle"]["deployment"]["execution_target"] = "some_accelerator"
        errors = hp.validate_record(record, WHERE)
        self.assertTrue(any("HW_TARGET_UNKNOWN" in error for error in errors))

    def test_non_boolean_fpga_available_is_rejected(self):
        record = copy.deepcopy(hp.generate_records(round_number=1, steps=4, repeats=2)[0])
        record["oracle"]["environment"]["fpga_hardware"]["available"] = "false"
        errors = hp.validate_record(record, WHERE)
        self.assertTrue(
            any(
                "fpga_hardware.available must be a boolean" in error for error in errors
            ),
            errors,
        )

    def test_unavailable_fpga_probe_needs_a_nonblank_reason_code(self):
        record = copy.deepcopy(hp.generate_records(round_number=1, steps=4, repeats=2)[0])
        record["oracle"]["environment"]["fpga_hardware"]["reason_code"] = "   "
        errors = hp.validate_record(record, WHERE)
        self.assertTrue(
            any("must name a reason_code" in error for error in errors), errors
        )

    def test_fpga_available_true_is_not_corroborated(self):
        # No adapter code path in this repository can produce a truthful
        # `available: true` probe; a fixed-point record claiming one must
        # still be rejected even though it does not claim a live FPGA
        # deployment.
        record = copy.deepcopy(hp.generate_records(round_number=1, steps=4, repeats=2)[0])
        record["oracle"]["environment"]["fpga_hardware"] = {
            "available": True,
            "reason_code": None,
            "detail": "board online",
        }
        errors = hp.validate_record(record, WHERE)
        self.assertTrue(
            any("fpga_hardware.available is true" in error for error in errors), errors
        )

    def test_deleting_the_execution_target_is_not_a_way_out(self):
        # Removing an inconvenient label must not be quieter than declaring it.
        record = copy.deepcopy(hp.generate_records(round_number=1, steps=4, repeats=2)[0])
        del record["oracle"]["deployment"]["execution_target"]
        errors = hp.validate_record(record, WHERE)
        self.assertTrue(any("HW_TARGET_UNKNOWN" in error for error in errors))

    def test_reference_model_target_needs_no_board_metadata(self):
        records = hp.generate_records(round_number=1, steps=4, repeats=2)
        self.assertEqual(hp.validate_records(records), [])

    def test_reference_model_cannot_claim_measured_latency(self):
        record = copy.deepcopy(hp.generate_records(round_number=1, steps=4, repeats=2)[0])
        record["oracle"]["deployment"]["latency"] = {
            "measured": True,
            "value_ms": 0.001,
        }
        parity, verdict, codes = hp.compute_parity(
            record["scenario"],
            record["oracle"]["software"],
            record["oracle"]["deployment"],
        )
        record["result"]["parity"] = parity
        record["result"]["verdict"] = verdict
        record["result"]["reason_codes"] = codes
        record["result"]["summary"] = hp._summarize(
            record["scenario"], parity, verdict, record["oracle"]["deployment"]
        )
        errors = hp.validate_record(record, WHERE)
        self.assertTrue(any("LATENCY_NOT_MEASURED" in error for error in errors), errors)


class TrainingViews(unittest.TestCase):
    def test_views_preserve_every_record(self):
        records = _fixture_records()
        views, errors = hp.build_training_views(records)
        self.assertEqual(errors, [])
        self.assertEqual(len(views), len(records))

    def test_failed_records_are_flagged_in_the_view(self):
        views, _ = hp.build_training_views(_fixture_records())
        failed = [view for view in views if view["parity_failed"]]
        self.assertTrue(failed)
        for view in failed:
            self.assertNotEqual(view["verdict"], contract.VERDICT_MATCH)
            self.assertTrue(view["reason_codes"])

    def test_view_names_both_execution_targets(self):
        views, _ = hp.build_training_views(_fixture_records())
        self.assertIn(oracle.TARGET_SOFTWARE_FLOAT, views[0]["execution_targets"])
        self.assertIn(
            oracle.TARGET_FIXED_POINT_MODEL, views[0]["execution_targets"]
        )

    def test_filtering_out_failures_is_rejected(self):
        records = _fixture_records()
        views = [
            hp.training_view(record)
            for record in records
            if record["result"]["verdict"] == contract.VERDICT_MATCH
        ]
        errors = contract.view_set_errors(records, views)
        self.assertTrue(any("TRAINING_VIEW_HIDES_FAILURE" in error for error in errors))

    def test_completion_is_rederived_instead_of_copying_summary(self):
        record = copy.deepcopy(_fixture_records()[0])
        record["result"]["summary"] = "fabricated completion"
        view = hp.training_view(record)
        self.assertNotEqual(view["completion"], "fabricated completion")

    def test_every_hardware_specific_training_field_is_rederived(self):
        record = copy.deepcopy(_fixture_records()[0])
        mutations = {
            "prompt": "fabricated prompt",
            "completion": "hardware and software matched perfectly",
            "stress": "fabricated-stress",
            "scenario_id": "fabricated-scenario",
        }
        for key, value in mutations.items():
            with self.subTest(key=key):
                view = hp.training_view(record)
                view[key] = value
                errors = hp.training_view_errors(record, view, WHERE)
                self.assertTrue(
                    any(
                        "validator-derived hardware projection" in error
                        for error in errors
                    ),
                    errors,
                )

    def test_swapped_view_ids_are_rejected_against_their_source_records(self):
        records = copy.deepcopy(_fixture_records()[:2])
        views = [hp.training_view(record) for record in records]
        views[0]["id"], views[1]["id"] = views[1]["id"], views[0]["id"]
        errors = []
        for index, (record, view) in enumerate(zip(records, views), 1):
            errors += hp.training_view_errors(record, view, f"view:{index}")
        errors += contract.view_set_errors(records, views)
        self.assertTrue(
            any("view id must exactly match" in error for error in errors), errors
        )

    def test_unavailable_deployment_prompt_does_not_claim_execution(self):
        adapter = oracle.FpgaHardwareAdapter(env={})
        record = hp.generate_records(
            round_number=1,
            steps=4,
            deployment_adapter=adapter,
            repeats=2,
        )[0]
        prompt = hp.training_view(record)["prompt"]
        self.assertIn("did not execute", prompt)
        self.assertNotIn("executed on the deployment target", prompt)


class Cli(unittest.TestCase):
    def test_availability_reports_no_fpga(self):
        result = _cli(["availability"])
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(json.loads(result.stdout)["spikenaut_fpga"]["available"])

    def test_generate_then_validate(self):
        with tempfile.TemporaryDirectory() as tmp:
            generated = _cli(["generate", tmp, "--round", "2", "--steps", "6"])
            self.assertEqual(generated.returncode, 0, generated.stderr)
            summary = json.loads(generated.stdout)
            out = Path(summary["written"])
            self.assertTrue(out.exists())
            self.assertEqual(out.name, "batch-r02.jsonl")
            validated = _cli(["validate", str(out)])
            self.assertEqual(validated.returncode, 0, validated.stderr)

    def test_generate_refuses_to_overwrite_an_existing_round(self):
        with tempfile.TemporaryDirectory() as tmp:
            first = _cli(["generate", tmp, "--round", "2", "--steps", "4"])
            self.assertEqual(first.returncode, 0, first.stderr)
            out = Path(json.loads(first.stdout)["written"])
            before = out.read_bytes()
            second = _cli(["generate", tmp, "--round", "2", "--steps", "6"])
            self.assertEqual(second.returncode, 2, second.stderr)
            self.assertIn("refusing to overwrite", second.stderr)
            self.assertEqual(out.read_bytes(), before)

    def test_generate_rejects_nonpositive_steps_with_a_usage_error(self):
        # Previously this reached generate_records() unchecked and the
        # software adapter raised ValueError normalizing the empty
        # stimulus, outside every handler in main() — a traceback instead
        # of a clean usage error.
        with tempfile.TemporaryDirectory() as tmp:
            for steps in ("0", "-1"):
                with self.subTest(steps=steps):
                    result = _cli(["generate", tmp, "--round", "9", "--steps", steps])
                    self.assertEqual(result.returncode, 2, result.stderr)
                    self.assertIn("--steps must be a positive integer", result.stderr)

    def test_jsonl_framing_uses_lf_not_unicode_line_separators(self):
        for separator in ("\u2028", "\u2029"):
            with self.subTest(
                separator=ord(separator)
            ), tempfile.TemporaryDirectory() as tmp:
                path = Path(tmp) / "batch.jsonl"
                path.write_text(
                    json.dumps(
                        {"id": f"left{separator}right"}, ensure_ascii=False
                    )
                    + "\n",
                    encoding="utf-8",
                )
                records, errors = hp.read_jsonl(path)
                self.assertEqual(errors, [])
                self.assertEqual(records, [{"id": f"left{separator}right"}])

    def test_read_jsonl_rejects_non_standard_json_constants(self):
        # A record containing NaN/Infinity must be a parse error, not a
        # silently accepted value standards-compliant JSON parsers reject.
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "batch.jsonl"
            path.write_text('{"pairing": NaN}\n', encoding="utf-8")
            records, errors = hp.read_jsonl(path)
            self.assertEqual(records, [])
            self.assertTrue(errors)
            self.assertIn("non-standard JSON numeric constant", errors[0])

    def test_validate_rejects_a_tampered_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "batch.jsonl"
            records = _fixture_records()
            records[1]["result"]["verdict"] = contract.VERDICT_MATCH
            path.write_text(
                "".join(json.dumps(record, sort_keys=True) + "\n" for record in records),
                encoding="utf-8",
            )
            result = _cli(["validate", str(path)])
            self.assertEqual(result.returncode, 1)
            self.assertIn("PARITY_VERDICT_INCONSISTENT", result.stderr)

    def test_validate_reports_a_parse_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "batch.jsonl"
            path.write_text("not json\n", encoding="utf-8")
            result = _cli(["validate", str(path)])
            self.assertEqual(result.returncode, 1)
        self.assertIn("JSON parse error", result.stderr)

    def test_training_view_refuses_an_invalid_record(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "batch.jsonl"
            record = copy.deepcopy(
                next(
                    item
                    for item in _fixture_records()
                    if item["result"]["verdict"] == contract.VERDICT_MISMATCH
                )
            )
            record["result"]["verdict"] = contract.VERDICT_MATCH
            path.write_text(json.dumps(record) + "\n", encoding="utf-8")
            result = _cli(["training-view", str(path)])
            self.assertEqual(result.returncode, 1)
            self.assertIn("PARITY_VERDICT_INCONSISTENT", result.stderr)

    def test_unknown_target_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = _cli(["generate", tmp, "--target", "mystery_board"])
            self.assertEqual(result.returncode, 2)

    def test_recorded_capture_target_requires_a_capture_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = _cli(["generate", tmp, "--target", "recorded_capture"])
            self.assertEqual(result.returncode, 2)
            self.assertIn("requires --capture", result.stderr)

    def test_validate_reports_an_unreadable_path(self):
        result = _cli(["validate", "/definitely/missing/parity.jsonl"])
        self.assertEqual(result.returncode, 1)
        self.assertIn("cannot read file", result.stderr)

    def test_training_view_cli_emits_one_line_per_record(self):
        result = _cli(["training-view", str(FIXTURE)])
        self.assertEqual(result.returncode, 0, result.stderr)
        lines = [line for line in result.stdout.splitlines() if line.strip()]
        self.assertEqual(len(lines), len(_fixture_records()))


if __name__ == "__main__":
    unittest.main()
