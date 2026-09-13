#!/usr/bin/env python3
"""Leftover-mill records never enter a preference pair denominator."""

import json
import tempfile
import unittest
from pathlib import Path

from preference_test_support import (  # noqa: E402
    leftover_mill_episode,
    pair,
    write_jsonl,
)
import curate_preferences  # noqa: E402


class LeftoverMillQuarantine(unittest.TestCase):
    """Leftover-mill records are excluded and named, never silently dropped."""

    def _run(self, records):
        with tempfile.TemporaryDirectory() as td:
            source = Path(td) / "source"
            source.mkdir()
            write_jsonl(source / "batch-r723.jsonl", records)
            return curate_preferences.curate_source(source)

    def test_episode_in_a_preference_tree_is_quarantined_not_counted(self):
        run = self._run(
            [
                leftover_mill_episode("dbc-r723-buildah-layers-vfs-id-leftover"),
                pair("crp-r723-real-pair"),
            ]
        )

        summary = run.summary
        self.assertEqual(summary["json_records_seen"], 2)
        self.assertEqual(summary["preference_records"], 1)
        self.assertEqual(summary["skipped_non_preference_records"], 1)
        self.assertEqual(summary["leftover_mill_records"], 1)
        self.assertEqual(summary["leftover_mill_kinds"], {"episode": 1})
        # The pair denominator never absorbs the mill record.
        self.assertEqual(summary["retained_pairs"], 1)
        self.assertEqual(len(run.records), 1)
        self.assertEqual(run.records[0]["id"], "crp-r723-real-pair")

        quarantined = [
            entry
            for entry in run.manifest
            if entry["action"] == curate_preferences.ACTION_QUARANTINED
        ]
        self.assertEqual(len(quarantined), 1)
        entry = quarantined[0]
        self.assertEqual(entry["source_path"], "batch-r723.jsonl")
        self.assertEqual(entry["source_line"], 1)
        self.assertEqual(entry["source_record_id"], "dbc-r723-buildah-layers-vfs-id-leftover")
        self.assertEqual(entry["classification"], "leftover_mill_episode")
        self.assertEqual(entry["reason_codes"], ["LEFTOVER_MILL_KIND_MIX"])
        self.assertIsNone(entry["output_id"])
        self.assertIsNone(entry["output_sha256"])

    def test_episode_with_reward_delta_still_bypasses_pair_denominator(self):
        episode = leftover_mill_episode("dbc-r723-buildah-layers-vfs-id-leftover")
        episode["reward_delta"] = 0.4
        run = self._run([episode])

        self.assertEqual(run.summary["preference_records"], 0)
        self.assertEqual(run.summary["skipped_non_preference_records"], 1)
        self.assertEqual(run.summary["leftover_mill_records"], 1)
        self.assertEqual(run.summary["actions"], {})
        self.assertEqual(len(run.manifest), 1)
        self.assertEqual(
            run.manifest[0]["action"],
            curate_preferences.ACTION_QUARANTINED,
        )
        self.assertEqual(
            run.manifest[0]["transform"],
            {
                "name": "same-context-preference-curation",
                "version": "1.3.0",
            },
        )
        self.assertEqual(run.summary["transform"], run.manifest[0]["transform"])

    def test_unclassifiable_skips_are_not_reported_as_leftover_mill(self):
        run = self._run([{"id": "ordinary", "state": {}}, pair("crp-r723-real-pair")])

        self.assertEqual(run.summary["skipped_non_preference_records"], 1)
        self.assertEqual(run.summary["leftover_mill_records"], 0)
        self.assertEqual(run.summary["leftover_mill_kinds"], {})
        self.assertEqual(
            [entry["action"] for entry in run.manifest],
            [curate_preferences.ACTION_RETAINED],
        )

    def test_public_audit_excludes_quarantine_rows(self):
        run = self._run(
            [
                leftover_mill_episode("dbc-r723-buildah-vfs-audit-leftover"),
                pair("crp-r723-real-pair"),
            ]
        )

        audit = curate_preferences.build_audit(run)
        self.assertEqual(audit["summary"]["preference_pairs"], 1)
        self.assertEqual(audit["summary"]["impure_pairs"], 0)
        self.assertEqual(audit["impure_pairs"], [])
        self.assertEqual(audit["transform"]["version"], "1.3.0")

    def test_human_report_names_the_quarantined_count(self):
        run = self._run(
            [
                leftover_mill_episode("dbc-r723-buildah-vfs-graphroot-leftover"),
                pair("crp-r723-real-pair"),
            ]
        )
        report = curate_preferences._render_human(run)
        self.assertIn("Leftover mill (quarantined): 1", report)
        self.assertIn("quarantined [LEFTOVER_MILL_KIND_MIX]", report)

    def test_an_encodable_quarantined_id_is_still_reported(self):
        """The guard drops only what the destination cannot encode."""
        run = self._run([leftover_mill_episode("dbc-r723-ordinary-id")])
        quarantined = [
            entry
            for entry in run.manifest
            if entry["action"] == curate_preferences.ACTION_QUARANTINED
        ]
        self.assertEqual(len(quarantined), 1)
        self.assertEqual(quarantined[0]["source_record_id"], "dbc-r723-ordinary-id")

    def test_a_quarantined_id_taken_from_meta_is_still_reported(self):
        """record_id()'s meta.id fallback must survive the canonicalizability
        guard: only the value is filtered, not the lookup."""
        episode = leftover_mill_episode("unused")
        del episode["id"]
        episode["meta"]["id"] = "dbc-r723-meta-fallback-id"
        run = self._run([episode])
        quarantined = [
            entry
            for entry in run.manifest
            if entry["action"] == curate_preferences.ACTION_QUARANTINED
        ]
        self.assertEqual(len(quarantined), 1)
        self.assertEqual(
            quarantined[0]["source_record_id"], "dbc-r723-meta-fallback-id"
        )

    def test_a_quarantined_id_the_manifest_cannot_encode_is_dropped_not_fatal(self):
        """json.loads accepts an escaped lone surrogate, so a foreign-mill
        record can carry an id that write_run cannot serialize. Storing it raw
        made write_run raise UnicodeEncodeError, destroying the whole
        auditable quarantine manifest rather than one field (Codex #92)."""
        with tempfile.TemporaryDirectory() as td:
            source = Path(td) / "source"
            source.mkdir()
            write_jsonl(
                source / "batch-r723.jsonl",
                [
                    leftover_mill_episode("dbc-r723-\ud800-leftover"),
                    pair("crp-r723-real-pair"),
                ],
            )
            run = curate_preferences.curate_source(source)
            output = Path(td) / "out.jsonl"
            manifest = Path(td) / "manifest.jsonl"
            curate_preferences.write_run(run, source, output, manifest)
            rows = [
                json.loads(line)
                for line in manifest.read_text(encoding="utf-8").splitlines()
            ]

        quarantined = [
            row for row in rows if row["action"] == curate_preferences.ACTION_QUARANTINED
        ]
        self.assertEqual(len(quarantined), 1)
        entry = quarantined[0]
        # The unencodable id is dropped; every other coordinate an auditor
        # needs to find the record survives.
        self.assertIsNone(entry["source_record_id"])
        self.assertEqual(entry["source_path"], "batch-r723.jsonl")
        self.assertEqual(entry["source_line"], 1)
        self.assertEqual(entry["classification"], "leftover_mill_episode")
        self.assertEqual(entry["reason_codes"], ["LEFTOVER_MILL_KIND_MIX"])
        self.assertTrue(entry["source_sha256"])
        self.assertTrue(entry["source_file_sha256"])


if __name__ == "__main__":
    unittest.main()
