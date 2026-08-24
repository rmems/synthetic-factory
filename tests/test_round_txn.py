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
        # The publish gate runs verify_execution in strict mode, so the fixture
        # has to carry the observable outcome evidence a real record carries.
        "future_outcome": {
            "success": True,
            "timeline": [{"t_ms": 0, "event": "noop accepted"}],
            "observed_effects": ["no actuator motion"],
            "new_state": {"sim_or_real": "designed", "domain": "transaction-test"},
        },
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
        (stage / reservation["notes_file"]).write_text(
            "# Critique\n\nConcrete gap.\n\nNovel coverage: 42%\n"
        )
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

            with self.assertRaisesRegex(
                round_txn.TransactionError, "staging directory is unsafe"
            ):
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

    def test_publish_requires_a_novel_coverage_line_on_the_legacy_lane(self):
        """The NOTES latch line gates every registered round, legacy included.

        Without it the token-efficiency early-stop has nothing to read, which
        is why the 2026-08-19 harvest saw 0/49 parseable NOTES.
        """
        with tempfile.TemporaryDirectory() as td:
            factory = self.factory(td)
            self.assertNotIn(factory.name, round_txn.AGENTIC_FACTORY_KINDS)
            reservation = round_txn.reserve(factory, 1, 1)
            stage = Path(reservation["staging_dir"])
            write_records(stage / reservation["batch_file"], [thalamic("txn-cov")])
            notes = stage / reservation["notes_file"]
            notes.write_text("# Critique\n\nDensified the tail. No latch line.\n")

            with self.assertRaisesRegex(round_txn.TransactionError, "Novel coverage"):
                round_txn.publish(factory, 1, reservation["token"])

            # A rejected publish is retryable: the reservation and stage stay.
            self.assertTrue(stage.is_dir())
            self.assertTrue((factory / "ROUND-r01.reserved.json").is_file())
            self.assertFalse((factory / "ROUND-r01.complete.json").exists())

            notes.write_text("# Critique\n\nDensified the tail.\n\nNovel coverage: 3.1%\n")
            manifest = round_txn.publish(factory, 1, reservation["token"])
            self.assertEqual(manifest["records"], 1)
            self.assertTrue((factory / "ROUND-r01.complete.json").is_file())

    def test_publish_preserves_the_generic_notes_contract_for_custom_lanes(self):
        with tempfile.TemporaryDirectory() as td:
            factory = Path(td) / "outputs" / "raw" / "2099-01-01" / "custom-factory"
            factory.mkdir(parents=True)
            self.assertNotIn(factory.name, round_txn.FACTORY_QUOTAS)
            reservation = round_txn.reserve(factory, 1, 1)
            stage = Path(reservation["staging_dir"])
            record = thalamic("custom-txn")
            record["meta"]["factory"] = factory.name
            write_records(stage / reservation["batch_file"], [record])
            (stage / reservation["notes_file"]).write_text(
                "# Custom critique\n\nNo registered token-efficiency policy.\n"
            )

            manifest = round_txn.publish(factory, 1, reservation["token"])

            self.assertEqual(manifest["records"], 1)
            self.assertTrue((factory / "ROUND-r01.complete.json").is_file())

    def test_publish_rejects_an_out_of_range_novel_coverage(self):
        with tempfile.TemporaryDirectory() as td:
            factory = self.factory(td)
            reservation = round_txn.reserve(factory, 1, 1)
            stage = Path(reservation["staging_dir"])
            write_records(stage / reservation["batch_file"], [thalamic("txn-range")])
            (stage / reservation["notes_file"]).write_text("Novel coverage: 140%\n")

            with self.assertRaisesRegex(
                round_txn.TransactionError, "between 0% and 100%"
            ):
                round_txn.publish(factory, 1, reservation["token"])
            self.assertFalse((factory / "ROUND-r01.complete.json").exists())

    def test_publish_rejects_ambiguous_novel_coverage_lines(self):
        for suffix, notes_text in (
            ("duplicate-same", "Novel coverage: 3.1%\nNovel coverage: 3.1%\n"),
            ("duplicate-different", "Novel coverage: 3.1%\nNovel coverage: 80%\n"),
            ("malformed-second", "Novel coverage: 3.1%\nNovel coverage: malformed\n"),
            ("same-line-second", "Novel coverage: 3.1% Novel coverage: 80%\n"),
            ("trailing-prose", "Novel coverage: 3.1% trailing prose\n"),
        ):
            with self.subTest(suffix=suffix), tempfile.TemporaryDirectory() as td:
                factory = self.factory(td)
                reservation = round_txn.reserve(factory, 1, 1)
                stage = Path(reservation["staging_dir"])
                write_records(
                    stage / reservation["batch_file"],
                    [thalamic(f"txn-ambiguous-{suffix}")],
                )
                (stage / reservation["notes_file"]).write_text(notes_text)

                with self.assertRaisesRegex(
                    round_txn.TransactionError, "exactly one unambiguous"
                ):
                    round_txn.publish(factory, 1, reservation["token"])
                self.assertFalse((factory / "ROUND-r01.complete.json").exists())

    def test_publish_rejects_coverage_split_across_physical_lines(self):
        with tempfile.TemporaryDirectory() as td:
            factory = self.factory(td)
            reservation = round_txn.reserve(factory, 1, 1)
            stage = Path(reservation["staging_dir"])
            write_records(
                stage / reservation["batch_file"],
                [thalamic("txn-split-line")],
            )
            (stage / reservation["notes_file"]).write_text(
                "Novel coverage:\n80% of tests passed.\n"
            )

            with self.assertRaisesRegex(
                round_txn.TransactionError,
                "exactly one unambiguous",
            ):
                round_txn.publish(factory, 1, reservation["token"])
            self.assertFalse((factory / "ROUND-r01.complete.json").exists())

    def test_read_path_does_not_retroactively_reject_pre_contract_notes(self):
        """Committed legacy rounds predate the contract and must stay readable.

        Widening the gate is forward-only: publish requires the line, while the
        history-reading paths keep the original fixed-agentic scope so no raw
        round has to be rewritten.
        """
        with tempfile.TemporaryDirectory() as td:
            factory = self.factory(td)
            notes = factory / "NOTES-r01.md"
            notes.write_text("# Critique\n\nPublished before the contract.\n")

            self.assertIsNone(round_txn.validate_novel_coverage(notes, factory))
            self.assertIn(
                "Novel coverage",
                round_txn.validate_novel_coverage(notes, factory, required=True),
            )

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

            with mock.patch.object(
                round_txn, "check_jsonl", side_effect=mutate_after_check
            ):
                with self.assertRaisesRegex(
                    round_txn.TransactionError, "changed while publishing"
                ):
                    round_txn.publish(factory, 1, reservation["token"])

            self.assertFalse((factory / "ROUND-r01.complete.json").exists())

    def test_publication_id_scan_ignores_symlinked_sibling_directories(self):
        with tempfile.TemporaryDirectory() as td:
            factory = self.factory(td)
            outside = Path(td) / "outside-factory"
            outside.mkdir()
            write_records(outside / "records.jsonl", [thalamic("shared-id")])
            (factory.parent / "symlinked-sibling").symlink_to(
                outside, target_is_directory=True
            )
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
            legacy_records.extend(
                thalamic(f"legacy-{index}") for index in range(1, 5)
            )
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


