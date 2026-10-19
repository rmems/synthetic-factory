"""The task gate's decision table: one test per verdict, the required denylist, the dedup index."""

import hashlib
import json
import tempfile
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from task_gate_test_support import (
    ADD, DENY, FAILED, NO_DOCTESTS, PASSED, PROGRAM, PROGRAMS, FakeHarness, cv, dedup_index,
    denylist, gate, harness, mutation, proposal, proposal_for, refused, report, rules, runner,
    span_of,
)


def decide(item, fake=None, rule_set=None, programs=None):
    fake = fake or FakeHarness({ADD: PASSED})
    machine = gate.Gate(PROGRAMS if programs is None else programs, rule_set or rules(), fake)
    return machine.decide(item), fake


class Verdicts(unittest.TestCase):
    def test_kept_when_mutant_fails_a_doctest(self):
        decision, fake = decide(proposal_for())
        self.assertEqual((decision.verdict, decision.detail), (cv.VERDICT_KEPT, cv.DETAIL_MUTANT_FAILED_DOCTESTS))
        self.assertEqual(len(fake.calls), 2)
        self.assertEqual(decision.doctests, {"attempted": 2, "failed": 1})

    def test_mutant_passes_when_every_doctest_still_passes(self):
        decision, _ = decide(proposal_for("b + a"), FakeHarness(default=PASSED))
        self.assertEqual(decision.verdict, cv.VERDICT_MUTANT_PASSES)

    def test_timeout_is_a_reject_not_a_keep(self):
        timeout = harness.HarnessResult(cv.OUTCOME_TIMEOUT, detail="wall_clock")
        decision, _ = decide(proposal_for(), FakeHarness({ADD: PASSED}, default=timeout))
        self.assertEqual((decision.verdict, decision.detail), (cv.VERDICT_TIMEOUT, cv.DETAIL_MUTANT_TIMEOUT))

    def test_original_that_fails_rejects_every_proposal_on_it(self):
        for outcome, detail in (
            (FAILED, cv.DETAIL_ORIGINAL_FAILED),
            (harness.HarnessResult(cv.OUTCOME_LOAD_ERROR), cv.DETAIL_ORIGINAL_LOAD_ERROR),
            (harness.HarnessResult(cv.OUTCOME_TIMEOUT), cv.DETAIL_ORIGINAL_TIMEOUT),
            (harness.HarnessResult(cv.OUTCOME_CRASHED), cv.DETAIL_ORIGINAL_CRASHED),
            (harness.HarnessResult(cv.OUTCOME_PASSED, 0, 0), cv.DETAIL_NO_DOCTESTS),
        ):
            with self.subTest(detail=detail):
                decision, fake = decide(proposal_for(), FakeHarness({ADD: outcome}))
                self.assertEqual((decision.verdict, decision.detail), (cv.VERDICT_ORIGINAL_FAILS, detail))
                self.assertEqual(len(fake.calls), 1, "the mutant must not run on a broken original")

    def test_original_is_run_once_per_program(self):
        fake = FakeHarness({ADD: PASSED})
        machine = gate.Gate(PROGRAMS, rules(), fake)
        machine.run([proposal_for("a - b"), proposal_for("a * b")])
        self.assertEqual([text for text, _ in fake.calls].count(ADD), 1)

    def test_mutant_that_does_not_load_or_crashes_is_a_parse_error(self):
        for outcome, detail in (
            (cv.OUTCOME_LOAD_ERROR, cv.DETAIL_MUTANT_LOAD_ERROR),
            (cv.OUTCOME_CRASHED, cv.DETAIL_MUTANT_CRASHED),
        ):
            with self.subTest(outcome=outcome):
                fake = FakeHarness({ADD: PASSED}, default=harness.HarnessResult(outcome))
                decision, _ = decide(proposal_for(), fake)
                self.assertEqual((decision.verdict, decision.detail), (cv.VERDICT_PARSE_ERROR, detail))


