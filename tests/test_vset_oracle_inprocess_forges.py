"""Regression: patched src/ must not be able to neuter oracle suites.

Each forge drops Counter.sub and rewrites unittest from inside src/counter.py.
The oracle must refuse both; the honest record must still pass.
"""
from __future__ import annotations

import json
import subprocess  # nosec B404
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent
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
