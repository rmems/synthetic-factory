#!/usr/bin/env python3
"""training_audit.py's preference-pair purity and context invariants.

Thalamic pairs must hold state/proposal constant; episode-sided pairs use
the shared goal, not thalamic context, and a legacy 'thought' step or a
side-goal conflict must block training even when a malformed pair does not
crash the audit outright.
"""

import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path

_TESTS = Path(__file__).resolve().parent
if str(_TESTS) not in sys.path:
    sys.path.insert(0, str(_TESTS))

from training_audit_test_helpers import episode_preference, thalamic, write  # noqa: E402

import training_audit  # noqa: E402


class TrainingAuditPreferencePurity(unittest.TestCase):
    def test_numeric_lexeme_variants_share_one_semantic_context(self):
        def nested(value):
            for _ in range(70):
                value = [value]
            return value

        chosen = thalamic("numeric-chosen")
        rejected = copy.deepcopy(chosen)
        rejected["id"] = "numeric-rejected"
        chosen["state"]["measurement"] = nested("STATE_CHOSEN_NUMBER")
        rejected["state"]["measurement"] = nested("STATE_REJECTED_NUMBER")
        chosen["proposed_action"]["score"] = "PROPOSAL_CHOSEN_NUMBER"
        rejected["proposed_action"]["score"] = "PROPOSAL_REJECTED_NUMBER"
        pair = {
            "id": "numeric-context-preference",
            "chosen": chosen,
            "rejected": rejected,
            "critique": "numeric spellings do not change the modeled context",
        }
        payload = (
            json.dumps(pair)
            .replace('"STATE_CHOSEN_NUMBER"', "25.0", 1)
            .replace('"STATE_REJECTED_NUMBER"', "25.00", 1)
            .replace('"PROPOSAL_CHOSEN_NUMBER"', "2.5e1", 1)
            .replace('"PROPOSAL_REJECTED_NUMBER"', "25", 1)
        )
        parsed = json.loads(
            payload,
            parse_float=training_audit._parse_finite_json_float,
        )
        self.assertNotEqual(
            training_audit.canonical_blob(parsed["chosen"]["state"]),
            training_audit.canonical_blob(parsed["rejected"]["state"]),
            "evidence/hash serialization must retain source number lexemes",
        )

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root / "failure-as-fuel-preference-cascade" / "batch-r01.jsonl"
            source.parent.mkdir(parents=True)
            source.write_text(payload + "\n", encoding="utf-8")

            report = training_audit.audit_run(root)

        self.assertEqual(report["preferences"]["same_state"], 1)
        self.assertEqual(report["preferences"]["same_proposal"], 1)
        self.assertEqual(report["preferences"]["same_context"], 1)

    def test_malformed_preference_does_not_crash_audit(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            malformed = {
                "id": "bad-pref",
                "chosen": "not-an-object",
                "rejected": thalamic("rejected"),
                "critique": "malformed fixture",
            }
            write(root / "prefs" / "batch.jsonl", [malformed])
            report = training_audit.audit_run(root)

        self.assertEqual(report["preferences"]["pairs"], 1)
        self.assertEqual(report["preferences"]["same_context"], 0)
        self.assertGreater(report["record_invariants"]["errors"], 0)

    def test_legacy_thalamic_preference_is_not_exempt_from_the_thought_ban(self):
        # Thalamic-shaped records used to be exempt. Wrap records are Thalamic
        # shaped, so the exemption let published hidden CoT through; the ban is
        # now corpus-wide regardless of record kind.
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            chosen = thalamic("legacy-chosen")
            rejected = thalamic("legacy-rejected")
            chosen["state"]["thought"] = "legacy annotation"
            record = {
                "id": "legacy-preference",
                "chosen": chosen,
                "rejected": rejected,
                "critique": "legacy Thalamic comparison",
            }
            write(root / "legacy-preference" / "batch-r01.jsonl", [record])

            report = training_audit.audit_run(root)

        self.assertEqual(report["preferences"]["thalamic_pairs"], 1)
        self.assertEqual(report["episodes"]["hidden_thought_fields"], 1)
        self.assertEqual(
            report["hidden_thought_examples"],
            ["legacy-preference/batch-r01.jsonl:1:chosen.state.thought"],
        )
        self.assertTrue(any("hidden-thought fields" in item for item in report["blockers"]))
        self.assertFalse(report["training_ready"])

    def test_episode_preference_uses_shared_goal_not_thalamic_context(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            valid = episode_preference("episode-pref", pair_goal="repair the cache")
            write(root / "tool-use-preference-factory" / "batch-r01.jsonl", [valid])

            report = training_audit.audit_run(root)

        self.assertTrue(report["training_ready"], report["blockers"])
        self.assertEqual(report["preferences"]["episode_pairs"], 1)
        self.assertEqual(report["preferences"]["same_goal"], 1)
        self.assertEqual(report["preferences"]["same_context"], 1)
        self.assertEqual(report["preferences"]["same_state"], 0)
        self.assertEqual(report["preferences"]["same_proposal"], 0)

    def test_episode_preference_with_mismatched_side_goals_blocks_training(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            invalid = episode_preference(
                "episode-pref-mismatch",
                chosen_goal="repair the cache",
                rejected_goal="rotate credentials",
            )
            write(root / "tool-use-preference-factory" / "batch-r01.jsonl", [invalid])

            report = training_audit.audit_run(root)

        self.assertFalse(report["training_ready"])
        self.assertEqual(report["preferences"]["same_goal"], 0)
        self.assertTrue(any("shared-goal" in item for item in report["blockers"]))

    def test_episode_preference_legacy_thought_blocks_training(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            record = episode_preference("episode-pref-hidden-thought", pair_goal="repair the cache")
            step = record["chosen"]["steps"][0]
            step.pop("decision_basis")
            step["thought"] = "private reasoning must not become training data"
            write(root / "tool-use-preference-factory" / "batch-r01.jsonl", [record])

            report = training_audit.audit_run(root)

        self.assertEqual(report["episodes"]["legacy_thought_only_steps"], 1)
        self.assertFalse(report["training_ready"])
        self.assertTrue(any("hidden-thought" in item for item in report["blockers"]))

    def test_episode_preference_does_not_let_wrapper_goal_mask_side_conflict(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            conflicting = episode_preference(
                "episode-pref-wrapper-conflict",
                pair_goal="repair the cache",
                chosen_goal="repair the cache",
                rejected_goal="rotate credentials",
            )
            write(root / "tool-use-preference-factory" / "batch-r01.jsonl", [conflicting])

            report = training_audit.audit_run(root)

        self.assertFalse(report["training_ready"])
        self.assertEqual(report["preferences"]["same_goal"], 0)


if __name__ == "__main__":
    unittest.main()
