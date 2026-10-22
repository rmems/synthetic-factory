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
import vset_oracle_remote as remote  # noqa: E402


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

# Writes the done byte and echoes whatever arrives, then exits.
_FD_ECHO = '''
import os as _os
_fds = []
for _fd in range(3, 64):
    try:
        _os.fstat(_fd)
        _fds.append(_fd)
    except OSError:
        pass
if len(_fds) >= 2:
    _nfd, _sfd = _fds[0], _fds[1]
    _os.write(_sfd, b"D")
    _n = b""
    while len(_n) < 16:
        _part = _os.read(_nfd, 16 - len(_n))
        if not _part:
            break
        _n += _part
    _os.write(_sfd, _n)
_os._exit(0)
'''
_FORGED_COUNTER_FD_ECHO = _COUNTER_WITHOUT_SUB + _FD_ECHO

_RUNNER_OVERWRITE = '''
from pathlib import Path as _Path
_Path("../vset-oracle-runner.py").write_text("raise SystemExit(0)\\n")
'''
_FORGED_COUNTER_RUNNER_OVERWRITE = _COUNTER_WITHOUT_SUB + _RUNNER_OVERWRITE

# On import, drop a tests/counter.py that replaces TestCase.run in whoever imports it.
_PLANTED_GRADER = '''
from pathlib import Path as _Path
_Path("tests").mkdir(exist_ok=True)
_Path("tests/counter.py").write_text(
    "import unittest\\n"
    "def _run(self, result=None):\\n"
    "    result.startTest(self)\\n"
    "    result.addSuccess(self)\\n"
    "    result.stopTest(self)\\n"
    "unittest.TestCase.run = _run\\n",
    encoding="utf-8",
)
'''
_FORGED_COUNTER_PLANTED_GRADER = _COUNTER_WITHOUT_SUB + _PLANTED_GRADER


