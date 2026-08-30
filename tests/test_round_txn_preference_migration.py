#!/usr/bin/env python3
"""Historical FFPC v1 completion markers and their migration ledger.

Split out of ``test_round_txn_preference`` so that module keeps the
publication gate and this one keeps the one-way upgrade of a lane that
predates the v2 marker.
"""

import json
import tempfile
import unittest

from round_txn_preference_support import (  # noqa: E402
    PreferenceRoundHarness,
    ffpc_record,
)
import round_txn  # noqa: E402
import round_txn_preference  # noqa: E402


class HistoricalV1MarkerMigration(PreferenceRoundHarness):
    def test_historical_v1_completion_marker_remains_visible(self):
        with tempfile.TemporaryDirectory() as td:
            factory = self.factory(td)
            round_txn.ensure_marker_mode(factory)
            marker = self.write_v1_completion(factory)

            with self.assertRaisesRegex(
                round_txn.TransactionError,
                "migrate-preference-v1",
            ):
                round_txn.frontier_status(factory)

            migration = round_txn.migrate_preference_v1_markers(factory)
            marker_digest = round_txn.file_sha256(marker)
            ledger = factory / round_txn.PREFERENCE_V1_LEDGER_FILE

            self.assertEqual(round_txn.frontier_status(factory)["next_round"], 2)
            self.assertEqual(ledger.stat().st_mode & 0o222, 0)
            reservation = self.reserve(factory, round_number=2)

        self.assertEqual(migration["markers"], [{"round": 1, "sha256": marker_digest}])
        self.assertEqual(reservation["round"], 2)
        self.assertEqual(reservation["version"], 1)

    def test_migrated_lane_survives_its_first_v2_publish(self):
        # `remember_execution_gate_cutover` rewrites .round-marker-mode.json
        # when the first v2 round publishes. A ledger frozen against the whole
        # file was invalidated by that write, so the lane it had just upgraded
        # could never be read again.
        with tempfile.TemporaryDirectory() as td:
            factory = self.factory(td)
            round_txn.ensure_marker_mode(factory)
            self.write_v1_completion(factory)
            round_txn.migrate_preference_v1_markers(factory)
            mode_path = round_txn.marker_mode_path(factory)
            mode_before = round_txn.file_sha256(mode_path)

            reservation = self.reserve(factory, round_number=2)
            self.fill_stage(reservation, ffpc_record(round_number=2))
            round_txn.publish(factory, 2, reservation["token"])

            self.assertNotEqual(round_txn.file_sha256(mode_path), mode_before)
            self.assertEqual(round_txn.frontier_status(factory)["next_round"], 3)
            self.assertEqual(self.reserve(factory, round_number=3)["round"], 3)

    def test_ledger_digest_covers_the_frozen_fields_and_only_those(self):
        # Only the publish-time cutover bookkeeping is allowed to move; the
        # declaration that decides how historical markers are read still seals
        # the ledger.
        with tempfile.TemporaryDirectory() as td:
            factory = self.factory(td)
            round_txn.ensure_marker_mode(factory)
            self.write_v1_completion(factory)
            round_txn.migrate_preference_v1_markers(factory)
            mode_path = round_txn.marker_mode_path(factory)
            frozen = round_txn_preference._ledger_marker_mode_digest(mode_path)

            mode = json.loads(mode_path.read_text())
            mode[round_txn.EXECUTION_CUTOVER_KEY] = 7
            mode_path.write_text(json.dumps(mode))
            self.assertEqual(
                round_txn_preference._ledger_marker_mode_digest(mode_path), frozen
            )

            mode["commit_point"] = "SOMETHING-ELSE-rNN.complete.json"
            mode_path.write_text(json.dumps(mode))
            self.assertNotEqual(
                round_txn_preference._ledger_marker_mode_digest(mode_path), frozen
            )

    def test_v1_migration_ledger_does_not_expand_to_later_markers(self):
        with tempfile.TemporaryDirectory() as td:
            factory = self.factory(td)
            round_txn.ensure_marker_mode(factory)
            self.write_v1_completion(factory, round_number=1)
            migration = round_txn.migrate_preference_v1_markers(factory)
            self.write_v1_completion(factory, round_number=2)

            with self.assertRaisesRegex(
                round_txn.TransactionError,
                "not in the frozen migration ledger",
            ):
                round_txn.frontier_status(factory)

        self.assertEqual([entry["round"] for entry in migration["markers"]], [1])

    def test_v1_migration_ledger_must_remain_read_only(self):
        with tempfile.TemporaryDirectory() as td:
            factory = self.factory(td)
            round_txn.ensure_marker_mode(factory)
            self.write_v1_completion(factory)
            round_txn.migrate_preference_v1_markers(factory)
            ledger = factory / round_txn.PREFERENCE_V1_LEDGER_FILE
            ledger.chmod(0o600)

            with self.assertRaisesRegex(
                round_txn.TransactionError,
                "migration ledger is writable",
            ):
                round_txn.frontier_status(factory)

    def test_historical_completion_marker_version_must_be_an_integer(self):
        for invalid_version in (True, 1.0):
            with self.subTest(version=invalid_version), tempfile.TemporaryDirectory() as td:
                factory = self.factory(td)
                round_txn.ensure_marker_mode(factory)
                self.write_v1_completion(factory, version=invalid_version)

                with self.assertRaisesRegex(
                    round_txn.TransactionError,
                    "unsupported completion marker version",
                ):
                    round_txn.migrate_preference_v1_markers(factory)


if __name__ == "__main__":
    unittest.main()
