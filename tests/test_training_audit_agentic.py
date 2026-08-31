#!/usr/bin/env python3
"""training_audit.py's agentic structural and hidden-reasoning checks.

A null steps/transcript container must be reported, not crash the audit; a
recursive hidden-thought field, an empty decision_basis, or a coordination
transcript's hidden reasoning must each block training; and staged agentic
tool turns receive the same publication-strictness structural checks.
"""

import sys
import tempfile
import unittest
from pathlib import Path

_TESTS = Path(__file__).resolve().parent
if str(_TESTS) not in sys.path:
    sys.path.insert(0, str(_TESTS))

from training_audit_test_helpers import episode_preference, write  # noqa: E402

import training_audit  # noqa: E402


class TrainingAuditAgenticStructure(unittest.TestCase):
    def test_null_agentic_turn_containers_are_reported_without_crashing(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            malformed_episode = {
                "id": "null-episode-steps",
                "goal": "repair the cache",
                "steps": None,
                "outcome": "not reached",
                "reward": {"success": False},
            }
            malformed_multi_agent = {
                "id": "null-transcript",
                "goal": "resolve rollout ownership",
                "agents": [
                    {"role": "operator", "mandate": "ship safely"},
                    {"role": "reviewer", "mandate": "block regressions"},
                ],
                "transcript": None,
                "joint_outcome": "not reached",
                "reward": {"success": False},
            }
            write(root / "agentic" / "batch-r01.jsonl", [malformed_episode, malformed_multi_agent])

            report = training_audit.audit_run(root)

        self.assertFalse(report["training_ready"])
        self.assertGreaterEqual(report["record_invariants"]["errors"], 2)

    def test_audit_rejects_recursive_hidden_thought_fields_with_basis(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            record = episode_preference("episode-pref-recursive-thought", pair_goal="repair the cache")
            record["rejected"]["steps"][0]["tool_call"]["args"]["scratch"] = "private"
            write(root / "tool-use-preference-factory" / "batch-r01.jsonl", [record])

            report = training_audit.audit_run(root)

        self.assertEqual(report["episodes"]["hidden_thought_fields"], 1)
        self.assertFalse(report["training_ready"])

    def test_audit_rejects_hidden_thought_in_coordination_transcript(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            record = {
                "id": "coordination-hidden-thought",
                "goal": "resolve a deploy disagreement",
                "agents": [
                    {"role": "operator", "mandate": "ship safely"},
                    {"role": "reviewer", "mandate": "block unsafe rollout"},
                ],
                "transcript": [
                    {"n": 1, "speaker": "operator", "content": "Canary is ready."},
                    {
                        "n": 2,
                        "speaker": "reviewer",
                        "content": "Need a rollback checkpoint first.",
                        "inner_monologue": "private reasoning",
                    },
                ],
                "disagreements": ["rollback checkpoint"],
                "resolution": "create checkpoint before rollout",
                "joint_outcome": "safe canary plan",
                "reward": {"success": True},
                "meta": {"factory": "multi-agent-coordination-factory", "round": 1},
            }
            write(root / "multi-agent-coordination-factory" / "batch-r01.jsonl", [record])

            report = training_audit.audit_run(root)

        self.assertEqual(report["episodes"]["hidden_thought_fields"], 1)
        self.assertFalse(report["training_ready"])

    def test_audit_blocks_empty_decision_basis(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            record = episode_preference("episode-pref-empty-basis", pair_goal="repair the cache")
            record["chosen"]["steps"][0]["decision_basis"] = "   "
            write(root / "tool-use-preference-factory" / "batch-r01.jsonl", [record])

            report = training_audit.audit_run(root)

        self.assertEqual(report["episodes"]["missing_decision_basis_steps"], 1)
        self.assertFalse(report["training_ready"])
        self.assertTrue(any("non-empty textual decision_basis" in item for item in report["blockers"]))

    def test_agentic_tool_turns_receive_publication_strictness(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            record = episode_preference(
                "malformed-tool-turn", pair_goal="repair the cache"
            )
            record["chosen"]["steps"][0]["tool_call"] = "not-object"
            write(root / "tool-use-preference-factory" / "batch-r01.jsonl", [record])

            report = training_audit.audit_run(root)

        self.assertFalse(report["training_ready"])
        self.assertTrue(
            any(
                "tool_call must be an object" in error
                for error in report["record_invariants"]["error_examples"]
            ),
            report["record_invariants"],
        )


if __name__ == "__main__":
    unittest.main()
