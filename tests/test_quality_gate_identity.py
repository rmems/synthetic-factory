#!/usr/bin/env python3
"""Exact-identity and semantic-projection quality-gate tests."""

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "pipelines"))

from gate_fixtures import write  # noqa: E402
from quality_gate_test_support import DISTINCT_NOTES  # noqa: E402
import quality_gate  # noqa: E402


REPO_ROOT = Path(__file__).resolve().parents[1]


class ExactDedup(unittest.TestCase):
    @staticmethod
    def _agentic_episode(tool_name):
        return {
            "steps": [
                {
                    "n": 1,
                    "decision_basis": "inspect the same deployment state",
                    "tool_call": {"name": tool_name, "args": {"path": "service.py"}},
                    "observation": "the command completed",
                }
            ],
            "outcome": "complete",
            "reward": {"success": True},
        }

    def test_exact_duplicate_is_excluded_with_a_reason(self):
        record = {"id": "a", "state": {"sim_or_real": "unknown", "note": DISTINCT_NOTES[0]}}
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            write(root / "batch.jsonl", [record, {**record, "id": "b"}])
            report = quality_gate.audit_run(root)

        self.assertTrue(report["blocked"])
        self.assertEqual(len(report["duplicates"]), 1)
        duplicate = report["duplicates"][0]
        # Legacy report shape (file/line/hash) must survive.
        self.assertEqual(duplicate["file"], "batch.jsonl")
        self.assertEqual(duplicate["line"], 2)
        self.assertTrue(duplicate["hash"])
        self.assertEqual(duplicate["kind"], "exact")
        self.assertIn("already seen at batch.jsonl:1", duplicate["reason"])
        clusters = [c for c in report["duplicate_clusters"] if c["kind"] == "exact"]
        self.assertEqual(len(clusters), 1)
        self.assertEqual(clusters[0]["size"], 2)
        self.assertEqual(clusters[0]["representative"], {"file": "batch.jsonl", "line": 1})
        self.assertEqual(report["counts"]["excluded_records"], 1)

    @staticmethod
    def _thalamic(spike_events):
        """A Thalamic trajectory whose only varying content is its stream."""
        return {
            "id": "thal-1",
            "state": {"sim_or_real": "designed", "domain": "gate-test"},
            "proposed_action": {"action": "noop", "decision_basis": "fixture"},
            "safety_decision": {"decision": "ACCEPT", "rationale": "bounded"},
            "executed_action": {"action": "noop"},
            "future_outcome": {"success": True},
            "reward_components": {"task_progress": 0.5, "safety": 0.5, "total": 1.0},
            "spike_events": spike_events,
            "meta": {"factory": "thalamic-trajectory-factory", "round": 1},
        }

    def test_spike_streams_are_exact_identity(self):
        """spike_events + state are the distillation input for Thalamic
        trajectories (prompts/01-thalamic-trajectory-factory.md), so two
        trajectories that differ only in channels, timing, and amplitude are
        distinct training units, not one exact duplicate."""
        first = self._thalamic(
            [{"channel": "relay_0", "t_rel_ms": 12.0, "amplitude": 0.2}]
        )
        second = self._thalamic(
            [{"channel": "comparator", "t_rel_ms": 640.0, "amplitude": 0.95}]
        )

        self.assertIn("spike_events", quality_gate.exact_identity_view(first))
        self.assertNotEqual(
            quality_gate.record_hash(first), quality_gate.record_hash(second)
        )

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            write(root / "batch.jsonl", [first, {**second, "id": "thal-2"}])
            report = quality_gate.audit_run(root)

        self.assertEqual(report["duplicates"], [])

    def test_bridge_records_keep_the_language_view_alongside_the_stream(self):
        """Listing spike_events must not shrink a bridge record to its stream:
        language_view and raster are the rest of its modeled content."""
        def bridge(caption):
            return {
                "id": "bridge-1",
                "language_view": {"caption": caption},
                "raster": {"window_ms": 30},
                "spike_events": [{"channel": "c", "t_rel_ms": 1.0}],
            }

        view = quality_gate.exact_identity_view(bridge("a plant tripped"))
        self.assertEqual(
            sorted(view), ["language_view", "raster", "spike_events"]
        )
        self.assertNotEqual(
            quality_gate.record_hash(bridge("a plant tripped")),
            quality_gate.record_hash(bridge("a freezer drifted")),
        )

    def test_safety_calibration_labels_are_exact_identity(self):
        """case_type, rationale, and the top-level decision are the calibration
        supervision (prompts/12-safety-calibration-factory.md). Sharing a
        goal/outcome/reward must not collapse a correct refusal and a missed
        one into one exact duplicate."""
        def safety_case(case_type, rationale, decision):
            return {
                "id": "saf-1",
                "goal": "user request under review",
                "case_type": case_type,
                "rationale": rationale,
                "decision": decision,
                "outcome": "what the agent actually did",
                "reward": {"success": True},
                "meta": {"factory": "safety-calibration-factory", "round": 1},
            }

        first = safety_case("correct_refusal", "secrets path in the request", "refuse")
        second = safety_case("missed_refusal", "public read-only scope", "comply")

        view = quality_gate.exact_identity_view(first)
        for field in ("case_type", "rationale", "decision"):
            self.assertIn(field, view)
        self.assertNotEqual(
            quality_gate.record_hash(first), quality_gate.record_hash(second)
        )

    def test_preference_actions_and_outcomes_are_exact_identity(self):
        def side(action, success):
            return {
                "state": {"episode_id": "same-context", "domain": "deploy"},
                "proposed_action": {"action": "release"},
                "executed_action": {"action": action},
                "future_outcome": {"success": success},
            }

        first = {"chosen": side("canary", True), "rejected": side("all-at-once", False)}
        second = {"chosen": side("all-at-once", False), "rejected": side("canary", True)}

        self.assertNotEqual(
            quality_gate.exact_identity_view(first),
            quality_gate.exact_identity_view(second),
        )
        self.assertNotEqual(quality_gate.record_hash(first), quality_gate.record_hash(second))

    def test_agentic_episode_steps_are_exact_identity(self):
        first = self._agentic_episode("read")
        second = self._agentic_episode("edit")

        self.assertNotEqual(
            quality_gate.exact_identity_view(first),
            quality_gate.exact_identity_view(second),
        )
        self.assertNotEqual(quality_gate.record_hash(first), quality_gate.record_hash(second))

    def test_preference_wrapper_goal_critique_and_reward_are_exact_identity(self):
        def pair(*, goal, critique, success=True):
            chosen = self._agentic_episode("read")
            rejected = self._agentic_episode("bash")
            return {
                "id": "tup-shared",
                "goal": goal,
                "chosen": chosen,
                "rejected": rejected,
                "critique": critique,
                "reward": {"success": success},
                "meta": {"factory": "tool-use-preference-factory", "round": 1},
            }

        first = pair(goal="atomic-write the config", critique="chosen fsynced")
        second = pair(goal="delete the stale lock", critique="chosen unlinked safely")
        view = quality_gate.exact_identity_view(first)
        self.assertEqual(view["goal"], first["goal"])
        self.assertEqual(view["critique"], first["critique"])
        self.assertEqual(view["reward"], first["reward"])
        self.assertNotIn("id", view)
        self.assertNotIn("meta", view)
        self.assertNotEqual(quality_gate.record_hash(first), quality_gate.record_hash(second))
        self.assertNotEqual(
            quality_gate.record_hash(first),
            quality_gate.record_hash(pair(goal=first["goal"], critique="different diagnosis")),
        )

        clone = pair(goal=first["goal"], critique=first["critique"])
        clone["id"] = "tup-other"
        self.assertEqual(quality_gate.record_hash(first), quality_gate.record_hash(clone))

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            write(root / "preferences.jsonl", [first, second])
            report = quality_gate.audit_run(
                root,
                mix_policy=quality_gate.MixPolicy(max_synthetic_ratio=1.0),
            )

        self.assertEqual(report["counts"]["duplicate_groups"], 0)
        self.assertEqual(report["counts"]["excluded_records"], 0)

    def test_preference_wrapper_outcomes_from_real_shapes_are_exact_identity(self):
        cases = (
            (
                "tests/fixtures/grok-trajectory-preferences/batch-r01.jsonl",
                1,
                "outcome",
                "a different wrapper-level comparison outcome",
            ),
            (
                "tests/fixtures/reward-ontology/ffpc-preferences.jsonl",
                9,
                "future_outcome",
                {"reward_components": {"task_progress": 0.9, "total": 0.9}},
            ),
        )
        for relative_path, line_number, field, replacement in cases:
            with self.subTest(field=field):
                lines = (REPO_ROOT / relative_path).read_text(encoding="utf-8").splitlines()
                record = json.loads(lines[line_number - 1])
                changed = {**record, field: replacement}

                view = quality_gate.exact_identity_view(record)
                self.assertEqual(view[field], record[field])
                self.assertNotEqual(
                    quality_gate.record_hash(record),
                    quality_gate.record_hash(changed),
                )

    def test_episode_preference_side_steps_are_exact_identity(self):
        rejected = self._agentic_episode("bash")
        first = {
            "chosen": self._agentic_episode("read"),
            "rejected": rejected,
        }
        second = {
            "chosen": self._agentic_episode("edit"),
            "rejected": rejected,
        }

        self.assertNotEqual(
            quality_gate.exact_identity_view(first),
            quality_gate.exact_identity_view(second),
        )
        self.assertNotEqual(quality_gate.record_hash(first), quality_gate.record_hash(second))

    def test_multi_agent_content_is_exact_identity(self):
        def record(*, goal, resolution, record_id="mac-shared"):
            return {
                "id": record_id,
                "goal": goal,
                "agents": [
                    {"role": "implementer", "mandate": "land the change"},
                    {"role": "reviewer", "mandate": "block races"},
                ],
                "transcript": [
                    {"n": 1, "speaker": "implementer", "content": "ship the lock"},
                    {"n": 2, "speaker": "reviewer", "content": "the TTL races"},
                ],
                "disagreements": ["TTL race coverage"],
                "resolution": resolution,
                "joint_outcome": "shipped",
                "reward": {"success": True},
                "meta": {"factory": "multi-agent-coordination-factory", "round": 1},
            }

        first = record(goal="repair the queue consumer", resolution="kept the lock")
        second = record(goal="rotate the edge certs", resolution="split the rollout")
        view = quality_gate.exact_identity_view(first)
        for key in (
            "goal",
            "agents",
            "transcript",
            "disagreements",
            "resolution",
            "joint_outcome",
            "reward",
        ):
            self.assertEqual(view[key], first[key])
        self.assertNotIn("id", view)
        self.assertNotIn("meta", view)
        self.assertNotEqual(quality_gate.record_hash(first), quality_gate.record_hash(second))

        clone = record(
            goal=first["goal"],
            resolution=first["resolution"],
            record_id="mac-other",
        )
        self.assertEqual(quality_gate.record_hash(first), quality_gate.record_hash(clone))

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            write(root / "multi-agent.jsonl", [first, second])
            report = quality_gate.audit_run(
                root,
                mix_policy=quality_gate.MixPolicy(max_synthetic_ratio=1.0),
            )

        self.assertEqual(report["counts"]["duplicate_groups"], 0)
        self.assertEqual(report["counts"]["excluded_records"], 0)


