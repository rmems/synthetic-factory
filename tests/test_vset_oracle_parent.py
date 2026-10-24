"""Parent-side oracle behavior: mocks, output, and callbacks."""

from __future__ import annotations

import json
import sys
import tempfile
import time
import unittest
from pathlib import Path

_TESTS = Path(__file__).resolve().parent
if str(_TESTS) not in sys.path:
    sys.path.insert(0, str(_TESTS))

from vset_testutil import vset  # noqa: E402
import vset_oracle_collect as collect  # noqa: E402
import vset_oracle_subclass as subclass  # noqa: E402


def _pack(name: str) -> dict[str, str]:
    path = _TESTS / "fixtures" / "vset" / "oracle-packs" / f"{name}.json"
    return json.loads(path.read_text(encoding="utf-8"))


def _run(filename: str, files: dict[str, str]):
    with tempfile.TemporaryDirectory() as tmp:
        pack = Path(tmp)
        (pack / "src").mkdir()
        (pack / "tests").mkdir()
        for name, text in files.items():
            target = pack / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(text, encoding="utf-8")
        return vset.run_oracle(pack, reference_tests=[f"tests/{filename}"])


class ParentOracleTests(unittest.TestCase):
    def _ok_files(self, filename: str, files: dict[str, str]) -> None:
        report = _run(filename, files)
        self.assertTrue(report["reference"]["ok"], report["reference"])

    def test_callback_attributes_and_namedtuples(self) -> None:
        self._ok_files(
            "use.py",
            {
                "src/c.py": (
                    "def norm(point):\n"
                    "    return point.x + point.y\n"
                    "def read_clock(clock):\n"
                    "    return clock.now()\n"
                    "def send(svc, msg):\n"
                    "    svc.send(msg)\n"
                    "def bump(acc):\n"
                    "    acc.total += 1\n"
                ),
                "tests/use.py": (
                    "import unittest\nfrom collections import namedtuple\n"
                    "from unittest.mock import Mock\nimport c\n"
                    "P = namedtuple('P', 'x y')\n"
                    "class Clock:\n"
                    "    def now(self):\n"
                    "        return 5\n"
                    "class Acc:\n"
                    "    def __init__(self):\n"
                    "        self.total = 0\n"
                    "class T(unittest.TestCase):\n"
                    "    def test_point(self):\n"
                    "        self.assertEqual(c.norm(P(1, 2)), 3)\n"
                    "    def test_clock(self):\n"
                    "        self.assertEqual(c.read_clock(Clock()), 5)\n"
                    "    def test_mock(self):\n"
                    "        svc = Mock()\n"
                    "        c.send(svc, 'ping')\n"
                    "        svc.send.assert_called_once_with('ping')\n"
                    "    def test_bump(self):\n"
                    "        acc = Acc()\n"
                    "        c.bump(acc)\n"
                    "        self.assertEqual(acc.total, 1)\n"
                ),
            },
        )

    def test_parent_captures_output_logs_and_environ(self) -> None:
        self._ok_files(
            "use.py",
            {
                "src/c.py": (
                    "import logging\nimport os\n"
                    "def hello():\n    print('hi')\n"
                    "def env(name):\n    return os.environ.get(name)\n"
                    "def shout():\n    logging.getLogger('c').warning('boom')\n"
                ),
                "tests/use.py": (
                    "import contextlib\nimport io\nimport os\nimport unittest\n"
                    "from unittest import mock\nimport c\n"
                    "class T(unittest.TestCase):\n"
                    "    def test_redirect(self):\n"
                    "        buf = io.StringIO()\n"
                    "        with contextlib.redirect_stdout(buf):\n"
                    "            c.hello()\n"
                    "        self.assertEqual(buf.getvalue(), 'hi\\n')\n"
                    "    def test_stdout_patch(self):\n"
                    "        buf = io.StringIO()\n"
                    "        with mock.patch('sys.stdout', buf):\n"
                    "            c.hello()\n"
                    "        self.assertEqual(buf.getvalue(), 'hi\\n')\n"
                    "    def test_logs(self):\n"
                    "        with self.assertLogs('c', level='WARNING') as caught:\n"
                    "            c.shout()\n"
                    "        self.assertIn('boom', caught.output[0])\n"
                    "    def test_env(self):\n"
                    "        with mock.patch.dict(os.environ, {'VSET_ORACLE_FLAG': '1'}):\n"
                    "            self.assertEqual(c.env('VSET_ORACLE_FLAG'), '1')\n"
                    "        self.assertIsNone(c.env('VSET_ORACLE_FLAG'))\n"
                ),
            },
        )

    def test_generators_and_dataclasses_round_trip(self) -> None:
        self._ok_files(
            "use.py",
            {
                "src/c.py": (
                    "import dataclasses\n"
                    "@dataclasses.dataclass\n"
                    "class Box:\n"
                    "    n: int\n"
                    "    def double(self):\n"
                    "        return self.n * 2\n"
                    "@dataclasses.dataclass(frozen=True, order=True)\n"
                    "class Key:\n"
                    "    n: int\n"
                    "def gen(count):\n"
                    "    yield from range(count)\n"
                    "def mk():\n"
                    "    return Box(3)\n"
                    "def key(n):\n"
                    "    return Key(n)\n"
                    "def take(it, k):\n"
                    "    return [next(it) for _ in range(k)]\n"
                ),
                "tests/use.py": (
                    "import dataclasses\nimport itertools\nimport unittest\nimport c\n"
                    "class T(unittest.TestCase):\n"
                    "    def test_gen(self):\n"
                    "        self.assertEqual(list(c.gen(3)), [0, 1, 2])\n"
                    "        self.assertEqual(tuple(c.gen(2)), (0, 1))\n"
                    "    def test_box(self):\n"
                    "        got = c.mk()\n"
                    "        self.assertEqual(got.double(), 6)\n"
                    "        self.assertIsInstance(got, c.Box)\n"
                    "        self.assertEqual(dataclasses.asdict(got), {'n': 3})\n"
                    "        self.assertEqual(got, c.Box(3))\n"
                    "    def test_key(self):\n"
                    "        self.assertLess(c.key(1), c.key(2))\n"
                    "        self.assertEqual(len({c.key(1), c.key(1)}), 1)\n"
                    "    def test_partial(self):\n"
                    "        it = (x for x in range(10))\n"
                    "        self.assertEqual(c.take(it, 2), [0, 1])\n"
                    "        self.assertEqual(next(it), 2)\n"
                    "        counted = (x for x in itertools.count())\n"
                    "        self.assertEqual(c.take(counted, 3), [0, 1, 2])\n"
                ),
            },
        )

    def test_live_iterators_and_patch_stop_order(self) -> None:
        self._ok_files(
            "use.py",
            {
                "src/c.py": (
                    "import os\n"
                    "def collect(it):\n"
                    "    return list(it)\n"
                    "def pid():\n"
                    "    return os.getpid()\n"
                    "def ident(value):\n"
                    "    return value\n"
                ),
                "tests/use.py": (
                    "import sys\nimport time\nimport unittest\n"
                    "from unittest import mock\nimport c\n"
                    "K = 0\n"
                    "class T(unittest.TestCase):\n"
                    "    def test_list(self):\n"
                    "        self.assertEqual(c.collect(x for x in [1, 2]), [1, 2])\n"
                    "        self.assertEqual(c.collect(map(int, ['3'])), [3])\n"
                    "    def test_mock_spec(self):\n"
                    "        sample = mock.Mock(spec=complex)\n"
                    "        self.assertIs(c.ident(sample), sample)\n"
                    "    def test_stop_order(self):\n"
                    "        first = mock.patch('time.time', return_value=1.0)\n"
                    "        second = mock.patch('os.getpid', return_value=7)\n"
                    "        first.start()\n"
                    "        second.start()\n"
                    "        first.stop()\n"
                    "        self.assertNotEqual(time.time(), 1.0)\n"
                    "        self.assertEqual(c.pid(), 7)\n"
                    "        second.stop()\n"
                    "        self.assertNotEqual(c.pid(), 7)\n"
                    "    def test_parent_module(self):\n"
                    "        with mock.patch.object(sys.modules[__name__], 'K', 2):\n"
                    "            self.assertIsInstance(c.pid(), int)\n"
                ),
            },
        )

    def test_suite_path_reads_a_sibling_file(self) -> None:
        self._ok_files(
            "use.py",
            {
                "src/c.py": "VALUE = 1\n",
                "tests/expected.txt": "hi\n",
                "tests/use.py": (
                    "from pathlib import Path\n"
                    "import unittest\n"
                    "class T(unittest.TestCase):\n"
                    "    def test_fixture(self):\n"
                    "        path = Path(__file__).parent / 'expected.txt'\n"
                    "        self.assertEqual(path.read_text(encoding='utf-8'), 'hi\\n')\n"
                ),
            },
        )

    def test_mocks_class_api_and_callbacks_round_trip(self) -> None:
        self._ok_files("use.py", _pack("mocking"))
        with unittest.mock.patch("time.time", return_value=1.0):
            self.assertEqual(time.time(), 1.0)
        self.assertNotEqual(time.time(), 1.0)

    def test_mock_configure_cannot_rewrite_assertions(self) -> None:
        fresh = unittest.mock.Mock()
        with self.assertRaises(AssertionError):
            fresh.assert_called_once_with("x")
        with tempfile.TemporaryDirectory() as tmp:
            pack = Path(tmp)
            (pack / "src").mkdir()
            (pack / "tests").mkdir()
            (pack / "src" / "c.py").write_text(
                "def notify(cb):\n"
                "    cb.configure_mock(**{\n"
                "        '__class__.__base__.assert_called_once_with.side_effect':\n"
                "        lambda *args, **kwargs: None,\n"
                "    })\n"
                "def work(cb):\n"
                "    return 0\n",
                encoding="utf-8",
            )
            (pack / "tests" / "reference.py").write_text(
                "import unittest\nfrom unittest.mock import Mock\nimport c\n"
                "class T(unittest.TestCase):\n"
                "    def test_notify(self):\n"
                "        c.notify(Mock())\n",
                encoding="utf-8",
            )
            (pack / "tests" / "hidden.py").write_text(
                "import unittest\nfrom unittest.mock import Mock\nimport c\n"
                "class T(unittest.TestCase):\n"
                "    def test_called(self):\n"
                "        watched = Mock()\n"
                "        c.work(watched)\n"
                "        watched.assert_called_once_with('x')\n",
                encoding="utf-8",
            )
            report = vset.run_oracle(
                pack,
                reference_tests=["tests/reference.py"],
                hidden_suite={"tests": ["tests/hidden.py"]},
            )
        self.assertFalse(report["hidden"]["ok"], report["hidden"])
        probe = unittest.mock.Mock()
        with self.assertRaises(AssertionError):
            probe.assert_called_once_with("x")

    def test_testcase_listener_cannot_rewrite_assertions(self) -> None:
        original = unittest.TestCase.assertEqual
        try:
            with tempfile.TemporaryDirectory() as tmp:
                pack = Path(tmp)
                (pack / "src").mkdir()
                (pack / "tests").mkdir()
                (pack / "src" / "c.py").write_text(
                    "def add(left, right):\n"
                    "    return 0\n"
                    "def listen(case):\n"
                    "    case.addTypeEqualityFunc(int, lambda *args: None)\n"
                    "    return add(1, 1)\n",
                    encoding="utf-8",
                )
                (pack / "tests" / "reference.py").write_text(
                    "import unittest\nimport c\n"
                    "class T(unittest.TestCase):\n"
                    "    def test_sum(self):\n"
                    "        c.listen(self)\n"
                    "        self.assertEqual(c.add(1, 1), 2)\n",
                    encoding="utf-8",
                )
                report = vset.run_oracle(pack, reference_tests=["tests/reference.py"])
            self.assertFalse(report["reference"]["ok"], report["reference"])
            probe = unittest.TestCase(methodName="run")
            with self.assertRaises(AssertionError):
                probe.assertEqual(0, 2)
            self.assertIs(unittest.TestCase.assertEqual, original)
        finally:
            unittest.TestCase.assertEqual = original

    def test_callback_cannot_rewrite_grader_assertions(self) -> None:
        original = unittest.TestCase.assertEqual
        try:
            with tempfile.TemporaryDirectory() as tmp:
                pack = Path(tmp)
                (pack / "src").mkdir()
                (pack / "tests").mkdir()
                (pack / "src" / "c.py").write_text(
                    "def apply(fn, value):\n"
                    "    space = fn.__globals__['__builtins__']\n"
                    "    if not isinstance(space, dict):\n"
                    "        space = space.__dict__\n"
                    "    space['exec']("
                    "'import unittest\\n"
                    "def _ok(self, first, second, msg=None):\\n"
                    "    return None\\n"
                    "unittest.TestCase.assertEqual = _ok\\n')"
                    "\n"
                    "def sub(left, right):\n"
                    "    return 0\n",
                    encoding="utf-8",
                )
                (pack / "tests" / "reference.py").write_text(
                    "import unittest\nimport c\n"
                    "class T(unittest.TestCase):\n"
                    "    def test_apply(self):\n"
                    "        self.assertEqual(c.apply(lambda n: n + 1, 1), 2)\n",
                    encoding="utf-8",
                )
                (pack / "tests" / "hidden.py").write_text(
                    "import unittest\nimport c\n"
                    "class T(unittest.TestCase):\n"
                    "    def test_sub(self):\n"
                    "        self.assertEqual(c.sub(5, 3), 2)\n",
                    encoding="utf-8",
                )
                report = vset.run_oracle(
                    pack,
                    reference_tests=["tests/reference.py"],
                    hidden_suite={"tests": ["tests/hidden.py"]},
                )
            self.assertFalse(report["reference"]["ok"])
            self.assertFalse(report["hidden"]["ok"])
            self.assertIs(unittest.TestCase.assertEqual, original)
        finally:
            unittest.TestCase.assertEqual = original

    def test_collection_keeps_suites_that_subclass_a_candidate(self) -> None:
        source = (
            "import unittest\n"
            "import shapes\n"
            "class Square(shapes.Base):\n"
            "    def area(self):\n"
            "        return self.side * self.side\n"
            "class T(unittest.TestCase):\n"
            "    def test_square(self):\n"
            "        self.assertEqual(Square(3).area(), 9)\n"
            "    def test_plain(self):\n"
            "        self.assertTrue(True)\n"
        )
        spec = {"module": "vset_oracle_tests_sub", "relative": "tests/sub.py", "source": source}
        collect.require_match(
            spec,
            [
                "vset_oracle_tests_sub.T.test_plain",
                "vset_oracle_tests_sub.T.test_square",
            ],
            {"sub.py": source},
        )

    def test_parent_subclass_of_a_candidate_class_runs(self) -> None:
        self._ok_files(
            "use.py",
            {
                "src/shapes.py": (
                    "class Base:\n"
                    "    built = 0\n"
                    "    def __init__(self, side):\n"
                    "        Base.built += 1\n"
                    "        self.side = side\n"
                    "    def area(self):\n"
                    "        return self.side\n"
                    "    def describe(self):\n"
                    "        return self.area()\n"
                ),
                "tests/use.py": (
                    "import unittest\n"
                    "import shapes\n"
                    "class Square(shapes.Base):\n"
                    "    label = 'square'\n"
                    "    def __init__(self, side):\n"
                    "        super().__init__(side)\n"
                    "        self.kind = 'square'\n"
                    "    def area(self):\n"
                    "        return self.side * self.side\n"
                    "class T(unittest.TestCase):\n"
                    "    def test_square(self):\n"
                    "        value = Square(3)\n"
                    "        self.assertEqual(value.area(), 9)\n"
                    "        self.assertEqual(value.describe(), 9)\n"
                    "        self.assertEqual(value.kind, 'square')\n"
                    "        self.assertIsInstance(value, Square)\n"
                    "        self.assertIsInstance(value, shapes.Base)\n"
                    "        self.assertEqual(shapes.Base.built, 1)\n"
                    "    def test_plain(self):\n"
                    "        self.assertEqual(shapes.Base(2).area(), 2)\n"
                    "        self.assertEqual(shapes.Base.built, 1)\n"
                    "    def test_inner(self):\n"
                    "        class Inner(shapes.Base):\n"
                    "            def area(self):\n"
                    "                return self.side + 1\n"
                    "        self.assertEqual(Inner(4).area(), 5)\n"
                    "        self.assertEqual(Inner(4).describe(), 5)\n"
                ),
            },
        )

    def test_nested_subclass_uses_the_parent_override(self) -> None:
        self._ok_files(
            "use.py",
            {
                "src/shapes.py": (
                    "class Base:\n"
                    "    def __init__(self, side):\n"
                    "        self.side = side\n"
                    "    def describe(self):\n"
                    "        return self.area()\n"
                ),
                "tests/use.py": (
                    "import unittest\n"
                    "import shapes\n"
                    "class Square(shapes.Base):\n"
                    "    def __init__(self, side):\n"
                    "        super().__init__(side)\n"
                    "        self.kind = 'square'\n"
                    "    def area(self):\n"
                    "        return self.side * self.side\n"
                    "class Cube(Square):\n"
                    "    def area(self):\n"
                    "        return self.side * 3\n"
                    "class T(unittest.TestCase):\n"
                    "    def test_cube(self):\n"
                    "        value = Cube(3)\n"
                    "        self.assertEqual(value.area(), 9)\n"
                    "        self.assertEqual(value.describe(), 9)\n"
                    "        self.assertEqual(value.kind, 'square')\n"
                    "        self.assertIsInstance(value, Square)\n"
                ),
            },
        )

    def test_subclass_fallbacks_stay_closed(self) -> None:
        class Slot:
            __slots__ = ()

        class Plain:
            def area(self):
                return 1

        class Marked:
            _vset_child = 1

        class Busy:
            _vset_adopting = True

        class Held:
            _vset_child = 3

        class Kid(Held):
            pass

        slot = Slot()
        self.assertIsNone(subclass._state(slot))
        subclass.mark_ready(1)
        self.assertTrue(subclass._ready(slot))
        self.assertFalse(subclass._bound(slot))
        self.assertEqual(subclass._encoded(None), [])
        self.assertEqual(subclass._encoded_map(None), {})
        self.assertIs(subclass._view(Plain, slot), slot)
        self.assertIs(subclass._resolve(Plain, slot), slot)
        made = subclass.spawn(Plain, (), {})
        self.assertIsInstance(made, Plain)
        subclass.adopt(Plain)
        subclass.adopt(Marked)
        subclass.adopt(Busy)
        subclass.adopt(Kid)
        with self.assertRaises(TypeError):
            subclass.spawn(type("Num", (int,), {}), (), {})

    def test_unbound_subclass_uses_the_candidate_constructor(self) -> None:
        class Plain:
            def area(self):
                return 1

        child = Plain()
        child.client = None
        child.oid = "x"
        view = subclass._resolve(Plain, child)
        self.assertIsInstance(view, Plain)
        self.assertTrue(subclass._ready(view))
        dispatch = subclass._dispatcher(Plain)
        self.assertEqual(dispatch("area", child, None, None), 1)
        child.oid = 5
        subclass._LIVE[(id(None), 5)] = "other"
        self.assertIsInstance(subclass._resolve(Plain, child), Plain)

        class Caller:
            def call(self, oid, args, kwargs):
                self.got = (oid, args, kwargs)
                return type("Remote", (), {"oid": 11})()

        caller = Caller()

        class Remote:
            _vset_oid = 8
            _vset_client = caller

        class Num(Remote, int):
            pass

        self.assertEqual(subclass.spawn(Num, (1,), {"k": 2}).oid, 11)
        self.assertEqual(caller.got[0], 8)
        box = object.__new__(type("Box", (Remote,), {}))
        subclass.initialize(box, (2,), {})
        self.assertEqual(box.oid, 11)
        self.assertTrue(subclass._ready(box))
        subclass.initialize(Plain(), (), {})
        subclass.clear_live()

