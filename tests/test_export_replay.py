#!/usr/bin/env python3
"""Focused contracts for deterministic export replay."""

import unittest
from collections import Counter
from copy import deepcopy
from dataclasses import FrozenInstanceError
from pathlib import Path
from types import SimpleNamespace

from pipelines import compose_curated, export_hf, export_replay


class ReplayAuthenticationContexts(unittest.TestCase):
    def test_absent_calibration_identity_uses_a_direct_factory_sidecar(self):
        source_root = Path("/source/failure-as-fuel-preference-cascade")

        self.assertEqual(
            export_replay._calibration_evidence_identity({"mode": "none"}, source_root),
            ("none", str(source_root / "units-migration.json")),
        )

    def test_replay_contexts_are_immutable(self):
        contexts = (
            export_replay._SourceReplay(
                relative="factory/batch-r1.jsonl",
                raw_file=b"{}\n",
                catalog={},
                mill_findings={},
            ),
            export_replay._LineReplay(
                relative="factory/batch-r1.jsonl",
                line_number=1,
                output_line=1,
                source_file_sha256="a" * 64,
                catalog={},
                mill_finding=None,
            ),
            export_replay._PublishedReplay(
                summary={},
                actual_outputs={},
                manifest_documents=(),
                sidecar_documents=(),
            ),
        )

        for context in contexts:
            with self.subTest(context=type(context).__name__):
                with self.assertRaises(FrozenInstanceError):
                    context.summary = {"forged": True}

    def test_each_replayed_aggregate_has_its_specific_failure(self):
        snapshot = export_replay._ReplaySnapshot(
            counts=Counter(
                {
                    "source_files": 1,
                    "source_records": 2,
                    "blank_lines": 0,
                    "retained": 1,
                    "excluded": 1,
                    "output_files": 1,
                    "reward_sidecars": 0,
                }
            ),
            exclusions=Counter({"compose.test": 1}),
            lane_actions={"identity": Counter({"retained": 1})},
            expected_manifest=[],
            expected_sidecars=[],
            expected_outputs=[],
            expected_payloads={},
            source_files=[],
        )
        summary = {
            "counts": {
                "source_files": 1,
                "source_records": 2,
                "blank_lines": 0,
                "retained": 1,
                "excluded": 1,
                "output_files": 1,
                "reward_sidecars": 0,
            },
            "lane_actions": {"identity": {"retained": 1}},
            "exclusions": {"compose.test": 1},
            "transforms": compose_curated.transform_contract(),
        }
        mutations = (
            ("counts", {}, "source/output counts do not reproduce"),
            ("lane_actions", {}, "lane action counts do not reproduce"),
            ("exclusions", {}, "exclusions do not reproduce"),
            ("transforms", {}, "transform declarations do not match"),
        )

        for field, forged, message in mutations:
            with self.subTest(field=field):
                tampered = deepcopy(summary)
                tampered[field] = forged
                with self.assertRaisesRegex(export_hf.ExportError, message):
                    export_replay._require_replayed_counts(snapshot, tampered)


class ReplayCompatibilityAdapters(unittest.TestCase):
    @staticmethod
    def _empty_replay_contract():
        snapshot = export_replay._ReplaySnapshot(
            counts=Counter(),
            exclusions=Counter(),
            lane_actions={},
            expected_manifest=[],
            expected_sidecars=[],
            expected_outputs=[],
            expected_payloads={},
            source_files=[],
        )
        summary = {
            "counts": {
                "source_files": 0,
                "source_records": 0,
                "blank_lines": 0,
                "retained": 0,
                "excluded": 0,
                "output_files": 0,
                "reward_sidecars": 0,
            },
            "lane_actions": {},
            "exclusions": {},
            "transforms": compose_curated.transform_contract(),
            "outputs": [],
        }
        return snapshot, summary

    def test_export_hf_verify_replay_preserves_keyword_contract(self):
        snapshot, summary = self._empty_replay_contract()

        export_hf._verify_replay_matches(
            snapshot,
            summary=summary,
            actual_outputs={},
            manifest_documents=[],
            sidecar_documents=[],
        )

    def test_record_replayed_retained_preserves_emitted_list_contract(self):
        state = export_replay._ReplayState()
        decision = SimpleNamespace(
            record={"id": "record-1"},
            output_id="record-1",
            reward_sidecar=None,
        )
        entry = {"source_line": 3}
        emitted = []

        export_replay._record_replayed_retained(
            state, decision, entry, "factory/batch-r1.jsonl", emitted
        )

        self.assertEqual(emitted, ['{"id":"record-1"}'])
        self.assertEqual(entry["output_path"], "records/factory/batch-r1.jsonl")
        self.assertEqual(entry["output_line"], 1)
        self.assertEqual(state.counts["retained"], 1)

    def test_replay_one_line_preserves_coordinate_and_context_contract(self):
        state = export_replay._ReplayState()
        emitted = []

        export_replay._replay_one_line(
            state,
            b"{not-json}",
            ("factory/batch-r1.jsonl", 4),
            ("a" * 64, {}, emitted),
            {},
        )

        self.assertEqual(emitted, [])
        self.assertEqual(state.counts["source_records"], 1)
        self.assertEqual(state.counts["excluded"], 1)
        self.assertEqual(state.expected_manifest[0]["source_path"], "factory/batch-r1.jsonl")
        self.assertEqual(state.expected_manifest[0]["source_line"], 4)
        self.assertIsNone(state.expected_manifest[0]["output_path"])

    def test_replay_source_file_preserves_positional_contract(self):
        state = export_replay._ReplayState()

        export_replay._replay_source_file(
            state,
            "factory/batch-r1.jsonl",
            b"{not-json}\n\n",
            {},
            {},
        )

        self.assertEqual(state.counts["source_files"], 1)
        self.assertEqual(state.counts["source_records"], 1)
        self.assertEqual(state.counts["blank_lines"], 1)
        self.assertEqual(state.counts["excluded"], 1)
        self.assertEqual(state.source_files[0]["path"], "factory/batch-r1.jsonl")


if __name__ == "__main__":
    unittest.main()
