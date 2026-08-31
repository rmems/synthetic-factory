#!/usr/bin/env python3
"""Cohesive frontier execution-gate regression suite."""

import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tests.frontier_gate_helpers import (
    FrontierGateTestCaseMixin,
    round_txn,
    thalamic,
)


class FrontierPublishAtomicity(FrontierGateTestCaseMixin, unittest.TestCase):
    def test_gate_precedes_every_commit_point_link(self):
        with tempfile.TemporaryDirectory() as td:
            factory = self.factory(td)
            reservation = round_txn.reserve(factory, 1, 1)
            self.stage(reservation, [thalamic("gate-order")])
            real_gate = round_txn.execution_gate
            real_link = os.link
            order = []

            def gate_recorder(batch, staged_batch, override=None):
                order.append("gate")
                return real_gate(batch, staged_batch, override=override)

            def link_recorder(*args, **kwargs):
                order.append(args[1])
                return real_link(*args, **kwargs)

            with mock.patch.object(round_txn, "execution_gate", gate_recorder):
                with mock.patch.object(round_txn.os, "link", side_effect=link_recorder):
                    round_txn.publish(factory, 1, reservation["token"])

            self.assertEqual(order[0], "gate")
            self.assertTrue(
                any(
                    str(item).endswith("ROUND-r01.complete.json")
                    for item in order[1:]
                ),
                order,
            )
            self.assertTrue((factory / "ROUND-r01.complete.json").is_file())


    def test_blocked_gate_never_reaches_the_commit_point(self):
        with tempfile.TemporaryDirectory() as td:
            factory = self.factory(td)
            reservation = round_txn.reserve(factory, 1, 1)
            self.stage(reservation, [thalamic("gate-order-blocked", observable=False)])

            with mock.patch.object(
                round_txn.os,
                "link",
                side_effect=AssertionError("commit point reached"),
            ) as link:
                with self.assertRaises(round_txn.TransactionError) as raised:
                    round_txn.publish(factory, 1, reservation["token"])

            link.assert_not_called()
            self.assertIn("cannot verify", str(raised.exception))
            self.assertFalse((factory / "ROUND-r01.complete.json").exists())
            self.assertFalse((factory / "batch-r01.jsonl").exists())


    def test_publish_rejects_unsafe_publishing_markers(self):
        with tempfile.TemporaryDirectory() as td:
            factory = self.factory(td)
            reservation = round_txn.reserve(factory, 1, 1)
            self.stage(reservation, [thalamic("unsafe-publishing")])
            publishing = factory / "ROUND-r01.publishing.json"
            publishing.symlink_to(Path(td) / "missing-publishing")

            with self.assertRaisesRegex(
                round_txn.TransactionError, "unsafe publishing marker"
            ):
                round_txn.publish(factory, 1, reservation["token"])


    def test_publish_rejects_mismatched_publishing_markers(self):
        with tempfile.TemporaryDirectory() as td:
            factory = self.factory(td)

            def mutate(payload):
                payload["token"] = "not-the-reservation-token"
                return payload

            reservation = self._mutate_publishing_marker(
                factory, "mismatched-publishing", mutate
            )

            with self.assertRaisesRegex(
                round_txn.TransactionError, "publishing marker identity mismatch"
            ):
                round_txn.publish(factory, 1, reservation["token"])



if __name__ == "__main__":
    unittest.main()
