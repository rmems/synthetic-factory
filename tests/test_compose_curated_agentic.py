#!/usr/bin/env python3
"""Agentic hidden-field repair and curation-lane gate agreement."""

import json
import sys
import tempfile
import unittest
from dataclasses import dataclass
from pathlib import Path

TESTS = Path(__file__).resolve().parent
REPO = TESTS.parent
for _path in (TESTS, REPO / "pipelines"):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

import compose_curated  # noqa: E402
import curate_agentic  # noqa: E402
import curate_bridge  # noqa: E402
import curate_coding  # noqa: E402
import curate_preferences  # noqa: E402
import training_audit  # noqa: E402
from compose_curated_test_support import (  # noqa: E402
    bridge_pair,
    episode,
    multi_agent,
    preference_pair,
    read_jsonl,
    safety_case,
    thalamic,
    write_jsonl,
)


@dataclass(frozen=True)
class _AgenticHiddenShape:
    multi: tuple[str, str]
    safety: tuple[str, str]


class ComposeCuratedAgenticAndLaneGates(unittest.TestCase):
    @staticmethod
    def _compose_agentic_hidden_shapes(
        root: Path,
        hidden: _AgenticHiddenShape,
    ):
        multi_key, multi_value = hidden.multi
        safety_key, safety_value = hidden.safety
        multi = multi_agent()
        multi["transcript"][1][multi_key] = multi_value
        safety = safety_case()
        safety["steps"][0][safety_key] = safety_value
        source = root / "run"
        write_jsonl(
            source / "multi-agent-coordination-factory" / "batch-r01.jsonl",
            [multi],
        )
        write_jsonl(
            source / "safety-calibration-factory" / "batch-r01.jsonl",
            [safety],
        )
        summary = compose_curated.compose_run(source, root / "curated")
        records_dir = root / "curated" / compose_curated.RECORDS_DIRNAME
        return summary, records_dir

    def test_registered_agentic_shapes_strip_hidden_fields_before_strict_audit(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            summary, records_dir = self._compose_agentic_hidden_shapes(
                root,
                _AgenticHiddenShape(
                    ("inner_monologue", "hidden review reasoning"),
                    ("thought", "hidden refusal reasoning"),
                ),
            )
            self.assertTrue(summary["audit"]["training_ready"], summary["audit"])
            self.assertEqual(summary["audit"]["blockers"], [])
            self.assertEqual(
                summary["transforms"]["coding"]["registered_agentic"],
                {
                    "name": curate_agentic.TRANSFORM_NAME,
                    "version": curate_agentic.TRANSFORM_VERSION,
                    "record_kinds": ["multi_agent", "safety_case"],
                },
            )
            report = training_audit.audit_run(records_dir)
            self.assertTrue(report["training_ready"], report["blockers"])
            self.assertEqual(report["episodes"]["hidden_thought_fields"], 0)
            for output in records_dir.rglob("*.jsonl"):
                for record in read_jsonl(output):
                    self.assertFalse(curate_agentic.contains_hidden_thought_key(record))

            manifest = read_jsonl(root / "curated" / summary["manifest"]["path"])
            coding_stages = [
                next(stage for stage in entry["stages"] if stage["lane"] == "coding")
                for entry in manifest
            ]
            self.assertEqual(
                {stage["transform_name"] for stage in coding_stages},
                {curate_agentic.TRANSFORM_NAME},
            )
            self.assertTrue(
                all(
                    curate_agentic.REASON_THOUGHT_REMOVED in stage["reason_codes"]
                    for stage in coding_stages
                )
            )

    def test_registered_agentic_shapes_strip_the_full_hidden_reasoning_vocabulary(self):
        """Codex #97 P2: agentic curation must catch what the audit catches.

        ``curate_agentic`` used to recognise only the narrow scratch-pad
        vocabulary (thought/chain_of_thought/scratch/inner_monologue).  A
        multi_agent or safety_case record carrying the coding-factory key
        ``reasoning`` or an ``internal_reasoning*`` variant was retained by
        this lane with the private field intact, then rejected by
        ``training_audit``'s broader hidden-reasoning check -- an
        otherwise-repairable record that composition could never make
        training-ready. Both keys must now be stripped here too.
        """
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            summary, records_dir = self._compose_agentic_hidden_shapes(
                root,
                _AgenticHiddenShape(
                    ("reasoning", "hidden coding-style reasoning"),
                    ("internal_reasoning_optimizer", "hidden optimizer trace"),
                ),
            )
            self.assertTrue(summary["audit"]["training_ready"], summary["audit"])
            self.assertEqual(summary["audit"]["blockers"], [])
            report = training_audit.audit_run(records_dir)
            self.assertTrue(report["training_ready"], report["blockers"])
            self.assertEqual(report["episodes"]["hidden_thought_fields"], 0)
            for output in records_dir.rglob("*.jsonl"):
                for record in read_jsonl(output):
                    self.assertFalse(curate_agentic.contains_hidden_thought_key(record))
                    self.assertNotIn("reasoning", json.dumps(record))
                    self.assertNotIn("internal_reasoning_optimizer", json.dumps(record))

    def _assert_lane_predicates_agree(self, sample):
        self.assertEqual(
            compose_curated.is_preference_record(sample),
            curate_preferences._is_preference_candidate(sample),
            sample,
        )
        bridge_decision = curate_bridge.curate_record(
            sample,
            source_path="factory/batch-r01.jsonl",
            source_line=1,
            source_hash="0" * 64,
        )
        rejected_as_bridge = (
            curate_bridge.REASON_NOT_BRIDGE in bridge_decision.manifest["reason_codes"]
        )
        self.assertEqual(compose_curated.is_bridge_record(sample), not rejected_as_bridge, sample)
        _curated, coding_manifest = curate_coding.curate_episode(sample)
        rejected_as_episode = coding_manifest["reason_codes"] == [
            curate_coding.REASON_STEPS_NOT_ARRAY
        ]
        self.assertEqual(compose_curated.is_episode_record(sample), not rejected_as_episode, sample)

    def test_lane_gates_match_each_lane_predicate(self):
        record = thalamic("gate")
        decision = compose_curated.compose_record(
            record,
            source_path="thalamic-trajectory-factory/batch-r01.jsonl",
            source_line=1,
            source_sha256="0" * 64,
        )
        self.assertEqual(decision.action, "retained")
        actions = {stage["lane"]: stage["action"] for stage in decision.stages}
        self.assertEqual(actions["bridge"], compose_curated.ACTION_NOT_APPLICABLE)
        self.assertEqual(actions["preferences"], compose_curated.ACTION_NOT_APPLICABLE)
        self.assertEqual(actions["coding"], compose_curated.ACTION_NOT_APPLICABLE)
        self.assertEqual(actions["identity"], compose_curated.ACTION_RETAINED)
        self.assertEqual(actions["rewards"], compose_curated.ACTION_RETAINED)

        unstamped = thalamic("unstamped")
        unstamped["meta"].pop("factory")
        refused = compose_curated.compose_record(
            unstamped,
            source_path="thalamic-trajectory-factory/batch-r01.jsonl",
            source_line=1,
            source_sha256="0" * 64,
        )
        self.assertEqual(refused.action, compose_curated.ACTION_EXCLUDED)
        self.assertEqual(
            refused.reason_codes,
            ("identity.factory_path_payload_mismatch",),
        )

        # The compose gates must agree with the gates the lanes apply themselves.
        samples = [
            thalamic("x"),
            bridge_pair(),
            preference_pair(),
            episode(),
            {"reward_delta": 1.0},
            {"steps": "not-a-list"},
            {"language_view": {}, "spike_events": "not-a-list"},
        ]
        for sample in samples:
            self._assert_lane_predicates_agree(sample)


if __name__ == "__main__":
    unittest.main()
