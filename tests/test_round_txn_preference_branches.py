"""Fail-closed branches of ``round_txn_preference`` not reached by the flow tests.

The FFPC migration ledger, the sealed-plan link, and the committed-round
re-check all refuse rather than repair; each refusal is pinned here as a
contract with the exact message the module raises.
"""

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "pipelines"))

import round_txn
import round_txn_preference as rtp
from round_txn_preference_support import PreferenceRoundHarness, thalamic_factory

TransactionError = round_txn.TransactionError
TOKEN = "0" * 32
MALFORMED = "XYZ"


def _stat(dev=1, ino=1, mode=0o100400):
    return SimpleNamespace(st_dev=dev, st_ino=ino, st_mode=mode)


def _sealed_json(path, payload):
    path.write_text(json.dumps(payload))
    path.chmod(0o400)
    return path


class TempCaseMixin:
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)


class ReadOnlyJsonRefusals(TempCaseMixin, unittest.TestCase):
    def test_missing_symlinked_and_directory_plans_are_refused(self):
        target = _sealed_json(self.root / "plan.json", {})
        link = self.root / "link.json"
        link.symlink_to(target)
        cases = (
            (self.root / "missing.json", "cannot inspect plan"),
            (link, "unsafe plan"),
            (self.root, "unsafe plan"),
        )
        for path, pattern in cases:
            with self.subTest(path=path.name), self.assertRaisesRegex(TransactionError, pattern):
                rtp.read_readonly_json(path, label="plan")


class MigrationLedgerRefusals(PreferenceRoundHarness):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.lane = self.factory(tmp.name)
        round_txn.ensure_marker_mode(self.lane)
        self.write_v1_completion(self.lane)
        self.valid = round_txn.migrate_preference_v1_markers(self.lane)
        self.ledger = self.lane / round_txn.PREFERENCE_V1_LEDGER_FILE

    def rewrite(self, **fields):
        self.ledger.chmod(0o600)
        _sealed_json(self.ledger, {**self.valid, **fields})

    def test_directory_in_place_of_the_ledger_is_unsafe(self):
        self.ledger.unlink()
        self.ledger.mkdir()
        with self.assertRaisesRegex(TransactionError, "unsafe FFPC v1 migration ledger"):
            rtp.validated_preference_v1_ledger(self.lane)

    def test_ledger_header_and_entries_are_strictly_validated(self):
        digest = self.valid["markers"][0]["sha256"]
        cases = (
            ({"version": True}, "unsupported FFPC v1 migration ledger version"),
            ({"factory": "other"}, "identity mismatch"),
            ({"marker_mode_sha256": "nope"}, "invalid marker-mode hash"),
            ({"marker_mode_sha256": "f" * 64}, "marker-mode hash mismatch"),
            ({"markers": {}}, "markers must be an array"),
            ({"markers": ["entry"]}, "invalid entry"),
            ({"markers": [{"round": "1", "sha256": digest}]}, "invalid entry"),
            ({"markers": [{"round": 0, "sha256": digest}]}, "invalid entry"),
            ({"markers": [{"round": 1, "sha256": 7}]}, "invalid entry"),
            ({"markers": [{"round": 1, "sha256": digest}] * 2}, "invalid entry"),
        )
        for fields, pattern in cases:
            with self.subTest(fields=fields):
                self.rewrite(**fields)
                with self.assertRaisesRegex(TransactionError, pattern):
                    rtp.validated_preference_v1_ledger(self.lane)

    def test_ledger_without_marker_mode_is_refused(self):
        round_txn.marker_mode_path(self.lane).unlink()
        with self.assertRaisesRegex(TransactionError, "has no marker mode"):
            rtp.validated_preference_v1_ledger(self.lane)

    def test_second_migration_returns_the_frozen_ledger(self):
        self.write_v1_completion(self.lane, round_number=2)
        self.assertEqual(round_txn.migrate_preference_v1_markers(self.lane), self.valid)

    def test_concurrent_ledger_writer_wins_and_its_ledger_is_returned(self):
        self.ledger.chmod(0o600)
        self.ledger.unlink()
        real_write = round_txn.write_exclusive_json

        def racing_write(path, payload, *, mode):
            real_write(path, payload, mode=mode)
            raise FileExistsError(path)

        with mock.patch.object(round_txn, "write_exclusive_json", racing_write):
            payload = round_txn.migrate_preference_v1_markers(self.lane)
        self.assertEqual(payload["markers"], self.valid["markers"])


