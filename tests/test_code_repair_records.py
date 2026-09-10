#!/usr/bin/env python3
"""Envelope records of the family: contract checks, curation gate, tampers, golden bytes.

Fake-executor evidence (canned reports) pins the record bytes; real subprocess
evidence (the smoke corpus) proves the same assembly passes every shared check
with rows the harness actually produced.
"""

import copy
import dataclasses
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from code_repair_test_support import (  # noqa: E402
    FIXTURE_CATALOG, FakeExecutor, PINNED_AT, SEED, boundary_site, envelope, generate, mutate, oc,
    program, records, refusal, report, rows, smoke_run, verify, vocabulary as cv,
)

# The pin moves whenever the harness bytes, the fixture catalog or the record layout change:
# the harness digest sits inside every record's oracle fingerprint by design. Re-pinned for the
# exact-integer harness (Codex on #196) and the executed reference phase (Codex on #197), then
# for digests on passing rows (Codex on #196, round 3).
GOLDEN_SHA256 = "0dbbd01684bbdd76aec31653d5435f78cb0327c143f297bd10b09d0d6a9ba42f"


def accepting_executor():
    return FakeExecutor({
        "original": lambda job: report(rows("public", 9), rows("hidden", 24)),
        "mutant": lambda job: report(rows("public", 9, (0,), got="9"), rows("hidden", 24, (0,))),
        "repaired": lambda job: report(rows("public", 9), rows("hidden", 24)),
        "reference": lambda job: report((), rows("hidden", len(job.cases))),
    })


def fake_records(seed=SEED, count=4, executor=None):
    root = Path(tempfile.mkdtemp(prefix="code-repair-fake-"))
    try:
        request = generate.RunRequest(FIXTURE_CATALOG, root / "run", seed, count, PINNED_AT)
        generate.run(request, executor or accepting_executor())
        return [r for _n, r in oc.read_jsonl(root / "run" / generate.CANDIDATES_FILENAME)]
    finally:
        shutil.rmtree(root, ignore_errors=True)


def contract_findings(record):
    where = record["id"]
    return (
        oc.check_envelope(record, where) + oc.check_digest(record, where)
        + oc.check_measurements(record, where) + oc.check_no_theoretical_energy_claim(record, where)
        + oc.check_oracle_label_leak(record, where)
    )


class GoldenBytes(unittest.TestCase):
    def test_a_fixed_seed_and_pinned_stamp_rebuild_the_same_record_bytes(self):
        first, second = fake_records(), fake_records()
        self.assertEqual(first, second)
        self.assertEqual(first[0]["id"], f"pfr-7d4f596598e144d5da999d58015279b84e3889dad99028b611407f4fee20adff-{SEED}-00000")
        self.assertEqual(first[0]["provenance"]["produced_at"], PINNED_AT)
        self.assertEqual(first[0]["provenance"]["record_sha256"], GOLDEN_SHA256)

    def test_the_real_corpus_shares_the_golden_proposal(self):
        """The generator sections do not depend on what the oracle saw."""

        _summary, real, _run_dir = smoke_run()
        fake = fake_records(count=12)
        by_id = {r["id"]: r for r in fake}
        for record in real:
            with self.subTest(record=record["id"]):
                self.assertEqual(envelope.proposal_digest(record), envelope.proposal_digest(by_id[record["id"]]))


