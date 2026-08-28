#!/usr/bin/env python3
"""docs/verify-execution.md clauses 16–24 — round_txn publish gate."""

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "pipelines"))

from gate_fixtures import (  # noqa: E402
    execution_summary,
    stage_reservation,
    thalamic,
    thalamic_factory,
    write,
    write_marker_mode,
)
import round_txn  # noqa: E402


class FrontierPublishGate(unittest.TestCase):
    """docs/verify-execution.md clause 16 — round_txn round-trip."""

    def factory(self, root):
        return thalamic_factory(root)

    def stage(self, reservation, records):
        return stage_reservation(reservation, records)

    def test_inconclusive_record_blocks_publish_and_the_frontier(self):
        with tempfile.TemporaryDirectory() as td:
            factory = self.factory(td)
            reservation = round_txn.reserve(factory, 1, 1)
            stage = self.stage(reservation, [thalamic("gate-1", observable=False)])

            with self.assertRaises(round_txn.TransactionError) as raised:
                round_txn.publish(factory, 1, reservation["token"])

            message = str(raised.exception)
            self.assertIn("cannot verify 1 of 1", message)
            self.assertIn("future_outcome lacks observable", message)
            self.assertIn("--allow-inconclusive", message)
            # No commit point, no committed artifacts, frontier unmoved, and
            # the staging area stays inspectable for the operator.
            self.assertFalse((factory / "ROUND-r01.complete.json").exists())
            self.assertFalse((factory / "ROUND-r01.publishing.json").exists())
            self.assertFalse((factory / "batch-r01.jsonl").exists())
            self.assertFalse((factory / "NOTES-r01.md").exists())
            self.assertEqual(round_txn.frontier_status(factory)["next_round"], 1)
            self.assertTrue(stage.is_dir())
            self.assertTrue((factory / "ROUND-r01.reserved.json").is_file())

    def test_verified_batch_publishes_and_records_the_verdict(self):
        with tempfile.TemporaryDirectory() as td:
            factory = self.factory(td)
            reservation = round_txn.reserve(factory, 1, 1)
            self.stage(reservation, [thalamic("gate-ok")])

            manifest = round_txn.publish(factory, 1, reservation["token"])

            verdict = manifest["execution_verification"]
            self.assertTrue(verdict["strict"])
            self.assertIsNone(verdict["override"])
            self.assertEqual(verdict["counts"]["verified"], 1)
            self.assertEqual(verdict["counts"]["inconclusive"], 0)
            self.assertEqual(verdict["counts"]["failed"], 0)
            self.assertEqual(
                verdict["semantics_version"],
                round_txn.EXECUTION_VERIFIER_SEMANTICS_VERSION,
            )
            self.assertEqual(
                json.loads((factory / "ROUND-r01.complete.json").read_text())[
                    "execution_verification"
                ],
                verdict,
            )
            self.assertEqual(manifest["version"], 2)
            self.assertEqual(round_txn.frontier_status(factory)["next_round"], 2)

    def test_version_2_completion_marker_binds_the_execution_verdict(self):
        with tempfile.TemporaryDirectory() as td:
            factory = self.factory(td)
            reservation = round_txn.reserve(factory, 1, 1)
            self.stage(reservation, [thalamic("gate-bound")])
            round_txn.publish(factory, 1, reservation["token"])
            marker = factory / "ROUND-r01.complete.json"
            payload = json.loads(marker.read_text())

            deleted = dict(payload)
            deleted.pop("execution_verification")
            marker.write_text(json.dumps(deleted, indent=2, sort_keys=True) + "\n")
            with self.assertRaisesRegex(
                round_txn.TransactionError, "version 2 completion marker"
            ):
                round_txn.frontier_status(factory)

            corrupted = json.loads(json.dumps(payload))
            corrupted["execution_verification"]["counts"]["verified"] = 0
            corrupted["execution_verification"]["counts"]["inconclusive"] = 1
            corrupted["execution_verification"]["override"] = {
                "reason": "hil replay rig offline",
                "waived_inconclusive": 1,
            }
            marker.write_text(json.dumps(corrupted, indent=2, sort_keys=True) + "\n")
            with self.assertRaisesRegex(
                round_txn.TransactionError,
                "execution verification conflicts with committed batch",
            ):
                round_txn.frontier_status(factory)

    def test_legacy_version_1_markers_without_verification_remain_visible(self):
        with tempfile.TemporaryDirectory() as td:
            factory = self.factory(td)
            batch = factory / "batch-r01.jsonl"
            notes = factory / "NOTES-r01.md"
            write(batch, [thalamic("legacy-v1")])
            notes.write_text("# Critique\n\nConcrete gap.\n\nNovel coverage: 42%\n")
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
                            {
                                "name": batch.name,
                                "sha256": round_txn.file_sha256(batch),
                            },
                            {
                                "name": notes.name,
                                "sha256": round_txn.file_sha256(notes),
                            },
                        ],
                    },
                    indent=2,
                    sort_keys=True,
                )
                + "\n"
            )
            write_marker_mode(factory)

            status = round_txn.frontier_status(factory)

            self.assertEqual(status["next_round"], 2)
            self.assertEqual(status["completed_markers"], [1])

    def test_operator_override_records_the_waiver_before_advancing(self):
        with tempfile.TemporaryDirectory() as td:
            factory = self.factory(td)
            reservation = round_txn.reserve(factory, 1, 1)
            self.stage(reservation, [thalamic("gate-waived", observable=False)])

            manifest = round_txn.publish(
                factory,
                1,
                reservation["token"],
                "hil replay rig offline; reviewed by operator",
            )

            override = manifest["execution_verification"]["override"]
            self.assertEqual(
                override["reason"], "hil replay rig offline; reviewed by operator"
            )
            self.assertEqual(override["waived_inconclusive"], 1)
            self.assertEqual(
                manifest["execution_verification"]["counts"]["inconclusive"], 1
            )
            self.assertEqual(
                manifest["execution_verification"]["counts"]["verified"], 0
            )
            self.assertTrue((factory / "ROUND-r01.complete.json").is_file())
            self.assertEqual(round_txn.frontier_status(factory)["next_round"], 2)

    def test_cli_publish_accepts_the_operator_waiver(self):
        with tempfile.TemporaryDirectory() as td:
            factory = self.factory(td)
            reservation = round_txn.reserve(factory, 1, 1)
            self.stage(reservation, [thalamic("gate-cli", observable=False)])

            blocked = round_txn.main(
                ["publish", str(factory), "--round", "1", "--token", reservation["token"]]
            )
            self.assertEqual(blocked, 1)
            self.assertFalse((factory / "ROUND-r01.complete.json").exists())

            allowed = round_txn.main(
                [
                    "publish",
                    str(factory),
                    "--round",
                    "1",
                    "--token",
                    reservation["token"],
                    "--allow-inconclusive",
                    "replay harness unavailable this window",
                ]
            )
            self.assertEqual(allowed, 0)
            marker = json.loads((factory / "ROUND-r01.complete.json").read_text())
            self.assertEqual(
                marker["execution_verification"]["override"]["reason"],
                "replay harness unavailable this window",
            )

    def test_failed_record_is_never_waivable(self):
        with tempfile.TemporaryDirectory() as td:
            batch = Path(td) / "batch-r01.jsonl"
            write(batch, [thalamic("gate-failed", rationale="")])

            with self.assertRaises(round_txn.TransactionError) as raised:
                round_txn.execution_gate(
                    batch, batch, override="operator accepts this batch"
                )

            self.assertIn("never waivable", str(raised.exception))

    def test_gate_fails_closed_when_the_verifier_is_unimportable(self):
        with mock.patch.dict(sys.modules, {"verify_execution": None}):
            with self.assertRaises(round_txn.TransactionError) as raised:
                round_txn.load_execution_verifier()
        self.assertIn("execution verification is unavailable", str(raised.exception))

    def _interrupt_publish(self, factory, reservation, records, reason=None):
        self.stage(reservation, records)
        with mock.patch.object(
            round_txn, "copy_verified_exclusive", side_effect=OSError("boom")
        ):
            with self.assertRaises(OSError):
                round_txn.publish(factory, 1, reservation["token"], reason)
        publishing = factory / "ROUND-r01.publishing.json"
        self.assertTrue(publishing.is_file())
        return publishing

    def test_publish_retry_keeps_the_first_recorded_waiver(self):
        with tempfile.TemporaryDirectory() as td:
            factory = self.factory(td)
            reservation = round_txn.reserve(factory, 1, 1)
            reason = "sensor replay pending; waived for this window"
            self._interrupt_publish(
                factory, reservation, [thalamic("gate-retry", observable=False)], reason
            )

            manifest = round_txn.publish(
                factory, 1, reservation["token"], "reworded on retry, same batch"
            )

            self.assertEqual(
                manifest["execution_verification"]["override"]["reason"], reason
            )
            self.assertTrue((factory / "ROUND-r01.complete.json").is_file())

    def test_publish_retry_reuses_the_recorded_waiver_without_a_new_flag(self):
        with tempfile.TemporaryDirectory() as td:
            factory = self.factory(td)
            reservation = round_txn.reserve(factory, 1, 1)
            reason = "sensor replay pending; waived for this window"
            self._interrupt_publish(
                factory, reservation, [thalamic("gate-resume", observable=False)], reason
            )

            manifest = round_txn.publish(factory, 1, reservation["token"])

            self.assertEqual(
                manifest["execution_verification"]["override"]["reason"], reason
            )
            self.assertTrue((factory / "ROUND-r01.complete.json").is_file())

    def test_publish_retry_migrates_a_pre_gate_publishing_marker(self):
        with tempfile.TemporaryDirectory() as td:
            factory = self.factory(td)
            reservation = round_txn.reserve(factory, 1, 1)
            publishing = self._interrupt_publish(
                factory, reservation, [thalamic("gate-legacy-retry")]
            )
            legacy = json.loads(publishing.read_text())
            legacy["version"] = 1
            legacy.pop("execution_verification")
            publishing.write_text(json.dumps(legacy) + "\n")

            manifest = round_txn.publish(factory, 1, reservation["token"])

            self.assertEqual(
                manifest["execution_verification"]["counts"]["verified"], 1
            )
            self.assertIsNone(manifest["execution_verification"]["override"])
            self.assertEqual(
                json.loads((factory / "ROUND-r01.complete.json").read_text()),
                manifest,
            )

    def test_publish_retry_rejects_corrupted_execution_verification(self):
        with tempfile.TemporaryDirectory() as td:
            factory = self.factory(td)
            reservation = round_txn.reserve(factory, 1, 1)
            publishing = self._interrupt_publish(
                factory, reservation, [thalamic("gate-corrupt-retry")]
            )
            corrupted = json.loads(publishing.read_text())
            corrupted["execution_verification"]["counts"]["verified"] = 999
            publishing.write_text(json.dumps(corrupted) + "\n")

            with self.assertRaisesRegex(
                round_txn.TransactionError, "execution verification conflicts"
            ):
                round_txn.publish(factory, 1, reservation["token"])
            self.assertFalse((factory / "ROUND-r01.complete.json").exists())

    def test_gate_summarizes_when_findings_exceed_five(self):
        with tempfile.TemporaryDirectory() as td:
            batch = Path(td) / "batch-r01.jsonl"
            write(batch, [thalamic(f"inc-{index}", observable=False) for index in range(6)])

            with self.assertRaises(round_txn.TransactionError) as raised:
                round_txn.execution_gate(batch, batch)

            self.assertIn("... and 1 more findings", str(raised.exception))

    def test_unsupported_completion_marker_version_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            factory = self.factory(td)
            batch = factory / "batch-r01.jsonl"
            notes = factory / "NOTES-r01.md"
            write(batch, [thalamic("unsupported-version")])
            notes.write_text("# Critique\n\nConcrete gap.\n\nNovel coverage: 42%\n")
            marker = factory / "ROUND-r01.complete.json"
            marker.write_text(
                json.dumps(
                    {
                        "version": 3,
                        "factory": factory.name,
                        "round": 1,
                        "records": 1,
                        "expected_records": 1,
                        "commit_point": marker.name,
                        "files": [
                            {"name": batch.name, "sha256": round_txn.file_sha256(batch)},
                            {"name": notes.name, "sha256": round_txn.file_sha256(notes)},
                        ],
                    },
                    indent=2,
                    sort_keys=True,
                )
                + "\n"
            )
            write_marker_mode(factory)

            with mock.patch.object(round_txn, "validate_completed_batch"):
                with self.assertRaisesRegex(
                    round_txn.TransactionError,
                    r"unsupported completion marker version: ",
                ):
                    round_txn.completed_manifests(factory)

    def test_publish_rejects_unsafe_or_mismatched_publishing_markers(self):
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

        with tempfile.TemporaryDirectory() as td:
            factory = self.factory(td)
            reservation = round_txn.reserve(factory, 1, 1)
            publishing = self._interrupt_publish(
                factory, reservation, [thalamic("mismatched-publishing")]
            )
            payload = json.loads(publishing.read_text())
            payload["token"] = "not-the-reservation-token"
            publishing.write_text(json.dumps(payload) + "\n")

            with self.assertRaisesRegex(
                round_txn.TransactionError, "publishing marker identity mismatch"
            ):
                round_txn.publish(factory, 1, reservation["token"])

    def test_publish_retry_migrates_a_legacy_v1_publishing_marker(self):
        with tempfile.TemporaryDirectory() as td:
            factory = self.factory(td)
            reservation = round_txn.reserve(factory, 1, 1)
            publishing = self._interrupt_publish(
                factory, reservation, [thalamic("gate-v1-retry")]
            )
            legacy = json.loads(publishing.read_text())
            legacy["version"] = 1
            publishing.write_text(json.dumps(legacy) + "\n")

            manifest = round_txn.publish(factory, 1, reservation["token"])

            self.assertEqual(manifest["version"], 2)
            self.assertEqual(
                manifest["execution_verification"]["counts"]["verified"], 1
            )
            self.assertTrue((factory / "ROUND-r01.complete.json").is_file())

    def test_publish_retry_rejects_version_2_marker_missing_verification(self):
        with tempfile.TemporaryDirectory() as td:
            factory = self.factory(td)
            reservation = round_txn.reserve(factory, 1, 1)
            publishing = self._interrupt_publish(
                factory, reservation, [thalamic("gate-v2-missing")]
            )
            payload = json.loads(publishing.read_text())
            payload.pop("execution_verification")
            publishing.write_text(json.dumps(payload) + "\n")

            with self.assertRaisesRegex(
                round_txn.TransactionError,
                "version 2 publishing marker is missing execution verification",
            ):
                round_txn.publish(factory, 1, reservation["token"])
            self.assertFalse((factory / "ROUND-r01.complete.json").exists())

    def test_version_downgrade_cannot_skip_execution_verification(self):
        with tempfile.TemporaryDirectory() as td:
            factory = self.factory(td)
            reservation = round_txn.reserve(factory, 1, 1)
            self.stage(reservation, [thalamic("gate-downgrade")])
            round_txn.publish(factory, 1, reservation["token"])
            marker = factory / "ROUND-r01.complete.json"
            payload = json.loads(marker.read_text())
            payload["version"] = 1
            payload.pop("execution_verification")
            marker.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")

            with self.assertRaisesRegex(
                round_txn.TransactionError,
                "completion marker version downgrade cannot skip execution",
            ):
                round_txn.frontier_status(factory)

    def _write_complete_round(self, factory, round_number, record, *, version, verification=None):
        rr = f"{round_number:02d}"
        batch = factory / f"batch-r{rr}.jsonl"
        notes = factory / f"NOTES-r{rr}.md"
        write(batch, [record])
        notes.write_text("# Critique\n\nConcrete gap.\n\nNovel coverage: 42%\n")
        payload = {
            "version": version,
            "factory": factory.name,
            "round": round_number,
            "records": 1,
            "expected_records": 1,
            "commit_point": f"ROUND-r{rr}.complete.json",
            "files": [
                {"name": batch.name, "sha256": round_txn.file_sha256(batch)},
                {"name": notes.name, "sha256": round_txn.file_sha256(notes)},
            ],
        }
        if verification is not None:
            payload["execution_verification"] = verification
        (factory / payload["commit_point"]).write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n"
        )

    def test_completion_markers_are_ordered_by_round_before_downgrade_checks(self):
        with tempfile.TemporaryDirectory() as td:
            factory = self.factory(td)
            write_marker_mode(factory)
            self._write_complete_round(
                factory, 10, thalamic("legacy-r10"), version=1
            )
            self._write_complete_round(
                factory, 11, thalamic("legacy-r11"), version=1
            )
            self._write_complete_round(
                factory,
                100,
                thalamic("verified-r100"),
                version=2,
                verification=execution_summary(),
            )

            manifests = round_txn.completed_manifests(factory)

            self.assertEqual(sorted(manifests), [10, 11, 100])
            self.assertEqual(manifests[10]["version"], 1)
            self.assertEqual(manifests[100]["version"], 2)


if __name__ == "__main__":
    unittest.main()
