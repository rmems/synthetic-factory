#!/usr/bin/env python3
"""check_records.py's robustness to malformed input, and its CLI surface.

Unknown shapes, JSON parse errors, non-standard JSON numeric constants
(NaN/Infinity), and invalid UTF-8 must all report as findings, never as a
traceback — the run tree is untrusted generated output. CheckRecordsCli
locks the --strict exit-code contract and confirms the checker never
writes into the run directory it is scanning.
"""

import json
import sys
import tempfile
import unittest
from pathlib import Path

_TESTS = Path(__file__).resolve().parent
if str(_TESTS) not in sys.path:
    sys.path.insert(0, str(_TESTS))

from check_records_test_helpers import (  # noqa: E402
    FIXTURES,
    _cli,
    _run_dir,
    _thalamic,
)

import check_records  # noqa: E402


class CheckRecordsParsingRobustness(unittest.TestCase):
    def test_unknown_shape_is_error(self):
        tmp, run_dir = _run_dir([{"hello": "world", "not": "a factory record"}])
        with tmp:
            result = check_records.check_run(run_dir)
        blob = "\n".join(result["errors"])
        self.assertIn("unrecognized record shape", blob)
        self.assertIn("batch.jsonl:1", blob)
        self.assertEqual(result["exit_code"], 1)

    def test_json_parse_error(self):
        tmp = tempfile.TemporaryDirectory()
        with tmp:
            (Path(tmp.name) / "broken.jsonl").write_text("{not json\n")
            result = check_records.check_run(tmp.name)
        self.assertTrue(any("JSON parse" in e for e in result["errors"]))
        self.assertEqual(result["exit_code"], 1)

    def test_nonstandard_json_numeric_constants_are_parse_errors(self):
        template = json.dumps(_thalamic()).replace(
            '"domain": "test"',
            '"domain": "test", "measurement": CONSTANT',
        )
        for constant in ("NaN", "Infinity", "-Infinity"):
            with self.subTest(constant=constant), tempfile.TemporaryDirectory() as td:
                path = Path(td) / "nonstandard-number.jsonl"
                path.write_text(template.replace("CONSTANT", constant) + "\n")

                result = check_records.check_run(td)

                self.assertEqual(result["exit_code"], 1)
                self.assertTrue(
                    any(
                        f"non-standard JSON numeric constant {constant}" in error
                        for error in result["errors"]
                    ),
                    result,
                )

    def test_invalid_utf8_is_error_not_traceback(self):
        with tempfile.TemporaryDirectory() as td:
            (Path(td) / "bad.jsonl").write_bytes(b'{"id":"bad-\xff"}\n')
            result = check_records.check_run(td)
        self.assertEqual(result["exit_code"], 1)
        self.assertIn("invalid UTF-8", "\n".join(result["errors"]))



class CheckRecordsCli(unittest.TestCase):
    def test_does_not_write_into_run_dir(self):
        rec = _thalamic()
        tmp, run_dir = _run_dir([rec])
        with tmp:
            before = {p.name for p in run_dir.iterdir()}
            result = check_records.check_run(run_dir)
            after = {p.name for p in run_dir.iterdir()}
        self.assertEqual(before, after)
        self.assertNotIn("manifest.json", after)
        self.assertEqual(result["exit_code"], 0)

    def test_cli_strict_and_exit_codes(self):
        rec = _thalamic()
        rec["state"] = {"domain": "no-sim"}
        tmp, run_dir = _run_dir([rec])
        with tmp:
            loose = _cli([str(run_dir)])
            strict = _cli(["--strict", str(run_dir)])
        self.assertEqual(loose.returncode, 0, loose.stderr)
        self.assertEqual(strict.returncode, 1, strict.stderr)
        self.assertIn("WARNING", loose.stderr)
        self.assertIn("sim_or_real", loose.stderr)

    def test_cli_fixture_dir_exits_1(self):
        proc = _cli([str(FIXTURES)])
        self.assertEqual(proc.returncode, 1, proc.stderr)
        self.assertIn("ERROR", proc.stderr)


if __name__ == "__main__":
    unittest.main()
