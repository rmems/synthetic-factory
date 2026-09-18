#!/usr/bin/env python3
"""Byte-identical golden reports for the validate_run CLI.

Each case under tests/fixtures/validate-run-golden/ pins stdout, stderr, and
the exit code of a direct ``python3 pipelines/validate_run.py`` invoke. The
valid, malformed, provenance, safety, reward, and spike cases are single
JSONL files; mini-run is the mixed committed fixture tree.
"""

import shutil
import sys
import tempfile
import unittest
from pathlib import Path

_TESTS = Path(__file__).resolve().parent
if str(_TESTS) not in sys.path:
    sys.path.insert(0, str(_TESTS))

from validate_run_test_helpers import REPO, _invoke, _invoke_module  # noqa: E402

GOLDEN = _TESTS / "fixtures" / "validate-run-golden"
SINGLE_CASES = ("valid", "malformed", "provenance", "safety", "reward", "spike")
MINI_RUN = _TESTS / "fixtures" / "mini-run"


def _read_expected(case):
    root = GOLDEN / case
    return (
        (root / "expected.stdout").read_text(),
        (root / "expected.stderr").read_text(),
        int((root / "expected.exit").read_text().strip()),
    )


def _assert_result(test, result, expected):
    expected_stdout, expected_stderr, expected_exit = expected
    test.assertEqual(result.returncode, expected_exit, result.stderr)
    test.assertEqual(result.stdout, expected_stdout)
    test.assertEqual(result.stderr, expected_stderr)


class ValidateRunGoldenReports(unittest.TestCase):
    def _run_single_case(self, case, invoker):
        expected = _read_expected(case)
        with tempfile.TemporaryDirectory() as raw:
            run_dir = Path(raw) / "run"
            run_dir.mkdir()
            shutil.copy(GOLDEN / case / "records.jsonl", run_dir / "records.jsonl")
            result = invoker(str(run_dir))
        _assert_result(self, result, expected)

    def test_direct_cli_matches_golden_reports(self):
        for case in SINGLE_CASES:
            with self.subTest(case=case):
                self._run_single_case(case, _invoke)

    def test_direct_cli_matches_mini_run_golden(self):
        expected = _read_expected("mini-run")
        result = _invoke(str(MINI_RUN))
        _assert_result(self, result, expected)

    def test_package_module_cli_matches_direct_cli(self):
        with tempfile.TemporaryDirectory() as raw:
            run_dir = Path(raw) / "run"
            run_dir.mkdir()
            shutil.copy(GOLDEN / "valid" / "records.jsonl", run_dir / "records.jsonl")
            direct = _invoke(str(run_dir))
            packaged = _invoke_module(str(run_dir))
        self.assertEqual(direct.returncode, packaged.returncode)
        self.assertEqual(direct.stdout, packaged.stdout)
        self.assertEqual(direct.stderr, packaged.stderr)
        self.assertEqual(direct.returncode, 0, packaged.stderr)

    def test_package_module_cli_matches_reward_golden(self):
        expected = _read_expected("reward")
        with tempfile.TemporaryDirectory() as raw:
            run_dir = Path(raw) / "run"
            run_dir.mkdir()
            shutil.copy(GOLDEN / "reward" / "records.jsonl", run_dir / "records.jsonl")
            result = _invoke_module(str(run_dir))
        _assert_result(self, result, expected)


class ValidateRunGoldenFixturesExist(unittest.TestCase):
    def test_golden_cases_cover_the_required_shapes(self):
        self.assertEqual(
            set(SINGLE_CASES) | {"mini-run"},
            {path.name for path in GOLDEN.iterdir() if path.is_dir()},
        )
        self.assertTrue(REPO.joinpath("pipelines", "validate_run.py").is_file())


if __name__ == "__main__":
    unittest.main()
