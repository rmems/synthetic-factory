"""Defensive paths of the band stage: bad tasks files, cleanup, injected contract, odd candidates."""

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))

from band_test_support import (
    ADD, PROGRAMS, STUDENT_PASSES, ScriptedSolver, band_run, bv, cv, gate_tasks, read_rows,
    write_contract,
)
from task_gate import band_contract, band_report, band_solver, band_tasks
from task_gate_test_support import PROGRAM, FakeHarness, refused


class TasksFile(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.tasks = gate_tasks(self.root)

    def code(self, path):
        return refused(band_tasks.load_kept, path)

    def test_unreadable_directory_and_oversized_files_are_refused(self):
        self.assertEqual(self.code(self.root / "absent.jsonl"), bv.REFUSE_TASKS_INVALID)
        self.assertEqual(self.code(self.root), bv.REFUSE_TASKS_INVALID)
        with mock.patch.object(bv, "MAX_TASKS_BYTES", 10):
            self.assertEqual(self.code(self.tasks), bv.REFUSE_TASKS_INVALID)

    def test_unframed_and_unknown_rows_are_refused(self):
        bad = self.root / "bad.jsonl"
        bad.write_bytes(b'{"format": "task-gate-tasks/1"')
        self.assertEqual(self.code(bad), bv.REFUSE_TASKS_INVALID)
        row = read_rows(self.tasks)[0]
        for fields in ({"verdict": "maybe"}, {"proposal_id": ""}, {"start_byte": -1}, {"program_id": 3}):
            bad.write_text(json.dumps({**row, **fields}) + "\n")
            with self.subTest(fields=fields):
                self.assertEqual(self.code(bad), bv.REFUSE_TASKS_INVALID)

    def test_a_repeated_proposal_id_is_refused(self):
        row = json.dumps(read_rows(self.tasks)[0]) + "\n"
        bad = self.root / "bad.jsonl"
        bad.write_text(row + row)
        self.assertEqual(self.code(bad), bv.REFUSE_TASKS_INVALID)

    def test_a_mutant_that_no_longer_rebuilds_is_refused(self):
        loaded = band_tasks.load_kept(self.tasks)
        row = band_tasks.KeptTask({**loaded.kept[0], "mutant_sha256": "0" * 64})
        self.assertEqual(refused(band_tasks.rebuild, row, PROGRAMS), bv.REFUSE_TASK_PROGRAM_MISMATCH)


class RunCleanup(unittest.TestCase):
    def test_a_failed_publish_leaves_no_stage_and_no_destination(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            tasks = gate_tasks(root)
            contract = band_contract.load_contract(write_contract(root))
            request = band_run.BandRequest(PROGRAMS, tasks, contract, root / "band", "self")
            with mock.patch.object(band_report, "publish", side_effect=cv.GateRefusal("X", "boom")):
                code = refused(band_run.run, request, ScriptedSolver({}), STUDENT_PASSES)
            self.assertEqual(code, "X")
            self.assertEqual(sorted(p.name for p in root.iterdir()), ["contract.json", "gate"])


class OddCandidates(unittest.TestCase):
    def test_candidates_that_do_not_parse_as_modules_fail_without_raising(self):
        scorer = band_solver.Scorer(PROGRAM, FakeHarness())
        for candidate in ("def (:", "\x00", ADD.replace("\n", "\r\n"), b"bytes", 3):
            with self.subTest(candidate=candidate):
                self.assertFalse(scorer.passes(candidate))

    def test_a_candidate_that_parses_but_drops_the_target_fails(self):
        self.assertFalse(band_solver.Scorer(PROGRAM, FakeHarness()).passes("x = 1\n"))

    def test_a_legality_check_that_raises_fails_the_attempt_without_running_it(self):
        fake = FakeHarness()
        scorer = band_solver.Scorer(PROGRAM, fake)
        for error in (SyntaxError("bad"), ValueError("bad"), RecursionError("deep")):
            with self.subTest(error=type(error).__name__):
                with mock.patch.object(band_solver.mutation, "candidate_problem", side_effect=error):
                    self.assertFalse(scorer.passes(ADD))
        self.assertEqual(fake.calls, [])


if __name__ == "__main__":
    unittest.main()