class MigrationEntryRefusals(PreferenceRoundHarness):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)

    def test_migration_is_only_for_an_existing_preference_lane(self):
        missing = self.root / round_txn.PREFERENCE_ISOLATION_FACTORY
        cases = (
            (thalamic_factory(self.root), "only valid for"),
            (missing, "not a factory directory"),
        )
        for factory, pattern in cases:
            with self.subTest(factory=factory.name), self.assertRaisesRegex(
                TransactionError, pattern
            ):
                round_txn.migrate_preference_v1_markers(factory)

    def test_migration_requires_marker_mode(self):
        with self.assertRaisesRegex(TransactionError, "marker mode is not enabled"):
            round_txn.migrate_preference_v1_markers(self.factory(self.root))

    def test_lane_without_v1_markers_freezes_an_empty_ledger(self):
        lane = self.factory(self.root)
        round_txn.ensure_marker_mode(lane)
        self.assertEqual(round_txn.migrate_preference_v1_markers(lane)["markers"], [])

    def test_v1_prefix_must_be_contiguous_and_precede_v2(self):
        cases = (
            ({1: {"version": 1}, 3: {"version": 1}}, [1, 3], 0, "one contiguous"),
            ({1: {"version": 2}, 2: {"version": 1}}, [2], 1, "cannot follow a v2"),
        )
        for manifests, v1_rounds, baseline, pattern in cases:
            with self.subTest(pattern=pattern), self.assertRaisesRegex(TransactionError, pattern):
                rtp._require_contiguous_v1_prefix(
                    manifests, v1_rounds, {"legacy_baseline": baseline}
                )


class CompletionMarkerSealing(TempCaseMixin, unittest.TestCase):
    def review(self, factory_name, mode):
        factory = self.root / factory_name
        factory.mkdir()
        path = factory / "ROUND-r01.complete.json"
        path.write_text("{}")
        path.chmod(mode)
        return rtp.PreferenceMarkerReview(factory, 1, path, {"version": 2}, set())

    def test_writable_v2_marker_is_refused_only_on_the_preference_lane(self):
        rtp._completed_preference_marker_is_sealed(self.review("other", 0o644))
        writable = self.review(round_txn.PREFERENCE_ISOLATION_FACTORY, 0o644)
        with self.assertRaisesRegex(TransactionError, "completion marker is writable"):
            rtp._completed_preference_marker_is_sealed(writable)


