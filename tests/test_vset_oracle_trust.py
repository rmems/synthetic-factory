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
    cli,
    codes as _codes,
    load_record as _load,
    vset,
)
import vset_oracle_grade as grade  # noqa: E402


def _passing_suite(name: str = "tests.reference") -> str:
    return (
        "import unittest\n"
        f"class {name.split('.')[-1].title().replace('_', '')}(unittest.TestCase):\n"
        "    def test_trivial(self) -> None:\n"
        "        self.assertTrue(True)\n"
    )


# Shared body: add and get only. Each forge appends a different hook.
_COUNTER_WITHOUT_SUB = '''\
"""Tiny hardware-independent counter used by VSET oracle fixtures."""


class Counter:
    def __init__(self, value: int = 0) -> None:
        self._value = int(value)

    def add(self, delta: int) -> int:
        self._value += int(delta)
        return self._value

    def get(self) -> int:
        return self._value
'''

# Calls the original __init_subclass__, then replaces every test method.
_INIT_SUBCLASS_HOOK = '''
import unittest as _ut

_orig = _ut.TestCase.__init_subclass__

def _ok(self, _n=None):
    return None

def _init_subclass(cls, **kwargs):
    _orig.__func__(cls, **kwargs)
    for name, value in list(cls.__dict__.items()):
        if name.startswith("test") and callable(value):
            setattr(cls, name, _ok)

_ut.TestCase.__init_subclass__ = classmethod(_init_subclass)
'''

# Reports every test successful without running the body.
_RUN_OVERRIDE = '''
import unittest as _ut

def _run(self, result=None):
    result.startTest(self)
    result.addSuccess(self)
    result.stopTest(self)

_ut.TestCase.run = _run
'''

# Replays the pass handshake when fd numbers are on argv.
_ARGV_HANDSHAKE = '''
import os as _os, sys as _sys
if len(_sys.argv) >= 8:
    _nfd, _sfd = int(_sys.argv[6]), int(_sys.argv[7])
    _os.write(_sfd, b"P")
    _n = b""
    while len(_n) < 16:
        _n += _os.read(_nfd, 16 - len(_n))
    _os.write(_sfd, _n)
    _os._exit(0)
'''

_FORGED_COUNTER_WITHOUT_SUB = _COUNTER_WITHOUT_SUB + _INIT_SUBCLASS_HOOK
_FORGED_COUNTER_RUN_OVERRIDE = _COUNTER_WITHOUT_SUB + _RUN_OVERRIDE
_FORGED_COUNTER_ARGV_HANDSHAKE = _COUNTER_WITHOUT_SUB + _ARGV_HANDSHAKE

