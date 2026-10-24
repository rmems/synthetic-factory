"""Out-of-process oracle paths the in-process grader used to get wrong.

Covers a passing suite, an assertion failure, a child crash, a timeout,
and a candidate that tampers with the worktree after the call returns.
"""
from __future__ import annotations

import os
import sys
import tempfile
import unittest
from collections import Counter, OrderedDict, defaultdict, namedtuple
from datetime import time, timedelta
from pathlib import Path, PurePath

_TESTS = Path(__file__).resolve().parent
if str(_TESTS) not in sys.path:
    sys.path.insert(0, str(_TESTS))

from vset_testutil import vset  # noqa: E402
import vset_oracle_layout as layout  # noqa: E402
import vset_oracle_record as record  # noqa: E402
import vset_oracle_remote as remote  # noqa: E402
import vset_oracle_shape as shape  # noqa: E402
import vset_oracle_values as values  # noqa: E402


def _run(files: dict[str, str | bytes]):
    with tempfile.TemporaryDirectory() as tmp:
        pack = Path(tmp)
        for name, text in files.items():
            target = pack / name
            target.parent.mkdir(parents=True, exist_ok=True)
            if isinstance(text, bytes):
                target.write_bytes(text)
            else:
                target.write_text(text, encoding="utf-8")
        return vset.run_oracle(pack, reference_tests=["tests/use.py"])


_SRC = '''
from datetime import time, timedelta
from pathlib import Path
import collections
import dataclasses

@dataclasses.dataclass
class Box:
    n: int

def td():
    return timedelta(seconds=5)

def path():
    return Path("x/y")

def ctr():
    return collections.Counter("aab")

def cx():
    return 1 + 2j

def rng():
    return range(3)

def sl():
    return slice(1, 3)

def box():
    return Box(3)

def clock():
    return time(1, 2, 3)

def ident(value):
    return value

def keys(obj):
    return list(obj.keys())

def kind(obj):
    return (
        type(obj).__name__,
        isinstance(obj, tuple),
        getattr(obj, "x", None),
        obj[0] if isinstance(obj, tuple) else None,
    )

def total(xs):
    return sum(xs)

def safe(fetch):
    try:
        return fetch()
    except ValueError:
        return -1

def take(fn):
    fn()
    try:
        fn()
    except StopIteration:
        return 1
    return 0
'''

_SUITE = '''
import collections
import dataclasses
import unittest
from collections import OrderedDict, defaultdict, deque, namedtuple
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from fractions import Fraction
from pathlib import Path
from unittest import mock
import m

P = namedtuple("P", "x y")

class T(unittest.TestCase):
    def test_td(self):
        self.assertEqual(m.td(), timedelta(seconds=5))

    def test_path(self):
        self.assertEqual(m.path(), Path("x/y"))

    def test_ctr(self):
        self.assertEqual(m.ctr(), collections.Counter("aab"))

    def test_cx(self):
        self.assertEqual(m.cx(), 1 + 2j)

    def test_rng(self):
        self.assertEqual(list(m.rng()), [0, 1, 2])
        self.assertEqual(len(m.rng()), 3)

    def test_sl(self):
        self.assertEqual([0, 1, 2, 3][m.sl()], [1, 2])

    def test_box(self):
        got = m.box()
        self.assertEqual(dataclasses.asdict(got), {"n": 3})
        self.assertEqual(got, m.box())
        self.assertEqual(got.n, 3)

    def test_time(self):
        self.assertEqual(m.clock(), time(1, 2, 3))

    def test_maps(self):
        self.assertEqual(m.keys(OrderedDict({1: 2, 3: 4})), [1, 3])
        self.assertEqual(m.keys(defaultdict(int, {2: 1})), [2])
        self.assertEqual(m.ident(collections.Counter("aab")), collections.Counter("aab"))

    def test_namedtuple(self):
        self.assertEqual(m.kind(P(1, 2)), ("P", True, 1, 1))

    def test_iterables(self):
        self.assertEqual(m.total(range(4)), 6)
        self.assertEqual(m.total(x for x in [1, 2]), 3)
        self.assertEqual(m.total(map(int, ["1", "2"])), 3)
        self.assertEqual(m.total({1: 2, 3: 4}.keys()), 4)
        self.assertEqual(m.total(deque([1, 2])), 3)

    def test_side_effect(self):
        fetch = mock.Mock(side_effect=ValueError("boom"))
        self.assertEqual(m.safe(fetch), -1)

    def test_stop(self):
        fetch = mock.Mock(side_effect=[1])
        self.assertEqual(m.take(fetch), 1)

    def test_numbers(self):
        self.assertEqual(m.ident(Decimal("1.20")), Decimal("1.20"))
        self.assertEqual(m.ident(Fraction(1, 3)), Fraction(1, 3))
        stamp = datetime(2020, 1, 2, 3, 4, 5)
        self.assertEqual(m.ident(stamp), stamp)
        self.assertEqual(m.ident(date(2020, 1, 2)), date(2020, 1, 2))
        self.assertEqual(m.ident(b"ab"), b"ab")
        self.assertEqual(m.ident({1, 2}), {1, 2})
        self.assertEqual(m.ident(frozenset({1})), frozenset({1}))
'''


