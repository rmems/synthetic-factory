"""Scenario catalogue, parity metrics, record generation, and the CLI for
pipelines/hardware_parity.py."""

import copy
import json
import tempfile
import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from hardware_parity_support import (  # noqa: E402
    FIXTURE,
    WHERE,
    cli as _cli,
    fixture_records as _fixture_records,
)

import hardware_parity as hp  # noqa: E402
import neuro_oracle as oracle  # noqa: E402
import oracle_contract as contract  # noqa: E402

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
