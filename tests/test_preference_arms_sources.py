#!/usr/bin/env python3
"""Source resolution, and the guarantee that scanning mutates nothing."""

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from preference_arms_support import (  # noqa: E402
    ARM_FIXTURES,
    TWO_SESSION_ROUND,
    first,
    run_cli,
)
import preference_arms  # noqa: E402


# Pinned so a scan that rewrote its own input would fail loudly rather than
# verify itself against a baseline it just produced.
GOLDEN_FIXTURE_SHA256 = {
    "batch-r11.jsonl": "5f24db6543f41782ac61aadfddab707cf5c1cac4249adadaf056d99bbb677a5c",
    "near-verbatim-r11.jsonl": ("3e08181a1aa61772edc9fb780d7ea2a76a0892ffa9451e1e0e14c1898f6e5546"),
    "gate-label-only-r11.jsonl": (
        "75e85ca69792a78c953ab91a4a9585d8b860398317739ffc3a143d711a3aff9c"
    ),
    "single-session-r11.jsonl": (
        "f6c4588141d91bed533f651971f3438cace26dcba1a0c693c29407a3f1c379a2"
    ),
}


class SourceHandling(unittest.TestCase):
    def test_directory_source_scans_every_batch(self):
        scan = preference_arms.scan_source(ARM_FIXTURES)
        self.assertEqual(scan.summary["preference_pairs"], 6)
        self.assertEqual(scan.summary["blocked_pairs"], 3)
        self.assertEqual(
            sorted({d.source_path for d in scan.decisions}),
            [
                "batch-r11.jsonl",
                "gate-label-only-r11.jsonl",
                "near-verbatim-r11.jsonl",
                "single-session-r11.jsonl",
            ],
        )

    def test_non_preference_records_are_skipped_not_gated(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "mixed.jsonl"
            record = first(TWO_SESSION_ROUND)
            path.write_text(
                json.dumps({"id": "solo", "state": {"sim_or_real": "designed"}})
                + "\n"
                + json.dumps(record)
                + "\n",
                encoding="utf-8",
            )
            scan = preference_arms.scan_source(path)
        self.assertEqual(scan.summary["preference_pairs"], 1)
        self.assertEqual(scan.summary["skipped_non_preference_records"], 1)
        self.assertFalse(scan.blocked)

    def test_scan_without_preference_pairs_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "empty.jsonl"
            path.write_text(
                json.dumps({"id": "solo", "state": {"sim_or_real": "designed"}}) + "\n",
                encoding="utf-8",
            )
            code, _, err = run_cli(["scan", str(path)])
        self.assertEqual(code, 1)
        self.assertIn("no preference pairs", err)

    def test_missing_and_non_jsonl_sources_are_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            missing = Path(td) / "absent.jsonl"
            with self.assertRaises(preference_arms.PreferenceArmsError):
                preference_arms.scan_source(missing)
            wrong = Path(td) / "batch.json"
            wrong.write_text("{}\n", encoding="utf-8")
            with self.assertRaises(preference_arms.PreferenceArmsError):
                preference_arms.scan_source(wrong)
            empty_dir = Path(td) / "empty-dir"
            empty_dir.mkdir()
            with self.assertRaises(preference_arms.PreferenceArmsError):
                preference_arms.scan_source(empty_dir)

    def test_unreadable_json_is_reported_with_its_location(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "broken.jsonl"
            path.write_text("{not json}\n", encoding="utf-8")
            with self.assertRaises(preference_arms.PreferenceArmsError) as ctx:
                preference_arms.scan_source(path)
        self.assertIn("broken.jsonl:1", str(ctx.exception))

    def test_blank_lines_are_skipped(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "padded.jsonl"
            path.write_text(
                "\n" + json.dumps(first(TWO_SESSION_ROUND)) + "\n\n",
                encoding="utf-8",
            )
            scan = preference_arms.scan_source(path)
        self.assertEqual(scan.summary["preference_pairs"], 1)
        self.assertFalse(scan.blocked)

    def test_out_of_range_min_distance_is_refused(self):
        for value in ("1.0", "-0.1", "nan", "not-a-number"):
            with self.subTest(value), self.assertRaises(SystemExit):
                run_cli(["scan", str(TWO_SESSION_ROUND), "--min-distance", value])

    def test_cli_reports_an_unreadable_source_instead_of_raising(self):
        with tempfile.TemporaryDirectory() as td:
            code, _, err = run_cli(["scan", str(Path(td) / "absent.jsonl")])
        self.assertEqual(code, 1)
        self.assertIn("preference arm gate failed", err)


class ScanIsReadOnly(unittest.TestCase):
    def test_fixtures_match_pinned_digests_after_a_full_scan(self):
        preference_arms.scan_source(ARM_FIXTURES)
        for name, digest in GOLDEN_FIXTURE_SHA256.items():
            with self.subTest(name):
                self.assertEqual(
                    hashlib.sha256((ARM_FIXTURES / name).read_bytes()).hexdigest(),
                    digest,
                )

    def test_check_pair_does_not_mutate_its_record(self):
        record = first(TWO_SESSION_ROUND)
        before = json.dumps(record, sort_keys=True)
        preference_arms.check_pair(record, source_path="memory.jsonl", source_line=1)
        self.assertEqual(json.dumps(record, sort_keys=True), before)

    def test_json_report_is_serializable_and_complete(self):
        code, out, _ = run_cli(["scan", str(TWO_SESSION_ROUND), "--json"])
        self.assertEqual(code, 0)
        report = json.loads(out)
        self.assertEqual(len(report["decisions"]), 3)
        self.assertEqual(report["summary"]["gate"]["name"], preference_arms.GATE_NAME)
        self.assertFalse(any(d["blocked"] for d in report["decisions"]))

if __name__ == "__main__":
    unittest.main()
