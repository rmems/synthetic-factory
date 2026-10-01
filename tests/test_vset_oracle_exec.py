#!/usr/bin/env python3
"""VSET oracle execution and pack-snapshot tests."""

from __future__ import annotations

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

_TESTS = Path(__file__).resolve().parent
if str(_TESTS) not in sys.path:
    sys.path.insert(0, str(_TESTS))

from vset_testutil import (  # noqa: E402
    ACCEPT,
    MANIFEST,
    PACK,
    REJECT,
    codes as _codes,
    load_record as _load,
    vset,
)

class OracleExecutionTests(unittest.TestCase):
    def test_pack_snapshot_matches_accepted_fixtures(self) -> None:
        digest = vset.pack_snapshot_hash(PACK)
        for path in sorted(ACCEPT.glob("*.json")):
            record = _load(path)
            self.assertEqual(record["environment"]["repo_snapshot_hash"], digest, path.name)

    def test_pack_snapshot_ignores_bytecode(self) -> None:
        before = vset.pack_snapshot_hash(PACK)
        cache = PACK / "tests" / "__pycache__"
        cache.mkdir(exist_ok=True)
        junk = cache / "reference.cpython-314.pyc"
        junk.write_bytes(b"not-a-real-pyc")
        try:
            self.assertEqual(vset.pack_snapshot_hash(PACK), before)
        finally:
            junk.unlink(missing_ok=True)

    def test_pack_snapshot_ignores_factory_metadata(self) -> None:
        before = vset.pack_snapshot_hash(PACK)
        pack_meta = PACK / "PACK.json"
        original = pack_meta.read_text()
        try:
            pack_meta.write_text(original.replace("vset-counter-v1", "vset-counter-mutated"))
            self.assertEqual(vset.pack_snapshot_hash(PACK), before)
        finally:
            pack_meta.write_text(original)

    def test_validated_issue_patch_oracle_executes(self) -> None:
        record = _load(ACCEPT / "issue-patch-validated.json")
        errors, execution = vset.validate_record_with_oracle(record, PACK)
        self.assertEqual(_codes(errors), [])
        self.assertIsNotNone(execution)
        if execution is None:
            self.fail("expected an oracle execution report")
        self.assertTrue(execution["reference"]["ok"])
        self.assertTrue(execution["hidden"]["ok"])

    def test_validated_review_and_recovery_oracles_execute(self) -> None:
        for name in (
            "review-remediation-validated.json",
            "failure-recovery-validated.json",
        ):
            with self.subTest(name=name):
                errors, execution = vset.validate_record_with_oracle(
                    _load(ACCEPT / name), PACK
                )
                self.assertEqual(_codes(errors), [])
                self.assertTrue(execution["reference"]["ok"])
                self.assertTrue(execution["hidden"]["ok"])

    def test_provisional_runs_reference_without_claiming_validated(self) -> None:
        record = _load(ACCEPT / "provisional.json")
        errors, execution = vset.validate_record_with_oracle(record, PACK)
        self.assertEqual(_codes(errors), [])
        self.assertTrue(execution["reference"]["ok"])
        self.assertIsNone(execution["hidden"])
        self.assertEqual(record["oracle"]["status"], "provisional")

    def test_invalid_impossible_is_measured_without_self_certifying(self) -> None:
        record = _load(ACCEPT / "invalid-impossible.json")
        errors, execution = vset.validate_record_with_oracle(record, PACK)
        self.assertEqual(_codes(errors), [])
        self.assertIsNone(execution)
        self.assertEqual(record["curation"]["reason_codes"], ["vset.impossible_task"])

    def test_unpatched_hidden_tests_fail_and_cannot_validate(self) -> None:
        record = _load(ACCEPT / "issue-patch-validated.json")
        del record["payload"]["patch"]
        errors, execution = vset.validate_record_with_oracle(record, PACK)
        self.assertIn("vset.oracle_execution_mismatch", _codes(errors))
        self.assertFalse(execution["hidden"]["ok"])

    def test_hidden_pass_is_meaningless_when_oracle_is_self_certified(self) -> None:
        record = _load(REJECT / "self-certify-solver-pass.json")
        errors, execution = vset.validate_record_with_oracle(record, PACK)
        codes = _codes(errors)
        self.assertIn("vset.oracle_self_certified", codes)
        self.assertTrue(execution["hidden"]["ok"])

    def test_wrong_result_hash_fails_closed(self) -> None:
        record = _load(ACCEPT / "issue-patch-validated.json")
        record["oracle"]["result_hash"] = "sha256:" + ("cd" * 32)
        errors, _execution = vset.validate_record_with_oracle(record, PACK)
        self.assertIn("vset.oracle_execution_mismatch", _codes(errors))

    def test_hidden_suite_checks_state_on_the_negative_delta_case(self) -> None:
        """A `sub` that stores nothing for a negative delta must not pass.

        The hidden FAIL_TO_PASS suite is the only thing between a real fix
        and a plausible-looking one, so every case asserts the counter's
        state afterwards and not only what the call returned. This solver
        mutates correctly for positive deltas -- so it satisfies
        `test_sub_decrements` -- and only skips the store when the delta is
        negative, which is caught solely by the negative-delta state check.
        """

        record = _load(ACCEPT / "issue-patch-validated.json")
        files = record["payload"]["patch"]["files"]
        honest = (
            "    def sub(self, delta):\n"
            "        self._value -= int(delta)\n"
            "        return self._value\n"
        )
        self.assertIn(honest, files["src/counter.py"])
        files["src/counter.py"] = files["src/counter.py"].replace(
            honest,
            "    def sub(self, delta):\n"
            "        if int(delta) < 0:\n"
            "            return self._value - int(delta)\n"
            "        self._value -= int(delta)\n"
            "        return self._value\n",
        )
        _errors, execution = vset.validate_record_with_oracle(record, PACK)
        self.assertTrue(execution["reference"]["ok"])
        self.assertFalse(execution["hidden"]["ok"])


