#!/usr/bin/env python3
"""Source scan, writer, command line, and lane boundary for trajectory pairs.

The per-record keep / repair / reject contract lives in
``test_curate_trajectory_preferences``. These tests pin what the gate does with
a *corpus*: how it reads sources, what provenance the manifest carries, where
it refuses to write, and which records it hands back to
``pipelines/curate_preferences.py``.
"""

import io
import json
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from trajectory_preference_support import (
    FIXTURE_DIR,
    PIPELINES,
    PURITY_FIXTURES,
    same_state_pair,
    step,
    trajectory_pair,
)

import curate_preferences  # noqa: E402
import curate_trajectory_preferences as ctp  # noqa: E402


class LaneBoundary(unittest.TestCase):
    def test_same_state_pairs_are_skipped_not_judged(self):
        decision = ctp.curate_trajectory_pair(same_state_pair())

        self.assertEqual(decision.action, ctp.ACTION_SKIPPED)
        self.assertEqual(decision.reason_codes, (ctp.REASON_SAME_STATE_SCHEMA,))
        self.assertIsNone(decision.record)

    def test_non_preference_records_are_skipped(self):
        episode = {"id": "mill-1", "goal": "Rebuild the index.", "steps": [step(1, "b")]}

        decision = ctp.curate_trajectory_pair(episode)

        self.assertEqual(decision.action, ctp.ACTION_SKIPPED)
        self.assertEqual(decision.reason_codes, (ctp.REASON_NOT_A_PAIR,))

    def test_committed_fable_corpus_is_entirely_out_of_scope_here(self):
        # The Fable FFPC corpus must never land in this lane's denominator.
        run = ctp.curate_source(PURITY_FIXTURES)

        self.assertEqual(run.summary["trajectory_pairs_considered"], 0)
        self.assertEqual(run.records, ())
        self.assertEqual(run.summary["skipped_same_state_pairs"], run.summary["json_records_seen"])

    def test_same_state_gate_names_trajectory_pairs_out_of_scope(self):
        # Lives here because it pins the boundary this lane depends on: the
        # Fable gate must report a schema mismatch, not a malformed record.
        decision = curate_preferences.curate_preference_record(trajectory_pair())

        self.assertEqual(decision.action, curate_preferences.ACTION_EXCLUDED)
        self.assertEqual(
            decision.classification,
            curate_preferences.CLASSIFICATION_TRAJECTORY_PAIR,
        )
        self.assertEqual(decision.reason_codes, (curate_preferences.REASON_TRAJECTORY_PAIR,))

    def test_same_state_gate_still_flags_genuinely_malformed_pairs(self):
        decision = curate_preferences.curate_preference_record(
            {"id": "bad", "chosen": {}, "rejected": {}, "reward_delta": {}}
        )

        self.assertEqual(decision.reason_codes, ("PREFERENCE_CONTEXT_MISSING_OR_INVALID",))


