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


def _reference(src: str, tests: str):
    with tempfile.TemporaryDirectory() as tmp:
        pack = Path(tmp)
        (pack / "src").mkdir()
        (pack / "tests").mkdir()
        (pack / "src" / "c.py").write_text(src, encoding="utf-8")
        body = "import unittest\nimport c\nclass T(unittest.TestCase):\n" + tests
        (pack / "tests" / "use.py").write_text(body, encoding="utf-8")
        report = vset.run_oracle(pack, reference_tests=["tests/use.py"])
    statuses = {
        row["id"].rsplit(".", 1)[-1]: row["status"] for row in report["reference"]["tests"]
    }
    return report, statuses


def _eq_source(result: str) -> str:
    return (
        "class E:\n"
        "    def __eq__(self, other):\n"
        f"        return {result}\n"
        "    def __sub__(self, other):\n"
        "        return 0\n"
        "    def __rsub__(self, other):\n"
        "        return 0\n"
        "def add(a, b):\n"
        "    return E()\n"
        "def total(a, b):\n"
        "    return a + b\n"
    )


def _expect_refused(
    case: unittest.TestCase, source: str, tests: str, refused: tuple[str, ...]
) -> None:
    report, by_name = _reference(source, tests)
    case.assertEqual(by_name["test_number"], "ok")
    for name in refused:
        case.assertNotEqual(by_name[name], "ok", name)
    case.assertFalse(report["reference"]["ok"])


