"""A scenario-bound capture must never be reused across the entire catalog."""

from contextlib import redirect_stderr, redirect_stdout
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

import test_hardware_parity_capture as capture_tests  # noqa: E402

import hardware_parity as hp  # noqa: E402
import hardware_parity_cli as cli  # noqa: E402


class CaptureSelection(unittest.TestCase):
    def _invoke(self, arguments):
        stdout, stderr = io.StringIO(), io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            code = cli.main(arguments)
        return code, stdout.getvalue(), stderr.getvalue()

    def _capture(self, directory):
        scenario = hp.build_scenarios(steps=6)[0]
        adapter = capture_tests.RecordedCapturePath()._capture_adapter(directory, scenario)
        return scenario, adapter.capture_path

    def test_capture_requires_explicit_scenario_before_writing(self):
        with tempfile.TemporaryDirectory() as directory:
            _, capture = self._capture(directory)
            output = Path(directory) / "output"
            code, _, error = self._invoke(["generate", str(output), "--capture", str(capture), "--steps", "6"])
            self.assertEqual(code, 2)
            self.assertIn("--scenario", error)
            self.assertFalse(output.exists())

    def test_selected_capture_emits_one_valid_diagnostic_not_a_complete_round(self):
        with tempfile.TemporaryDirectory() as directory:
            scenario, capture = self._capture(directory)
            output = Path(directory) / "output"
            code, stdout, error = self._invoke([
                "generate", str(output), "--capture", str(capture), "--steps", "6",
                "--scenario", scenario["id"],
            ])
            self.assertEqual(code, 0, error)
            summary = json.loads(stdout)
            self.assertEqual(summary["scope"], "single_scenario")
            self.assertFalse(summary["complete_catalog_round"])
            self.assertEqual(summary["scenario"], scenario["id"])
            path = Path(summary["written"])
            self.assertTrue(path.name.startswith("scenario-"))
            records = [json.loads(line) for line in path.read_text().splitlines()]
            self.assertEqual(len(records), 1)
            self.assertEqual(records[0]["scenario"]["id"], scenario["id"])
            self.assertEqual(hp.validate_records(records), [])
            self.assertIsNotNone(records[0]["oracle"]["deployment"])
            self.assertIn("PHYSICAL_EXECUTION_UNATTESTED", records[0]["result"]["reason_codes"])
            _, errors = hp.build_training_views(records)
            self.assertTrue(any("catalog" in error for error in errors))

    def test_capture_for_a_different_scenario_refuses_without_output(self):
        with tempfile.TemporaryDirectory() as directory:
            _, capture = self._capture(directory)
            output = Path(directory) / "output"
            other = hp.build_scenarios(steps=6)[1]["id"]
            code, _, error = self._invoke([
                "generate", str(output), "--capture", str(capture), "--steps", "6",
                "--scenario", other,
            ])
            self.assertEqual(code, 1)
            self.assertIn("CAPTURE_INPUT_FIXTURE_MISMATCH", error)
            self.assertFalse(output.exists())

    def test_selected_reference_keeps_default_environment_independence(self):
        expected = hp.generate_records(steps=6)[0]
        ambient = {"SPIKENAUT_FPGA_DEVICE": "/dev/unrelated-test-board",
                   "SPIKENAUT_FPGA_BITSTREAM": "/nonexistent/test-bitstream.bin"}
        with tempfile.TemporaryDirectory() as directory, mock.patch.dict("os.environ", ambient):
            code, stdout, error = self._invoke([
                "generate", directory, "--scenario", expected["scenario"]["id"], "--steps", "6",
            ])
            self.assertEqual(code, 0, error)
            actual = json.loads(Path(json.loads(stdout)["written"]).read_text())
        self.assertEqual(actual, expected)