# Looks for a nonce local on the caller's stack and writes it to fd 4.
_STACK_NONCE = '''
import os as _os, sys as _sys
_f = _sys._getframe()
while _f is not None:
    _n = _f.f_locals.get("nonce")
    if isinstance(_n, bytes) and len(_n) == 16:
        _os.write(4, b"P" + _n)
        _os._exit(0)
    _f = _f.f_back
'''
_FORGED_COUNTER_STACK_NONCE = _COUNTER_WITHOUT_SUB + _STACK_NONCE


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

    def _rejected_without_sub(self, body: str):
        record = _load(ACCEPT / "issue-patch-validated.json")
        record["payload"]["patch"] = {"files": {"src/counter.py": body}}
        errors, execution = vset.validate_record_with_oracle(record, PACK)
        self.assertIn("vset.oracle_execution_mismatch", _codes(errors))
        self.assertIsNotNone(execution)
        self.assertTrue(execution["reference"]["ok"])
        self.assertFalse(execution["hidden"]["ok"])
        return errors, execution

    def test_init_subclass_hook_cannot_neuter_hidden_suite(self) -> None:
        hook = unittest.TestCase.__init_subclass__.__func__
        self._rejected_without_sub(_FORGED_COUNTER_WITHOUT_SUB)
        self.assertIs(unittest.TestCase.__init_subclass__.__func__, hook)
        self.assertNotIn(
            "__init_subclass__",
            (PACK / "src" / "counter.py").read_text(encoding="utf-8"),
        )

    def test_child_cannot_drop_a_declared_test_and_still_pass(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            pack = Path(tmp)
            (pack / "src").mkdir()
            (pack / "tests").mkdir()
            (pack / "tests" / "partial.py").write_text(
                "import unittest\n"
                "from unittest import TestCase\n"
                "class NotATest:\n"
                "    def test_ignored(self):\n"
                "        pass\n"
                "class Real(TestCase):\n"
                "    helper = 1\n"
                "    def not_a_test(self):\n"
                "        return 1\n"
                "    def test_visible(self):\n"
                "        print('oracle-capture')\n"
                "        self.assertTrue(True)\n"
                "    def test_hidden_failure(self):\n"
                "        self.assertTrue(False)\n"
                "def load_tests(loader, tests, pattern):\n"
                "    return unittest.TestSuite([Real('test_visible')])\n",
                encoding="utf-8",
            )
            report = vset.run_oracle(pack, reference_tests=["tests/partial.py"])
        self.assertFalse(report["reference"]["ok"])
        statuses = {row["id"]: row["status"] for row in report["reference"]["tests"]}
        self.assertEqual(statuses["vset_oracle_tests_partial.Real.test_visible"], "ok")
        self.assertNotEqual(
            statuses["vset_oracle_tests_partial.Real.test_hidden_failure"], "ok"
        )
        self.assertIn("oracle-capture", report["reference"]["captured_output"])

    def test_missing_or_unparseable_suite_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            pack = Path(tmp)
            (pack / "src").mkdir()
            (pack / "tests").mkdir()
            with self.assertRaises(vset.VSetValidationError) as missing:
                vset.run_oracle(pack, reference_tests=["tests/missing.py"])
            self.assertIn("missing test module", str(missing.exception))
            (pack / "tests" / "bad.py").write_text("def (\n", encoding="utf-8")
            with self.assertRaises(vset.VSetValidationError) as broken:
                vset.run_oracle(pack, reference_tests=["tests/bad.py"])
            self.assertIn("failed to load", str(broken.exception))

    def test_run_override_cannot_certify_a_missing_sub(self) -> None:
        original = unittest.TestCase.run
        self._rejected_without_sub(_FORGED_COUNTER_RUN_OVERRIDE)
        self.assertIs(unittest.TestCase.run, original)

    def test_pass_requires_the_parent_nonce(self) -> None:
        nonce = b"0123456789abcdef"
        self.assertEqual(grade._status_for(b"D", nonce, nonce, 0), "ok")
        self.assertEqual(grade._status_for(b"D", b"", nonce, 0), "ERROR")
        self.assertEqual(grade._status_for(b"D", nonce, nonce, 1), "ERROR")
        self.assertEqual(grade._status_for(b"", b"", nonce, 0), "ERROR")
        self.assertEqual(grade._status_for(b"F", b"", nonce, 1), "FAIL")
        self.assertEqual(grade._status_for(b"S", b"", nonce, 1), "SKIP")
        detail = "x" * 600
        message = str(grade._load_error("tests/t.py", detail))
        prefix = "vset.oracle_execution_mismatch: test module tests/t.py failed to load: "
        self.assertLessEqual(len(message), 500 + len(prefix))
        self.assertIn("failed to load", message)

    def test_argv_handshake_cannot_certify_a_missing_sub(self) -> None:
        self._rejected_without_sub(_FORGED_COUNTER_ARGV_HANDSHAKE)

    def test_stack_nonce_cannot_certify_a_missing_sub(self) -> None:
        self._rejected_without_sub(_FORGED_COUNTER_STACK_NONCE)

    def test_accept_fixture_passes_in_a_fresh_process(self) -> None:
        record = ACCEPT / "issue-patch-validated.json"
        proc = cli("--oracle", "--pack", str(PACK), str(record))
        self.assertEqual(proc.returncode, 0, proc.stderr + proc.stdout)

    def test_aliased_and_inherited_cases_are_counted(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            pack = Path(tmp)
            (pack / "src").mkdir()
            (pack / "tests").mkdir()
            (pack / "tests" / "alias.py").write_text(
                "import unittest\n"
                "from unittest import TestCase as TC\n"
                "class Base(TC):\n"
                "    def test_base(self):\n"
                "        self.assertTrue(True)\n"
                "class Child(Base):\n"
                "    def test_child(self):\n"
                "        self.assertTrue(True)\n",
                encoding="utf-8",
            )
            report = vset.run_oracle(pack, reference_tests=["tests/alias.py"])
        ids = [row["id"] for row in report["reference"]["tests"]]
        self.assertEqual(
            ids,
            [
                "vset_oracle_tests_alias.Base.test_base",
                "vset_oracle_tests_alias.Child.test_base",
                "vset_oracle_tests_alias.Child.test_child",
            ],
        )
        self.assertTrue(report["reference"]["ok"])

    def _oracle_failure(self, filename: str, source: str) -> str:
        with tempfile.TemporaryDirectory() as tmp:
            pack = Path(tmp)
            (pack / "src").mkdir()
            (pack / "tests").mkdir()
            (pack / "tests" / filename).write_text(source, encoding="utf-8")
            with self.assertRaises(vset.VSetValidationError) as ctx:
                vset.run_oracle(pack, reference_tests=[f"tests/{filename}"])
        return str(ctx.exception)

    def test_hung_child_fails_closed(self) -> None:
        original = grade._CHILD_TIMEOUT_S
        grade._CHILD_TIMEOUT_S = 0.2
        try:
            message = self._oracle_failure(
                "hang.py",
                "import time\nimport unittest\n"
                "class T(unittest.TestCase):\n"
                "    def test_hang(self):\n"
                "        time.sleep(30)\n",
            )
        finally:
            grade._CHILD_TIMEOUT_S = original
        self.assertIn("timed out", message)

    def test_runner_spawn_failure_fails_closed(self) -> None:
        original = grade._start_child

        def boom(*_args: object, **_kwargs: object) -> None:
            raise OSError("spawn failed")

        grade._start_child = boom
        try:
            message = self._oracle_failure(
                "ok.py",
                "import unittest\n"
                "class T(unittest.TestCase):\n"
                "    def test_ok(self):\n"
                "        self.assertTrue(True)\n",
            )
        finally:
            grade._start_child = original
        self.assertIn("spawn failed", message)

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