class OracleBoundaryTests(unittest.TestCase):
    def test_stdlib_values_and_callbacks_pass(self) -> None:
        report = _run({"src/m.py": _SRC, "tests/use.py": _SUITE})
        self.assertTrue(report["reference"]["ok"], report["reference"])

    def test_assertion_failure_is_not_ok(self) -> None:
        report = _run(
            {
                "src/m.py": "def add(left, right):\n    return 0\n",
                "tests/use.py": (
                    "import unittest\nimport m\n"
                    "class T(unittest.TestCase):\n"
                    "    def test_add(self):\n"
                    "        self.assertEqual(m.add(1, 1), 2)\n"
                ),
            }
        )
        self.assertFalse(report["reference"]["ok"])
        self.assertEqual(report["reference"]["tests"][0]["status"], "FAIL")

    def test_child_crash_is_an_error(self) -> None:
        report = _run(
            {
                "src/m.py": "import os\ndef boom():\n    os._exit(9)\n",
                "tests/use.py": (
                    "import unittest\nimport m\n"
                    "class T(unittest.TestCase):\n"
                    "    def test_boom(self):\n"
                    "        m.boom()\n"
                ),
            }
        )
        self.assertFalse(report["reference"]["ok"])
        self.assertEqual(report["reference"]["tests"][0]["status"], "ERROR")

    def test_hung_child_fails_closed(self) -> None:
        original = remote._CHILD_TIMEOUT_S
        remote._CHILD_TIMEOUT_S = 0.2
        try:
            with self.assertRaises(vset.VSetValidationError) as caught:
                _run(
                    {
                        "tests/use.py": (
                            "import time\nimport unittest\n"
                            "class T(unittest.TestCase):\n"
                            "    def test_hang(self):\n"
                            "        time.sleep(30)\n"
                        ),
                    }
                )
        finally:
            remote._CHILD_TIMEOUT_S = original
        self.assertEqual(caught.exception.code, "vset.oracle_execution_mismatch")
        self.assertIn("timed out", str(caught.exception))

    def test_child_cannot_read_operator_secrets(self) -> None:
        os.environ["HF_TOKEN"] = "sekret-token"
        try:
            report = _run(
                {
                    "src/m.py": "import os\ndef token():\n    return os.environ.get('HF_TOKEN')\n",
                    "tests/use.py": (
                        "import unittest\nimport m\n"
                        "class T(unittest.TestCase):\n"
                        "    def test_token(self):\n"
                        "        self.assertIsNone(m.token())\n"
                    ),
                }
            )
        finally:
            os.environ.pop("HF_TOKEN", None)
        self.assertTrue(report["reference"]["ok"], report["reference"])

    def test_bad_suite_bytes_fail_closed(self) -> None:
        with self.assertRaises(vset.VSetValidationError) as caught:
            _run(
                {
                    "src/m.py": "def n():\n    return 1\n",
                    "tests/helper.py": b"\xff",
                    "tests/use.py": (
                        "import unittest\nimport m\n"
                        "class T(unittest.TestCase):\n"
                        "    def test_n(self):\n"
                        "        self.assertEqual(m.n(), 1)\n"
                    ),
                }
            )
        self.assertEqual(caught.exception.code, "vset.oracle_execution_mismatch")
        self.assertIn("helper.py", str(caught.exception))

    def test_directory_masquerading_as_module_fails_closed(self) -> None:
        with self.assertRaises(vset.VSetValidationError) as caught:
            _run(
                {
                    "src/m.py": (
                        "import os\n"
                        "def plant():\n"
                        "    os.mkdir('src/evil.py')\n"
                        "    return 1\n"
                    ),
                    "tests/use.py": (
                        "import unittest\nimport m\n"
                        "class T(unittest.TestCase):\n"
                        "    def test_plant(self):\n"
                        "        self.assertEqual(m.plant(), 1)\n"
                    ),
                }
            )
        self.assertEqual(caught.exception.code, "vset.oracle_execution_mismatch")
        self.assertIn("cannot clean candidate src", str(caught.exception))

    def test_added_package_is_removed(self) -> None:
        report = _run(
            {
                "src/m.py": (
                    "import os\n"
                    "def plant():\n"
                    "    os.makedirs('src/evilpkg', exist_ok=True)\n"
                    "    open('src/evilpkg/__init__.py', 'w').close()\n"
                    "    return 1\n"
                ),
                "tests/use.py": (
                    "import unittest\nimport m\n"
                    "class T(unittest.TestCase):\n"
                    "    def test_plant(self):\n"
                    "        self.assertEqual(m.plant(), 1)\n"
                ),
            }
        )
        self.assertTrue(report["reference"]["ok"], report["reference"])

    def test_same_exception_name_does_not_cross_modules(self) -> None:
        report = _run(
            {
                "src/a.py": "class Error(Exception):\n    pass\n",
                "src/b.py": "class Error(Exception):\n    pass\ndef boom():\n    raise Error('b')\n",
                "tests/use.py": (
                    "import unittest\nimport a, b\n"
                    "class T(unittest.TestCase):\n"
                    "    def test_same(self):\n"
                    "        with self.assertRaises(b.Error):\n"
                    "            b.boom()\n"
                    "    def test_cross(self):\n"
                    "        with self.assertRaises(a.Error):\n"
                    "            b.boom()\n"
                ),
            }
        )
        statuses = {row["id"].rsplit(".", 1)[-1]: row["status"] for row in report["reference"]["tests"]}
        self.assertEqual(statuses["test_same"], "ok")
        self.assertNotEqual(statuses["test_cross"], "ok")
        self.assertFalse(report["reference"]["ok"])

    def test_custom_exception_ancestry_is_preserved(self) -> None:
        report = _run(
            {
                "src/m.py": (
                    "class BaseError(Exception):\n"
                    "    pass\n"
                    "class SpecificError(BaseError):\n"
                    "    pass\n"
                    "def boom():\n"
                    "    raise SpecificError('x')\n"
                ),
                "tests/use.py": (
                    "import unittest\nimport m\n"
                    "class T(unittest.TestCase):\n"
                    "    def test_base(self):\n"
                    "        with self.assertRaises(m.BaseError):\n"
                    "            m.boom()\n"
                    "    def test_specific(self):\n"
                    "        with self.assertRaises(m.SpecificError):\n"
                    "            m.boom()\n"
                ),
            }
        )
        self.assertTrue(report["reference"]["ok"], report["reference"])


