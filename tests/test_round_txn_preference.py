#!/usr/bin/env python3
"""The preference-arm gate on transactional round publication.

Split out of ``test_round_txn`` so that module keeps plain round
reservation and publication, and this one keeps the two-session
preference gate.
"""

import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from round_txn_preference_support import (  # noqa: E402
    diagnosis_document,
    ffpc_record,
    thalamic_factory,
    write_records,
)
import round_txn  # noqa: E402
import preference_arms  # noqa: E402


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
            "\nNovel coverage: 42%\n"
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

    def stage_with_marker(self, factory, *, set_fields=None, drop_fields=()):
        """Reserve, rewrite the reservation marker, and stage a valid pair."""
        reservation = self.reserve(factory)
        marker = factory / "ROUND-r01.reserved.json"
        payload = json.loads(marker.read_text())
        for field in drop_fields:
            payload.pop(field)
        payload.update(set_fields or {})
        marker.write_text(json.dumps(payload) + "\n")
        self.fill_stage(reservation, ffpc_record())
        return reservation

    def staged_round_paths(self, factory):
        """Stage a valid pair; return its reservation, stage, and marker paths."""
        reservation = self.reserve(factory)
        stage = self.fill_stage(reservation, ffpc_record())
        return (
            reservation,
            stage,
            factory / "ROUND-r01.publishing.json",
            factory / "ROUND-r01.complete.json",
        )

    def assert_reserve_refused(self, factory, pattern):
        """Reserving a two-session preference round fails with ``pattern``."""
        with self.assertRaisesRegex(round_txn.TransactionError, pattern):
            round_txn.reserve(factory, 1, 1, round_txn.PREFERENCE_TWO_SESSION)

    def assert_publish_refused(self, factory, reservation, pattern):
        """Publication fails with ``pattern`` and commits no completion marker."""
        with self.assertRaisesRegex(round_txn.TransactionError, pattern):
            round_txn.publish(factory, 1, reservation["token"])
        self.assertFalse((factory / "ROUND-r01.complete.json").exists())

    def assert_recovery_state_preserved(self, factory, stage, publishing, complete):
        """A refused publish leaves the round retryable, not half-committed."""
        self.assertTrue(stage.is_dir())
        self.assertTrue((factory / "ROUND-r01.reserved.json").is_file())
        self.assertTrue(publishing.is_file())
        self.assertFalse(complete.exists())

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
            self.assert_reserve_refused(self.factory(td), "requires exactly 3 records")

    def test_unrelated_factory_rejects_the_preference_isolation_flag(self):
        with tempfile.TemporaryDirectory() as td:
            self.assert_reserve_refused(
                thalamic_factory(td),
                "only valid for failure-as-fuel-preference-cascade",
            )

    def test_near_verbatim_pair_cannot_reach_the_commit_point(self):
        with tempfile.TemporaryDirectory() as td:
            factory = self.factory(td)
            reservation = self.reserve(factory)
            stage = self.fill_stage(
                reservation,
                ffpc_record("near-verbatim-r11.jsonl"),
            )

            self.assert_publish_refused(
                factory, reservation, "preference arm gate blocked publication"
            )

            self.assertTrue(stage.is_dir())
            self.assertTrue((factory / "ROUND-r01.reserved.json").is_file())
            self.assertFalse((factory / "batch-r01.jsonl").exists())

    def test_record_relabel_cannot_replace_the_reservation_marker(self):
        with tempfile.TemporaryDirectory() as td:
            factory = self.factory(td)
            reservation = self.stage_with_marker(
                factory, drop_fields=("preference_isolation",)
            )

            self.assert_publish_refused(
                factory, reservation, "lacks the two-session orchestration assertion"
            )

    def test_unknown_arm_extension_cannot_reach_the_commit_point(self):
        with tempfile.TemporaryDirectory() as td:
            factory = self.factory(td)
            reservation = self.reserve(factory)
            record = ffpc_record("gate-label-only-r11.jsonl")
            record["chosen"]["padding"] = "alpha beta gamma delta epsilon"
            self.fill_stage(reservation, record)

            self.assert_publish_refused(
                factory, reservation, preference_arms.REASON_EXTENSION_FIELDS
            )

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
            reservation = self.stage_with_marker(factory, set_fields={"version": 0})

            self.assert_publish_refused(factory, reservation, "unsupported version")

    def test_json_bool_and_float_are_not_reservation_version_one(self):
        for invalid_version in (True, 1.0):
            with self.subTest(version=invalid_version), tempfile.TemporaryDirectory() as td:
                factory = self.factory(td)
                reservation = self.stage_with_marker(
                    factory, set_fields={"version": invalid_version}
                )

                self.assert_publish_refused(factory, reservation, "unsupported version")

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
            reservation, stage, publishing, complete = self.staged_round_paths(factory)
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

            self.assert_recovery_state_preserved(factory, stage, publishing, complete)

    def test_completion_marker_replacement_after_read_preserves_recovery_state(self):
        with tempfile.TemporaryDirectory() as td:
            factory = self.factory(td)
            reservation, stage, publishing, complete = self.staged_round_paths(factory)
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

            self.assert_recovery_state_preserved(factory, stage, publishing, complete)


if __name__ == "__main__":
    unittest.main()
