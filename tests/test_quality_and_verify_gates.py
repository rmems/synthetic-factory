#!/usr/bin/env python3
"""Regression tests for the quality gate.

The gate runs over untrusted generated JSONL, so malformed records must
produce a verdict rather than an exception, and provenance must be counted
from whichever field carries it.
"""

import copy
import json
import random
import sys
import tempfile
import unittest
import weakref
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "pipelines"))

from gate_fixtures import REPO, write  # noqa: E402
import quality_gate  # noqa: E402

EMBEDDING_FIXTURE = REPO / "tests" / "fixtures" / "embedding-dedup"

# Distinct enough that no pair is a near-duplicate, so a mix test blocks on the
# mix and nothing else.
DISTINCT_NOTES = [
    "the harbour crane lost hoist encoder agreement under a loaded spreader",
    "chlorine residual fell at the far zone sample point during full duty",
    "a feeder breaker tripped on instantaneous overcurrent mid reclose",
    "the vaccine freezer bank drifted upward after a defrost heater stuck",
    "turbine pitch bearing grease pressure spiked under yaw misalignment",
    "the milking robot logged a partial rinse against standing procedure",
]


def mix_records(synthetic, real):
    """``synthetic`` designed records and ``real`` unknown ones, all distinct."""
    kinds = ["designed"] * synthetic + ["unknown"] * real
    return [
        {"id": f"m-{index}", "state": {"sim_or_real": kind, "note": DISTINCT_NOTES[index]}}
        for index, kind in enumerate(kinds)
    ]


