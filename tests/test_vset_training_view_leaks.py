#!/usr/bin/env python3
"""Hidden-suite text must not leak into training_view under any key.

Lowercase ``hidden_tests`` is caught; renamed keys, nested containers, and
value-only leaks must be refused as well (vset_record_checks training view).
"""

from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path

_TESTS = Path(__file__).resolve().parent
if str(_TESTS) not in sys.path:
    sys.path.insert(0, str(_TESTS))

from vset_testutil import ACCEPT, PACK, load_record as _load, vset  # noqa: E402

HIDDEN = (PACK / "tests/hidden_sub.py").read_text(encoding="utf-8")

FORGES = {
    "HIDDEN_TESTS": {"HIDDEN_TESTS": HIDDEN},
    "private_tests": {"private_tests": HIDDEN},
    "oracle_suite": {"oracle_suite": HIDDEN},
    "grading_tests": {"grading_tests": HIDDEN},
    "tests_source": {"tests_source": HIDDEN},
    "nested_object": {"notes": {"private_tests": HIDDEN}},
    "nested_list": {"extras": [{"grading_tests": HIDDEN}]},
    "value_only": {"decision_basis": HIDDEN},
}


def _record(extra: dict | None = None) -> dict:
    record = _load(ACCEPT / "issue-patch-validated.json")
    if extra:
        record = copy.deepcopy(record)
        record["training_view"].update(extra)
    return record


class HiddenSuiteLeakForges(unittest.TestCase):
    def test_control_honest_record_passes(self) -> None:
        self.assertEqual(vset.validate_record(_record()), [])

    def test_control_lowercase_hidden_tests_caught(self) -> None:
        record = _record({"hidden_tests": HIDDEN})
        self.assertTrue(vset.validate_record(record))
        errors, _execution = vset.validate_record_with_oracle(record, PACK)
        self.assertTrue(errors)

    def test_forge_validate_record_refuses_leak(self) -> None:
        for name, extra in FORGES.items():
            with self.subTest(variant=name):
                self.assertTrue(
                    vset.validate_record(_record(extra)),
                    f"{name}: hidden suite leaked with 0 errors",
                )

    def test_forge_oracle_refuses_leak(self) -> None:
        for name, extra in FORGES.items():
            with self.subTest(variant=name):
                errors, _execution = vset.validate_record_with_oracle(_record(extra), PACK)
                self.assertTrue(errors, f"{name}: oracle accepted hidden-suite leak")


if __name__ == "__main__":
    unittest.main()