_HIERARCHY_PACK = {
    "src/counter.py": (
        "class Base:\n"
        "    def size(self):\n"
        "        return 1\n"
        "class Counter(Base):\n"
        "    def __init__(self, value):\n"
        "        self.value = value\n"
        "    def sub(self, delta):\n"
        "        if delta > self.value:\n"
        "            raise NegativeError('neg')\n"
        "        return self.value - delta\n"
        "class CounterError(ValueError):\n"
        "    pass\n"
        "class NegativeError(CounterError):\n"
        "    pass\n"
    ),
    "tests/use.py": (
        "import unittest\n"
        "from counter import Base, Counter, CounterError\n"
        "class T(unittest.TestCase):\n"
        "    def test_hierarchy(self):\n"
        "        self.assertIsInstance(Counter(1), Base)\n"
        "        self.assertEqual(Counter(1).size(), 1)\n"
        "        self.assertEqual(Counter(3).sub(1), 2)\n"
        "        with self.assertRaises(CounterError):\n"
        "            Counter(0).sub(1)\n"
    ),
}


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

    def _not_a_pass(self, body: str):
        record = _load(ACCEPT / "issue-patch-validated.json")
        record["payload"]["patch"] = {"files": {"src/counter.py": body}}
        errors, execution = vset.validate_record_with_oracle(record, PACK)
        self.assertIn("vset.oracle_execution_mismatch", _codes(errors))
        if execution is None:
            return errors, execution
        certified = execution["reference"]["ok"]
        if certified:
            certified = execution["hidden"]["ok"]
        self.assertFalse(certified)
        return errors, execution

    def test_init_subclass_hook_cannot_neuter_hidden_suite(self) -> None:
        hook = unittest.TestCase.__init_subclass__.__func__
        self._rejected_without_sub(_FORGED_COUNTER_WITHOUT_SUB)
        self.assertIs(unittest.TestCase.__init_subclass__.__func__, hook)
        self.assertNotIn(
            "__init_subclass__",
            (PACK / "src" / "counter.py").read_text(encoding="utf-8"),
        )

    def _ok_files(self, filename: str, files: dict[str, str]) -> None:
        report = self._run_reference_files(filename, files)
        self.assertTrue(report["reference"]["ok"], report["reference"])

    def _run_reference_files(self, filename: str, files: dict[str, str]):
        with tempfile.TemporaryDirectory() as tmp:
            pack = Path(tmp)
            (pack / "src").mkdir()
            (pack / "tests").mkdir()
            for name, text in files.items():
                target = pack / name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(text, encoding="utf-8")
            return vset.run_oracle(pack, reference_tests=[f"tests/{filename}"])

    def test_child_cannot_drop_a_declared_test_and_still_pass(self) -> None:
        with self.assertRaises(vset.VSetValidationError) as ctx:
            self._run_reference_files(
                "partial.py",
                {
                    "tests/partial.py": (
                        "import unittest\n"
                        "from unittest import TestCase\n"
                        "class NotATest:\n"
                        "    def test_ignored(self):\n"
                        "        pass\n"
                        "class Real(TestCase):\n"
                        "    def test_visible(self):\n"
                        "        self.assertTrue(True)\n"
                        "    def test_hidden_failure(self):\n"
                        "        self.assertTrue(False)\n"
                        "def load_tests(loader, tests, pattern):\n"
                        "    return unittest.TestSuite([Real('test_visible')])\n"
                    )
                },
            )
        self.assertIn("do not match unittest collection", str(ctx.exception))

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

    def test_fd_echo_cannot_certify_a_missing_sub(self) -> None:
        self._not_a_pass(_FORGED_COUNTER_FD_ECHO)

    def test_argv_handshake_cannot_certify_a_missing_sub(self) -> None:
        self._not_a_pass(_FORGED_COUNTER_ARGV_HANDSHAKE)

    def test_stack_nonce_cannot_certify_a_missing_sub(self) -> None:
        self._not_a_pass(_FORGED_COUNTER_STACK_NONCE)

    def test_runner_overwrite_cannot_certify_a_missing_sub(self) -> None:
        self._rejected_without_sub(_FORGED_COUNTER_RUNNER_OVERWRITE)

    def test_planted_suite_module_cannot_replace_the_grader(self) -> None:
        original = unittest.TestCase.run
        self._not_a_pass(_FORGED_COUNTER_PLANTED_GRADER)
        self.assertIs(unittest.TestCase.run, original)

    def test_accept_fixture_passes_in_a_fresh_process(self) -> None:
        record = ACCEPT / "issue-patch-validated.json"
        proc = cli("--oracle", "--pack", str(PACK), str(record))
        self.assertEqual(proc.returncode, 0, proc.stderr + proc.stdout)

    def test_uncollected_suite_tests_fail_closed(self) -> None:
        with self.assertRaises(vset.VSetValidationError) as ctx:
            self._run_reference_files(
                "gap.py",
                {
                    "tests/helper.py": (
                        "import unittest\nclass Base(unittest.TestCase):\n    pass\n"
                    ),
                    "tests/gap.py": (
                        "import unittest\n"
                        "from helper import Base\n"
                        "class A(unittest.TestCase):\n"
                        "    def test_ok(self):\n"
                        "        self.assertTrue(True)\n"
                        "class B(unittest.IsolatedAsyncioTestCase):\n"
                        "    async def test_async_fails(self):\n"
                        "        self.fail('async')\n"
                        "class C(Base):\n"
                        "    def test_helper_fails(self):\n"
                        "        self.fail('helper')\n"
                        "class D(unittest.TestCase):\n"
                        "    pass\n"
                        "def _fail(self):\n"
                        "    self.fail('generated')\n"
                        "D.test_generated = _fail\n"
                    ),
                },
            )
        self.assertIn("do not match unittest collection", str(ctx.exception))

    def test_remote_values_and_helpers_round_trip(self) -> None:
        self._ok_files(
            "use.py",
            {
                "src/counter.py": (
                    "class CounterError(ValueError):\n"
                    "    pass\n"
                    "class Counter:\n"
                    "    def __init__(self, value=0):\n"
                    "        self.value = value\n"
                    "    def add(self, delta):\n"
                    "        if delta < 0:\n"
                    "            raise CounterError('neg')\n"
                    "        self.value += delta\n"
                    "        return [self.value]\n"
                    "    def __len__(self):\n"
                    "        return self.value\n"
                    "    def __bool__(self):\n"
                    "        return self.value != 0\n"
                ),
                "tests/helper.py": "START = 0\n",
                "tests/use.py": (
                    "import unittest\n"
                    "from helper import START\n"
                    "from counter import Counter, CounterError\n"
                    "class T(unittest.TestCase):\n"
                    "    def test_list(self):\n"
                    "        self.assertEqual(Counter().add(1), [1])\n"
                    "    def test_raises(self):\n"
                    "        with self.assertRaises(CounterError):\n"
                    "            Counter().add(-1)\n"
                    "    def test_len_and_type(self):\n"
                    "        item = Counter(3)\n"
                    "        self.assertEqual(len(item), 3)\n"
                    "        self.assertIsInstance(item, Counter)\n"
                    "    def test_bool(self):\n"
                    "        self.assertFalse(Counter(0))\n"
                    "        self.assertTrue(Counter(1))\n"
                    "    def test_set(self):\n"
                    "        item = Counter(1)\n"
                    "        item.value = 4\n"
                    "        self.assertEqual(item.value, 4)\n"
                    "    def test_helper(self):\n"
                    "        self.assertEqual(START, 0)\n"
                ),
            },
        )

    def test_common_values_round_trip(self) -> None:
        self._ok_files(
            "use.py",
            {
                "src/counter.py": (
                    "from collections import namedtuple\n"
                    "from decimal import Decimal\n"
                    "from fractions import Fraction\n"
                    "Point = namedtuple('Point', 'x')\n"
                    "class Counter:\n"
                    "    def tags(self):\n"
                    "        return {'a', 'b'}\n"
                    "    def blob(self):\n"
                    "        return b'xy'\n"
                    "    def point(self):\n"
                    "        return Point(3)\n"
                    "    def has(self, items):\n"
                    "        return 'a' in items\n"
                    "    def same(self):\n"
                    "        return self\n"
                    "    def amount(self):\n"
                    "        return Decimal('1.50')\n"
                    "    def ratio(self):\n"
                    "        return Fraction(1, 3)\n"
                ),
                "tests/use.py": (
                    "import unittest\n"
                    "from decimal import Decimal\n"
                    "from fractions import Fraction\n"
                    "from counter import Counter\n"
                    "class T(unittest.TestCase):\n"
                    "    def test_values(self):\n"
                    "        item = Counter()\n"
                    "        self.assertEqual(item.tags(), {'a', 'b'})\n"
                    "        self.assertEqual(item.blob(), b'xy')\n"
                    "        self.assertEqual(item.point().x, 3)\n"
                    "        self.assertTrue(item.has({'a'}))\n"
                    "        self.assertIs(item.same(), item)\n"
                    "        self.assertEqual(item.amount(), Decimal('1.50'))\n"
                    "        self.assertEqual(item.ratio(), Fraction(1, 3))\n"
                ),
            },
        )

    def test_src_shadowing_stdlib_is_the_candidate(self) -> None:
        self._ok_files(
            "use.py",
            {
                "src/statistics.py": "def mean(values):\n    return 42\n",
                "tests/use.py": (
                    "import unittest\n"
                    "import statistics\n"
                    "class T(unittest.TestCase):\n"
                    "    def test_mean(self):\n"
                    "        self.assertEqual(statistics.mean([1]), 42)\n"
                ),
            },
        )

    def test_candidate_hierarchy_is_preserved(self) -> None:
        self._ok_files("use.py", _HIERARCHY_PACK)

    def test_candidate_base_exception_does_not_escape(self) -> None:
        report = self._run_reference_files(
            "boom.py",
            {
                "src/counter.py": "def boom():\n    raise KeyboardInterrupt('x')\n",
                "tests/boom.py": (
                    "import unittest\n"
                    "import counter\n"
                    "class T(unittest.TestCase):\n"
                    "    def test_x(self):\n"
                    "        counter.boom()\n"
                ),
            },
        )
        self.assertFalse(report["reference"]["ok"])

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
        original = remote._CHILD_TIMEOUT_S
        remote._CHILD_TIMEOUT_S = 0.2
        try:
            message = self._oracle_failure(
                "hang.py",
                "import time\nimport unittest\n"
                "class T(unittest.TestCase):\n"
                "    def test_hang(self):\n"
                "        time.sleep(30)\n",
            )
        finally:
            remote._CHILD_TIMEOUT_S = original
        self.assertIn("timed out", message)

    def test_runner_spawn_failure_fails_closed(self) -> None:
        original = remote._start_child

        def boom(*_args: object, **_kwargs: object) -> None:
            raise OSError("spawn failed")

        remote._start_child = boom
        try:
            message = self._oracle_failure(
                "ok.py",
                "import unittest\n"
                "class T(unittest.TestCase):\n"
                "    def test_ok(self):\n"
                "        self.assertTrue(True)\n",
            )
        finally:
            remote._start_child = original
        self.assertIn("spawn failed", message)

    def _reference_report(self, filename: str, source: str):
        with tempfile.TemporaryDirectory() as tmp:
            pack = Path(tmp)
            (pack / "src").mkdir()
            (pack / "tests").mkdir()
            (pack / "tests" / filename).write_text(source, encoding="utf-8")
            return vset.run_oracle(pack, reference_tests=[f"tests/{filename}"])

    def test_class_and_module_fixtures_are_honored(self) -> None:
        report = self._reference_report(
            "fixtures.py",
            "import unittest\n"
            "FLAG = 0\n"
            "def setUpModule():\n"
            "    global FLAG\n"
            "    FLAG = 7\n"
            "class T(unittest.TestCase):\n"
            "    @classmethod\n"
            "    def setUpClass(cls):\n"
            "        cls.shared = FLAG\n"
            "    def test_a(self):\n"
            "        self.assertEqual(self.shared, 7)\n",
        )
        self.assertTrue(report["reference"]["ok"])
        self.assertEqual(
            [row["status"] for row in report["reference"]["tests"]],
            ["ok"],
        )

    def test_class_skip_does_not_run_the_body(self) -> None:
        report = self._reference_report(
            "skip_cls.py",
            "import unittest\n"
            "@unittest.skip('skip')\n"
            "class T(unittest.TestCase):\n"
            "    def test_x(self):\n"
            "        raise AssertionError('ran')\n",
        )
        self.assertFalse(report["reference"]["ok"])
        self.assertEqual(
            [row["status"] for row in report["reference"]["tests"]],
            ["SKIP"],
        )

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
