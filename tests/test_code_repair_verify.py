#!/usr/bin/env python3
"""The decision table, the tamper guard and the public evidence (fake reports; one real corpus)."""

import dataclasses
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from code_repair_test_support import (  # noqa: E402
    program, report, rows, smoke_run, verify, vocabulary as cv,
)

CERTIFIED = verify.DecisionContext(cv.REFERENCE_REVIEWED, True, False, 4)
SELF = verify.DecisionContext(cv.REFERENCE_SELF, True, False, 4)


def phases(mutant_public=(1,), mutant_hidden=(0,), repaired_public=(), repaired_hidden=()):
    """Original clean; mutant and repaired with the listed failing indexes."""

    return verify.Phases(
        report(rows("public", 3), rows("hidden", 4)),
        report(rows("public", 3, mutant_public), rows("hidden", 4, mutant_hidden)),
        report(rows("public", 3, repaired_public), rows("hidden", 4, repaired_hidden)),
        reference=report((), rows("hidden", 4)),
        original_repeat=report(rows("public", 3), rows("hidden", 4)),
    )


class DecisionTable(unittest.TestCase):
    def test_original_passes_mutant_fails_repair_passes_is_accepted_and_validated(self):
        verdict = verify.decide(phases(), CERTIFIED)
        self.assertTrue(verdict.accepted)
        self.assertEqual(verdict.oracle_status, cv.STATUS_VALIDATED)
        self.assertEqual(
            verdict.reason_codes,
            (cv.REASON_MUTANT_FAILS_PUBLIC, cv.REASON_MUTANT_FAILS_HIDDEN, cv.REASON_REPAIR_PASSES_ALL),
        )

    def test_a_program_without_an_independent_reference_is_only_provisional(self):
        verdict = verify.decide(phases(), SELF)
        self.assertTrue(verdict.accepted)
        self.assertEqual(verdict.oracle_status, cv.STATUS_PROVISIONAL)
        self.assertIn(cv.REASON_HIDDEN_CHECK_UNAVAILABLE, verdict.reason_codes)

    def test_validated_needs_the_reference_executed_and_passing_in_this_run(self):
        """Codex on #197: the catalog's word alone never makes a record validated."""

        for label, reference in (
            ("not run", None),
            ("timed out", report(failure="timeout")),
            ("one case disagrees", report((), rows("hidden", 4, (1,)))),
            ("a case is missing", report((), rows("hidden", 3))),
        ):
            with self.subTest(reference=label):
                partial = dataclasses.replace(phases(), reference=reference)
                verdict = verify.decide(partial, CERTIFIED)
                self.assertTrue(verdict.accepted)
                self.assertEqual(verdict.oracle_status, cv.STATUS_PROVISIONAL)
                self.assertIn(cv.REASON_REFERENCE_NOT_CERTIFYING, verdict.reason_codes)
                self.assertNotIn(cv.REASON_HIDDEN_CHECK_UNAVAILABLE, verdict.reason_codes)

    def test_a_broken_original_is_invalid_whatever_the_mutant_did(self):
        broken = verify.Phases(report(rows("public", 3, (0,)), rows("hidden", 4)), phases().mutant)
        verdict = verify.decide(broken, CERTIFIED)
        self.assertEqual((verdict.outcome, verdict.oracle_status), ("rejected", cv.STATUS_INVALID))
        self.assertEqual(verdict.reason_codes, (cv.REASON_ORIGINAL_FAILS_PUBLIC,))
        hidden = verify.Phases(report(rows("public", 3), rows("hidden", 4, (2,))), phases().mutant)
        self.assertEqual(verify.decide(hidden, CERTIFIED).reason_codes, (cv.REASON_ORIGINAL_FAILS_HIDDEN,))
        timeout = verify.Phases(report(failure="timeout"))
        self.assertEqual(verify.decide(timeout, CERTIFIED).reason_codes, (cv.REASON_ORIGINAL_TIMEOUT,))
        crash = verify.Phases(report(failure="harness_error"))
        self.assertEqual(verify.decide(crash, CERTIFIED).reason_codes, (cv.REASON_ORIGINAL_HARNESS_ERROR,))

    def test_a_mutant_with_no_observed_failure_is_rejected_not_called_equivalent(self):
        verdict = verify.decide(phases(mutant_public=(), mutant_hidden=()), CERTIFIED)
        self.assertEqual(verdict.reason_codes, (cv.REASON_MUTANT_NO_OBSERVED_FAILURE,))
        self.assertEqual(verdict.oracle_status, cv.STATUS_VALIDATED)
        self.assertNotIn("EQUIVALENT", " ".join(cv.REASON_CODES))

    def test_failures_visible_to_only_one_suite_are_rejected(self):
        only_hidden = verify.decide(phases(mutant_public=(), mutant_hidden=(1,)), CERTIFIED)
        self.assertEqual(only_hidden.reason_codes, (cv.REASON_MUTANT_NO_PUBLIC_FAILURE,))
        only_public = verify.decide(phases(mutant_public=(1,), mutant_hidden=()), CERTIFIED)
        self.assertEqual(only_public.reason_codes, (cv.REASON_MUTANT_NO_HIDDEN_FAILURE,))
        no_cases = verify.DecisionContext(cv.REFERENCE_SELF, True, False, 0)
        self.assertTrue(verify.decide(phases(mutant_hidden=()), no_cases).accepted)

    def test_a_mutant_timeout_or_crash_is_coded(self):
        timed = dataclasses.replace(phases(), mutant=report(failure="timeout"))
        self.assertEqual(verify.decide(timed, CERTIFIED).reason_codes, (cv.REASON_MUTANT_TIMEOUT,))
        crashed = dataclasses.replace(phases(), mutant=report(failure="load", detail="SyntaxError"))
        self.assertEqual(verify.decide(crashed, CERTIFIED).reason_codes, (cv.REASON_MUTANT_HARNESS_ERROR,))
        missing = dataclasses.replace(phases(), mutant=None)
        self.assertEqual(verify.decide(missing, CERTIFIED).reason_codes, (cv.REASON_MUTANT_HARNESS_ERROR,))

    def test_a_repair_that_does_not_restore_or_edits_the_tests_is_refused_before_running(self):
        not_restored = verify.DecisionContext(cv.REFERENCE_REVIEWED, False, False, 4)
        self.assertEqual(verify.pre_repair_problem(phases(), not_restored), cv.REASON_REPAIR_DOES_NOT_RESTORE)
        tampered = verify.DecisionContext(cv.REFERENCE_REVIEWED, True, True, 4)
        self.assertEqual(verify.pre_repair_problem(phases(), tampered), cv.REASON_PUBLIC_TESTS_TAMPERED)
        self.assertEqual(verify.decide(phases(), tampered).reason_codes, (cv.REASON_PUBLIC_TESTS_TAMPERED,))
        self.assertIsNone(verify.pre_repair_problem(phases(), CERTIFIED))

    def test_an_incorrect_repair_fails(self):
        wrong_public = verify.decide(phases(repaired_public=(1,)), CERTIFIED)
        self.assertEqual(wrong_public.reason_codes, (cv.REASON_REPAIR_FAILS_PUBLIC,))
        wrong_hidden = verify.decide(phases(repaired_hidden=(3,)), CERTIFIED)
        self.assertEqual(wrong_hidden.reason_codes, (cv.REASON_REPAIR_FAILS_HIDDEN,))
        timed = dataclasses.replace(phases(), repaired=report(failure="timeout"))
        self.assertEqual(verify.decide(timed, CERTIFIED).reason_codes, (cv.REASON_REPAIR_TIMEOUT,))
        unrun = dataclasses.replace(phases(), repaired=None)
        self.assertEqual(verify.decide(unrun, CERTIFIED).reason_codes, (cv.REASON_REPAIR_HARNESS_ERROR,))

    def test_every_verdict_code_is_declared(self):
        for code in verify.decide(phases(), CERTIFIED).reason_codes:
            self.assertIn(code, cv.REASON_CODE_SET)


