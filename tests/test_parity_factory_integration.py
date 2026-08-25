"""The parity families must route through the normal factory layers.

A dataset family that only its own CLI understands is not part of the factory.
These tests pin the three integration points: census classification, the shape
layer in validate_run, and the deep layer in check_records.
"""

import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PIPELINES = REPO / "pipelines"
FIXTURE_RUN = REPO / "tests" / "fixtures" / "parity-run"
HARDWARE_BATCH = (
    FIXTURE_RUN / "hardware-parity-spike-trajectories" / "batch-r01.jsonl"
)
NIR_BATCH = FIXTURE_RUN / "nir-cross-runtime-equivalence" / "batch-r01.jsonl"
sys.path.insert(0, str(PIPELINES))

import census  # noqa: E402
import check_records  # noqa: E402
import oracle_contract as contract  # noqa: E402
import validate_run  # noqa: E402


def _records(path):
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _run(script, *args):
    return subprocess.run(
        [sys.executable, str(PIPELINES / script), *args],
        capture_output=True,
        text=True,
    )


class FixtureRun(unittest.TestCase):
    def test_both_families_are_committed(self):
        self.assertTrue(HARDWARE_BATCH.exists())
        self.assertTrue(NIR_BATCH.exists())

    def test_fixture_is_regenerable_byte_for_byte(self):
        # The committed fixture is the generators' default output. If this
        # fails, either the fixture is stale or a generator stopped being
        # deterministic; both need a human decision, not a silent refresh.
        import hardware_parity
        import nir_equivalence

        with tempfile.TemporaryDirectory() as tmp:
            hardware_parity.write_jsonl(
                Path(tmp) / "hp.jsonl", hardware_parity.generate_records(round_number=1)
            )
            nir_equivalence.write_jsonl(
                Path(tmp) / "nir.jsonl", nir_equivalence.generate_records(round_number=1)
            )
            self.assertEqual(
                (Path(tmp) / "hp.jsonl").read_text(encoding="utf-8"),
                HARDWARE_BATCH.read_text(encoding="utf-8"),
            )
            self.assertEqual(
                (Path(tmp) / "nir.jsonl").read_text(encoding="utf-8"),
                NIR_BATCH.read_text(encoding="utf-8"),
            )

    def test_no_record_claims_real_world_provenance(self):
        for path in (HARDWARE_BATCH, NIR_BATCH):
            for record in _records(path):
                with self.subTest(record=record["id"]):
                    self.assertIn(
                        record["provenance"]["kind"], contract.PROVENANCE_KINDS
                    )
                    self.assertNotEqual(record["provenance"]["kind"], "real")

    def test_no_record_claims_an_unexecuted_oracle(self):
        for record in _records(HARDWARE_BATCH):
            target = record["oracle"]["deployment"]["execution_target"]
            with self.subTest(record=record["id"]):
                self.assertNotIn(target, ("fpga_hardware", "recorded_capture"))
                self.assertIn("ORACLE_UNAVAILABLE", record["result"]["reason_codes"])

    def test_nir_records_name_no_upstream_runtime_as_executed(self):
        for record in _records(NIR_BATCH):
            executed = [
                entry["runtime"]
                for entry in record["oracle"]["runtimes"]
                if entry["status"] == "executed"
            ]
            with self.subTest(record=record["id"]):
                self.assertNotIn("nir_rs", executed)
                self.assertNotIn("nirtorch_snntorch", executed)


class CensusRouting(unittest.TestCase):
    def test_kinds_are_classified_not_unknown(self):
        for record in _records(HARDWARE_BATCH):
            self.assertEqual(census.classify_kind(record), "hardware_parity")
        for record in _records(NIR_BATCH):
            self.assertEqual(census.classify_kind(record), "nir_equivalence")

    def test_census_counts_the_fixture_run(self):
        result = census.census_dir(FIXTURE_RUN)
        self.assertEqual(result["parse_failures"], 0)
        self.assertEqual(result["by_kind"]["unknown"], 0)
        self.assertEqual(
            result["by_kind"]["hardware_parity"], len(_records(HARDWARE_BATCH))
        )
        self.assertEqual(
            result["by_kind"]["nir_equivalence"], len(_records(NIR_BATCH))
        )

    def test_declared_kinds_are_in_the_reported_vocabulary(self):
        for kind in census.DECLARED_KINDS:
            self.assertIn(kind, census.KINDS)


class ShapeLayer(unittest.TestCase):
    def test_check_line_routes_on_the_declared_kind(self):
        for record in _records(HARDWARE_BATCH):
            errors, kind = validate_run.check_line(record, "unit:1")
            self.assertEqual(kind, "hardware_parity")
            self.assertEqual(errors, [])
        for record in _records(NIR_BATCH):
            errors, kind = validate_run.check_line(record, "unit:1")
            self.assertEqual(kind, "nir_equivalence")
            self.assertEqual(errors, [])

    def test_shape_layer_rejects_a_self_certifying_generator(self):
        record = copy.deepcopy(_records(HARDWARE_BATCH)[0])
        record["generator"]["may_certify_oracle_result"] = True
        errors, kind = validate_run.check_line(record, "unit:1")
        self.assertEqual(kind, "hardware_parity")
        self.assertTrue(any("GENERATOR_SELF_CERTIFIED" in error for error in errors))

    def test_validate_run_cli_accepts_the_fixture_run(self):
        result = _run("validate_run.py", str(FIXTURE_RUN))
        self.assertEqual(result.returncode, 0, result.stderr)
        totals = json.loads(result.stdout)
        self.assertEqual(totals["error_count"], 0)
        self.assertEqual(
            set(totals["by_kind"]), {"hardware_parity", "nir_equivalence"}
        )

    def test_a_parity_record_is_never_mistaken_for_a_trajectory(self):
        # A parity record that happens to carry a thalamic-looking key must
        # still route on its declared kind.
        record = copy.deepcopy(_records(HARDWARE_BATCH)[0])
        record["reward_components"] = {"task_progress": 1.0, "total": 1.0}
        _, kind = validate_run.check_line(record, "unit:1")
        self.assertEqual(kind, "hardware_parity")


