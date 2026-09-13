#!/usr/bin/env python3
"""Finite-energy regressions for the SNN distillation raster loader."""

from __future__ import annotations

import io
import json
import math
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from fractions import Fraction
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "pipelines"))

import spike_probe  # noqa: E402
from spike_probe_test_helpers import gate_snn_record, write  # noqa: E402


class FiniteProbeEnergy(unittest.TestCase):
    """A normalized raster has to stay standards-compliant JSON.

    ``spike_probe --jsonl`` is the distillation loader's input, and this repo
    already refuses the non-standard ``Infinity``/``NaN`` tokens on the way in
    (``reject_json_constant``), so it must never emit one either.
    """

    def extreme_rate_record(self):
        """A schema-valid raster whose 23 pJ/spike product overflows a float."""

        record = gate_snn_record()
        raster = record["raster"]
        raster["window_ms"] = 50
        raster["window_s"] = 0.05
        raster["neurons"] = 1
        raster["mean_rate_hz"] = 1.7e308
        raster["spikes"] = round(Fraction(str(1.7e308)) * Fraction(str(0.05)))
        raster["excerpt"] = [{"t_us": 1000, "neuron_id": 0}]
        # No declared energy: the record is schema-valid, and only the derived
        # 23 pJ/spike product leaves the IEEE-754 double range.
        raster.pop("energy_pJ", None)
        raster.pop("energy_uJ", None)
        self.assertFalse(
            math.isfinite(float(raster["spikes"]) * spike_probe.RASTER_ENERGY_PJ_PER_SPIKE)
        )
        return record

    def test_derived_energy_is_exact_integer_picojoules(self):
        raster = spike_probe.normalize_raster(self.extreme_rate_record())

        self.assertIsNotNone(raster)
        self.assertIsInstance(raster["energy_pJ"], int)
        self.assertEqual(
            raster["energy_pJ"],
            raster["spikes"] * spike_probe.RASTER_ENERGY_PJ_PER_SPIKE,
        )

    def test_jsonl_output_never_emits_the_non_standard_infinity_token(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            write(root / "extreme.jsonl", [self.extreme_rate_record()])
            stdout = io.StringIO()
            with redirect_stdout(stdout), redirect_stderr(io.StringIO()):
                spike_probe.main(["--jsonl", str(root)])

        lines = [line for line in stdout.getvalue().splitlines() if line.strip()]
        self.assertEqual(len(lines), 1)
        self.assertNotIn("Infinity", lines[0])
        for line in lines:
            json.loads(line, parse_constant=spike_probe.reject_json_constant)

    def test_records_framed_only_by_line_feed_are_not_fragmented(self):
        """U+2028 inside a JSON string is payload, not a record terminator."""

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            record = gate_snn_record()
            record["bridge_notes"] = "line one\u2028line two"
            # ensure_ascii=False keeps U+2028 literal, exactly as a producer
            # that emits UTF-8 JSONL does.
            (root / "separators.jsonl").write_text(
                json.dumps(record, ensure_ascii=False) + "\n", encoding="utf-8"
            )
            stdout = io.StringIO()
            with redirect_stdout(stdout), redirect_stderr(io.StringIO()):
                code = spike_probe.main(["--strict", str(root)])

        report = json.loads(stdout.getvalue())
        self.assertEqual(code, 0)
        self.assertEqual(report["loaded"], 1)
        self.assertEqual(report["input_errors"], 0)

    def test_bare_carriage_return_is_not_treated_as_a_jsonl_record_boundary(self):
        first = json.dumps(gate_snn_record()).encode("utf-8")
        second_record = gate_snn_record()
        second_record["id"] = "bridge-gate-snn-fixture-002"
        second = json.dumps(second_record).encode("utf-8")

        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "bare-cr.jsonl"
            path.write_bytes(first + b"\r" + second)
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                code = spike_probe.main(["--strict", str(path)])

        report = json.loads(stdout.getvalue())
        self.assertEqual(code, 1)
        self.assertEqual((report["loaded"], report["input_errors"]), (0, 1))

    def test_crlf_remains_a_valid_physical_jsonl_delimiter(self):
        first = json.dumps(gate_snn_record()).encode("utf-8")
        second_record = gate_snn_record()
        second_record["id"] = "bridge-gate-snn-fixture-002"
        second = json.dumps(second_record).encode("utf-8")

        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "crlf.jsonl"
            path.write_bytes(first + b"\r\n" + second + b"\r\n")
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                code = spike_probe.main(["--strict", str(path)])

        report = json.loads(stdout.getvalue())
        self.assertEqual(code, 0)
        self.assertEqual((report["loaded"], report["input_errors"]), (2, 0))


if __name__ == "__main__":
    unittest.main()