class SourceScan(unittest.TestCase):
    def test_fixture_corpus_summary_separates_every_bucket(self):
        run = ctp.curate_source(FIXTURE_DIR)
        summary = run.summary

        self.assertEqual(summary["json_records_seen"], 3)
        self.assertEqual(summary["trajectory_pairs_considered"], 2)
        self.assertEqual(summary["retained_pairs"], 1)
        self.assertEqual(summary["excluded_pairs"], 1)
        self.assertEqual(summary["prefix_overlap_absent_pairs"], 1)
        self.assertEqual(summary["branch_label_only_first_step_pairs"], 1)
        self.assertEqual(summary["skipped_non_preference_records"], 1)
        self.assertEqual(summary["skipped_same_state_pairs"], 0)
        self.assertEqual(summary["retained_gate_pass_pct"], 50.0)
        self.assertEqual(len(run.records), 1)
        self.assertEqual(len(run.manifest), 3)

    def test_manifest_entries_carry_source_and_output_provenance(self):
        run = ctp.curate_source(FIXTURE_DIR)
        retained = run.manifest[0]

        self.assertEqual(retained["source_path"], "batch-r01.jsonl")
        self.assertEqual(retained["source_line"], 1)
        self.assertEqual(retained["action"], ctp.ACTION_RETAINED)
        self.assertEqual(retained["transform"]["name"], ctp.TRANSFORM_NAME)
        self.assertEqual(retained["output_id"], retained["source_record_id"])
        self.assertEqual(len(retained["source_sha256"]), 64)
        self.assertEqual(len(retained["output_sha256"]), 64)
        self.assertEqual(retained["prefix_overlap"]["shared_steps"], 2)
        self.assertEqual(retained["pair_validation_errors"], [])
        self.assertEqual(retained["side_validation_errors"], {})

    def test_manifest_surfaces_each_side_episode_shape_error(self):
        source_record = trajectory_pair("malformed-sides")
        source_record["chosen"]["outcome"] = 1
        source_record["rejected"]["steps"] = ["not-a-step"]
        with tempfile.TemporaryDirectory() as td:
            source = Path(td) / "batch-r01.jsonl"
            source.write_text(json.dumps(source_record) + "\n")

            entry = ctp.curate_source(source).manifest[0]

        self.assertEqual(entry["action"], ctp.ACTION_EXCLUDED)
        self.assertIn("chosen", entry["side_validation_errors"])
        self.assertIn("rejected", entry["side_validation_errors"])
        self.assertTrue(
            any(
                "outcome must be a non-empty string" in error
                for error in entry["side_validation_errors"]["chosen"]
            )
        )
        self.assertTrue(
            any(
                "must be an object" in error
                for error in entry["side_validation_errors"]["rejected"]
            )
        )

    def test_scan_does_not_touch_the_source_corpus(self):
        path = FIXTURE_DIR / "batch-r01.jsonl"
        before = path.read_bytes()

        ctp.curate_source(FIXTURE_DIR)

        self.assertEqual(path.read_bytes(), before)

    def test_malformed_json_fails_loudly(self):
        with tempfile.TemporaryDirectory() as td:
            source = Path(td) / "batch-r01.jsonl"
            source.write_text('{"id": "x"}\nnot json\n')

            with self.assertRaises(ctp.TrajectoryCurationError):
                ctp.curate_source(source)

    def test_nan_is_rejected_at_parse_time(self):
        with tempfile.TemporaryDirectory() as td:
            source = Path(td) / "batch-r01.jsonl"
            source.write_text('{"id": "x", "reward": NaN}\n')

            with self.assertRaises(ctp.TrajectoryCurationError):
                ctp.curate_source(source)

    def test_finite_token_overflow_is_rejected_at_parse_time(self):
        record = trajectory_pair("finite-overflow")
        record["meta"] = {"unchecked_score": 0.5}
        payload = ctp.canonical_json(record).replace(
            '"unchecked_score":0.5',
            '"unchecked_score":1e999',
        )
        self.assertIn('"unchecked_score":1e999', payload)

        with tempfile.TemporaryDirectory() as td:
            source = Path(td) / "batch-r01.jsonl"
            source.write_text(payload + "\n")

            with self.assertRaisesRegex(
                ctp.TrajectoryCurationError,
                "non-finite JSON number 1e999",
            ):
                ctp.curate_source(source)

    def test_non_jsonl_source_file_is_refused(self):
        with tempfile.TemporaryDirectory() as td:
            source = Path(td) / "batch-r01.json"
            source.write_text("{}\n")

            with self.assertRaises(ctp.TrajectoryCurationError):
                ctp.curate_source(source)


