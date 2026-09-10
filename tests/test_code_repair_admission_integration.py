"""Real catalog/evidence integration; requires the shared S2/S3 validators."""
from __future__ import annotations

import copy
import hashlib
import json
import tempfile
import unittest
from itertools import product
from pathlib import Path
from unittest.mock import patch

from tests.code_repair_admission_test_support import build_generated_admission_evidence, restamp
from tests.test_curate_identity import identity as ci
from tests.code_repair_test_support import (
    PINNED_AT, REPO, SEED, envelope, generate, oc, records, verify, vocabulary,
)
from code_repair import admission, catalog, source_policy, validation
from check_records import check_record
from validate_run import check_line
from training_audit import audit_run
from exact_json import ExactJSONFloat, dumps_exact_json


class ProceduralIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root, cls.run_dir, cls.records, cls.row = build_generated_admission_evidence(cls)

    def test_shared_checks_refuse_restamped_upstream_substitutions(self):
        changes = (("repository", "unreviewed/project"), ("commit", "0" * 40),
                   ("path", "forged.py"), ("license", "Proprietary"))
        for outcome, (field, value) in product(("accepted", "rejected"), changes):
            with self.subTest(outcome=outcome, field=field):
                record = copy.deepcopy(next(r for r in self.records
                                            if r["result"]["outcome"] == outcome))
                record["scenario"]["source"]["upstream"][field] = value
                restamp(record)
                self.assertEqual(validation.validate_record(record), [])
                self.assertEqual(check_line(record, "restamped")[0],
                                 ["EXPORT_CATALOG_MISMATCH"])
                self.assertEqual(check_record(record, "restamped")[0],
                                 ["EXPORT_CATALOG_MISMATCH"])

    def test_shared_checks_report_unreadable_sealed_catalog(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(
            source_policy, "ROOT", Path(directory)
        ):
            for checker in (check_line, check_record):
                findings = checker(self.records[0], "unreadable")[0]
                self.assertTrue(findings)
                self.assertIn("PROCEDURAL_CATALOG_UNREADABLE", findings[0])

    def test_generator_extensions_cannot_survive_identity_admission(self):
        changes = (("model", "example-model"), ("provider", "example-provider"),
                   ("source_kind", "model_generated"))
        for outcome, (field, value) in product(("accepted", "rejected"), changes):
            with self.subTest(outcome=outcome, field=field):
                record = copy.deepcopy(next(r for r in self.records
                                            if r["result"]["outcome"] == outcome))
                record["generator"][field] = value
                restamp(record)
                self.assertEqual(oc.check_digest(record, "restamped"), [])
                self.assertTrue(admission.validate_source_route(record, self.row))
                with self.assertRaisesRegex(source_policy.SourcePolicyError,
                                            "PROCEDURAL_GENERATOR_MISMATCH"):
                    admission.natural_eligibility(record, self.row)
                result = ci.curate_record(ci.SourceRecord(
                    record, f"{self.row.path_id}/batch-r01.jsonl", 1))
                self.assertEqual(result.action, "exclude")

    def assert_shared_refusal(self, record):
        self.assertEqual(oc.check_digest(record, "restamped"), [])
        self.assertTrue(validation.validate_record(record))
        self.assertTrue(check_record(record, "restamped")[0])
        with self.assertRaises(source_policy.SourcePolicyError):
            admission.natural_eligibility(record, self.row)
        result = ci.curate_record(ci.SourceRecord(record, f"{self.row.path_id}/batch-r01.jsonl", 1))
        self.assertEqual(result.action, "exclude")
        run = json.loads((self.run_dir / "RUN.json").read_bytes())
        candidates = [record if r["id"] == record["id"] else r for r in self.records]
        digest = hashlib.sha256("".join(oc.canonical_json(r) + "\n" for r in candidates).encode()).hexdigest()
        run["candidates_sha256"] = digest
        self.assertTrue(validation.validate_run(run, candidates,
            catalog=catalog.load_catalog(REPO / "catalogs/python-repair-v1"), candidates_sha256=digest))

    def test_nested_real_claims_refuse_all_shared_boundaries(self):
        for outcome in ("accepted", "rejected"):
            original = next(r for r in self.records if r["result"]["outcome"] == outcome)
            for claim in ({"sim_or_real": "real"}, {"provenance": {"kind": "real"}}):
                with self.subTest(outcome=outcome, claim=claim):
                    record = copy.deepcopy(original)
                    record["provenance"]["extra"] = [claim]
                    restamp(record)
                    self.assert_shared_refusal(record)

    def test_fixed_oracle_identity_refuses_all_shared_boundaries(self):
        for outcome in ("accepted", "rejected"):
            original = next(r for r in self.records if r["result"]["outcome"] == outcome)
            for field, value in (("name", "forged-oracle"), ("type", "recorded_measurement"),
                                 ("implementation", "forged.py:main"), ("version", "99.0"),
                                 ("commit", "forged-commit")):
                with self.subTest(outcome=outcome, field=field):
                    record = copy.deepcopy(original)
                    record["oracle"][field] = value
                    restamp(record)
                    self.assert_shared_refusal(record)
            record = copy.deepcopy(original)
            record["oracle"]["configuration"]["isolation"] = "arbitrary-isolation"
            restamp(record)
            self.assert_shared_refusal(record)

    def test_reference_only_oracle_remains_refused_before_admission(self):
        record = copy.deepcopy(next(r for r in self.records if admission.natural_eligibility(r, self.row)[0]))
        self.assertEqual(oc.curation_eligible(record, []), (True, []))
        record["oracle"]["authority"] = "reference_only"
        restamp(record)
        self.assertFalse(oc.curation_eligible(record, [])[0])
        with self.assertRaises(source_policy.SourcePolicyError):
            admission.natural_eligibility(record, self.row)

    def test_emitter_owned_provenance_cannot_be_substituted(self):
        for outcome, field in product(("accepted", "rejected"), ("producer", "source_kind", "oracle_run")):
            with self.subTest(outcome=outcome, field=field):
                record = copy.deepcopy(next(r for r in self.records if r["result"]["outcome"] == outcome))
                record["provenance"][field] = "forged-provenance"
                restamp(record)
                self.assert_shared_refusal(json.loads(dumps_exact_json(record)))

    def test_emitter_owned_actor_identities_cannot_be_substituted(self):
        combinations = product(("accepted", "rejected"),
            ("task_author", "solver", "oracle_certifier"), ("name", "kind", "role", "version"))
        for outcome, role, field in combinations:
            with self.subTest(outcome=outcome, actor=role, field=field):
                record = copy.deepcopy(next(r for r in self.records if r["result"]["outcome"] == outcome))
                record["provenance"]["actors"][role][field] = "forged-actor"
                restamp(record)
                self.assert_shared_refusal(json.loads(dumps_exact_json(record)))

    def test_fabricated_abstention_cannot_relabel_measured_phase_evidence(self):
        for outcome in ("accepted", "rejected"):
            with self.subTest(outcome=outcome):
                record = copy.deepcopy(next(r for r in self.records if r["result"]["outcome"] == outcome))
                record["result"].update(status="abstained", abstention_reason="fabricated abstention")
                restamp(record)
                self.assertFalse(oc.curation_eligible(record, [])[0])
                with self.assertRaises(source_policy.SourcePolicyError):
                    admission.natural_eligibility(record, self.row)
                self.assert_shared_refusal(record)

    def test_real_abstention_remains_valid_evidence_only_at_admission(self):
        with tempfile.TemporaryDirectory() as scratch:
            output = Path(scratch) / "run"
            generate.run(generate.RunRequest(REPO / "catalogs/python-repair-v1", output,
                SEED, 1, PINNED_AT, timeout_s=0.001))
            record = oc.read_jsonl(output / "candidates.jsonl")[0][1]
            self.assertEqual(record["result"]["status"], "abstained")
            self.assertFalse(oc.curation_eligible(record, [])[0])
            self.assertEqual(validation.validate_record(record), [])
            eligible, reasons = admission.natural_eligibility(record, self.row)
            self.assertFalse(eligible)
            self.assertEqual(reasons, tuple(record["result"]["reason_codes"]))
            curated = ci.curate_record(ci.SourceRecord(record, f"{self.row.path_id}/batch-r01.jsonl", 1))
            self.assertEqual(curated.action, "retained")
            self.assertFalse(curated.mapping["procedural_authority"]["eligible_training_candidate"])

    def test_failed_phases_cannot_retain_fabricated_suite_rows(self):
        original = next(
            r for r in self.records
            if r["result"]["reason_codes"] == ["MUTANT_NO_OBSERVED_FAILURE"]
        )
        for status, reason in (
            ("timeout", "MUTANT_TIMEOUT"),
            ("harness_error", "MUTANT_HARNESS_ERROR"),
        ):
            with self.subTest(status=status):
                record = copy.deepcopy(original)
                phase = record["result"]["phases"]["mutant"]
                self.assertTrue(phase["public"] and phase["hidden"])
                phase.update(status=status, load_ok=False, limits_applied=None)
                phases = verify.phases_from_blocks(record["result"]["phases"])
                record["result"].update(
                    reason_codes=[reason],
                    measurements=records.measurements(phases),
                    evidence_sha256=verify.result_hash(record["result"]["phases"]),
                )
                restamp(record)
                self.assertEqual(oc.check_digest(record, "restamped"), [])
                self.assertEqual(
                    validation.validate_record(record, catalog=catalog.load_catalog(
                        REPO / "catalogs/python-repair-v1"
                    )),
                    [vocabulary.EXPORT_EVIDENCE_VERDICT_MISMATCH],
                )

    def test_identity_refuses_recursive_training_ready_true_claims(self):
        original = next(r for r in self.records if r["result"]["outcome"] == "accepted")
        for nested in (False, True):
            with self.subTest(nested=nested):
                record = copy.deepcopy(original)
                if nested:
                    record["provenance"]["extra"] = [{"training_ready": True}]
                else:
                    record["training_ready"] = True
                restamp(record)
                before = copy.deepcopy(record)
                result = ci.curate_record(ci.SourceRecord(
                    record, f"{self.row.path_id}/batch-r01.jsonl", 1,
                ))
                self.assertEqual(result.action, "exclude")
                self.assertEqual(
                    result.mapping["reason_codes"],
                    ["identity.training_ready_policy_violation"],
                )
                self.assertEqual(record, before)

    def test_identity_preserves_false_training_ready_claims_without_mutation(self):
        original = next(r for r in self.records if r["result"]["outcome"] == "accepted")
        record = copy.deepcopy(original)
        record["training_ready"] = False
        record["provenance"]["extra"] = [{"training_ready": False}]
        restamp(record)
        before = copy.deepcopy(record)
        result = ci.curate_record(ci.SourceRecord(
            record, f"{self.row.path_id}/batch-r01.jsonl", 1,
        ))
        self.assertEqual(result.action, "retained", result.mapping)
        self.assertEqual(result.record, before)
        self.assertEqual(record, before)

    def test_derivable_record_identity_is_required_before_admission(self):
        for outcome in ("accepted", "rejected"):
            original = next(r for r in self.records if r["result"]["outcome"] == outcome)
            for field in ("id", "generator_seed", "oracle_seed", "harness", "limits"):
                with self.subTest(outcome=outcome, field=field):
                    record = copy.deepcopy(original)
                    targets = {"id": (record, "id", "forged"),
                        "generator_seed": (record["generator"], "seed", 42),
                        "oracle_seed": (record["oracle"], "seed", 42),
                        "harness": (record["oracle"]["fingerprint"], "harness_sha256", "0" * 64),
                        "limits": (record["oracle"]["configuration"]["limits"], "cpu_s", 99)}
                    owner, key, value = targets[field]
                    owner[key] = value
                    restamp(record)
                    self.assertEqual(oc.check_digest(record, "restamped"), [])
                    with self.assertRaises(source_policy.SourcePolicyError):
                        admission.natural_eligibility(record, self.row)

    def timeout_source(self, token):
        record = copy.deepcopy(next(r for r in self.records if r["result"]["outcome"] == "accepted"))
        record["oracle"]["configuration"]["timeout_s"] = ExactJSONFloat(token)
        record["oracle"]["configuration"]["limits"]["cpu_s"] = int(float(token)) + 2
        restamp(record)
        return dumps_exact_json(record) + "  "

    def write_source(self, root, raw):
        batch = root / "source" / self.row.path_id / "batch-r01.jsonl"
        batch.parent.mkdir(parents=True)
        batch.write_bytes(raw.encode() + b"\r\n")
        ci.write_run(root / "source", root / "output")
        return root / "output" / self.row.path_id / batch.name

    def test_exact_decimal_source_is_refused_before_identity_admission(self):
        raw = self.timeout_source("60.0").replace('"timeout_s":60.0', '"timeout_s":60.0000000000000000000001')
        with tempfile.TemporaryDirectory() as scratch:
            output = self.write_source(Path(scratch), raw)
            self.assertFalse(output.exists())
            ci.validate_identity_tree(Path(scratch) / "output")
        with self.assertRaises(ci.IdentityCurationError):
            ci.curate_record(ci.SourceRecord(json.loads(raw), f"{self.row.path_id}/batch-r01.jsonl", 1,
                                            source_json=raw))

    def test_valid_exact_decimal_source_and_whitespace_survive_identity(self):
        for token in ("2.0", "2.0000000000000000000001", "2e0"):
            with self.subTest(token=token), tempfile.TemporaryDirectory() as scratch:
                raw = self.timeout_source(token)
                output = self.write_source(Path(scratch), raw)
                self.assertEqual(output.read_bytes(), raw.encode() + b"\n")
                ci.validate_identity_tree(Path(scratch) / "output")

    def test_identity_tree_replay_rejects_coherently_rehashed_decimal_snapshot(self):
        with tempfile.TemporaryDirectory() as scratch:
            root = Path(scratch)
            raw = self.timeout_source("60.0")
            output = self.write_source(root, raw)
            ci.validate_identity_tree(root / "output")
            forged = raw.replace('"timeout_s":60.0', '"timeout_s":60.0000000000000000000001')
            output.write_bytes(forged.encode() + b"\n")
            manifest_path = root / "output" / ci.IDENTITY_MANIFEST_SIDECAR
            manifest = json.loads(manifest_path.read_bytes())
            manifest[0]["source"].update(original=forged, sha256=hashlib.sha256(forged.encode()).hexdigest())
            manifest_path.write_text(ci.canonical_json(manifest) + "\n")
            with self.assertRaises(ci.IdentityTreeError):
                ci.validate_identity_tree(root / "output")

    def test_identity_tree_replay_refuses_nested_real_claim_snapshot(self):
        with tempfile.TemporaryDirectory() as scratch:
            root = Path(scratch)
            output = self.write_source(root, self.timeout_source("2.0"))
            record = json.loads(output.read_bytes())
            record["provenance"]["extra"] = [{"sim_or_real": "real", "provenance": {"kind": "real"}}]
            restamp(record)
            raw = dumps_exact_json(record)
            output.write_bytes(raw.encode() + b"\n")
            manifest_path = root / "output" / ci.IDENTITY_MANIFEST_SIDECAR
            manifest = json.loads(manifest_path.read_bytes())
            manifest[0]["source"].update(original=raw, sha256=hashlib.sha256(raw.encode()).hexdigest())
            manifest[0]["output_sha256"] = ci.sha256_json(record)
            manifest_path.write_text(ci.canonical_json(manifest) + "\n")
            with self.assertRaises(ci.IdentityTreeError):
                ci.validate_identity_tree(root / "output")

    def test_accepted_record_passes_shape_and_deep_checks(self):
        record = next(r for r in self.records if r["result"]["outcome"] == "accepted")
        self.assertIsNone(record["oracle"]["commit"])
        self.assertEqual(record["oracle"]["configuration"]["isolation"],
            "rlimits and a fresh working directory only: no filesystem or network isolation "
            "(issue #198); programs come from a pinned catalog whose selector admits stdlib-only modules")
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
        self.assertEqual(report["identity"]["duplicates"], [])
        self.assertEqual(report["exact_duplicates"], [])
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

    def test_audit_accounts_duplicate_rejected_records_as_evidence_only(self):
        natural = next(r for r in self.records if r["result"]["outcome"] != "accepted")
        path = f"{self.row.path_id}/batch-r01.jsonl"
        line = dumps_exact_json(natural) + "\n"
        report = audit_run(self.root, snapshot={path: (line + line).encode()})
        first, again = f"{path}:1", f"{path}:2"
        self.assertEqual(report["totals"]["eligible_records"], 0)
        self.assertEqual(report["code_repair"]["eligible_records"], 0)
        self.assertEqual(report["code_repair"]["evidence_only_records"], 2)
        self.assertEqual(
            report["identity"]["duplicates"],
            [{"id": natural["id"], "first": first, "again": again}],
        )
        self.assertEqual(report["exact_duplicates"], [{"first": first, "again": again}])
