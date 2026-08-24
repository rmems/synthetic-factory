"""Tests for pipelines/hardware_parity.py."""

import copy
import json
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

    def test_timing_counts_neurons_that_fire_on_one_side_only(self):
        metrics = hp.timing_metrics([[1, 1]], [[1, 0]], dt_ms=1.0)
        self.assertEqual(metrics["neurons_firing_software_only"], 1)
        self.assertEqual(metrics["neurons_firing_hardware_only"], 0)

    def test_membrane_within_tolerance(self):
        metrics = hp.membrane_metrics(
            {"observable": True, "trace": [[0.0, 1.0]]},
            {"observable": True, "trace": [[0.0, 1.0]]},
        )
        self.assertTrue(metrics["within_tolerance"])
        self.assertEqual(metrics["max_abs_error"], 0.0)

    def test_membrane_beyond_tolerance_is_flagged(self):
        metrics = hp.membrane_metrics(
            {"observable": True, "trace": [[0.0]]},
            {"observable": True, "trace": [[1.0]]},
        )
        self.assertFalse(metrics["within_tolerance"])

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

    def test_falsified_quantization_provenance_is_caught(self):
        record = copy.deepcopy(self.records[0])
        record["oracle"]["deployment"]["quantization"]["parameters"][0]["q88_raw"] += 1
        errors = hp.validate_record(record, WHERE)
        self.assertTrue(any("Q88_PROVENANCE_MISMATCH" in error for error in errors))

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


class PhysicalTargetClaims(unittest.TestCase):
    def _promoted(self, **deployment_overrides):
        """A reference-model record relabelled as if it came from a board."""
        record = copy.deepcopy(hp.generate_records(round_number=1, steps=4, repeats=2)[0])
        deployment = record["oracle"]["deployment"]
        deployment["execution_target"] = oracle.TARGET_FPGA_HARDWARE
        deployment.update(copy.deepcopy(deployment_overrides))
        return record

    def test_bare_fpga_claim_is_rejected(self):
        errors = hp.validate_record(self._promoted(), WHERE)
        self.assertTrue(any("HW_PROVENANCE_MISSING" in error for error in errors))

    def _fully_attributed(self):
        return {
            "hardware": {"revision": "rev-b", "board_serial": "SN-1"},
            "bitstream": {"sha256": "sha256:aa", "toolchain": "vendor 1.2"},
            "capture": {"manifest_sha256": "sha256:bb"},
            "latency": {"measured": True, "value_ms": 0.4},
            "repeats": 3,
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

    def test_a_fully_attributed_claim_clears_the_provenance_gate(self):
        # The parity metrics still have to hold up; this asserts only that the
        # board/bitstream/capture gate itself is satisfiable.
        errors = hp.validate_record(self._promoted(**self._fully_attributed()), WHERE)
        self.assertFalse(
            [
                error
                for error in errors
                if "HW_PROVENANCE_MISSING" in error or "REPEATABILITY_UNPROVEN" in error
            ],
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

    def test_deleting_the_execution_target_is_not_a_way_out(self):
        # Removing an inconvenient label must not be quieter than declaring it.
        record = copy.deepcopy(hp.generate_records(round_number=1, steps=4, repeats=2)[0])
        del record["oracle"]["deployment"]["execution_target"]
        errors = hp.validate_record(record, WHERE)
        self.assertTrue(any("HW_TARGET_UNKNOWN" in error for error in errors))

    def test_reference_model_target_needs_no_board_metadata(self):
        records = hp.generate_records(round_number=1, steps=4, repeats=2)
        self.assertEqual(hp.validate_records(records), [])


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

    def test_unknown_target_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = _cli(["generate", tmp, "--target", "mystery_board"])
            self.assertEqual(result.returncode, 2)

    def test_training_view_cli_emits_one_line_per_record(self):
        result = _cli(["training-view", str(FIXTURE)])
        self.assertEqual(result.returncode, 0, result.stderr)
        lines = [line for line in result.stdout.splitlines() if line.strip()]
        self.assertEqual(len(lines), len(_fixture_records()))


if __name__ == "__main__":
    unittest.main()
