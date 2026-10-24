"""The band stage through the real subprocess harness, and both import spellings."""

import importlib
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from band_test_support import (
    DENY, PROGRAMS, ScriptedSolver, band_run, bv, cv, proposal_for, read_rows, runner,
    write_contract,
)
from task_gate import harness as gate_harness


class RealHarnessEndToEnd(unittest.TestCase):
    def test_real_gate_then_real_band_with_a_deterministic_solver(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            real = gate_harness.SubprocessHarness(10)
            proposals = [proposal_for("a - b"), proposal_for("a * b")]
            runner.run(runner.GateRequest(PROGRAMS, proposals, DENY, root / "gate"), real)
            tasks = root / "gate" / cv.TASKS_FILENAME
            first, second = [row["proposal_id"] for row in read_rows(tasks)]
            solver = ScriptedSolver({first: 1, second: 0})
            request = band_run.BandRequest(
                PROGRAMS, tasks, write_contract(root, attempts=2, low=0.5, high=0.5),
                root / "band", "self",
            )
            summary = band_run.run(request, solver, real)
            rows = read_rows(root / "band" / bv.ROWS_FILENAME)
            self.assertEqual([(r["successes"], r["band"]) for r in rows], [
                (1, bv.BAND_KEPT), (0, bv.BAND_SEED_NEEDED),
            ])
            self.assertEqual(summary["bands"][bv.BAND_KEPT], 1)


class ImportSpellings(unittest.TestCase):
    def test_package_and_flat_spellings_are_one_object(self):
        flat = importlib.import_module("task_gate.band_run")
        package = importlib.import_module("pipelines.task_gate.band_run")
        self.assertIs(flat.run, package.run)


if __name__ == "__main__":
    unittest.main()