class ContractChecks(unittest.TestCase):
    def test_fake_and_real_records_pass_every_shared_check_and_the_curation_gate(self):
        _summary, real, _run_dir = smoke_run()
        for label, corpus in (("fake", fake_records()), ("real", real)):
            for record in corpus:
                with self.subTest(label=label, record=record["id"]):
                    findings = contract_findings(record)
                    self.assertEqual(findings, [])
                    eligible, reasons = oc.curation_eligible(record, findings)
                    self.assertTrue(eligible, reasons)
                    self.assertEqual(record["family"], cv.FAMILY)
                    self.assertEqual(record["scenario"]["record_kind"], cv.RECORD_KIND)
                    self.assertEqual(record["oracle"]["type"], cv.ORACLE_TYPE)
                    self.assertEqual(record["generator"]["authority"], "propose_only")

    def test_counts_are_genuine_ints_per_phase_and_suite(self):
        record = fake_records(count=1)[0]
        readings = record["result"]["measurements"]
        self.assertEqual(len(readings), 18)  # four program phases and the reference's hidden suite
        self.assertTrue(all(isinstance(r["value"], int) and not isinstance(r["value"], bool) for r in readings))
        detail = {(r["detail"]["phase"], r["detail"]["suite"]) for r in readings}
        expected = {(p, s) for p in cv.PHASES for s in (cv.SUITE_PUBLIC, cv.SUITE_HIDDEN)}
        self.assertEqual(detail, expected - {(cv.PHASE_REFERENCE, cv.SUITE_PUBLIC)})
        self.assertTrue(all(r["meter"] == cv.METER and r["measured"] is True for r in readings))

    def test_actors_source_kind_and_lineage_ride_in_provenance(self):
        record = fake_records(count=1)[0]
        provenance = record["provenance"]
        self.assertEqual(set(provenance["actors"]), set(cv.ACTOR_ROLES))
        self.assertNotEqual(provenance["actors"]["solver"]["name"], provenance["actors"]["task_author"]["name"])
        self.assertEqual(provenance["source_kind"], cv.SOURCE_KIND)
        self.assertEqual(provenance["split_lineage"]["lineage_id"], record["scenario"]["source"]["program_id"])
        self.assertEqual(record["oracle"]["fingerprint"]["python"], "3.14")
        self.assertEqual(len(record["oracle"]["fingerprint"]["harness_sha256"]), 64)

    def test_a_rejected_record_is_stored_as_evidence_and_stays_eligible(self):
        fake = FakeExecutor({
            "original": lambda job: report(rows("public", 9), rows("hidden", 24)),
            "mutant": lambda job: report(rows("public", 9), rows("hidden", 24)),
        })
        record = fake_records(count=1, executor=fake)[0]
        self.assertEqual(record["result"]["outcome"], cv.OUTCOME_REJECTED)
        self.assertEqual(record["result"]["reason_codes"], [cv.REASON_MUTANT_NO_OBSERVED_FAILURE])
        self.assertIsNone(record["result"]["phases"]["repaired"])
        self.assertEqual(oc.curation_eligible(record, contract_findings(record)), (True, []))

    def test_a_harness_failure_on_the_original_abstains(self):
        fake = FakeExecutor({
            "original": lambda job: report(failure="load", detail="ImportError: nope"),
            "mutant": lambda job: report(failure="load", detail="ImportError: nope"),
        })
        record = fake_records(count=1, executor=fake)[0]
        self.assertEqual(record["result"]["status"], oc.RESULT_ABSTAINED)
        self.assertEqual(record["result"]["oracle_status"], cv.STATUS_INVALID)
        # The volatile harness detail stays in the execution log (Codex on #197).
        self.assertEqual(
            record["result"]["abstention_reason"],
            f"{cv.REASON_ORIGINAL_HARNESS_ERROR}: the harness could not measure the original program",
        )
        self.assertEqual(contract_findings(record), [])
        eligible, reasons = oc.curation_eligible(record, [])
        self.assertFalse(eligible)
        self.assertTrue(any(r.startswith("ORACLE_RESULT_NOT_MEASURED") for r in reasons))


class Tampers(unittest.TestCase):
    def test_edited_phase_rows_break_the_digest_and_the_gate(self):
        record = copy.deepcopy(fake_records(count=1)[0])
        record["result"]["phases"]["mutant"]["public"][0]["status"] = "pass"
        findings = oc.check_digest(record, record["id"])
        self.assertEqual(len(findings), 1)
        self.assertFalse(oc.curation_eligible(record, findings)[0])

    def test_a_label_planted_in_the_scenario_is_refused_at_build_time(self):
        prog = program("factorial")
        poisoned = dataclasses.replace(prog, upstream={**prog.upstream, "outcome": "accepted"})
        site = boundary_site(prog)
        mutated = mutate.apply(prog.text, site)
        phases = verify.Phases(
            report(rows("public", 7), rows("hidden", 15)),
            report(rows("public", 7, (3,), got="2"), rows("hidden", 15, (0,))),
            report(rows("public", 7), rows("hidden", 15)),
            reference=report((), rows("hidden", 15)),
            original_repeat=report(rows("public", 7), rows("hidden", 15)),
        )
        context = verify.DecisionContext(prog.reference.kind, True, False, len(prog.cases))
        verdict = verify.decide(phases, context)
        evidence, omitted = verify.public_evidence(phases.mutant, prog.examples)
        candidate = records.Candidate(
            "pfr-1-00000", poisoned, mutate.Mutation(site, prog.text, mutated), prog.text, phases,
            verdict, tuple(evidence), omitted, 7, 0,
        )
        batch = records.new_batch(SEED, PINNED_AT, accepting_executor())
        with refusal(self, cv.FINDING_RECORD_FAILS_ENVELOPE, "refuses"):
            records.build_record(candidate, batch)
        clean = records.build_record(dataclasses.replace(candidate, program=prog), batch)
        self.assertEqual(contract_findings(clean), [])
        self.assertTrue(verdict.accepted)

    def test_produced_at_must_be_a_real_instant(self):
        for stamp in ("2026-02-30T00:00:00Z", "yesterday", 5):
            with self.subTest(stamp=repr(stamp)), refusal(self, cv.FINDING_PRODUCED_AT_NOT_A_TIMESTAMP, "produced_at"):
                generate.run(generate.RunRequest(FIXTURE_CATALOG, Path("/nonexistent/x"), SEED, 1, stamp))

    def test_candidate_seeds_are_64_bit_and_distinct(self):
        seeds = {records.candidate_seed(SEED, "tap-a", i) for i in range(50)}
        self.assertEqual(len(seeds), 50)
        self.assertTrue(all(0 <= s < 2**64 for s in seeds))


if __name__ == "__main__":
    unittest.main()
