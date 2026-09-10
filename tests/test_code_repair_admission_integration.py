"""Real catalog/evidence integration; requires the shared S2/S3 validators."""
from __future__ import annotations

import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from tests.test_curate_identity import identity as ci
from tests.code_repair_test_support import REPO, envelope, generate, oc
from code_repair import source_policy
from check_records import check_record
from validate_run import check_line
from training_audit import audit_run
from exact_json import ExactJSONFloat, dumps_exact_json


class ProceduralIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.scratch = tempfile.TemporaryDirectory(prefix="admission-real-evidence-")
        cls.root = Path(cls.scratch.name)
        cls.addClassCleanup(cls.scratch.cleanup)
        cls.run_dir = cls.root / "generated"
        generate.run(generate.RunRequest(
            REPO / "catalogs/python-repair-v1", cls.run_dir, 20260908, 12,
            "2026-09-09T00:00:00.000Z",
        ))
        cls.records = [r for _, r in oc.read_jsonl(cls.run_dir / generate.CANDIDATES_FILENAME)]
        cls.row = ci.load_registry().by_path_id["python-function-repair-factory"]

    def test_accepted_record_passes_shape_and_deep_checks(self):
        record = next(r for r in self.records if r["result"]["outcome"] == "accepted")
        errors, kind = check_line(record, "candidate")
        self.assertEqual(kind, "code_repair")
        self.assertEqual(errors, [])
        self.assertEqual(check_record(record, "candidate")[:3], ([], [], "code_repair"))

    def test_exact_json_parsed_evidence_passes_real_shared_validation(self):
        from code_repair.validation import validate_record
        record = next(r for r in self.records if r["result"]["outcome"] == "accepted")
        parsed = json.loads(json.dumps(record), parse_float=ExactJSONFloat)
        self.assertEqual(validate_record(parsed), [])
        self.assertEqual(check_line(parsed, "exact")[0], [])
        self.assertEqual(check_record(parsed, "exact")[0], [])

    def test_restamped_malformed_timeouts_are_refused(self):
        from code_repair.validation import validate_record
        accepted = next(r for r in self.records if r["result"]["outcome"] == "accepted")
        for timeout in (True, "2.0", None, [], 0, -1, 61, 10**400,
                        ExactJSONFloat("60.0000000000000000000001")):
            with self.subTest(timeout=timeout):
                record = copy.deepcopy(accepted)
                record["oracle"]["configuration"]["timeout_s"] = timeout
                record["provenance"]["record_sha256"] = envelope.record_digest(record)
                self.assertTrue(validate_record(record))
                raw = dumps_exact_json(record) + "\n"
                report = audit_run(self.root, snapshot={
                    f"{self.row.path_id}/batch-r01.jsonl": raw.encode(),
                })
                self.assertEqual(report["totals"]["eligible_records"], 0)
                self.assertGreater(report["record_invariants"]["errors"], 0)
        for timeout in (float("inf"), float("nan")):
            with self.subTest(timeout=timeout):
                record = copy.deepcopy(accepted)
                record["oracle"]["configuration"]["timeout_s"] = timeout
                self.assertTrue(validate_record(record))

    def test_bad_family_claim_returns_coded_errors_without_throwing(self):
        record = {"family": "python-function-repair", "result": [], "goal": "x", "steps": []}
        errors, kind = check_line(record, "bad")
        self.assertEqual(kind, "code_repair")
        self.assertTrue(errors)
        self.assertTrue(all("REPAIR" in e or "RECORD" in e or "ENVELOPE" in e for e in errors))

    def test_identity_preserves_source_bytes_and_digest_and_refuses_wrong_path(self):
        record = next(r for r in self.records if r["result"]["outcome"] == "accepted")
        original = copy.deepcopy(record)
        raw = json.dumps(record, ensure_ascii=False, separators=(", ", ": ")) + "  "
        digest = hashlib.sha256(raw.encode()).hexdigest()
        source = ci.SourceRecord(record, f"{self.row.path_id}/batch-r01.jsonl", 1, digest, raw)
        result = ci.curate_record(source)
        self.assertEqual(result.action, "retained", result.mapping)
        self.assertEqual(result.record, original)
        self.assertEqual(record, original)
        wrong = ci.SourceRecord(record, "agentic-coding-trajectory-factory/batch-r01.jsonl", 1)
        self.assertEqual(ci.curate_record(wrong).action, "exclude")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            batch = root / "source" / self.row.path_id / "batch-r01.jsonl"
            batch.parent.mkdir(parents=True)
            batch.write_bytes(raw.encode() + b"\r\n")
            ci.write_run(root / "source", root / "output")
            written = root / "output" / self.row.path_id / batch.name
            self.assertEqual(written.read_bytes(), raw.encode() + b"\n")
            ci.validate_identity_tree(root / "output")
            written.write_text(json.dumps(record) + "\n")
            with self.assertRaises(ci.IdentityTreeError):
                ci.validate_identity_tree(root / "output")

    def test_replayed_manifest_refuses_duplicate_preserved_ids(self):
        record = next(r for r in self.records if r["result"]["outcome"] == "accepted")
        raw = ci.canonical_json(record)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            registry = ci.load_registry()
            (root / ci.FACTORY_REGISTRY_SIDECAR).write_bytes(registry.raw_bytes)
            mappings = []
            for name in ("batch-r01.jsonl", "batch-r02.jsonl"):
                rel = f"{self.row.path_id}/{name}"
                result = ci.curate_record(ci.SourceRecord(record, rel, 1))
                self.assertEqual(result.action, "retained")
                mappings.append(result.mapping)
                path = root / rel
                path.parent.mkdir(exist_ok=True)
                path.write_text(raw + "\n")
            (root / ci.IDENTITY_MANIFEST_SIDECAR).write_text(json.dumps(mappings))
            with self.assertRaises(ci.IdentityTreeError):
                ci.validate_identity_tree(root)

    def test_real_natural_ineligibility_is_evidence_but_corruption_is_an_error(self):
        from code_repair import admission
        natural = next(r for r in self.records if r["result"]["outcome"] != "accepted")
        eligible, reasons = admission.natural_eligibility(natural, self.row)
        self.assertFalse(eligible)
        self.assertTrue(reasons)
        broken = copy.deepcopy(natural)
        broken["provenance"]["record_sha256"] = "0" * 64
        with self.assertRaises(source_policy.SourcePolicyError):
            admission.natural_eligibility(broken, self.row)

    def test_substituted_catalog_and_self_consistent_source_are_refused(self):
        from code_repair import admission
        record = copy.deepcopy(self.records[0])
        forged = admission.load_trusted_catalog(self.row)
        forged.programs[0].upstream["repository"] = "unreviewed/project"
        with self.assertRaises(source_policy.SourcePolicyError):
            admission.natural_eligibility(record, self.row, catalog=forged)
        record["scenario"]["source"]["upstream"]["repository"] = "unreviewed/project"
        record["provenance"]["record_sha256"] = envelope.record_digest(record)
        self.assertEqual(oc.check_digest(record, "restamped"), [])
        with self.assertRaisesRegex(source_policy.SourcePolicyError, "PROCEDURAL_SOURCE_MISMATCH"):
            admission.natural_eligibility(record, self.row)

    def test_audit_counts_only_valid_positive_records_as_eligible(self):
        accepted = next(r for r in self.records if r["result"]["outcome"] == "accepted")
        natural = next(r for r in self.records if r["result"]["outcome"] != "accepted")
        path = f"{self.row.path_id}/batch-r01.jsonl"
        snapshot = {path: (json.dumps(accepted) + "\n" + json.dumps(natural) + "\n").encode()}
        report = audit_run(self.root, snapshot=snapshot)
        self.assertEqual(report["totals"]["eligible_records"], 1)
        self.assertEqual(report["code_repair"]["evidence_only_records"], 1)
        self.assertEqual(report["record_invariants"]["errors"], 0)
        self.assertFalse(report["training_ready"], "pure inspection cannot complete fresh gate")
        broken = copy.deepcopy(natural)
        broken["provenance"]["record_sha256"] = "0" * 64
        report = audit_run(self.root, snapshot={path: (json.dumps(broken) + "\n").encode()})
        self.assertEqual(report["totals"]["eligible_records"], 0)
        self.assertGreater(report["record_invariants"]["errors"], 0)
        wrong = "agentic-coding-trajectory-factory/batch-r01.jsonl"
        report = audit_run(self.root, snapshot={wrong: (json.dumps(accepted) + "\n").encode()})
        self.assertEqual(report["totals"]["eligible_records"], 0)
        self.assertGreater(report["record_invariants"]["errors"], 0)
