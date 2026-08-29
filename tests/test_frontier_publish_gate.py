#!/usr/bin/env python3
"""Cohesive frontier execution-gate regression suite."""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tests.frontier_gate_helpers import (
    FrontierGateTestCaseMixin,
    round_txn,
    thalamic,
)


class FrontierPublishGate(FrontierGateTestCaseMixin, unittest.TestCase):
    def test_inconclusive_record_blocks_publish_and_the_frontier(self):
        with tempfile.TemporaryDirectory() as td:
            factory = self.factory(td)
            reservation = round_txn.reserve(factory, 1, 1)
            stage = self.stage(reservation, [thalamic("gate-1", observable=False)])

            with self.assertRaises(round_txn.TransactionError) as raised:
                round_txn.publish(factory, 1, reservation["token"])

            message = str(raised.exception)
            self.assertIn("cannot verify 1 of 1", message)
            self.assertIn("future_outcome lacks observable", message)
            self.assertIn("--allow-inconclusive", message)
            # No commit point, no committed artifacts, frontier unmoved, and
            # the staging area stays inspectable for the operator.
            self.assertFalse((factory / "ROUND-r01.complete.json").exists())
            self.assertFalse((factory / "ROUND-r01.publishing.json").exists())
            self.assertFalse((factory / "batch-r01.jsonl").exists())
            self.assertFalse((factory / "NOTES-r01.md").exists())
            self.assertTrue((stage / "batch-r01.jsonl").is_file())
            self.assertTrue((stage / "NOTES-r01.md").is_file())
            self.assertEqual(round_txn.frontier_status(factory)["next_round"], 1)
            self.assertTrue(stage.is_dir())
            self.assertTrue((factory / "ROUND-r01.reserved.json").is_file())


    def test_verified_batch_publishes_and_records_the_verdict(self):
        with tempfile.TemporaryDirectory() as td:
            factory = self.factory(td)
            reservation = round_txn.reserve(factory, 1, 1)
            self.stage(reservation, [thalamic("gate-ok")])

            manifest = round_txn.publish(factory, 1, reservation["token"])

            verdict = manifest["execution_verification"]
            self.assertTrue(verdict["strict"])
            self.assertIsNone(verdict["override"])
            self.assertEqual(verdict["counts"]["verified"], 1)
            self.assertEqual(verdict["counts"]["inconclusive"], 0)
            self.assertEqual(verdict["counts"]["failed"], 0)
            self.assertEqual(
                verdict["semantics_version"],
                round_txn.EXECUTION_VERIFIER_SEMANTICS_VERSION,
            )
            self.assertEqual(
                json.loads((factory / "ROUND-r01.complete.json").read_text())[
                    "execution_verification"
                ],
                verdict,
            )
            self.assertEqual(manifest["version"], 2)
            self.assertEqual(round_txn.frontier_status(factory)["next_round"], 2)


    def test_operator_override_records_the_waiver_before_advancing(self):
        with tempfile.TemporaryDirectory() as td:
            factory = self.factory(td)
            reservation = round_txn.reserve(factory, 1, 1)
            self.stage(reservation, [thalamic("gate-waived", observable=False)])

            manifest = round_txn.publish(
                factory,
                1,
                reservation["token"],
                "hil replay rig offline; reviewed by operator",
            )

            override = manifest["execution_verification"]["override"]
            self.assertEqual(
                override["reason"], "hil replay rig offline; reviewed by operator"
            )
            self.assertEqual(override["waived_inconclusive"], 1)
            self.assertEqual(
                manifest["execution_verification"]["counts"]["inconclusive"], 1
            )
            self.assertEqual(
                manifest["execution_verification"]["counts"]["verified"], 0
            )
            self.assertTrue((factory / "ROUND-r01.complete.json").is_file())
            self.assertEqual(round_txn.frontier_status(factory)["next_round"], 2)


    def test_cli_publish_accepts_the_operator_waiver(self):
        with tempfile.TemporaryDirectory() as td:
            factory = self.factory(td)
            reservation = round_txn.reserve(factory, 1, 1)
            self.stage(reservation, [thalamic("gate-cli", observable=False)])

            blocked = round_txn.main(
                ["publish", str(factory), "--round", "1", "--token", reservation["token"]]
            )
            self.assertEqual(blocked, 1)
            self.assertFalse((factory / "ROUND-r01.complete.json").exists())

            allowed = round_txn.main(
                [
                    "publish",
                    str(factory),
                    "--round",
                    "1",
                    "--token",
                    reservation["token"],
                    "--allow-inconclusive",
                    "replay harness unavailable this window",
                ]
            )
            self.assertEqual(allowed, 0)
            marker = json.loads((factory / "ROUND-r01.complete.json").read_text())
            self.assertEqual(
                marker["execution_verification"]["override"]["reason"],
                "replay harness unavailable this window",
            )

    def test_cli_bounds_invalid_override_without_a_traceback(self):
        script = Path(__file__).resolve().parents[1] / "pipelines" / "round_txn.py"
        with tempfile.TemporaryDirectory() as td:
            result = subprocess.run(
                [
                    sys.executable,
                    str(script),
                    "publish",
                    td,
                    "--round",
                    "1",
                    "--token",
                    "unused",
                    "--allow-inconclusive",
                    "looks fine",
                ],
                capture_output=True,
                check=False,
                text=True,
            )
        self.assertEqual(result.returncode, 1)
        self.assertIn("ERROR:", result.stderr)
        self.assertNotIn("Traceback", result.stderr)



if __name__ == "__main__":
    unittest.main()
