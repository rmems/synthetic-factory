#!/usr/bin/env python3
"""Oracle trust-boundary tests (#154).

A candidate patch must not be able to rewrite the suite that judges it,
and a forged result hash must not become validated evidence.
"""

from __future__ import annotations

import shutil
import sys
import tempfile
import unittest
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


def _passing_suite(name: str = "tests.reference") -> str:
    return (
        "import unittest\n"
        f"class {name.split('.')[-1].title().replace('_', '')}(unittest.TestCase):\n"
        "    def test_trivial(self) -> None:\n"
        "        self.assertTrue(True)\n"
    )


class OracleTrustBoundaryTests(unittest.TestCase):
    def test_patch_rejects_suite_pack_and_escape_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            (work / "src").mkdir()
            (work / "tests").mkdir()
            (work / "src" / "app.py").write_text("VALUE = 1\n", encoding="utf-8")
            cases = {
                "tests/reference.py": "tests/",
                "tests/hidden.py": "tests/",
                "PACK.json": "PACK.json",
                "": "empty",
                ".": "directory",
                "src": "directory",
                "/var/abs.py": "absolute",
                "../escape.py": "..",
            }
            for relative in cases:
                with self.subTest(relative=relative):
                    with self.assertRaises(vset.VSetValidationError) as ctx:
                        vset.apply_patch(work, {"files": {relative: "x = 1\n"}})
                    self.assertEqual(ctx.exception.code, "vset.payload_invalid")
            vset.apply_patch(work, {"files": {"src/app.py": "VALUE = 2\n"}})
            self.assertEqual(
                (work / "src" / "app.py").read_text(encoding="utf-8"), "VALUE = 2\n"
            )

    def test_hidden_suite_runs_from_a_copy_the_patch_cannot_touch(self) -> None:
        record = _load(ACCEPT / "issue-patch-validated.json")
        record["payload"]["patch"] = {
            "files": {"tests/reference.py": _passing_suite("Forged")}
        }
        errors, execution = vset.validate_record_with_oracle(record, PACK)
        self.assertIn("vset.payload_invalid", _codes(errors))
        self.assertIsNone(execution)
        original = (PACK / "tests" / "reference.py").read_text(encoding="utf-8")
        self.assertNotIn("Forged", original)

    def test_broken_implementation_plus_forged_hash_is_not_validated(self) -> None:
        record = _load(ACCEPT / "issue-patch-validated.json")
        record["payload"]["patch"] = {"files": {"src/counter.py": "def add(a, b):\n    raise RuntimeError('broken')\n"}}
        record["oracle"]["result_hash"] = "sha256:" + ("ab" * 32)
        errors, execution = vset.validate_record_with_oracle(record, PACK)
        self.assertIn("vset.oracle_execution_mismatch", _codes(errors))
        self.assertNotIn("validated-forged", _codes(errors))
        if execution is not None:
            self.assertFalse(execution["reference"]["ok"])

    def test_root_module_cannot_shadow_src(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            pack = Path(tmp) / "pack"
            shutil.copytree(PACK, pack)
            (pack / "counter.py").write_text(
                "def add(a, b):\n    return 0\n", encoding="utf-8"
            )
            record = _load(ACCEPT / "issue-patch-validated.json")
            record["environment"]["repo_snapshot_hash"] = vset.pack_snapshot_hash(pack)
            errors, execution = vset.validate_record_with_oracle(record, pack)
            self.assertNotIn("vset.oracle_execution_mismatch", _codes(errors))
            self.assertIsNotNone(execution)
            self.assertTrue(execution["reference"]["ok"])


if __name__ == "__main__":
    unittest.main()
