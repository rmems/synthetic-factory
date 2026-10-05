#!/usr/bin/env python3
"""Hash binding and training-view leakage tests (#154)."""

from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path

_TESTS = Path(__file__).resolve().parent
if str(_TESTS) not in sys.path:
    sys.path.insert(0, str(_TESTS))

from vset_testutil import ACCEPT, codes as _codes, load_record as _load, vset  # noqa: E402


class HashBindingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.record = _load(ACCEPT / "issue-patch-validated.json")

    def test_forged_prompt_hash_is_rejected(self) -> None:
        record = copy.deepcopy(self.record)
        record["task_author"]["prompt_hash"] = "sha256:" + ("ab" * 32)
        self.assertIn("vset.release_contract_mismatch", _codes(vset.validate_record(record)))

    def test_forged_result_hash_is_rejected_by_execution(self) -> None:
        from vset_testutil import PACK

        record = copy.deepcopy(self.record)
        record["oracle"]["result_hash"] = "sha256:" + ("cd" * 32)
        errors, _execution = vset.validate_record_with_oracle(record, PACK)
        self.assertIn("vset.oracle_execution_mismatch", _codes(errors))

    def test_missing_snapshot_hash_is_rejected(self) -> None:
        record = copy.deepcopy(self.record)
        del record["environment"]["repo_snapshot_hash"]
        self.assertIn("vset.actor_fields_invalid", _codes(vset.validate_record(record)))

    def test_missing_registry_pin_is_rejected(self) -> None:
        record = copy.deepcopy(self.record)
        record["release"].pop("factory_registry_sha256", None)
        self.assertIn(
            "vset.release_contract_mismatch", _codes(vset.validate_record(record))
        )

    def test_training_view_rejects_hidden_suite_oracle_payload_and_solver(self) -> None:
        leaks = {
            "hidden_tests": ["tests/hidden.py"],
            "hiddenTests": ["tests/hidden.py"],
            "reference_tests": ["tests/reference.py"],
            "oracle": {"status": "validated"},
            "payload": {"patch": {}},
            "patch": {"files": {}},
            "solver": {"run_id": "x"},
            "solverRunId": "x",
        }
        for key, value in leaks.items():
            with self.subTest(key=key):
                record = copy.deepcopy(self.record)
                record["training_view"][key] = value
                self.assertIn(
                    "vset.hidden_reasoning_in_training_view",
                    _codes(vset.validate_record(record)),
                )

    def test_accept_still_requires_validated_on_a_manifest_entry(self) -> None:
        entry = vset.manifest_entry_from_record(self.record)
        entry["oracle"]["status"] = "provisional"
        entry["curation"]["decision"] = "accept"
        manifest = {
            "schema_version": "vset-release-manifest-v1",
            "actor_provenance_schema_version": self.record["actor_provenance_schema_version"],
            "factory_contract_version": vset.registry_pin()["schema_version"],
            "factory_registry_sha256": vset.registry_pin()["sha256"],
            "counts": {
                "records": 1,
                "by_record_kind": {"issue_patch_v1": 1},
                "by_oracle_status": {"provisional": 1, "validated": 0, "invalid": 0},
                "by_curation_decision": {"accept": 1, "exclude": 0, "measure": 0},
                "invalid_or_impossible": 0,
            },
            "entries": [entry],
        }
        manifest["manifest_hash"] = vset.manifest_body_hash(manifest)
        self.assertIn(
            "vset.accept_requires_validated_oracle",
            _codes(vset.validate_manifest(manifest)),
        )


if __name__ == "__main__":
    unittest.main()
