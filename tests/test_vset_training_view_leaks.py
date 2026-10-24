#!/usr/bin/env python3
"""Hidden-suite text must not leak into training_view under any key.

Lowercase ``hidden_tests`` is caught; renamed keys, nested containers, and
the pack's own hidden source must be refused. Unrelated ``def test_`` code
is the factory's visible work and must pass.
"""

from __future__ import annotations

import copy
import hashlib
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

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
        # Small te, capital te, and small ie before an ASCII capital.
        for key in ("hidden_\u0442ests", "hidden\u0422ests", "oracl\u0435Suite"):
            with self.subTest(key=key):
                self.assertTrue(vset.validate_record(_record({key: SUITE_PATH})))

    def test_separator_and_width_keys_are_refused(self) -> None:
        for key in ("hidden.tests", "hidden tests", "hidden\uff34ests"):
            with self.subTest(key=key):
                self.assertTrue(vset.validate_record(_record({key: SUITE_PATH})))

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

    def test_generic_assert_line_passes_with_the_pack(self) -> None:
        observation = (
            "def test_parse(self):\n"
            "    with self.assertRaises(ValueError):\n"
            '        parse("x")\n'
            "    self.assertEqual(counter.get(), 5)\n"
        )
        record = _record({"observations": [observation]})
        self.assertEqual(vset.validate_record(record, pack_dir=PACK), [])

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
        class_body = HIDDEN[HIDDEN.index("class ") :]
        cases = {
            "observation": {"steps": [{"observation": "notes\n" + HIDDEN}]},
            "edit": {"tool_call": {"args": {"old": "pass\n", "new": HIDDEN}}},
            "digest": {"decision_basis": f"hidden pin {digest}"},
            "class_body": {"decision_basis": class_body},
            "crlf": {"decision_basis": HIDDEN.replace("\n", "\r\n")},
            "truncated": {"decision_basis": HIDDEN.rstrip()[:-5]},
        }
        for name, extra in cases.items():
            with self.subTest(variant=name):
                record = _record(extra)
                self.assertTrue(vset.validate_record(record, pack_dir=PACK))
                errors, _execution = vset.validate_record_with_oracle(record, PACK)
                self.assertTrue(errors)

    def test_unreadable_hidden_suite_is_reported(self) -> None:
        real_read = Path.read_bytes

        def deny_hidden_suite(self: Path) -> bytes:
            if self.name.startswith("hidden_") and self.suffix == ".py":
                raise OSError("denied")
            return real_read(self)

        with mock.patch.object(Path, "read_bytes", deny_hidden_suite):
            errors = vset.validate_record(_record(), pack_dir=PACK)
        self.assertIn("vset.payload_invalid", [item.code for item in errors])
        self.assertTrue(any("unreadable hidden suite" in item.message for item in errors))

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

    def test_declared_private_suite_name_is_refused(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            pack = Path(tmp) / "pack"
            shutil.copytree(PACK, pack)
            private = pack / "tests" / "private_sub.py"
            (pack / "tests" / "hidden_sub.py").rename(private)
            text = private.read_text(encoding="utf-8")
            declared = _record({"decision_basis": text})
            declared["oracle"]["hidden_tests"] = ["tests/private_sub.py"]
            self.assertTrue(vset.validate_record(declared, pack_dir=pack))
            undeclared = _record({"decision_basis": text})
            undeclared["oracle"]["hidden_tests"] = []
            self.assertEqual(vset.validate_record(undeclared, pack_dir=pack), [])

    def test_hidden_filename_is_refused_when_oracle_lists_nothing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            pack = Path(tmp) / "pack"
            shutil.copytree(PACK, pack)
            text = (pack / "tests" / "hidden_none.py").read_text(encoding="utf-8")
            record = _record({"decision_basis": text})
            record["oracle"]["hidden_tests"] = []
            self.assertTrue(vset.validate_record(record, pack_dir=pack))

    def test_unpaired_surrogate_does_not_stop_the_record(self) -> None:
        record = _record({"decision_basis": "notes \ud800"})
        self.assertEqual(vset.validate_record(record, pack_dir=PACK), [])

    def test_digit_and_acronym_boundaries_are_folded(self) -> None:
        self.assertTrue(vset.validate_record(_record({"HIDDENTests": SUITE_PATH})))
        self.assertEqual(
            vset.validate_record(_record({"hidden2Tests": "visible", "n": 1}), pack_dir=PACK),
            [],
        )

    def test_non_object_training_view_is_refused(self) -> None:
        record = _record()
        record["training_view"] = None
        errors = vset.validate_record(record, pack_dir=PACK)
        self.assertIn("vset.hidden_reasoning_in_training_view", [item.code for item in errors])

    def test_hidden_reasoning_key_is_refused(self) -> None:
        self.assertTrue(vset.validate_record(_record({"reasoning": "scratch"})))

    def test_missing_oracle_object_still_checks_hidden_filenames(self) -> None:
        record = _record({"decision_basis": HIDDEN})
        record["oracle"] = None
        self.assertTrue(vset.validate_record(record, pack_dir=PACK))

    def test_declared_paths_outside_the_pack_are_ignored(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pack = root / "pack"
            shutil.copytree(PACK, pack)
            shutil.rmtree(pack / "tests")
            (pack / "notes.txt").write_text("note", encoding="utf-8")
            (pack / "broken.py").symlink_to(pack / "missing-target")
            (pack / "loop.py").symlink_to("loop.py")
            outside = root / "outside.py"
            outside.write_text(
                "class Secret:\n    def test_hidden(self):\n        pass\n",
                encoding="utf-8",
            )
            (pack / "escape.py").symlink_to(outside)
            record = _record()
            record["oracle"]["hidden_tests"] = [
                "",
                "/etc/passwd",
                "notes.txt",
                "broken.py",
                "loop.py",
                "escape.py",
            ]
            self.assertEqual(vset.validate_record(record, pack_dir=pack), [])

    def test_short_hidden_file_matches_by_digest_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            pack = Path(tmp) / "pack"
            shutil.copytree(PACK, pack)
            short = "x = 1\n"
            (pack / "tests" / "hidden_short.py").write_text(short, encoding="utf-8")
            self.assertEqual(vset.validate_record(_record(), pack_dir=pack), [])
            embedded = _record({"decision_basis": short})
            self.assertTrue(vset.validate_record(embedded, pack_dir=pack))

    def test_undecodable_hidden_suite_is_reported(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            pack = Path(tmp) / "pack"
            shutil.copytree(PACK, pack)
            (pack / "tests" / "hidden_bad.py").write_bytes(b"# coding: ascii\n\xff\n")
            errors = vset.validate_record(_record(), pack_dir=pack)
        self.assertTrue(any("undecodable hidden suite" in item.message for item in errors))

    def test_escaped_hidden_test_path_is_not_read(self) -> None:
        record = _record()
        record["oracle"]["hidden_tests"] = ["../../etc/passwd"]
        errors, execution = vset.validate_record_with_oracle(record, PACK)
        codes = [item.code for item in errors]
        self.assertIsNone(execution)
        self.assertIn("vset.oracle_execution_mismatch", codes)
        self.assertNotIn("vset.hidden_reasoning_in_training_view", codes)


if __name__ == "__main__":
    unittest.main()
