#!/usr/bin/env python3
"""Composed hosted trees retain research-only records and stay non-exportable."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

TESTS = Path(__file__).resolve().parent
REPO = TESTS.parent
for _path in (TESTS, REPO / "pipelines"):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

import compose_curated
import training_audit
from compose_curated_test_support import (
    assert_research_only_audit,
    build_source_run,
    read_jsonl,
)


class ComposeCuratedRights(unittest.TestCase):
    def test_hosted_compose_retains_research_only_and_is_not_training_ready(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = build_source_run(root / "run")
            summary = compose_curated.compose_run(source, root / "curated")

            self.assertGreater(summary["counts"]["retained"], 0)
            assert_research_only_audit(self, summary["audit"])
            self.assertEqual(
                summary["rights"]["lanes"]["research"],
                summary["counts"]["retained"],
            )
            self.assertEqual(summary["rights"]["lanes"]["training"], 0)
            self.assertFalse(summary["rights"]["training_exportable"])
            self.assertEqual(summary["lane_order"], list(compose_curated.LANE_ORDER))

            manifest = read_jsonl(root / "curated" / summary["manifest"]["path"])
            retained = [entry for entry in manifest if entry["action"] == "retained"]
            self.assertEqual(len(retained), summary["counts"]["retained"])
            for entry in retained:
                self.assertEqual(entry["rights_lane"], "research")
                self.assertEqual(entry["rights"]["intended_use"], "research_only")
                self.assertEqual(entry["rights"]["project_training_policy"], "blocked")
                stages = [stage["lane"] for stage in entry["stages"] if stage["lane"] != "source"]
                self.assertEqual(stages[:5], list(compose_curated.LANE_ORDER)[: len(stages)])

            records_dir = root / "curated" / compose_curated.RECORDS_DIRNAME
            report = training_audit.audit_run(records_dir)
            assert_research_only_audit(self, report)
            for path in records_dir.rglob("*.jsonl"):
                for record in read_jsonl(path):
                    self.assertNotIn("rights", record)

            compose_summary = json.loads(
                (root / "curated" / compose_curated.SUMMARY_FILENAME).read_text(encoding="utf-8")
            )
            self.assertEqual(compose_summary["audit"], summary["audit"])
