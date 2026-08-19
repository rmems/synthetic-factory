#!/usr/bin/env python3
"""Focused tests for deterministic identity and provenance curation."""

from __future__ import annotations

import copy
import hashlib
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PIPELINES = REPO / "pipelines"
sys.path.insert(0, str(PIPELINES))

import curate_identity as identity  # noqa: E402


def thalamic(claim="real", **overrides):
    record = {
        "state": {
            "sim_or_real": claim,
            "episode_id": "legacy-episode-17",
            "domain": "fixture",
        },
        "proposed_action": {"action_type": "noop"},
        "safety_decision": {"decision": "ACCEPT", "rationale": "bounded"},
        "executed_action": {"action_type": "noop"},
        "future_outcome": {"success": "full"},
        "reward_components": {"task": 1.0, "total": 1.0},
        "meta": {"id": "legacy-meta-id"},
    }
    record.update(overrides)
    return record


def source(record, path="thalamic-trajectory-factory/batch-r02.jsonl", line=1, digest=None):
    return identity.SourceRecord(record, path, line, digest)


class TestCanonicalIdentity(unittest.TestCase):
    def test_thalamic_assigns_root_id_and_preserves_legacy_forms(self):
        raw = thalamic()
        before = copy.deepcopy(raw)

        result = identity.curate_record(source(raw))

        self.assertEqual(result.action, "retained")
        self.assertEqual(raw, before, "the source object must not be mutated")
        self.assertRegex(
            result.record["id"],
            r"^sfcur-thalamic-record-[0-9a-f]{64}$",
        )
        self.assertEqual(result.record["meta"]["id"], "legacy-meta-id")
        self.assertEqual(result.record["state"]["episode_id"], "legacy-episode-17")
        original_paths = {
            item["path"] for item in result.mapping["original_ids"]
        }
        self.assertEqual(original_paths, {"/meta/id", "/state/episode_id"})
        self.assertEqual(result.mapping["output_id"], result.record["id"])

    def test_ids_depend_on_source_identity_and_version_not_legacy_id(self):
        first = thalamic()
        second = thalamic()
        second["meta"]["id"] = "different-legacy-id"

        first_result = identity.curate_record(source(first))
        second_result = identity.curate_record(source(second))

        self.assertEqual(first_result.record["id"], second_result.record["id"])
        changed_line = identity.curate_record(source(first, line=2))
        self.assertNotEqual(first_result.record["id"], changed_line.record["id"])

    def test_cross_factory_same_content_cannot_collide(self):
        raw = thalamic("simulated")
        left = source(raw, "thalamic-trajectory-factory/batch-r08.jsonl", 1)
        right = source(raw, "agentic-coding-trajectory-factory/batch-r08.jsonl", 1)

        results = identity.curate_records([left, right])

        ids = [
            item["output_id"]
            for result in results
            for item in result.mapping["id_mappings"]
        ]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertNotEqual(results[0].record["id"], results[1].record["id"])

    def test_duplicate_source_coordinate_is_detected_independently(self):
        raw = thalamic("simulated")
        item = source(raw, "thalamic-trajectory-factory/batch-r08.jsonl", 1)
        with self.assertRaisesRegex(identity.CanonicalIdCollision, "collision"):
            identity.curate_records([item, item])

    def test_output_is_stable_when_input_order_changes(self):
        records = [
            source(thalamic("designed"), line=1),
            source(thalamic("simulated"), line=2),
        ]
        forward = identity.curate_records(records)
        reverse = identity.curate_records(reversed(records))
        forward_by_line = {
            result.mapping["source"]["line"]: result.record["id"] for result in forward
        }
        reverse_by_line = {
            result.mapping["source"]["line"]: result.record["id"] for result in reverse
        }
        self.assertEqual(forward_by_line, reverse_by_line)

    def test_source_coordinate_contract_rejects_ambiguous_paths(self):
        raw = thalamic()
        bad = (
            "/absolute/batch.jsonl",
            "../escape/batch.jsonl",
            "factory/./batch.jsonl",
            "batch.jsonl",
        )
        for path in bad:
            with self.subTest(path=path):
                with self.assertRaises(identity.IdentityCurationError):
                    identity.curate_record(source(raw, path=path))
        with self.assertRaisesRegex(identity.IdentityCurationError, "positive integer"):
            identity.curate_record(source(raw, line=0))

    def test_explicit_source_hash_is_preserved_with_basis(self):
        digest = hashlib.sha256(b"exact source line").hexdigest()
        result = identity.curate_record(source(thalamic(), digest=digest))
        self.assertEqual(result.mapping["source"]["sha256"], digest)
        self.assertEqual(
            result.mapping["source"]["hash_basis"],
            "source-json-line-sha256",
        )


