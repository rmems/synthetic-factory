"""Sealed evidence and deterministic planning integration scenarios."""

from __future__ import annotations

import copy
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from tests.code_repair_admission_test_support import (
    PROCEDURAL_FACTORY,
    RAW_RUN,
    REAL_CATALOG,
    REAL_COUNT,
    REAL_PRODUCED_AT,
    restamp,
    validate_captured_run,
)
from tests.code_repair_test_support import (
    FIXTURE_CATALOG,
    PINNED_AT,
    REPO,
    SEED,
    catalog,
    fixture,
    generate,
    oc,
    records,
    smoke_run,
    vocabulary as cv,
)
import compose_curated
import training_audit
from code_repair import planning, publication, validation
from pipelines import eval_exclusion_policy as policy
from tests.code_repair_test_support import required_item


class TrustedBindings(unittest.TestCase):
    @staticmethod
    def evidence():
        return copy.deepcopy(smoke_run()[:2])

    def test_fixed_task_metadata_cannot_be_restamped_on_any_outcome(self):
        _, candidates = self.evidence()
        for outcome in ("accepted", "rejected"):
            original = required_item(r for r in candidates if r["result"]["outcome"] == outcome)
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
            original = required_item(r for r in candidates if r["result"]["outcome"] == outcome)
            integral_float = float(original["result"]["measurements"][0]["value"])
            for field, value in (("value", 999), ("value", True), ("value", integral_float),
                                 ("unit", "invented"), ("meter", "invented"),
                                 ("quantity", "invented"),
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
            original = required_item(r for r in candidates if r["result"]["outcome"] == outcome)
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
        self.assertEqual(validate_captured_run(run, candidates), [])
        identities = [(r["id"], r["intervention"]["draw_index"]) for r in candidates[:2]]
        for record, (record_id, index) in zip(candidates[:2], reversed(identities)):
            record["id"] = record_id
            record["intervention"]["draw_index"] = index
            record["oracle"]["seed"] = records.candidate_seed(
                run["seed"], record["scenario"]["source"]["program_id"], index,
            )
            restamp(record)
            self.assertEqual(validation.validate_record(record, catalog=fixture()), [])
        self.assertTrue(validate_captured_run(run, candidates))

    def test_skip_accounting_must_come_from_the_same_draw_plan(self):
        run, candidates = self.evidence()
        skipped = run["skips"].pop("DUPLICATE_MUTANT_IN_RUN")
        self.assertGreater(skipped, 0)
        run["skips"]["MUTATION_UNVERIFIABLE"] = skipped
        self.assertTrue(validate_captured_run(run, candidates))

    def test_generated_zero_skip_key_cannot_be_removed(self):
        run, candidates = self.evidence()
        self.assertEqual(validate_captured_run(run, candidates), [])
        self.assertEqual(run["skips"].pop("MUTATION_NO_SITES"), 0)
        self.assertTrue(validate_captured_run(run, candidates))

    def test_ungenerated_zero_skip_key_cannot_be_added(self):
        run, candidates = self.evidence()
        self.assertEqual(validate_captured_run(run, candidates), [])
        self.assertNotIn("MUTATION_UNVERIFIABLE", run["skips"])
        run["skips"]["MUTATION_UNVERIFIABLE"] = 0
        self.assertTrue(validate_captured_run(run, candidates))


class PlanningEquivalence(unittest.TestCase):
    def test_unassigned_splits_stay_eligible(self):
        source = fixture()
        unassigned = replace(
            source,
            programs=tuple(replace(program, split=None) for program in source.programs),
            split_policy=None,
        )
        plan = planning.ProposalPlan(unassigned, SEED, 3)
        proposals = list(plan.proposals(4))
        self.assertTrue(proposals)
        self.assertTrue(all(proposal.program.split is None for proposal in proposals))
        self.assertNotIn("PROGRAM_CAP_EXHAUSTED", plan.skips)

    def test_duplicate_draws_preserve_original_indexes(self):
        plan = planning.ProposalPlan(fixture(), SEED, 3)
        proposals = list(plan.proposals(12))
        self.assertEqual([p.index for p in proposals], [0, 1, 2, 3, 4, 5, 6, 9, 10, 11])
        self.assertEqual(plan.skips, {"MUTATION_NO_SITES": 0, "DUPLICATE_MUTANT_IN_RUN": 2})

    def test_a_2_0_0_run_header_is_refused_before_replay(self):
        """Train-only draws are generator 2.1.0; a 2.0.0 stamp is not a matching plan."""

        run, records, _run_dir = smoke_run()
        stale = copy.deepcopy(run)
        stale["generator"] = dict(stale["generator"], version="2.0.0")
        findings = validation.validate_run(
            stale, records, catalog=fixture(), candidates_sha256=run["candidates_sha256"],
        )
        self.assertEqual(findings, [cv.EXPORT_RUN_SUMMARY_MISMATCH])

    def test_real_cap_exhaustion_and_no_site_inventory_match_plan(self):
        cases = ((FIXTURE_CATALOG, 40, 1, 4, {"MUTATION_NO_SITES": 0, "PROGRAM_CAP_EXHAUSTED": 36}),
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

    def test_real_catalog_seed_20260908_draws_train_only_and_stays_training_ready(self):
        """Regression: held-out ids must not be generated (#508) or compose drops the round."""

        seed = 20260908
        deny = policy.ACTIVE_POLICY.denylist.program_ids
        with tempfile.TemporaryDirectory() as scratch:
            root = Path(scratch)
            run_dir = root / "generated"
            generate.run(generate.RunRequest(
                REAL_CATALOG, run_dir, seed, REAL_COUNT, REAL_PRODUCED_AT, per_program_cap=3,
            ))
            for _, record in oc.read_jsonl(run_dir / generate.CANDIDATES_FILENAME):
                lineage = record["provenance"]["split_lineage"]
                self.assertEqual(lineage["split"], "train")
                self.assertNotIn(lineage["lineage_id"], deny)
            factory = root / RAW_RUN / PROCEDURAL_FACTORY
            factory.mkdir(parents=True)
            publication.publish_run(publication.PublishRequest(run_dir, factory, 1))
            source = factory.parent
            before = training_audit.audit_run(source)
            self.assertTrue(before["training_ready"], before["blockers"])
            curated = root / "curated"
            summary = compose_curated.compose_run(
                compose_curated.ComposeRunContext(source, curated),
            )
            self.assertTrue(summary["audit"]["training_ready"], summary["audit"]["blockers"])

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
            record["result"]["measurements"] = copy.deepcopy(
                smoke_run()[1][0]["result"]["measurements"]
            )
            restamp(record)
            self.assertTrue(validation.validate_record(record, catalog=fixture()))
