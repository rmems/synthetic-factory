#!/usr/bin/env python3
"""Exit and stream translation tests for the in-process gate runner."""

import sys
import unittest
from pathlib import Path

PIPELINES = Path(__file__).resolve().parents[1] / "pipelines"
if str(PIPELINES) not in sys.path:
    sys.path.insert(0, str(PIPELINES))

import curate_gate_gates  # noqa: E402


class RunToolTests(unittest.TestCase):
    def test_audit_examples_accept_non_sliceable_iterables(self):
        report = {
            "exact_duplicates": {"duplicate-a", "duplicate-b"},
            "identity": {
                "duplicates": iter(("id-a", "id-b")),
                "missing_top_level": 1,
                "missing_examples": iter(("missing-a",)),
            },
        }
        log = curate_gate_gates._GateLog({}, [])

        curate_gate_gates._audit_gates(report, log)

        self.assertEqual(
            log.gates["exact_duplicates"]["examples"], ["duplicate-a", "duplicate-b"]
        )
        self.assertEqual(log.gates["canonical_id_collisions"]["examples"], ["id-a", "id-b"])
        self.assertEqual(log.gates["canonical_id_coverage"]["examples"], ["missing-a"])

    def test_a_returning_main_reports_exit_zero(self):
        code, err = curate_gate_gates._run_tool(lambda argv: None, ["x"])
        self.assertEqual((code, err), (0, ""))

    def test_a_returned_nonzero_code_is_the_gate_exit_code(self):
        code, err = curate_gate_gates._run_tool(lambda argv: 2, ["x"])
        self.assertEqual((code, err), (2, ""))

    def test_system_exit_code_is_the_gate_exit_code(self):
        def main(argv):
            raise SystemExit(2)

        code, err = curate_gate_gates._run_tool(main, ["x"])
        self.assertEqual((code, err), (2, ""))

    def test_bare_system_exit_reports_exit_zero(self):
        def main(argv):
            raise SystemExit

        code, err = curate_gate_gates._run_tool(main, ["x"])
        self.assertEqual((code, err), (0, ""))

    def test_non_int_system_exit_prints_the_code_to_stderr(self):
        def main(argv):
            raise SystemExit("bad argv")

        code, err = curate_gate_gates._run_tool(main, ["x"])
        self.assertEqual(code, 1)
        self.assertEqual(err, "bad argv\n")

    def test_a_validator_crash_fails_closed_with_a_traceback(self):
        def main(argv):
            raise RuntimeError("boom")

        code, err = curate_gate_gates._run_tool(main, ["x"])
        self.assertEqual(code, 1)
        self.assertIn("Traceback", err)
        self.assertIn("RuntimeError: boom", err)

    def test_stderr_is_captured_and_stdout_is_swallowed(self):
        def main(argv):
            print("stdout noise")
            print("ERROR: line", file=sys.stderr)

        code, err = curate_gate_gates._run_tool(main, ["x"])
        self.assertEqual((code, err), (0, "ERROR: line\n"))


if __name__ == "__main__":
    unittest.main()
