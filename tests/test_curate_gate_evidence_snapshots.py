#!/usr/bin/env python3
"""Evidence-snapshot tests for the curation gate (pipelines/curate_gate.py).

Authenticated snapshots and governance evidence in the curation gate: lane and
source files are read once and refused when symlinked or swapped mid-read,
evidence copies come from that snapshot, lane manifests stay out of the corpus,
and JSONL framing survives Unicode line separators.
"""

import json
import sys
import unittest
from functools import partial
from pathlib import Path
from unittest import mock

_TESTS = Path(__file__).resolve().parent
if str(_TESTS) not in sys.path:
    sys.path.insert(0, str(_TESTS))

from curate_gate_test_support import required_item, temp_root  # noqa: E402
from gate_fixture import (  # noqa: E402
    PIPELINES,
    GateFixture,
    _thalamic,
    _write_jsonl,
)

if str(PIPELINES) not in sys.path:
    sys.path.insert(0, str(PIPELINES))

import curate_gate  # noqa: E402
import curate_gate_digest  # noqa: E402
import curate_gate_gates  # noqa: E402


class EvidenceSnapshotTests(unittest.TestCase):
    """Evidence is copied from the bytes the gate authenticated."""

    def setUp(self):
        self.root = temp_root(self)

    def test_jsonl_lane_manifest_remains_parseable_as_promoted_evidence(self):
        # This case isolates evidence framing and promotion mechanics from rights policy.
        self.enterContext(mock.patch.object(curate_gate_gates, "evaluate_rights",
            return_value=({"passed": True, "enforced": False}, [])))
        fixture = GateFixture(self.root)
        entries = json.loads(fixture.manifest_paths[0].read_text())
        entries[0]["reason_codes"] = ["literal\u2028separator\u2029evidence"]
        jsonl_manifest = fixture.lane_bridge / "manifest.jsonl"
        jsonl_manifest.write_text(
            "".join(
                json.dumps(entry, ensure_ascii=False, sort_keys=True) + "\n" for entry in entries
            ),
            encoding="utf-8",
        )
        plan = json.loads(fixture.plan_path.read_text())
        plan["lanes"][0]["manifest"] = "lane-bridge/manifest.jsonl"
        fixture.plan_path.write_text(json.dumps(plan, indent=2) + "\n")

        self.assertEqual(fixture.integrate(), 0)
        review = fixture.accepted_review()
        self.assertEqual(fixture.promote(review), 0)
        copied = (
            fixture.curated
            / curate_gate.GOVERNANCE_DIRNAME
            / curate_gate.LANE_MANIFEST_DIRNAME
            / "01"
            / "manifest.jsonl.evidence"
        )
        self.assertEqual(copied.read_bytes(), jsonl_manifest.read_bytes())

    def test_jsonl_readers_keep_unicode_line_separators_inside_one_record(self):
        # This case isolates evidence framing and promotion mechanics from rights policy.
        self.enterContext(mock.patch.object(curate_gate_gates, "evaluate_rights",
            return_value=({"passed": True, "enforced": False}, [])))
        record = _thalamic("unicode-separators")
        record["state"]["env"] = "before\u2028middle\u2029after"
        record["reward_components"]["note"] = "reward\u2028evidence\u2029value"
        fixture = GateFixture(self.root, thalamic_records=[record])
        self.assertEqual(fixture.integrate(), 0)
        manifest = fixture.manifest()
        for gate in ("structural_validator", "record_invariants", "training_audit"):
            self.assertTrue(manifest["gates"][gate]["passed"], gate)

        output = fixture.cleaned / "thalamic-mini" / "batch-r02.jsonl"
        self.assertEqual(curate_gate.count_records(output), 1)
        parsed = list(curate_gate.iter_records(fixture.cleaned))
        self.assertEqual(len(parsed), 2)
        thalamic = required_item(item for item in parsed if item[0].startswith("thalamic-mini/"))
        self.assertEqual(thalamic[2]["state"]["env"], "before\u2028middle\u2029after")
        self.assertEqual(
            thalamic[2]["reward_components"]["note"],
            "reward\u2028evidence\u2029value",
        )
        review = fixture.accepted_review()
        self.assertEqual(fixture.promote(review), 0)
        promoted = list(curate_gate.iter_records(fixture.curated))
        promoted_thalamic = required_item(
            item for item in promoted if item[0].startswith("thalamic-mini/")
        )
        self.assertEqual(
            promoted_thalamic[2]["state"]["env"],
            "before\u2028middle\u2029after",
        )

    def test_integrate_refuses_a_symlinked_lane_output(self):
        fixture = GateFixture(self.root)
        outside = self.root / "outside.jsonl"
        _write_jsonl(outside, [_thalamic("t-outside")])
        link = fixture.lane_core / "thalamic-mini" / "linked.jsonl"
        try:
            link.symlink_to(outside)
        except (OSError, NotImplementedError):
            self.skipTest("symlinks are unavailable on this platform")
        self.assertEqual(fixture.integrate(), 2)
        self.assertFalse(fixture.cleaned.exists())

    def test_a_lane_manifest_inside_the_output_tree_stays_out_of_the_corpus(self):
        fixture = GateFixture(self.root)
        self.assertTrue(fixture.manifest_paths[0].is_file())
        self.assertEqual(fixture.integrate(), 1)
        self.assertFalse((fixture.cleaned / "manifest.json").exists())
        manifest = fixture.manifest()
        self.assertNotIn("manifest.json", {entry["path"] for entry in manifest["outputs"]})
        copied = fixture.cleaned / curate_gate.GOVERNANCE_DIRNAME / "lane-manifests"
        self.assertEqual(len(list(copied.rglob("*.evidence"))), 6)

    def _assert_refuses_replacement_during_read(self, path, replacement, read):
        """Swap ``replacement`` over ``path`` at the second fstat; ``read`` must refuse."""
        original_fstat = curate_gate_digest.os.fstat
        calls = 0

        def replace_before_second_fstat(descriptor):
            nonlocal calls
            calls += 1
            if calls == 2:
                replacement.replace(path)
            return original_fstat(descriptor)

        with (
            mock.patch.object(
                curate_gate_digest.os,
                "fstat",
                side_effect=replace_before_second_fstat,
            ),
            self.assertRaisesRegex(curate_gate.GateError, "changed while"),
        ):
            read()

    def test_lane_snapshot_rejects_a_path_replaced_during_read(self):
        path = self.root / "lane.jsonl"
        replacement = self.root / "replacement.jsonl"
        path.write_text('{"id":"before"}\n', encoding="utf-8")
        replacement.write_text('{"id":"after"}\n', encoding="utf-8")

        self._assert_refuses_replacement_during_read(
            path,
            replacement,
            partial(curate_gate._read_regular_file_snapshot, path, "lane output"),
        )

    def test_source_loader_rejects_a_path_replaced_during_read(self):
        source_run = self.root / "raw"
        path = source_run / "factory" / "batch-r01.jsonl"
        replacement = self.root / "replacement.jsonl"
        _write_jsonl(path, [_thalamic("before")])
        _write_jsonl(replacement, [_thalamic("after")])

        self._assert_refuses_replacement_during_read(
            path,
            replacement,
            partial(curate_gate._load_source_records, source_run),
        )

    def test_lane_manifest_evidence_uses_the_authenticated_snapshot(self):
        fixture = GateFixture(self.root)
        prepared = curate_gate.prepare_lanes(curate_gate.load_plan(fixture.plan_path))
        original = prepared[0]["manifest_payload"]
        fixture.manifest_paths[0].write_text("[]", encoding="utf-8")
        destination = self.root / "evidence"
        destination.mkdir()

        lane_evidence, _governance = curate_gate.copy_lane_evidence(prepared, destination)

        copied = destination / lane_evidence[0]["manifest"]["path"]
        self.assertEqual(copied.read_bytes(), original)
        self.assertNotEqual(copied.read_bytes(), fixture.manifest_paths[0].read_bytes())

    def test_reward_artifact_evidence_uses_the_authenticated_snapshot(self):
        fixture = GateFixture(self.root)
        prepared = curate_gate.prepare_lanes(curate_gate.load_plan(fixture.plan_path))
        reward_lane = required_item(
            lane for lane in prepared if lane["transform"] == "reward_ontology"
        )
        artifact = reward_lane["artifacts"][0]
        original = artifact["_payload"]
        artifact["source_path"].write_text("{}\n", encoding="utf-8")
        destination = self.root / "evidence"
        destination.mkdir()

        lane_evidence, _governance = curate_gate.copy_lane_evidence(prepared, destination)

        reward_evidence = required_item(
            lane for lane in lane_evidence if lane["transform"] == "reward_ontology"
        )["artifacts"][0]
        copied = destination / reward_evidence["path"]
        self.assertEqual(copied.read_bytes(), original)
        self.assertNotEqual(copied.read_bytes(), artifact["source_path"].read_bytes())


if __name__ == '__main__':
    unittest.main()
