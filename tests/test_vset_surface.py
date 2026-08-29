#!/usr/bin/env python3
"""Coverage of already-shipped VSET error and in-process CLI branches."""

from __future__ import annotations

import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
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

class ExistingSurfaceCoverageTests(unittest.TestCase):
    """Exercise already-shipped error and CLI branches. No new contract."""

    def _record(self, name: str = "issue-patch-validated.json") -> dict:
        return _load(ACCEPT / name)

    def _main(self, *args: str) -> tuple[int, str, str]:
        stdout = io.StringIO()
        stderr = io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            code = vset.main(list(args))
        return code, stdout.getvalue(), stderr.getvalue()

    def test_non_object_record_and_manifest_fail_closed(self):
        self.assertIn("vset.record_not_object", _codes(vset.validate_record([])))
        self.assertIn("vset.record_not_object", _codes(vset.validate_manifest("nope")))
        errors, execution = vset.validate_record_with_oracle("nope", PACK)
        self.assertIn("vset.record_not_object", _codes(errors))
        self.assertIsNone(execution)

    def test_schema_and_kind_header_errors(self):
        record = self._record()
        record["schema_version"] = "vset-record-v0"
        record["actor_provenance_schema_version"] = "actor-provenance-v0"
        record["record_kind"] = "not_a_kind"
        codes = _codes(vset.validate_record(record))
        self.assertIn("vset.schema_version_invalid", codes)
        self.assertIn("vset.record_kind_invalid", codes)

    def test_source_kind_and_payload_shape_errors(self):
        record = self._record()
        record["source_kind"] = "lab_notes"
        self.assertIn("vset.source_kind_invalid", _codes(vset.validate_record(record)))
        record = self._record()
        record["payload"] = {}
        self.assertIn("vset.payload_invalid", _codes(vset.validate_record(record)))
        record = self._record()
        del record["payload"]["patch"]
        self.assertIn("vset.payload_invalid", _codes(vset.validate_record(record)))

    def test_actor_field_and_optional_reviewer_errors(self):
        record = self._record()
        record["task_author"]["model"] = "   "
        record["solver"]["tool_policy"] = ""
        record["task_author"]["prompt_hash"] = "not-a-hash"
        codes = _codes(vset.validate_record(record))
        self.assertIn("vset.actor_fields_invalid", codes)
        record = self._record()
        record["reviewer"] = "not-an-object"
        self.assertIn("vset.actor_fields_invalid", _codes(vset.validate_record(record)))
        record = self._record()
        record["reviewer"] = {"model": "r", "version": "v", "run_id": ""}
        self.assertIn("vset.actor_fields_invalid", _codes(vset.validate_record(record)))
        record = self._record()
        record["reviewer"] = {"model": "r", "version": "v", "run_id": "review-run"}
        self.assertEqual(_codes(vset.validate_record(record)), [])

    def test_oracle_and_curation_and_release_shape_errors(self):
        record = self._record()
        record["oracle"]["status"] = "certified"
        self.assertIn("vset.oracle_status_invalid", _codes(vset.validate_record(record)))
        record = self._record()
        record["oracle"]["kind"] = ""
        self.assertIn("vset.oracle_status_invalid", _codes(vset.validate_record(record)))
        record = self._record()
        record["oracle"]["command"] = ""
        record["oracle"]["result_hash"] = "nope"
        record["oracle"]["certifier"] = ""
        codes = _codes(vset.validate_record(record))
        self.assertIn("vset.oracle_validated_without_evidence", codes)
        self.assertIn("vset.oracle_self_certified", codes)
        record = self._record()
        record["curation"]["pipeline_version"] = ""
        record["curation"]["decision"] = "maybe"
        record["curation"]["reason_codes"] = ["Not-A-Token"]
        self.assertIn("vset.actor_fields_invalid", _codes(vset.validate_record(record)))
        record = self._record()
        record["source_kind"] = "real_public_engineering"
        record["environment"]["repo_pack_id"] = "upstream-public-1"
        self.assertIn(
            "vset.accept_requires_synthetic", _codes(vset.validate_record(record))
        )
        record = self._record()
        record["environment"]["repo_snapshot_hash"] = "sha256:nope"
        record["environment"]["task_id"] = ""
        record["release"]["factory_contract_version"] = "not-the-registry"
        record["release"]["manifest_hash"] = "sha256:zz"
        self.assertIn("vset.actor_fields_invalid", _codes(vset.validate_record(record)))
        self.assertIn(
            "vset.release_contract_mismatch", _codes(vset.validate_record(record))
        )
        record = self._record()
        del record["training_view"]
        self.assertIn(
            "vset.hidden_reasoning_in_training_view",
            _codes(vset.validate_record(record)),
        )

    def test_apply_patch_and_run_oracle_existing_guards(self):
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            with self.assertRaises(vset.VSetValidationError) as ctx:
                vset.apply_patch(work, "not-an-object")
            self.assertEqual(ctx.exception.code, "vset.payload_invalid")
            with self.assertRaises(vset.VSetValidationError):
                vset.apply_patch(work, {"files": {}})
            with self.assertRaises(vset.VSetValidationError):
                vset.apply_patch(work, {"files": {"/abs.py": "x"}})
            with self.assertRaises(vset.VSetValidationError):
                vset.apply_patch(work, {"files": {"src/ok.py": 1}})
        with self.assertRaises(vset.VSetValidationError) as ctx:
            vset.run_oracle(ACCEPT / "issue-patch-validated.json")
        self.assertEqual(ctx.exception.code, "vset.oracle_execution_mismatch")

    def test_oracle_execution_path_list_and_snapshot_errors(self):
        record = self._record("provisional.json")
        record["oracle"]["reference_tests"] = "tests/reference.py"
        errors, execution = vset.validate_record_with_oracle(record, PACK)
        self.assertIn("vset.oracle_execution_mismatch", _codes(errors))
        self.assertIsNone(execution)
        record = self._record("provisional.json")
        record["oracle"]["hidden_tests"] = [1]
        errors, execution = vset.validate_record_with_oracle(record, PACK)
        self.assertIn("vset.oracle_execution_mismatch", _codes(errors))
        self.assertIsNone(execution)
        record = self._record("provisional.json")
        record["oracle"]["reference_tests"] = ["tests/missing_module.py"]
        errors, execution = vset.validate_record_with_oracle(record, PACK)
        self.assertIn("vset.oracle_execution_mismatch", _codes(errors))
        self.assertIsNone(execution)
        record = self._record()
        record["environment"]["repo_snapshot_hash"] = "sha256:" + ("ab" * 32)
        errors, _execution = vset.validate_record_with_oracle(record, PACK)
        self.assertIn("vset.oracle_execution_mismatch", _codes(errors))

    def test_manifest_entry_projection_and_existing_count_errors(self):
        record = self._record()
        entry = vset.manifest_entry_from_record(record)
        self.assertEqual(entry["record_kind"], "issue_patch_v1")
        self.assertEqual(entry["oracle"]["status"], "validated")
        self.assertEqual(entry["task_author"]["run_id"], record["task_author"]["run_id"])
        manifest = _load(MANIFEST)
        manifest["schema_version"] = "wrong"
        manifest["actor_provenance_schema_version"] = "wrong"
        manifest["factory_contract_version"] = "wrong"
        manifest["factory_registry_sha256"] = "sha256:" + ("cd" * 32)
        codes = _codes(vset.validate_manifest(manifest))
        self.assertIn("vset.schema_version_invalid", codes)
        self.assertIn("vset.release_contract_mismatch", codes)
        manifest = _load(MANIFEST)
        manifest["entries"] = []
        self.assertIn("vset.payload_invalid", _codes(vset.validate_manifest(manifest)))
        manifest = _load(MANIFEST)
        manifest["entries"][0] = "not-an-entry"
        self.assertIn("vset.record_not_object", _codes(vset.validate_manifest(manifest)))
        manifest = _load(MANIFEST)
        manifest["entries"][0]["record_kind"] = "not_a_kind"
        manifest["entries"][0]["source_kind"] = "lab_notes"
        codes = _codes(vset.validate_manifest(manifest))
        self.assertIn("vset.record_kind_invalid", codes)
        self.assertIn("vset.source_kind_invalid", codes)
        manifest = _load(MANIFEST)
        manifest["counts"]["by_record_kind"] = {"issue_patch_v1": 99}
        manifest["counts"]["by_oracle_status"]["validated"] = 99
        manifest["counts"]["by_curation_decision"]["accept"] = 99
        manifest["counts"]["invalid_or_impossible"] = 99
        manifest["counts"]["records"] = 99
        self.assertIn("vset.payload_invalid", _codes(vset.validate_manifest(manifest)))
        manifest = _load(MANIFEST)
        del manifest["counts"]
        self.assertIn("vset.payload_invalid", _codes(vset.validate_manifest(manifest)))

    def test_manifest_entry_evidence_errors(self):
        manifest = _load(MANIFEST)
        manifest["entries"][0]["environment"]["repo_snapshot_hash"] = "sha256:nope"
        manifest["entries"][0]["oracle"]["result_hash"] = "sha256:nope"
        manifest["entries"][1]["curation"]["decision"] = "accept"
        manifest["entries"][0]["release"]["factory_contract_version"] = "other"
        codes = _codes(vset.validate_manifest(manifest))
        self.assertIn("vset.actor_fields_invalid", codes)
        self.assertIn("vset.accept_requires_validated_oracle", codes)
        self.assertIn("vset.release_contract_mismatch", codes)
        manifest = _load(MANIFEST)
        manifest["entries"][0]["solver"]["run_id"] = manifest["entries"][0]["task_author"][
            "run_id"
        ]
        self.assertIn("vset.actors_conflated", _codes(vset.validate_manifest(manifest)))
        manifest = _load(MANIFEST)
        manifest["entries"][0]["record_kind"] = "review_remediation_v1"
        manifest["entries"][0]["reviewer"] = None
        self.assertIn("vset.reviewer_required", _codes(vset.validate_manifest(manifest)))

    def test_helpers_and_in_process_cli(self):
        path = ACCEPT / "issue-patch-validated.json"
        self.assertEqual(vset.iter_record_paths(path), [path])
        self.assertIn(path, vset.iter_record_paths(ACCEPT))
        loaded = vset.load_json(path)
        self.assertEqual(loaded["record_kind"], "issue_patch_v1")
        summary = vset.summarize([])
        self.assertTrue(summary["ok"])
        self.assertEqual(summary["error_count"], 0)
        code, stdout, _stderr = self._main(str(path))
        self.assertEqual(code, 0)
        self.assertTrue(json.loads(stdout)["ok"])
        code, _stdout, stderr = self._main("/no/such/vset-record.json")
        self.assertEqual(code, 2)
        self.assertIn("not found", stderr)
        code, _stdout, stderr = self._main("--oracle", str(path))
        self.assertEqual(code, 2)
        self.assertIn("--oracle requires --pack", stderr)
        code, stdout, _stderr = self._main("--manifest", str(MANIFEST))
        self.assertEqual(code, 0)
        self.assertTrue(json.loads(stdout)["ok"])
        code, _stdout, stderr = self._main(str(REJECT / "missing-actor-role.json"))
        self.assertEqual(code, 1)
        self.assertIn("ERROR:", stderr)
        code, stdout, _stderr = self._main(
            "--oracle",
            "--pack",
            str(PACK),
            str(path),
        )
        self.assertEqual(code, 0)
        self.assertTrue(json.loads(stdout)["records"][0]["oracle_execution"]["hidden_ok"])
        args = vset.parse_args(["--require-registry-sha", str(path)])
        self.assertTrue(args.require_registry_sha)
        self.assertEqual(args.target, str(path))

