#!/usr/bin/env python3
"""VSET actor-provenance contract and oracle fixtures (#154 / #155)."""

from __future__ import annotations

import copy
import io
import json
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PIPELINES = REPO / "pipelines"
FIXTURES = Path(__file__).resolve().parent / "fixtures" / "vset"
PACK = FIXTURES / "repo-pack-counter"
ACCEPT = FIXTURES / "records" / "accept"
REJECT = FIXTURES / "records" / "reject"
MANIFEST = FIXTURES / "manifests" / "pilot-v1.json"
VALIDATE = PIPELINES / "validate_vset.py"

sys.path.insert(0, str(PIPELINES))
import record_kind  # noqa: E402
import validate_vset as vset  # noqa: E402
from curate_coding import contains_hidden_reasoning_key  # noqa: E402


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _codes(errors) -> list[str]:
    return [item.code for item in errors]


def _cli(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(VALIDATE), *args],
        cwd=str(REPO),
        capture_output=True,
        text=True,
    )


class ActorProvenanceContractTests(unittest.TestCase):
    def test_accepted_validated_issue_patch_passes(self):
        errors = vset.validate_record(_load(ACCEPT / "issue-patch-validated.json"))
        self.assertEqual(_codes(errors), [])

    def test_provisional_and_invalid_are_first_class_outcomes(self):
        for name in ("provisional.json", "invalid-impossible.json"):
            with self.subTest(name=name):
                record = _load(ACCEPT / name)
                errors = vset.validate_record(record)
                self.assertEqual(_codes(errors), [])
                self.assertIn(record["oracle"]["status"], {"provisional", "invalid"})
                self.assertEqual(record["curation"]["decision"], "measure")

    def test_review_remediation_requires_explicit_reviewer(self):
        ok = _load(ACCEPT / "review-remediation-validated.json")
        self.assertEqual(_codes(vset.validate_record(ok)), [])
        self.assertIsInstance(ok["reviewer"], dict)
        missing = _load(REJECT / "missing-reviewer-when-required.json")
        codes = _codes(vset.validate_record(missing))
        self.assertIn("vset.reviewer_required", codes)

    def test_issue_patch_reviewer_is_optional(self):
        record = _load(ACCEPT / "issue-patch-validated.json")
        self.assertNotIn("reviewer", record)
        self.assertEqual(_codes(vset.validate_record(record)), [])

    def test_task_author_and_solver_cannot_share_a_run(self):
        record = _load(ACCEPT / "issue-patch-validated.json")
        record["solver"]["run_id"] = record["task_author"]["run_id"]
        self.assertIn("vset.actors_conflated", _codes(vset.validate_record(record)))

    def test_missing_solver_fails_closed(self):
        record = _load(REJECT / "missing-actor-role.json")
        self.assertNotIn("solver", record)
        self.assertIn("vset.missing_actor_role", _codes(vset.validate_record(record)))

    def test_solver_success_does_not_self_certify_validated(self):
        record = _load(REJECT / "self-certify-solver-pass.json")
        self.assertEqual(record["solver"]["outcome"], "success")
        self.assertEqual(record["oracle"]["status"], "validated")
        codes = _codes(vset.validate_record(record))
        self.assertIn("vset.oracle_self_certified", codes)

    def test_source_kind_masquerade_fails_closed(self):
        record = _load(REJECT / "source-kind-masquerade.json")
        self.assertEqual(record["source_kind"], "synthetic")
        codes = _codes(vset.validate_record(record))
        self.assertIn("vset.source_kind_masquerade", codes)

    def test_real_public_engineering_cannot_wear_a_vset_pack(self):
        record = _load(ACCEPT / "provisional.json")
        record["source_kind"] = "real_public_engineering"
        codes = _codes(vset.validate_record(record))
        self.assertIn("vset.source_kind_masquerade", codes)

    def test_accept_requires_synthetic_and_validated_oracle(self):
        record = _load(ACCEPT / "provisional.json")
        record["curation"]["decision"] = "accept"
        codes = _codes(vset.validate_record(record))
        self.assertIn("vset.accept_requires_validated_oracle", codes)

    def test_training_view_rejects_hidden_reasoning(self):
        record = _load(REJECT / "hidden-reasoning-in-training-view.json")
        self.assertTrue(contains_hidden_reasoning_key(record["training_view"]))
        codes = _codes(vset.validate_record(record))
        self.assertIn("vset.hidden_reasoning_in_training_view", codes)

    def test_accepted_training_view_is_clean_while_raw_trace_may_keep_thought(self):
        record = _load(ACCEPT / "issue-patch-validated.json")
        self.assertFalse(contains_hidden_reasoning_key(record["training_view"]))
        self.assertIn("thought", record["trace"])
        self.assertEqual(_codes(vset.validate_record(record)), [])

    def test_new_model_occupies_an_existing_role_without_schema_change(self):
        record = _load(ACCEPT / "issue-patch-validated.json")
        record["solver"]["model"] = "gpt-5.6-sol"
        record["solver"]["version"] = "2026-08-28"
        record["task_author"]["model"] = "muse-spark-1.2"
        self.assertEqual(_codes(vset.validate_record(record)), [])

    def test_registry_version_is_the_reviewed_factory_table(self):
        pin = vset.registry_pin()
        self.assertEqual(pin["schema_version"], "factory-registry-v0.1")
        record = _load(ACCEPT / "issue-patch-validated.json")
        self.assertEqual(
            record["release"]["factory_contract_version"], pin["schema_version"]
        )
        stamped = copy.deepcopy(record)
        stamped["release"]["factory_registry_sha256"] = pin["sha256"]
        self.assertEqual(
            _codes(vset.validate_record(stamped, require_registry_sha=True)), []
        )
        stamped["release"]["factory_registry_sha256"] = "sha256:" + ("ab" * 32)
        self.assertIn(
            "vset.release_contract_mismatch",
            _codes(vset.validate_record(stamped, require_registry_sha=True)),
        )

    def test_vset_payload_is_not_an_identity_kind(self):
        record = _load(ACCEPT / "issue-patch-validated.json")
        self.assertEqual(record_kind.classify_kind(record), "unknown")

    def test_identity_unresolved_provenance_is_not_an_actor_gap(self):
        record = _load(ACCEPT / "provisional.json")
        record["curation"]["reason_codes"] = [vset.IDENTITY_UNRESOLVED_PROVENANCE]
        self.assertIn(
            "vset.identity_reason_collision", _codes(vset.validate_record(record))
        )
        self.assertIn("identity.unresolved_provenance", vset.__doc__)
        self.assertNotIn(
            vset.IDENTITY_UNRESOLVED_PROVENANCE,
            ("vset.missing_actor_role", "vset.reviewer_required"),
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


class ValidateVsetCliTests(unittest.TestCase):
    def test_accept_directory_exits_zero(self):
        result = _cli(str(ACCEPT))
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertTrue(payload["ok"])

    def test_reject_directory_exits_nonzero(self):
        result = _cli(str(REJECT))
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn("ERROR:", result.stderr)

    def test_oracle_cli_validates_the_accepted_issue_patch(self):
        result = _cli(
            "--oracle",
            "--pack",
            str(PACK),
            str(ACCEPT / "issue-patch-validated.json"),
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertTrue(payload["records"][0]["oracle_execution"]["hidden_ok"])

    def test_manifest_cli_exits_zero(self):
        result = _cli("--manifest", str(MANIFEST))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(json.loads(result.stdout)["ok"])


class ReleaseManifestTests(unittest.TestCase):
    def test_pilot_manifest_retains_actor_graph_and_pins(self):
        manifest = _load(MANIFEST)
        self.assertEqual(_codes(vset.validate_manifest(manifest)), [])
        pin = vset.registry_pin()
        self.assertEqual(manifest["factory_contract_version"], pin["schema_version"])
        self.assertEqual(manifest["factory_registry_sha256"], pin["sha256"])
        self.assertEqual(manifest["manifest_hash"], vset.manifest_body_hash(manifest))
        self.assertEqual(manifest["counts"]["invalid_or_impossible"], 1)
        statuses = {entry["oracle"]["status"] for entry in manifest["entries"]}
        self.assertEqual(statuses, {"validated", "invalid"})
        for entry in manifest["entries"]:
            for role in vset.MANIFEST_ROLES:
                self.assertIn(role, entry)
            self.assertIn("source_kind", entry)
            self.assertTrue(entry["environment"]["repo_snapshot_hash"].startswith("sha256:"))
            if entry["oracle"]["status"] == "validated":
                self.assertTrue(entry["oracle"]["result_hash"].startswith("sha256:"))

    def test_dropping_an_impossible_entry_fails_closed(self):
        manifest = _load(MANIFEST)
        kept = [
            entry
            for entry in manifest["entries"]
            if not vset._is_invalid_or_impossible(entry)
        ]
        manifest["entries"] = kept
        manifest["counts"]["records"] = 1
        manifest["counts"]["by_record_kind"] = {"issue_patch_v1": 1}
        manifest["counts"]["by_oracle_status"] = {
            "invalid": 0,
            "provisional": 0,
            "validated": 1,
        }
        manifest["counts"]["by_curation_decision"] = {
            "accept": 1,
            "exclude": 0,
            "measure": 0,
        }
        manifest["counts"]["invalid_or_impossible"] = 0
        # A release that forgets to report the field is the silent-drop case.
        del manifest["counts"]["invalid_or_impossible"]
        manifest["manifest_hash"] = vset.manifest_body_hash(manifest)
        self.assertIn("vset.payload_invalid", _codes(vset.validate_manifest(manifest)))

    def test_missing_manifest_actor_role_is_vset_not_identity(self):
        manifest = _load(MANIFEST)
        del manifest["entries"][0]["solver"]
        codes = _codes(vset.validate_manifest(manifest))
        self.assertIn("vset.missing_actor_role", codes)
        self.assertNotIn(vset.IDENTITY_UNRESOLVED_PROVENANCE, codes)

    def test_identity_reason_on_a_manifest_entry_fails_closed(self):
        manifest = _load(MANIFEST)
        manifest["entries"][0]["curation"]["reason_codes"] = [
            vset.IDENTITY_UNRESOLVED_PROVENANCE
        ]
        self.assertIn(
            "vset.identity_reason_collision", _codes(vset.validate_manifest(manifest))
        )

    def test_wrong_manifest_hash_fails_closed(self):
        manifest = _load(MANIFEST)
        manifest["manifest_hash"] = "sha256:" + ("ab" * 32)
        self.assertIn(
            "vset.release_contract_mismatch", _codes(vset.validate_manifest(manifest))
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


if __name__ == "__main__":
    unittest.main()

