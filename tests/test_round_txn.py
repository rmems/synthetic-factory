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

    def test_publish_copies_staged_files_to_independent_inodes(self):
        with tempfile.TemporaryDirectory() as td:
            factory = self.factory(td)
            reservation = round_txn.reserve(factory, 1, 1)
            stage = self.fill_stage(reservation, [thalamic("independent-copy")])
            staged_batch = stage / reservation["batch_file"]
            staged_handle = staged_batch.open("a")
            try:
                round_txn.publish(factory, 1, reservation["token"])
                staged_handle.write("mutated after publish\n")
                staged_handle.flush()
            finally:
                staged_handle.close()

            published = factory / reservation["batch_file"]
            self.assertNotIn("mutated after publish", published.read_text())
            marker = json.loads((factory / "ROUND-r01.complete.json").read_text())
            batch_entry = next(item for item in marker["files"] if item["name"] == published.name)
            self.assertEqual(round_txn.file_sha256(published), batch_entry["sha256"])

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

    def test_abort_refuses_a_symlinked_staging_directory(self):
        with tempfile.TemporaryDirectory() as td:
            factory = self.factory(td)
            reservation = round_txn.reserve(factory, 1, 1)
            stage = Path(reservation["staging_dir"])
            outside = Path(td) / "outside-stage"
            outside.mkdir()
            sentinel = outside / "keep.txt"
            sentinel.write_text("do not delete\n")
            stage.rmdir()
            stage.symlink_to(outside, target_is_directory=True)

            with self.assertRaisesRegex(round_txn.TransactionError, "staging directory is unsafe"):
                round_txn.abort(factory, 1, reservation["token"])

            self.assertEqual(sentinel.read_text(), "do not delete\n")
            self.assertTrue((factory / "ROUND-r01.reserved.json").is_file())

    def test_publish_refuses_a_symlinked_staging_directory(self):
        with tempfile.TemporaryDirectory() as td:
            factory = self.factory(td)
            reservation = round_txn.reserve(factory, 1, 1)
            stage = Path(reservation["staging_dir"])
            outside = Path(td) / "outside-publish-stage"
            outside.mkdir()
            write_records(outside / reservation["batch_file"], [thalamic("outside")])
            (outside / reservation["notes_file"]).write_text("# Critique\n\nExternal.\n")
            sentinel = outside / "keep.txt"
            sentinel.write_text("do not delete\n")
            stage.rmdir()
            stage.symlink_to(outside, target_is_directory=True)

            with self.assertRaisesRegex(
                round_txn.TransactionError, "staging directory is unsafe"
            ):
                round_txn.publish(factory, 1, reservation["token"])

            self.assertEqual(sentinel.read_text(), "do not delete\n")
            self.assertTrue(outside.is_dir())
            self.assertFalse((factory / "ROUND-r01.complete.json").exists())

    def test_abort_rejects_a_traversal_token_before_removing_any_directory(self):
        with tempfile.TemporaryDirectory() as td:
            factory = self.factory(td)
            reservation = round_txn.reserve(factory, 1, 1)
            reservation_path = factory / "ROUND-r01.reserved.json"
            outside = Path(td) / "victim"
            outside.mkdir()
            sentinel = outside / "keep.txt"
            sentinel.write_text("do not delete\n")
            malicious_token = "x/../../../../../victim"
            edited = json.loads(reservation_path.read_text())
            edited["token"] = malicious_token
            edited["staging_dir"] = str(
                Path(reservation["staging_dir"]).parent / f"r01-{malicious_token}"
            )
            reservation_path.write_text(json.dumps(edited) + "\n")

            with self.assertRaisesRegex(round_txn.TransactionError, "token must be"):
                round_txn.abort(factory, 1, malicious_token)

            self.assertEqual(sentinel.read_text(), "do not delete\n")
            self.assertTrue(reservation_path.is_file())

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

    def test_resume_rejects_corrupted_immutable_publishing_fields(self):
        for field, value in (
            ("version", 2),
            ("commit_point", "ROUND-r99.complete.json"),
        ):
            with self.subTest(field=field), tempfile.TemporaryDirectory() as td:
                factory = self.factory(td)
                reservation = round_txn.reserve(factory, 1, 1)
                self.fill_stage(reservation, [thalamic(f"resume-{field}")])
                real_link = round_txn.os.link
                calls = {"count": 0}

                def interrupt_completion_link(*args, **kwargs):
                    calls["count"] += 1
                    if calls["count"] == 3:
                        raise OSError("simulated interruption")
                    return real_link(*args, **kwargs)

                with mock.patch.object(
                    round_txn.os, "link", side_effect=interrupt_completion_link
                ):
                    with self.assertRaisesRegex(OSError, "simulated interruption"):
                        round_txn.publish(factory, 1, reservation["token"])

                publishing = factory / "ROUND-r01.publishing.json"
                payload = json.loads(publishing.read_text())
                payload[field] = value
                publishing.write_text(json.dumps(payload) + "\n")

                with self.assertRaisesRegex(
                    round_txn.TransactionError, "publishing plan conflicts"
                ):
                    round_txn.publish(factory, 1, reservation["token"])
                self.assertFalse((factory / "ROUND-r01.complete.json").exists())

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

    def test_staged_id_cannot_duplicate_nested_pre_marker_legacy_payload(self):
        with tempfile.TemporaryDirectory() as td:
            factory = self.factory(td)
            sibling = factory.parent / "other-factory"
            nested = sibling / "legacy" / "archive"
            nested.mkdir(parents=True)
            write_records(nested / "payload.jsonl", [thalamic("nested-legacy-id")])

            reservation = round_txn.reserve(factory, 1, 1)
            self.fill_stage(reservation, [thalamic("nested-legacy-id")])

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

    def test_publish_rejects_bytes_changed_after_record_validation(self):
        with tempfile.TemporaryDirectory() as td:
            factory = self.factory(td)
            reservation = round_txn.reserve(factory, 1, 1)
            stage = self.fill_stage(reservation, [thalamic("validated-bytes")])
            batch = stage / reservation["batch_file"]
            real_check_jsonl = round_txn.check_jsonl

            def mutate_after_check(path, *args, **kwargs):
                result = real_check_jsonl(path, *args, **kwargs)
                if Path(path) == batch:
                    batch.write_text("{not-json\n")
                return result

            with mock.patch.object(
                round_txn, "check_jsonl", side_effect=mutate_after_check
            ):
                with self.assertRaisesRegex(
                    round_txn.TransactionError, "changed during validation"
                ):
                    round_txn.publish(factory, 1, reservation["token"])

            self.assertFalse((factory / "ROUND-r01.complete.json").exists())

    def test_invalid_utf8_completion_marker_is_a_transaction_error(self):
        with tempfile.TemporaryDirectory() as td:
            factory = self.factory(td)
            round_txn.ensure_marker_mode(factory)
            (factory / "ROUND-r01.complete.json").write_bytes(b"{\xff}\n")

            with self.assertRaisesRegex(
                round_txn.TransactionError, "cannot read transaction file"
            ):
                round_txn.frontier_status(factory)

    def test_invalid_utf8_staged_notes_report_a_transaction_error(self):
        with tempfile.TemporaryDirectory() as td:
            factory = self.factory(td)
            reservation = round_txn.reserve(factory, 1, 1)
            stage = self.fill_stage(reservation, [thalamic("bad-notes")])
            (stage / reservation["notes_file"]).write_bytes(b"Novel coverage: 80%\xff\n")

            with self.assertRaisesRegex(round_txn.TransactionError, "cannot read staged notes"):
                round_txn.publish(factory, 1, reservation["token"])

            self.assertTrue((factory / "ROUND-r01.reserved.json").is_file())
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
            notes = factory / "NOTES-r01.md"
            write_records(batch, [thalamic("manifest-checked")])
            notes.write_text("# Critique\n\nManifest fixture.\n")
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
                            },
                            {
                                "name": notes.name,
                                "sha256": round_txn.file_sha256(notes),
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
            with self.assertRaisesRegex(round_txn.TransactionError, "hash mismatch"):
                round_txn.frontier_status(factory)

    def test_completion_manifest_validates_every_declared_artifact(self):
        with tempfile.TemporaryDirectory() as td:
            factory = self.factory(td)
            round_txn.ensure_marker_mode(factory)
            batch = factory / "batch-r01.jsonl"
            notes = factory / "NOTES-r01.md"
            auxiliary = factory / "EVIDENCE-r01.json"
            write_records(batch, [thalamic("complete-artifacts")])
            notes.write_text("# Critique\n\nArtifact fixture.\n")
            auxiliary.write_text('{"check":"passed"}\n')
            marker = factory / "ROUND-r01.complete.json"
            marker.write_text(
                json.dumps(
                    {
                        "factory": factory.name,
                        "round": 1,
                        "commit_point": marker.name,
                        "files": [
                            {"name": batch.name, "sha256": round_txn.file_sha256(batch)},
                            {"name": notes.name, "sha256": round_txn.file_sha256(notes)},
                            {"name": auxiliary.name, "sha256": round_txn.file_sha256(auxiliary)},
                        ],
                    }
                )
                + "\n"
            )

            self.assertEqual(round_txn.frontier_status(factory)["next_round"], 2)
            outside = Path(td) / "outside-evidence.json"
            outside.write_text(auxiliary.read_text())
            auxiliary.unlink()
            auxiliary.symlink_to(outside)
            with self.assertRaisesRegex(round_txn.TransactionError, "unsafe committed artifact"):
                round_txn.frontier_status(factory)

            auxiliary.unlink()
            auxiliary.write_text('{"check":"tampered"}\n')
            with self.assertRaisesRegex(round_txn.TransactionError, "hash mismatch"):
                round_txn.frontier_status(factory)

    def test_marker_mode_requires_schema_and_real_legacy_baseline(self):
        with tempfile.TemporaryDirectory() as td:
            factory = self.factory(td)
            mode = factory / round_txn.MODE_FILE
            mode.write_text(
                json.dumps(
                    {
                        "version": 2,
                        "legacy_baseline": 0,
                        "commit_point": "ROUND-rNN.complete.json",
                    }
                )
                + "\n"
            )
            with self.assertRaisesRegex(round_txn.TransactionError, "version"):
                round_txn.frontier_status(factory)

            mode.write_text(
                json.dumps(
                    {
                        "version": 1,
                        "legacy_baseline": 0,
                        "commit_point": "ROUND-rNN.publishing.json",
                    }
                )
                + "\n"
            )
            with self.assertRaisesRegex(round_txn.TransactionError, "commit point"):
                round_txn.frontier_status(factory)

            mode.write_text(
                json.dumps(
                    {
                        "version": 1,
                        "legacy_baseline": 1,
                        "commit_point": "ROUND-rNN.complete.json",
                    }
                )
                + "\n"
            )
            with self.assertRaisesRegex(round_txn.TransactionError, "exceeds discovered"):
                round_txn.frontier_status(factory)

    def test_marker_mode_cannot_hide_validated_legacy_named_payloads(self):
        with tempfile.TemporaryDirectory() as td:
            factory = self.factory(td)
            write_records(
                factory / "trajectories.jsonl",
                [thalamic(f"legacy-{index}") for index in range(5)],
            )
            (factory / round_txn.MODE_FILE).write_text(
                json.dumps(
                    {
                        "version": 1,
                        "legacy_baseline": 0,
                        "commit_point": "ROUND-rNN.complete.json",
                    }
                )
                + "\n"
            )

            with self.assertRaisesRegex(round_txn.TransactionError, "excludes validated legacy"):
                round_txn.committed_jsonl_paths(factory)

    def test_marker_mode_cannot_hide_validated_legacy_batch_r01(self):
        with tempfile.TemporaryDirectory() as td:
            factory = self.factory(td)
            write_records(
                factory / "batch-r01.jsonl",
                [thalamic(f"legacy-{index}") for index in range(5)],
            )
            (factory / round_txn.MODE_FILE).write_text(
                json.dumps(
                    {
                        "version": 1,
                        "legacy_baseline": 0,
                        "commit_point": "ROUND-rNN.complete.json",
                    }
                )
                + "\n"
            )

            with self.assertRaisesRegex(round_txn.TransactionError, "excludes validated legacy"):
                round_txn.committed_jsonl_paths(factory)

    def test_committed_paths_ignore_symlinked_legacy_payloads(self):
        with tempfile.TemporaryDirectory() as td:
            factory = self.factory(td)
            outside = Path(td) / "outside.jsonl"
            write_records(outside, [thalamic("outside")])
            (factory / "batch-r01.jsonl").symlink_to(outside)

            self.assertEqual(round_txn.committed_jsonl_paths(factory), [])
            self.assertEqual(round_txn.frontier_status(factory)["next_round"], 1)

    def test_marker_mode_frontier_requires_verified_completion_manifest(self):
        with tempfile.TemporaryDirectory() as td:
            factory = self.factory(td)
            round_txn.ensure_marker_mode(factory)
            (factory / "ROUND-r01.complete.json").write_text('{"round":1}\n')

            with self.assertRaisesRegex(round_txn.TransactionError, "identity mismatch"):
                round_txn.reserve(factory, 2, 1)


if __name__ == "__main__":
    unittest.main()