class LinkVerifiedCompletionMarker(TempCaseMixin, unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.publishing = _sealed_json(self.root / "ROUND-r01.publishing.json", {"a": 1})
        self.complete = self.root / "ROUND-r01.complete.json"

    def link(self, publishing=None, *, require_readonly=True):
        rtp.link_verified_completion_marker(
            publishing or self.publishing,
            self.complete,
            {"a": 1},
            require_readonly=require_readonly,
        )

    def test_plan_must_exist_be_regular_and_sealed(self):
        link = self.root / "link.json"
        link.symlink_to(self.publishing)
        self.publishing.chmod(0o600)
        cases = (
            (self.root / "missing.json", "cannot inspect publishing plan"),
            (link, "unsafe publishing plan"),
            (self.publishing, "publishing plan is writable"),
        )
        for path, pattern in cases:
            with self.subTest(path=path.name), self.assertRaisesRegex(TransactionError, pattern):
                self.link(path)
        self.assertFalse(self.complete.exists())

    def test_existing_completion_marker_is_never_replaced(self):
        self.complete.write_text("{}")
        with self.assertRaisesRegex(TransactionError, "completion marker already exists"):
            self.link()

    def test_vanished_marker_during_rollback_still_reraises(self):
        def vanish(path, **_kwargs):
            path.unlink()
            raise TransactionError("replaced")

        patch = mock.patch.object(round_txn, "_read_json_from_expected_inode", vanish)
        with patch, self.assertRaisesRegex(TransactionError, "replaced"):
            self.link()
        self.assertFalse(self.complete.exists())

    def test_linked_marker_must_be_the_plan_inode(self):
        plan = _stat()
        cases = (
            (_stat(ino=2), plan),
            (plan, _stat(ino=2)),
            (plan, _stat(mode=0o120777)),
            (plan, _stat(mode=0o040755)),
        )
        for publishing_stat, complete_stat in cases:
            with self.subTest(publishing=publishing_stat, complete=complete_stat):
                self.assertFalse(rtp._linked_marker_is_the_plan(plan, publishing_stat, complete_stat))

    def test_linked_identity_mismatch_is_refused(self):
        patch = mock.patch.object(rtp, "_linked_marker_is_the_plan", return_value=False)
        with patch, self.assertRaisesRegex(TransactionError, "changed while linking"):
            self.link()
        self.assertFalse(self.complete.exists())


class ExpectedInodeReads(TempCaseMixin, unittest.TestCase):
    @staticmethod
    def read(path, expected_stat):
        return rtp._read_json_from_expected_inode(
            path, label="marker", expected_stat=expected_stat, require_readonly=True
        )

    def test_descriptor_read_refuses_drift_and_non_objects(self):
        plan = _sealed_json(self.root / "plan.json", [1])
        other = _sealed_json(self.root / "other.json", {})
        cases = (
            (self.root, self.root.lstat(), "changed while it was opened"),
            (plan, other.lstat(), "changed while it was opened"),
            (self.root / "missing.json", plan.lstat(), "cannot read marker"),
            (plan, plan.lstat(), "must contain an object"),
        )
        for path, expected, pattern in cases:
            with self.subTest(path=path.name), self.assertRaisesRegex(TransactionError, pattern):
                self.read(path, expected)

    def test_path_identity_recheck_refuses_missing_links_and_directories(self):
        plan = _sealed_json(self.root / "plan.json", {})
        link = self.root / "link.json"
        link.symlink_to(plan)
        cases = (
            (self.root / "missing.json", "cannot inspect marker"),
            (link, "marker changed during commit"),
            (self.root, "marker changed during commit"),
        )
        expected = plan.lstat()
        for path, pattern in cases:
            with self.subTest(path=path.name), self.assertRaisesRegex(TransactionError, pattern):
                rtp._require_expected_path_identity(path, expected, label="marker")

    def test_open_flags_without_o_nofollow(self):
        with mock.patch.object(rtp, "os", SimpleNamespace(O_RDONLY=os.O_RDONLY)):
            self.assertEqual(rtp._readonly_open_flags(), os.O_RDONLY)

    def test_non_dict_gate_evidence_is_kept_verbatim(self):
        summary = {"gate": "legacy", "pairs": 3}
        self.assertEqual(rtp._stable_preference_gate_evidence(summary), summary)


class CommittedRoundRecheck(TempCaseMixin, unittest.TestCase):
    def committed(self, records=3, **manifest):
        factory = self.root / "outputs" / "raw" / "2099-01-01"
        factory = factory / round_txn.PREFERENCE_ISOLATION_FACTORY
        factory.mkdir(parents=True, exist_ok=True)
        return rtp.CommittedPreferenceRound(
            factory, 1, manifest, factory / "batch-r01.jsonl", records, 2, False
        )

    def test_v2_round_evidence_refusals(self):
        two = round_txn.PREFERENCE_TWO_SESSION
        cases = (
            (self.committed(records=1), "requires exactly 3"),
            (self.committed(), "lacks trusted two-session isolation"),
            (self.committed(preference_isolation=two), "lacks the preference arm gate"),
        )
        for committed, pattern in cases:
            with self.subTest(pattern=pattern), self.assertRaisesRegex(TransactionError, pattern):
                rtp._completed_preference_isolation_matches(committed)

    def test_invalid_reservation_token_is_refused(self):
        committed = self.committed(token=MALFORMED)
        with self.assertRaisesRegex(TransactionError, "invalid reservation token"):
            rtp._require_recorded_diagnosis_handoff(committed)

    def test_handoff_must_match_the_recorded_receipt(self):
        committed = self.committed(token=TOKEN, preference_diagnosis_handoff={"old": 1})
        with mock.patch.object(
            rtp, "validate_preference_diagnosis_handoff", return_value={"new": 1}
        ), self.assertRaisesRegex(TransactionError, "diagnosis handoff does not match"):
            rtp._require_recorded_diagnosis_handoff(committed)


class ReservationMatch(unittest.TestCase):
    def test_reservation_must_name_this_factory_round_and_token(self):
        base = {"version": 1, "factory": "f", "round": 1, "token": TOKEN}
        self.assertTrue(rtp.reservation_matches_completed_round(base, "f", 1, TOKEN))
        for field, value in (("factory", "g"), ("round", 2), ("token", "1" * 32)):
            with self.subTest(field=field):
                reservation = {**base, field: value}
                self.assertFalse(rtp.reservation_matches_completed_round(reservation, "f", 1, TOKEN))


if __name__ == "__main__":
    unittest.main()
