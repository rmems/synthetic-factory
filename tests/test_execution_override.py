#!/usr/bin/env python3
"""Tests for execution-override and completion-marker verification blocks."""

import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "pipelines"))

from gate_fixtures import execution_summary, thalamic, write  # noqa: E402
import round_txn  # noqa: E402


class ExecutionOverrideReason(unittest.TestCase):
    def test_absent_override_stays_absent(self):
        self.assertIsNone(round_txn.normalized_execution_override(None))

    def test_reason_is_whitespace_normalized(self):
        self.assertEqual(
            round_txn.normalized_execution_override(
                "  hil rig\n  offline until Monday  "
            ),
            "hil rig offline until Monday",
        )

    def test_reason_must_be_written_printable_and_bounded(self):
        for rejected in (
            "",
            "     ",
            "brief",
            "12345678",
            "xxxxxxxx",
            "looks fine",
            "hi there",
            "a bbbbbb",
            "see notes",
            "ok\x00fine because",
            "\u200b" * 8,
            "audit \u202ereason",
            b"bytes reason",
            42,
            True,
            "x" * (round_txn.EXECUTION_OVERRIDE_MAX_CHARS + 1),
        ):
            with self.subTest(rejected=rejected):
                with self.assertRaises(round_txn.TransactionError):
                    round_txn.normalized_execution_override(rejected)

    def test_recorded_override_rejects_non_canonical_markers(self):
        reason = "hil replay rig offline"
        valid_override = {"reason": reason, "waived_inconclusive": 1}
        cases = (
            {"execution_verification": "nope"},
            {"execution_verification": {"override": ["not-a-dict"]}},
            {
                "execution_verification": {
                    "override": {"reason": "  " + reason + "  ", "waived_inconclusive": 1}
                }
            },
            {
                "execution_verification": {
                    "override": {"reason": reason, "waived_inconclusive": 0}
                }
            },
            {
                "execution_verification": {
                    "override": {"reason": reason, "waived_inconclusive": True}
                }
            },
        )
        for manifest in cases:
            with self.subTest(manifest=manifest):
                with self.assertRaises(round_txn.TransactionError):
                    round_txn.recorded_execution_override(manifest)
        self.assertEqual(
            round_txn.recorded_execution_override(
                {"execution_verification": {"override": valid_override}}
            ),
            reason,
        )
        with self.assertRaises(round_txn.TransactionError):
            round_txn.comparable_execution_verification("nope")
        comparable = round_txn.comparable_execution_verification(
            {"gate": "g", "override": dict(valid_override)}
        )
        self.assertNotIn("reason", comparable["override"])
        self.assertEqual(comparable["override"]["waived_inconclusive"], 1)

    def test_verification_summary_rejects_invalid_blocks(self):
        waived = {
            "reason": "hil replay rig offline",
            "waived_inconclusive": 1,
        }
        valid = execution_summary()
        self.assertEqual(
            round_txn.validated_execution_verification_summary(valid), valid
        )
        self.assertEqual(
            round_txn.validated_execution_verification_summary(
                execution_summary(
                    verified=0, inconclusive=1, override=waived
                )
            )["override"]["reason"],
            waived["reason"],
        )
        extra_key = execution_summary()
        extra_key["extra"] = True
        wrong_counts = execution_summary()
        wrong_counts["counts"] = {"verified": 1}
        other_gate = execution_summary()
        other_gate["gate"] = "other.gate"
        not_strict = execution_summary()
        not_strict["strict"] = False
        bool_verified = execution_summary()
        bool_verified["counts"]["verified"] = True
        rejected = (
            "nope",
            extra_key,
            wrong_counts,
            bool_verified,
            execution_summary(verified=-1),
            other_gate,
            not_strict,
            execution_summary(verified=0, inconclusive=0, failed=0),
            execution_summary(failed=1),
            execution_summary(verified=1, inconclusive=1, failed=0),
            execution_summary(verified=0, inconclusive=1, override=None),
            execution_summary(
                verified=0,
                inconclusive=1,
                override={"reason": "hil replay rig offline", "waived_inconclusive": 2},
            ),
            execution_summary(override=waived),
        )
        for summary in rejected:
            with self.subTest(summary=summary):
                with self.assertRaises(round_txn.TransactionError):
                    round_txn.validated_execution_verification_summary(summary)

        # verified+inconclusive != total is a counts-key mismatch on the object
        mismatched = execution_summary()
        mismatched["counts"]["total"] = 3
        with self.assertRaises(round_txn.TransactionError):
            round_txn.validated_execution_verification_summary(mismatched)

    def test_completed_verification_wraps_a_live_gate_failure(self):
        with tempfile.TemporaryDirectory() as td:
            batch = Path(td) / "batch-r01.jsonl"
            write(batch, [thalamic("conflict", rationale="")])
            recorded = execution_summary(
                verified=0,
                inconclusive=1,
                override={
                    "reason": "hil replay rig offline",
                    "waived_inconclusive": 1,
                },
            )
            with self.assertRaisesRegex(
                round_txn.TransactionError,
                "conflicts with committed batch",
            ):
                round_txn.validate_completed_execution_verification(
                    batch, {"execution_verification": recorded}
                )

    def test_historical_semantics_are_not_rederived_under_new_rules(self):
        with tempfile.TemporaryDirectory() as td:
            batch = Path(td) / "batch-r01.jsonl"
            write(batch, [thalamic("historical-semantics")])
            recorded = execution_summary()
            recorded["semantics_version"] = 1
            with mock.patch.object(round_txn, "EXECUTION_VERIFIER_SEMANTICS_VERSION", 2):
                with mock.patch.object(
                    round_txn, "execution_gate", side_effect=AssertionError("rederived")
                ):
                    round_txn.validate_completed_execution_verification(
                        batch,
                        {"execution_verification": recorded, "records": 1},
                    )

    def test_historical_semantics_total_must_match_manifest_records(self):
        with tempfile.TemporaryDirectory() as td:
            batch = Path(td) / "batch-r01.jsonl"
            write(
                batch,
                [
                    thalamic("historical-a"),
                    thalamic("historical-b"),
                    thalamic("historical-c"),
                ],
            )
            recorded = execution_summary(verified=1)
            recorded["semantics_version"] = 1
            with mock.patch.object(round_txn, "EXECUTION_VERIFIER_SEMANTICS_VERSION", 2):
                with self.assertRaisesRegex(
                    round_txn.TransactionError,
                    "execution verification total does not match committed records",
                ):
                    round_txn.validate_completed_execution_verification(
                        batch,
                        {"execution_verification": recorded, "records": 3},
                    )

    def test_replace_json_atomically_rejects_unsafe_markers(self):
        with tempfile.TemporaryDirectory() as td:
            missing = Path(td) / "ROUND-r01.publishing.json"
            with self.assertRaisesRegex(
                round_txn.TransactionError, "unsafe publishing marker"
            ):
                round_txn.replace_json_atomically(missing, {"ok": True})
            link = Path(td) / "ROUND-r01.link.json"
            link.symlink_to(Path(td) / "missing-target")
            with self.assertRaisesRegex(
                round_txn.TransactionError, "unsafe publishing marker"
            ):
                round_txn.replace_json_atomically(link, {"ok": True})



if __name__ == "__main__":
    unittest.main()
