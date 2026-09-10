"""Real catalog/evidence integration; requires the shared S2/S3 validators."""
from __future__ import annotations

import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from tests.test_curate_identity import identity as ci
from tests.code_repair_test_support import (
    FIXTURE_CATALOG, PINNED_AT, REPO, SEED, envelope, fixture, generate, oc, records, smoke_run,
)
from code_repair import catalog, planning, source_policy, validation
from check_records import check_record
from validate_run import check_line
from training_audit import audit_run
from exact_json import ExactJSONFloat, dumps_exact_json


def restamp(record):
    record["provenance"]["record_sha256"] = envelope.record_digest(record)


def capture(run, candidates):
    payload = "".join(oc.canonical_json(record) + "\n" for record in candidates).encode()
    run["candidates_sha256"] = hashlib.sha256(payload).hexdigest()
    return validation.validate_run(
        run, candidates, catalog=fixture(), candidates_sha256=run["candidates_sha256"],
    )


class TrustedBindings(unittest.TestCase):
    def evidence(self):
        return copy.deepcopy(smoke_run()[:2])

    def test_fixed_task_metadata_cannot_be_restamped_on_any_outcome(self):
        _, candidates = self.evidence()
        for outcome in ("accepted", "rejected"):
            original = next(r for r in candidates if r["result"]["outcome"] == outcome)
            self.assertEqual(validation.validate_record(original, catalog=fixture()), [])
            for section, key in (("scenario", "task_specification"), ("scenario", "language"),
                                 ("scenario", "record_kind"), ("candidate_prediction", "method")):
                with self.subTest(outcome=outcome, field=key):
                    changed = copy.deepcopy(original)
                    changed[section][key] = "unreviewed instructions"
                    restamp(changed)
                    self.assertEqual(oc.check_digest(changed, "restamped"), [])
                    self.assertTrue(validation.validate_record(changed, catalog=fixture()))

    def test_measurements_must_equal_actual_phase_readings(self):
        _, candidates = self.evidence()
        for outcome in ("accepted", "rejected"):
            original = next(r for r in candidates if r["result"]["outcome"] == outcome)
            integral_float = float(original["result"]["measurements"][0]["value"])
            for field, value in (("value", 999), ("value", True), ("value", integral_float),
                                 ("unit", "invented"),
                                 ("meter", "invented"), ("quantity", "invented"),
                                 ("detail", {"phase": "invented", "suite": "public"})):
                with self.subTest(outcome=outcome, field=field, value=value):
                    changed = copy.deepcopy(original)
                    changed["result"]["measurements"][0][field] = value
                    restamp(changed)
                    self.assertEqual(oc.check_digest(changed, "restamped"), [])
                    self.assertTrue(validation.validate_record(changed, catalog=fixture()))

    def test_measurement_list_presence_and_order_are_bound(self):
        _, candidates = self.evidence()
        for outcome in ("accepted", "rejected"):
            original = next(r for r in candidates if r["result"]["outcome"] == outcome)
            for mode in ("empty", "missing", "extra", "reordered"):
                with self.subTest(outcome=outcome, mode=mode):
                    changed = copy.deepcopy(original)
                    readings = changed["result"]["measurements"]
                    if mode == "missing":
                        del changed["result"]["measurements"]
                    else:
                        replacements = {"empty": [], "extra": readings + [readings[0]],
                                        "reordered": list(reversed(readings))}
                        changed["result"]["measurements"] = replacements[mode]
                    restamp(changed)
                    self.assertTrue(validation.validate_record(changed, catalog=fixture()))

    def test_seeded_draw_identity_cannot_be_swapped_and_restamped(self):
        run, candidates = self.evidence()
        self.assertEqual(capture(run, candidates), [])
        identities = [(r["id"], r["intervention"]["draw_index"]) for r in candidates[:2]]
        for record, (record_id, index) in zip(candidates[:2], reversed(identities)):
            record["id"] = record_id
            record["intervention"]["draw_index"] = index
            record["oracle"]["seed"] = records.candidate_seed(
                run["seed"], record["scenario"]["source"]["program_id"], index,
            )
            restamp(record)
            self.assertEqual(validation.validate_record(record, catalog=fixture()), [])
        self.assertTrue(capture(run, candidates))

    def test_skip_accounting_must_come_from_the_same_draw_plan(self):
        run, candidates = self.evidence()
        skipped = run["skips"].pop("DUPLICATE_MUTANT_IN_RUN")
        self.assertGreater(skipped, 0)
        run["skips"]["MUTATION_UNVERIFIABLE"] = skipped
        self.assertTrue(capture(run, candidates))

    def test_generated_zero_skip_key_cannot_be_removed(self):
        run, candidates = self.evidence()
        self.assertEqual(capture(run, candidates), [])
        self.assertEqual(run["skips"].pop("MUTATION_NO_SITES"), 0)
        self.assertTrue(capture(run, candidates))

    def test_ungenerated_zero_skip_key_cannot_be_added(self):
        run, candidates = self.evidence()
        self.assertEqual(capture(run, candidates), [])
        self.assertNotIn("MUTATION_UNVERIFIABLE", run["skips"])
        run["skips"]["MUTATION_UNVERIFIABLE"] = 0
        self.assertTrue(capture(run, candidates))


class PlanningEquivalence(unittest.TestCase):
    def test_duplicate_draws_preserve_original_indexes(self):
        plan = planning.ProposalPlan(fixture(), SEED, 3)
        proposals = list(plan.proposals(12))
        self.assertEqual([p.index for p in proposals], [0, 1, 2, 3, 5, 6, 7, 8, 9, 10])
        self.assertEqual(plan.skips, {"MUTATION_NO_SITES": 0, "DUPLICATE_MUTANT_IN_RUN": 2})

    def test_real_cap_exhaustion_and_no_site_inventory_match_plan(self):
        cases = ((FIXTURE_CATALOG, 40, 1, 6, {"MUTATION_NO_SITES": 0, "PROGRAM_CAP_EXHAUSTED": 34}),
                 (REPO / "catalogs/python-repair-v1", 2, 3, 2, {"MUTATION_NO_SITES": 4}))
        for catalog_dir, count, cap, wanted_records, wanted_skips in cases:
            with self.subTest(catalog=catalog_dir.name), tempfile.TemporaryDirectory() as scratch:
                out = Path(scratch) / "run"
                run = generate.run(generate.RunRequest(
                    catalog_dir, out, SEED, count, PINNED_AT, per_program_cap=cap,
                ))
                self.assertEqual(run["records"], wanted_records)
                self.assertEqual(run["skips"], wanted_skips)
                candidates = [r for _, r in oc.read_jsonl(out / "candidates.jsonl")]
                self.assertEqual(validation.validate_run(
                    run, candidates, catalog=catalog.load_catalog(catalog_dir),
                    candidates_sha256=run["candidates_sha256"],
                ), [])

    def test_real_abstention_requires_empty_measurements(self):
        with tempfile.TemporaryDirectory() as scratch:
            out = Path(scratch) / "run"
            generate.run(generate.RunRequest(
                FIXTURE_CATALOG, out, SEED, 1, PINNED_AT, timeout_s=0.001,
            ))
            record = oc.read_jsonl(out / "candidates.jsonl")[0][1]
            self.assertEqual(record["result"]["status"], "abstained")
            self.assertEqual(record["result"]["measurements"], [])
            self.assertEqual(validation.validate_record(record, catalog=fixture()), [])
            record["result"]["measurements"] = copy.deepcopy(smoke_run()[1][0]["result"]["measurements"])
            restamp(record)
            self.assertTrue(validation.validate_record(record, catalog=fixture()))



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
