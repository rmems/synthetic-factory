#!/usr/bin/env python3
"""Composed hosted trees retain research-only records and stay non-exportable."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from pipelines import compose_curated, compose_curated_rights, training_audit
from tests.compose_curated_test_support import (
    assert_research_only_audit,
    build_source_run,
    read_jsonl,
)


class ComposeCuratedRights(unittest.TestCase):
    def test_hosted_compose_retains_research_only_and_is_not_training_ready(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        root = Path(temp.name)
        source = build_source_run(root / "run")
        summary = compose_curated.compose_run(
            compose_curated.ComposeRunContext(source, root / "curated")
        )

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
            self._assert_retained_rights(entry)

        records_dir = root / "curated" / compose_curated.RECORDS_DIRNAME
        report = training_audit.audit_run(records_dir)
        assert_research_only_audit(self, report)
        self.assertFalse(any("tampered or stale" in item for item in report["blockers"]), report["blockers"])
        for path in records_dir.rglob("*.jsonl"):
            for record in read_jsonl(path):
                self.assertNotIn("rights", record)

        compose_summary = json.loads(
            (root / "curated" / compose_curated.SUMMARY_FILENAME).read_text(encoding="utf-8")
        )
        self.assertEqual(compose_summary["audit"], summary["audit"])


    def _assert_retained_rights(self, entry):
        self.assertEqual(entry["rights_lane"], "research")
        identity_detail = {stage["lane"]: stage.get("detail") for stage in entry["stages"]}["identity"]
        self.assertIsInstance(identity_detail["source"]["original"], str)
        self.assertEqual(entry["rights"]["intended_use"], "research_only")
        self.assertEqual(entry["rights"]["project_training_policy"], "blocked")
        stages = [stage["lane"] for stage in entry["stages"] if stage["lane"] != "source"]
        self.assertEqual(stages[:5], list(compose_curated.LANE_ORDER)[: len(stages)])


def _replay_source():
    return SimpleNamespace(
        record={}, source_path="batch-r01.jsonl", source_line=1,
        source_sha256="0" * 64, source_json="{}",
    )


def _appending(*stages):
    def compose(_record, out, _coordinates):
        out.extend(stages)
    return compose


class ReplayedIdentityStageCount(unittest.TestCase):
    """The replay accepts exactly the one identity stage compose appends."""

    def _replay(self, *stages):
        with mock.patch.object(
            compose_curated_rights, "_compose_identity_stage_with_source", _appending(*stages)
        ):
            return compose_curated_rights._replayed_identity_stage(_replay_source())

    def test_one_retained_stage_returns_its_detail_with_the_source_bytes(self):
        stage = {"action": "retained", "detail": {"source": {"line": 1}}}
        expected = self._replay(stage)
        self.assertEqual(expected, {"source": {"line": 1, "original": "{}"}})

    def test_no_stage_or_extra_stages_are_refused(self):
        retained = {"action": "retained", "detail": {"source": {}}}
        for stages in ((), (retained, retained)):
            with (
                self.subTest(count=len(stages)),
                self.assertRaisesRegex(ValueError, "one identity stage"),
            ):
                self._replay(*stages)
