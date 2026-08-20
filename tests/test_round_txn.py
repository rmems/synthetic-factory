#!/usr/bin/env python3
"""Tests for transactional round reservation and publication."""

import contextlib
import json
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from unittest import mock

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "pipelines"))

import round_txn  # noqa: E402


def thalamic(record_id, round_number=1):
    return {
        "id": record_id,
        "state": {"sim_or_real": "designed", "domain": "transaction-test"},
        "proposed_action": {"action": "noop", "decision_basis": "fixture"},
        "safety_decision": {"decision": "ACCEPT", "rationale": "bounded fixture"},
        "executed_action": {"action": "noop"},
        "future_outcome": {"success": True},
        "reward_components": {"task_progress": 0.5, "safety": 0.5, "total": 1.0},
        "meta": {
            "factory": "thalamic-trajectory-factory",
            "round": round_number,
            "tags": ["transaction-test"],
        },
    }


def write_records(path, records):
    path.write_text("".join(json.dumps(record) + "\n" for record in records))


class RoundTransaction(unittest.TestCase):
    def factory(self, root):
        path = Path(root) / "outputs" / "raw" / "2099-01-01" / "thalamic-trajectory-factory"
        path.mkdir(parents=True)
        return path

    def fill_stage(self, reservation, records):
        stage = Path(reservation["staging_dir"])
        write_records(stage / reservation["batch_file"], records)
        (stage / reservation["notes_file"]).write_text("# Critique\n\nConcrete gap.\n")
        return stage

    def test_reserve_stage_publish_commits_once(self):
        with tempfile.TemporaryDirectory() as td:
            factory = self.factory(td)
            reservation = round_txn.reserve(factory, 1, 1)
            self.assertFalse((factory / "batch-r01.jsonl").exists())
            self.assertTrue(Path(reservation["staging_dir"]).is_dir())
            self.fill_stage(reservation, [thalamic("txn-1")])

            manifest = round_txn.publish(factory, 1, reservation["token"])

            self.assertEqual(manifest["records"], 1)
            self.assertTrue((factory / "batch-r01.jsonl").is_file())
            self.assertTrue((factory / "NOTES-r01.md").is_file())
            self.assertTrue((factory / "ROUND-r01.complete.json").is_file())
            self.assertFalse((factory / "ROUND-r01.reserved.json").exists())
            self.assertFalse(Path(reservation["staging_dir"]).exists())
            self.assertEqual(round_txn.frontier_status(factory)["next_round"], 2)
            with self.assertRaisesRegex(round_txn.TransactionError, "not the frontier"):
                round_txn.reserve(factory, 1, 1)

    def test_abort_releases_reservation_so_round_can_be_retried(self):
        with tempfile.TemporaryDirectory() as td:
            factory = self.factory(td)
            reservation = round_txn.reserve(factory, 1, 1)
            stage = Path(reservation["staging_dir"])
            self.assertTrue(stage.is_dir())

            result = round_txn.abort(factory, 1, reservation["token"])

            self.assertTrue(result["aborted"])
            self.assertEqual(result["next_round"], 1)
            self.assertFalse(stage.exists())
            self.assertFalse((factory / "ROUND-r01.reserved.json").exists())
            # The frontier is retryable: a fresh reservation for r1 succeeds.
            retry = round_txn.reserve(factory, 1, 1)
            self.fill_stage(retry, [thalamic("txn-retry")])
            manifest = round_txn.publish(factory, 1, retry["token"])
            self.assertEqual(manifest["records"], 1)

    def test_abort_requires_matching_token_and_refuses_committed_round(self):
        with tempfile.TemporaryDirectory() as td:
            factory = self.factory(td)
            reservation = round_txn.reserve(factory, 1, 1)
            with self.assertRaisesRegex(round_txn.TransactionError, "token mismatch"):
                round_txn.abort(factory, 1, "not-the-token")
            self.assertTrue(Path(reservation["staging_dir"]).is_dir())

            self.fill_stage(reservation, [thalamic("txn-committed")])
            round_txn.publish(factory, 1, reservation["token"])
            with self.assertRaisesRegex(round_txn.TransactionError, "already committed"):
                round_txn.abort(factory, 1, reservation["token"])
            self.assertTrue((factory / "ROUND-r01.complete.json").is_file())

    def test_abort_refuses_mid_publish_and_leaves_reservation(self):
        with tempfile.TemporaryDirectory() as td:
            factory = self.factory(td)
            reservation = round_txn.reserve(factory, 1, 1)
            self.fill_stage(reservation, [thalamic("txn-mid-publish")])
            real_link = round_txn.os.link
            calls = {"count": 0}

            def interrupt_second_link(*args, **kwargs):
                calls["count"] += 1
                if calls["count"] == 2:
                    raise OSError("simulated interruption")
                return real_link(*args, **kwargs)

            with mock.patch.object(round_txn.os, "link", side_effect=interrupt_second_link):
                with self.assertRaisesRegex(OSError, "simulated interruption"):
                    round_txn.publish(factory, 1, reservation["token"])

            self.assertTrue((factory / "ROUND-r01.publishing.json").is_file())
            self.assertTrue((factory / "ROUND-r01.reserved.json").is_file())
            with self.assertRaisesRegex(round_txn.TransactionError, "mid-publish"):
                round_txn.abort(factory, 1, reservation["token"])
            self.assertTrue((factory / "ROUND-r01.reserved.json").is_file())
            self.assertTrue((factory / "ROUND-r01.publishing.json").is_file())
            self.assertFalse((factory / "ROUND-r01.complete.json").exists())
            # The only safe unstick is resume publish, not abort.
            manifest = round_txn.publish(factory, 1, reservation["token"])
            self.assertEqual(manifest["records"], 1)
            self.assertTrue((factory / "ROUND-r01.complete.json").is_file())

    def test_abort_waits_for_inflight_publish_before_cleaning_stage(self):
        with tempfile.TemporaryDirectory() as td:
            factory = self.factory(td)
            reservation = round_txn.reserve(factory, 1, 1)
            stage = self.fill_stage(reservation, [thalamic("abort-race")])
            entered_validation = threading.Event()
            release_publish = threading.Event()
            publish_error = []
            abort_error = []
            real_validate = round_txn.validate_stage
            real_lock = round_txn.run_publish_lock
            abort_attempted_lock = threading.Event()

            def pause_validation(*args, **kwargs):
                entered_validation.set()
                self.assertTrue(release_publish.wait(timeout=2))
                return real_validate(*args, **kwargs)

            def publish_round():
                try:
                    round_txn.publish(factory, 1, reservation["token"])
                except BaseException as exc:
                    publish_error.append(exc)

            def abort_round():
                try:
                    round_txn.abort(factory, 1, reservation["token"])
                except BaseException as exc:
                    abort_error.append(exc)

            @contextlib.contextmanager
            def observed_publish_lock(lock_factory):
                if threading.current_thread().name == "aborter":
                    abort_attempted_lock.set()
                with real_lock(lock_factory):
                    yield

            with mock.patch.object(
                round_txn, "validate_stage", side_effect=pause_validation
            ), mock.patch.object(
                round_txn, "run_publish_lock", side_effect=observed_publish_lock
            ):
                publisher = threading.Thread(target=publish_round, name="publisher")
                publisher.start()
                self.assertTrue(entered_validation.wait(timeout=2))

                aborter = threading.Thread(target=abort_round, name="aborter")
                aborter.start()
                self.assertTrue(abort_attempted_lock.wait(timeout=2))
                self.assertTrue(stage.is_dir())
                release_publish.set()
                publisher.join(timeout=2)
                aborter.join(timeout=2)

            self.assertFalse(publisher.is_alive())
            self.assertFalse(aborter.is_alive())
            self.assertEqual(publish_error, [])
            self.assertEqual(len(abort_error), 1)
            self.assertIsInstance(abort_error[0], round_txn.TransactionError)
            self.assertIn("already committed", str(abort_error[0]))
            self.assertTrue((factory / "ROUND-r01.complete.json").is_file())
            self.assertFalse(stage.exists())

    def test_staged_id_cannot_duplicate_a_committed_round(self):
        with tempfile.TemporaryDirectory() as td:
            factory = self.factory(td)
            first = round_txn.reserve(factory, 1, 1)
            self.fill_stage(first, [thalamic("global-id")])
            round_txn.publish(factory, 1, first["token"])

            second = round_txn.reserve(factory, 2, 1)
            self.fill_stage(second, [thalamic("global-id", 2)])
            with self.assertRaisesRegex(round_txn.TransactionError, "duplicate record id"):
                round_txn.publish(factory, 2, second["token"])
            self.assertFalse((factory / "ROUND-r02.complete.json").exists())

    def test_staged_id_cannot_duplicate_another_factory(self):
        with tempfile.TemporaryDirectory() as td:
            factory = self.factory(td)
            sibling = factory.parent / "other-factory"
            sibling.mkdir()
            write_records(sibling / "batch-r01.jsonl", [thalamic("cross-factory")])

            reservation = round_txn.reserve(factory, 1, 1)
            self.fill_stage(reservation, [thalamic("cross-factory")])
            with self.assertRaisesRegex(round_txn.TransactionError, "duplicate record id"):
                round_txn.publish(factory, 1, reservation["token"])
            self.assertFalse((factory / "ROUND-r01.complete.json").exists())

    def test_staged_id_cannot_duplicate_root_level_legacy_jsonl(self):
        with tempfile.TemporaryDirectory() as td:
            factory = self.factory(td)
            write_records(factory.parent / "legacy.jsonl", [thalamic("root-level-id")])

            reservation = round_txn.reserve(factory, 1, 1)
            self.fill_stage(reservation, [thalamic("root-level-id")])
            with self.assertRaisesRegex(round_txn.TransactionError, "duplicate record id"):
                round_txn.publish(factory, 1, reservation["token"])
            self.assertFalse((factory / "ROUND-r01.complete.json").exists())

    def test_staged_id_cannot_duplicate_another_factory_inflight_publish(self):
        with tempfile.TemporaryDirectory() as td:
            factory = self.factory(td)
            sibling = factory.parent / "other-factory"
            sibling.mkdir()
            first = round_txn.reserve(factory, 1, 1)
            second = round_txn.reserve(sibling, 1, 1)
            self.fill_stage(first, [thalamic("inflight-id")])
            self.fill_stage(second, [thalamic("inflight-id")])
            real_link = round_txn.os.link
            calls = {"count": 0}

            def interrupt_completion_link(*args, **kwargs):
                calls["count"] += 1
                if calls["count"] == 3:
                    raise OSError("simulated interruption")
                return real_link(*args, **kwargs)

            with mock.patch.object(round_txn.os, "link", side_effect=interrupt_completion_link):
                with self.assertRaisesRegex(OSError, "simulated interruption"):
                    round_txn.publish(factory, 1, first["token"])

            self.assertTrue((factory / "ROUND-r01.publishing.json").is_file())
            with self.assertRaisesRegex(round_txn.TransactionError, "duplicate record id"):
                round_txn.publish(sibling, 1, second["token"])
            self.assertFalse((sibling / "ROUND-r01.complete.json").exists())

    def test_validation_failure_leaves_stage_and_does_not_advance(self):
        with tempfile.TemporaryDirectory() as td:
            factory = self.factory(td)
            reservation = round_txn.reserve(factory, 1, 1)
            invalid = thalamic("unused")
            invalid.pop("id")
            stage = self.fill_stage(reservation, [invalid])

            with self.assertRaisesRegex(round_txn.TransactionError, "not training-ready"):
                round_txn.publish(factory, 1, reservation["token"])

            self.assertTrue(stage.is_dir())
            self.assertTrue((factory / "ROUND-r01.reserved.json").is_file())
            self.assertFalse((factory / "batch-r01.jsonl").exists())
            self.assertFalse((factory / "ROUND-r01.complete.json").exists())
            self.assertEqual(round_txn.frontier_status(factory)["next_round"], 1)

    def test_exact_quota_is_enforced(self):
        with tempfile.TemporaryDirectory() as td:
            factory = self.factory(td)
            reservation = round_txn.reserve(factory, 1, 2)
            self.fill_stage(reservation, [thalamic("only-one")])
            with self.assertRaisesRegex(round_txn.TransactionError, "requires exactly 2"):
                round_txn.publish(factory, 1, reservation["token"])
            self.assertFalse((factory / "ROUND-r01.complete.json").exists())

    def test_preexisting_destination_is_never_replaced(self):
        with tempfile.TemporaryDirectory() as td:
            factory = self.factory(td)
            reservation = round_txn.reserve(factory, 1, 1)
            self.fill_stage(reservation, [thalamic("new")])
            destination = factory / "batch-r01.jsonl"
            destination.write_text("sentinel\n")

            with self.assertRaisesRegex(round_txn.TransactionError, "replace existing output"):
                round_txn.publish(factory, 1, reservation["token"])

            self.assertEqual(destination.read_text(), "sentinel\n")
            self.assertFalse((factory / "ROUND-r01.complete.json").exists())

    def test_extra_jsonl_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            factory = self.factory(td)
            reservation = round_txn.reserve(factory, 1, 1)
            stage = self.fill_stage(reservation, [thalamic("primary")])
            write_records(stage / "bonus.jsonl", [thalamic("undeclared")])
            with self.assertRaisesRegex(round_txn.TransactionError, "only the reserved JSONL"):
                round_txn.publish(factory, 1, reservation["token"])
            self.assertFalse((factory / "ROUND-r01.complete.json").exists())

    def test_unscoped_or_marker_like_artifact_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            factory = self.factory(td)
            reservation = round_txn.reserve(factory, 1, 1)
            stage = self.fill_stage(reservation, [thalamic("primary")])
            (stage / "ROUND-r99.complete.json").write_text("{}\n")
            with self.assertRaisesRegex(round_txn.TransactionError, "round-scoped"):
                round_txn.publish(factory, 1, reservation["token"])
            self.assertFalse((factory / "ROUND-r99.complete.json").exists())

    def test_interrupted_batch_link_resumes_without_self_duplicate(self):
        with tempfile.TemporaryDirectory() as td:
            factory = self.factory(td)
            reservation = round_txn.reserve(factory, 1, 1)
            self.fill_stage(reservation, [thalamic("resume")])
            real_link = round_txn.os.link
            calls = {"count": 0}

            def interrupt_completion_link(*args, **kwargs):
                calls["count"] += 1
                # Notes and batch have already linked; fail just before the
                # completion marker. Retrying must not see that linked but
                # uncommitted batch as a duplicate of its staged record.
                if calls["count"] == 3:
                    raise OSError("simulated interruption")
                return real_link(*args, **kwargs)

            with mock.patch.object(round_txn.os, "link", side_effect=interrupt_completion_link):
                with self.assertRaisesRegex(OSError, "simulated interruption"):
                    round_txn.publish(factory, 1, reservation["token"])

            self.assertTrue((factory / "ROUND-r01.publishing.json").is_file())
            self.assertFalse((factory / "ROUND-r01.complete.json").exists())
            self.assertTrue((factory / "batch-r01.jsonl").is_file())
            manifest = round_txn.publish(factory, 1, reservation["token"])
            self.assertEqual(manifest["records"], 1)
            self.assertTrue((factory / "ROUND-r01.complete.json").is_file())

    def test_malformed_legacy_filename_does_not_advance_frontier(self):
        with tempfile.TemporaryDirectory() as td:
            factory = self.factory(td)
            write_records(
                factory / "batch-r02.jsonl",
                [thalamic(f"legacy-{index}", 2) for index in range(5)],
            )
            (factory / "batch-r99.jsonl").write_text("{not-json\n")

            status = round_txn.frontier_status(factory)

            self.assertEqual(status["mode"], "legacy")
            self.assertEqual(status["highest_flushed"], 2)
            self.assertEqual(status["next_round"], 3)
            reservation = round_txn.reserve(factory, 3, 5)
            self.assertEqual(json.loads((factory / round_txn.MODE_FILE).read_text())["legacy_baseline"], 2)
            self.assertEqual(reservation["round"], 3)

    def test_marker_mode_exposes_only_manifest_verified_batches(self):
        with tempfile.TemporaryDirectory() as td:
            factory = self.factory(td)
            round_txn.ensure_marker_mode(factory)
            batch = factory / "batch-r01.jsonl"
            write_records(batch, [thalamic("manifest-checked")])
            marker = factory / "ROUND-r01.complete.json"

            marker.write_text('{"round":1}\n')
            with self.assertRaisesRegex(round_txn.TransactionError, "identity mismatch"):
                round_txn.committed_jsonl_paths(factory)

            marker.write_text(
                json.dumps(
                    {
                        "factory": factory.name,
                        "round": 1,
                        "commit_point": marker.name,
                        "files": [
                            {
                                "name": batch.name,
                                "sha256": round_txn.file_sha256(batch),
                            }
                        ],
                    }
                )
                + "\n"
            )
            self.assertEqual(round_txn.committed_jsonl_paths(factory), [batch])

            batch.write_text("tampered\n")
            with self.assertRaisesRegex(round_txn.TransactionError, "hash mismatch"):
                round_txn.committed_jsonl_paths(factory)

    def test_marker_mode_frontier_requires_verified_completion_manifest(self):
        with tempfile.TemporaryDirectory() as td:
            factory = self.factory(td)
            round_txn.ensure_marker_mode(factory)
            (factory / "ROUND-r01.complete.json").write_text('{"round":1}\n')

            with self.assertRaisesRegex(round_txn.TransactionError, "identity mismatch"):
                round_txn.reserve(factory, 2, 1)


if __name__ == "__main__":
    unittest.main()
