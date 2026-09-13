#!/usr/bin/env python3
"""Cohesive frontier execution-gate regression suite."""

import json
import tempfile
import unittest
from unittest import mock

from tests.frontier_gate_helpers import (
    FrontierGateTestCaseMixin,
    _write_round,
    round_txn,
    thalamic,
    write_marker_mode,
)
from tests.gate_fixtures import execution_summary


class FrontierMarkerPolicy(FrontierGateTestCaseMixin, unittest.TestCase):
    def test_version_2_completion_marker_binds_the_execution_verdict(self):
        with tempfile.TemporaryDirectory() as td:
            factory = self.factory(td)

            def mutate_delete(payload):
                payload.pop("execution_verification", None)
                return payload

            payload = self._mutate_complete_marker(
                factory, "gate-bound", mutate_delete
            )
            with self.assertRaisesRegex(
                round_txn.TransactionError, "version 2 completion marker"
            ):
                round_txn.frontier_status(factory)

            def mutate_corrupt(marker_payload):
                marker_payload["execution_verification"]["counts"]["verified"] = 0
                marker_payload["execution_verification"]["counts"]["inconclusive"] = 1
                marker_payload["execution_verification"]["override"] = {
                    "reason": "hil replay rig offline",
                    "waived_inconclusive": 1,
                }
                return marker_payload

            marker = factory / "ROUND-r01.complete.json"
            marker.write_text(
                json.dumps(mutate_corrupt(payload), indent=2, sort_keys=True) + "\n"
            )
            with self.assertRaisesRegex(
                round_txn.TransactionError,
                "execution verification conflicts with committed batch",
            ):
                round_txn.frontier_status(factory)


    def test_legacy_version_1_markers_without_verification_remain_visible(self):
        with tempfile.TemporaryDirectory() as td:
            factory = self.factory(td)
            _write_round(factory, 1, thalamic("legacy-v1"), {"version": 1})

            status = round_txn.frontier_status(factory)

            self.assertEqual(status["next_round"], 2)
            self.assertEqual(status["completed_markers"], [1])


    def test_unsupported_completion_marker_version_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            factory = self.factory(td)
            _write_round(
                factory, 1, thalamic("unsupported-version"), {"version": 3}
            )

            with mock.patch.object(round_txn, "validate_completed_batch"):
                with self.assertRaisesRegex(
                    round_txn.TransactionError,
                    r"unsupported completion marker version: ",
                ):
                    round_txn.completed_manifests(factory)


    def test_version_downgrade_cannot_skip_execution_verification(self):
        with tempfile.TemporaryDirectory() as td:
            factory = self.factory(td)

            def mutate(payload):
                payload["version"] = 1
                payload.pop("execution_verification", None)
                return payload

            self._mutate_complete_marker(factory, "gate-downgrade", mutate)

            with self.assertRaisesRegex(
                round_txn.TransactionError,
                "completion marker version downgrade cannot skip execution",
            ):
                round_txn.frontier_status(factory)


    def test_gap_publish_preserves_higher_legacy_markers(self):
        with tempfile.TemporaryDirectory() as td:
            factory = self.factory(td)
            write_marker_mode(factory)
            _write_round(factory, 2, thalamic("legacy-r02"), {"version": 1})
            self.assertEqual(round_txn.frontier_status(factory)["next_round"], 1)

            reservation = round_txn.reserve(factory, 1, 1)
            self.stage(reservation, [thalamic("verified-r01")])
            round_txn.publish(factory, 1, reservation["token"])

            mode = json.loads((factory / ".round-marker-mode.json").read_text())
            self.assertEqual(mode[round_txn.EXECUTION_CUTOVER_KEY], 3)
            self.assertEqual(mode[round_txn.EXECUTION_VERIFIED_ROUNDS_KEY], [1])
            frontier = round_txn.frontier_status(factory)
            self.assertEqual(frontier["completed_markers"], [1, 2])
            self.assertEqual(frontier["next_round"], 3)

            marker_path = factory / "ROUND-r01.complete.json"
            marker = json.loads(marker_path.read_text())
            marker["version"] = 1
            marker.pop("execution_verification", None)
            marker_path.write_text(json.dumps(marker, indent=2, sort_keys=True) + "\n")

            with self.assertRaisesRegex(
                round_txn.TransactionError,
                "completion marker version downgrade cannot skip execution",
            ):
                round_txn.frontier_status(factory)


    def test_completion_markers_are_ordered_by_round_before_downgrade_checks(self):
        with tempfile.TemporaryDirectory() as td:
            factory = self.factory(td)
            _write_round(
                factory,
                2,
                thalamic("verified-r02"),
                {"version": 2, "verification": execution_summary()},
            )
            _write_round(
                factory, 10, thalamic("legacy-r10"), {"version": 1}
            )
            write_marker_mode(factory, execution_verified_from_round=10)
            visited = []
            real_bind = round_txn._bind_completion_execution_verdict

            def record_bind(factory_dir, round_number, *args, **kwargs):
                visited.append(round_number)
                return real_bind(factory_dir, round_number, *args, **kwargs)

            with mock.patch.object(
                round_txn,
                "_bind_completion_execution_verdict",
                side_effect=record_bind,
            ):
                with self.assertRaisesRegex(
                    round_txn.TransactionError,
                    "version downgrade cannot skip execution",
                ):
                    round_txn.completed_manifests(factory)

            self.assertEqual(visited, [2, 10])



if __name__ == "__main__":
    unittest.main()
