#!/usr/bin/env python3
"""VSET fail-closed hygiene (#154). FailClosedHygieneTests stay here."""

from __future__ import annotations

import io
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

_TESTS = Path(__file__).resolve().parent
if str(_TESTS) not in sys.path:
    sys.path.insert(0, str(_TESTS))

from vset_testutil import (  # noqa: E402
    ACCEPT,
    PACK,
    codes as _codes,
    load_record as _load,
    vset,
)


class FailClosedHygieneTests(unittest.TestCase):
    """Smallest proofs for the five existing split-module holes."""

    def test_non_object_required_role_is_rejected(self):
        record = _load(ACCEPT / "issue-patch-validated.json")
        record["task_author"] = "fixture-author"
        self.assertIn("vset.actor_fields_invalid", _codes(vset.validate_record(record)))
        record = _load(ACCEPT / "issue-patch-validated.json")
        record["solver"] = ["not-an-object"]
        self.assertIn("vset.actor_fields_invalid", _codes(vset.validate_record(record)))

    def test_reference_tests_parent_path_is_rejected(self):
        record = _load(ACCEPT / "provisional.json")
        record["oracle"]["reference_tests"] = ["../outside.py"]
        errors, execution = vset.validate_record_with_oracle(record, PACK)
        self.assertIn("vset.oracle_execution_mismatch", _codes(errors))
        self.assertIsNone(execution)
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            (work / "tests").mkdir()
            with self.assertRaises(vset.VSetValidationError) as ctx:
                vset._load_tests(work, "../outside.py")
            self.assertEqual(ctx.exception.code, "vset.oracle_execution_mismatch")

    def test_oracle_does_not_leak_a_non_counter_pack_module(self):
        with tempfile.TemporaryDirectory() as tmp:
            pack = Path(tmp)
            (pack / "src").mkdir()
            (pack / "tests").mkdir()
            (pack / "src" / "other_mod.py").write_text("VALUE = 1\n")
            (pack / "tests" / "probe.py").write_text(
                "import unittest\nimport other_mod\n\n"
                "class Probe(unittest.TestCase):\n"
                "    def test_value(self):\n"
                "        self.assertEqual(other_mod.VALUE, 1)\n"
            )
            self.assertNotIn("other_mod", sys.modules)
            report = vset.run_oracle(pack, reference_tests=["tests/probe.py"])
            self.assertTrue(report["reference"]["ok"])
            self.assertNotIn("other_mod", sys.modules)
            self.assertFalse(
                any(name.startswith("vset_oracle_tests_") for name in sys.modules)
            )

    def test_empty_or_all_skipped_suite_is_not_ok(self):
        with tempfile.TemporaryDirectory() as tmp:
            pack = Path(tmp)
            (pack / "src").mkdir()
            (pack / "tests").mkdir()
            (pack / "tests" / "empty.py").write_text("# no tests\n")
            (pack / "tests" / "skipped.py").write_text(
                "import unittest\n\n"
                "class Skipped(unittest.TestCase):\n"
                "    @unittest.skip('skip')\n"
                "    def test_x(self):\n"
                "        self.assertTrue(True)\n"
            )
            empty = vset.run_oracle(pack, reference_tests=["tests/empty.py"])
            self.assertFalse(empty["reference"]["ok"])
            skipped = vset.run_oracle(pack, reference_tests=["tests/skipped.py"])
            self.assertFalse(skipped["reference"]["ok"])

    def test_oracle_cli_forwards_require_registry_sha(self):
        path = ACCEPT / "issue-patch-validated.json"
        stdout = io.StringIO()
        stderr = io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            code = vset.main(
                [
                    "--oracle",
                    "--pack",
                    str(PACK),
                    "--require-registry-sha",
                    str(path),
                ]
            )
        self.assertEqual(code, 1)
        self.assertIn("vset.release_contract_mismatch", stderr.getvalue())
        errors, _execution = vset.validate_record_with_oracle(
            _load(path), PACK, require_registry_sha=True
        )
        self.assertIn("vset.release_contract_mismatch", _codes(errors))


if __name__ == "__main__":
    unittest.main()
