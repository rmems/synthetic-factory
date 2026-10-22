"""The difficulty-band stage (#497): contract, band edges, recorded attempts, seed_needed."""

import json
import sys
import tempfile
import unittest
from fractions import Fraction
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from band_test_support import (
    ADD, PROGRAMS, STUDENT_PASSES, ScriptedSolver, band_run, bv, contract_document,
    cv, gate_tasks, read_rows, run_band, write_contract,
)
from task_gate import band_contract
from task_gate_test_support import refused


class TempRoot(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)


class BandEdges(TempRoot):
    """Five kept tasks scored 0, 1, 5, 9 and 10 of 10 attempts under the 0.1-0.9 band."""

    def test_each_edge_gets_its_band_verdict(self):
        summary, out, _ = run_band(self.root, {0: 0, 1: 1, 2: 5, 3: 9, 4: 10})
        bands = [row["band"] for row in read_rows(out / bv.ROWS_FILENAME)]
        self.assertEqual(bands, [
            bv.BAND_SEED_NEEDED, bv.BAND_KEPT, bv.BAND_KEPT, bv.BAND_KEPT, bv.BAND_TOO_EASY,
        ])
        self.assertEqual(summary["bands"], {
            bv.BAND_KEPT: 3, bv.BAND_TOO_EASY: 1, bv.BAND_TOO_HARD: 0, bv.BAND_SEED_NEEDED: 1,
        })

    def test_lower_edge_is_inclusive_and_just_below_is_too_hard(self):
        # 20 attempts: 1/20 = 0.05 is below 0.1, 2/20 sits exactly on the 0.1 bound.
        _, out, _ = run_band(self.root, {0: 1, 1: 2}, attempts=20)
        bands = [row["band"] for row in read_rows(out / bv.ROWS_FILENAME)][:2]
        self.assertEqual(bands, [bv.BAND_TOO_HARD, bv.BAND_KEPT])

    def test_upper_edge_is_inclusive_and_just_above_is_too_easy(self):
        _, out, _ = run_band(self.root, {0: 18, 1: 19}, attempts=20)
        bands = [row["band"] for row in read_rows(out / bv.ROWS_FILENAME)][:2]
        self.assertEqual(bands, [bv.BAND_KEPT, bv.BAND_TOO_EASY])

    def test_bounds_come_from_the_contract_not_from_the_code(self):
        _, out, _ = run_band(self.root, {0: 7, 1: 8}, low=0.7, high=0.7)
        bands = [row["band"] for row in read_rows(out / bv.ROWS_FILENAME)][:2]
        self.assertEqual(bands, [bv.BAND_KEPT, bv.BAND_TOO_EASY])

    def test_kept_file_holds_exactly_the_in_band_rows(self):
        _, out, _ = run_band(self.root, {0: 0, 1: 1, 2: 5, 3: 9, 4: 10})
        kept = read_rows(out / bv.KEPT_FILENAME)
        self.assertEqual([row["successes"] for row in kept], [1, 5, 9])


class AttemptsRecorded(TempRoot):
    def test_every_row_records_attempts_successes_and_pass_rate(self):
        _, out, solver = run_band(self.root, {0: 0, 1: 1, 2: 5, 3: 9, 4: 10})
        rows = read_rows(out / bv.ROWS_FILENAME)
        self.assertEqual([(r["attempts"], r["successes"], r["pass_rate"]) for r in rows], [
            (10, 0, 0.0), (10, 1, 0.1), (10, 5, 0.5), (10, 9, 0.9), (10, 10, 1.0),
        ])
        self.assertTrue(all(row["generator"] == "self" for row in rows))
        self.assertEqual(len(solver.calls), 50)

    def test_attempts_per_task_follows_the_contract(self):
        _, out, solver = run_band(self.root, {0: 2}, attempts=4)
        self.assertEqual({row["attempts"] for row in read_rows(out / bv.ROWS_FILENAME)}, {4})
        self.assertEqual(len(solver.calls), 20)
        self.assertEqual(sorted({a for _, a in solver.calls}), [0, 1, 2, 3])


