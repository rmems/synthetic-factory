#!/usr/bin/env python3
"""VSET oracle execution and pack-snapshot tests."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

_TESTS = Path(__file__).resolve().parent
if str(_TESTS) not in sys.path:
    sys.path.insert(0, str(_TESTS))

from vset_testutil import (  # noqa: E402
    ACCEPT,
    PACK,
    REJECT,
    codes as _codes,
    load_record as _load,
    vset,
)

class OracleExecutionTests(unittest.TestCase):
    def test_pack_snapshot_matches_accepted_fixtures(self):
        digest = vset.pack_snapshot_hash(PACK)
        for path in sorted(ACCEPT.glob("*.json")):
            record = _load(path)
            self.assertEqual(record["environment"]["repo_snapshot_hash"], digest, path.name)

    def test_pack_snapshot_ignores_bytecode(self):
        before = vset.pack_snapshot_hash(PACK)
        cache = PACK / "tests" / "__pycache__"
        cache.mkdir(exist_ok=True)
        junk = cache / "reference.cpython-314.pyc"
        junk.write_bytes(b"not-a-real-pyc")
        try:
            self.assertEqual(vset.pack_snapshot_hash(PACK), before)
        finally:
            junk.unlink(missing_ok=True)

    def test_pack_snapshot_ignores_factory_metadata(self):
        before = vset.pack_snapshot_hash(PACK)
        pack_meta = PACK / "PACK.json"
        original = pack_meta.read_text()
        try:
            pack_meta.write_text(original.replace("vset-counter-v1", "vset-counter-mutated"))
            self.assertEqual(vset.pack_snapshot_hash(PACK), before)
        finally:
            pack_meta.write_text(original)

    def test_validated_issue_patch_oracle_executes(self):
        record = _load(ACCEPT / "issue-patch-validated.json")
        errors, execution = vset.validate_record_with_oracle(record, PACK)
        self.assertEqual(_codes(errors), [])
        self.assertIsNotNone(execution)
        assert execution is not None
        self.assertTrue(execution["reference"]["ok"])
        self.assertTrue(execution["hidden"]["ok"])

    def test_validated_review_and_recovery_oracles_execute(self):
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

    def test_provisional_runs_reference_without_claiming_validated(self):
        record = _load(ACCEPT / "provisional.json")
        errors, execution = vset.validate_record_with_oracle(record, PACK)
        self.assertEqual(_codes(errors), [])
        self.assertTrue(execution["reference"]["ok"])
        self.assertIsNone(execution["hidden"])
        self.assertEqual(record["oracle"]["status"], "provisional")

    def test_invalid_impossible_is_measured_without_self_certifying(self):
        record = _load(ACCEPT / "invalid-impossible.json")
        errors, execution = vset.validate_record_with_oracle(record, PACK)
        self.assertEqual(_codes(errors), [])
        self.assertIsNone(execution)
        self.assertEqual(record["curation"]["reason_codes"], ["vset.impossible_task"])

    def test_unpatched_hidden_tests_fail_and_cannot_validate(self):
        record = _load(ACCEPT / "issue-patch-validated.json")
        del record["payload"]["patch"]
        errors, execution = vset.validate_record_with_oracle(record, PACK)
        self.assertIn("vset.oracle_execution_mismatch", _codes(errors))
        self.assertFalse(execution["hidden"]["ok"])

    def test_hidden_pass_is_meaningless_when_oracle_is_self_certified(self):
        record = _load(REJECT / "self-certify-solver-pass.json")
        errors, execution = vset.validate_record_with_oracle(record, PACK)
        codes = _codes(errors)
        self.assertIn("vset.oracle_self_certified", codes)
        self.assertTrue(execution["hidden"]["ok"])

    def test_wrong_result_hash_fails_closed(self):
        record = _load(ACCEPT / "issue-patch-validated.json")
        record["oracle"]["result_hash"] = "sha256:" + ("cd" * 32)
        errors, _execution = vset.validate_record_with_oracle(record, PACK)
        self.assertIn("vset.oracle_execution_mismatch", _codes(errors))