class WriteDestinations(unittest.TestCase):
    def test_curate_writes_pairs_and_manifest_without_clobbering(self):
        with tempfile.TemporaryDirectory() as td:
            destination = Path(td)
            output = destination / "pairs.jsonl"
            manifest = destination / "manifest.jsonl"

            with redirect_stdout(io.StringIO()):
                code = ctp.main(
                    [
                        "curate",
                        str(FIXTURE_DIR),
                        "--output",
                        str(output),
                        "--manifest",
                        str(manifest),
                    ]
                )

            self.assertEqual(code, 0)
            written = output.read_text().splitlines()
            self.assertEqual(len(written), 1)
            emitted = json.loads(written[0])
            self.assertTrue(ctp.pair_passes_gate(emitted))
            self.assertEqual(len(manifest.read_text().splitlines()), 3)

            # Second run must refuse rather than overwrite.
            with redirect_stdout(io.StringIO()):
                rerun = ctp.main(
                    [
                        "curate",
                        str(FIXTURE_DIR),
                        "--output",
                        str(output),
                        "--manifest",
                        str(manifest),
                    ]
                )
            self.assertEqual(rerun, 1)

    def test_output_hash_matches_the_written_line(self):
        with tempfile.TemporaryDirectory() as td:
            destination = Path(td)
            output = destination / "pairs.jsonl"
            manifest = destination / "manifest.jsonl"
            with redirect_stdout(io.StringIO()):
                ctp.main(
                    [
                        "curate",
                        str(FIXTURE_DIR),
                        "--output",
                        str(output),
                        "--manifest",
                        str(manifest),
                    ]
                )
            entry = next(
                json.loads(line)
                for line in manifest.read_text().splitlines()
                if json.loads(line)["output_sha256"]
            )

            self.assertEqual(
                ctp.sha256_hex(output.read_text().splitlines()[0].encode("utf-8")),
                entry["output_sha256"],
            )

    def test_destinations_under_outputs_raw_are_refused(self):
        with tempfile.TemporaryDirectory() as td:
            raw = Path(td) / "outputs" / "raw" / "2026-08-19-agentic"
            raw.mkdir(parents=True)
            output = raw / "pairs.jsonl"
            manifest = Path(td) / "manifest.jsonl"

            with redirect_stdout(io.StringIO()):
                code = ctp.main(
                    [
                        "curate",
                        str(FIXTURE_DIR),
                        "--output",
                        str(output),
                        "--manifest",
                        str(manifest),
                    ]
                )

            self.assertEqual(code, 1)
            self.assertFalse(output.exists())
            self.assertFalse(manifest.exists())


class CommandLine(unittest.TestCase):
    def test_scan_json_reports_summary_and_decisions(self):
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            code = ctp.main(["scan", str(FIXTURE_DIR), "--json"])
        payload = json.loads(buffer.getvalue())

        self.assertEqual(code, 0)
        self.assertEqual(payload["summary"]["retained_pairs"], 1)
        self.assertEqual(len(payload["decisions"]), 3)

    def test_scan_human_output_names_every_decision(self):
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            ctp.main(["scan", str(FIXTURE_DIR)])
        text = buffer.getvalue()

        self.assertIn(ctp.REASON_PREFIX_ABSENT, text)
        self.assertIn(ctp.REASON_BRANCH_LABEL_ONLY, text)
        self.assertIn("Skipped non-preference records: 1", text)

    def test_outcome_agreement_is_off_unless_the_operator_asks_for_it(self):
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            ctp.main(["scan", str(FIXTURE_DIR), "--json"])
        default = json.loads(buffer.getvalue())["summary"]

        buffer = io.StringIO()
        with redirect_stdout(buffer):
            ctp.main(["scan", str(FIXTURE_DIR), "--json", "--enforce-outcome-agreement"])
        strict = json.loads(buffer.getvalue())["summary"]

        # The summary records which policy produced it, so two scans of one
        # corpus are never mistaken for each other in an audit.
        self.assertFalse(default["enforce_outcome_agreement"])
        self.assertTrue(strict["enforce_outcome_agreement"])

    def test_missing_source_exits_nonzero(self):
        proc = subprocess.run(
            [
                sys.executable,
                str(PIPELINES / "curate_trajectory_preferences.py"),
                "scan",
                str(FIXTURE_DIR / "absent"),
            ],
            capture_output=True,
            text=True,
        )

        self.assertEqual(proc.returncode, 1)
        self.assertIn("source does not exist", proc.stderr)


if __name__ == "__main__":
    unittest.main()
