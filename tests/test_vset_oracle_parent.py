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
def _pack(name: str) -> dict[str, str]:
    path = _TESTS / "fixtures" / "vset" / "oracle-packs" / f"{name}.json"
    return json.loads(path.read_text(encoding="utf-8"))


_BASE_SRC = (
    "class Base:\n"
    "    built = 0\n"
    "    def __init__(self, side):\n"
    "        Base.built += 1\n"
    "        self.side = side\n"
    "    def area(self):\n"
    "        return self.side\n"
    "    def describe(self):\n"
    "        return self.area()\n"
    "    def tagged(self):\n"
    "        return self.label\n"
    "    def scaled(self):\n"
    "        return self.side * self._scale()\n"
    "    def show(self):\n"
    "        return self.unit\n"
    "    def marked(self):\n"
    "        return type(self).stamp()\n"
    "    def born(self):\n"
    "        return type(self).make(self.side).side\n"
    "    def cmp(self, other):\n"
    "        return self == other\n"
)

_SQUARE_SRC = (
    "class Square(shapes.Base):\n"
    "    label = 'square'\n"
    "    def __init__(self, side):\n"
    "        super().__init__(side)\n"
    "        self.kind = 'square'\n"
    "    def area(self):\n"
    "        return self.side * self.side\n"
    "    def _scale(self):\n"
    "        return 2\n"
    "    @property\n"
    "    def unit(self):\n"
    "        return 'cm'\n"
    "    @staticmethod\n"
    "    def stamp():\n"
    "        return 'ok'\n"
    "    @classmethod\n"
    "    def make(cls, side):\n"
    "        return cls(side)\n"
    "    def __eq__(self, other):\n"
    "        return getattr(other, 'side', None) == self.side\n"
)


def _shapes(extra: str, tests: str) -> dict[str, str]:
    suite = "import unittest\nimport shapes\n" + _SQUARE_SRC + extra
    suite += "class T(unittest.TestCase):\n" + tests
    return {"src/shapes.py": _BASE_SRC, "tests/use.py": suite}


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

    def test_stdlib_exceptions_match_assert_raises(self) -> None:
        self._ok_files(
            "use.py",
            {
                "src/c.py": (
                    "import decimal\nimport json\n"
                    "from json import JSONDecodeError as Decode\n"
                    "def parse(text):\n    return json.loads(text)\n"
                    "def dec(text):\n    return decimal.Decimal(text)\n"
                ),
                "tests/use.py": (
                    "import decimal\nimport json\nimport unittest\nimport c\n"
                    "class T(unittest.TestCase):\n"
                    "    def test_json(self):\n"
                    "        with self.assertRaises(json.JSONDecodeError):\n"
                    "            c.parse('{')\n"
                    "        with self.assertRaises(c.Decode):\n"
                    "            c.parse('{')\n"
                    "    def test_decimal(self):\n"
                    "        with self.assertRaises(decimal.InvalidOperation):\n"
                    "            c.dec('x')\n"
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
                    "def info():\n    logging.getLogger('c').info('hi')\n"
                    "def debug():\n    logging.getLogger('c').debug('lo')\n"
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
                    "    def test_info(self):\n"
                    "        with self.assertLogs('c', level='INFO') as caught:\n"
                    "            c.info()\n"
                    "        self.assertIn('hi', caught.output[0])\n"
                    "    def test_debug(self):\n"
                    "        with self.assertLogs('c', level='DEBUG') as caught:\n"
                    "            c.debug()\n"
                    "        self.assertIn('lo', caught.output[0])\n"
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

    def test_parent_subclass_of_a_candidate_class_runs(self) -> None:
        tests = (
            "    def test_square(self):\n"
            "        before = shapes.Base.built\n"
            "        value = Square(3)\n"
            "        self.assertEqual(value.area(), 9)\n"
            "        self.assertEqual(value.describe(), 9)\n"
            "        self.assertEqual(value.kind, 'square')\n"
            "        self.assertEqual(value.tagged(), 'square')\n"
            "        self.assertEqual(value.scaled(), 6)\n"
            "        self.assertEqual(value.show(), 'cm')\n"
            "        self.assertEqual(value.marked(), 'ok')\n"
            "        self.assertIsInstance(value, Square)\n"
            "        self.assertIsInstance(value, shapes.Base)\n"
            "        self.assertEqual(shapes.Base.built, before + 1)\n"
            "        self.assertEqual(value.born(), 3)\n"
            "        self.assertTrue(value.cmp(Square(3)))\n"
            "    def test_plain(self):\n"
            "        before = shapes.Base.built\n"
            "        self.assertEqual(shapes.Base(2).area(), 2)\n"
            "        self.assertEqual(shapes.Base.built, before + 1)\n"
            "    def test_inner(self):\n"
            "        class Inner(shapes.Base):\n"
            "            def area(self):\n"
            "                return self.side + 1\n"
            "        self.assertEqual(Inner(4).area(), 5)\n"
            "        self.assertEqual(Inner(4).describe(), 5)\n"
        )
        self._ok_files("use.py", _shapes("", tests))

    def test_nested_subclass_uses_the_parent_override(self) -> None:
        extra = (
            "class Cube(Square):\n"
            "    def area(self):\n"
            "        return self.side * 3\n"
        )
        tests = (
            "    def test_cube(self):\n"
            "        value = Cube(3)\n"
            "        self.assertEqual(value.area(), 9)\n"
            "        self.assertEqual(value.describe(), 9)\n"
            "        self.assertEqual(value.kind, 'square')\n"
            "        self.assertIsInstance(value, Square)\n"
            "        self.assertEqual(shapes.Base.built, 1)\n"
        )
        self._ok_files("use.py", _shapes(extra, tests))
