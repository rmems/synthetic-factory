#!/usr/bin/env python3
"""The out-of-band harness limits attestation protocol and inherited report fd."""

import io
import json
import os
import resource
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))

from code_repair_test_support import executor as ex, vocabulary as cv  # noqa: E402
from code_repair import _harness as harness  # noqa: E402


class LimitsAttestation(unittest.TestCase):
    """Issue #213: out-of-band attestation parse, write, and in-process main paths."""

    def test_parent_and_child_share_the_attestation_constants(self):
        self.assertEqual(ex.LIMITS_ATTESTATION_PREFIX, harness.LIMITS_ATTESTATION_PREFIX)
        self.assertEqual(ex.REPORT_FD_ENV, harness.REPORT_FD_ENV)
        self.assertEqual(cv.HARNESS_PROTOCOL, harness.PROTOCOL)
        self.assertTrue(callable(harness._write_protocol_report))

    def test_limits_attested_rejects_empty_missing_and_malformed_lines(self):
        cases = (
            (b"", "empty stdout"),
            (b"no-newline", "missing limits attestation line"),
            (b'{"protocol": "x"}\n', "missing limits attestation line"),
            (f"{ex.LIMITS_ATTESTATION_PREFIX}yes\n{{}}".encode(), "limits attestation malformed"),
            (ex.LIMITS_ATTESTATION_PREFIX.encode() + b"\xff\n", "limits attestation malformed"),
        )
        for stdout, detail in cases:
            with self.subTest(stdout=stdout[:40]):
                self.assertEqual(ex._limits_attested(stdout), detail)

    def test_limits_attested_accepts_true_and_false_tokens(self):
        for token, expected in ((str(True).lower(), True), (str(False).lower(), False)):
            with self.subTest(token=token):
                stdout = f"{ex.LIMITS_ATTESTATION_PREFIX}{token}\n".encode()
                self.assertIs(ex._limits_attested(stdout), expected)

    def test_limit_setup_errors_attest_unavailable_instead_of_raising(self):
        self.assertIs(harness._apply_limits({}), False)
        spec = {"cpu_seconds": 1, "address_space_bytes": 1024, "file_size_bytes": 1024}
        with mock.patch.object(resource, "setrlimit", side_effect=OSError("denied")):
            self.assertIs(harness._apply_limits(spec), False)

    def test_harness_writes_attestation_before_any_program_load(self):
        buffer = io.StringIO()
        harness._write_limits_attestation(buffer, True)
        harness._write_limits_attestation(buffer, False)
        self.assertEqual(
            buffer.getvalue(),
            f"{harness.LIMITS_ATTESTATION_PREFIX}{str(True).lower()}\n"
            f"{harness.LIMITS_ATTESTATION_PREFIX}{str(False).lower()}\n",
        )

    def test_run_executes_only_when_limits_were_applied(self):
        text = "def f(n):\n    return n\n"
        spec = {
            "function": "f", "run_public": False,
            "cases": [{"args": "(1,)", "want": "1"}],
            "float_rel_tol": 1e-9, "float_abs_tol": 1e-12,
        }
        with tempfile.TemporaryDirectory() as root:
            directory = Path(root)
            (directory / harness.PROGRAM_FILENAME).write_text(text, encoding="utf-8")
            ok = harness._run(directory, spec, limits_applied=True)
            denied = harness._run(directory, spec, limits_applied=False)
        self.assertEqual(ok["load"]["status"], "ok")
        self.assertTrue(ok["environment"]["limits_applied"])
        self.assertEqual(ok["hidden"][0]["status"], "pass")
        self.assertEqual(denied["load"]["status"], "error")
        self.assertFalse(denied["environment"]["limits_applied"])

    def _run_main(self, workdir: Path, *, limits_applied: bool) -> tuple[int, str, dict]:
        stdout = io.StringIO()
        report_file = tempfile.TemporaryFile()
        self.addCleanup(report_file.close)
        with mock.patch.object(harness, "_apply_limits", return_value=limits_applied), \
                mock.patch.object(os, "dup2", spec=os.dup2), \
                mock.patch.object(sys, "stdout", stdout), \
                mock.patch.object(sys, "stderr", io.StringIO()), \
                mock.patch.object(harness, "_ATEXIT_CLEAR"), \
                mock.patch.dict(os.environ, {harness.REPORT_FD_ENV: str(report_file.fileno())}):
            code = harness.main(["_harness.py", str(workdir)])
        report_file.seek(0)
        body = json.loads(report_file.read().decode("utf-8"))
        return code, stdout.getvalue(), body

    def test_main_attests_true_and_writes_the_report_on_the_inherited_fd(self):
        text = "def f(n):\n    return n\n"
        job = ex.Job("main:test", text, "f", ({"args": "(1,)", "want": "1"},), False)
        with tempfile.TemporaryDirectory() as root:
            workdir = Path(root)
            (workdir / harness.PROGRAM_FILENAME).write_text(text, encoding="utf-8")
            (workdir / "spec.json").write_text(json.dumps(ex.Executor(timeout_s=3).spec(job)))
            code, attested, body = self._run_main(workdir, limits_applied=True)
        self.assertEqual(code, 0)
        self.assertEqual(attested, f"{harness.LIMITS_ATTESTATION_PREFIX}true\n")
        self.assertEqual(body["protocol"], harness.PROTOCOL)
        self.assertEqual(body["load"]["status"], "ok")

    def test_main_attests_false_when_spec_is_unreadable(self):
        with tempfile.TemporaryDirectory() as root:
            workdir = Path(root)
            (workdir / "spec.json").write_text("not json", encoding="utf-8")
            code, attested, body = self._run_main(workdir, limits_applied=False)
        self.assertEqual(code, 0)
        self.assertEqual(attested, f"{harness.LIMITS_ATTESTATION_PREFIX}false\n")
        self.assertEqual(body["load"]["status"], "error")
        self.assertIn("SANDBOX_UNAVAILABLE", body["load"]["error"])

    def test_main_names_exception_types_and_preserves_attestation(self):
        """Both ordinary and empty-message crashes preserve actionable diagnostics."""

        for error in (RuntimeError("boom"), MemoryError()):
            with self.subTest(error=type(error).__name__):
                with tempfile.TemporaryDirectory() as root:
                    workdir = Path(root)
                    (workdir / "spec.json").write_text("{}", encoding="utf-8")
                    with mock.patch.object(harness, "_run", side_effect=error):
                        code, attested, body = self._run_main(workdir, limits_applied=True)
                self.assertEqual(code, 0)
                self.assertEqual(attested, f"{harness.LIMITS_ATTESTATION_PREFIX}true\n")
                self.assertNotIn("environment", body)
                self.assertEqual(body["load"]["status"], "error")
                self.assertIn(f"HarnessError: {type(error).__name__}: {error}", body["load"]["error"])

    def test_main_usage_error_is_exit_two(self):
        stderr = io.StringIO()
        with mock.patch.object(sys, "stderr", stderr):
            self.assertEqual(harness.main(["_harness.py"]), 2)
        self.assertIn("usage:", stderr.getvalue())

    def test_write_protocol_report_round_trips_sorted_json(self):
        with tempfile.TemporaryFile() as report_file, mock.patch.object(
            harness, "_ATEXIT_CLEAR"
        ) as clearer:
            with mock.patch.dict(os.environ, {harness.REPORT_FD_ENV: str(report_file.fileno())}):
                harness._write_protocol_report({"z": 1, "a": 2}, json.dumps)
            report_file.seek(0)
            self.assertEqual(report_file.read(), b'{"a": 2, "z": 1}')
            clearer.assert_called_once()


if __name__ == "__main__":
    unittest.main()
