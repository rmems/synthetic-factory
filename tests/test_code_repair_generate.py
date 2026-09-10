#!/usr/bin/env python3
"""The run engine: request refusals, accounting, artifacts, stable bytes."""

import hashlib
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from code_repair_test_support import (  # noqa: E402
    FIXTURE_CATALOG, FakeExecutor, PINNED_AT, SEED, catalog, fixture, generate, oc, refusal, report, rows, smoke_run,
    vocabulary as cv,
)


class Refusals(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="code-repair-gen-"))
        self.addCleanup(shutil.rmtree, self.root, True)

    def request(self, **overrides):
        fields = {
            "catalog_dir": FIXTURE_CATALOG, "out_dir": self.root / "run", "seed": SEED, "count": 2,
            "produced_at": PINNED_AT,
        }
        fields.update(overrides)
        return generate.RunRequest(**fields)

    def test_seed_count_cap_and_timeout_domains(self):
        cases = (
            ({"seed": "7"}, cv.FINDING_SEED_NOT_AN_INTEGER), ({"seed": True}, cv.FINDING_SEED_NOT_AN_INTEGER),
            ({"seed": -1}, cv.FINDING_SEED_OUT_OF_DOMAIN), ({"seed": 2**64}, cv.FINDING_SEED_OUT_OF_DOMAIN),
            ({"seed": 10**5000}, cv.FINDING_SEED_OUT_OF_DOMAIN),
            ({"count": 0}, cv.FINDING_COUNT_OUT_OF_DOMAIN), ({"count": 2.0}, cv.FINDING_COUNT_OUT_OF_DOMAIN),
            ({"count": cv.MAX_COUNT + 1}, cv.FINDING_COUNT_OUT_OF_DOMAIN),
            ({"per_program_cap": 0}, cv.FINDING_CAP_OUT_OF_DOMAIN),
            ({"timeout_s": 0}, cv.FINDING_TIMEOUT_OUT_OF_DOMAIN),
        )
        for overrides, code in cases:
            label = next(iter(overrides))
            with self.subTest(field=label, code=code), refusal(self, code):
                generate.run(self.request(**overrides))

    def test_destinations_that_exist_or_alias_the_raw_tree_are_refused(self):
        (self.root / "run").mkdir()
        with refusal(self, cv.FINDING_DESTINATION_EXISTS, "already exists"):
            generate.run(self.request())
        raw = self.root / "outputs" / "raw" / "x"
        with refusal(self, cv.FINDING_DESTINATION_UNDER_RAW, "raw tree"):
            generate.run(self.request(out_dir=raw))
        self.assertFalse(raw.exists())

    def test_a_catalog_refusal_surfaces_before_any_execution(self):
        with refusal(self, cv.FINDING_CATALOG_FILE_MISSING):
            generate.run(self.request(catalog_dir=self.root / "nowhere"))