class Denylist(unittest.TestCase):
    def test_denylisted_program_is_rejected_before_anything_runs(self):
        decision, fake = decide(proposal_for(program_id="prog-eval"))
        self.assertEqual((decision.verdict, decision.detail), (cv.VERDICT_DENYLISTED, cv.DETAIL_ON_DENYLIST))
        self.assertEqual(fake.calls, [])

    def test_denylist_wins_over_a_malformed_row_for_the_same_program(self):
        item = proposal.MalformedProposal("x", "prog-eval", cv.DETAIL_MALFORMED_ROW)
        self.assertEqual(decide(item)[0].verdict, cv.VERDICT_DENYLISTED)

    def test_gate_refuses_without_a_loaded_denylist(self):
        for missing in (None, set(), ["prog-eval"], frozenset({"prog-eval"})):
            with self.subTest(missing=missing):
                broken = rules(deny=missing)
                self.assertEqual(
                    refused(gate.Gate, PROGRAMS, broken, FakeHarness()), cv.REFUSE_DENYLIST_MISSING,
                )

    def test_loader_fails_closed_on_absent_or_malformed_files(self):
        cases = {
            "absent": (None, cv.REFUSE_DENYLIST_MISSING),
            "empty": (b"", cv.REFUSE_DENYLIST_MALFORMED),
            "no trailing newline": (b"a", cv.REFUSE_DENYLIST_MALFORMED),
            "blank line": (b"a\n\nb\n", cv.REFUSE_DENYLIST_MALFORMED),
            "crlf": (b"a\r\nb\r\n", cv.REFUSE_DENYLIST_MALFORMED),
            "padded id": (b" a\n", cv.REFUSE_DENYLIST_MALFORMED),
            "duplicate id": (b"a\na\n", cv.REFUSE_DENYLIST_MALFORMED),
            "not utf-8": (b"\xff\xfe\n", cv.REFUSE_DENYLIST_MALFORMED),
            "control byte": (b"a\x00b\n", cv.REFUSE_DENYLIST_MALFORMED),
        }
        with tempfile.TemporaryDirectory() as tmp:
            for name, (payload, code) in cases.items():
                path = None
                if payload is not None:
                    path = Path(tmp) / f"{name}.txt"
                    path.write_bytes(payload)
                with self.subTest(name=name):
                    self.assertEqual(refused(denylist.load_denylist, path), code)
            absent, directory = Path(tmp) / "nope.txt", Path(tmp)
            self.assertEqual(refused(denylist.load_denylist, absent), cv.REFUSE_DENYLIST_MISSING)
            self.assertEqual(refused(denylist.load_denylist, directory), cv.REFUSE_DENYLIST_MALFORMED)

    def test_loader_returns_ids_and_the_file_digest(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "deny.txt"
            path.write_bytes(b"prog-eval\nother\n")
            loaded = denylist.load_denylist(path)
        self.assertEqual(loaded.program_ids, frozenset({"prog-eval", "other"}))
        self.assertEqual(loaded.sha256, hashlib.sha256(b"prog-eval\nother\n").hexdigest())

    def test_run_without_a_denylist_refuses_and_writes_nothing(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "out"
            request = runner.GateRequest(PROGRAMS, [proposal_for()], None, out)
            code = refused(runner.run, request, FakeHarness({ADD: PASSED}))
            self.assertEqual(code, cv.REFUSE_DENYLIST_MISSING)
            self.assertFalse(out.exists())
            self.assertEqual(list(Path(tmp).iterdir()), [])


class ParseErrors(unittest.TestCase):
    def assert_parse_error(self, item, detail):
        decision, fake = decide(item)
        self.assertEqual((decision.verdict, decision.detail), (cv.VERDICT_PARSE_ERROR, detail))
        self.assertEqual(fake.calls, [], "a proposal that does not apply must not execute anything")

    def test_unknown_program(self):
        self.assert_parse_error(proposal_for(program_id="nobody"), cv.DETAIL_UNKNOWN_PROGRAM)

    def test_span_outside_the_module(self):
        self.assert_parse_error(proposal_for(start_byte=10_000, end_byte=10_001), cv.DETAIL_SPAN_OUT_OF_RANGE)
        self.assert_parse_error(proposal_for(start_byte=5, end_byte=5), cv.DETAIL_SPAN_OUT_OF_RANGE)

    def test_span_text_must_match_the_named_bytes(self):
        self.assert_parse_error(proposal_for(original_text="a * b"), cv.DETAIL_SPAN_TEXT_MISMATCH)

    def test_text_only_form_needs_exactly_one_match(self):
        self.assert_parse_error(
            proposal_for(original_text="nothing here", start_byte=None, end_byte=None),
            cv.DETAIL_SPAN_NOT_FOUND,
        )
        self.assert_parse_error(
            proposal_for(original_text="a", start_byte=None, end_byte=None), cv.DETAIL_SPAN_AMBIGUOUS,
        )

    def test_text_only_form_resolves_to_the_same_edit_as_explicit_offsets(self):
        explicit, _ = decide(proposal_for())
        located, _ = decide(proposal_for(start_byte=None, end_byte=None))
        self.assertEqual(located.verdict, cv.VERDICT_KEPT)
        self.assertEqual(
            (located.start_byte, located.end_byte, located.dedup_key),
            (explicit.start_byte, explicit.end_byte, explicit.dedup_key),
        )

    def test_span_on_a_multibyte_boundary(self):
        text = 'def f():\n    """\n    >>> f()\n    1\n    """\n    return 1  # é\n'
        program = proposal.GateProgram("prog-u", text, "f")
        start, _ = span_of(text, "é")
        item = proposal_for(
            "2", "é", program, start_byte=start + 1, end_byte=start + 2, original_text=None,
        )
        decision, _ = decide(item, programs={"prog-u": program})
        self.assertEqual(decision.detail, cv.DETAIL_SPAN_NOT_ON_BOUNDARY)

    def test_span_in_the_docstring_or_outside_the_body(self):
        self.assert_parse_error(proposal_for("4", needle=">>> add(1, 2)\n    3"), cv.DETAIL_SPAN_TOUCHES_DOCSTRING)
        self.assert_parse_error(proposal_for("a, c", needle="a, b"), cv.DETAIL_SPAN_OUTSIDE_BODY)

    def test_mutant_that_does_not_compile(self):
        self.assert_parse_error(proposal_for("a +"), cv.DETAIL_MUTANT_SYNTAX_ERROR)
        self.assert_parse_error(proposal_for("a\x00"), cv.DETAIL_MUTANT_SYNTAX_ERROR)

    def test_replacement_that_dedents_into_module_scope_is_not_kept(self):
        """The span sits in the body, but what it becomes rewrites the doctests or the module."""

        escapes = {
            "doc rewrite": "return a\nadd.__doc__ = '>>> add(1, 2)\\n99\\n'",
            "redefinition": "return a\ndef add(a, b): return 2",
            "__test__": "return a\n__test__ = {'t': '>>> 1\\n2\\n'}",
            "extra statement": "return a\nOTHER = 1",
        }
        for name, replacement in escapes.items():
            with self.subTest(name=name):
                item = proposal_for(replacement, "return a + b")
                self.assert_parse_error(item, cv.DETAIL_MUTANT_ESCAPES_BODY)

    def test_replacement_that_rewrites_the_target_from_inside_is_not_kept(self):
        inside = {
            "attribute store": "add.__doc__ = 'x'\n    return a",
            "dunder test": "add.__test__ = {}\n    return a",
            "name rebinding": "global add\n    add = len\n    return a",
            "item store": "add.__dict__['k'] = 1\n    return a",
            "attribute delete": "del add.__doc__\n    return a",
        }
        for name, replacement in inside.items():
            with self.subTest(name=name):
                item = proposal_for(replacement, "return a + b")
                self.assert_parse_error(item, cv.DETAIL_MUTANT_ESCAPES_BODY)

    def test_ordinary_body_edits_still_pass_the_escape_check(self):
        for replacement in ("return a - b", "x = a\n    return x + b", "return add_one(a) + b"):
            with self.subTest(replacement=replacement):
                resolved = mutation.resolve(PROGRAM, proposal_for(replacement, "return a + b"))
                self.assertIsInstance(resolved, mutation.Resolved)

    def test_a_target_that_already_writes_to_itself_is_not_blamed_on_the_proposal(self):
        text = ADD.replace("return a + b", "add.calls = 1\n    return a + b")
        program = proposal.GateProgram("prog-self", text, "add")
        item = proposal_for("a - b", "a + b", program)
        self.assertIsInstance(mutation.resolve(program, item), mutation.Resolved)

    def test_malformed_rows_get_a_verdict_row_instead_of_aborting_the_batch(self):
        lines = [
            json.dumps({"program_id": "prog-add", "replacement_text": "a - b", "original_text": "a + b"}),
            "not json",
            json.dumps(["a list"]),
            json.dumps({"program_id": "prog-add", "replacement_text": "x", "start_byte": 1}),
            json.dumps({"program_id": "prog-add", "replacement_text": "x", "original_text": "a", "extra": 1}),
            json.dumps({"program_id": "prog-add", "replacement_text": 3, "original_text": "a"}),
            json.dumps({"program_id": "prog-add", "replacement_text": "x", "start_byte": True, "end_byte": 2}),
        ]
        parsed = proposal.parse_proposals(("\n".join(lines) + "\n").encode(), "mem")
        verdicts = [gate.Gate(PROGRAMS, rules(), FakeHarness({ADD: PASSED})).decide(p)
                    for p in parsed]
        self.assertEqual([v.verdict for v in verdicts], [cv.VERDICT_KEPT] + [cv.VERDICT_PARSE_ERROR] * 6)
        self.assertTrue(all(v.detail == cv.DETAIL_MALFORMED_ROW for v in verdicts[1:]))

    def test_proposal_file_framing_faults_refuse(self):
        for payload in (b'{"a":1}', b'{"a":1}\r\n', b'{"a":1}\n\n'):
            with self.subTest(payload=payload):
                code = refused(proposal.parse_proposals, payload, "mem")
                self.assertEqual(code, cv.REFUSE_PROPOSALS_INVALID)

    def test_unusable_programs_refuse_at_construction(self):
        for text in ("def other():\n    pass\n", "def add(:\n", ADD.replace("\n", "\r\n"), ADD + ADD):
            with self.subTest(text=text[:20]):
                code = refused(proposal.GateProgram, "p", text, "add")
                self.assertEqual(code, cv.REFUSE_PROGRAM_INVALID)
        self.assertEqual(
            refused(proposal.GateProgram, "p", NO_DOCTESTS, ""), cv.REFUSE_PROGRAM_INVALID,
        )

    def test_a_proposal_without_any_span_refuses_at_construction(self):
        for fields in ({}, {"original_text": ""}, {"start_byte": 1}, {"end_byte": 2}):
            with self.subTest(fields=fields):
                code = refused(lambda f=fields: proposal.GateProposal("p", "prog-add", "x", **f))
                self.assertEqual(code, cv.REFUSE_PROPOSALS_INVALID)


class Duplicates(unittest.TestCase):
    def test_key_is_sha256_over_program_span_and_replacement(self):
        key = dedup_index.dedup_key("prog-add", 1, 2, "x")
        self.assertEqual(len(key), 64)
        self.assertNotEqual(key, dedup_index.dedup_key("prog-add", 1, 2, "y"))
        self.assertNotEqual(key, dedup_index.dedup_key("prog-add", 1, 3, "x"))
        self.assertNotEqual(key, dedup_index.dedup_key("prog-eval", 1, 2, "x"))

    def test_second_identical_proposal_in_one_run_is_a_duplicate(self):
        machine = gate.Gate(PROGRAMS, rules(), FakeHarness({ADD: PASSED}))
        first, second = machine.run([proposal_for(), proposal_for(proposal_id="again")])
        self.assertEqual(first.verdict, cv.VERDICT_KEPT)
        self.assertEqual((second.verdict, second.detail), (cv.VERDICT_DUPLICATE, cv.DETAIL_THIS_RUN))

    def test_proposal_kept_in_a_prior_run_is_a_duplicate(self):
        with tempfile.TemporaryDirectory() as tmp:
            first = runner.run(
                runner.GateRequest(PROGRAMS, [proposal_for()], DENY, Path(tmp) / "run1"),
                FakeHarness({ADD: PASSED}),
            )
            self.assertEqual(first["verdicts"][cv.VERDICT_KEPT], 1)
            fake = FakeHarness({ADD: PASSED})
            second = runner.run(
                runner.GateRequest(
                    PROGRAMS, [proposal_for(), proposal_for("a * b")], DENY, Path(tmp) / "run2",
                    prior_index_paths=[Path(tmp) / "run1" / cv.INDEX_FILENAME],
                ),
                fake,
            )
            self.assertEqual(second["verdicts"][cv.VERDICT_DUPLICATE], 1)
            self.assertEqual(second["verdicts"][cv.VERDICT_KEPT], 1)
            self.assertEqual(second["details"]["duplicate"], {cv.DETAIL_PRIOR_RUN: 1})
            self.assertEqual(second["outputs"][cv.INDEX_FILENAME]["keys"], 2)
            self.assertEqual(second["outputs"][cv.INDEX_FILENAME]["new_keys"], 1)

    def test_different_replacement_or_span_is_not_a_duplicate(self):
        machine = gate.Gate(PROGRAMS, rules(), FakeHarness({ADD: PASSED}))
        verdicts = [d.verdict for d in machine.run([
            proposal_for("a - b"), proposal_for("a * b"), proposal_for("b", needle="a + b"),
        ])]
        self.assertEqual(verdicts, [cv.VERDICT_KEPT] * 3)

    def test_rejected_proposals_are_not_indexed(self):
        machine = gate.Gate(PROGRAMS, rules(), FakeHarness(default=PASSED))
        machine.run([proposal_for()])
        self.assertEqual(machine.kept, {})

    def test_prior_runs_files_are_read_only_inputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            runner.run(runner.GateRequest(PROGRAMS, [proposal_for()], DENY, Path(tmp) / "run1"),
                       FakeHarness({ADD: PASSED}))
            before = {p: p.read_bytes() for p in (Path(tmp) / "run1").iterdir()}
            runner.run(
                runner.GateRequest(PROGRAMS, [proposal_for("a * b")], DENY, Path(tmp) / "run2",
                                   prior_index_paths=[Path(tmp) / "run1" / cv.INDEX_FILENAME]),
                FakeHarness({ADD: PASSED}),
            )
            self.assertEqual({p: p.read_bytes() for p in (Path(tmp) / "run1").iterdir()}, before)

    def test_unreadable_or_malformed_prior_index_refuses_the_run(self):
        row = {"format": cv.INDEX_FORMAT, "key": "0" * 64, "program_id": "p", "start_byte": 1, "end_byte": 2}
        cases = {
            "missing": (None, cv.REFUSE_INDEX_UNREADABLE),
            "not json": (b"nope\n", cv.REFUSE_INDEX_MALFORMED),
            "extra field": (json.dumps({**row, "x": 1}).encode() + b"\n", cv.REFUSE_INDEX_MALFORMED),
            "short key": (json.dumps({**row, "key": "ab"}).encode() + b"\n", cv.REFUSE_INDEX_MALFORMED),
            "bad format": (json.dumps({**row, "format": "x"}).encode() + b"\n", cv.REFUSE_INDEX_MALFORMED),
            "repeated key": (((json.dumps(row) + "\n") * 2).encode(), cv.REFUSE_INDEX_MALFORMED),
            "no newline": (json.dumps(row).encode(), cv.REFUSE_INDEX_MALFORMED),
        }
        with tempfile.TemporaryDirectory() as tmp:
            for name, (payload, code) in cases.items():
                path = Path(tmp) / f"{name}.jsonl"
                if payload is not None:
                    path.write_bytes(payload)
                out = Path(tmp) / f"out-{name}"
                request = runner.GateRequest(
                    PROGRAMS, [proposal_for()], DENY, out, prior_index_paths=[path],
                )
                with self.subTest(name=name):
                    self.assertEqual(refused(runner.run, request, FakeHarness({ADD: PASSED})), code)
                    self.assertFalse(out.exists())


class Outputs(unittest.TestCase):
    def run_all(self, tmp, items, **overrides):
        request = runner.GateRequest(PROGRAMS, items, DENY, Path(tmp) / "out", **overrides)
        return runner.run(request, FakeHarness({ADD: PASSED}))

    def test_every_proposal_gets_one_row_and_counts_cover_all_verdicts(self):
        items = [
            proposal_for(), proposal_for(program_id="prog-eval"), proposal_for(program_id="ghost"),
            proposal_for(), proposal.MalformedProposal("bad", None, cv.DETAIL_MALFORMED_ROW),
        ]
        with tempfile.TemporaryDirectory() as tmp:
            summary = self.run_all(tmp, items)
            rows = [json.loads(line) for line in (Path(tmp) / "out" / cv.TASKS_FILENAME).read_text().splitlines()]
            on_disk = json.loads((Path(tmp) / "out" / cv.SUMMARY_FILENAME).read_text())
        self.assertEqual(summary, on_disk)
        self.assertEqual(
            [row["verdict"] for row in rows],
            [cv.VERDICT_KEPT, cv.VERDICT_DENYLISTED, cv.VERDICT_PARSE_ERROR, cv.VERDICT_DUPLICATE, cv.VERDICT_PARSE_ERROR],
        )
        self.assertEqual(set(summary["verdicts"]), set(cv.VERDICTS))
        self.assertEqual(sum(summary["verdicts"].values()), summary["total"])
        self.assertEqual(summary["total"], 5)
        self.assertEqual(summary["survival_rate"], "0.200000")
        self.assertEqual(summary["by_source"]["model"]["kept"], 1)
        self.assertEqual(summary["inputs"]["denylist"]["sha256"], DENY.sha256)

    def test_destination_must_be_new_and_outside_the_raw_tree(self):
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "out").mkdir()
            existing = runner.GateRequest(PROGRAMS, [proposal_for()], DENY, Path(tmp) / "out")
            fake = FakeHarness({ADD: PASSED})
            self.assertEqual(refused(runner.run, existing, fake), cv.REFUSE_DESTINATION_EXISTS)
            raw = Path(tmp) / "outputs" / "raw" / "x"
            raw.parent.mkdir(parents=True)
            under_raw = runner.GateRequest(PROGRAMS, [proposal_for()], DENY, raw)
            self.assertEqual(refused(runner.run, under_raw, fake), cv.REFUSE_DESTINATION_UNDER_RAW)
            self.assertEqual(list(raw.parent.iterdir()), [])

    def test_no_proposals_refuses(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(refused(self.run_all, tmp, []), cv.REFUSE_NO_PROPOSALS)

    def test_a_failing_self_check_refuses_before_any_proposal_runs(self):
        class Broken(FakeHarness):
            def selfcheck(self):
                raise cv.GateRefusal(cv.REFUSE_HARNESS_UNAVAILABLE, "broken")

        with tempfile.TemporaryDirectory() as tmp:
            request = runner.GateRequest(PROGRAMS, [proposal_for()], DENY, Path(tmp) / "out")
            self.assertEqual(refused(runner.run, request, Broken()), cv.REFUSE_HARNESS_UNAVAILABLE)

    def test_resolution_is_pure(self):
        resolved = mutation.resolve(PROGRAM, proposal_for())
        self.assertEqual(resolved.original_text, "a + b")
        self.assertEqual(resolved.mutant_text, ADD.replace("a + b", "a - b"))
        self.assertIsNone(report.check_destination(Path(tempfile.gettempdir()) / "task-gate-never-created-xyz"))


if __name__ == "__main__":
    unittest.main()
