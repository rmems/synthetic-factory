#!/usr/bin/env python3
"""Promotion CLI regressions for fail-closed quality-gate preflight."""

import contextlib
import io
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

REPO = Path(__file__).resolve().parents[1]
PIPELINES = REPO / "pipelines"
FIXTURES = Path(__file__).resolve().parent / "fixtures"
PROMOTER = PIPELINES / "promote.py"
sys.path.insert(0, str(PIPELINES))

import promote  # noqa: E402
import quality_gate  # noqa: E402


def _record():
    return {
        "state": {"sim_or_real": "real", "domain": "test"},
        "proposed_action": {"action_type": "noop"},
        "safety_decision": {"decision": "ACCEPT", "rationale": "ok"},
        "executed_action": {"action_type": "noop"},
        "future_outcome": {"success": "full"},
        "reward_components": {"task_progress": 0.4, "safety": 0.6, "total": 1.0},
        "meta": {"id": "t-001"},
    }


def _write_jsonl(path, records):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(record) + "\n" for record in records))


def _cli(args):
    return subprocess.run(
        [sys.executable, str(PROMOTER), *args],
        cwd=str(REPO),
        capture_output=True,
        text=True,
    )


class TestPromoteQualityGatePreflight(unittest.TestCase):
    def _assert_cli_threshold_rejected(self, threshold):
        with tempfile.TemporaryDirectory() as td:
            raw = Path(td) / "raw"
            cleaned = Path(td) / "cleaned"
            _write_jsonl(raw / "f" / "a.jsonl", [_record()])

            proc = _cli([str(raw), str(cleaned), "--threshold", threshold])

            self.assertEqual(proc.returncode, 2, proc.stderr)
            expected = f"[{quality_gate.EMBEDDING_MIN_THRESHOLD:.4f}, 1)"
            self.assertIn(expected, proc.stderr)
            self.assertFalse(cleaned.exists())

    def test_sub_lsh_threshold_is_rejected_before_any_output_is_created(self):
        """A threshold below the LSH soundness floor must not promote first."""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            raw = root / "raw"
            cleaned = root / "cleaned"
            manifest = root / "sidecars" / "quality-manifest.json"
            raw.mkdir()
            stderr = io.StringIO()

            with mock.patch.object(promote, "promote_run") as promote_run:
                with contextlib.redirect_stderr(stderr):
                    with self.assertRaises(SystemExit) as raised:
                        promote.main(
                            [
                                str(raw),
                                str(cleaned),
                                "--quality-manifest",
                                str(manifest),
                                "--threshold",
                                "0.5",
                            ]
                        )

            self.assertEqual(raised.exception.code, 2)
            self.assertIn("threshold must be a finite cosine", stderr.getvalue())
            self.assertIn("0.5", stderr.getvalue())
            promote_run.assert_not_called()
            self.assertFalse(cleaned.exists())
            self.assertFalse(manifest.exists())

    def test_cli_rejects_threshold_one_before_writing_destination(self):
        self._assert_cli_threshold_rejected("1.0")

    def test_cli_rejects_a_negative_threshold_before_writing_destination(self):
        self._assert_cli_threshold_rejected("-0.5")