class OracleHelperTests(unittest.TestCase):
    def test_unlisted_builtin_stays_a_proxy(self) -> None:
        made = shape.blank_instance(range)
        self.assertIs(type(made), values.RemoteObject)
        made = shape.blank_instance(memoryview)
        self.assertIs(type(made), values.RemoteObject)

    def test_child_environment_is_minimal(self) -> None:
        with unittest.mock.patch.dict(os.environ, {"HF_TOKEN": "sekret"}, clear=False):
            env = remote._child_environment()
        self.assertNotIn("HF_TOKEN", env)
        self.assertIn("PATH", env)
        with unittest.mock.patch.dict(os.environ, {}, clear=True):
            bare = remote._child_environment()
        self.assertEqual(bare["PATH"], os.defpath)
        with unittest.mock.patch.object(remote.os, "name", "nt"):
            with unittest.mock.patch.dict(os.environ, {"SYSTEMROOT": r"C:\Windows"}):
                windows = remote._child_environment()
        self.assertEqual(windows["SYSTEMROOT"], r"C:\Windows")

    def test_pack_sources_and_simple_records(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            pack = Path(tmp)
            (pack / "tests").mkdir()
            (pack / "tests" / "use.py").write_text("x = 1\n", encoding="utf-8")
            found = layout.pack_sources(pack, "tests")
            self.assertEqual(found["use.py"], "x = 1\n")
            self.assertEqual(layout.pack_sources(pack, "missing"), {})
            (pack / "tests" / "bad.py").write_bytes(b"\xff")
            with self.assertRaises(vset.VSetValidationError):
                layout.pack_sources(pack, "tests")
            work = pack / "work"
            layout.drop_added_src(work, frozenset())

        class Plain:
            def __init__(self) -> None:
                self.n = 1

        recorded = record.data_record(Plain())
        self.assertEqual(recorded, {"record": {"n": 1}})

        class Mixed:
            def __init__(self) -> None:
                self.items = [1]

        self.assertIsNone(record.data_record(Mixed()))
        point = namedtuple("P", "x y")(1, (2, 3))
        encoded = record.data_record(point)
        self.assertEqual(encoded["namedtuple"], "P")
        self.assertIsNone(record.data_record(object()))
        self.assertIsNone(record.data_record(lambda: None))

    def test_parent_rebuilds_stdlib_payloads(self) -> None:
        client = object()
        self.assertEqual(values.interpret(client, {"kind": "complex", "real": 1, "imag": 2}), 1 + 2j)
        self.assertEqual(values.interpret(client, {"kind": "range", "start": 0, "stop": 3, "step": 1}), range(3))
        self.assertEqual(
            values.interpret(client, {"kind": "slice", "start": 1, "stop": 3, "step": None}),
            slice(1, 3, None),
        )
        self.assertEqual(
            values.interpret(client, {"kind": "timedelta", "days": 0, "seconds": 5, "micro": 0}),
            timedelta(seconds=5),
        )
        self.assertEqual(values.interpret(client, {"kind": "time", "data": "01:02:03"}), time(1, 2, 3))
        self.assertEqual(
            values.interpret(client, {"kind": "path", "data": "x/y", "cls": "PurePath"}),
            PurePath("x/y"),
        )
        counted = values.interpret(
            client,
            {
                "kind": "counter",
                "items": [[
                    {"kind": "value", "value": "a"},
                    {"kind": "value", "value": 2},
                ]],
            },
        )
        self.assertEqual(counted, Counter(a=2))
        self.assertIsInstance(
            values.interpret(client, {"kind": "ordered", "items": []}),
            OrderedDict,
        )
        self.assertIsInstance(
            values.interpret(client, {"kind": "default", "items": [], "factory": "int"}),
            defaultdict,
        )
        built = values.interpret(
            client,
            {
                "kind": "namedtuple",
                "name": "P",
                "fields": ["x", "y"],
                "items": [{"kind": "value", "value": 1}, {"kind": "value", "value": 2}],
            },
        )
        self.assertEqual(built, namedtuple("P", "x y")(1, 2))
        box = values.interpret(
            client,
            {"kind": "dataclass", "name": "Box", "oid": 4, "fields": {"n": {"kind": "value", "value": 3}}},
        )
        self.assertEqual(box.n, 3)
        values.reset_identity()