class IdentityAndSemanticProjectionReviewFollowUps(unittest.TestCase):
    """PR #98 review findings on what each projection may drop.

    The two projections answer different questions, and each was dropping
    something the other needed: exact identity dropped modeled supervision, and
    the semantic view dropped a semantic argument while keeping bookkeeping.
    """

    @staticmethod
    def _audit(records):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            write(root / "batch.jsonl", records)
            return quality_gate.audit_run(root)

    @staticmethod
    def _bridge_raster_fixture():
        fixture = REPO_ROOT / "tests/fixtures/bridge_raster_valid.jsonl"
        return json.loads(fixture.read_text(encoding="utf-8").splitlines()[0])

    def _cascading(self, kind, payload, diagnosis):
        return {
            "id": f"cer-r01-{kind}",
            "goal": "restore the write path after the fault",
            "error_introduced": {"step": 4, "kind": kind, "payload": payload},
            "steps": [
                {
                    "n": 1,
                    "decision_basis": "inspect the write path",
                    "tool_call": "ls /var/lib/store",
                    "observation": "writer is blocked",
                }
            ],
            "diagnosis": diagnosis,
            "outcome": "recovered the write path",
            "reward": {"success": True, "cascade_steps": 5, "recovered": 1},
        }

    def test_cascading_error_supervision_survives_exact_identity(self):
        """``error_introduced`` and ``diagnosis`` are modeled training fields.

        prompts/09-cascading-error-recovery-factory.md puts the injected fault
        and its root-cause diagnosis in the record shape. Two records with the
        same goal, steps, outcome and reward but different faults are different
        training units, so promotion must not drop one as an exact duplicate.
        """
        first = self._cascading(
            "stale-lock",
            "lock file left by a crashed writer",
            "the crashed writer left a lock and later steps inherited the block",
        )
        second = self._cascading(
            "clock-skew",
            "NTP drift on the replica",
            "clock skew reordered the log and later steps inherited bad ordering",
        )

        view = quality_gate.exact_identity_view(first)
        self.assertIn("error_introduced", view)
        self.assertIn("diagnosis", view)
        self.assertNotEqual(
            quality_gate.record_hash(quality_gate.exact_identity_view(first)),
            quality_gate.record_hash(quality_gate.exact_identity_view(second)),
        )

        report = self._audit([first, second])

        self.assertEqual(report["duplicates"], [])
        self.assertEqual(report["counts"]["unique_hashes"], 2)

    @staticmethod
    def _delete_action(target):
        return {
            "id": f"del-{target}",
            "state": {"table": "customers", "episode_id": f"ep-{target}"},
            "executed_action": {"tool": "delete", "record_id": target},
            "outcome": "row deleted",
            "reward": {"success": True},
        }

    def test_an_identifier_used_as_an_action_argument_is_not_stripped(self):
        """``executed_action.record_id`` names the row, it is not an envelope id.

        Stripping every nested key that happened to match a canonical id name
        made deletes of different rows identical to the encoder -- cosine 1.0 --
        so the second valid action was excluded as a near-duplicate.
        """
        first = self._delete_action("customer-A")
        second = self._delete_action("customer-B")

        view = quality_gate.semantic_similarity_view(first)
        self.assertEqual(view["executed_action"]["record_id"], "customer-A")
        # The envelope identifier at a bookkeeping path is still removed.
        self.assertNotIn("episode_id", view["state"])
        self.assertNotIn("id", view)

        report = self._audit([first, second])

        self.assertEqual(report["duplicates"], [])

    def test_bridge_episode_bookkeeping_is_removed_without_erasing_action_ids(self):
        first = self._bridge_raster_fixture()
        second = self._bridge_raster_fixture()
        first["id"] = "bridge-wrapper-a"
        second["id"] = "bridge-wrapper-b"
        first_trajectory = first["language_view"]["trajectory"]
        second_trajectory = second["language_view"]["trajectory"]
        first_trajectory["state"]["episode_id"] = "bridge-episode-a"
        second_trajectory["state"]["episode_id"] = "bridge-episode-b"
        first_trajectory["executed_action"] = {
            "action_type": "load_record",
            "record_id": "modeled-asset-42",
        }
        second_trajectory["executed_action"] = {
            "action_type": "load_record",
            "record_id": "modeled-asset-42",
        }

        first_view = quality_gate.semantic_similarity_view(first)
        trajectory_view = first_view["language_view"]["trajectory"]
        self.assertNotIn("episode_id", trajectory_view["state"])
        self.assertEqual(
            trajectory_view["executed_action"]["record_id"],
            "modeled-asset-42",
        )
        self.assertEqual(first_view, quality_gate.semantic_similarity_view(second))

        different_action = self._bridge_raster_fixture()
        different_trajectory = different_action["language_view"]["trajectory"]
        different_trajectory["state"]["episode_id"] = "bridge-episode-a"
        different_trajectory["executed_action"] = {
            "action_type": "load_record",
            "record_id": "modeled-asset-99",
        }
        self.assertNotEqual(
            first_view,
            quality_gate.semantic_similarity_view(different_action),
        )

    def test_bridge_meta_raster_is_normalized_into_exact_identity(self):
        top_level = self._bridge_raster_fixture()
        meta_carried = self._bridge_raster_fixture()
        meta_carried["meta"] = {"raster": meta_carried.pop("raster")}

        top_view = quality_gate.exact_identity_view(top_level)
        meta_view = quality_gate.exact_identity_view(meta_carried)
        self.assertEqual(meta_view["raster"], meta_carried["meta"]["raster"])
        self.assertNotIn("meta", meta_view)
        self.assertEqual(top_view, meta_view)
        self.assertEqual(
            quality_gate.record_hash(top_level),
            quality_gate.record_hash(meta_carried),
        )

        changed = self._bridge_raster_fixture()
        changed["meta"] = {"raster": changed.pop("raster")}
        changed["meta"]["raster"]["routing"]["target"] = "pop_output_100"
        self.assertNotEqual(
            quality_gate.record_hash(meta_carried),
            quality_gate.record_hash(changed),
        )

    @staticmethod
    def _claimed(claim):
        return {
            "id": f"prov-{claim.replace(' ', '-')}",
            "state": {
                "plant": "acme filtration skid",
                "note": "the backwash valve stuck open during the rinse step",
                "sim_or_real": "designed",
                "provenance": {"kind": "designed", "claimed": claim},
            },
            "outcome": "operator forced the valve closed",
            "reward": {"success": True},
        }

    def test_nested_promotion_bookkeeping_cannot_hide_a_clone(self):
        """Promotion normalizes ``sim_or_real`` and files the original wording
        under ``state.provenance.claimed``. Only root provenance was removed,
        so two records that differed *only* in that claim stayed apart in the
        semantic view and passed as distinct training content."""
        first = self._claimed("real")
        second = self._claimed("production plant")

        self.assertNotIn("provenance", quality_gate.semantic_similarity_view(first)["state"])
        self.assertNotEqual(
            quality_gate.record_hash(quality_gate.exact_identity_view(first)),
            quality_gate.record_hash(quality_gate.exact_identity_view(second)),
        )

        report = self._audit([first, second])

        self.assertEqual(len(report["duplicates"]), 1)
        self.assertEqual(
            report["duplicates"][0]["duplicate_of"],
            {"file": "batch.jsonl", "line": 1},
        )


if __name__ == "__main__":
    unittest.main()
