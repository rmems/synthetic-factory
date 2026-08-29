#!/usr/bin/env python3
"""The diagnosis-only Session A to Session B handoff bridge."""

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from preference_arms_support import (  # noqa: E402
    diagnosis_document,
    run_cli,
)
import preference_arms  # noqa: E402


class DiagnosisHandoffVerification(unittest.TestCase):
    TOKEN = "a" * 32

    def stage(self, root, *, count=3, round_number=11):
        round_text = f"{round_number:02d}"
        stage = (
            Path(root)
            / "outputs"
            / "staging"
            / "2026-08-17"
            / "failure-as-fuel-preference-cascade"
            / f"r{round_text}-{self.TOKEN}"
        )
        stage.mkdir(parents=True)
        names = []
        for index in range(1, count + 1):
            name = f"diagnosis-{index:02d}-r{round_text}.md"
            (stage / name).write_text(
                diagnosis_document(index),
                encoding="utf-8",
            )
            names.append(name)
        return stage, names

    def test_receipt_binds_names_sizes_and_digests(self):
        with tempfile.TemporaryDirectory() as td:
            stage, names = self.stage(td)
            receipt = preference_arms.verify_diagnosis_handoff(stage, names)

        self.assertEqual(receipt["factory"], "failure-as-fuel-preference-cascade")
        self.assertEqual(receipt["round"], 11)
        self.assertEqual(receipt["version"], preference_arms.HANDOFF_RECEIPT_VERSION)
        self.assertEqual(receipt["reservation_token"], self.TOKEN)
        self.assertEqual(
            [item["name"] for item in receipt["diagnosis_files"]],
            names,
        )
        self.assertTrue(all(item["bytes"] > 0 for item in receipt["diagnosis_files"]))
        self.assertTrue(all(len(item["sha256"]) == 64 for item in receipt["diagnosis_files"]))

    def test_cli_emits_the_same_bounded_receipt(self):
        with tempfile.TemporaryDirectory() as td:
            stage, names = self.stage(td)
            argv = ["verify-handoff", str(stage)]
            for name in names:
                argv.extend(("--file", name))
            code, out, err = run_cli(argv)

        self.assertEqual(code, 0)
        self.assertEqual(err, "")
        receipt = json.loads(out)
        self.assertEqual(receipt["round"], 11)
        self.assertEqual(
            [item["name"] for item in receipt["diagnosis_files"]],
            names,
        )
        self.assertNotIn("root cause", out)

    def test_cli_exclusively_writes_the_canonical_receipt(self):
        with tempfile.TemporaryDirectory() as td:
            stage, names = self.stage(td)
            argv = ["verify-handoff", str(stage)]
            for name in names:
                argv.extend(("--file", name))
            argv.append("--write-receipt")

            code, out, err = run_cli(argv)
            receipt_path = stage / preference_arms.diagnosis_receipt_filename(11)
            persisted = json.loads(receipt_path.read_text())
            receipt_mode = receipt_path.stat().st_mode
            second_code, _, second_err = run_cli(argv)

        self.assertEqual(code, 0)
        self.assertEqual(err, "")
        self.assertEqual(persisted, json.loads(out))
        self.assertEqual(receipt_mode & 0o222, 0)
        self.assertEqual(second_code, 1)
        self.assertIn("cannot be created exclusively", second_err)

    def test_receipt_must_precede_session_b_outputs(self):
        with tempfile.TemporaryDirectory() as td:
            stage, names = self.stage(td)
            (stage / "batch-r11.jsonl").write_text("{}\n", encoding="utf-8")

            with self.assertRaisesRegex(
                preference_arms.PreferenceArmsError,
                "before Session B outputs",
            ):
                preference_arms.write_diagnosis_handoff_receipt(stage, names)

            self.assertFalse((stage / preference_arms.diagnosis_receipt_filename(11)).exists())

    def test_session_b_output_race_removes_the_uncommitted_receipt(self):
        with tempfile.TemporaryDirectory() as td:
            stage, names = self.stage(td)
            receipt_name = preference_arms.diagnosis_receipt_filename(11)
            real_open = os.open

            def create_batch_before_receipt(path, flags, *args, **kwargs):
                if Path(path).name == receipt_name:
                    (stage / "batch-r11.jsonl").write_text("{}\n", encoding="utf-8")
                return real_open(path, flags, *args, **kwargs)

            with (
                mock.patch.object(
                    preference_arms.os,
                    "open",
                    side_effect=create_batch_before_receipt,
                ),
                self.assertRaisesRegex(
                    preference_arms.PreferenceArmsError,
                    "appeared during diagnosis receipt creation",
                ),
            ):
                preference_arms.write_diagnosis_handoff_receipt(stage, names)

            self.assertFalse((stage / receipt_name).exists())

    def test_parent_swap_cannot_redirect_receipt_creation(self):
        with tempfile.TemporaryDirectory() as td:
            stage, names = self.stage(td)
            receipt_name = preference_arms.diagnosis_receipt_filename(11)
            parked = Path(td) / "parked-stage"
            outside = Path(td) / "outside"
            outside.mkdir()
            real_open = os.open

            def swap_parent_before_receipt(path, flags, *args, **kwargs):
                if Path(path).name == receipt_name:
                    stage.rename(parked)
                    stage.symlink_to(outside, target_is_directory=True)
                return real_open(path, flags, *args, **kwargs)

            with (
                mock.patch.object(
                    preference_arms.os,
                    "open",
                    side_effect=swap_parent_before_receipt,
                ),
                self.assertRaisesRegex(
                    preference_arms.PreferenceArmsError,
                    "staging directory changed",
                ),
            ):
                preference_arms.write_diagnosis_handoff_receipt(stage, names)

            self.assertFalse((outside / receipt_name).exists())
            self.assertFalse((parked / receipt_name).exists())

    def test_stage_path_swap_after_verification_cannot_rebind_receipt(self):
        with tempfile.TemporaryDirectory() as td:
            stage, names = self.stage(td)
            receipt_name = preference_arms.diagnosis_receipt_filename(11)
            parked = Path(td) / "parked-stage"
            real_verify = preference_arms.verify_diagnosis_handoff

            def swap_after_verification(*args, **kwargs):
                receipt = real_verify(*args, **kwargs)
                stage.rename(parked)
                stage.mkdir()
                return receipt

            with (
                mock.patch.object(
                    preference_arms,
                    "verify_diagnosis_handoff",
                    side_effect=swap_after_verification,
                ),
                self.assertRaisesRegex(
                    preference_arms.PreferenceArmsError,
                    "staging directory changed",
                ),
            ):
                preference_arms.write_diagnosis_handoff_receipt(stage, names)

            self.assertFalse((stage / receipt_name).exists())
            self.assertFalse((parked / receipt_name).exists())

    def test_late_session_b_output_is_caught_by_finalization_scan(self):
        with tempfile.TemporaryDirectory() as td:
            stage, names = self.stage(td)
            receipt_name = preference_arms.diagnosis_receipt_filename(11)
            real_require = preference_arms._require_open_directory_identity
            identity_checks = 0

            def create_batch_after_post_create_scan(*args, **kwargs):
                nonlocal identity_checks
                real_require(*args, **kwargs)
                identity_checks += 1
                if identity_checks == 4:
                    (stage / "batch-r11.jsonl").write_text("{}\n", encoding="utf-8")

            with (
                mock.patch.object(
                    preference_arms,
                    "_require_open_directory_identity",
                    side_effect=create_batch_after_post_create_scan,
                ),
                self.assertRaisesRegex(
                    preference_arms.PreferenceArmsError,
                    "appeared during diagnosis receipt finalization",
                ),
            ):
                preference_arms.write_diagnosis_handoff_receipt(stage, names)

            self.assertFalse((stage / receipt_name).exists())

    def test_failed_document_validation_leaves_no_receipt(self):
        with tempfile.TemporaryDirectory() as td:
            stage, names = self.stage(td)
            (stage / names[0]).write_text("# Diagnosis\n", encoding="utf-8")

            with self.assertRaises(preference_arms.PreferenceArmsError):
                preference_arms.write_diagnosis_handoff_receipt(stage, names)

            self.assertFalse((stage / preference_arms.diagnosis_receipt_filename(11)).exists())

    def test_persisted_receipt_revalidates_against_the_bound_bytes(self):
        with tempfile.TemporaryDirectory() as td:
            stage, names = self.stage(td)
            receipt = preference_arms.write_diagnosis_handoff_receipt(stage, names)

            validated = preference_arms.validate_diagnosis_handoff_receipt(
                stage,
                preference_arms.ReceiptExpectation(
                    factory="failure-as-fuel-preference-cascade",
                    round_number=11,
                    staging_dir=stage,
                    reservation_token=self.TOKEN,
                    expected_count=3,
                ),
            )

        self.assertEqual(validated, receipt)

    def test_persisted_receipt_detects_post_verification_tampering(self):
        with tempfile.TemporaryDirectory() as td:
            stage, names = self.stage(td)
            preference_arms.write_diagnosis_handoff_receipt(stage, names)
            (stage / names[1]).write_text(
                diagnosis_document(2, root_cause="Changed after verification."),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(
                preference_arms.PreferenceArmsError,
                "does not match receipt",
            ):
                preference_arms.validate_diagnosis_handoff_receipt(
                    stage,
                    preference_arms.ReceiptExpectation(
                        factory="failure-as-fuel-preference-cascade",
                        round_number=11,
                        staging_dir=stage,
                        reservation_token=self.TOKEN,
                        expected_count=3,
                    ),
                )

    def test_invalid_receipt_name_is_rejected_before_any_outside_read(self):
        with tempfile.TemporaryDirectory() as td:
            stage, names = self.stage(td)
            preference_arms.write_diagnosis_handoff_receipt(stage, names)
            outside = Path(td) / "outside.md"
            outside.write_text(diagnosis_document(1), encoding="utf-8")
            receipt_path = stage / preference_arms.diagnosis_receipt_filename(11)
            receipt = json.loads(receipt_path.read_text())
            receipt["diagnosis_files"][0]["name"] = str(outside)
            receipt_path.chmod(0o600)
            receipt_path.write_text(json.dumps(receipt) + "\n", encoding="utf-8")
            receipt_path.chmod(0o400)

            with (
                mock.patch.object(preference_arms.os, "open", wraps=os.open) as open_spy,
                self.assertRaisesRegex(
                    preference_arms.PreferenceArmsError,
                    "invalid name",
                ),
            ):
                preference_arms.validate_diagnosis_handoff_receipt(
                    stage,
                    preference_arms.ReceiptExpectation(
                        factory="failure-as-fuel-preference-cascade",
                        round_number=11,
                        staging_dir=stage,
                        reservation_token=self.TOKEN,
                        expected_count=3,
                    ),
                )

            opened_paths = [Path(call.args[0]) for call in open_spy.call_args_list]
            self.assertNotIn(outside, opened_paths)

    def test_round_one_hundred_handoff_uses_the_transaction_round_range(self):
        with tempfile.TemporaryDirectory() as td:
            stage, names = self.stage(td, round_number=100)
            receipt = preference_arms.verify_diagnosis_handoff(stage, names)

        self.assertEqual(receipt["round"], 100)
        self.assertTrue(all("-r100.md" in name for name in names))

    def test_missing_empty_symlink_and_invalid_utf8_files_fail_closed(self):
        mutations = ("missing", "empty", "whitespace", "symlink", "invalid-utf8")
        for mutation in mutations:
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as td:
                stage, names = self.stage(td)
                target = stage / names[0]
                if mutation == "missing":
                    target.unlink()
                elif mutation == "empty":
                    target.write_bytes(b"")
                elif mutation == "whitespace":
                    target.write_text(" \n\t", encoding="utf-8")
                elif mutation == "symlink":
                    target.unlink()
                    real = stage / "not-allowlisted.txt"
                    real.write_text("diagnosis", encoding="utf-8")
                    target.symlink_to(real.name)
                else:
                    target.write_bytes(b"\xff\xfe")

                with self.assertRaises(preference_arms.PreferenceArmsError):
                    preference_arms.verify_diagnosis_handoff(stage, names)

    def test_full_rejected_trajectory_cannot_enter_the_diagnosis_bridge(self):
        malicious = {
            "extra-fence": diagnosis_document(1)
            + "\n```json\n"
            + json.dumps({"executed_action": {"action": "copied"}})
            + "\n```\n",
            "extra-context-key": diagnosis_document(1).replace(
                '"state":', '"executed_action": {"action": "copied"}, "state":', 1
            ),
            "serialized-narrative": diagnosis_document(
                1,
                root_cause='The copied payload was {"executed_action": {"action": "unsafe"}}.',
            ),
        }
        for label, document in malicious.items():
            with self.subTest(label=label), tempfile.TemporaryDirectory() as td:
                stage, names = self.stage(td)
                (stage / names[0]).write_text(document, encoding="utf-8")

                with self.assertRaisesRegex(
                    preference_arms.PreferenceArmsError,
                    "(?:code fence|shared context keys|serialized trajectory mapping|object syntax)",
                ):
                    preference_arms.verify_diagnosis_handoff(stage, names)

    def test_nested_encoded_and_structured_payload_channels_fail_closed(self):
        nested = {"leaf": "safe"}
        for _ in range(preference_arms.MAX_DIAGNOSIS_DEPTH + 2):
            nested = {"nested": nested}
        malicious = {
            "nested-rejected": diagnosis_document(
                1,
                context={
                    "state": {"debug_payload": {"executed_action": {"action": "unsafe"}}},
                    "proposed_action": {"action": "hold"},
                },
            ),
            "case-variant-rejected": diagnosis_document(
                1,
                context={
                    "state": {
                        "Executed_Action": {"action": "unsafe"},
                        "executedAction": {"action": "unsafe"},
                        "Future-Outcome": {"status": "destroyed"},
                        "Reward Components": {"safety": -1},
                    },
                    "proposed_action": {"action": "hold"},
                },
            ),
            "serialized-context-string": diagnosis_document(
                1,
                context={
                    "state": {"notes": '"future_outcome": {"success": false}'},
                    "proposed_action": {"action": "hold"},
                },
            ),
            "base64-narrative": diagnosis_document(1, root_cause="base64 " + "A" * 300),
            "yaml-narrative": diagnosis_document(
                1,
                root_cause="executed_action = unsafe\nfuture_outcome = failed",
            ),
            "homoglyph-yaml-narrative": diagnosis_document(
                1,
                root_cause="executed_actіon = unsafe\nfuture_outcοme = failed",
            ),
            "raw-html": diagnosis_document(1, root_cause="<!-- hidden trajectory -->"),
            "nonfinite-context": diagnosis_document(1).replace('"case": 1', '"case": 1e999', 1),
            "excessive-depth": diagnosis_document(
                1,
                context={
                    "state": nested,
                    "proposed_action": {"action": "hold"},
                },
            ),
        }
        for label, document in malicious.items():
            with self.subTest(label=label), tempfile.TemporaryDirectory() as td:
                stage, names = self.stage(td)
                (stage / names[0]).write_text(document, encoding="utf-8")

                with self.assertRaises(preference_arms.PreferenceArmsError):
                    preference_arms.verify_diagnosis_handoff(stage, names)

    def test_malformed_bounded_diagnosis_structure_fails_closed(self):
        valid = diagnosis_document(1)
        malformed = {
            "wrong-heading": valid.replace("## Root cause", "## Failure analysis", 1),
            "duplicate-context-key": valid.replace('"state":', '"state": {}, "state":', 1),
            "nonfinite-target": valid.replace('"total": 0.75', '"total": NaN', 1),
            "unreconciled-target": valid.replace('"total": 0.75', '"total": 0.5', 1),
            "oversized-prose": diagnosis_document(
                1,
                root_cause="x" * (preference_arms.MAX_DIAGNOSIS_NARRATIVE_CHARS + 1),
            ),
        }
        for label, document in malformed.items():
            with self.subTest(label=label), tempfile.TemporaryDirectory() as td:
                stage, names = self.stage(td)
                (stage / names[0]).write_text(document, encoding="utf-8")

                with self.assertRaises(preference_arms.PreferenceArmsError):
                    preference_arms.verify_diagnosis_handoff(stage, names)

    def test_traversal_duplicates_wrong_round_and_gaps_fail_closed(self):
        with tempfile.TemporaryDirectory() as td:
            stage, names = self.stage(td)
            invalid_lists = (
                ["../diagnosis-01-r11.md"],
                [names[0], names[0]],
                ["diagnosis-01-r10.md"],
                [names[0], names[2]],
            )
            for invalid in invalid_lists:
                with (
                    self.subTest(files=invalid),
                    self.assertRaises(preference_arms.PreferenceArmsError),
                ):
                    preference_arms.verify_diagnosis_handoff(stage, invalid)

    def test_cli_reports_a_missing_file_without_a_traceback(self):
        with tempfile.TemporaryDirectory() as td:
            stage, names = self.stage(td)
            (stage / names[1]).unlink()
            argv = ["verify-handoff", str(stage)]
            for name in names:
                argv.extend(("--file", name))
            code, out, err = run_cli(argv)

        self.assertEqual(code, 1)
        self.assertEqual(out, "")
        self.assertIn("diagnosis handoff verification failed", err)

if __name__ == "__main__":
    unittest.main()