BRIDGE_FIXTURE = REPO / "tests" / "fixtures" / "bridge_gate_snn.jsonl"


def bridge(record_id, *, gate_snn=True):
    """The committed raster + gate-as-SNN reference record, re-identified."""

    record = json.loads(BRIDGE_FIXTURE.read_text(encoding="utf-8").splitlines()[0])
    record["id"] = record_id
    trajectory = record["language_view"]["trajectory"]
    trajectory["id"] = f"{record_id}-traj"
    trajectory["state"]["episode_id"] = record_id
    trajectory["meta"]["round"] = 1
    if not gate_snn:
        del record["gate_snn"]
    return record


class BridgeRasterEnvelope(unittest.TestCase):
    """A newly published Bridge round must be loadable by a distillation probe.

    ``curate_bridge`` owns the spike arithmetic; this layer only refuses the
    publish, and only for the staged batch — rounds committed before the
    contract existed keep their markers.
    """

    def factory(self, root):
        path = (
            Path(root)
            / "outputs"
            / "raw"
            / "2099-01-01"
            / "neuromorphic-event-language-bridge"
        )
        path.mkdir(parents=True)
        return path

    def stage(self, factory, records):
        reservation = round_txn.reserve(factory, 1, len(records))
        staging = Path(reservation["staging_dir"])
        write_records(staging / reservation["batch_file"], records)
        (staging / reservation["notes_file"]).write_text("# Critique\n\nConcrete gap.\n")
        return reservation

    def test_raster_backed_round_with_a_gate_head_publishes(self):
        with tempfile.TemporaryDirectory() as td:
            factory = self.factory(td)
            reservation = self.stage(
                factory, [bridge("bridge-1", gate_snn=False), bridge("bridge-2")]
            )
            manifest = round_txn.publish(factory, 1, reservation["token"])

        self.assertEqual(manifest["records"], 2)

    def test_record_without_a_raster_cannot_be_published(self):
        with tempfile.TemporaryDirectory() as td:
            factory = self.factory(td)
            bare = bridge("bridge-1")
            del bare["raster"]
            reservation = self.stage(factory, [bare])

            with self.assertRaisesRegex(
                round_txn.TransactionError, "20-50 ms raster excerpt sidecar"
            ):
                round_txn.publish(factory, 1, reservation["token"])
            self.assertFalse((factory / "batch-r01.jsonl").exists())

    def test_broken_spike_product_cannot_be_published(self):
        with tempfile.TemporaryDirectory() as td:
            factory = self.factory(td)
            record = bridge("bridge-1")
            record["raster"]["spikes"] = 999
            reservation = self.stage(factory, [record])

            with self.assertRaisesRegex(
                round_txn.TransactionError, "BRIDGE_SPIKE_BUDGET_MISMATCH"
            ):
                round_txn.publish(factory, 1, reservation["token"])

    def test_raster_without_a_routing_table_cannot_be_published(self):
        with tempfile.TemporaryDirectory() as td:
            factory = self.factory(td)
            record = bridge("bridge-1")
            record["raster"]["routing"]["table"] = []
            reservation = self.stage(factory, [record])

            with self.assertRaisesRegex(
                round_txn.TransactionError, "routing.table must carry at least one"
            ):
                round_txn.publish(factory, 1, reservation["token"])

    def test_round_without_a_spike_implemented_gate_cannot_be_published(self):
        with tempfile.TemporaryDirectory() as td:
            factory = self.factory(td)
            reservation = self.stage(
                factory,
                [bridge("bridge-1", gate_snn=False), bridge("bridge-2", gate_snn=False)],
            )

            with self.assertRaisesRegex(
                round_txn.TransactionError, "at least one spike-implemented gate"
            ):
                round_txn.publish(factory, 1, reservation["token"])

    def test_other_factories_are_untouched_by_the_bridge_envelope(self):
        with tempfile.TemporaryDirectory() as td:
            factory = (
                Path(td) / "outputs" / "raw" / "2099-01-01" / "thalamic-trajectory-factory"
            )
            factory.mkdir(parents=True)
            self.assertEqual(
                round_txn.validate_bridge_envelope(factory / "batch-r01.jsonl", factory),
                [],
            )


if __name__ == "__main__":
    unittest.main()
