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
    PreferenceRoundHarness,
    diagnosis_document,
    ffpc_record,
    rejected_scratch,
    shared_context,
    thalamic_factory,
    write_records,
)
import round_txn  # noqa: E402
import round_txn_preference  # noqa: E402
import preference_arms  # noqa: E402


class PreferencePublicationGate(PreferenceRoundHarness):
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

    def test_published_rejected_arm_must_be_session_as_scratch_failure(self):
        # Session B assembles the batch by injecting each rejected scratch
        # file. Nothing checked that it did, so both arms could be synthesized
        # together in one session and published beside unrelated Session A
        # failures.
        with tempfile.TemporaryDirectory() as td:
            factory = self.factory(td)
            reservation = self.reserve(factory)
            stage = self.fill_stage(reservation, ffpc_record())
            forged = json.loads((stage / "rejected-01-r01.json").read_text())
            forged["executed_action"]["action"] = "something-session-a-never-did"
            (stage / "rejected-01-r01.json").write_text(json.dumps(forged))

            self.assert_publish_refused(
                factory, reservation, "does not match Session A"
            )

    def test_publication_requires_every_rejected_scratch_artifact(self):
        with tempfile.TemporaryDirectory() as td:
            factory = self.factory(td)
            reservation = self.reserve(factory)
            stage = self.fill_stage(reservation, ffpc_record())
            (stage / "rejected-02-r01.json").unlink()

            self.assert_publish_refused(factory, reservation, "rejected scratch artifact")

    def test_published_pair_must_use_its_diagnosis_shared_context(self):
        # The handoff validated each diagnosis and threw its parsed context
        # away, so a batch could publish records that no authorized diagnosis
        # ever described. The mismatch is written before the receipt, so this
        # is the binding failing rather than the receipt digest.
        with tempfile.TemporaryDirectory() as td:
            factory = self.factory(td)
            reservation = self.reserve(factory)
            record = ffpc_record()
            unrelated = shared_context(record)
            unrelated["state"] = {"sim_or_real": "designed", "domain": "somewhere_else"}
            self.fill_stage(reservation, record, contexts={1: unrelated})

            self.assert_publish_refused(factory, reservation, "shared context")

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
