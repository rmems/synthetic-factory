#!/usr/bin/env python3
"""Record-level privacy repair and ownership quarantine during composition."""

import copy
import sys
import tempfile
import unittest
from pathlib import Path

TESTS = Path(__file__).resolve().parent
REPO = TESTS.parent
for _path in (TESTS, REPO / "pipelines"):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

import compose_curated  # noqa: E402
from compose_curated_test_support import (  # noqa: E402
    bridge_pair,
    read_jsonl,
    thalamic,
    write_jsonl,
)


class ComposeCuratedRecordSafety(unittest.TestCase):
    """Exercise record repairs that keep private or foreign data out."""

    def test_bridge_embedded_coding_wraps_are_repaired_not_blocked(self):
        """Codex #97 P2: language_view.trajectory wraps reach the coding lane.

        The audit inspects a bridge pair's embedded trajectory exactly like a
        top-level Thalamic wrap, so hidden reasoning there used to survive
        composition and block the composed corpus even though the coding lane
        can repair it.
        """

        pair = bridge_pair()
        pair["internal_reasoning"] = "hidden outer bridge reasoning"
        pair["language_view"]["trajectory"]["executed_action"] = {
            "steps": [
                {
                    "n": 1,
                    "thought": "hidden nested reasoning",
                    "tool_call": {"name": "inspect", "args": {}},
                    "observation": "fixture result",
                }
            ],
            "goal": "nested goal",
            "outcome": "nested outcome",
            "reward": {"success": True},
        }

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root / "run"
            write_jsonl(
                source / "neuromorphic-event-language-bridge" / "batch-r01.jsonl",
                [pair],
            )

            summary = compose_curated.compose_run(source, root / "curated")

            self.assertEqual(summary["counts"]["retained"], 1)
            self.assertTrue(
                summary["audit"]["training_ready"], summary["audit"]["blockers"]
            )
            manifest = read_jsonl(root / "curated" / summary["manifest"]["path"])
            coding_stage = next(
                stage
                for stage in manifest[0]["stages"]
                if stage["lane"] == "coding"
            )
            self.assertEqual(
                coding_stage["detail"]["embedded_at"], "language_view.trajectory"
            )
            self.assertEqual(
                coding_stage["detail"]["hidden_reasoning_fields_removed"], 2
            )
            self.assertEqual(
                coding_stage["detail"]["wrapper_hidden_reasoning_fields_removed"], 1
            )
            records_dir = root / "curated" / compose_curated.RECORDS_DIRNAME
            emitted = next(records_dir.rglob("*.jsonl")).read_text(encoding="utf-8")
            self.assertNotIn("hidden nested reasoning", emitted)
            self.assertNotIn("hidden outer bridge reasoning", emitted)
            self.assertNotIn("internal_reasoning", emitted)
            self.assertNotIn('"thought"', emitted)

    def test_wrap_records_with_incidental_root_steps_ground_the_wrapped_episode(self):
        """Codex #97 P2: the wrapped episode wins over an incidental root array.

        The strict audit grounds a registered Thalamic record's
        ``executed_action.steps`` — and a bridge record's
        ``language_view.trajectory`` wrap — never a root-level ``steps``
        array. Curating the incidental root array instead used to leave the
        actual wrap ungrounded, blocking an otherwise repairable corpus.
        """

        wrap_episode = {
            "steps": [
                {
                    "n": 1,
                    "thought": "hidden nested reasoning",
                    "tool_call": {"name": "inspect", "args": {}},
                    "observation": "fixture result",
                }
            ],
            "goal": "nested goal",
            "outcome": "nested outcome",
            "reward": {"success": True},
        }
        incidental = [
            {
                "n": 1,
                "decision_basis": "incidental top-level step",
                "tool_call": {"name": "noop", "args": {}},
                "observation": "incidental",
            }
        ]
        wrap = thalamic("root-steps")
        wrap["executed_action"] = dict(
            wrap["executed_action"], **copy.deepcopy(wrap_episode)
        )
        wrap["steps"] = copy.deepcopy(incidental)
        pair = bridge_pair()
        pair["language_view"]["trajectory"]["executed_action"] = copy.deepcopy(
            wrap_episode
        )
        pair["steps"] = copy.deepcopy(incidental)

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root / "run"
            write_jsonl(
                source / "thalamic-trajectory-factory" / "batch-r01.jsonl", [wrap]
            )
            write_jsonl(
                source / "neuromorphic-event-language-bridge" / "batch-r01.jsonl",
                [pair],
            )

            summary = compose_curated.compose_run(source, root / "curated")

            self.assertEqual(summary["counts"]["retained"], 2)
            self.assertTrue(
                summary["audit"]["training_ready"], summary["audit"]["blockers"]
            )
            records_dir = root / "curated" / compose_curated.RECORDS_DIRNAME
            emitted = "".join(
                path.read_text(encoding="utf-8")
                for path in sorted(records_dir.rglob("*.jsonl"))
            )
            self.assertNotIn("hidden nested reasoning", emitted)
            self.assertNotIn('"thought"', emitted)

    def test_hidden_only_thalamic_records_are_stripped_not_blocked(self):
        """Codex #97 P2: hidden reasoning on a stepless Thalamic record is repaired.

        A valid Thalamic record with ``proposed_action.internal_reasoning``
        but no episode step array has no coding lane, so composition used to
        retain the private field and the strict audit then blocked the whole
        corpus — even though the generic recursive stripper can repair it
        exactly as it does for preference sides and stepless bridge wraps.
        """

        record = thalamic("hidden-only")
        record["proposed_action"]["internal_reasoning"] = "secret plan"

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root / "run"
            write_jsonl(
                source / "thalamic-trajectory-factory" / "batch-r01.jsonl", [record]
            )

            summary = compose_curated.compose_run(source, root / "curated")

            self.assertEqual(summary["counts"]["retained"], 1)
            self.assertTrue(
                summary["audit"]["training_ready"], summary["audit"]["blockers"]
            )
            manifest = read_jsonl(root / "curated" / summary["manifest"]["path"])
            coding_stage = next(
                stage
                for stage in manifest[0]["stages"]
                if stage["lane"] == "coding"
            )
            self.assertEqual(
                coding_stage["detail"]["hidden_reasoning_fields_removed"], 1
            )
            records_dir = root / "curated" / compose_curated.RECORDS_DIRNAME
            emitted = next(records_dir.rglob("*.jsonl")).read_text(encoding="utf-8")
            self.assertNotIn("secret plan", emitted)
            self.assertNotIn("internal_reasoning", emitted)

    def test_foreign_mill_records_are_quarantined_before_identity(self):
        """Codex #97 P1: mill ownership resolves before identity rewrites ids.

        A destination-stamped leftover mill is identifiable only by its
        foreign id prefix and goal family. Composing it record-by-record let
        identity replace that prefix with a canonical digest, so the curated
        tree audited clean and the export shipped the foreign record while
        reporting training_ready.
        """

        from curate_agentic_fixtures import (
            DEST_STAMPED_MILL,
            STAMPEDE_CONTROLS,
            write_mill_run,
        )

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root / "run"
            source.mkdir()
            write_mill_run(source, list(STAMPEDE_CONTROLS) + [DEST_STAMPED_MILL])

            summary = compose_curated.compose_run(source, root / "curated")

            self.assertEqual(summary["counts"]["source_records"], 5)
            self.assertEqual(summary["counts"]["excluded"], 1)
            self.assertIn("FOREIGN_MILL_ID_PREFIX", summary["exclusions"])
            records_dir = root / "curated" / compose_curated.RECORDS_DIRNAME
            emitted = "".join(
                path.read_text(encoding="utf-8")
                for path in records_dir.rglob("*.jsonl")
            )
            self.assertNotIn(DEST_STAMPED_MILL["goal"], emitted)
            manifest = read_jsonl(root / "curated" / summary["manifest"]["path"])
            quarantined = [
                entry
                for entry in manifest
                if "FOREIGN_MILL_ID_PREFIX" in entry["reason_codes"]
            ]
            self.assertEqual(len(quarantined), 1)
            self.assertEqual(quarantined[0]["action"], "excluded")
            self.assertEqual(
                quarantined[0]["stages"][0]["classification"],
                "foreign_mill_quarantined",
            )


if __name__ == "__main__":
    unittest.main()
