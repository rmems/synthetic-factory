"""Out-of-process oracle paths the in-process grader used to get wrong.

Covers a passing suite, an assertion failure, a child crash, a timeout,
and a candidate that tampers with the worktree after the call returns.
"""
from __future__ import annotations

import dataclasses
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


def _case(body: str) -> str:
    rows = ["import unittest", "import m", "class T(unittest.TestCase):", "    def test_case(self):"]
    rows.extend(f"        {line}" if line else "" for line in body.splitlines())
    return "\n".join(rows) + "\n"


def _grade(src: str, body: str, extra: dict[str, str | bytes] | None = None):
    files: dict[str, str | bytes] = {"src/m.py": src, "tests/use.py": _case(body)}
    if extra:
        files.update(extra)
    return _run(files)


def _hidden(name: str, value: str) -> dict[str, str]:
    return {name: value}


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
import array
import collections
import dataclasses
import unittest
import uuid
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

    def test_stdlib_instances(self):
        self.assertEqual(m.ident(uuid.UUID(int=5)), uuid.UUID(int=5))
        self.assertEqual(m.ident(array.array("i", [1, 2])), array.array("i", [1, 2]))
'''


class OracleBoundaryTests(unittest.TestCase):
    def test_stdlib_values_and_callbacks_pass(self) -> None:
        report = _run({"src/m.py": _SRC, "tests/use.py": _SUITE})
        self.assertTrue(report["reference"]["ok"], report["reference"])

    def test_shared_containers_private_patches_and_fixtures(self) -> None:
        report = _grade(
            "CONFIG = {'enabled': False}\n" "class Counter:\n" "    _limit = 1\n" "    def read(self):\n" "        return Counter._limit\n" "class Bag(dict):\n"
            "    pass\n" "class Stack:\n" "    def __init__(self):\n" "        self.items = []\n" "    def pop(self):\n" "        return self.items.pop()\n"
            "class Reg:\n" "    def take(self, data):\n" "        self.seen = data\n" "def fill(a, b):\n" "    a.append(1)\n" "    return b\n"
            "def grow(xs):\n" "    xs.append(1)\n" "    raise ValueError('x')\n" "def flag():\n" "    return CONFIG['enabled']\n" "def limit():\n"
            "    return Counter().read()\n" "def keys():\n" "    return sorted(Bag(a=1).keys())\n" "def token():\n" "    import os\n" "    return os.environ.get('HF_TOKEN')\n",
            "import os\n" "from unittest import mock\n" "xs = []\n" "self.assertEqual(m.fill(xs, xs), [1])\n" "self.assertEqual(xs, [1])\n" "grown = []\n"
            "with self.assertRaises(ValueError):\n" "    m.grow(grown)\n" "self.assertEqual(grown, [1])\n" "stack = m.Stack()\n" "stack.items.append(5)\n" "self.assertEqual(stack.pop(), 5)\n"
            "reg = m.Reg()\n" "data = [1]\n" "reg.take(data)\n" "data.append(2)\n" "self.assertEqual(reg.seen, [1, 2])\n" "with mock.patch.dict(m.CONFIG, {'enabled': True}):\n"
            "    self.assertTrue(m.flag())\n" "self.assertFalse(m.flag())\n" "with mock.patch.object(m.Counter, '_limit', 3):\n" "    self.assertEqual(m.limit(), 3)\n" "self.assertEqual(m.keys(), ['a'])\n" "key = 'HF_' + 'TOKEN'\n"
            "os.environ[key] = 'parent-only'\n" "try:\n" "    with mock.patch.dict(os.environ, {}, clear=True):\n" "        self.assertIsNone(m.token())\n" "    self.assertIsNone(m.token())\n" "finally:\n"
            "    os.environ.pop(key, None)\n",
        )
        self.assertTrue(report["reference"]["ok"], report["reference"])

    def test_module_fixtures_run_once(self) -> None:
        report = _run(
            {
                "src/m.py": "def value():\n    return 1\n",
                "tests/use.py": (
                    "import sys\nimport unittest\nimport m\n" "def setUpModule():\n" "    if getattr(sys, '_vset_fix_once', False):\n" "        raise RuntimeError('twice')\n" "    sys._vset_fix_once = True\n" "def tearDownModule():\n"
                    "    del sys._vset_fix_once\n" "class T(unittest.TestCase):\n" "    def test_a(self):\n" "        self.assertEqual(m.value(), 1)\n" "    def test_b(self):\n" "        self.assertEqual(m.value(), 1)\n"
                ),
            }
        )
        self.assertTrue(report["reference"]["ok"], report["reference"])
        self.assertFalse(hasattr(sys, "_vset_fix_once"))

    def test_large_return_values_grade(self) -> None:
        report = _grade(
            "def many():\n    return list(range(40000))\ndef big():\n    return 'x' * 2000000\n",
            "self.assertEqual(len(m.many()), 40000)\nself.assertEqual(len(m.big()), 2000000)",
        )
        self.assertTrue(report["reference"]["ok"], report["reference"])

    def test_failed_and_crashed_references(self) -> None:
        failed = _grade("def add(left, right):\n    return 0\n", "self.assertEqual(m.add(1, 1), 2)")
        self.assertEqual(failed["reference"]["tests"][0]["status"], "FAIL")
        crashed = _grade("import os\ndef boom():\n    os._exit(9)\n", "m.boom()")
        self.assertEqual(crashed["reference"]["tests"][0]["status"], "ERROR")
        self.assertFalse(failed["reference"]["ok"])
        self.assertFalse(crashed["reference"]["ok"])

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
        key = "HF_" + "TOKEN"
        os.environ[key] = "parent" + "-only"
        try:
            report = _grade(
                "import os\ndef token():\n    return os.environ.get('HF_TOKEN')\n",
                "self.assertIsNone(m.token())",
            )
        finally:
            os.environ.pop(key, None)
        self.assertTrue(report["reference"]["ok"], report["reference"])

    def test_corrupt_workspace_fails_closed(self) -> None:
        with self.assertRaises(vset.VSetValidationError) as bad_bytes:
            _grade("def n():\n    return 1\n", "self.assertEqual(m.n(), 1)", {"tests/helper.py": b"\xff"})
        self.assertEqual(bad_bytes.exception.code, "vset.oracle_execution_mismatch")
        self.assertIn("helper.py", str(bad_bytes.exception))
        with self.assertRaises(vset.VSetValidationError) as planted:
            _grade(
                "import os\ndef plant():\n    os.mkdir('src/evil.py')\n    return 1\n",
                "self.assertEqual(m.plant(), 1)",
            )
        self.assertEqual(planted.exception.code, "vset.oracle_execution_mismatch")
        self.assertIn("cannot clean candidate src", str(planted.exception))

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

    def test_fixture_subtest_and_container_edges(self) -> None:
        report = _run(
            {
                "src/m.py": (
                    "import re\n" "kept = []\n" "def save(xs):\n" "    kept.append(xs)\n" "    return len(xs)\n" "def grow():\n"
                    "    kept[0].append(1)\n" "    return kept[0]\n" "def make_list():\n" "    return [1, 2]\n" "def boom():\n" "    raise re.error('bad')\n"
                ),
                "tests/use.py": (
                    "import re\nimport unittest\nimport m\n" "class T(unittest.TestCase):\n" "    def test_list(self):\n" "        made = m.make_list()\n" "        self.assertIsInstance(made, list)\n" "        self.assertEqual(made, [1, 2])\n"
                    "    def test_keep(self):\n" "        xs = []\n" "        self.assertEqual(m.save(xs), 0)\n" "        self.assertEqual(m.grow(), [1])\n" "        self.assertEqual(xs, [1])\n" "    def test_re(self):\n"
                    "        with self.assertRaises(re.error):\n" "            m.boom()\n" "    def test_sub(self):\n" "        with self.subTest(i=1):\n" "            self.assertEqual(1, 2)\n"
                ),
            }
        )
        statuses = {
            row["id"].rsplit(".", 1)[-1]: row["status"] for row in report["reference"]["tests"]
        }
        self.assertEqual(statuses["test_list"], "ok")
        self.assertEqual(statuses["test_keep"], "ok")
        self.assertEqual(statuses["test_re"], "ok")
        self.assertNotEqual(statuses["test_sub"], "ok")
        failed = _run(
            {
                "src/m.py": "def value():\n    return 1\n",
                "tests/use.py": (
                    "import unittest\nimport m\n"
                    "class T(unittest.TestCase):\n"
                    "    @classmethod\n"
                    "    def setUpClass(cls):\n"
                    "        raise RuntimeError('fixture')\n"
                    "    def test_value(self):\n"
                    "        self.assertEqual(m.value(), 1)\n"
                ),
            }
        )
        self.assertNotEqual(failed["reference"]["tests"][0]["status"], "ok")
        self.assertFalse(failed["reference"]["ok"])

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
        key = "HF_" + "TOKEN"
        with unittest.mock.patch.dict(os.environ, _hidden(key, "parent" + "-only"), clear=False):
            env = remote._child_environment()
        self.assertNotIn(key, env)
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
        values.reset_identity()

    def test_parent_rebuilds_containers(self) -> None:
        client = object()
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
        values.reset_identity()

    def test_remote_dataclass_fields_support_asdict(self) -> None:
        class Box:
            pass

        shape.attach_dataclass_fields(Box, {"dc_fields": ["n"]})
        Box.n = 3  # type: ignore[attr-defined]
        self.assertEqual([item.name for item in dataclasses.fields(Box)], ["n"])
        self.assertEqual(dataclasses.asdict(Box()), {"n": 3})
        plain = type("Plain", (), {})
        shape.attach_dataclass_fields(plain, {})
        self.assertFalse(hasattr(plain, "__dataclass_fields__"))