class SeedNeeded(TempRoot):
    def test_zero_pass_tasks_are_written_not_discarded(self):
        _, out, _ = run_band(self.root, {1: 5})
        seeds = read_rows(out / bv.SEED_NEEDED_FILENAME)
        self.assertEqual(len(seeds), 4)
        self.assertTrue(all(row["successes"] == 0 and row["pass_rate"] == 0.0 for row in seeds))
        self.assertTrue(all(row["band"] == bv.BAND_SEED_NEEDED for row in seeds))
        self.assertEqual(len(read_rows(out / bv.ROWS_FILENAME)), 5)

    def test_an_empty_seed_file_is_still_written(self):
        _, out, _ = run_band(self.root, {i: 5 for i in range(5)})
        self.assertEqual((out / bv.SEED_NEEDED_FILENAME).read_bytes(), b"")


class Histogram(TempRoot):
    def test_summary_histogram_covers_every_success_count(self):
        summary, _, _ = run_band(self.root, {0: 0, 1: 1, 2: 5, 3: 5, 4: 10})
        hist = summary["histogram"]
        self.assertEqual([h["successes"] for h in hist], list(range(11)))
        self.assertEqual({h["successes"]: h["count"] for h in hist if h["count"]}, {0: 1, 1: 1, 5: 2, 10: 1})
        self.assertEqual(hist[1]["band"], bv.BAND_KEPT)
        self.assertEqual(hist[0]["band"], bv.BAND_SEED_NEEDED)
        self.assertEqual(sum(h["count"] for h in hist), summary["total"])

    def test_summary_records_contract_digest_and_input_digest(self):
        summary, out, _ = run_band(self.root, {})
        self.assertEqual(summary["contract"]["attempts_per_task"], 10)
        self.assertEqual(len(summary["contract"]["sha256"]), 64)
        self.assertEqual(len(summary["inputs"]["tasks"]["sha256"]), 64)
        self.assertEqual(summary["outputs"][bv.ROWS_FILENAME]["rows"], 5)
        self.assertTrue((out / bv.SUMMARY_FILENAME).is_file())

    def test_non_kept_gate_rows_are_skipped_and_counted(self):
        from task_gate_test_support import proposal_for

        tasks = gate_tasks(self.root, extra=[proposal_for("a + b")])
        solver = ScriptedSolver({}, default=5)
        request = band_run.BandRequest(
            PROGRAMS, tasks, write_contract(self.root), self.root / "band", "self",
        )
        summary = band_run.run(request, solver, STUDENT_PASSES)
        self.assertEqual((summary["total"], summary["inputs"]["tasks"]["skipped_not_kept"]), (5, 1))


class FailClosed(TempRoot):
    def request(self, tasks=None, contract="default", programs=None):
        programs = PROGRAMS if programs is None else programs
        tasks = tasks or gate_tasks(self.root)
        if contract == "default":
            contract = write_contract(self.root)
        return band_run.BandRequest(programs, tasks, contract, self.root / "band", "self")

    def attempt(self, request, solver=None):
        solver = solver or ScriptedSolver({})
        return refused(band_run.run, request, solver, STUDENT_PASSES), solver

    def test_missing_contract_refuses_before_the_solver_runs(self):
        code, solver = self.attempt(self.request(contract=None))
        self.assertEqual(code, bv.REFUSE_CONTRACT_MISSING)
        self.assertEqual(solver.calls, [])
        self.assertFalse((self.root / "band").exists())

    def test_unreadable_contract_path_refuses(self):
        code, _ = self.attempt(self.request(contract=self.root / "absent.json"))
        self.assertEqual(code, bv.REFUSE_CONTRACT_MISSING)

    def test_program_drift_refuses_before_any_attempt(self):
        drifted = dict(PROGRAMS)
        drifted["prog-add"] = type(PROGRAMS["prog-add"])("prog-add", ADD + "\n\n", "add")
        code, solver = self.attempt(self.request(programs=drifted))
        self.assertEqual(code, bv.REFUSE_TASK_PROGRAM_MISMATCH)
        self.assertEqual(solver.calls, [])

    def test_unknown_program_refuses(self):
        code, _ = self.attempt(self.request(programs={"prog-eval": PROGRAMS["prog-eval"]}))
        self.assertEqual(code, bv.REFUSE_TASK_PROGRAM_MISMATCH)

    def test_existing_destination_refuses(self):
        (self.root / "band").mkdir()
        code, solver = self.attempt(self.request())
        self.assertEqual(code, cv.REFUSE_DESTINATION_EXISTS)
        self.assertEqual(solver.calls, [])

    def test_no_kept_task_refuses(self):
        tasks = self.root / "tasks.jsonl"
        tasks.write_bytes(b"")
        code, _ = self.attempt(self.request(tasks=tasks))
        self.assertEqual(code, bv.REFUSE_NO_TASKS)

    def test_malformed_tasks_file_refuses(self):
        tasks = self.root / "tasks.jsonl"
        tasks.write_text('{"format": "x"}\n')
        code, _ = self.attempt(self.request(tasks=tasks))
        self.assertEqual(code, bv.REFUSE_TASKS_INVALID)

    def test_unnamed_generator_refuses(self):
        request = self.request()
        request = band_run.BandRequest(request.programs, request.tasks_path, request.contract, request.out, "")
        self.assertEqual(self.attempt(request)[0], bv.REFUSE_REQUEST_INVALID)

    def test_a_crashing_solver_stops_the_run_and_writes_nothing(self):
        class Crashing:
            def solve(self, task, attempt):
                raise RuntimeError("student fell over")

        code = refused(band_run.run, self.request(), Crashing(), STUDENT_PASSES)
        self.assertEqual(code, bv.REFUSE_SOLVER_FAILED)
        self.assertFalse((self.root / "band").exists())
        self.assertEqual([p.name for p in self.root.glob(".band-stage-*")], [])


