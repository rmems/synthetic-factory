"""The shared validator binds retained rows to evidence the emitter could produce."""

from __future__ import annotations

import copy
import json
import unittest
from collections import Counter

from tests.code_repair_admission_test_support import (
    build_generated_admission_evidence,
    passing_rows,
    restamp_evidence,
    validate_captured_run,
)
from tests.test_curate_identity import identity as ci
from tests.code_repair_test_support import oc, vocabulary as cv
from code_repair import admission, catalog, source_policy, validation


class EmittedEvidenceContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root, cls.run_dir, cls.records, cls.row = build_generated_admission_evidence(cls)
        cls.trusted = admission.load_trusted_catalog(cls.row)

    def candidates_with(self, changed):
        return [changed if record["id"] == changed["id"] else record for record in self.records]

    def run_with(self, changed=None):
        run = json.loads((self.run_dir / "RUN.json").read_bytes())
        candidates = self.records if changed is None else self.candidates_with(changed)
        run["outcomes"] = dict(sorted(Counter(
            record["result"]["outcome"] for record in candidates
        ).items()))
        run["oracle_statuses"] = dict(sorted(Counter(
            record["result"]["oracle_status"] for record in candidates
        ).items()))
        run["reasons"] = dict(sorted(Counter(
            reason for record in candidates for reason in record["result"]["reason_codes"]
        ).items()))
        return validate_captured_run(run, candidates, trusted_catalog=self.trusted)

    def curate(self, record):
        source = ci.SourceRecord(record, f"{self.row.path_id}/batch-r01.jsonl", 1)
        return ci.curate_record(source)

    def assert_shared_refusal(self, record):
        self.assertEqual(oc.check_digest(record, "restamped"), [])
        self.assertTrue(validation.validate_record(record, catalog=self.trusted))
        with self.assertRaises(source_policy.SourcePolicyError):
            admission.natural_eligibility(record, self.row, catalog=self.trusted)
        self.assertEqual(self.curate(record).action, "exclude")
        self.assertTrue(self.run_with(record))

    def assert_valid_evidence(self, record, expected_eligibility):
        self.assertEqual(validation.validate_record(record, catalog=self.trusted), [])
        self.assertEqual(
            admission.natural_eligibility(record, self.row, catalog=self.trusted),
            expected_eligibility,
        )
        self.assertEqual(self.curate(record).action, "retained")

    def accepted(self):
        return next(record for record in self.records if record["result"]["outcome"] == "accepted")

    def test_unexecuted_files_are_refused(self):
        for location in ("broken", "repair"):
            record = copy.deepcopy(self.accepted())
            files = (record["scenario"]["broken_program"]["files"] if location == "broken"
                     else record["candidate_prediction"]["predicted_repair"]["files"])
            files["extra.py"] = "unexecuted = True\n"
            restamp_evidence(record)
            self.assert_shared_refusal(record)

    def test_producer_cannot_supply_a_passed_validation_stamp(self):
        record = copy.deepcopy(self.accepted())
        record = oc.stamp_validation(record, validator="fabricated", version="1", findings=[])
        with self.assertRaises(source_policy.SourcePolicyError):
            admission.natural_eligibility(record, self.row, catalog=self.trusted)

    def test_relative_authorized_catalog_is_accepted(self):
        supplied = catalog.load_catalog("catalogs/python-repair-v1")
        self.assertEqual(admission.natural_eligibility(
            self.accepted(), self.row, catalog=supplied), (True, ()))

    def test_fabricated_passing_outputs_are_refused(self):
        for suite in ("public", "hidden"):
            record = copy.deepcopy(self.accepted())
            for observed in passing_rows(record, suite):
                observed.update(got="fabricated", got_sha256=catalog.sha256_text("fabricated"),
                                truncated=False)
            restamp_evidence(record)
            self.assert_shared_refusal(record)

    def test_replay_loader_preserves_out_of_range_decimal_token(self):
        from code_repair import replay
        record = copy.deepcopy(self.accepted())
        record["oracle"]["configuration"]["timeout_s"] = 60.0
        restamp_evidence(record)
        payload = oc.canonical_json(record).replace(
            '"timeout_s":60.0', '"timeout_s":60.0000000000000000000001')
        directory = self.root / "exact-replay"
        directory.mkdir()
        (directory / "candidates.jsonl").write_text(payload + "\r\n")
        loaded, = replay._records(directory)
        self.assertTrue(validation.validate_record(loaded, catalog=self.trusted))

    def test_stored_public_outcomes_preserve_doctest_directives_and_clipping(self):
        from code_repair import executor, row_validation
        examples = (
            ("f()  # doctest: +ELLIPSIS", "xxx...", "print('x' * 2100 + 'a')"),
            ("f()  # doctest: +IGNORE_EXCEPTION_DETAIL",
             "Traceback (most recent call last):\n    ValueError: expected",
             "raise ValueError('actual')"),
            ("f()  # doctest: +IGNORE_EXCEPTION_DETAIL",
             "Traceback (most recent call last):\n    ValueError: expected",
             "raise ValueError('actual\\nsecond line')"),
            ("f()", "Traceback (most recent call last):\n    ValueError: " + "x" * 2100,
             "raise ValueError('x' * 2100)"),
        )
        engine = executor.Executor(timeout_s=3)
        for source, want, body in examples:
            with self.subTest(source=source):
                text = f"def f():\n    '''\n    >>> {source}\n    {want}\n    '''\n    {body}\n"
                report = engine.run(executor.Job("doctest-options", text, "f", (), True, 1))
                observed, = executor.rows_of(report.public)
                self.assertEqual(observed["status"], "pass")
                example, = row_validation._public_examples(text, "f")
                self.assertTrue(row_validation._public_matches(observed, example))


    def natural_rejection(self):
        return next(
            record for record in self.records
            if record["result"]["reason_codes"] == [cv.REASON_MUTANT_NO_OBSERVED_FAILURE]
        )

    def test_coherently_restamped_phase_that_was_not_scheduled_is_refused(self):
        record = copy.deepcopy(self.natural_rejection())
        self.assertIsNone(record["result"]["phases"]["repaired"])
        record["result"]["phases"]["repaired"] = copy.deepcopy(
            record["result"]["phases"]["original"]
        )
        restamp_evidence(record)

        self.assert_shared_refusal(record)

    def test_coherently_restamped_public_row_without_observations_is_refused(self):
        record = copy.deepcopy(self.accepted())
        row = next(
            row for row in record["result"]["phases"]["mutant"]["public"]
            if row["status"] != cv.ROW_SUCCESS and row["got"].strip()
        )
        for field in ("got", "truncated", "got_sha256"):
            del row[field]
        restamp_evidence(record, refresh_public_evidence=True)

        self.assert_shared_refusal(record)

    def test_empty_public_output_is_still_complete_observation_evidence(self):
        record = copy.deepcopy(self.accepted())
        row = next(
            row for row in record["result"]["phases"]["mutant"]["public"]
            if row["status"] != cv.ROW_SUCCESS
        )
        row.update(
            got="",
            truncated=False,
            got_sha256=catalog.sha256_text(""),
        )
        restamp_evidence(record, refresh_public_evidence=True)

        self.assert_valid_evidence(record, (True, ()))
        self.assertEqual(self.run_with(record), [])

    def test_declared_rejection_without_repaired_phase_remains_valid(self):
        rejected = self.natural_rejection()
        self.assertIsNone(rejected["result"]["phases"]["repaired"])
        self.assert_valid_evidence(
            rejected,
            (False, (cv.REASON_MUTANT_NO_OBSERVED_FAILURE,)),
        )
        self.assertEqual(self.run_with(), [])

    def test_hidden_rows_without_public_observation_fields_remain_valid(self):
        accepted = self.accepted()
        self.assertTrue(any(
            "got" not in row
            for phase in accepted["result"]["phases"].values() if phase is not None
            for row in phase["hidden"]
        ))
        self.assert_valid_evidence(accepted, (True, ()))

    def test_failed_phase_with_empty_rows_remains_valid_negative_evidence(self):
        record = copy.deepcopy(self.natural_rejection())
        mutant = record["result"]["phases"]["mutant"]
        mutant.update(status=cv.PHASE_TIMEOUT, load_ok=False, limits_applied=None,
                      public=[], hidden=[])
        record["result"]["reason_codes"] = [cv.REASON_MUTANT_TIMEOUT]
        restamp_evidence(record, refresh_public_evidence=True)

        self.assert_valid_evidence(record, (False, (cv.REASON_MUTANT_TIMEOUT,)))
        self.assertEqual(self.run_with(record), [])


if __name__ == "__main__":
    unittest.main()
