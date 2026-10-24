"""Regression: patched src/ must not be able to neuter oracle suites.

Each forge drops Counter.sub and rewrites unittest from inside src/counter.py.
The oracle must refuse both; the honest record must still pass.
"""
from __future__ import annotations

import json
import shutil
import subprocess  # nosec B404
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from vset_testutil import cli, vset  # noqa: E402

PACK = ROOT / "fixtures/vset/repo-pack-counter"
RECORD = ROOT / "fixtures/vset/records/accept/issue-patch-validated.json"

_BASE = '''import unittest

class Counter:
    def __init__(self, value=0):
        self._value = int(value)
    def add(self, delta):
        self._value += int(delta)
        return self._value
    def get(self):
        return self._value

def _neuter(cls):
    for name in list(vars(cls)):
        if name.startswith("test"):
            setattr(cls, name, lambda self: None)
'''

FORGES = {
    "init_subclass": _BASE + '''
_orig = unittest.TestCase.__dict__["__init_subclass__"]
def _hook(cls, **kw):
    _orig.__get__(None, cls)(**kw)
    _neuter(cls)
unittest.TestCase.__init_subclass__ = classmethod(_hook)
''',
    "setUpClass": _BASE + '''
unittest.TestCase.setUpClass = classmethod(_neuter)
''',
}


def _record(source: str | None = None) -> dict:
    rec = json.loads(RECORD.read_text())
    if source is not None:
        rec["payload"]["patch"]["files"]["src/counter.py"] = source
    return rec


_CHILD = """
import json, sys
sys.path.insert(0, sys.argv[1])
from vset_oracle import validate_record_with_oracle
from pathlib import Path
rec = json.loads(sys.stdin.read())
errors, _ = validate_record_with_oracle(rec, Path(sys.argv[2]))
print(len(errors))
"""


def _error_count(rec: dict) -> int:
    # Fresh interpreter per case: a forge that escapes the oracle would
    # otherwise also corrupt this test process and every case after it.
    # Fresh interpreter, fixed argv, no shell. A forge must not share this process.
    out = subprocess.run(  # nosec B603  # nosemgrep: python.lang.security.audit.dangerous-subprocess-use-audit.dangerous-subprocess-use-audit
        [sys.executable, "-c", _CHILD, str(ROOT.parent / "pipelines"), str(PACK)],
        input=json.dumps(rec), capture_output=True, text=True, timeout=120, check=True,
    )
    return int(out.stdout.strip().splitlines()[-1])


class InProcessForgeTests(unittest.TestCase):
    def test_honest_record_passes(self) -> None:
        self.assertEqual(_error_count(_record()), 0)

    def test_forges_are_refused(self) -> None:
        for name, source in FORGES.items():
            with self.subTest(forge=name):
                self.assertGreater(_error_count(_record(source)), 0, f"{name} forge was accepted")

    def test_candidate_values_compare_with_literals(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            pack = Path(tmp)
            (pack / "src").mkdir()
            (pack / "tests").mkdir()
            (pack / "src" / "c.py").write_text(
                "class Money:\n"
                "    def __init__(self, cents):\n"
                "        self.cents = cents\n"
                "    def __eq__(self, other):\n"
                "        if isinstance(other, Money):\n"
                "            return self.cents == other.cents\n"
                "        if isinstance(other, (int, float)):\n"
                "            return self.cents == other\n"
                "        return NotImplemented\n"
                "    def __lt__(self, other):\n"
                "        if isinstance(other, Money):\n"
                "            return self.cents < other.cents\n"
                "        return self.cents < other\n"
                "def money():\n"
                "    return Money(5)\n",
                encoding="utf-8",
            )
            (pack / "tests" / "use.py").write_text(
                "import unittest\nimport c\n"
                "class T(unittest.TestCase):\n"
                "    def test_equal(self):\n"
                "        self.assertEqual(c.money(), 5)\n"
                "    def test_less(self):\n"
                "        self.assertLess(c.money(), 10)\n",
                encoding="utf-8",
            )
            report = vset.run_oracle(pack, reference_tests=["tests/use.py"])
        self.assertTrue(report["reference"]["ok"], report["reference"])

    def test_almost_equal_does_not_trust_candidate_subtraction(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            pack = Path(tmp)
            (pack / "src").mkdir()
            (pack / "tests").mkdir()
            (pack / "src" / "c.py").write_text(
                "class E:\n"
                "    def __eq__(self, other):\n"
                "        return False\n"
                "    def __sub__(self, other):\n"
                "        return 0\n"
                "    def __rsub__(self, other):\n"
                "        return 0\n"
                "def add(a, b):\n"
                "    return E()\n"
                "def total(a, b):\n"
                "    return a + b\n",
                encoding="utf-8",
            )
            (pack / "tests" / "use.py").write_text(
                "import unittest\nimport c\n"
                "class T(unittest.TestCase):\n"
                "    def test_almost(self):\n"
                "        self.assertAlmostEqual(c.add(1, 2), 3)\n"
                "    def test_places(self):\n"
                "        self.assertAlmostEqual(c.add(1, 2), 3.0, places=3)\n"
                "    def test_right(self):\n"
                "        self.assertAlmostEqual(3, c.add(1, 2))\n"
                "    def test_delta(self):\n"
                "        self.assertAlmostEqual(c.add(1, 2), 3, delta=0.1)\n"
                "    def test_number(self):\n"
                "        self.assertAlmostEqual(c.total(1, 2), 3)\n",
                encoding="utf-8",
            )
            report = vset.run_oracle(pack, reference_tests=["tests/use.py"])
        by_name = {
            row["id"].rsplit(".", 1)[-1]: row["status"]
            for row in report["reference"]["tests"]
        }
        self.assertEqual(by_name["test_number"], "ok")
        for name in ("test_almost", "test_places", "test_right", "test_delta"):
            self.assertNotEqual(by_name[name], "ok", name)
        self.assertFalse(report["reference"]["ok"])

    def test_import_time_print_stays_inside_the_json_report(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            pack = Path(tmp) / "pack"
            shutil.copytree(PACK, pack)
            counter = pack / "src" / "counter.py"
            counter.write_text("print('IMPORT-TIME-INJECTED')\n" + counter.read_text(encoding="utf-8"), encoding="utf-8")
            proc = cli("--oracle", "--pack", str(pack), str(RECORD))
        payload = json.loads(proc.stdout)
        self.assertNotIn("IMPORT-TIME-INJECTED", proc.stdout)
        self.assertTrue(payload["records"][0]["oracle_execution"]["reference_ok"])
        with tempfile.TemporaryDirectory() as tmp:
            pack = Path(tmp)
            (pack / "src").mkdir()
            (pack / "tests").mkdir()
            (pack / "src" / "c.py").write_text(
                "print('IMPORT-TIME-INJECTED')\ndef value():\n    return 1\n",
                encoding="utf-8",
            )
            (pack / "tests" / "use.py").write_text(
                "import unittest\nimport c\n"
                "class T(unittest.TestCase):\n"
                "    def test_value(self):\n"
                "        self.assertEqual(c.value(), 1)\n",
                encoding="utf-8",
            )
            report = vset.run_oracle(pack, reference_tests=["tests/use.py"])
        self.assertTrue(report["reference"]["ok"], report["reference"])
        self.assertIn("IMPORT-TIME-INJECTED", report["reference"].get("captured_output", ""))