class TamperGuard(unittest.TestCase):
    def test_the_docstring_examples_must_be_exactly_the_catalog_s(self):
        prog = program("factorial")
        self.assertFalse(verify.tests_tampered(prog.examples, prog.text, prog.function))
        edited = prog.text.replace(">>> factorial(6)\n    720", ">>> factorial(6)\n    721", 1)
        self.assertTrue(verify.tests_tampered(prog.examples, edited, prog.function))
        dropped = prog.text.replace("    >>> factorial(0)\n    1\n", "", 1)
        self.assertTrue(verify.tests_tampered(prog.examples, dropped, prog.function))
        self.assertTrue(verify.tests_tampered(prog.examples, "def factorial(:\n", prog.function))


class PublicEvidence(unittest.TestCase):
    def test_entries_come_from_failing_rows_in_docstring_order_and_are_bounded(self):
        prog = program("get_1s_count")
        failing = tuple(range(len(prog.examples)))
        mutant = report(rows("public", len(prog.examples), failing, got="7"), ())
        entries, omitted = verify.public_evidence(mutant, prog.examples)
        self.assertEqual(len(entries), cv.MAX_EVIDENCE_EXAMPLES)
        self.assertEqual(omitted, len(prog.examples) - cv.MAX_EVIDENCE_EXAMPLES)
        self.assertEqual([e["example_id"] for e in entries], ["get_1s_count:0", "get_1s_count:1", "get_1s_count:2"])
        self.assertEqual(entries[0]["source"], prog.examples[0].source)
        text = verify.render_evidence(entries, omitted)
        self.assertIn("Failed example:\n    get_1s_count(25)\nExpected:\n    3\nGot:\n    7", text)
        self.assertTrue(text.endswith(cv.EVIDENCE_MORE.format(count=omitted)))

    def test_a_huge_got_is_truncated_to_the_byte_budget(self):
        prog = program("factorial")
        mutant = report(rows("public", len(prog.examples), (3,), got="x" * 5000), ())
        entries, omitted = verify.public_evidence(mutant, prog.examples)
        self.assertEqual((len(entries), omitted), (1, 0))
        self.assertTrue(entries[0]["truncated"])
        rendered = verify.render_evidence(entries, omitted)
        self.assertLessEqual(len(rendered), cv.MAX_EVIDENCE_CHARS + 20)

    def test_no_failing_rows_means_no_evidence(self):
        prog = program("factorial")
        self.assertEqual(verify.public_evidence(report(rows("public", 7), ()), prog.examples), ([], 0))
        self.assertEqual(verify.render_evidence([], 0), "")


class RealCorpus(unittest.TestCase):
    """Real subprocess evidence: the stored verdicts re-derive from the stored rows."""

    def test_every_smoke_verdict_is_re_derived_from_its_own_phase_rows(self):
        _summary, records, _run_dir = smoke_run()
        self.assertGreaterEqual(len(records), 4)
        for record in records:
            with self.subTest(record=record["id"]):
                result = record["result"]
                blocks = result["phases"]
                self.assertEqual(verify.result_hash(blocks), result["evidence_sha256"])
                self.assertIn(result["outcome"], cv.OUTCOMES)
                self.assertTrue(set(result["reason_codes"]).issubset(cv.REASON_CODE_SET))
                if result["outcome"] == cv.OUTCOME_ACCEPTED:
                    self.assertEqual({r["status"] for r in blocks["repaired"]["public"]}, {"pass"})
                    self.assertTrue(any(r["status"] != "pass" for r in blocks["mutant"]["public"]))
                self.assertEqual({r["status"] for r in blocks["original"]["public"]}, {"pass"})


if __name__ == "__main__":
    unittest.main()
