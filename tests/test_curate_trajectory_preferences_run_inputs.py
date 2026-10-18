"""``_run_command`` narrows its confined paths in main's order: output, manifest, source."""

import argparse
import contextlib
import io
import shutil
import tempfile
import unittest
from pathlib import Path

from pipelines import curate_trajectory_preferences as ctp

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "grok-trajectory-preferences"
RAW_OUTPUT = Path("outputs/raw/o.jsonl")


def _args(command: str) -> argparse.Namespace:
    return argparse.Namespace(command=command, json=False, enforce_outcome_agreement=False)


class RunCommandInputs(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="ctp-inputs-"))
        self.addCleanup(shutil.rmtree, self.root, True)
        self.output = self.root / "out.jsonl"
        self.manifest = self.root / "manifest.json"

    def _refusal(self, expected: type[Exception], command: str, inputs: ctp.Inputs) -> str:
        args = _args(command)
        with self.assertRaises(expected) as caught:
            ctp._run_command(args, inputs)
        return str(caught.exception)

    def test_a_missing_required_path_is_named_in_check_order(self):
        cases = {
            "output": ctp.Inputs(FIXTURE, None, self.manifest),
            "manifest": ctp.Inputs(FIXTURE, self.output, None),
            "source": ctp.Inputs(None, self.output, self.manifest),
        }
        for argument, inputs in cases.items():
            with self.subTest(argument=argument):
                message = self._refusal(TypeError, "curate", inputs)
                self.assertEqual(message, f"{argument} must be a path, not None")
        message = self._refusal(TypeError, "curate", ctp.Inputs(None, None, None))
        self.assertEqual(message, "output must be a path, not None")
        message = self._refusal(TypeError, "scan", ctp.Inputs(None, None, None))
        self.assertEqual(message, "source must be a path, not None")

    def test_raw_destination_refusal_still_precedes_later_missing_paths(self):
        inputs = ctp.Inputs(None, RAW_OUTPUT, None)
        message = self._refusal(ctp.TrajectoryCurationError, "curate", inputs)
        self.assertEqual(message, f"output must not be written under outputs/raw/: {RAW_OUTPUT}")
        self.assertFalse(self.output.exists())

    def test_scan_needs_no_destinations_and_curate_writes_both(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            self.assertIsNone(ctp._run_command(_args("scan"), ctp.Inputs(FIXTURE, None, None)))
        self.assertIn("Trajectory pairs considered: 2", out.getvalue())
        with contextlib.redirect_stdout(io.StringIO()):
            ctp._run_command(_args("curate"), ctp.Inputs(FIXTURE, self.output, self.manifest))
        self.assertTrue(self.output.is_file())
        self.assertTrue(self.manifest.is_file())


if __name__ == "__main__":
    unittest.main()
