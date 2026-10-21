"""Harness report parsing and coded launch failures."""

import sys
import unittest
from pathlib import Path
from unittest import mock

REPO = Path(__file__).resolve().parents[1]
PIPELINES = REPO / "pipelines"
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(PIPELINES))

PRODUCED_AT = "2026-10-20T23:00:00Z"

import honest_stop.vocabulary as cv
from honest_stop import harness


def _flags() -> tuple[str, ...]:
    return harness.INTERPRETER_FLAGS


class HarnessTests(unittest.TestCase):
    def test_reports_and_timeouts_are_coded_refusals(self):
        self.assertIn("-S", _flags())
        self.assertEqual(
            harness.run_gate(b"x" * (cv.MAX_RECORD_BYTES + 1)).code, "record.too_large"
        )
        self.assertEqual(harness._parse(None).code, "harness.timeout")
        self.assertEqual(harness._parse(b"noise\n").code, "harness.report")
        marker = cv.GATE_MARKER
        doubled = f"{marker}{{}}\n{marker}{{}}\n".encode()
        self.assertEqual(harness._parse(doubled).code, "harness.report")
        self.assertEqual(harness._parse(f"{marker}{{\n".encode()).code, "harness.report")
        with mock.patch("honest_stop.harness.load_strict_json", side_effect=RecursionError):
            self.assertEqual(harness._parse(f"{marker}{{}}\n".encode()).code, "harness.report")
        self.assertEqual(harness._from_report([]).code, "harness.report")
        self.assertEqual(
            harness._from_report({"protocol": "other", "accepted": False, "code": "x"}).code,
            "harness.report",
        )
        self.assertEqual(
            harness._from_report({"protocol": cv.GATE_PROTOCOL, "accepted": False, "code": 1}).code,
            "harness.report",
        )
        inconsistent = {
            "protocol": cv.GATE_PROTOCOL,
            "accepted": True,
            "code": "nope",
            "measured_blocker": True,
            "counterfactual_holds": False,
        }
        self.assertEqual(harness._from_report(inconsistent).code, "harness.report")

    def test_optional_fields_and_consistent_pass(self):
        self.assertIn("-S", _flags())
        partial = {
            "protocol": cv.GATE_PROTOCOL,
            "accepted": False,
            "code": "result.forged_blocker",
            "measured_blocker": "yes",
            "counterfactual_holds": 1,
        }
        parsed = harness._from_report(partial)
        self.assertIsNone(parsed.measured_blocker)
        self.assertIsNone(parsed.counterfactual_holds)
        self.assertIsNone(harness._optional_bool(None))
        self.assertTrue(harness._optional_bool(True))
        passed = {
            "protocol": cv.GATE_PROTOCOL,
            "accepted": True,
            "code": cv.CODE_OK,
            "measured_blocker": True,
            "counterfactual_holds": False,
        }
        self.assertTrue(harness._from_report(passed).accepted)
        self.assertFalse(
            harness._consistent(
                {
                    "accepted": True,
                    "code": cv.CODE_OK,
                    "measured_blocker": False,
                    "counterfactual_holds": False,
                }
            )
        )
        self.assertFalse(
            harness._consistent(
                {
                    "accepted": True,
                    "code": cv.CODE_OK,
                    "measured_blocker": True,
                    "counterfactual_holds": True,
                }
            )
        )
        self.assertTrue(harness._consistent({"accepted": False}))

    def test_launch_failures_become_harness_unavailable(self):
        self.assertIn("-S", _flags())

        class _Timeout:
            pid = 424242

            def wait(self, timeout=None):
                raise harness.subprocess.TimeoutExpired("child", 1)

        with mock.patch("honest_stop.harness.os.killpg", side_effect=ProcessLookupError):
            self.assertTrue(harness._wait(_Timeout(), 0.01))
        with mock.patch("honest_stop.harness.os.killpg", side_effect=PermissionError):
            self.assertTrue(harness._wait(_Timeout(), 0.01))
        with (
            mock.patch("honest_stop.harness.subprocess.Popen", return_value=mock.Mock()),
            mock.patch("honest_stop.harness._wait", return_value=True),
        ):
            self.assertIsNone(harness._launch(b"{}", 0.1))
        with mock.patch(
            "honest_stop.harness.tempfile.TemporaryDirectory", side_effect=OSError("full")
        ):
            self.assertEqual(harness.run_gate(b"{}").code, "harness.unavailable")
        with mock.patch("honest_stop.harness.Path.write_bytes", side_effect=OSError("full")):
            self.assertEqual(harness.run_gate(b"{}").code, "harness.unavailable")