class ScoringIsTheHarnessNotTheSolver(TempRoot):
    def test_candidates_that_edit_the_doctests_or_are_not_text_do_not_pass(self):
        edited = ADD.replace(">>> add(1, 2)\n    3", ">>> add(1, 2)\n    -1").replace("a + b", "a - b")
        from task_gate_test_support import FakeHarness, PASSED

        class Cheater(ScriptedSolver):
            def solve(self, task, attempt):
                return (edited, None, "def (:", ADD)[attempt % 4]

        tasks = gate_tasks(self.root)
        request = band_run.BandRequest(
            PROGRAMS, tasks, write_contract(self.root, attempts=4), self.root / "band", "self",
        )
        harness = FakeHarness({edited: PASSED, ADD: PASSED})
        summary = band_run.run(request, Cheater({}), harness)
        self.assertEqual([h["count"] for h in summary["histogram"]], [0, 5, 0, 0, 0])


class ContractTests(TempRoot):
    def load(self, **fields):
        path = write_contract(self.root, name="c.json", **fields)
        return band_contract.load_contract(path)

    def test_valid_contract_round_trips(self):
        contract = self.load()
        self.assertEqual((contract.attempts_per_task, float(contract.pass_rate_min)), (10, 0.1))
        self.assertEqual(float(contract.pass_rate_max), 0.9)

    def test_classify_is_exact_on_both_edges(self):
        contract = self.load(attempts=10)
        self.assertEqual(contract.classify(1, 10), bv.BAND_KEPT)
        self.assertEqual(contract.classify(9, 10), bv.BAND_KEPT)
        self.assertEqual(contract.classify(0, 10), bv.BAND_SEED_NEEDED)
        self.assertEqual(contract.classify(10, 10), bv.BAND_TOO_EASY)
        self.assertEqual(contract.classify(1, 20), bv.BAND_TOO_HARD)
        self.assertEqual(contract.classify(19, 20), bv.BAND_TOO_EASY)

    def test_bounds_keep_the_decimal_token_not_its_nearest_double(self):
        # json.dumps cannot write this token (it is the double 0.1), so write the bytes directly.
        document = contract_document()
        key = '"pass_rate_min": ' + json.dumps(document["pass_rate_min"])
        text = json.dumps(document)
        self.assertEqual(text.count(key), 1)
        text = text.replace(key, '"pass_rate_min": 0.10000000000000001')
        path = Path(self.root) / "exact.json"
        path.write_text(text, encoding="utf-8")
        contract = band_contract.load_contract(path)
        self.assertGreater(contract.pass_rate_min, Fraction(1, 10))
        self.assertEqual(contract.classify(2, 20), bv.BAND_TOO_HARD)
        summary, _, _ = run_band(self.root, {0: 2}, contract=path)
        self.assertEqual(summary["contract"]["pass_rate_min"], "10000000000000001/100000000000000000")

    def test_each_malformed_contract_is_refused(self):
        bad = [
            {"attempts": 1}, {"attempts": 65}, {"attempts": True}, {"attempts": 2.0},
            {"low": 0}, {"low": 0.0}, {"high": 1}, {"high": 1.0}, {"low": 0.95},
            {"low": True}, {"low": "0.1"}, {"low": -0.1},
        ]
        for fields in bad:
            with self.subTest(fields=fields):
                path = write_contract(self.root, name="bad.json", **fields)
                self.assertEqual(refused(band_contract.load_contract, path), bv.REFUSE_CONTRACT_MALFORMED)

    def test_unknown_missing_wrong_format_and_junk_are_refused(self):
        document = contract_document()
        cases = {
            "extra": {**document, "keep": 1}, "missing": {k: v for k, v in document.items() if k != "format"},
            "format": {**document, "format": "other/1"},
        }
        import json

        for name, content in cases.items():
            path = self.root / f"{name}.json"
            path.write_text(json.dumps(content))
            with self.subTest(name=name):
                self.assertEqual(refused(band_contract.load_contract, path), bv.REFUSE_CONTRACT_MALFORMED)
        junk = self.root / "junk.json"
        junk.write_bytes(b"\xff{")
        dup = self.root / "dup.json"
        dup.write_text('{"format": "a", "format": "b"}')
        for path in (junk, dup):
            self.assertEqual(refused(band_contract.load_contract, path), bv.REFUSE_CONTRACT_MALFORMED)

    def test_directory_and_oversized_contract_are_refused(self):
        self.assertEqual(refused(band_contract.load_contract, self.root), bv.REFUSE_CONTRACT_MISSING)
        big = self.root / "big.json"
        big.write_bytes(b" " * (bv.MAX_CONTRACT_BYTES + 1))
        self.assertEqual(refused(band_contract.load_contract, big), bv.REFUSE_CONTRACT_MALFORMED)