class TestCanonicalProvenance(unittest.TestCase):
    def test_real_claim_maps_to_designed_and_is_reversible(self):
        result = identity.curate_record(source(thalamic("real (production plant)")))
        self.assertEqual(result.record["state"]["sim_or_real"], "designed")
        self.assertEqual(
            result.record["state"]["provenance"],
            {"kind": "designed", "claimed": "real (production plant)"},
        )
        self.assertEqual(
            result.record["provenance"],
            {"kind": "designed", "claimed": "real (production plant)"},
        )
        mapping = result.mapping["provenance_mappings"][0]
        self.assertTrue(mapping["original"]["sim_or_real"]["present"])
        self.assertEqual(
            mapping["original"]["sim_or_real"]["value"],
            "real (production plant)",
        )
        self.assertFalse(mapping["original"]["state_provenance"]["present"])

    def test_simulation_hil_and_existing_canonical_claims(self):
        claims = {
            "high-fidelity plant simulation": "simulated",
            "hardware-in-the-loop flight rig": "hil",
            "designed": "designed",
        }
        for claim, expected in claims.items():
            with self.subTest(claim=claim):
                result = identity.curate_record(source(thalamic(claim)))
                self.assertEqual(result.record["state"]["sim_or_real"], expected)
                self.assertEqual(result.record["state"]["provenance"]["kind"], expected)

    def test_missing_or_ambiguous_state_claim_is_explicitly_excluded(self):
        for claim in (None, "decision-support staging context", 17):
            with self.subTest(claim=claim):
                result = identity.curate_record(source(thalamic(claim)))
                self.assertEqual(result.action, "exclude")
                self.assertIsNone(result.record)
                self.assertEqual(
                    result.mapping["reason_codes"],
                    ["identity.unresolved_provenance"],
                )
                self.assertEqual(
                    result.mapping["unresolved_provenance"][0]["path"],
                    "/state",
                )

    def test_existing_canonical_provenance_can_resolve_a_missing_claim(self):
        raw = thalamic(None)
        raw["state"].pop("sim_or_real")
        raw["provenance"] = {"kind": "hil", "claimed": "HIL bench"}

        result = identity.curate_record(source(raw))

        self.assertEqual(result.action, "retained")
        self.assertEqual(result.record["state"]["sim_or_real"], "hil")
        self.assertEqual(result.record["state"]["provenance"]["claimed"], "HIL bench")

    def test_normalizing_curated_output_is_record_idempotent(self):
        first = identity.curate_record(source(thalamic("real")))
        second = identity.curate_record(source(first.record))
        self.assertEqual(first.record, second.record)
        self.assertEqual(
            identity.canonical_json(first.record),
            identity.canonical_json(second.record),
        )