class Accounting(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="code-repair-gen-"))
        self.addCleanup(shutil.rmtree, self.root, True)

    def run_fake(self, count=6, cap=3, seed=SEED):
        fake = FakeExecutor({
            "original": lambda job: report(rows("public", 9), rows("hidden", 24)),
            "mutant": lambda job: report(rows("public", 9, (0,), got="9"), rows("hidden", 24, (0,))),
            "repaired": lambda job: report(rows("public", 9), rows("hidden", 24)),
        })
        out = self.root / f"run-{seed}-{count}"
        request = generate.RunRequest(FIXTURE_CATALOG, out, seed, count, PINNED_AT, per_program_cap=cap)
        return generate.run(request, fake), fake, out

    def test_the_summary_accounts_for_every_draw(self):
        summary, fake, out = self.run_fake()
        drawn = summary["records"] + sum(v for k, v in summary["skips"].items() if k != cv.SKIP_MUTATION_NO_SITES)
        self.assertEqual(drawn, 6)
        self.assertEqual(summary["skips"][cv.SKIP_MUTATION_NO_SITES], 0)
        self.assertEqual(summary["outcomes"], {"accepted": summary["records"]})
        self.assertEqual(summary["seed"], SEED)
        self.assertEqual(summary["produced_at"], PINNED_AT)
        self.assertEqual(sum(p["records"] for p in summary["programs"].values()), summary["records"])
        originals = [job for job in fake.jobs if job.label.startswith("original:")]
        self.assertEqual(len(originals), len({job.label for job in originals}))
        for name in (generate.CANDIDATES_FILENAME, generate.RUN_FILENAME, generate.LOG_FILENAME):
            self.assertTrue((out / name).is_file(), name)

    def test_the_per_program_cap_bounds_variants_and_exhausts_cleanly(self):
        summary, _fake, _out = self.run_fake(count=40, cap=1)
        self.assertTrue(all(p["records"] <= 1 for p in summary["programs"].values()))
        self.assertIn(cv.SKIP_PROGRAM_CAP_EXHAUSTED, summary["skips"])

    def test_a_failing_original_skips_the_mutant_and_repaired_phases(self):
        fake = FakeExecutor({
            "original": lambda job: report(failure="timeout"),
            "mutant": lambda job: self.fail("the mutant phase must not run"),
            "repaired": lambda job: self.fail("the repaired phase must not run"),
        })
        request = generate.RunRequest(FIXTURE_CATALOG, self.root / "run", SEED, 2, PINNED_AT)
        summary = generate.run(request, fake)
        self.assertEqual(summary["reasons"], {cv.REASON_ORIGINAL_TIMEOUT: summary["records"]})
        self.assertEqual(summary["oracle_statuses"], {cv.STATUS_INVALID: summary["records"]})
        originals = [e for e in fake.log if e["label"].startswith("original:")]
        self.assertEqual(fake.log[0]["label"], originals[0]["label"])

    def test_a_reference_that_does_not_certify_leaves_records_provisional(self):
        """Codex on #197: validated is decided on this run's reference execution."""

        fake = FakeExecutor({
            "original": lambda job: report(rows("public", 9), rows("hidden", 24)),
            "mutant": lambda job: report(rows("public", 9, (0,), got="9"), rows("hidden", 24, (0,))),
            "repaired": lambda job: report(rows("public", 9), rows("hidden", 24)),
            "reference": lambda job: report((), rows("hidden", len(job.cases), (0,))),
        })
        request = generate.RunRequest(FIXTURE_CATALOG, self.root / "run", SEED, 4, PINNED_AT)
        summary = generate.run(request, fake)
        self.assertEqual(summary["oracle_statuses"], {cv.STATUS_PROVISIONAL: summary["records"]})
        references = [e["label"] for e in fake.log if e["label"].startswith("reference:")]
        self.assertEqual(len(references), len(set(references)))  # once per program

    def test_rejected_candidates_skip_the_repaired_phase(self):
        fake = FakeExecutor({
            "original": lambda job: report(rows("public", 9), rows("hidden", 24)),
            "mutant": lambda job: report(rows("public", 9), rows("hidden", 24)),
            "repaired": lambda job: self.fail("the repaired phase must not run"),
        })
        request = generate.RunRequest(FIXTURE_CATALOG, self.root / "run", SEED, 3, PINNED_AT)
        summary = generate.run(request, fake)
        self.assertEqual(summary["outcomes"], {"rejected": summary["records"]})
        self.assertEqual(summary["reasons"], {cv.REASON_MUTANT_NO_OBSERVED_FAILURE: summary["records"]})


class StableBytes(unittest.TestCase):
    def test_run_summary_carries_the_pinned_catalog_split_policy(self):
        summary, _, _ = smoke_run()
        metadata = json.loads((FIXTURE_CATALOG / 'CATALOG.json').read_text())
        self.assertEqual(summary.get('split_policy'), metadata['split_policy'])

    """Real subprocess evidence: the smoke run and a second identical run."""

    def test_two_real_runs_with_the_same_seed_and_stamp_are_byte_identical(self):
        summary, records, run_dir = smoke_run()
        again = Path(tempfile.mkdtemp(prefix="code-repair-again-")) / "run"
        self.addCleanup(shutil.rmtree, again.parent, True)
        generate.run(generate.RunRequest(FIXTURE_CATALOG, again, SEED, summary["count"], PINNED_AT))
        first = hashlib.sha256((run_dir / generate.CANDIDATES_FILENAME).read_bytes()).hexdigest()
        second = hashlib.sha256((again / generate.CANDIDATES_FILENAME).read_bytes()).hexdigest()
        self.assertEqual(first, second)
        self.assertEqual(summary["outcomes"], {"accepted": 7, "rejected": 3})
        self.assertEqual(
            summary["reasons"],
            {"HIDDEN_CHECK_UNAVAILABLE": 2, "MUTANT_FAILS_HIDDEN": 7, "MUTANT_FAILS_PUBLIC": 7,
             "MUTANT_NO_OBSERVED_FAILURE": 2, "MUTANT_NO_PUBLIC_FAILURE": 1, "REPAIR_PASSES_ALL": 7},
        )
        self.assertEqual(summary["oracle_statuses"], {"provisional": 2, "validated": 8})
        self.assertEqual(summary["skips"][cv.SKIP_DUPLICATE_MUTANT_IN_RUN], 2)
        identity = catalog.sha256_text(oc.canonical_json(
            [fixture().catalog_id, fixture().programs_sha256]))
        expected_ids = [f"pfr-{identity}-{SEED}-{i:05d}" for i in (0, 1, 2, 3, 5, 6, 7, 8, 9, 10)]
        self.assertEqual([r["id"] for r in records], expected_ids)
        operators = {r["intervention"]["operator"] for r in records}
        self.assertEqual(operators, set(cv.OPERATORS))
        log = [entry for _n, entry in oc.read_jsonl(run_dir / generate.LOG_FILENAME)]
        self.assertTrue(all("duration_s" in entry for entry in log))
        self.assertTrue(all("timed_out" in entry for entry in log))


if __name__ == "__main__":
    unittest.main()