class TestPromoteGateFlags(unittest.TestCase):
    """Pin every quality-gate flag through the promotion CLI."""

    EMBEDDING_BATCH = FIXTURES / "embedding-dedup" / "batch-r01.jsonl"

    def _run(self, td, *flags):
        raw = Path(td) / "raw"
        cleaned = Path(td) / "cleaned"
        raw.mkdir(parents=True)
        (raw / "f").mkdir()
        (raw / "f" / "batch-r01.jsonl").write_bytes(
            self.EMBEDDING_BATCH.read_bytes()
        )
        proc = _cli([str(raw), str(cleaned), *flags])
        manifest = cleaned / "quality-manifest.json"
        report = json.loads(manifest.read_text()) if manifest.is_file() else None
        return proc, report

    def test_default_flags_block_on_the_near_duplicate_pair(self):
        with tempfile.TemporaryDirectory() as td:
            proc, report = self._run(td)

        self.assertEqual(proc.returncode, 1, proc.stderr)
        self.assertTrue(report["blocked"])
        self.assertEqual(report["threshold"], quality_gate.DEFAULT_EMBEDDING_THRESHOLD)

    def test_threshold_flag_unblocks_the_pair_through_promote(self):
        with tempfile.TemporaryDirectory() as td:
            proc, report = self._run(td, "--threshold", "0.999")

        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertFalse(report["blocked"])
        self.assertEqual(report["threshold"], 0.999)
        self.assertEqual(report["embedding"]["threshold"], 0.999)

    def test_no_embedding_dedup_flag_reaches_the_gate(self):
        with tempfile.TemporaryDirectory() as td:
            proc, report = self._run(td, "--no-embedding-dedup")

        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertFalse(report["blocked"])
        self.assertFalse(report["embedding"]["enabled"])

    def test_max_embedding_pairs_flag_fails_closed_through_promote(self):
        records = [
            {
                "id": f"coding-{index}",
                "goal": "repair the same queue consumer and verify every retry",
                "outcome": f"retry-pass-{index}",
                "meta": {"factory": "agentic-coding-trajectory-factory"},
            }
            for index in range(3)
        ]
        with tempfile.TemporaryDirectory() as td:
            raw = Path(td) / "raw"
            cleaned = Path(td) / "cleaned"
            _write_jsonl(raw / "f" / "a.jsonl", records)

            proc = _cli(
                [
                    str(raw),
                    str(cleaned),
                    "--max-embedding-pairs",
                    "1",
                    "--max-synthetic-ratio",
                    "1.0",
                ]
            )
            report = json.loads((cleaned / "quality-manifest.json").read_text())

        self.assertEqual(proc.returncode, 1, proc.stderr)
        self.assertTrue(report["blocked"])
        self.assertTrue(report["embedding"]["truncated"])
        self.assertTrue(
            any("cannot be certified" in blocker for blocker in report["blockers"])
        )

    def test_mix_ceiling_flag_blocks_a_tree_the_default_policy_passes(self):
        with tempfile.TemporaryDirectory() as td:
            passing, passing_report = self._run(td, "--threshold", "0.999")
        self.assertEqual(passing.returncode, 0, passing.stderr)
        self.assertFalse(passing_report["blocked"])

        with tempfile.TemporaryDirectory() as td:
            proc, report = self._run(
                td, "--threshold", "0.999", "--max-synthetic-ratio", "0.1"
            )

        self.assertEqual(proc.returncode, 1, proc.stderr)
        self.assertTrue(report["blocked"])
        self.assertEqual(report["mix_policy"]["max_synthetic_ratio"], 0.1)

    def test_synthetic_floor_flag_blocks_through_promote(self):
        with tempfile.TemporaryDirectory() as td:
            proc, report = self._run(
                td,
                "--threshold",
                "0.999",
                "--min-synthetic-ratio",
                "0.9",
                "--max-synthetic-ratio",
                "1.0",
            )

        self.assertEqual(proc.returncode, 1, proc.stderr)
        self.assertTrue(report["blocked"])
        self.assertEqual(report["mix_policy"]["min_synthetic_ratio"], 0.9)

    def test_every_gate_flag_lands_in_the_manifest(self):
        with tempfile.TemporaryDirectory() as td:
            proc, report = self._run(
                td,
                "--threshold", "0.999",
                "--max-embedding-pairs", "12345",
                "--mix-target", "0.25",
                "--mix-tolerance", "0.10",
                "--max-synthetic-ratio", "0.85",
                "--min-synthetic-ratio", "0.05",
                "--max-unlabeled-ratio", "0.20",
            )

        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(report["threshold"], 0.999)
        self.assertTrue(report["embedding"]["enabled"])
        self.assertEqual(
            report["mix_policy"],
            {
                "target_synthetic_ratio": 0.25,
                "tolerance": 0.10,
                "max_synthetic_ratio": 0.85,
                "min_synthetic_ratio": 0.05,
                "max_unlabeled_ratio": 0.20,
                "blocking": True,
            },
        )

    def test_custom_manifest_destination_is_honoured(self):
        with tempfile.TemporaryDirectory() as td:
            raw = Path(td) / "raw"
            cleaned = Path(td) / "cleaned"
            sidecar = Path(td) / "elsewhere" / "gate.json"
            _write_jsonl(raw / "f" / "a.jsonl", [_record()])

            proc = _cli(
                [
                    str(raw),
                    str(cleaned),
                    "--quality-manifest",
                    str(sidecar),
                    "--max-synthetic-ratio",
                    "1.0",
                ]
            )

            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertTrue(sidecar.is_file())
            self.assertFalse((cleaned / "quality-manifest.json").exists())


if __name__ == "__main__":
    unittest.main()