class DeepLayer(unittest.TestCase):
    def test_check_records_cli_accepts_the_fixture_run(self):
        result = _run("check_records.py", str(FIXTURE_RUN))
        self.assertEqual(result.returncode, 0, result.stderr)
        totals = json.loads(result.stdout)
        self.assertEqual(totals["error_count"], 0)
        self.assertEqual(totals["warning_count"], 0)

    def test_deep_layer_recomputes_hardware_parity_metrics(self):
        record = copy.deepcopy(_records(HARDWARE_BATCH)[0])
        record["result"]["parity"]["spike_bitmap"]["hamming_distance"] = 99
        errors, _warnings, kind, _id = check_records.check_record(record, "unit:1")
        self.assertEqual(kind, "hardware_parity")
        self.assertTrue(any("PARITY_METRIC_MISMATCH" in error for error in errors))

    def test_deep_layer_re_executes_nir_runtimes(self):
        record = copy.deepcopy(_records(NIR_BATCH)[0])
        entry = next(
            item
            for item in record["oracle"]["runtimes"]
            if item["status"] == "executed"
        )
        entry["outputs"]["spike_count"] += 1
        errors, _warnings, kind, _id = check_records.check_record(record, "unit:1")
        self.assertEqual(kind, "nir_equivalence")
        self.assertTrue(errors)

    def test_deep_layer_keeps_the_record_id_for_duplicate_detection(self):
        record = _records(HARDWARE_BATCH)[0]
        _errors, _warnings, _kind, record_id = check_records.check_record(
            record, "unit:1"
        )
        self.assertEqual(record_id, record["id"])

    def test_nested_real_world_claims_are_caught_like_any_other_kind(self):
        # The publish-time provenance scan is repository-wide. Skipping it for
        # these kinds would make a parity record the one place in the factory
        # where a buried real-world claim is allowed through.
        record = copy.deepcopy(_records(HARDWARE_BATCH)[0])
        record["oracle"]["deployment"]["hardware"] = {
            "revision": "rev-a",
            "sim_or_real": "real",
        }
        errors, _warnings, _kind, _id = check_records.check_record(record, "unit:1")
        self.assertTrue(any("must not be 'real'" in error for error in errors))

    def test_nested_real_provenance_kind_is_caught(self):
        record = copy.deepcopy(_records(NIR_BATCH)[0])
        record["oracle"]["capture_note"] = {"provenance": {"kind": "real"}}
        errors, _warnings, _kind, _id = check_records.check_record(record, "unit:1")
        self.assertTrue(any("must not be 'real'" in error for error in errors))

    def test_an_unroutable_parity_kind_is_loud(self):
        # No silent fallthrough to whichever validator happened to be last.
        errors = check_records.check_parity_record({}, "some_future_kind", "unit:1")
        self.assertTrue(any("no parity validator" in error for error in errors))

    def test_a_malformed_record_does_not_abort_the_whole_run_scan(self):
        # One bad line must be reported, not raise and take the directory
        # scan down with it.
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp) / "run" / "hardware-parity-spike-trajectories"
            run_dir.mkdir(parents=True)
            records = _records(HARDWARE_BATCH)[:2]
            records[0] = copy.deepcopy(records[0])
            records[0]["id"] = "broken-1"
            records[0]["oracle"]["deployment"] = "tampered"
            (run_dir / "batch-r01.jsonl").write_text(
                "".join(json.dumps(record, sort_keys=True) + "\n" for record in records),
                encoding="utf-8",
            )
            result = _run("check_records.py", str(Path(tmp) / "run"))
            self.assertEqual(result.returncode, 1)
            self.assertNotIn("Traceback", result.stderr)
            totals = json.loads(result.stdout)
            self.assertEqual(totals["records"], 2)

    def test_shape_failure_stops_before_the_family_validator(self):
        record = copy.deepcopy(_records(HARDWARE_BATCH)[0])
        record["scenario"] = "bad"
        try:
            errors, _warnings, kind, _id = check_records.check_record(
                record, "unit:1"
            )
        except Exception as exc:  # noqa: BLE001 - this is the crash regression
            self.fail(f"shape failure escaped as {type(exc).__name__}: {exc}")
        self.assertEqual(kind, "hardware_parity")
        self.assertTrue(errors)

    def test_duplicate_ids_across_the_run_are_caught(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp) / "run" / "hardware-parity-spike-trajectories"
            run_dir.mkdir(parents=True)
            records = _records(HARDWARE_BATCH)[:1]
            for name in ("batch-r01.jsonl", "batch-r02.jsonl"):
                (run_dir / name).write_text(
                    "".join(
                        json.dumps(record, sort_keys=True) + "\n" for record in records
                    ),
                    encoding="utf-8",
                )
            result = _run("check_records.py", str(Path(tmp) / "run"))
            self.assertEqual(result.returncode, 1)
            self.assertIn("duplicate record id", result.stderr)


if __name__ == "__main__":
    unittest.main()