class OracleEdgeCaseTests(unittest.TestCase):
    def test_explicit_empty_reference_tests_fails_closed(self) -> None:
        record = _load(ACCEPT / "issue-patch-validated.json")
        record["oracle"]["reference_tests"] = []
        errors, _execution = vset.validate_record_with_oracle(record, PACK)
        self.assertIn("vset.oracle_execution_mismatch", _codes(errors))

    def test_non_list_reference_tests_fails_closed(self) -> None:
        record = _load(ACCEPT / "issue-patch-validated.json")
        record["oracle"]["reference_tests"] = "tests/reference.py"
        errors, _execution = vset.validate_record_with_oracle(record, PACK)
        self.assertIn("vset.oracle_execution_mismatch", _codes(errors))

    def test_undeclared_task_id_fails_pack_binding(self) -> None:
        record = _load(ACCEPT / "issue-patch-validated.json")
        record["environment"]["task_id"] = "vset-counter-v1.undeclared"
        errors, _execution = vset.validate_record_with_oracle(record, PACK)
        self.assertIn("vset.oracle_pack_binding", _codes(errors))

    def test_unreadable_pack_manifest_fails_closed(self) -> None:
        record = _load(ACCEPT / "issue-patch-validated.json")
        with tempfile.TemporaryDirectory() as tmp:
            pack = Path(tmp) / "pack"
            shutil.copytree(PACK, pack)
            (pack / "PACK.json").write_text("{not json", encoding="utf-8")
            errors, _execution = vset.validate_record_with_oracle(record, pack)
            self.assertIn("vset.oracle_pack_binding", _codes(errors))

    def test_malformed_task_manifest_is_skipped_then_binding_fails(self) -> None:
        record = _load(ACCEPT / "issue-patch-validated.json")
        record["environment"]["task_id"] = "vset-counter-v1.undeclared"
        with tempfile.TemporaryDirectory() as tmp:
            pack = Path(tmp) / "pack"
            shutil.copytree(PACK, pack)
            (pack / "tasks" / "junk.json").write_text("[", encoding="utf-8")
            errors, _execution = vset.validate_record_with_oracle(record, pack)
            self.assertIn("vset.oracle_pack_binding", _codes(errors))

    def test_patch_rejects_illegal_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            for bad in ("", "   ", "..", "../escape.py", "/abs.py", 7):
                patch = {"files": {bad: "x = 1\n"}}
                with self.assertRaises(vset.VSetValidationError) as ctx:
                    vset.apply_patch(work, patch)
                self.assertEqual(ctx.exception.code, "vset.payload_invalid")

    def test_patch_rejects_directory_target_and_protected_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            (work / "tests").mkdir()
            with self.assertRaises(vset.VSetValidationError) as ctx:
                vset.apply_patch(work, {"files": {"tests": "x = 1\n"}})
            self.assertEqual(ctx.exception.code, "vset.payload_invalid")
            with self.assertRaises(vset.VSetValidationError) as ctx2:
                vset.apply_patch(
                    work,
                    {"files": {"tests/reference.py": "x = 1\n"}},
                    protected=["tests/reference.py"],
                )
            self.assertEqual(ctx2.exception.code, "vset.payload_invalid")

    def test_manifest_entry_with_non_object_reviewer_fails_closed(self) -> None:
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        manifest["entries"][0]["reviewer"] = 42
        manifest["manifest_hash"] = vset.manifest_body_hash(manifest)
        self.assertNotEqual(_codes(vset.validate_manifest(manifest)), [])
