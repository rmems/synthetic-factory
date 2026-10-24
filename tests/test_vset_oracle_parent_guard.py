"""Candidate code must not be able to rewrite the grader's assertions."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

_TESTS = Path(__file__).resolve().parent
if str(_TESTS) not in sys.path:
    sys.path.insert(0, str(_TESTS))

from vset_testutil import vset  # noqa: E402


def _grade(src: str, reference: str, hidden: str | None = None):
    with tempfile.TemporaryDirectory() as tmp:
        pack = Path(tmp)
        (pack / "src").mkdir()
        (pack / "tests").mkdir()
        (pack / "src" / "c.py").write_text(src, encoding="utf-8")
        (pack / "tests" / "reference.py").write_text(reference, encoding="utf-8")
        if hidden is None:
            return vset.run_oracle(pack, reference_tests=["tests/reference.py"])
        (pack / "tests" / "hidden.py").write_text(hidden, encoding="utf-8")
        return vset.run_oracle(
            pack,
            reference_tests=["tests/reference.py"],
            hidden_suite={"tests": ["tests/hidden.py"]},
        )


class ParentGuardTests(unittest.TestCase):
    def test_mock_configure_cannot_rewrite_assertions(self) -> None:
        fresh = unittest.mock.Mock()
        with self.assertRaises(AssertionError):
            fresh.assert_called_once_with("x")
        report = _grade(
            "def notify(cb):\n"
            "    cb.configure_mock(**{\n"
            "        '__class__.__base__.assert_called_once_with.side_effect':\n"
            "        lambda *args, **kwargs: None,\n"
            "    })\n"
            "def work(cb):\n"
            "    return 0\n",
            "import unittest\nfrom unittest.mock import Mock\nimport c\n"
            "class T(unittest.TestCase):\n"
            "    def test_notify(self):\n"
            "        c.notify(Mock())\n",
            "import unittest\nfrom unittest.mock import Mock\nimport c\n"
            "class T(unittest.TestCase):\n"
            "    def test_called(self):\n"
            "        watched = Mock()\n"
            "        c.work(watched)\n"
            "        watched.assert_called_once_with('x')\n",
        )
        self.assertFalse(report["hidden"]["ok"], report["hidden"])
        probe = unittest.mock.Mock()
        with self.assertRaises(AssertionError):
            probe.assert_called_once_with("x")

    def test_testcase_listener_cannot_rewrite_assertions(self) -> None:
        original = unittest.TestCase.assertEqual
        try:
            report = _grade(
                "def add(left, right):\n"
                "    return 0\n"
                "def listen(case):\n"
                "    case.addTypeEqualityFunc(int, lambda *args: None)\n"
                "    return add(1, 1)\n",
                "import unittest\nimport c\n"
                "class T(unittest.TestCase):\n"
                "    def test_sum(self):\n"
                "        c.listen(self)\n"
                "        self.assertEqual(c.add(1, 1), 2)\n",
            )
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
            report = _grade(
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
                "import unittest\nimport c\n"
                "class T(unittest.TestCase):\n"
                "    def test_apply(self):\n"
                "        self.assertEqual(c.apply(lambda n: n + 1, 1), 2)\n",
                "import unittest\nimport c\n"
                "class T(unittest.TestCase):\n"
                "    def test_sub(self):\n"
                "        self.assertEqual(c.sub(5, 3), 2)\n",
            )
            self.assertFalse(report["reference"]["ok"])
            self.assertFalse(report["hidden"]["ok"])
            self.assertIs(unittest.TestCase.assertEqual, original)
        finally:
            unittest.TestCase.assertEqual = original
