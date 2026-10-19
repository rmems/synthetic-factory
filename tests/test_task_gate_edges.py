"""Edge branches of the gate: oversized inputs, unreadable files, bad reports, failed writes."""

import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))

from task_gate_test_support import (
    ADD, DENY, PASSED, PROGRAM, FakeHarness, cv, denylist, gate, harness, mutation, proposal,
    proposal_for, refused, report, rules, runner,
)

DOC_ONLY = 'def f():\n    """\n    >>> 1\n    1\n    """\n'


class MutantCache(unittest.TestCase):
    def test_an_identical_rejected_mutant_is_executed_once(self):
        fake = FakeHarness(default=PASSED)
        machine = gate.Gate({"prog-add": PROGRAM}, rules(), fake)
        first, second = machine.run([proposal_for("b + a"), proposal_for("b + a", proposal_id="2")])
        self.assertEqual((first.verdict, second.verdict), (cv.VERDICT_MUTANT_PASSES,) * 2)
        self.assertEqual(len(fake.calls), 2, "one original run and one mutant run")


class ProposalLimits(unittest.TestCase):
    def test_oversized_program_text_refuses(self):
        with mock.patch.object(cv, "MAX_PROGRAM_BYTES", 10):
            code = refused(proposal.GateProgram, "big", ADD, "add")
        self.assertEqual(code, cv.REFUSE_PROGRAM_INVALID)

    def test_oversized_proposal_file_refuses(self):
        with mock.patch.object(cv, "MAX_PROPOSALS_BYTES", 4):
            code = refused(proposal.parse_proposals, b'{"a": 1}\n', "mem")
        self.assertEqual(code, cv.REFUSE_PROPOSALS_INVALID)


class SpanEdges(unittest.TestCase):
    def test_a_function_with_only_a_docstring_has_no_editable_body(self):
        program = proposal.GateProgram("doc-only", DOC_ONLY, "f")
        item = proposal_for("g", "def f", program)
        self.assertEqual(mutation.resolve(program, item), cv.DETAIL_SPAN_OUTSIDE_BODY)

    def test_a_replacement_that_cannot_be_encoded_is_not_program_text(self):
        item = proposal_for("\ud800")
        self.assertEqual(mutation.resolve(PROGRAM, item), cv.DETAIL_MUTANT_SYNTAX_ERROR)


class DenylistEdges(unittest.TestCase):
    def test_a_bare_string_is_not_a_collection_of_ids(self):
        for bare in ("prog-eval", b"prog-eval"):
            with self.subTest(bare=bare):
                self.assertEqual(refused(denylist.Denylist.of, bare), cv.REFUSE_DENYLIST_MALFORMED)

    def test_a_file_that_exists_but_cannot_be_opened_refuses_as_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "deny.txt"
            path.write_bytes(b"prog-eval\n")
            with mock.patch.object(Path, "open", side_effect=OSError("denied")):
                code = refused(denylist.load_denylist, path)
        self.assertEqual(code, cv.REFUSE_DENYLIST_MISSING)

    def test_an_oversized_file_refuses_as_malformed(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "deny.txt"
            path.write_bytes(b"prog-eval\n")
            with mock.patch.object(cv, "MAX_DENYLIST_BYTES", 3):
                code = refused(denylist.load_denylist, path)
        self.assertEqual(code, cv.REFUSE_DENYLIST_MALFORMED)


class HarnessReports(unittest.TestCase):
    def test_a_report_line_that_is_not_json_is_a_crash(self):
        result = harness._report_of(b"TASK-GATE-REPORT {not json\n")
        self.assertEqual((result.outcome, result.detail), (cv.OUTCOME_CRASHED, "report_not_json"))

    def test_no_report_line_is_a_crash(self):
        result = harness._report_of(b"nothing here\n")
        self.assertEqual((result.outcome, result.detail), (cv.OUTCOME_CRASHED, "no_single_report"))

    def test_reports_that_break_the_protocol_are_crashes(self):
        ok = {"protocol": cv.HARNESS_PROTOCOL, "outcome": "ran", "attempted": 2, "failed": 1}
        broken = {
            "not a dict": ["ran"],
            "other protocol": {**ok, "protocol": "other/1"},
            "unknown outcome": {**ok, "outcome": "passed"},
            "negative count": {**ok, "failed": -1},
            "bool count": {**ok, "attempted": True},
            "more failures than examples": {**ok, "attempted": 1, "failed": 2},
        }
        for name, payload in broken.items():
            with self.subTest(name=name):
                self.assertEqual(harness._result_of(payload).outcome, cv.OUTCOME_CRASHED)
        self.assertEqual(harness._result_of(ok), harness.HarnessResult(cv.OUTCOME_FAILED, 2, 1))


class FailedWrites(unittest.TestCase):
    def test_a_failure_while_publishing_leaves_no_destination_and_no_stage(self):
        with tempfile.TemporaryDirectory() as tmp:
            request = runner.GateRequest(
                {"prog-add": PROGRAM}, [proposal_for()], DENY, Path(tmp) / "out",
            )
            fake = FakeHarness({ADD: PASSED})
            with mock.patch.object(report.os, "rename", side_effect=OSError("disk full")):
                with self.assertRaises(OSError):
                    runner.run(request, fake)
            leftover = sorted(path.name for path in Path(tmp).iterdir())
        self.assertEqual(leftover, [])


if __name__ == "__main__":
    unittest.main()