class InProcessForgeTests(unittest.TestCase):
    def test_honest_record_passes(self) -> None:
        self.assertEqual(_error_count(_record()), 0)

    def test_forges_are_refused(self) -> None:
        for name, source in FORGES.items():
            with self.subTest(forge=name):
                self.assertGreater(_error_count(_record(source)), 0, f"{name} forge was accepted")

    def test_candidate_values_compare_with_literals(self) -> None:
        report, _statuses = _reference(
            "class Money:\n" "    def __init__(self, cents):\n" "        self.cents = cents\n" "    def __eq__(self, other):\n" "        if isinstance(other, Money):\n" "            return self.cents == other.cents\n"
            "        if isinstance(other, (int, float)):\n" "            return self.cents == other\n" "        return NotImplemented\n" "    def __lt__(self, other):\n" "        if isinstance(other, Money):\n" "            return self.cents < other.cents\n"
            "        return self.cents < other\n" "def money():\n" "    return Money(5)\n" "def huge():\n" "    return Money(1e20 + 1.0)\n", "    def test_equal(self):\n"
            "        self.assertEqual(c.money(), 5)\n" "        self.assertAlmostEqual(c.money(), 5)\n" "        self.assertEqual(c.huge(), 1e20)\n" "    def test_less(self):\n" "        self.assertLess(c.money(), 10)\n",
        )
        self.assertTrue(report["reference"]["ok"], report["reference"])

    def test_forged_equality_does_not_satisfy_parent_comparisons(self) -> None:
        cases = {
            "candidate_subtraction": (
                "False",
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
                ("test_almost", "test_places", "test_right", "test_delta"),
            ),
            "always_equal": (
                "True",
                "    def test_almost(self):\n"
                "        self.assertAlmostEqual(c.add(1, 2), 3)\n"
                "    def test_almost_right(self):\n"
                "        self.assertAlmostEqual(3, c.add(1, 2))\n"
                "    def test_equal(self):\n"
                "        self.assertEqual(c.add(1, 2), 3)\n"
                "    def test_equal_right(self):\n"
                "        self.assertEqual(3, c.add(1, 2))\n"
                "    def test_number(self):\n"
                "        self.assertAlmostEqual(c.total(1, 2), 3)\n",
                ("test_almost", "test_almost_right", "test_equal", "test_equal_right"),
            ),
        }
        for label, (result, tests, refused) in cases.items():
            with self.subTest(forge=label):
                _expect_refused(self, _eq_source(result), tests, refused)

    def test_alternating_eq_cannot_bypass_a_second_probe(self) -> None:
        report, by_name = _reference(
            "class E:\n" "    n = 0\n" "    def __eq__(self, other):\n" "        E.n += 1\n" "        return E.n % 2 == 1\n" "    def __sub__(self, other):\n"
            "        return 0\n" "    def __rsub__(self, other):\n" "        return 0\n" "def add(a, b):\n" "    return E()\n" "def total(a, b):\n"
            "    return a + b\n", "    def test_equal(self):\n" "        self.assertEqual(c.add(1, 2), 999)\n" "    def test_almost(self):\n" "        self.assertAlmostEqual(c.add(1, 2), 999)\n" "    def test_number(self):\n"
            "        self.assertAlmostEqual(c.total(1, 2), 3)\n",
        )
        self.assertEqual(by_name["test_number"], "ok")
        self.assertNotEqual(by_name["test_equal"], "ok")
        self.assertNotEqual(by_name["test_almost"], "ok")
        self.assertFalse(report["reference"]["ok"])

    def test_module_label_and_failing_state_cannot_force_equality(self) -> None:
        report, by_name = _reference(
            "class Liar:\n" "    __module__ = 'json'\n" "    def __eq__(self, other):\n" "        return True\n" "    __hash__ = None\n" "class Hidden:\n"
            "    @property\n" "    def __dict__(self):\n" "        raise RuntimeError('no')\n" "    def __eq__(self, other):\n" "        return True\n" "    __hash__ = None\n"
            "def liar():\n" "    return Liar()\n" "def hidden():\n" "    return Hidden()\n" "def total(a, b):\n" "    return a + b\n",
            "    def test_module(self):\n" "        self.assertEqual(c.liar(), 1)\n" "    def test_state(self):\n" "        self.assertEqual(c.hidden(), 1)\n" "    def test_number(self):\n" "        self.assertEqual(c.total(1, 2), 3)\n",
        )
        self.assertEqual(by_name["test_number"], "ok")
        self.assertNotEqual(by_name["test_module"], "ok")
        self.assertNotEqual(by_name["test_state"], "ok")
        self.assertFalse(report["reference"]["ok"])

    def test_many_fields_cannot_cover_every_expected_value(self) -> None:
        source = "".join(
            [
                "class E:\n",
                "    def __init__(self):\n",
                "        for i in range(-50, 51):\n",
                "            setattr(self, 'f%d' % (i + 50), i)\n",
                "    def __eq__(self, other):\n",
                "        return True\n",
                "    def __lt__(self, other):\n",
                "        return True\n",
                "    __hash__ = None\n",
                "def add(a, b):\n",
                "    return E()\n",
                "def total(a, b):\n",
                "    return a + b\n",
            ]
        )
        tests = "".join(
            [
                "    def test_equal(self):\n",
                "        self.assertEqual(c.add(1, 2), 3)\n",
                "    def test_less(self):\n",
                "        self.assertLess(c.add(1, 2), 10)\n",
                "    def test_number(self):\n",
                "        self.assertEqual(c.total(1, 2), 3)\n",
            ]
        )
        _expect_refused(self, source, tests, ("test_equal", "test_less"))

    def test_one_decoy_field_does_not_confirm_equality(self) -> None:
        source = (
            "class E:\n"
            "    def __init__(self):\n"
            "        self.cents = 5\n"
            "        self.extra = 9\n"
            "    def __eq__(self, other):\n"
            "        return True\n"
            "    __hash__ = None\n"
            "def add(a, b):\n"
            "    return E()\n"
            "def total(a, b):\n"
            "    return a + b\n"
        )
        tests = (
            "    def test_equal(self):\n"
            "        self.assertEqual(c.add(1, 2), 5)\n"
            "    def test_number(self):\n"
            "        self.assertEqual(c.total(1, 2), 3)\n"
        )
        _expect_refused(self, source, tests, ("test_equal",))

    def test_private_and_slot_fields_still_compare(self) -> None:
        report, _statuses = _reference(
            "class Hidden:\n" "    def __init__(self, cents):\n" "        self._cents = cents\n" "    def __eq__(self, other):\n" "        return self._cents == other\n" "    def __lt__(self, other):\n"
            "        return self._cents < other\n" "class Coin:\n" "    __slots__ = ('cents',)\n" "    def __init__(self, cents):\n" "        self.cents = cents\n" "    def __eq__(self, other):\n"
            "        return self.cents == other\n" "def hidden():\n" "    return Hidden(5)\n" "def coin():\n" "    return Coin(5)\n", "    def test_hidden(self):\n"
            "        self.assertEqual(c.hidden(), 5)\n" "        self.assertLess(c.hidden(), 10)\n" "    def test_coin(self):\n" "        self.assertEqual(c.coin(), 5)\n",
        )
        self.assertTrue(report["reference"]["ok"], report["reference"])

    def test_extra_fields_and_tuples_still_compare(self) -> None:
        source = "".join(
            [
                "class Money:\n",
                "    def __init__(self, cents, currency='USD'):\n",
                "        self.cents = cents\n",
                "        self.currency = currency\n",
                "    def __eq__(self, other):\n",
                "        if isinstance(other, int):\n",
                "            return self.cents == other\n",
                "        return NotImplemented\n",
                "    def __lt__(self, other):\n",
                "        return self.cents < other\n",
                "class Version:\n",
                "    def __init__(self, major, minor):\n",
                "        self.major = major\n",
                "        self.minor = minor\n",
                "    def __eq__(self, other):\n",
                "        return (self.major, self.minor) == tuple(other)\n",
                "def money():\n",
                "    return Money(500)\n",
                "def version():\n",
                "    return Version(1, 2)\n",
            ]
        )
        tests = "".join(
            [
                "    def test_money(self):\n",
                "        self.assertEqual(c.money(), 500)\n",
                "        self.assertLess(c.money(), 600)\n",
                "    def test_version(self):\n",
                "        self.assertEqual(c.version(), (1, 2))\n",
            ]
        )
        report, _statuses = _reference(source, tests)
        self.assertTrue(report["reference"]["ok"], report["reference"])

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
