#!/usr/bin/env python3
"""Tests for the SNN distillation raster loader.

The probe's contract is that a distillation run reads execution-grounded
spikes out of structured JSON — never out of prose counts or margins — and
that an unverifiable raster is reported instead of emitted.
"""

from __future__ import annotations

import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "pipelines"))

import spike_probe  # noqa: E402

FIXTURES = REPO / "tests" / "fixtures"
GATE_SNN_FIXTURE = FIXTURES / "bridge_gate_snn.jsonl"


def gate_snn_record():
    return json.loads(GATE_SNN_FIXTURE.read_text(encoding="utf-8").splitlines()[0])


def write(path, records):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(record) + "\n" for record in records))


class NormalizeRaster(unittest.TestCase):
    def test_events_load_as_sorted_neuron_id_and_microsecond_pairs(self):
        raster = spike_probe.normalize_raster(gate_snn_record())

        self.assertEqual(raster["record_id"], "bridge-gate-snn-fixture-001")
        self.assertEqual(raster["window_us"], 40000)
        self.assertEqual(raster["neurons"], 256)
        self.assertEqual(raster["spikes"], 123)
        self.assertEqual(raster["energy_pJ"], 123 * 23)
        self.assertEqual(
            [(event["neuron_id"], event["t_us"]) for event in raster["events"]],
            [(7, 800), (131, 4600), (44, 17200), (200, 29500), (255, 38100)],
        )
        times = [event["t_us"] for event in raster["events"]]
        self.assertEqual(times, sorted(times))
        for event in raster["events"]:
            self.assertIsInstance(event["t_us"], int)

    def test_routing_third_factor_and_gate_head_are_structured(self):
        raster = spike_probe.normalize_raster(gate_snn_record())

        self.assertEqual(raster["routing"]["source"], "pop_gate_exc_256")
        self.assertEqual(len(raster["routing"]["table"]), 2)
        self.assertEqual(raster["routing"]["third_factor"]["tau_e_s"], 2.0)
        self.assertEqual(raster["gate_snn"]["decision_window_ms"], 25)
        self.assertEqual(
            [pop["neurons"] for pop in raster["gate_snn"]["populations"]], [64, 64]
        )
        self.assertEqual(
            [pop["threshold"] for pop in raster["gate_snn"]["populations"]], [1.0, 1.0]
        )

    def test_window_may_be_declared_in_seconds(self):
        record = gate_snn_record()
        del record["raster"]["window_ms"]
        self.assertEqual(spike_probe.normalize_raster(record)["window_us"], 40000)

    def test_routing_free_raster_is_not_emitted(self):
        record = gate_snn_record()
        record["raster"]["routing"]["table"] = []
        self.assertIsNone(spike_probe.normalize_raster(record))

    def test_unverifiable_raster_is_not_emitted(self):
        record = gate_snn_record()
        record["raster"]["spikes"] = 999
        self.assertIsNone(spike_probe.normalize_raster(record))

    def test_record_without_a_raster_is_not_emitted(self):
        record = gate_snn_record()
        del record["raster"]
        self.assertIsNone(spike_probe.normalize_raster(record))