RATE = "pass_rate"  # a name, so a row literal is not read as a hardcoded credential


class SelfRowProvenance(unittest.TestCase):
    def good(self, **fields):
        return {"proposal_id": "p", "generator": "self", "attempts": 4, "successes": 1,
                RATE: 0.25, **fields}

    def test_a_sound_self_row_passes_and_other_generators_are_not_held_to_it(self):
        from task_gate import band_provenance

        self.assertIsNone(band_provenance.problem_with(self.good()))
        self.assertIsNone(band_provenance.problem_with({"generator": "teacher"}))
        band_provenance.check_row(self.good())

    def test_each_missing_or_inconsistent_field_is_refused(self):
        from task_gate import band_provenance

        bad = [
            {"attempts": None}, {"attempts": 0}, {"attempts": True}, {"successes": 5},
            {"successes": -1}, {"successes": "1"}, {RATE: None}, {RATE: 0.5},
            {RATE: True},
        ]
        for fields in bad:
            with self.subTest(fields=fields):
                self.assertEqual(
                    refused(band_provenance.check_row, self.good(**fields)), bv.REFUSE_ROW_PROVENANCE,
                )

    def test_the_rate_is_the_float_division_of_the_counts(self):
        from task_gate import band_provenance

        third = self.good(attempts=3, successes=1, **{RATE: 1 / 3})
        self.assertIsNone(band_provenance.problem_with(third))
        self.assertIsNotNone(band_provenance.problem_with({**third, RATE: 0.3333}))
        self.assertIsNotNone(band_provenance.problem_with({**third, RATE: 1 / 3 + 1e-12}))

    def test_absent_fields_are_refused(self):
        from task_gate import band_provenance

        for key in ("attempts", "successes", "pass_rate"):
            row = self.good()
            del row[key]
            self.assertEqual(refused(band_provenance.check_row, row), bv.REFUSE_ROW_PROVENANCE)


if __name__ == "__main__":
    unittest.main()
