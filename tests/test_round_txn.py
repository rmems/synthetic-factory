#!/usr/bin/env python3
"""Tests for transactional round reservation and publication."""

import contextlib
import hashlib
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
import preference_arms  # noqa: E402

PREFERENCE_FIXTURES = REPO / "tests" / "fixtures" / "preference-arms"


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


def ffpc_record(fixture="batch-r11.jsonl", round_number=1, index=0):
    records = [
        json.loads(line)
        for line in (PREFERENCE_FIXTURES / fixture).read_text().splitlines()
        if line.strip()
    ]
    record = records[index]
    record["id"] = record["id"].replace("r11", f"r{round_number:02d}")
    record["goal"] = "repair one failed action without changing its context"
    for holder in (record, record["chosen"], record["rejected"]):
        holder["meta"]["round"] = round_number
        holder["meta"]["factory"] = round_txn.PREFERENCE_ISOLATION_FACTORY
        holder["meta"]["isolation"] = round_txn.PREFERENCE_TWO_SESSION
    for arm_name in ("chosen", "rejected"):
        record[arm_name]["id"] = record[arm_name]["id"].replace("r11", f"r{round_number:02d}")
    return record


def diagnosis_document(index, *, root_cause=None):
    context = {
        "state": {"sim_or_real": "designed", "case": index},
        "proposed_action": {"action": "hold", "case": index},
    }
    target = {"per_component": {"safety": 0.5, "task_progress": 0.25}, "total": 0.75}
    return (
        "# Diagnosis\n\n"
        "## Shared context\n\n"
        "```json\n"
        f"{json.dumps(context, sort_keys=True)}\n"
        "```\n\n"
        "## Root cause\n\n"
        f"{root_cause or f'The gate skipped the required check for case {index}.'}\n\n"
        "## Cascade effects\n\n"
        "The gate error propagated through execution, outcome, and reward.\n\n"
        "## Supervisor catch\n\n"
        "Require the missing evidence before allowing execution.\n\n"
        "## Repair sketch\n\n"
        "Add the bounded check and use the safe fallback on failure.\n\n"
        "## Target reward delta\n\n"
        "```json\n"
        f"{json.dumps(target, sort_keys=True)}\n"
        "```\n"
    )


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

    def test_reserve_rejects_symlinked_staging_root_before_creating_stage(self):
        with tempfile.TemporaryDirectory() as td:
            factory = self.factory(td)
            outside = Path(td) / "outside-staging"
            outside.mkdir()
            staging_root = Path(td) / "outputs" / "staging"
            staging_root.symlink_to(outside, target_is_directory=True)

            with self.assertRaisesRegex(round_txn.TransactionError, "staging directory is unsafe"):
                round_txn.reserve(factory, 1, 1)

            self.assertEqual(list(outside.iterdir()), [])
            self.assertFalse((factory / "ROUND-r01.reserved.json").exists())

    def test_reserve_rejects_staging_root_swapped_before_descriptor_open(self):
        with tempfile.TemporaryDirectory() as td:
            factory = self.factory(td)
            outside = Path(td) / "outside-race"
            outside.mkdir()
            staging_root = Path(td) / "outputs" / "staging"
            real_open = round_txn.os.open
            swapped = False

            def swap_before_open(path, flags, mode=0o777, *, dir_fd=None):
                nonlocal swapped
                if path == "staging" and dir_fd is not None and not swapped:
                    staging_root.rmdir()
                    staging_root.symlink_to(outside, target_is_directory=True)
                    swapped = True
                return real_open(path, flags, mode, dir_fd=dir_fd)

            with mock.patch.object(round_txn.os, "open", side_effect=swap_before_open):
                with self.assertRaisesRegex(
                    round_txn.TransactionError, "staging directory is unsafe"
                ):
                    round_txn.reserve(factory, 1, 1)

            self.assertTrue(swapped)
            self.assertEqual(list(outside.iterdir()), [])
            self.assertFalse((factory / "ROUND-r01.reserved.json").exists())

    def test_reserve_rejects_dangling_transaction_marker(self):
        with tempfile.TemporaryDirectory() as td:
            factory = self.factory(td)
            marker = factory / "ROUND-r01.publishing.json"
            marker.symlink_to(Path(td) / "missing-marker-target")

            with self.assertRaisesRegex(
                round_txn.TransactionError, "publishing path already exists"
            ):
                round_txn.reserve(factory, 1, 1)

            self.assertTrue(marker.is_symlink())
            self.assertFalse((factory / "ROUND-r01.reserved.json").exists())

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

            with self.assertRaisesRegex(round_txn.TransactionError, "staging directory is unsafe"):
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

    def test_completed_publish_retry_finishes_interrupted_cleanup(self):
        with tempfile.TemporaryDirectory() as td:
            factory = self.factory(td)
            reservation = round_txn.reserve(factory, 1, 1)
            stage = self.fill_stage(reservation, [thalamic("cleanup-retry")])
            paths = round_txn.marker_paths(factory, 1)
            real_unlink = Path.unlink

            def interrupt_cleanup(path, *args, **kwargs):
                if path == paths["publishing"] and paths["complete"].exists():
                    raise OSError("simulated cleanup interruption")
                return real_unlink(path, *args, **kwargs)

            with mock.patch.object(
                Path,
                "unlink",
                autospec=True,
                side_effect=interrupt_cleanup,
            ):
                with self.assertRaisesRegex(OSError, "simulated cleanup interruption"):
                    round_txn.publish(factory, 1, reservation["token"])

            self.assertTrue(paths["complete"].is_file())
            self.assertTrue(paths["publishing"].is_file())
            self.assertTrue(paths["reservation"].is_file())
            self.assertTrue(stage.is_dir())

            manifest = round_txn.publish(factory, 1, reservation["token"])

            self.assertEqual(manifest["records"], 1)
            self.assertFalse(paths["publishing"].exists())
            self.assertFalse(paths["reservation"].exists())
            self.assertFalse(stage.exists())
            self.assertEqual(
                round_txn.publish(factory, 1, reservation["token"]),
                manifest,
            )

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

                with mock.patch.object(round_txn.os, "link", side_effect=interrupt_completion_link):
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

            with (
                mock.patch.object(round_txn, "validate_stage", side_effect=pause_validation),
                mock.patch.object(round_txn, "run_publish_lock", side_effect=observed_publish_lock),
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

    def test_publish_rejects_nonstandard_json_numeric_constants_anywhere(self):
        with tempfile.TemporaryDirectory() as td:
            factory = self.factory(td)
            reservation = round_txn.reserve(factory, 1, 1)
            record = thalamic("nonstandard-number")
            record["state"]["nested"] = {"measurement": float("nan")}
            self.fill_stage(reservation, [record])

            with self.assertRaisesRegex(
                round_txn.TransactionError,
                "non-standard JSON numeric constant NaN",
            ):
                round_txn.publish(factory, 1, reservation["token"])

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
                if Path(path).name == batch.name and Path(path) != batch:
                    batch.write_text("{not-json\n")
                return result

            with mock.patch.object(round_txn, "check_jsonl", side_effect=mutate_after_check):
                with self.assertRaisesRegex(round_txn.TransactionError, "changed while publishing"):
                    round_txn.publish(factory, 1, reservation["token"])

            self.assertFalse((factory / "ROUND-r01.complete.json").exists())

    def test_publication_id_scan_ignores_symlinked_sibling_directories(self):
        with tempfile.TemporaryDirectory() as td:
            factory = self.factory(td)
            outside = Path(td) / "outside-factory"
            outside.mkdir()
            write_records(outside / "records.jsonl", [thalamic("shared-id")])
            (factory.parent / "symlinked-sibling").symlink_to(outside, target_is_directory=True)
            reservation = round_txn.reserve(factory, 1, 1)
            self.fill_stage(reservation, [thalamic("shared-id")])

            manifest = round_txn.publish(factory, 1, reservation["token"])

            self.assertEqual(manifest["records"], 1)
            self.assertTrue((factory / "ROUND-r01.complete.json").is_file())

    def test_publication_id_scan_ignores_symlinked_run_root_payloads(self):
        with tempfile.TemporaryDirectory() as td:
            factory = self.factory(td)
            outside = Path(td) / "outside.jsonl"
            write_records(outside, [thalamic("shared-id")])
            (factory.parent / "linked-root.jsonl").symlink_to(outside)
            reservation = round_txn.reserve(factory, 1, 1)
            self.fill_stage(reservation, [thalamic("shared-id")])

            manifest = round_txn.publish(factory, 1, reservation["token"])

            self.assertEqual(manifest["records"], 1)
            self.assertTrue((factory / "ROUND-r01.complete.json").is_file())

    def test_invalid_utf8_completion_marker_is_a_transaction_error(self):
        with tempfile.TemporaryDirectory() as td:
            factory = self.factory(td)
            round_txn.ensure_marker_mode(factory)
            (factory / "ROUND-r01.complete.json").write_bytes(b"{\xff}\n")

            with self.assertRaisesRegex(round_txn.TransactionError, "cannot read transaction file"):
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
            self.assertEqual(
                json.loads((factory / round_txn.MODE_FILE).read_text())["legacy_baseline"], 2
            )
            self.assertEqual(reservation["round"], 3)

    def test_marker_baseline_rejects_malformed_lower_legacy_payload(self):
        with tempfile.TemporaryDirectory() as td:
            factory = self.factory(td)
            (factory / "batch-r25.jsonl").write_text("{not-json\n")
            write_records(
                factory / "batch-r26.jsonl",
                [thalamic(f"legacy-r26-{index}", 26) for index in range(5)],
            )
            (factory / round_txn.MODE_FILE).write_text(
                json.dumps(
                    {
                        "version": 1,
                        "legacy_baseline": 26,
                        "commit_point": "ROUND-rNN.complete.json",
                    }
                )
                + "\n"
            )

            with self.assertRaisesRegex(
                round_txn.TransactionError,
                "invalid legacy payload covered by marker baseline",
            ):
                round_txn.frontier_status(factory)

    def test_completed_batch_id_cannot_duplicate_legacy_baseline_id(self):
        with tempfile.TemporaryDirectory() as td:
            factory = self.factory(td)
            legacy_records = [thalamic("shared-id")]
            legacy_records.extend(thalamic(f"legacy-{index}") for index in range(1, 5))
            write_records(factory / "trajectories.jsonl", legacy_records)
            (factory / round_txn.MODE_FILE).write_text(
                json.dumps(
                    {
                        "version": 1,
                        "legacy_baseline": 1,
                        "commit_point": "ROUND-rNN.complete.json",
                    }
                )
                + "\n"
            )
            batch = factory / "batch-r02.jsonl"
            notes = factory / "NOTES-r02.md"
            write_records(batch, [thalamic("shared-id", 2)])
            notes.write_text("# Critique\n\nDuplicate ID fixture.\n")
            marker = factory / "ROUND-r02.complete.json"
            marker.write_text(
                json.dumps(
                    {
                        "version": 1,
                        "factory": factory.name,
                        "round": 2,
                        "records": 1,
                        "expected_records": 1,
                        "commit_point": marker.name,
                        "files": [
                            {"name": batch.name, "sha256": round_txn.file_sha256(batch)},
                            {"name": notes.name, "sha256": round_txn.file_sha256(notes)},
                        ],
                    }
                )
                + "\n"
            )

            with self.assertRaisesRegex(
                round_txn.TransactionError, "duplicate record id 'shared-id'"
            ):
                round_txn.frontier_status(factory)

    def test_legacy_baseline_id_cannot_duplicate_a_sibling_factory(self):
        with tempfile.TemporaryDirectory() as td:
            run = Path(td) / "run"
            first = run / "factory-first"
            second = run / "factory-second"
            first.mkdir(parents=True)
            second.mkdir()
            for factory in (first, second):
                write_records(factory / "trajectories.jsonl", [thalamic("shared-sibling-id")])
                (factory / round_txn.MODE_FILE).write_text(
                    json.dumps(
                        {
                            "version": 1,
                            "legacy_baseline": 1,
                            "commit_point": "ROUND-rNN.complete.json",
                        }
                    )
                    + "\n"
                )

            with self.assertRaisesRegex(
                round_txn.TransactionError, "duplicate record id 'shared-sibling-id'"
            ):
                round_txn.frontier_status(first)

    def test_completed_marker_id_cannot_duplicate_a_sibling_factory(self):
        with tempfile.TemporaryDirectory() as td:
            run = Path(td) / "run"
            sibling = run / "factory-first"
            factory = run / "factory-second"
            sibling.mkdir(parents=True)
            factory.mkdir()
            write_records(
                sibling / "trajectories.jsonl",
                [thalamic("shared-completed-id")],
            )
            round_txn.ensure_marker_mode(factory)
            batch = factory / "batch-r01.jsonl"
            notes = factory / "NOTES-r01.md"
            marker = factory / "ROUND-r01.complete.json"
            write_records(batch, [thalamic("shared-completed-id")])
            notes.write_text("# Critique\n\nDuplicate sibling ID fixture.\n")
            marker.write_text(
                json.dumps(
                    {
                        "version": 1,
                        "factory": factory.name,
                        "round": 1,
                        "records": 1,
                        "expected_records": 1,
                        "commit_point": marker.name,
                        "files": [
                            {"name": batch.name, "sha256": round_txn.file_sha256(batch)},
                            {"name": notes.name, "sha256": round_txn.file_sha256(notes)},
                        ],
                    }
                )
                + "\n"
            )

            with self.assertRaisesRegex(
                round_txn.TransactionError, "duplicate record id 'shared-completed-id'"
            ):
                round_txn.frontier_status(factory)

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
                        "version": 1,
                        "factory": factory.name,
                        "round": 1,
                        "records": 1,
                        "expected_records": 1,
                        "commit_point": marker.name,
                        "files": [
                            {
                                "name": batch.name,
                                "sha256": round_txn.file_sha256(batch),
                            },
                            {
                                "name": notes.name,
                                "sha256": round_txn.file_sha256(notes),
                            },
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

    def test_completion_manifest_rechecks_hash_after_semantic_validation(self):
        with tempfile.TemporaryDirectory() as td:
            factory = self.factory(td)
            round_txn.ensure_marker_mode(factory)
            batch = factory / "batch-r01.jsonl"
            notes = factory / "NOTES-r01.md"
            write_records(batch, [thalamic("semantic-swap")])
            notes.write_text("# Critique\n\nManifest fixture.\n")
            marker = factory / "ROUND-r01.complete.json"
            marker.write_text(
                json.dumps(
                    {
                        "version": 1,
                        "factory": factory.name,
                        "round": 1,
                        "records": 1,
                        "expected_records": 1,
                        "commit_point": marker.name,
                        "files": [
                            {"name": batch.name, "sha256": round_txn.file_sha256(batch)},
                            {"name": notes.name, "sha256": round_txn.file_sha256(notes)},
                        ],
                    }
                )
                + "\n"
            )
            real_validate = round_txn.validate_completed_batch

            def tamper_after_validation(*args, **kwargs):
                real_validate(*args, **kwargs)
                batch.write_text('{"id":"changed-after-validation"}\n')

            with mock.patch.object(
                round_txn,
                "validate_completed_batch",
                side_effect=tamper_after_validation,
            ):
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
                        "version": 1,
                        "factory": factory.name,
                        "round": 1,
                        "records": 1,
                        "expected_records": 1,
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

    def test_completion_marker_cannot_bless_a_malformed_batch(self):
        with tempfile.TemporaryDirectory() as td:
            factory = self.factory(td)
            round_txn.ensure_marker_mode(factory)
            batch = factory / "batch-r01.jsonl"
            notes = factory / "NOTES-r01.md"
            batch.write_text("{not-json\n")
            notes.write_text("# Critique\n\nMalformed batch fixture.\n")
            marker = factory / "ROUND-r01.complete.json"
            marker.write_text(
                json.dumps(
                    {
                        "version": 1,
                        "factory": factory.name,
                        "round": 1,
                        "records": 1,
                        "commit_point": marker.name,
                        "files": [
                            {"name": batch.name, "sha256": round_txn.file_sha256(batch)},
                            {"name": notes.name, "sha256": round_txn.file_sha256(notes)},
                        ],
                    }
                )
                + "\n"
            )

            with self.assertRaisesRegex(
                round_txn.TransactionError, "committed batch is not training-ready"
            ):
                round_txn.frontier_status(factory)

    def test_completion_marker_record_count_must_match_validated_batch(self):
        with tempfile.TemporaryDirectory() as td:
            factory = self.factory(td)
            reservation = round_txn.reserve(factory, 1, 1)
            self.fill_stage(reservation, [thalamic("count-mismatch")])
            round_txn.publish(factory, 1, reservation["token"])
            marker = factory / "ROUND-r01.complete.json"
            payload = json.loads(marker.read_text())
            payload["records"] = 2
            marker.write_text(json.dumps(payload) + "\n")

            with self.assertRaisesRegex(
                round_txn.TransactionError, "records does not match batch records"
            ):
                round_txn.frontier_status(factory)

    def test_completion_marker_requires_record_count_fields(self):
        with tempfile.TemporaryDirectory() as td:
            factory = self.factory(td)
            round_txn.ensure_marker_mode(factory)
            batch = factory / "batch-r01.jsonl"
            notes = factory / "NOTES-r01.md"
            batch.write_text("")
            notes.write_text("# Critique\n\nEmpty legacy marker fixture.\n")
            marker = factory / "ROUND-r01.complete.json"
            marker.write_text(
                json.dumps(
                    {
                        "version": 1,
                        "factory": factory.name,
                        "round": 1,
                        "commit_point": marker.name,
                        "files": [
                            {"name": batch.name, "sha256": round_txn.file_sha256(batch)},
                            {"name": notes.name, "sha256": round_txn.file_sha256(notes)},
                        ],
                    }
                )
                + "\n"
            )

            with self.assertRaisesRegex(
                round_txn.TransactionError,
                "completion marker records does not match batch records",
            ):
                round_txn.frontier_status(factory)

    def test_completion_marker_requires_schema_version(self):
        with tempfile.TemporaryDirectory() as td:
            factory = self.factory(td)
            round_txn.ensure_marker_mode(factory)
            batch = factory / "batch-r01.jsonl"
            notes = factory / "NOTES-r01.md"
            write_records(batch, [thalamic("missing-marker-version")])
            notes.write_text("# Critique\n\nVersion fixture.\n")
            marker = factory / "ROUND-r01.complete.json"
            marker.write_text(
                json.dumps(
                    {
                        "factory": factory.name,
                        "round": 1,
                        "records": 1,
                        "expected_records": 1,
                        "commit_point": marker.name,
                        "files": [
                            {"name": batch.name, "sha256": round_txn.file_sha256(batch)},
                            {"name": notes.name, "sha256": round_txn.file_sha256(notes)},
                        ],
                    }
                )
                + "\n"
            )

            with self.assertRaisesRegex(
                round_txn.TransactionError, "unsupported completion marker version"
            ):
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

    def test_marker_mode_cannot_hide_a_later_validated_legacy_batch(self):
        with tempfile.TemporaryDirectory() as td:
            factory = self.factory(td)
            for round_number in (1, 2):
                write_records(
                    factory / f"batch-r{round_number:02d}.jsonl",
                    [
                        thalamic(f"legacy-r{round_number:02d}-{index}", round_number)
                        for index in range(5)
                    ],
                )
            (factory / round_txn.MODE_FILE).write_text(
                json.dumps(
                    {
                        "version": 1,
                        "legacy_baseline": 1,
                        "commit_point": "ROUND-rNN.complete.json",
                    }
                )
                + "\n"
            )

            with self.assertRaisesRegex(
                round_txn.TransactionError,
                "excludes validated unmarked legacy frontier r02",
            ):
                round_txn.frontier_status(factory)

    def test_reserve_rejects_an_invalid_unowned_canonical_batch(self):
        with tempfile.TemporaryDirectory() as td:
            factory = self.factory(td)
            (factory / "batch-r01.jsonl").write_text("{not-json\n")
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

            with self.assertRaisesRegex(
                round_txn.TransactionError,
                "unowned canonical batch collision",
            ):
                round_txn.reserve(factory, 1, 1)

            self.assertFalse((factory / "ROUND-r01.reserved.json").exists())

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


class PreferencePublicationGate(unittest.TestCase):
    def factory(self, root):
        path = (
            Path(root) / "outputs" / "raw" / "2099-01-01" / round_txn.PREFERENCE_ISOLATION_FACTORY
        )
        path.mkdir(parents=True)
        return path

    def reserve(self, factory, round_number=1):
        return round_txn.reserve(
            factory,
            round_number,
            round_txn.FACTORY_QUOTAS[round_txn.PREFERENCE_ISOLATION_FACTORY],
            round_txn.PREFERENCE_TWO_SESSION,
        )

    def fill_stage(self, reservation, record, *, include_handoff=True):
        stage = Path(reservation["staging_dir"])
        round_number = reservation["round"]
        records = [
            record,
            ffpc_record(round_number=round_number, index=1),
            ffpc_record(round_number=round_number, index=2),
        ]
        if include_handoff:
            names = preference_arms.diagnosis_filenames(round_number, len(records))
            for index, name in enumerate(names, 1):
                (stage / name).write_text(
                    diagnosis_document(index),
                    encoding="utf-8",
                )
            preference_arms.write_diagnosis_handoff_receipt(stage, names)
        write_records(stage / reservation["batch_file"], records)
        (stage / reservation["notes_file"]).write_text(
            "# Critique\n\nIndependent arms were checked before publication.\n"
        )
        return stage

    def write_v1_completion(self, factory, round_number=1, *, version=1):
        batch = factory / f"batch-r{round_number:02d}.jsonl"
        notes = factory / f"NOTES-r{round_number:02d}.md"
        write_records(batch, [ffpc_record(round_number=round_number)])
        notes.write_text("# Critique\n\nHistorical pre-v2 preference evidence.\n")
        marker = factory / f"ROUND-r{round_number:02d}.complete.json"
        marker.write_text(
            json.dumps(
                {
                    "version": version,
                    "factory": factory.name,
                    "round": round_number,
                    "records": 1,
                    "expected_records": 1,
                    "commit_point": marker.name,
                    "files": [
                        {
                            "name": batch.name,
                            "sha256": round_txn.file_sha256(batch),
                        },
                        {
                            "name": notes.name,
                            "sha256": round_txn.file_sha256(notes),
                        },
                    ],
                }
            )
            + "\n"
        )
        return marker

    def test_ffpc_reservation_requires_the_publisher_isolation_marker(self):
        with tempfile.TemporaryDirectory() as td:
            factory = self.factory(td)
            with self.assertRaisesRegex(
                round_txn.TransactionError,
                "--preference-isolation two-session",
            ):
                round_txn.reserve(factory, 1, 1)
            self.assertFalse((factory / "ROUND-r01.reserved.json").exists())

    def test_ffpc_reservation_requires_the_fixed_three_record_quota(self):
        with tempfile.TemporaryDirectory() as td:
            factory = self.factory(td)
            with self.assertRaisesRegex(
                round_txn.TransactionError,
                "requires exactly 3 records",
            ):
                round_txn.reserve(
                    factory,
                    1,
                    1,
                    round_txn.PREFERENCE_TWO_SESSION,
                )

    def test_unrelated_factory_rejects_the_preference_isolation_flag(self):
        with tempfile.TemporaryDirectory() as td:
            factory = RoundTransaction().factory(td)
            with self.assertRaisesRegex(
                round_txn.TransactionError,
                "only valid for failure-as-fuel-preference-cascade",
            ):
                round_txn.reserve(
                    factory,
                    1,
                    1,
                    round_txn.PREFERENCE_TWO_SESSION,
                )

    def test_near_verbatim_pair_cannot_reach_the_commit_point(self):
        with tempfile.TemporaryDirectory() as td:
            factory = self.factory(td)
            reservation = self.reserve(factory)
            stage = self.fill_stage(
                reservation,
                ffpc_record("near-verbatim-r11.jsonl"),
            )

            with self.assertRaisesRegex(
                round_txn.TransactionError,
                "preference arm gate blocked publication",
            ):
                round_txn.publish(factory, 1, reservation["token"])

            self.assertTrue(stage.is_dir())
            self.assertTrue((factory / "ROUND-r01.reserved.json").is_file())
            self.assertFalse((factory / "batch-r01.jsonl").exists())
            self.assertFalse((factory / "ROUND-r01.complete.json").exists())

    def test_record_relabel_cannot_replace_the_reservation_marker(self):
        with tempfile.TemporaryDirectory() as td:
            factory = self.factory(td)
            reservation = self.reserve(factory)
            marker = factory / "ROUND-r01.reserved.json"
            edited = json.loads(marker.read_text())
            edited.pop("preference_isolation")
            marker.write_text(json.dumps(edited) + "\n")
            self.fill_stage(reservation, ffpc_record())

            with self.assertRaisesRegex(
                round_txn.TransactionError,
                "lacks the two-session orchestration assertion",
            ):
                round_txn.publish(factory, 1, reservation["token"])
            self.assertFalse((factory / "ROUND-r01.complete.json").exists())

    def test_unknown_arm_extension_cannot_reach_the_commit_point(self):
        with tempfile.TemporaryDirectory() as td:
            factory = self.factory(td)
            reservation = self.reserve(factory)
            record = ffpc_record("gate-label-only-r11.jsonl")
            record["chosen"]["padding"] = "alpha beta gamma delta epsilon"
            self.fill_stage(reservation, record)

            with self.assertRaisesRegex(
                round_txn.TransactionError,
                preference_arms.REASON_EXTENSION_FIELDS,
            ):
                round_txn.publish(factory, 1, reservation["token"])
            self.assertFalse((factory / "ROUND-r01.complete.json").exists())

    def test_direct_publish_requires_the_persisted_diagnosis_handoff(self):
        with tempfile.TemporaryDirectory() as td:
            factory = self.factory(td)
            reservation = self.reserve(factory)
            stage = self.fill_stage(
                reservation,
                ffpc_record(),
                include_handoff=False,
            )

            with self.assertRaisesRegex(
                round_txn.TransactionError,
                "missing diagnosis artifact",
            ):
                round_txn.publish(factory, 1, reservation["token"])

            self.assertTrue(stage.is_dir())
            self.assertTrue((factory / "ROUND-r01.reserved.json").is_file())
            self.assertFalse((factory / "ROUND-r01.complete.json").exists())

    def test_post_verification_diagnosis_tampering_blocks_publication(self):
        with tempfile.TemporaryDirectory() as td:
            factory = self.factory(td)
            reservation = self.reserve(factory)
            stage = self.fill_stage(reservation, ffpc_record())
            diagnosis = stage / preference_arms.diagnosis_filenames(1, 3)[1]
            diagnosis.write_text(
                diagnosis_document(2, root_cause="Changed after the verifier ran."),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(
                round_txn.TransactionError,
                "does not match receipt",
            ):
                round_txn.publish(factory, 1, reservation["token"])

            self.assertFalse((factory / "ROUND-r01.complete.json").exists())

    def test_forged_receipt_cannot_smuggle_a_rejected_trajectory(self):
        with tempfile.TemporaryDirectory() as td:
            factory = self.factory(td)
            reservation = self.reserve(factory)
            stage = self.fill_stage(reservation, ffpc_record())
            diagnosis_name = preference_arms.diagnosis_filenames(1, 3)[0]
            diagnosis = stage / diagnosis_name
            malicious = diagnosis_document(1) + (
                "\n```json\n"
                '{"safety_decision":{},"executed_action":{},'
                '"future_outcome":{},"reward_components":{}}\n'
                "```\n"
            )
            diagnosis.write_text(malicious, encoding="utf-8")

            receipt_path = stage / preference_arms.diagnosis_receipt_filename(1)
            receipt = json.loads(receipt_path.read_text())
            entry = next(
                item for item in receipt["diagnosis_files"] if item["name"] == diagnosis_name
            )
            payload = diagnosis.read_bytes()
            entry["bytes"] = len(payload)
            entry["sha256"] = hashlib.sha256(payload).hexdigest()
            receipt_path.chmod(0o600)
            receipt_path.write_text(json.dumps(receipt) + "\n")

            with self.assertRaisesRegex(
                round_txn.TransactionError,
                "diagnosis handoff receipt validation failed",
            ):
                round_txn.publish(factory, 1, reservation["token"])

            self.assertFalse((factory / "ROUND-r01.complete.json").exists())

    def test_receipt_identity_and_file_metadata_forgery_block_publication(self):
        mutations = {
            "version": lambda receipt: receipt.__setitem__("version", True),
            "old-version": lambda receipt: receipt.__setitem__("version", 1),
            "factory": lambda receipt: receipt.__setitem__("factory", "other-factory"),
            "round": lambda receipt: receipt.__setitem__("round", True),
            "stage": lambda receipt: receipt.__setitem__("staging_dir", "/tmp/other"),
            "token": lambda receipt: receipt.__setitem__("reservation_token", "0" * 32),
            "name": lambda receipt: receipt["diagnosis_files"][0].__setitem__(
                "name", "diagnosis-03-r01.md"
            ),
            "bytes": lambda receipt: receipt["diagnosis_files"][0].__setitem__("bytes", True),
            "digest": lambda receipt: receipt["diagnosis_files"][0].__setitem__("sha256", "0" * 64),
        }
        for label, mutate in mutations.items():
            with self.subTest(label=label), tempfile.TemporaryDirectory() as td:
                factory = self.factory(td)
                reservation = self.reserve(factory)
                stage = self.fill_stage(reservation, ffpc_record())
                receipt_path = stage / preference_arms.diagnosis_receipt_filename(1)
                receipt = json.loads(receipt_path.read_text())
                mutate(receipt)
                receipt_path.chmod(0o600)
                receipt_path.write_text(json.dumps(receipt) + "\n")

                with self.assertRaisesRegex(
                    round_txn.TransactionError,
                    "diagnosis handoff receipt validation failed",
                ):
                    round_txn.publish(factory, 1, reservation["token"])

                self.assertFalse((factory / "ROUND-r01.complete.json").exists())

    def test_diagnosis_artifact_set_is_exact(self):
        for mutation in ("missing", "extra", "legacy-single"):
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as td:
                factory = self.factory(td)
                reservation = self.reserve(factory)
                stage = self.fill_stage(reservation, ffpc_record())
                if mutation == "missing":
                    (stage / preference_arms.diagnosis_filenames(1, 3)[2]).unlink()
                elif mutation == "extra":
                    (stage / "diagnosis-04-r01.md").write_text("extra\n")
                else:
                    (stage / "diagnosis-r01.md").write_text("ambiguous legacy name\n")

                with self.assertRaisesRegex(
                    round_txn.TransactionError,
                    "diagnosis artifact",
                ):
                    round_txn.publish(factory, 1, reservation["token"])

                self.assertFalse((factory / "ROUND-r01.complete.json").exists())

    def test_cosmetic_identifier_edit_with_nested_padding_cannot_publish(self):
        for edit in (str.upper, lambda value: value + "/"):
            with self.subTest(edit=edit), tempfile.TemporaryDirectory() as td:
                factory = self.factory(td)
                reservation = self.reserve(factory)
                record = ffpc_record("gate-label-only-r11.jsonl")
                record["chosen"]["executed_action"]["padding"] = (
                    "alpha beta gamma delta epsilon zeta eta theta iota kappa lambda"
                )
                action = record["chosen"]["executed_action"]["action"]
                record["chosen"]["executed_action"]["action"] = edit(action)
                self.fill_stage(reservation, record)

                with self.assertRaisesRegex(
                    round_txn.TransactionError,
                    preference_arms.REASON_OBSERVABLES_IDENTICAL,
                ):
                    round_txn.publish(factory, 1, reservation["token"])
                self.assertFalse((factory / "ROUND-r01.complete.json").exists())

    def test_reservation_version_downgrade_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            factory = self.factory(td)
            reservation = self.reserve(factory)
            marker = factory / "ROUND-r01.reserved.json"
            payload = json.loads(marker.read_text())
            payload["version"] = 0
            marker.write_text(json.dumps(payload) + "\n")
            self.fill_stage(reservation, ffpc_record())

            with self.assertRaisesRegex(
                round_txn.TransactionError,
                "unsupported version",
            ):
                round_txn.publish(factory, 1, reservation["token"])
            self.assertFalse((factory / "ROUND-r01.complete.json").exists())

    def test_json_bool_and_float_are_not_reservation_version_one(self):
        for invalid_version in (True, 1.0):
            with self.subTest(version=invalid_version), tempfile.TemporaryDirectory() as td:
                factory = self.factory(td)
                reservation = self.reserve(factory)
                marker = factory / "ROUND-r01.reserved.json"
                payload = json.loads(marker.read_text())
                payload["version"] = invalid_version
                marker.write_text(json.dumps(payload) + "\n")
                self.fill_stage(reservation, ffpc_record())

                with self.assertRaisesRegex(
                    round_txn.TransactionError,
                    "unsupported version",
                ):
                    round_txn.publish(factory, 1, reservation["token"])
                self.assertFalse((factory / "ROUND-r01.complete.json").exists())

    def test_completed_publish_cleanup_rejects_non_integer_reservation_version(self):
        with tempfile.TemporaryDirectory() as td:
            factory = self.factory(td)
            reservation = self.reserve(factory)
            marker = factory / "ROUND-r01.reserved.json"
            reservation_payload = json.loads(marker.read_text())
            self.fill_stage(reservation, ffpc_record())
            round_txn.publish(factory, 1, reservation["token"])

            reservation_payload["version"] = True
            marker.write_text(json.dumps(reservation_payload) + "\n")
            with self.assertRaisesRegex(
                round_txn.TransactionError,
                "reservation conflicts with completed round",
            ):
                round_txn.publish(factory, 1, reservation["token"])

    def test_valid_pair_records_and_revalidates_the_gate(self):
        with tempfile.TemporaryDirectory() as td:
            factory = self.factory(td)
            reservation = self.reserve(factory)
            self.fill_stage(reservation, ffpc_record())

            manifest = round_txn.publish(factory, 1, reservation["token"])

            self.assertEqual(manifest["version"], 2)
            self.assertEqual(
                manifest["preference_isolation"],
                round_txn.PREFERENCE_TWO_SESSION,
            )
            self.assertEqual(manifest["preference_arm_gate"]["preference_pairs"], 3)
            self.assertEqual(manifest["preference_arm_gate"]["blocked_pairs"], 0)
            self.assertEqual(
                manifest["preference_diagnosis_handoff"]["reservation_token"],
                reservation["token"],
            )
            manifest_names = {item["name"] for item in manifest["files"]}
            self.assertIn("diagnosis-handoff-receipt-r01.json", manifest_names)
            self.assertTrue(set(preference_arms.diagnosis_filenames(1, 3)).issubset(manifest_names))
            self.assertEqual(
                (factory / "ROUND-r01.complete.json").stat().st_mode & 0o222,
                0,
            )
            self.assertEqual(round_txn.frontier_status(factory)["next_round"], 2)

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

    def test_completion_marker_cannot_forge_the_recorded_gate_result(self):
        with tempfile.TemporaryDirectory() as td:
            factory = self.factory(td)
            reservation = self.reserve(factory)
            self.fill_stage(reservation, ffpc_record())
            round_txn.publish(factory, 1, reservation["token"])
            marker = factory / "ROUND-r01.complete.json"
            manifest = json.loads(marker.read_text())
            manifest["preference_arm_gate"]["blocked_pairs"] = 1
            marker.chmod(0o600)
            marker.write_text(json.dumps(manifest) + "\n")
            marker.chmod(0o400)

            with self.assertRaisesRegex(
                round_txn.TransactionError,
                "preference arm gate does not match batch",
            ):
                round_txn.frontier_status(factory)

    def test_frontier_requires_the_committed_diagnosis_receipt_set(self):
        for omitted in (
            "diagnosis-handoff-receipt-r01.json",
            "diagnosis-02-r01.md",
        ):
            with self.subTest(omitted=omitted), tempfile.TemporaryDirectory() as td:
                factory = self.factory(td)
                reservation = self.reserve(factory)
                self.fill_stage(reservation, ffpc_record())
                round_txn.publish(factory, 1, reservation["token"])
                marker = factory / "ROUND-r01.complete.json"
                manifest = json.loads(marker.read_text())
                manifest["files"] = [
                    entry for entry in manifest["files"] if entry["name"] != omitted
                ]
                marker.chmod(0o600)
                marker.write_text(json.dumps(manifest) + "\n")
                marker.chmod(0o400)

                with self.assertRaisesRegex(
                    round_txn.TransactionError,
                    "diagnosis artifact set",
                ):
                    round_txn.frontier_status(factory)

    def test_gate_version_only_change_does_not_hide_a_completed_round(self):
        with tempfile.TemporaryDirectory() as td:
            factory = self.factory(td)
            reservation = self.reserve(factory)
            self.fill_stage(reservation, ffpc_record())
            round_txn.publish(factory, 1, reservation["token"])
            with mock.patch.object(preference_arms, "GATE_VERSION", "1.1.0"):
                self.assertEqual(round_txn.frontier_status(factory)["next_round"], 2)

    def test_gate_version_only_change_does_not_wedge_an_inflight_retry(self):
        with tempfile.TemporaryDirectory() as td:
            factory = self.factory(td)
            reservation = self.reserve(factory)
            self.fill_stage(reservation, ffpc_record())
            real_link = round_txn.os.link

            def interrupt_completion_link(*args, **kwargs):
                if Path(args[1]).name == "ROUND-r01.complete.json":
                    raise OSError("simulated interruption")
                return real_link(*args, **kwargs)

            with mock.patch.object(
                round_txn.os,
                "link",
                side_effect=interrupt_completion_link,
            ):
                with self.assertRaisesRegex(OSError, "simulated interruption"):
                    round_txn.publish(factory, 1, reservation["token"])

            publishing = factory / "ROUND-r01.publishing.json"
            original_gate_version = json.loads(publishing.read_text())["preference_arm_gate"][
                "gate"
            ]["version"]
            self.assertEqual(publishing.stat().st_mode & 0o222, 0)

            with mock.patch.object(preference_arms, "GATE_VERSION", "1.1.0"):
                manifest = round_txn.publish(factory, 1, reservation["token"])

            self.assertEqual(
                manifest["preference_arm_gate"]["gate"]["version"],
                original_gate_version,
            )
            self.assertEqual(round_txn.frontier_status(factory)["next_round"], 2)

    def test_writable_inflight_publish_plan_cannot_resume(self):
        with tempfile.TemporaryDirectory() as td:
            factory = self.factory(td)
            reservation = self.reserve(factory)
            self.fill_stage(reservation, ffpc_record())

            with mock.patch.object(
                round_txn.os,
                "link",
                side_effect=OSError("simulated interruption"),
            ):
                with self.assertRaisesRegex(OSError, "simulated interruption"):
                    round_txn.publish(factory, 1, reservation["token"])

            publishing = factory / "ROUND-r01.publishing.json"
            publishing.chmod(0o600)
            with self.assertRaisesRegex(
                round_txn.TransactionError,
                "publishing plan is writable",
            ):
                round_txn.publish(factory, 1, reservation["token"])

            self.assertFalse((factory / "ROUND-r01.complete.json").exists())

    def test_publish_plan_replacement_during_link_preserves_recovery_state(self):
        with tempfile.TemporaryDirectory() as td:
            factory = self.factory(td)
            reservation = self.reserve(factory)
            stage = self.fill_stage(reservation, ffpc_record())
            publishing = factory / "ROUND-r01.publishing.json"
            complete = factory / "ROUND-r01.complete.json"
            real_link = round_txn.os.link

            def replace_plan_before_link(source, destination, *args, **kwargs):
                if Path(destination).name == complete.name:
                    Path(source).unlink()
                    Path(source).write_text('{"attacker":true}\n', encoding="utf-8")
                    Path(source).chmod(0o400)
                return real_link(source, destination, *args, **kwargs)

            with (
                mock.patch.object(
                    round_txn.os,
                    "link",
                    side_effect=replace_plan_before_link,
                ),
                self.assertRaisesRegex(
                    round_txn.TransactionError,
                    r"(?:publishing plan changed while linking|"
                    r"completion marker bytes differ)",
                ),
            ):
                round_txn.publish(factory, 1, reservation["token"])

            self.assertTrue(stage.is_dir())
            self.assertTrue((factory / "ROUND-r01.reserved.json").is_file())
            self.assertTrue(publishing.is_file())
            self.assertFalse(complete.exists())

    def test_completion_marker_replacement_after_read_preserves_recovery_state(self):
        with tempfile.TemporaryDirectory() as td:
            factory = self.factory(td)
            reservation = self.reserve(factory)
            stage = self.fill_stage(reservation, ffpc_record())
            publishing = factory / "ROUND-r01.publishing.json"
            complete = factory / "ROUND-r01.complete.json"
            real_read = round_txn._read_json_from_expected_inode

            def replace_marker_after_read(path, **kwargs):
                value = real_read(path, **kwargs)
                Path(path).unlink()
                Path(path).write_text('{"attacker":true}\n', encoding="utf-8")
                Path(path).chmod(0o400)
                return value

            with (
                mock.patch.object(
                    round_txn,
                    "_read_json_from_expected_inode",
                    side_effect=replace_marker_after_read,
                ),
                self.assertRaisesRegex(
                    round_txn.TransactionError,
                    "completion marker changed during commit",
                ),
            ):
                round_txn.publish(factory, 1, reservation["token"])

            self.assertTrue(stage.is_dir())
            self.assertTrue((factory / "ROUND-r01.reserved.json").is_file())
            self.assertTrue(publishing.is_file())
            self.assertFalse(complete.exists())


if __name__ == "__main__":
    unittest.main()
