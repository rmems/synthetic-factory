"""Regression: task_gate must not keep duplicate, denylisted-copy, equivalent or self-labelled mutants.

On main, dedup compares the raw edit (``dedup_index.minimal_edit`` / ``dedup_key``), the denylist
matches program ids only, any doctest failure counts as a bug, and ``source`` is copied from the
proposal. The copy below is the denylisted program's own text under a new id.
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from task_gate_test_support import (  # noqa: E402
    EVAL_PROGRAM, PROGRAMS, gate, proposal, proposal_for, rules,
)
from task_gate import harness as H  # noqa: E402

HARNESS = H.SubprocessHarness()


def decide(props, programs=None):
    machine = gate.Gate(PROGRAMS if programs is None else programs, rules(), HARNESS)
    return [machine.decide(item) for item in props]


class TaskGateForges(unittest.TestCase):
    def test_control_real_mutant_kept(self):
        (decision,) = decide([proposal_for()])
        self.assertEqual(decision.verdict, "kept")

    def test_forge_spelling_variants_are_duplicates(self):
        for variant in ("a  -  b", "(a - b)"):
            with self.subTest(variant=variant):
                first, second = decide([proposal_for(), proposal_for(variant)])
                self.assertEqual(first.verdict, "kept")
                self.assertNotEqual(
                    second.verdict, "kept",
                    f"{variant!r} kept as a new task (same mutant as a - b)",
                )

    def test_forge_denylisted_eval_text_under_new_id(self):
        copy = proposal.GateProgram("prog-eval-copy", EVAL_PROGRAM.text, EVAL_PROGRAM.function)
        (decision,) = decide(
            [proposal_for(program=copy)], {**PROGRAMS, "prog-eval-copy": copy},
        )
        self.assertNotEqual(
            decision.verdict, "kept", "denylisted eval program text kept under a new id",
        )

    def test_forge_equivalent_mutant_stdout_noise(self):
        (decision,) = decide([proposal_for("print('x') or a + b")])
        self.assertNotEqual(
            decision.verdict, "kept", "equivalent mutant kept because of stdout noise",
        )

    def test_forge_self_declared_source_copied(self):
        (decision,) = decide([proposal_for(source="procedural-oracle-verified")])
        self.assertNotEqual(
            decision.source, "procedural-oracle-verified",
            "self-declared verified source copied into the decision unchecked",
        )

    def test_forge_json_row_cannot_claim_procedural(self):
        row = proposal.proposal_from_row(
            {"proposal_id": "p-row", "program_id": "prog-add", "replacement_text": "a - b",
             "original_text": "a + b", "source": "procedural"},
            "fallback",
        )
        self.assertEqual(row.source, "unspecified")
        (decision,) = decide([row])
        self.assertEqual(decision.source, "unspecified")
        self.assertEqual(decision.verdict, "kept")

    def test_forge_long_binop_chain_is_judged(self):
        wide = " + ".join(["a"] * 700) + " - b"
        tight = "+".join(["a"] * 700) + "-b"
        first, second = decide([proposal_for(wide), proposal_for(tight, proposal_id="p-tight")])
        self.assertEqual(first.verdict, "kept")
        self.assertEqual(second.verdict, "duplicate")

    def test_forge_printed_off_by_one_is_kept(self):
        text = (
            "def count(n):\n"
            '    """\n'
            "    >>> count(2)\n"
            "    1\n"
            "    2\n"
            '    """\n'
            "    for i in range(1, n + 1):\n"
            "        print(i)\n"
        )
        program = proposal.GateProgram("prog-count", text, "count")
        (decision,) = decide(
            [proposal_for("range(0, n + 1)", "range(1, n + 1)", program)],
            {"prog-count": program, **PROGRAMS},
        )
        self.assertEqual(decision.verdict, "kept")


if __name__ == "__main__":
    unittest.main()