class QualityGate(unittest.TestCase):
    def test_record_hash_survives_malformed_preference_records(self):
        for malformed in (
            {"chosen": {"state": {"a": 1}}},           # no rejected side
            {"chosen": "not-an-object", "rejected": None},
            {"chosen": {}, "rejected": 5},
        ):
            digest = quality_gate.record_hash(malformed)
            self.assertIsInstance(digest, str)
            self.assertTrue(digest)

    def test_provenance_counts_sim_or_real_without_top_level_provenance(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            write(root / "f" / "batch.jsonl", [
                {"id": "a", "state": {"sim_or_real": "designed"}},
                {"id": "b", "state": {"sim_or_real": "simulated"}},
            ])
            report = quality_gate.audit_run(root)

        mix = report["mix"] if "mix" in report else report
        self.assertEqual(mix["provenance"].get("designed"), 1)
        self.assertEqual(mix["provenance"].get("simulated"), 1)
        self.assertEqual(mix["synthetic"], 2)

    def test_provenance_falls_back_to_top_level_kind(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            write(root / "f" / "batch.jsonl", [
                {"id": "a", "state": {}, "provenance": {"kind": "hil"}},
            ])
            report = quality_gate.audit_run(root)

        mix = report["mix"] if "mix" in report else report
        self.assertEqual(mix["provenance"].get("hil"), 1)

    def test_non_object_line_does_not_crash_provenance_counting(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            write(root / "batch.jsonl", [["not", "an", "object"], 7, "loose string"])
            report = quality_gate.audit_run(root)

        self.assertEqual(report["counts"]["total"], 3)
        self.assertEqual(report["mix"]["unlabeled"], 3)

    def test_preference_side_provenance_counts_once_per_pair(self):
        pair = {
            # A promoted wrapper can carry a generic top-level unknown stamp;
            # the shared side provenance is the record's meaningful label.
            "provenance": {"kind": "unknown"},
            "chosen": {
                "state": {"sim_or_real": "designed", "note": "preferred"},
            },
            "rejected": {
                "state": {"sim_or_real": "designed", "note": "unsafe"},
            },
        }
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            write(root / "preferences.jsonl", [pair])
            report = quality_gate.audit_run(root)

        self.assertEqual(report["mix"]["synthetic"], 1)
        self.assertEqual(report["mix"]["unlabeled"], 0)
        self.assertEqual(report["mix"]["provenance"], {"designed": 1})
        self.assertTrue(report["blocked"])
        self.assertTrue(any("synthetic_ratio 1.00" in b for b in report["blockers"]))

    def test_bridge_trajectory_provenance_precedes_wrapper_unknown(self):
        bridge = {
            "provenance": {"kind": "unknown"},
            "language_view": {
                "trajectory": {"state": {"sim_or_real": "hil", "note": "rig"}},
            },
        }
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            write(root / "bridges.jsonl", [bridge])
            report = quality_gate.audit_run(root)

        self.assertEqual(report["mix"]["provenance"], {"hil": 1})
        self.assertEqual(report["mix"]["synthetic"], 1)

    def test_stateless_factory_record_is_counted_as_designed(self):
        record = {
            "id": "agentic-1",
            "goal": "repair the queue consumer without dropping work",
            "steps": [],
            "outcome": "recovered",
            "meta": {"factory": "agentic-coding-trajectory-factory"},
            "provenance": {"kind": "unknown", "claimed": None},
        }
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            write(root / "episodes.jsonl", [record])
            report = quality_gate.audit_run(
                root,
                mix_policy=quality_gate.MixPolicy(max_synthetic_ratio=1.0),
            )

        self.assertEqual(report["mix"]["provenance"], {"designed": 1})
        self.assertEqual(report["mix"]["synthetic"], 1)
        self.assertEqual(report["mix"]["unlabeled"], 0)


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


class EmbeddingDedup(unittest.TestCase):
    """The fixture holds one near-duplicate pair that exact hashing cannot see."""

    def test_fixture_near_duplicate_is_excluded_with_a_reason(self):
        report = quality_gate.audit_run(EMBEDDING_FIXTURE)

        self.assertEqual(report["counts"]["total"], 7)
        # Exact hashing sees nothing: the pair differs inside the dedup view.
        self.assertEqual(report["counts"]["duplicate_groups"], 0)
        self.assertTrue(report["blocked"])
        self.assertEqual(report["counts"]["embedding_duplicate_groups"], 1)
        self.assertEqual(report["counts"]["excluded_records"], 1)

        duplicate = report["duplicates"][0]
        self.assertEqual(duplicate["kind"], "embedding")
        self.assertEqual(duplicate["file"], "batch-r01.jsonl")
        # Line 1 is the representative that is kept; line 2 is excluded.
        self.assertEqual(duplicate["line"], 2)
        self.assertEqual(duplicate["duplicate_of"], {"file": "batch-r01.jsonl", "line": 1})
        self.assertGreater(duplicate["similarity"], quality_gate.DEFAULT_EMBEDDING_THRESHOLD)
        self.assertIn("embedding near-duplicate", duplicate["reason"])
        self.assertIn("cosine", duplicate["reason"])

        cluster = [c for c in report["duplicate_clusters"] if c["kind"] == "embedding"][0]
        self.assertEqual(cluster["size"], 2)
        self.assertEqual(cluster["encoder"], quality_gate.EMBEDDING_ENCODER)
        self.assertEqual(cluster["representative"], {"file": "batch-r01.jsonl", "line": 1})
        self.assertIn(
            f"{len(report['blockers'])} embedding near-duplicate record(s)",
            " ".join(report["blockers"]),
        )

    def test_distinct_fixture_records_are_not_flagged(self):
        report = quality_gate.audit_run(EMBEDDING_FIXTURE)
        excluded = {(d["file"], d["line"]) for d in report["duplicates"]}
        # Every record other than the planted near-duplicate survives.
        self.assertEqual(excluded, {("batch-r01.jsonl", 2)})
        self.assertEqual(report["embedding"]["compared_records"], 7)

    def test_result_is_deterministic(self):
        first = quality_gate.audit_run(EMBEDDING_FIXTURE)
        second = quality_gate.audit_run(EMBEDDING_FIXTURE)
        self.assertEqual(first, second)

    def test_raising_the_threshold_above_the_pair_unblocks(self):
        report = quality_gate.audit_run(EMBEDDING_FIXTURE, threshold=0.999)
        self.assertFalse(report["blocked"])
        self.assertEqual(report["duplicates"], [])
        self.assertEqual(report["threshold"], 0.999)

    def test_embedding_pass_can_be_disabled(self):
        report = quality_gate.audit_run(EMBEDDING_FIXTURE, embedding_dedup=False)
        self.assertFalse(report["blocked"])
        self.assertEqual(report["duplicates"], [])
        self.assertFalse(report["embedding"]["enabled"])
        self.assertIn(
            "embedding dedup disabled — only exact-hash duplicates were excluded",
            report["warnings"],
        )

    def test_candidate_cap_is_not_truncated_when_exactly_full(self):
        report = quality_gate.audit_run(EMBEDDING_FIXTURE, max_embedding_pairs=1)
        self.assertEqual(report["embedding"]["candidate_pairs"], 1)
        self.assertFalse(report["embedding"]["truncated"])
        self.assertFalse(any("recall is partial" in w for w in report["warnings"]))

    def test_candidate_cap_reports_only_when_an_extra_pair_is_omitted(self):
        signature = tuple(range(quality_gate.EMBEDDING_MINHASH_SLOTS))
        pairs, truncated = quality_gate._candidate_pairs(
            [(0, signature), (1, signature), (2, signature)], max_pairs=1
        )
        self.assertEqual(len(pairs), 1)
        self.assertTrue(truncated)

    def test_candidate_truncation_blocks_the_audit(self):
        records = [
            {
                "id": f"coding-{index}",
                "goal": "repair the same queue consumer and verify every retry",
                # Distinct modeled outcomes keep exact-hash identity apart so
                # the embedding pass still sees three near-duplicate records.
                "outcome": f"retry-pass-{index}",
            }
            for index in range(3)
        ]
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            write(root / "episodes.jsonl", records)
            report = quality_gate.audit_run(root, max_embedding_pairs=1)

        self.assertTrue(report["embedding"]["truncated"])
        self.assertTrue(report["blocked"])
        self.assertTrue(
            any("cannot be certified" in blocker for blocker in report["blockers"])
        )

    def test_string_operators_remain_semantically_distinct(self):
        records = [
            {"state": {"predicate": "queue_depth < hard_limit"}},
            {"state": {"predicate": "queue_depth > hard_limit"}},
        ]
        token_sets = [quality_gate.embedding_tokens(record) for record in records]
        self.assertNotEqual(token_sets[0], token_sets[1])
        self.assertTrue(any("str-op:<" in token for token in token_sets[0]))
        self.assertTrue(any("str-op:>" in token for token in token_sets[1]))
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            write(root / "batch.jsonl", records)
            report = quality_gate.audit_run(root)
        self.assertEqual(report["duplicates"], [])

    def test_null_and_empty_values_have_typed_sentinels(self):
        records = [
            {"state": {"value": None}},
            {"state": {"value": ""}},
            {"state": {"value": []}},
            {"state": {"value": {}}},
        ]
        token_sets = [quality_gate.embedding_tokens(record) for record in records]
        self.assertEqual(len({frozenset(tokens) for tokens in token_sets}), 4)
        for marker, tokens in zip(
            ("null", "str-empty", "list-empty", "dict-empty"), token_sets
        ):
            self.assertTrue(any(marker in token for token in tokens), marker)

    def test_case_sensitive_identifiers_remain_distinct(self):
        records = [
            {"state": {"principal": "User"}},
            {"state": {"principal": "user"}},
        ]
        token_sets = [quality_gate.embedding_tokens(record) for record in records]
        self.assertNotEqual(token_sets[0], token_sets[1])
        self.assertTrue(any("str-case:User" in token for token in token_sets[0]))
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            write(root / "batch.jsonl", records)
            report = quality_gate.audit_run(root)
        self.assertEqual(report["duplicates"], [])

    def test_repeated_sequence_order_is_position_qualified(self):
        records = [
            {"state": {"sequence": ["alpha", "beta", "alpha", "gamma", "alpha"]}},
            {"state": {"sequence": ["alpha", "gamma", "alpha", "beta", "alpha"]}},
        ]
        token_sets = [quality_gate.embedding_tokens(record) for record in records]
        self.assertNotEqual(token_sets[0], token_sets[1])
        self.assertTrue(any("/i:1" in token for token in token_sets[0]))
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            write(root / "batch.jsonl", records)
            report = quality_gate.audit_run(root)
        self.assertEqual(report["duplicates"], [])

    def test_field_paths_distinguish_equal_values_under_different_keys(self):
        records = [
            {"state": {"sim_or_real": "unknown", "pressure_status": "critical"}},
            {"state": {"sim_or_real": "unknown", "temperature_status": "critical"}},
        ]
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            write(root / "batch.jsonl", records)
            report = quality_gate.audit_run(root)

        self.assertNotEqual(
            quality_gate.embedding_tokens(records[0]),
            quality_gate.embedding_tokens(records[1]),
        )
        self.assertEqual(report["duplicates"], [])

    def test_numeric_features_preserve_sign_and_type(self):
        records = [
            {"executed_action": {"setpoint": -5}},
            {"executed_action": {"setpoint": 5}},
            {"executed_action": {"setpoint": "5"}},
        ]
        token_sets = [quality_gate.embedding_tokens(record) for record in records]
        self.assertEqual(len({frozenset(tokens) for tokens in token_sets}), 3)
        self.assertTrue(any("int:-5" in token for token in token_sets[0]))
        self.assertTrue(any("int:5" in token for token in token_sets[1]))
        self.assertTrue(any("str-case:5" in token for token in token_sets[2]))
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            write(root / "batch.jsonl", records)
            report = quality_gate.audit_run(root)

        self.assertEqual(report["duplicates"], [])

    def test_mapping_insertion_order_does_not_change_embedding_tokens(self):
        keys = [f"field_{index:03d}" for index in range(120)]
        forward = {key: f"value_{index:03d}" for index, key in enumerate(keys)}
        reverse = {
            key: f"value_{index:03d}"
            for index, key in reversed(list(enumerate(keys)))
        }
        self.assertEqual(
            quality_gate.embedding_tokens({"state": forward}),
            quality_gate.embedding_tokens({"state": reverse}),
        )

        reverse[keys[60]] = "one_minor_change"
        records = [{"state": forward}, {"state": reverse}]
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            write(root / "batch.jsonl", records)
            report = quality_gate.audit_run(root)

        self.assertEqual(report["counts"]["embedding_duplicate_groups"], 1)
        self.assertGreater(
            report["duplicates"][0]["similarity"],
            quality_gate.DEFAULT_EMBEDDING_THRESHOLD,
        )

    def test_unicode_text_is_preserved_in_embedding_tokens(self):
        records = [
            {"state": {"sim_or_real": "unknown", "note": "冷却水温度上昇"}},
            {"state": {"sim_or_real": "unknown", "note": "港口起重机故障"}},
        ]
        token_sets = [quality_gate.embedding_tokens(record) for record in records]
        self.assertTrue(any("str-char:冷" in token for token in token_sets[0]))
        self.assertTrue(any("str-char:港" in token for token in token_sets[1]))
        self.assertTrue(
            any(
                "str-char:冷" in token and "str-char:却" in token
                for token in token_sets[0]
            )
        )
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            write(root / "batch.jsonl", records)
            report = quality_gate.audit_run(root)

        self.assertEqual(report["duplicates"], [])

    def test_unsegmented_scripts_use_grapheme_fallback(self):
        samples = {
            "japanese": "クレーンの温度を下げる",
            "thai": "ระบบควบคุมลดอุณหภูมิน้ำหล่อเย็น",
        }
        for language, note in samples.items():
            with self.subTest(language=language):
                tokens = quality_gate.embedding_tokens({"state": {"note": note}})
                character_tokens = [
                    token
                    for token in tokens
                    if "str-char:" in token and quality_gate._BIGRAM_SEP not in token
                ]
                self.assertGreaterEqual(len(character_tokens), 4)

    def test_unsegmented_minimal_edit_is_an_embedding_duplicate(self):
        common = (
            "港口起重机正在执行集装箱装卸作业控制系统持续监测吊具位置载荷风速"
            "制动器温度液压压力电机电流和安全联锁状态操作员依据标准程序确认所有"
            "传感器读数稳定并记录每个控制周期的执行结果"
        )
        records = [
            {"state": {"note": common * 2 + "随后降低冷却水设定值保持设备稳定运行"}},
            {"state": {"note": common * 2 + "随后提高冷却水设定值保持设备稳定运行"}},
        ]
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            write(root / "batch.jsonl", records)
            report = quality_gate.audit_run(root)

        self.assertEqual(report["embedding"]["candidate_pairs"], 1)
        self.assertEqual(report["counts"]["embedding_duplicate_groups"], 1)
        self.assertEqual(len(report["duplicates"]), 1)
        self.assertGreater(
            report["duplicates"][0]["similarity"],
            quality_gate.DEFAULT_EMBEDDING_THRESHOLD,
        )

    def _audit_pair(self, first, second):
        """Audit two one-record-per-line records and return the report."""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            write(root / "batch.jsonl", [first, second])
            return quality_gate.audit_run(root)

    def test_unsegmented_reordering_is_not_an_embedding_duplicate(self):
        """A grapheme bag plus adjacent bigrams is not injective over
        sequences: 甲乙甲丙甲 and 甲丙甲乙甲 share both, so the encoder scored
        them at cosine 1.0 and the blocking gate excluded one even though
        their exact hashes differ (Codex #98, quality_gate.py:461)."""
        first = {"id": "u-1", "state": {"note": "甲乙甲丙甲"}}
        second = {"id": "u-2", "state": {"note": "甲丙甲乙甲"}}

        self.assertNotEqual(
            quality_gate.record_hash(first), quality_gate.record_hash(second)
        )
        self.assertNotEqual(
            quality_gate.embedding_tokens(first), quality_gate.embedding_tokens(second)
        )

        report = self._audit_pair(first, second)
        self.assertEqual(report["duplicates"], [])
        self.assertEqual(report["counts"]["embedding_duplicate_groups"], 0)

    def test_whitespace_boundaries_survive_in_code_strings(self):
        """Whitespace is semantic in agentic coding and shell content. These
        pairs have different exact hashes but used to produce identical token
        counters and cosine 1.0 (Codex #98, quality_gate.py:395)."""
        pairs = {
            "shell path": (
                "curl https://safe /admin",
                "curl https://safe/admin",
            ),
            "python indentation": (
                "if x:\n    return 1",
                "if x:\nreturn 1",
            ),
        }
        for label, (left, right) in pairs.items():
            with self.subTest(case=label):
                first = {"id": "w-1", "state": {"cmd": left}}
                second = {"id": "w-2", "state": {"cmd": right}}

                self.assertNotEqual(
                    quality_gate.record_hash(first), quality_gate.record_hash(second)
                )
                self.assertNotEqual(
                    quality_gate.embedding_tokens(first),
                    quality_gate.embedding_tokens(second),
                )

                report = self._audit_pair(first, second)
                self.assertEqual(report["duplicates"], [])

    def test_word_order_survives_the_whitespace_encoding(self):
        """The gap rides on the following unit instead of becoming a token of
        its own, so adjacent-word bigrams still relate word to word. A
        standalone whitespace token would make these two identical."""
        first = {"id": "o-1", "state": {"note": "alpha beta gamma delta"}}
        second = {"id": "o-2", "state": {"note": "alpha gamma beta delta"}}

        self.assertNotEqual(
            quality_gate.embedding_tokens(first), quality_gate.embedding_tokens(second)
        )
        self.assertEqual(self._audit_pair(first, second)["duplicates"], [])

    def test_corpus_idf_is_released_before_the_pair_phase(self):
        """idf spans the whole corpus vocabulary and its last read is the
        vector loop. It must not stay resident while _candidate_pairs
        materializes pairs and the cosine loop scores them, which is where the
        largest structures are allocated (mergestorm #98, quality_gate.py:731).

        The probe is an object owned only by the idf dict, so its weakref dies
        exactly when idf is released.
        """
        class Probe:
            """Weak-referenceable stand-in; a plain dict cannot be weakref'd."""

        seen = {}
        real_vector = quality_gate._tfidf_vector
        real_pairs = quality_gate._candidate_pairs

        def spy_vector(tokens, idf):
            if "probe" not in seen:
                probe = Probe()
                # Never looked up: _tfidf_vector only indexes record tokens.
                idf["\x00idf-liveness-probe"] = probe
                seen["probe"] = weakref.ref(probe)
            return real_vector(tokens, idf)

        def spy_pairs(signatures, max_pairs):
            seen["alive_at_pair_phase"] = seen["probe"]() is not None
            return real_pairs(signatures, max_pairs)

        records = [
            {"id": f"idf-{index}", "state": {"note": note}}
            for index, note in enumerate(DISTINCT_NOTES)
        ]
        with mock.patch.object(quality_gate, "_tfidf_vector", spy_vector), \
                mock.patch.object(quality_gate, "_candidate_pairs", spy_pairs):
            with tempfile.TemporaryDirectory() as td:
                root = Path(td)
                write(root / "batch.jsonl", records)
                quality_gate.audit_run(root)

        self.assertIn("alive_at_pair_phase", seen)
        self.assertFalse(seen["alive_at_pair_phase"])

    def test_frequency_aware_sketch_recalls_high_tf_cosine_pair(self):
        repeated = "saturated " * 2000
        records = [
            {"id": "tf-a", "goal": repeated + "alpha"},
            {"id": "tf-b", "goal": repeated + "beta"},
        ]
        token_sets = [set(quality_gate.embedding_tokens(record)) for record in records]
        unweighted_jaccard = len(token_sets[0] & token_sets[1]) / len(
            token_sets[0] | token_sets[1]
        )
        # Premise for this regression: on the raw token *set* these two
        # records overlap only half, and 8 bands of 4 recall an overlap
        # that weak barely 40% of the time. The frequency-aware tier
        # sketch is what turns the 2000 repeats into a reliable candidate;
        # the exact cosine asserted below is far above this set overlap.
        self.assertLessEqual(unweighted_jaccard, 0.5)
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            write(root / "episodes.jsonl", records)
            report = quality_gate.audit_run(root)

        self.assertEqual(report["embedding"]["candidate_pairs"], 1)
        self.assertEqual(report["embedding"]["candidate_sketch"], "weighted-tier-minhash/1")
        self.assertEqual(report["counts"]["embedding_duplicate_groups"], 1)
        self.assertGreater(
            report["duplicates"][0]["similarity"],
            quality_gate.DEFAULT_EMBEDDING_THRESHOLD,
        )
        self.assertLess(
            unweighted_jaccard, report["duplicates"][0]["similarity"]
        )

    def test_semantic_view_removes_top_level_and_episode_ids(self):
        common = "verify queue retries and preserve every acknowledged work item"
        stateless = [
            {
                "id": "coding-a",
                "goal": common,
                "meta": {"round": 1, "factory": "agentic-coding-trajectory-factory"},
            },
            {
                "id": "coding-b",
                "goal": common,
                "meta": {"round": 2, "factory": "agentic-coding-trajectory-factory"},
            },
        ]
        self.assertEqual(
            quality_gate.exact_identity_view(stateless[0]),
            quality_gate.exact_identity_view(stateless[1]),
        )
        self.assertEqual(
            quality_gate.semantic_similarity_view(stateless[0]),
            quality_gate.semantic_similarity_view(stateless[1]),
        )
        records = [
            {
                "id": "wrapper-a",
                "state": {
                    "episode_id": "episode-a",
                    "sim_or_real": "unknown",
                    "note": common,
                },
                "meta": {"round": 1, "factory": "thalamic-trajectory-factory"},
            },
            {
                "id": "wrapper-b",
                "state": {
                    "episode_id": "episode-b",
                    "sim_or_real": "unknown",
                    "note": common,
                },
                "meta": {"round": 2, "factory": "thalamic-trajectory-factory"},
            },
        ]
        self.assertNotEqual(quality_gate.record_hash(records[0]), quality_gate.record_hash(records[1]))
        self.assertEqual(
            quality_gate.semantic_similarity_view(records[0]),
            quality_gate.semantic_similarity_view(records[1]),
        )
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            write(root / "batch.jsonl", records)
            report = quality_gate.audit_run(root)

        self.assertEqual(report["counts"]["duplicate_groups"], 0)
        self.assertEqual(report["counts"]["embedding_duplicate_groups"], 1)

    def test_transitive_cluster_points_every_exclusion_at_retained_record(self):
        common = " ".join(f"common_{index:03d}" for index in range(80))
        records = [
            {"state": {"note": common + " alpha alpha"}},
            {"state": {"note": common + " alpha beta"}},
            {"state": {"note": common + " beta beta"}},
        ]
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            write(root / "batch.jsonl", records)
            report = quality_gate.audit_run(root, threshold=0.90)

        self.assertEqual(report["counts"]["embedding_duplicate_groups"], 1)
        self.assertEqual(len(report["duplicates"]), 2)
        for duplicate in report["duplicates"]:
            self.assertEqual(
                duplicate["duplicate_of"], {"file": "batch.jsonl", "line": 1}
            )
        self.assertEqual(
            report["duplicates"][1]["matched_with"],
            {"file": "batch.jsonl", "line": 2},
        )
        self.assertIn("linked by cosine", report["duplicate_clusters"][0]["reason"])

    def test_invalid_threshold_is_rejected(self):
        with self.assertRaises(ValueError):
            quality_gate.audit_run(EMBEDDING_FIXTURE, threshold=1.5)

    def test_threshold_one_is_rejected_instead_of_disabling_dedup(self):
        with self.assertRaisesRegex(ValueError, r"\[0, 1\)"):
            quality_gate.audit_run(EMBEDDING_FIXTURE, threshold=1.0)

    def test_negative_thresholds_are_rejected_not_silently_under_reported(self):
        """TF-IDF weights here are strictly positive, so every cosine is in
        [0, 1] and a negative threshold declares every pair a near-duplicate --
        including disjoint-vocabulary pairs the LSH candidate scheme never
        proposes. Scoring only candidates would exit clean while failing the
        configured policy, so the range excludes it (Codex #98)."""
        for threshold in (-0.5, -1.0, -0.000001):
            with self.subTest(threshold=threshold):
                with self.assertRaisesRegex(ValueError, r"\[0, 1\)"):
                    quality_gate.audit_run(EMBEDDING_FIXTURE, threshold=threshold)

    def test_disjoint_records_are_not_candidates_so_zero_stays_the_floor(self):
        """The premise of the bound above: two records sharing no vocabulary
        produce no candidate pair, so no threshold below their cosine of 0
        could ever have been honoured."""
        records = [
            {"id": "d-1", "state": {"note": DISTINCT_NOTES[0]}},
            {"id": "d-2", "state": {"note": DISTINCT_NOTES[1]}},
        ]
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            write(root / "batch.jsonl", records)
            report = quality_gate.audit_run(root, threshold=0.0)

        self.assertEqual(report["duplicates"], [])

    def test_planted_duplicates_are_all_recovered(self):
        """LSH banding may only cost recall, so guard it with planted clones.

        Each clone differs from its source only in ``state.tick`` — invisible
        to exact hashing, ~0.99 cosine to the encoder.
        """
        rng = random.Random(20260823)
        vocabulary = [f"w{index}" for index in range(600)]
        records = [
            {
                "id": f"p-{index}",
                "state": {
                    "sim_or_real": "designed",
                    "tick": index,
                    "observation": " ".join(rng.choice(vocabulary) for _ in range(120)),
                },
            }
            for index in range(120)
        ]
        planted = set()
        for index in rng.sample(range(len(records)), 12):
            clone = copy.deepcopy(records[index])
            clone["id"] = f"p-{index}-clone"
            clone["state"]["tick"] = 900000 + index
            planted.add(clone["id"])
            records.append(clone)
        rng.shuffle(records)
        identifiers = [record["id"] for record in records]

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            write(root / "batch.jsonl", records)
            report = quality_gate.audit_run(
                root, mix_policy=quality_gate.MixPolicy(max_synthetic_ratio=1.0)
            )

        # Exact hashing sees none of them.
        self.assertEqual(report["counts"]["duplicate_groups"], 0)
        self.assertEqual(report["counts"]["embedding_duplicate_groups"], len(planted))
        flagged = {identifiers[d["line"] - 1] for d in report["duplicates"]}
        self.assertEqual(len(flagged), len(planted))
        # Every flagged record is either a clone or the source it was cloned
        # from — nothing unrelated was swept in.
        for identifier in flagged:
            self.assertTrue(
                identifier in planted or f"{identifier}-clone" in planted,
                f"unexpected exclusion: {identifier}",
            )


class MixEnforcement(unittest.TestCase):
    def test_mix_outside_policy_blocks_instead_of_warning(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            write(root / "batch.jsonl", mix_records(synthetic=3, real=1))
            report = quality_gate.audit_run(root)

        self.assertAlmostEqual(report["mix"]["synthetic_ratio"], 0.75)
        self.assertTrue(report["blocked"])
        self.assertTrue(any("synthetic_ratio 0.75" in b for b in report["blockers"]))
        self.assertEqual(report["duplicates"], [])

    def test_mix_inside_tolerance_warns_but_passes(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            write(root / "batch.jsonl", mix_records(synthetic=2, real=3))
            report = quality_gate.audit_run(root)

        self.assertAlmostEqual(report["mix"]["synthetic_ratio"], 0.4)
        self.assertFalse(report["blocked"])
        self.assertTrue(any("synthetic_ratio 0.40" in w for w in report["warnings"]))

    def test_mix_on_target_is_silent(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            write(root / "batch.jsonl", mix_records(synthetic=1, real=4))
            report = quality_gate.audit_run(root)

        self.assertAlmostEqual(report["mix"]["synthetic_ratio"], 0.2)
        self.assertFalse(report["blocked"])
        self.assertEqual(report["warnings"], [])

    def test_ceiling_is_configurable(self):
        policy = quality_gate.MixPolicy(max_synthetic_ratio=0.9)
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            write(root / "batch.jsonl", mix_records(synthetic=3, real=1))
            report = quality_gate.audit_run(root, mix_policy=policy)

        self.assertFalse(report["blocked"])
        self.assertEqual(report["mix_policy"]["max_synthetic_ratio"], 0.9)

    def test_default_policy_is_thirty_seventy_and_blocking(self):
        policy = quality_gate.MixPolicy()
        self.assertEqual(policy.target, 0.30)
        self.assertEqual(policy.ceiling, 0.50)
        self.assertTrue(policy.as_dict()["blocking"])

    def test_optional_floor_blocks_a_corpus_with_too_little_synthetic(self):
        policy = quality_gate.MixPolicy(min_synthetic_ratio=0.25)
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            write(root / "batch.jsonl", mix_records(synthetic=0, real=5))
            report = quality_gate.audit_run(root, mix_policy=policy)

        self.assertTrue(report["blocked"])
        self.assertTrue(any("floor 0.25" in b for b in report["blockers"]))

    def test_unlabeled_records_are_reported_and_can_block(self):
        records = [
            {"id": f"u-{i}", "state": {"note": DISTINCT_NOTES[i]}} for i in range(4)
        ]
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            write(root / "batch.jsonl", records)
            warn_only = quality_gate.audit_run(root)
            blocking = quality_gate.audit_run(
                root, mix_policy=quality_gate.MixPolicy(max_unlabeled_ratio=0.5)
            )

        self.assertEqual(warn_only["mix"]["unlabeled_ratio"], 1.0)
        self.assertFalse(warn_only["blocked"])
        self.assertTrue(any("unlabeled_ratio" in w for w in warn_only["warnings"]))
        self.assertTrue(blocking["blocked"])
        self.assertTrue(any("unlabeled_ratio 1.00" in b for b in blocking["blockers"]))

    def test_unsatisfiable_policy_is_rejected(self):
        with self.assertRaises(ValueError):
            quality_gate.MixPolicy(min_synthetic_ratio=0.9).validate()
        with self.assertRaises(ValueError):
            quality_gate.MixPolicy(target=2.0).validate()

    def test_empty_run_does_not_block_on_mix(self):
        with tempfile.TemporaryDirectory() as td:
            report = quality_gate.audit_run(Path(td))
        self.assertEqual(report["counts"]["total"], 0)
        self.assertFalse(report["blocked"])

    def test_empty_run_blocks_when_a_synthetic_floor_is_configured(self):
        with tempfile.TemporaryDirectory() as td:
            report = quality_gate.audit_run(
                Path(td),
                mix_policy=quality_gate.MixPolicy(min_synthetic_ratio=0.1),
            )
        self.assertTrue(report["blocked"])
        self.assertTrue(any("floor 0.10" in blocker for blocker in report["blockers"]))


class CuratedManifest(unittest.TestCase):
    def run_cli(self, argv):
        """Run the CLI quietly and return its exit code."""
        with redirect_stdout(StringIO()), redirect_stderr(StringIO()):
            with self.assertRaises(SystemExit) as caught:
                quality_gate.main(argv)
        return caught.exception.code

    def test_manifest_carries_mix_ratio_and_duplicate_report(self):
        with tempfile.TemporaryDirectory() as td:
            manifest_path = Path(td) / "curated" / "quality-manifest.json"
            code = self.run_cli(
                [str(EMBEDDING_FIXTURE), "--json", "--manifest", str(manifest_path)]
            )
            self.assertEqual(code, 1)
            manifest = json.loads(manifest_path.read_text())

        self.assertEqual(manifest["schema"], "quality-manifest/1")
        self.assertEqual(manifest["run_dir"], str(EMBEDDING_FIXTURE))
        self.assertIn("synthetic_ratio", manifest["mix"])
        self.assertEqual(manifest["mix_policy"]["max_synthetic_ratio"], 0.5)
        self.assertEqual(len(manifest["duplicate_clusters"]), 1)
        self.assertEqual(manifest["duplicate_clusters"][0]["kind"], "embedding")
        self.assertTrue(manifest["duplicates"][0]["reason"])
        self.assertIn("unique_shapes", manifest["reward_shapes"])

    def test_cli_exits_zero_on_a_clean_tree(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "run"
            write(root / "batch.jsonl", mix_records(synthetic=1, real=4))
            self.assertEqual(self.run_cli([str(root)]), 0)

    def test_cli_rejects_an_unsatisfiable_policy(self):
        code = self.run_cli([str(EMBEDDING_FIXTURE), "--min-synthetic-ratio", "0.9"])
        self.assertEqual(code, 2)

    def test_cli_rejects_missing_run_without_writing_manifest(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            missing = root / "missing-run"
            manifest = root / "curated" / "quality-manifest.json"
            code = self.run_cli([str(missing), "--manifest", str(manifest)])
            self.assertEqual(code, 2)
            self.assertFalse(manifest.exists())

    def test_cli_refuses_to_overwrite_an_audited_jsonl_with_manifest(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "run"
            batch = root / "batch.jsonl"
            write(batch, mix_records(synthetic=1, real=4))
            before = batch.read_bytes()

            code = self.run_cli([str(root), "--manifest", str(batch)])

            self.assertEqual(code, 2)
            self.assertEqual(batch.read_bytes(), before)

    def test_cli_refuses_existing_or_in_run_manifest_targets(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            root = base / "run"
            write(root / "batch.jsonl", mix_records(synthetic=1, real=4))
            existing = base / "existing.json"
            existing.write_text("sentinel\n")

            existing_code = self.run_cli(
                [str(root), "--manifest", str(existing)]
            )
            in_run = root / "quality-manifest.json"
            in_run_code = self.run_cli([str(root), "--manifest", str(in_run)])

            self.assertEqual(existing_code, 2)
            self.assertEqual(existing.read_text(), "sentinel\n")
            self.assertEqual(in_run_code, 2)
            self.assertFalse(in_run.exists())

    def test_cli_does_not_write_a_manifest_unless_asked(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "run"
            write(root / "batch.jsonl", mix_records(synthetic=1, real=4))
            self.assertEqual(self.run_cli([str(root)]), 0)
            self.assertEqual([p.name for p in sorted(root.iterdir())], ["batch.jsonl"])


class RewardShapeReport(unittest.TestCase):
    def test_reward_vocabulary_is_reported_not_blocked(self):
        records = [
            {"id": "r-0", "state": {"sim_or_real": "unknown", "note": DISTINCT_NOTES[0]},
             "reward_components": {"process": 0.1, "world": -0.2}},
            {"id": "r-1", "state": {"sim_or_real": "unknown", "note": DISTINCT_NOTES[1]},
             "reward_components": {"process": 0.3, "latency_ms": 12}},
        ]
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            write(root / "batch.jsonl", records)
            report = quality_gate.audit_run(root)

        rewards = report["reward_shapes"]
        self.assertEqual(rewards["records_with_reward_components"], 2)
        self.assertEqual(rewards["unique_component_keys"], 3)
        self.assertEqual(rewards["unique_shapes"], 2)
        self.assertFalse(report["blocked"])



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
