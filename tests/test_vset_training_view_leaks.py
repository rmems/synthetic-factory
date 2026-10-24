#!/usr/bin/env python3
"""Hidden-suite text must not leak into training_view under any key.

Lowercase ``hidden_tests`` is caught; renamed keys, nested containers, and
the pack's own hidden source must be refused. Unrelated ``def test_`` code
is the factory's visible work and must pass.
"""

from __future__ import annotations

import copy
import hashlib
import sys
import unittest
from pathlib import Path

_TESTS = Path(__file__).resolve().parent
if str(_TESTS) not in sys.path:
    sys.path.insert(0, str(_TESTS))

from vset_testutil import ACCEPT, PACK, load_record as _load, vset  # noqa: E402

HIDDEN = (PACK / "tests/hidden_sub.py").read_text(encoding="utf-8")
REFERENCE = (PACK / "tests/reference.py").read_text(encoding="utf-8")
# A path list is not the hidden file, so a renamed key has to be refused
# on its own. The value-only case is the suite text under an innocent key.
SUITE_PATH = ["tests/hidden_sub.py"]
UNRELATED_TEST = (
    "def test_counter_add():\n"
    "    assert True\n"
    "\n"
    "import unittest\n"
)

FORGES = {
    "HIDDEN_TESTS": {"HIDDEN_TESTS": SUITE_PATH},
    "private_tests": {"private_tests": SUITE_PATH},
    "oracle_suite": {"oracle_suite": SUITE_PATH},
    "grading_tests": {"grading_tests": SUITE_PATH},
    "tests_source": {"tests_source": SUITE_PATH},
    "nested_object": {"notes": {"private_tests": SUITE_PATH}},
    "nested_list": {"extras": [{"grading_tests": SUITE_PATH}]},
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
        record = _record({"hidden_tests": SUITE_PATH})
        self.assertTrue(vset.validate_record(record))
        errors, _execution = vset.validate_record_with_oracle(record, PACK)
        self.assertTrue(errors)

    def test_lookalike_hidden_tests_key_is_refused(self) -> None:
        # Cyrillic small te, U+0442, folds to ASCII t.
        record = _record({"hidden_\u0442ests": SUITE_PATH})
        self.assertTrue(vset.validate_record(record))

    def test_one_quoted_marker_in_prose_passes(self) -> None:
        for prose in (
            "The note quotes def test_ as an example.",
            "The note quotes import unittest as an example.",
        ):
            with self.subTest(prose=prose):
                self.assertEqual(
                    vset.validate_record(_record({"decision_basis": prose})),
                    [],
                )

    def test_suite_text_used_as_a_key_is_refused(self) -> None:
        record = _record({HIDDEN: "notes"})
        self.assertTrue(vset.validate_record(record, pack_dir=PACK))
        errors, _execution = vset.validate_record_with_oracle(record, PACK)
        self.assertTrue(errors)

    def test_unrelated_test_code_in_observation_or_edit_passes(self) -> None:
        record = _record(
            {
                "steps": [{"observation": REFERENCE}, {"observation": UNRELATED_TEST}],
                "tool_call": {
                    "args": {"old": UNRELATED_TEST, "new": REFERENCE},
                },
            }
        )
        self.assertEqual(vset.validate_record(record, pack_dir=PACK), [])
        errors, _execution = vset.validate_record_with_oracle(record, PACK)
        self.assertEqual(errors, [])

    def test_embedded_hidden_source_is_refused(self) -> None:
        digest = hashlib.sha256(HIDDEN.encode("utf-8")).hexdigest()
        cases = {
            "observation": {"steps": [{"observation": "notes\n" + HIDDEN}]},
            "edit": {"tool_call": {"args": {"old": "pass\n", "new": HIDDEN}}},
            "digest": {"decision_basis": f"hidden pin {digest}"},
        }
        for name, extra in cases.items():
            with self.subTest(variant=name):
                record = _record(extra)
                self.assertTrue(vset.validate_record(record, pack_dir=PACK))
                errors, _execution = vset.validate_record_with_oracle(record, PACK)
                self.assertTrue(errors)

    def test_forge_validate_record_refuses_leak(self) -> None:
        for name, extra in FORGES.items():
            with self.subTest(variant=name):
                self.assertTrue(
                    vset.validate_record(_record(extra), pack_dir=PACK),
                    f"{name}: hidden suite leaked with 0 errors",
                )

    def test_forge_oracle_refuses_leak(self) -> None:
        for name, extra in FORGES.items():
            with self.subTest(variant=name):
                errors, _execution = vset.validate_record_with_oracle(_record(extra), PACK)
                self.assertTrue(errors, f"{name}: oracle accepted hidden-suite leak")


if __name__ == "__main__":
    unittest.main()