class TestSupportedRecordShapes(unittest.TestCase):
    def test_preference_gets_root_and_distinct_nested_ids(self):
        pair = {
            "chosen": thalamic("high-fidelity simulation", meta={"id": "chosen-old"}),
            "rejected": thalamic("high-fidelity simulation", meta={"id": "rejected-old"}),
            "critique": "same context, better process",
            "meta": {"id": "pair-old"},
        }
        result = identity.curate_record(
            source(
                pair,
                "failure-as-fuel-preference-cascade/batch-r06.jsonl",
                2,
            )
        )

        self.assertEqual(result.action, "retained")
        ids = {
            result.record["id"],
            result.record["chosen"]["id"],
            result.record["rejected"]["id"],
        }
        self.assertEqual(len(ids), 3)
        self.assertEqual(result.record["provenance"]["kind"], "simulated")
        for side in ("chosen", "rejected"):
            self.assertEqual(result.record[side]["state"]["sim_or_real"], "simulated")
        self.assertEqual(len(result.mapping["id_mappings"]), 3)
        self.assertEqual(len(result.mapping["provenance_mappings"]), 3)
        original_paths = {item["path"] for item in result.mapping["original_ids"]}
        self.assertEqual(
            original_paths,
            {
                "/meta/id",
                "/chosen/meta/id",
                "/chosen/state/episode_id",
                "/rejected/meta/id",
                "/rejected/state/episode_id",
            },
        )

    def test_bridge_gets_root_and_nested_trajectory_identity(self):
        bridge = {
            "pair_id": "legacy-pair",
            "language_view": {
                "trajectory": thalamic(
                    "hardware-in-the-loop (flight rig)",
                    meta={"id": "legacy-trajectory"},
                )
            },
            "spike_events": [{"channel": "x", "t_rel_ms": 1, "amplitude": 1}],
        }
        result = identity.curate_record(
            source(
                bridge,
                "neuromorphic-event-language-bridge/batch-r03.jsonl",
                1,
            )
        )

        trajectory = result.record["language_view"]["trajectory"]
        self.assertEqual(result.action, "retained")
        self.assertNotEqual(result.record["id"], trajectory["id"])
        self.assertEqual(trajectory["state"]["sim_or_real"], "hil")
        self.assertEqual(result.record["provenance"]["kind"], "hil")
        root_original = result.mapping["id_mappings"][0]["original_ids"]
        self.assertIn({"path": "/pair_id", "value": "legacy-pair"}, root_original)

    def test_agentic_coding_episode_has_source_grounded_designed_provenance(self):
        episode = {
            "goal": "repair a deterministic fixture",
            "steps": [{"tool_call": "inspect", "observation": "failing"}],
            "outcome": "fixed",
            "reward": 1.0,
            "meta": {"factory": identity.EPISODE_FACTORY, "round": 2},
        }
        result = identity.curate_record(
            source(
                episode,
                "agentic-coding-trajectory-factory/episodes.jsonl",
                1,
            )
        )

        self.assertEqual(result.action, "retained")
        self.assertRegex(result.record["id"], r"^sfcur-episode-record-[0-9a-f]{64}$")
        self.assertEqual(result.record["provenance"]["kind"], "designed")
        self.assertEqual(
            result.record["provenance"]["basis"],
            "synthetic_factory_episode_shape",
        )

    def test_episode_from_another_factory_is_not_silently_labeled(self):
        episode = {
            "goal": "fixture",
            "steps": [{"tool_call": "inspect", "observation": "ok"}],
            "outcome": "done",
            "reward": 1,
        }
        result = identity.curate_record(
            source(episode, "unknown-factory/episodes.jsonl", 1)
        )
        self.assertEqual(result.action, "exclude")
        self.assertEqual(
            result.mapping["unresolved_provenance"][0]["reason"],
            "episode_source_factory_not_authoritative",
        )

    def test_malformed_nested_shape_is_excluded_with_reason(self):
        pair = {"chosen": thalamic(), "rejected": None, "critique": "bad shape"}
        result = identity.curate_record(
            source(pair, "failure-as-fuel-preference-cascade/bad.jsonl", 1)
        )
        self.assertEqual(result.action, "exclude")
        self.assertEqual(
            result.mapping["reason_codes"],
            ["identity.invalid_nested_shape"],
        )

    def test_excluded_nested_record_still_maps_recoverable_legacy_ids(self):
        pair = {
            "chosen": thalamic(None, meta={"id": "chosen-legacy"}),
            "rejected": thalamic(None, meta={"id": "rejected-legacy"}),
            "critique": "missing provenance",
            "meta": {"id": "pair-legacy"},
        }
        result = identity.curate_record(
            source(pair, "failure-as-fuel-preference-cascade/preferences.jsonl", 1)
        )
        self.assertEqual(result.action, "exclude")
        paths = {item["path"] for item in result.mapping["original_ids"]}
        self.assertIn("/meta/id", paths)
        self.assertIn("/chosen/meta/id", paths)
        self.assertIn("/rejected/meta/id", paths)


if __name__ == "__main__":
    unittest.main()