class LoadRasters(unittest.TestCase):
    def test_run_tree_loads_without_reading_any_prose(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            record = gate_snn_record()
            # Prose counts of the kind the probe must never depend on.
            record["language_view"]["description"] = (
                "The accept population fired 366 times against 301, margin 0.097."
            )
            write(root / "neuromorphic-event-language-bridge" / "batch-r01.jsonl", [record])
            rasters, problems = spike_probe.load_rasters([root])

        self.assertEqual(problems, [])
        self.assertEqual(len(rasters), 1)
        self.assertEqual(rasters[0]["spikes"], 123)
        self.assertNotIn("366", json.dumps(rasters[0]))

    def test_missing_and_broken_rasters_are_reported_as_problems(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            bare = gate_snn_record()
            bare["id"] = "no-raster"
            del bare["raster"]
            broken = gate_snn_record()
            broken["id"] = "bad-budget"
            broken["raster"]["spikes"] = 999
            write(
                root / "neuromorphic-event-language-bridge" / "batch-r01.jsonl",
                [gate_snn_record(), bare, broken],
            )
            rasters, problems = spike_probe.load_rasters([root])

        self.assertEqual(len(rasters), 1)
        self.assertEqual(
            [problem["record_id"] for problem in problems], ["no-raster", "bad-budget"]
        )
        self.assertEqual(problems[0]["reason_codes"], ["BRIDGE_RASTER_MISSING"])
        self.assertIn("BRIDGE_SPIKE_BUDGET_MISMATCH", problems[1]["reason_codes"])
        self.assertTrue(problems[0]["source"].endswith("batch-r01.jsonl:2"))

    def test_thalamic_records_with_rasters_are_loaded(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            record = gate_snn_record()
            record.pop("spike_events")
            record.pop("language_view")
            record.update(
                {
                    "state": {"sim_or_real": "designed"},
                    "proposed_action": {"action": "noop"},
                    "safety_decision": {"decision": "ACCEPT", "rationale": "fixture"},
                    "executed_action": {"action": "noop"},
                    "future_outcome": {"success": True},
                    "reward_components": {"total": 1.0},
                }
            )
            write(
                root / "thalamic-trajectory-factory" / "batch-r01.jsonl",
                [record],
            )
            rasters, problems = spike_probe.load_rasters([root])

        self.assertEqual(problems, [])
        self.assertEqual(len(rasters), 1)
        self.assertEqual(rasters[0]["spikes"], 123)

    def test_non_bridge_records_are_ignored(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            write(
                root / "thalamic-trajectory-factory" / "batch-r01.jsonl",
                [{"id": "t-1", "state": {"sim_or_real": "designed"}}],
            )
            rasters, problems = spike_probe.load_rasters([root])

        self.assertEqual((rasters, problems), ([], []))

    def test_unparsable_lines_are_reported_without_crashing_the_probe(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            path = root / "bridge" / "batch-r01.jsonl"
            path.parent.mkdir(parents=True)
            path.write_text(json.dumps(gate_snn_record()) + "\nnot json\n")
            rasters, problems = spike_probe.load_rasters([root])

        self.assertEqual(len(rasters), 1)
        self.assertEqual(len(problems), 1)
        self.assertEqual(problems[0]["scope"], "input")
        self.assertEqual(
            problems[0]["reason_codes"], ["BRIDGE_SOURCE_JSON_INVALID"]
        )

    def test_invalid_utf8_is_reported_as_an_input_problem(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "bridge.jsonl"
            path.write_bytes(b'{"id":"bad-\xff"}\n')

            rasters, problems = spike_probe.load_rasters([path])

        self.assertEqual(rasters, [])
        self.assertEqual(problems[0]["scope"], "input")
        self.assertEqual(
            problems[0]["reason_codes"], ["BRIDGE_SOURCE_UTF8_INVALID"]
        )


class ProbeCli(unittest.TestCase):
    def test_summary_counts_spikes_energy_and_gate_heads(self):
        stdout = io.StringIO()
        with redirect_stdout(stdout):
            code = spike_probe.main([str(GATE_SNN_FIXTURE)])
        report = json.loads(stdout.getvalue())

        self.assertEqual(code, 0)
        self.assertEqual(report["bridge_records"], 1)
        self.assertEqual(report["loaded"], 1)
        self.assertEqual(report["spikes"], 123)
        self.assertEqual(report["energy_pJ"], 123 * 23)
        self.assertEqual(report["routing_tables"], 1)
        self.assertEqual(report["third_factor_routes"], 1)
        self.assertEqual(report["gate_snn_records"], 1)

    def test_jsonl_mode_emits_one_loadable_raster_per_line(self):
        stdout = io.StringIO()
        with redirect_stdout(stdout):
            code = spike_probe.main(["--jsonl", str(GATE_SNN_FIXTURE)])
        lines = stdout.getvalue().splitlines()

        self.assertEqual(code, 0)
        self.assertEqual(len(lines), 1)
        self.assertEqual(json.loads(lines[0])["window_us"], 40000)

    def test_jsonl_mode_surfaces_unloadable_records_and_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            bare = gate_snn_record()
            del bare["raster"]
            write(root / "bridge" / "batch-r01.jsonl", [gate_snn_record(), bare])
            stdout = io.StringIO()
            stderr = io.StringIO()
            with redirect_stdout(stdout), redirect_stderr(stderr):
                code = spike_probe.main(["--jsonl", str(root)])

        loaded = [json.loads(line) for line in stdout.getvalue().splitlines()]
        problems = [json.loads(line) for line in stderr.getvalue().splitlines()]
        self.assertEqual(code, 1)
        self.assertEqual(len(loaded), 1)
        self.assertTrue(all("events" in raster for raster in loaded))
        self.assertEqual(len(problems), 1)
        self.assertTrue(problems[0]["unloadable"])
        self.assertIn("BRIDGE_RASTER_MISSING", problems[0]["reason_codes"])

    def test_strict_probe_rejects_routing_free_rasters(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            record = gate_snn_record()
            record["raster"]["routing"]["table"] = []
            write(root / "bridge" / "batch-r01.jsonl", [record])
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                code = spike_probe.main(["--strict", str(root)])
        report = json.loads(stdout.getvalue())
        self.assertEqual(code, 1)
        self.assertEqual(report["loaded"], 0)
        self.assertEqual(report["unloadable"], 1)

    def test_strict_probe_rejects_nonstandard_json_constants(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "bridge.jsonl"
            path.write_text('{"id":"nan-1","spike_events":[{"t_rel_ms":NaN}]}\n')
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                code = spike_probe.main(["--strict", str(path)])
        report = json.loads(stdout.getvalue())
        self.assertEqual(code, 1)
        self.assertEqual(report["input_errors"], 1)
        self.assertEqual(
            report["problems"][0]["reason_codes"], ["BRIDGE_SOURCE_JSON_INVALID"]
        )

    def test_strict_mode_fails_on_an_unloadable_raster(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            bare = gate_snn_record()
            del bare["raster"]
            write(root / "bridge" / "batch-r01.jsonl", [bare])
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                lenient = spike_probe.main([str(root)])
                strict = spike_probe.main(["--strict", str(root)])

        self.assertEqual(lenient, 0)
        self.assertEqual(strict, 1)

    def test_strict_mode_fails_on_missing_and_invalid_inputs(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            invalid = root / "invalid.jsonl"
            invalid.write_text("not json\n")
            missing = root / "missing.jsonl"
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                invalid_code = spike_probe.main(["--strict", str(invalid)])
                missing_code = spike_probe.main(["--strict", str(missing)])

        self.assertEqual(invalid_code, 1)
        self.assertEqual(missing_code, 1)


if __name__ == "__main__":
    unittest.main()
