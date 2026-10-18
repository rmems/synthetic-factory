#!/usr/bin/env python3
"""The execution-gate fields of a factory's marker-mode file fail closed by name."""

import json
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "pipelines"))

import round_txn  # noqa: E402

CUTOVER = "execution_verified_from_round"
ROUNDS = "execution_verified_rounds"


class ExecutionPolicyFields(unittest.TestCase):
    def setUp(self):
        workspace = tempfile.TemporaryDirectory()
        self.addCleanup(workspace.cleanup)
        self.factory = Path(workspace.name) / "factory"
        self.factory.mkdir()
        self.mode_path = self.factory / round_txn.MODE_FILE

    def write_mode(self, fields):
        self.mode_path.write_text(json.dumps(fields) + "\n", encoding="utf-8")

    def test_field_constants_name_the_marker_mode_json_keys(self):
        self.assertEqual(round_txn.EXECUTION_CUTOVER_FIELD, CUTOVER)
        self.assertEqual(round_txn.EXECUTION_VERIFIED_ROUNDS_FIELD, ROUNDS)

    def test_malformed_verified_rounds_are_refused_by_field_name(self):
        cases = {
            "not a list": {CUTOVER: 5, ROUNDS: "1"},
            "not a positive round": {CUTOVER: 5, ROUNDS: [0]},
            "out of order": {CUTOVER: 5, ROUNDS: [2, 1]},
            "bound without a cutover": {ROUNDS: [1]},
            "at or after the cutover": {CUTOVER: 3, ROUNDS: [3]},
        }
        for label, fields in cases.items():
            with self.subTest(label):
                self.write_mode(fields)
                with self.assertRaisesRegex(round_txn.TransactionError, f"invalid {ROUNDS} in "):
                    round_txn.execution_gate_policy(self.factory)

    def test_a_non_positive_cutover_is_refused_when_read_and_when_extended(self):
        self.write_mode({CUTOVER: 0})
        before = self.mode_path.read_bytes()
        with self.assertRaisesRegex(round_txn.TransactionError, f"invalid {CUTOVER} in "):
            round_txn.execution_gate_policy(self.factory)
        with self.assertRaisesRegex(round_txn.TransactionError, f"invalid {CUTOVER} in "):
            round_txn.remember_execution_gate_cutover(self.factory, 2)
        self.assertEqual(self.mode_path.read_bytes(), before)

    def test_an_earlier_round_is_bound_below_the_existing_cutover(self):
        self.write_mode({CUTOVER: 5, ROUNDS: [1]})
        round_txn.remember_execution_gate_cutover(self.factory, 3)
        self.assertEqual(
            json.loads(self.mode_path.read_text(encoding="utf-8")), {CUTOVER: 5, ROUNDS: [1, 3]}
        )
        self.assertEqual(round_txn.execution_gate_policy(self.factory), (5, frozenset({1, 3})))
        before = self.mode_path.read_bytes()
        for already_covered in (3, 5, 6):
            round_txn.remember_execution_gate_cutover(self.factory, already_covered)
        self.assertEqual(self.mode_path.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
