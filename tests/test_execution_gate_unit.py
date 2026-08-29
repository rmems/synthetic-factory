#!/usr/bin/env python3
"""Cohesive frontier execution-gate regression suite."""

import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tests.frontier_gate_helpers import (
    FrontierGateTestCaseMixin,
    round_txn,
    thalamic,
    write,
)


class ExecutionGateUnit(FrontierGateTestCaseMixin, unittest.TestCase):
    def test_failed_record_is_never_waivable(self):
        with tempfile.TemporaryDirectory() as td:
            batch = Path(td) / "batch-r01.jsonl"
            write(batch, [thalamic("gate-failed", rationale="")])

            with self.assertRaises(round_txn.TransactionError) as raised:
                round_txn.execution_gate(
                    batch, batch, override="operator accepts this batch"
                )

            self.assertIn("never waivable", str(raised.exception))


    def test_execution_gate_returns_the_canonical_summary_when_unblocked(self):
        with tempfile.TemporaryDirectory() as td:
            batch = Path(td) / "batch-r01.jsonl"
            write(batch, [thalamic("gate-summary")])

            summary = round_txn.execution_gate(batch, batch)

        self.assertEqual(summary["gate"], round_txn.EXECUTION_GATE_LABEL)
        self.assertTrue(summary["strict"])
        self.assertEqual(
            summary["semantics_version"],
            round_txn.EXECUTION_VERIFIER_SEMANTICS_VERSION,
        )
        self.assertEqual(
            summary["counts"],
            {"failed": 0, "inconclusive": 0, "total": 1, "verified": 1},
        )
        self.assertIsNone(summary["override"])


    def test_execution_gate_blocks_unwaived_inconclusive(self):
        with tempfile.TemporaryDirectory() as td:
            batch = Path(td) / "batch-r01.jsonl"
            write(batch, [thalamic("gate-unwaived", observable=False)])

            with self.assertRaises(round_txn.TransactionError) as raised:
                round_txn.execution_gate(batch, batch)

            message = str(raised.exception)
            self.assertIn("cannot verify 1 of 1", message)
            self.assertIn("--allow-inconclusive", message)


    def test_execution_gate_failed_record_refuses_even_without_a_waiver(self):
        with tempfile.TemporaryDirectory() as td:
            batch = Path(td) / "batch-r01.jsonl"
            write(batch, [thalamic("gate-failed-strict", rationale="")])

            with self.assertRaises(round_txn.TransactionError) as raised:
                round_txn.execution_gate(batch, batch)

            self.assertIn("never waivable", str(raised.exception))


    def test_execution_gate_waives_inconclusive_with_a_recorded_override(self):
        with tempfile.TemporaryDirectory() as td:
            batch = Path(td) / "batch-r01.jsonl"
            write(batch, [thalamic("gate-waiver", observable=False)])

            summary = round_txn.execution_gate(
                batch, batch, override="hil replay rig offline"
            )

        self.assertEqual(
            summary["override"],
            {"reason": "hil replay rig offline", "waived_inconclusive": 1},
        )
        self.assertEqual(summary["counts"]["inconclusive"], 1)


    def test_execution_gate_normalizes_the_waiver_reason(self):
        with tempfile.TemporaryDirectory() as td:
            batch = Path(td) / "batch-r01.jsonl"
            write(batch, [thalamic("gate-normalize", observable=False)])

            summary = round_txn.execution_gate(
                batch, batch, override="  hil rig\n\toffline\tuntil Monday  "
            )

        self.assertEqual(
            summary["override"]["reason"], "hil rig offline until Monday"
        )


    def test_execution_gate_enforces_the_waiver_reason_bounds(self):
        with tempfile.TemporaryDirectory() as td:
            batch = Path(td) / "batch-r01.jsonl"
            write(batch, [thalamic("gate-bounds", observable=False)])

            with self.assertRaisesRegex(
                round_txn.TransactionError, "at least 8 characters"
            ):
                round_txn.execution_gate(batch, batch, override="1234567")

            with self.assertRaisesRegex(
                round_txn.TransactionError, "at most"
            ):
                round_txn.execution_gate(
                    batch,
                    batch,
                    override="x" * (round_txn.EXECUTION_OVERRIDE_MAX_CHARS + 1),
                )

            with self.assertRaisesRegex(
                round_txn.TransactionError, "written phrase"
            ):
                round_txn.execution_gate(batch, batch, override="12345678")

            with self.assertRaisesRegex(
                round_txn.TransactionError, "written phrase"
            ):
                round_txn.execution_gate(batch, batch, override="looks fine")

            shortest = round_txn.execution_gate(
                batch, batch, override="hil replay rig offline"
            )
            self.assertEqual(shortest["override"]["reason"], "hil replay rig offline")

        with tempfile.TemporaryDirectory() as td:
            batch = Path(td) / "batch-r01.jsonl"
            write(batch, [thalamic("gate-bounds-max", observable=False)])
            longest_reason = (
                "see the " + "x" * (round_txn.EXECUTION_OVERRIDE_MAX_CHARS - 8)
            )
            longest = round_txn.execution_gate(
                batch, batch, override=longest_reason
            )
            self.assertEqual(longest["override"]["waived_inconclusive"], 1)


    def test_execution_gate_fails_closed_without_the_verifier(self):
        with tempfile.TemporaryDirectory() as td:
            batch = Path(td) / "batch-r01.jsonl"
            write(batch, [thalamic("gate-no-verifier")])

            with mock.patch.dict(sys.modules, {"verify_execution": None}):
                with self.assertRaises(round_txn.TransactionError) as raised:
                    round_txn.execution_gate(batch, batch)

        self.assertIn("execution verification is unavailable", str(raised.exception))


    def test_gate_summarizes_when_findings_exceed_five(self):
        with tempfile.TemporaryDirectory() as td:
            batch = Path(td) / "batch-r01.jsonl"
            write(batch, [thalamic(f"inc-{index}", observable=False) for index in range(6)])

            with self.assertRaises(round_txn.TransactionError) as raised:
                round_txn.execution_gate(batch, batch)

            self.assertIn("... and 1 more findings", str(raised.exception))


    def test_gate_fails_closed_when_the_verifier_is_unimportable(self):
        with mock.patch.dict(sys.modules, {"verify_execution": None}):
            with self.assertRaises(round_txn.TransactionError) as raised:
                round_txn.load_execution_verifier()
        self.assertIn("execution verification is unavailable", str(raised.exception))



if __name__ == "__main__":
    unittest.main()
