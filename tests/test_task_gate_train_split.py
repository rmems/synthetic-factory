"""Procedural draws stay on the train split; verify denies catalog eval programs."""

import sys
import unittest
from dataclasses import replace
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from task_gate_test_support import REPO, cv, decide, proposal_for, rules
from task_gate import procedural


class ProceduralTrainSplit(unittest.TestCase):
    FIXTURE = REPO / "tests" / "fixtures" / "code-repair"
    PINNED = REPO / "catalogs" / "python-repair-v1"

    def test_procedural_draws_omit_validation_and_held_out(self):
        catalog = procedural.load_catalog(self.FIXTURE)
        eval_ids = {
            program.program_id for program in catalog.programs
            if program.split in procedural.EVAL_SPLITS
        }
        non_train = {
            program.program_id for program in catalog.programs if program.split != "train"
        }
        self.assertEqual(non_train, eval_ids)
        self.assertTrue(eval_ids, "fixture must include validation and held-out programs")
        proposals = procedural.proposals_from_plan(catalog, seed=7, count=400)
        self.assertTrue(proposals, "expected at least one procedural proposal")
        self.assertFalse({item.program_id for item in proposals} & eval_ids)

    def test_a_catalog_with_no_split_policy_still_draws(self):
        catalog = procedural.load_catalog(self.FIXTURE)
        cleared = replace(
            catalog,
            programs=tuple(replace(program, split=None) for program in catalog.programs),
        )
        self.assertEqual(procedural.eval_program_ids(cleared), frozenset())
        proposals = procedural.proposals_from_plan(cleared, seed=7, count=4)
        self.assertTrue(proposals, "null-split programs stay eligible")

    def test_verify_denies_catalog_validation_and_held_out_ids(self):
        catalog = procedural.load_catalog(self.FIXTURE)
        eval_ids = procedural.eval_program_ids(catalog)
        splits = {program.split: program.program_id for program in catalog.programs
                  if program.split in procedural.EVAL_SPLITS}
        self.assertEqual(set(splits), {"validation", "held_out"})
        self.assertEqual(eval_ids, set(splits.values()))
        gate_rules = rules(eval_program_ids=eval_ids)
        for split, program_id in splits.items():
            with self.subTest(split=split):
                decision, fake = decide(proposal_for(program_id=program_id), rule_set=gate_rules)
                self.assertEqual(decision.verdict, cv.VERDICT_DENYLISTED)
                self.assertEqual(fake.calls, [])

    def test_pinned_catalog_eval_splits_are_sixteen_validation_and_nineteen_held_out(self):
        catalog = procedural.load_catalog(self.PINNED)
        by_split = {"validation": set(), "held_out": set()}
        for program in catalog.programs:
            if program.split in by_split:
                by_split[program.split].add(program.program_id)
        self.assertEqual(len(by_split["validation"]), 16)
        self.assertEqual(len(by_split["held_out"]), 19)
        self.assertEqual(
            procedural.eval_program_ids(catalog), by_split["validation"] | by_split["held_out"],
        )


if __name__ == "__main__":
    unittest.main()
