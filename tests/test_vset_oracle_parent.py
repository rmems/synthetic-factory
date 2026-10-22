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
                    "def gen(count):\n"
                    "    yield from range(count)\n"
                    "def mk():\n"
                    "    return Box(3)\n"
                ),
                "tests/use.py": (
                    "import dataclasses\nimport unittest\nimport c\n"
                    "class T(unittest.TestCase):\n"
                    "    def test_gen(self):\n"
                    "        self.assertEqual(list(c.gen(3)), [0, 1, 2])\n"
                    "        self.assertEqual(tuple(c.gen(2)), (0, 1))\n"
                    "    def test_box(self):\n"
                    "        self.assertEqual(c.mk().n, 3)\n"
                    "        self.assertEqual(c.mk(), c.mk())\n"
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

