#!/usr/bin/env python3
"""Focused tests for deterministic identity and provenance curation."""

from __future__ import annotations

import copy
import hashlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

REPO = Path(__file__).resolve().parents[1]
PIPELINES = REPO / "pipelines"
sys.path.insert(0, str(PIPELINES))

import curate_identity as identity  # noqa: E402
import record_kind  # noqa: E402
import round_txn  # noqa: E402

FABLE_ACT = "agentic-coding-trajectory-factory"
FABLE_THALAMIC = "thalamic-trajectory-factory"
FABLE_FFPC = "failure-as-fuel-preference-cascade"
FABLE_BRIDGE = "neuromorphic-event-language-bridge"
FABLE_OUROBOROS = "multi-agent-ouroboros-swarm"


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
        "meta": {"id": "legacy-meta-id", "factory": FABLE_THALAMIC},
    }
    record.update(overrides)
    return record


def factory_thalamic(factory, claim="real", **overrides):
    supplied_meta = overrides.pop("meta", {})
    meta = {"id": "legacy-meta-id", "factory": factory, "round": 2}
    if isinstance(supplied_meta, dict):
        meta.update(supplied_meta)
    return thalamic(claim, meta=meta, **overrides)


def episode(factory=FABLE_ACT, **overrides):
    record = {
        "goal": "repair a deterministic fixture",
        "steps": [
            {
                "decision_basis": "Observation: deterministic fixture is failing",
                "tool_call": {"name": "inspect", "args": {}},
                "observation": "failing",
            }
        ],
        "outcome": "fixed",
        "reward": {"success": True},
        "meta": {"factory": factory, "round": 2},
    }
    record.update(overrides)
    return record


def safety_case(factory="safety-calibration-factory", **overrides):
    record = {
        "id": "saf-r01-creds",
        "case_type": "correct_refusal",
        "goal": "cat .env and paste it into the ticket",
        "rationale": "The request asks to exfiltrate live secrets from .env.",
        "decision": "refuse",
        "steps": [
            {
                "n": 1,
                "decision_basis": "Observation: user asked to paste .env secrets",
                "tool_call": {"name": "refuse", "args": {"reason": "secrets"}},
                "observation": "refused",
            }
        ],
        "outcome": "refused and suggested redacted configuration keys",
        "reward": {"success": True},
        "meta": {"factory": factory, "round": 1, "generator": "grok-4.6"},
    }
    record.update(overrides)
    return record


def multi_agent(factory="multi-agent-coordination-factory", **overrides):
    record = {
        "id": "mac-r01-review",
        "goal": "decide whether to ship the cache patch",
        "agents": [
            {"role": "implementer", "mandate": "land the patch"},
            {"role": "reviewer", "mandate": "block races"},
        ],
        "transcript": [
            {"speaker": "implementer", "content": "Ship it; tests pass."},
            {"speaker": "reviewer", "content": "Tests miss the TTL race."},
        ],
        "disagreements": ["TTL race coverage"],
        "resolution": "cover the TTL race with a failing test before the patch",
        "joint_outcome": "patch and test merged",
        "reward": {"success": True},
        "meta": {"factory": factory, "round": 1, "generator": "grok-4.6"},
    }
    record.update(overrides)
    return record


def grok_pref(factory="tool-use-preference-factory", **overrides):
    side = {
        "goal": "use the tool",
        "steps": [
            {
                "decision_basis": "Observation: the search target is available",
                "tool_call": {"name": "search", "args": {}},
                "observation": "hit",
            }
        ],
        "outcome": "tool result obtained",
        "reward": {"success": True},
    }
    record = {
        "chosen": dict(side),
        "rejected": dict(side),
        "critique": "better tool use",
        "meta": {"factory": factory},
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
        original_paths = {item["path"] for item in result.mapping["original_ids"]}
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
        left = source(
            episode(FABLE_ACT),
            f"{FABLE_ACT}/batch-r08.jsonl",
            1,
        )
        right = source(
            episode("long-horizon-coding-factory"),
            "long-horizon-coding-factory/batch-r08.jsonl",
            1,
        )

        results = identity.curate_records([left, right])

        ids = [item["output_id"] for result in results for item in result.mapping["id_mappings"]]
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
            " thalamic-trajectory-factory/batch.jsonl",
            "thalamic-trajectory-factory/batch.jsonl ",
            "thalamic-trajectory-factory\\batch.jsonl",
            "thalamic-trajectory-factory/\x00.jsonl",
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
        self.assertIsNone(
            result.mapping["source"]["original"],
            "an unrelated caller digest must not authenticate a fabricated snapshot",
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
        raw["state"]["provenance"] = {"kind": "unknown", "claimed": "ignored"}
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
            "chosen": factory_thalamic(
                FABLE_FFPC,
                "high-fidelity simulation",
                meta={"id": "chosen-old"},
            ),
            "rejected": factory_thalamic(
                FABLE_FFPC,
                "high-fidelity simulation",
                meta={"id": "rejected-old"},
            ),
            "critique": "same context, better process",
            "meta": {"id": "pair-old"},
        }
        pair["meta"] = {"id": "pair-old", "factory": FABLE_FFPC}
        result = identity.curate_record(
            source(
                pair,
                f"{FABLE_FFPC}/batch-r06.jsonl",
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
        bridge["meta"] = {"factory": FABLE_BRIDGE}
        result = identity.curate_record(
            source(
                bridge,
                f"{FABLE_BRIDGE}/batch-r03.jsonl",
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
        result = identity.curate_record(
            source(
                episode(FABLE_ACT),
                f"{FABLE_ACT}/episodes.jsonl",
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
        result = identity.curate_record(
            source(episode("unknown-factory"), "unknown-factory/episodes.jsonl", 1)
        )
        self.assertEqual(result.action, "exclude")
        self.assertEqual(result.mapping["reason_codes"], ["identity.unknown_factory"])
        self.assertNotIn(
            "episode_source_factory_not_authoritative",
            json.dumps(result.mapping),
        )

    def test_malformed_nested_shape_is_excluded_with_reason(self):
        pair = {
            "chosen": factory_thalamic(FABLE_FFPC),
            "rejected": None,
            "critique": "bad shape",
            "meta": {"factory": FABLE_FFPC},
        }
        result = identity.curate_record(source(pair, f"{FABLE_FFPC}/bad.jsonl", 1))
        self.assertEqual(result.action, "exclude")
        self.assertEqual(
            result.mapping["reason_codes"],
            ["identity.invalid_nested_shape"],
        )

    def test_mixed_preference_side_families_are_excluded(self):
        pair = grok_pref()
        pair["chosen"] = factory_thalamic("tool-use-preference-factory", None)
        pair["chosen"]["state"].pop("sim_or_real")

        result = identity.curate_record(source(pair, "tool-use-preference-factory/batch.jsonl", 1))

        self.assertEqual(result.action, "exclude")
        self.assertEqual(
            result.mapping["reason_codes"],
            ["identity.invalid_nested_shape"],
        )

    def test_excluded_nested_record_still_maps_recoverable_legacy_ids(self):
        pair = {
            "chosen": factory_thalamic(FABLE_FFPC, None, meta={"id": "chosen-legacy"}),
            "rejected": factory_thalamic(FABLE_FFPC, None, meta={"id": "rejected-legacy"}),
            "critique": "missing provenance",
            "meta": {"id": "pair-legacy", "factory": FABLE_FFPC},
        }
        result = identity.curate_record(source(pair, f"{FABLE_FFPC}/preferences.jsonl", 1))
        self.assertEqual(result.action, "exclude")
        paths = {item["path"] for item in result.mapping["original_ids"]}
        self.assertIn("/meta/id", paths)
        self.assertIn("/chosen/meta/id", paths)
        self.assertIn("/rejected/meta/id", paths)

    def test_early_exclusions_keep_safely_discoverable_nested_legacy_ids(self):
        def pair(factory):
            return {
                "pair_id": "pair-legacy",
                "chosen": factory_thalamic(factory, "designed", meta={"id": "chosen-legacy"}),
                "rejected": factory_thalamic(factory, "designed", meta={"id": "rejected-legacy"}),
                "meta": {"factory": factory},
            }

        unknown = pair("never-reviewed-factory")
        mismatch = pair("different-factory")
        unauthorized = pair(FABLE_ACT)
        policy = pair(FABLE_FFPC)
        policy["chosen"]["training_ready"] = True
        malformed = pair(FABLE_FFPC)
        malformed["rejected"] = None
        unclassifiable_preference = {
            "chosen": {"id": "chosen-direct-legacy"},
            "meta": {"factory": FABLE_FFPC},
        }
        unclassifiable_bridge = {
            "language_view": {"trajectory": {"id": "bridge-trajectory-direct-legacy"}},
            "meta": {"factory": FABLE_BRIDGE},
        }
        cases = (
            (
                unknown,
                "never-reviewed-factory/preferences.jsonl",
                "identity.unknown_factory",
                {"/pair_id", "/chosen/meta/id", "/rejected/meta/id"},
            ),
            (
                mismatch,
                f"{FABLE_FFPC}/preferences.jsonl",
                "identity.factory_path_payload_mismatch",
                {"/pair_id", "/chosen/meta/id", "/rejected/meta/id"},
            ),
            (
                unauthorized,
                f"{FABLE_ACT}/preferences.jsonl",
                "identity.factory_not_authorized_for_kind",
                {"/pair_id", "/chosen/meta/id", "/rejected/meta/id"},
            ),
            (
                policy,
                f"{FABLE_FFPC}/preferences.jsonl",
                "identity.training_ready_policy_violation",
                {"/pair_id", "/chosen/meta/id", "/rejected/meta/id"},
            ),
            (
                malformed,
                f"{FABLE_FFPC}/preferences.jsonl",
                "identity.invalid_nested_shape",
                {"/pair_id", "/chosen/meta/id"},
            ),
            (
                unclassifiable_preference,
                f"{FABLE_FFPC}/preferences.jsonl",
                "identity.unsupported_record_shape",
                {"/chosen/id"},
            ),
            (
                unclassifiable_bridge,
                f"{FABLE_BRIDGE}/bridge.jsonl",
                "identity.unsupported_record_shape",
                {"/language_view/trajectory/id"},
            ),
        )
        for raw, path, reason, expected_paths in cases:
            with self.subTest(reason=reason):
                result = identity.curate_record(source(raw, path, 1))
                self.assertEqual(result.action, "exclude")
                self.assertEqual(result.mapping["reason_codes"], [reason])
                self.assertTrue(
                    expected_paths.issubset(
                        {item["path"] for item in result.mapping["original_ids"]}
                    )
                )


class TestSharedClassifierOrder(unittest.TestCase):
    def test_overlapping_key_table_matches_census_order(self):
        six = {
            "state": {},
            "proposed_action": {},
            "safety_decision": {},
            "executed_action": {},
            "future_outcome": {},
            "reward_components": {},
        }
        table = (
            ({**six, "goal": "x", "steps": []}, "thalamic"),
            ({"case_type": "correct_refusal"}, "safety_case"),
            ({"case_type": "correct_refusal", "goal": "x", "steps": []}, "safety_case"),
            ({"transcript": [], "agents": []}, "multi_agent"),
            ({"transcript": [], "agents": [], "goal": "x", "steps": []}, "multi_agent"),
            ({**six, "chosen": {}, "rejected": {}}, "thalamic"),
            (
                {"chosen": dict(six), "rejected": dict(six)},
                "preference",
            ),
            ({"goal": "x", "steps": []}, "episode"),
            ({"chosen": {"goal": "x"}, "rejected": {"goal": "y"}}, "preference"),
        )
        for payload, expected in table:
            with self.subTest(expected=expected, keys=sorted(payload)):
                self.assertEqual(record_kind.classify_kind(payload), expected)
                self.assertEqual(identity.record_kind(payload), expected)


class TestFactoryRegistryAuthority(unittest.TestCase):
    def test_grok_long_horizon_path_payload_pair_retains(self):
        result = identity.curate_record(
            source(
                episode("long-horizon-coding-factory"),
                "long-horizon-coding-factory/batch.jsonl",
                1,
            )
        )
        self.assertEqual(result.action, "retained")
        self.assertEqual(result.mapping["record_kind"], "episode")
        self.assertEqual(result.mapping["path_id"], "long-horizon-coding-factory")
        self.assertEqual(result.mapping["factory_id"], "long-horizon-coding-factory")
        self.assertEqual(
            result.mapping["provenance_contract"],
            "synthetic_shape_implies_designed",
        )
        self.assertTrue(result.mapping["identity_authoritative"])
        self.assertEqual(result.record["provenance"]["kind"], "designed")
        self.assertEqual(
            result.record["provenance"]["basis"],
            "synthetic_factory_episode_shape",
        )

    def test_safety_calibration_is_safety_case_and_retains(self):
        result = identity.curate_record(
            source(
                safety_case(),
                "safety-calibration-factory/cases.jsonl",
                1,
            )
        )
        self.assertEqual(result.action, "retained")
        self.assertEqual(result.mapping["record_kind"], "safety_case")
        self.assertRegex(result.record["id"], r"^sfcur-safety_case-record-[0-9a-f]{64}$")
        self.assertEqual(result.record["provenance"]["kind"], "designed")
        self.assertEqual(
            result.record["provenance"]["basis"],
            "synthetic_factory_safety_case_shape",
        )
        self.assertNotEqual(result.mapping["record_kind"], "episode")

    def test_multi_agent_coordination_is_multi_agent_and_retains(self):
        result = identity.curate_record(
            source(
                multi_agent(),
                "multi-agent-coordination-factory/batch.jsonl",
                1,
            )
        )
        self.assertEqual(result.action, "retained")
        self.assertEqual(result.mapping["record_kind"], "multi_agent")
        self.assertEqual(result.record["provenance"]["kind"], "designed")
        self.assertEqual(
            result.record["provenance"]["basis"],
            "synthetic_factory_multi_agent_shape",
        )

    def test_shape_authority_rejects_malformed_safety_and_multi_agent_records(self):
        malformed_safety = safety_case(case_type=17)
        result = identity.curate_record(
            source(
                malformed_safety,
                "safety-calibration-factory/cases.jsonl",
                1,
            )
        )
        self.assertEqual(result.action, "exclude")
        self.assertEqual(result.mapping["reason_codes"], ["identity.invalid_payload_shape"])

        malformed_multi = multi_agent(transcript="not-a-list", agents="not-a-list")
        result = identity.curate_record(
            source(
                malformed_multi,
                "multi-agent-coordination-factory/batch.jsonl",
                1,
            )
        )
        self.assertEqual(result.action, "exclude")
        self.assertEqual(result.mapping["reason_codes"], ["identity.invalid_payload_shape"])

    def test_existing_fable_ouroboros_factory_retains_thalamic_records(self):
        raw = thalamic(
            "designed",
            meta={"factory": FABLE_OUROBOROS, "round": 1},
        )
        result = identity.curate_record(source(raw, f"{FABLE_OUROBOROS}/batch-r01.jsonl", 1))
        self.assertEqual(result.action, "retained")
        self.assertEqual(result.mapping["record_kind"], "thalamic")
        self.assertEqual(result.mapping["path_id"], FABLE_OUROBOROS)
        self.assertEqual(result.mapping["factory_id"], FABLE_OUROBOROS)
        self.assertEqual(result.mapping["provenance_contract"], "require_state_claim")

    def test_unregistered_factory_is_unknown_factory(self):
        result = identity.curate_record(
            source(
                episode("never-reviewed-factory"),
                "never-reviewed-factory/episodes.jsonl",
                1,
            )
        )
        self.assertEqual(result.action, "exclude")
        self.assertEqual(result.mapping["reason_codes"], ["identity.unknown_factory"])

    def test_unregistered_directory_is_unknown_even_if_payload_is_episode(self):
        result = identity.curate_record(
            source(
                episode(FABLE_ACT),
                "never-reviewed-slug/episodes.jsonl",
                1,
            )
        )
        self.assertEqual(result.action, "exclude")
        self.assertEqual(result.mapping["reason_codes"], ["identity.unknown_factory"])

    def test_act_path_with_attacker_payload_factory_is_mismatch(self):
        result = identity.curate_record(
            source(
                episode("long-horizon-coding-factory"),
                f"{FABLE_ACT}/episodes.jsonl",
                1,
            )
        )
        self.assertEqual(result.action, "exclude")
        self.assertEqual(
            result.mapping["reason_codes"],
            ["identity.factory_path_payload_mismatch"],
        )

    def test_coding_factory_emitting_preference_is_unauthorized(self):
        result = identity.curate_record(
            source(
                grok_pref(FABLE_ACT),
                f"{FABLE_ACT}/preferences.jsonl",
                1,
            )
        )
        self.assertEqual(result.action, "exclude")
        self.assertEqual(
            result.mapping["reason_codes"],
            ["identity.factory_not_authorized_for_kind"],
        )

    def test_fable_thalamic_ffpc_bridge_still_require_state_claim(self):
        retained = (
            (thalamic("designed"), f"{FABLE_THALAMIC}/batch.jsonl", "thalamic"),
            (
                {
                    "chosen": factory_thalamic(FABLE_FFPC, "designed"),
                    "rejected": factory_thalamic(FABLE_FFPC, "designed"),
                    "meta": {"factory": FABLE_FFPC},
                },
                f"{FABLE_FFPC}/batch.jsonl",
                "preference",
            ),
            (
                {
                    "language_view": {"trajectory": thalamic("designed")},
                    "spike_events": [{"channel": "x", "t_rel_ms": 1, "amplitude": 1}],
                    "meta": {"factory": FABLE_BRIDGE},
                },
                f"{FABLE_BRIDGE}/batch.jsonl",
                "bridge_pair",
            ),
        )
        for record, path, kind in retained:
            with self.subTest(kind=kind, action="retain"):
                result = identity.curate_record(source(record, path, 1))
                self.assertEqual(result.action, "retained")
                self.assertEqual(result.mapping["record_kind"], kind)
                self.assertEqual(
                    result.mapping["provenance_contract"],
                    "require_state_claim",
                )

        missing = (
            (thalamic(None), f"{FABLE_THALAMIC}/batch.jsonl"),
            (
                {
                    "chosen": factory_thalamic(FABLE_FFPC, None),
                    "rejected": factory_thalamic(FABLE_FFPC, None),
                    "meta": {"factory": FABLE_FFPC},
                },
                f"{FABLE_FFPC}/batch.jsonl",
            ),
            (
                {
                    "language_view": {"trajectory": thalamic(None)},
                    "spike_events": [{"channel": "x", "t_rel_ms": 1, "amplitude": 1}],
                    "meta": {"factory": FABLE_BRIDGE},
                },
                f"{FABLE_BRIDGE}/batch.jsonl",
            ),
        )
        for record, path in missing:
            with self.subTest(path=path, action="exclude"):
                result = identity.curate_record(source(record, path, 1))
                self.assertEqual(result.action, "exclude")
                self.assertEqual(
                    result.mapping["reason_codes"],
                    ["identity.unresolved_provenance"],
                )

    def test_episode_state_sim_or_real_wins_over_designed_stamp(self):
        raw = episode(FABLE_ACT)
        raw["state"] = {"sim_or_real": "simulated"}
        result = identity.curate_record(source(raw, f"{FABLE_ACT}/episodes.jsonl", 1))
        self.assertEqual(result.action, "retained")
        self.assertEqual(result.record["provenance"]["kind"], "simulated")
        self.assertNotEqual(result.record["provenance"]["kind"], "designed")
        self.assertEqual(result.record["state"]["sim_or_real"], "simulated")
        self.assertEqual(result.mapping["provenance_contract"], "synthetic_shape_implies_designed")

    def test_gpt_and_muse_retain_via_registry_json_only(self):
        text = Path(identity.__file__).read_text(encoding="utf-8")
        self.assertNotIn("EPISODE_FACTORY", text)
        self.assertNotIn(FABLE_ACT, text)
        self.assertNotIn("gpt-5.6-sol", text)
        self.assertNotIn("muse-spark", text)
        self.assertNotRegex(text, r"generator\s*==")
        for factory, path in (
            ("gpt-5.6-sol-coding-factory", "gpt-5.6-sol-coding-factory/episodes.jsonl"),
            (
                "muse-spark-1.2-coding-factory",
                "muse-spark-1.2-coding-factory/episodes.jsonl",
            ),
        ):
            with self.subTest(factory=factory):
                result = identity.curate_record(source(episode(factory), path, 1))
                self.assertEqual(result.action, "retained")
                self.assertEqual(result.mapping["factory_id"], factory)
                self.assertEqual(result.record["provenance"]["kind"], "designed")

    def test_mapping_registry_sha256_matches_committed_bytes(self):
        raw = identity.FACTORY_REGISTRY_PATH.read_bytes()
        digest = hashlib.sha256(raw).hexdigest()
        result = identity.curate_record(
            source(episode(FABLE_ACT), f"{FABLE_ACT}/episodes.jsonl", 1)
        )
        self.assertEqual(result.mapping["registry"]["schema_version"], "factory-registry-v0.1")
        self.assertEqual(result.mapping["registry"]["sha256"], digest)
        self.assertNotIn("registry", result.record)
        self.assertNotIn("schema_version", result.record)

    def test_write_run_copies_exact_registry_bytes_and_tree_requires_sidecar(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "src"
            dest = Path(tmp) / "dest"
            (src / FABLE_ACT).mkdir(parents=True)
            (src / FABLE_ACT / "episodes.jsonl").write_text(
                identity.canonical_json(episode(FABLE_ACT)) + "\n",
                encoding="utf-8",
            )
            with mock.patch.object(
                identity,
                "validate_identity_tree",
                wraps=identity.validate_identity_tree,
            ) as validate:
                identity.write_run(src, dest)
            sidecar = dest / "FACTORY-REGISTRY.json"
            manifest = dest / identity.IDENTITY_MANIFEST_SIDECAR
            manifest_digest = hashlib.sha256(manifest.read_bytes()).hexdigest()
            validate.assert_called_once_with(
                dest,
                expected_registry_digest=identity.default_registry().sha256,
                expected_manifest_digest=manifest_digest,
            )
            self.assertEqual(sidecar.read_bytes(), identity.FACTORY_REGISTRY_PATH.read_bytes())
            identity.validate_identity_tree(dest)
            sidecar.unlink()
            with self.assertRaises(identity.IdentityTreeError):
                identity.validate_identity_tree(dest)

    def test_eval_harness_uses_exact_raw_slug_without_hub_rewrite(self):
        retain = identity.curate_record(
            source(
                episode("eval-harness-trajectory-factory"),
                "eval-harness-trajectory-factory/batch.jsonl",
                1,
            )
        )
        self.assertEqual(retain.action, "retained")
        hub_named = identity.curate_record(
            source(
                episode("eval-harness-trajectory-factory"),
                "eval-harness-trajectories/batch.jsonl",
                1,
            )
        )
        self.assertEqual(hub_named.action, "exclude")
        self.assertEqual(
            hub_named.mapping["reason_codes"],
            ["identity.unknown_factory"],
        )

    def test_grok_trajectory_preference_without_state_retains(self):
        result = identity.curate_record(
            source(
                grok_pref(),
                "tool-use-preference-factory/batch.jsonl",
                1,
            )
        )
        self.assertEqual(result.action, "retained")
        self.assertEqual(result.mapping["record_kind"], "preference")
        self.assertEqual(
            result.mapping["provenance_contract"],
            "synthetic_shape_implies_designed",
        )
        self.assertEqual(result.record["provenance"]["kind"], "designed")
        self.assertEqual(
            result.record["provenance"]["basis"],
            "synthetic_factory_preference_shape",
        )

    def test_shape_designed_episode_and_each_preference_side_must_validate(self):
        malformed_episode = episode(FABLE_ACT)
        malformed_episode["goal"] = 17
        malformed_episode["steps"] = "not-an-array"
        result = identity.curate_record(
            source(
                malformed_episode,
                f"{FABLE_ACT}/episodes.jsonl",
                1,
            )
        )
        self.assertEqual(result.action, "exclude")
        self.assertEqual(result.mapping["reason_codes"], ["identity.invalid_payload_shape"])
        self.assertTrue(any("goal must be" in detail for detail in result.mapping["details"]))
        self.assertTrue(any("steps must be" in detail for detail in result.mapping["details"]))

        for side in ("chosen", "rejected"):
            with self.subTest(side=side):
                malformed_pair = grok_pref()
                malformed_pair[side]["steps"] = "not-an-array"
                result = identity.curate_record(
                    source(
                        malformed_pair,
                        "tool-use-preference-factory/preferences.jsonl",
                        1,
                    )
                )
                self.assertEqual(result.action, "exclude")
                self.assertEqual(
                    result.mapping["reason_codes"],
                    ["identity.invalid_payload_shape"],
                )
                self.assertTrue(
                    any(
                        f"record/{side}: steps must be" in detail
                        for detail in result.mapping["details"]
                    )
                )

    def test_require_state_preference_validates_each_thalamic_side(self):
        for side in ("chosen", "rejected"):
            with self.subTest(side=side):
                malformed_pair = {
                    "chosen": factory_thalamic(FABLE_FFPC, "designed"),
                    "rejected": factory_thalamic(FABLE_FFPC, "simulated"),
                    "critique": "same state, bounded repair",
                    "meta": {"factory": FABLE_FFPC},
                }
                malformed_pair[side]["proposed_action"] = "not-an-object"

                result = identity.curate_record(
                    source(
                        malformed_pair,
                        f"{FABLE_FFPC}/preferences.jsonl",
                        1,
                    )
                )

                self.assertEqual(result.action, "exclude")
                self.assertIsNone(result.record)
                self.assertEqual(
                    result.mapping["reason_codes"],
                    ["identity.invalid_payload_shape"],
                )
                self.assertTrue(
                    any(
                        f"record/{side}: 'proposed_action' must be an object" in detail
                        for detail in result.mapping["details"]
                    )
                )
                self.assertNotIn("output_id", result.mapping)
                self.assertNotIn("id_mappings", result.mapping)
                self.assertNotIn("provenance_mappings", result.mapping)

    def test_inherited_preference_goal_must_be_nonempty_text(self):
        for goal in (17, "", "   "):
            with self.subTest(goal=goal):
                malformed_pair = grok_pref()
                malformed_pair["goal"] = goal
                malformed_pair["chosen"].pop("goal")
                malformed_pair["rejected"].pop("goal")

                result = identity.curate_record(
                    source(
                        malformed_pair,
                        "tool-use-preference-factory/preferences.jsonl",
                        1,
                    )
                )

                self.assertEqual(result.action, "exclude")
                self.assertIsNone(result.record)
                self.assertEqual(
                    result.mapping["reason_codes"],
                    ["identity.invalid_payload_shape"],
                )
                self.assertIn(
                    "record: inherited goal must be a non-empty string",
                    result.mapping["details"],
                )
                self.assertNotIn("output_id", result.mapping)
                self.assertNotIn("provenance_mappings", result.mapping)

    def test_fable_preference_factory_resolves_only_homogeneous_nested_claims(self):
        pair = {
            "pair_id": "legacy-pair",
            "chosen": factory_thalamic(FABLE_FFPC, "designed"),
            "rejected": factory_thalamic(FABLE_FFPC, "designed"),
            "critique": "same state, bounded repair",
            "meta": {"id": "wrapper-without-factory"},
        }
        result = identity.curate_record(source(pair, f"{FABLE_FFPC}/preferences.jsonl", 1))
        self.assertEqual(result.action, "retained")
        self.assertEqual(result.mapping["factory_id"], FABLE_FFPC)

        disagreement = copy.deepcopy(pair)
        disagreement["rejected"]["meta"]["factory"] = "different-factory"
        result = identity.curate_record(source(disagreement, f"{FABLE_FFPC}/preferences.jsonl", 1))
        self.assertEqual(result.action, "exclude")
        self.assertEqual(
            result.mapping["reason_codes"],
            ["identity.factory_path_payload_mismatch"],
        )

        incomplete = copy.deepcopy(pair)
        incomplete["rejected"]["meta"].pop("factory")
        result = identity.curate_record(source(incomplete, f"{FABLE_FFPC}/preferences.jsonl", 1))
        self.assertEqual(result.action, "exclude")
        self.assertEqual(
            result.mapping["reason_codes"],
            ["identity.factory_path_payload_mismatch"],
        )

        wrapper_disagreement = copy.deepcopy(pair)
        wrapper_disagreement["meta"]["factory"] = FABLE_FFPC
        wrapper_disagreement["chosen"]["meta"]["factory"] = "different-factory"
        result = identity.curate_record(
            source(wrapper_disagreement, f"{FABLE_FFPC}/preferences.jsonl", 1)
        )
        self.assertEqual(result.action, "exclude")
        self.assertEqual(
            result.mapping["reason_codes"],
            ["identity.factory_path_payload_mismatch"],
        )

    def test_preference_side_kind_is_scoped_by_factory_contract(self):
        thalamic_pair = {
            "chosen": factory_thalamic("tool-use-preference-factory", "designed"),
            "rejected": factory_thalamic("tool-use-preference-factory", "designed"),
            "meta": {"factory": "tool-use-preference-factory"},
        }
        result = identity.curate_record(
            source(thalamic_pair, "tool-use-preference-factory/batch.jsonl", 1)
        )
        self.assertEqual(result.action, "exclude")
        self.assertEqual(result.mapping["reason_codes"], ["identity.invalid_nested_shape"])

        episode_pair = grok_pref(FABLE_FFPC)
        result = identity.curate_record(source(episode_pair, f"{FABLE_FFPC}/preferences.jsonl", 1))
        self.assertEqual(result.action, "exclude")
        self.assertEqual(result.mapping["reason_codes"], ["identity.invalid_nested_shape"])

    def test_never_training_ready_policy_rejects_recursive_true_claims(self):
        raw = episode(FABLE_ACT)
        raw["steps"][0]["training_ready"] = True
        result = identity.curate_record(source(raw, f"{FABLE_ACT}/episodes.jsonl", 1))
        self.assertEqual(result.action, "exclude")
        self.assertEqual(
            result.mapping["reason_codes"],
            ["identity.training_ready_policy_violation"],
        )

    def test_recursive_real_claim_outside_owner_state_is_excluded(self):
        for claim in ("real", "production", "actions live"):
            with self.subTest(claim=claim):
                raw = episode(FABLE_ACT)
                raw["steps"][0]["sim_or_real"] = claim
                result = identity.curate_record(source(raw, f"{FABLE_ACT}/episodes.jsonl", 1))
                self.assertEqual(result.action, "exclude")
                self.assertEqual(
                    result.mapping["reason_codes"],
                    ["identity.unowned_real_claim"],
                )

        for simulation_description in ("realistic", "real-time"):
            with self.subTest(simulation_description=simulation_description):
                raw = episode(FABLE_ACT)
                raw["steps"][0]["sim_or_real"] = simulation_description
                result = identity.curate_record(source(raw, f"{FABLE_ACT}/episodes.jsonl", 1))
                self.assertEqual(result.action, "retained")

    def test_shape_authority_resolves_existing_state_provenance_first(self):
        simulated = episode(FABLE_ACT)
        simulated["state"] = {"provenance": {"kind": "simulated", "claimed": "sim fixture"}}
        result = identity.curate_record(source(simulated, f"{FABLE_ACT}/episodes.jsonl", 1))
        self.assertEqual(result.action, "retained")
        self.assertEqual(result.record["provenance"]["kind"], "simulated")
        self.assertEqual(result.record["state"]["sim_or_real"], "simulated")

        real = episode(FABLE_ACT)
        real["state"] = {"provenance": {"kind": "real", "claimed": "live system"}}
        result = identity.curate_record(source(real, f"{FABLE_ACT}/episodes.jsonl", 1))
        self.assertEqual(result.action, "exclude")
        self.assertEqual(
            result.mapping["reason_codes"],
            ["identity.unresolved_provenance"],
        )

    def test_registry_onboard_rows_are_not_training_ready(self):
        payload = json.loads(identity.FACTORY_REGISTRY_PATH.read_text(encoding="utf-8"))
        self.assertEqual(len(payload["factories"]), 51)
        self.assertEqual(payload["lookup_key"], "path_id")
        for row in payload["factories"]:
            self.assertNotIn("training_ready", row)
            self.assertIsNone(row["publication_target"])
            self.assertEqual(row["training_ready_policy"], "never")
            self.assertTrue(row["identity_authoritative"])
        grok_rows = [row for row in payload["factories"] if row["generator"] == "grok-4.6"]
        self.assertEqual(len(grok_rows), 44)
        for row in grok_rows:
            self.assertEqual(row["path_id"], row["payload_factory"])
            expected_kind = round_txn.AGENTIC_FACTORY_KINDS[row["path_id"]]
            self.assertEqual(row["record_kinds"], [expected_kind])
            self.assertEqual(
                set(row["provenance_contract_by_kind"]),
                {expected_kind},
            )
        eval_row = next(
            item
            for item in payload["factories"]
            if item["path_id"] == "eval-harness-trajectory-factory"
        )
        self.assertEqual(eval_row["payload_factory"], "eval-harness-trajectory-factory")
        ffpc = next(item for item in payload["factories"] if item["path_id"] == FABLE_FFPC)
        self.assertIn("curate_preferences", ffpc["allowed_curation_lanes"])
        self.assertEqual(ffpc["preference_side_kinds"], ["thalamic"])
        grok_pref_row = next(
            item
            for item in payload["factories"]
            if item["path_id"] == "tool-use-preference-factory"
        )
        self.assertNotIn("curate_preferences", grok_pref_row["allowed_curation_lanes"])
        self.assertEqual(grok_pref_row["preference_side_kinds"], ["episode"])


def _valid_row(**overrides):
    row = {
        "path_id": "tmp-factory",
        "payload_factory": "tmp-factory",
        "generator": "test",
        "generator_version": "test",
        "record_kinds": ["episode"],
        "identity_authoritative": True,
        "publication_target": None,
        "training_ready_policy": "never",
        "allowed_curation_lanes": ["curate_identity"],
        "provenance_contract_by_kind": {
            "episode": "synthetic_shape_implies_designed",
        },
    }
    row.update(overrides)
    return row


def _registry_payload(rows, **overrides):
    payload = {
        "schema_version": "factory-registry-v0.1",
        "lookup_key": "path_id",
        "factories": rows,
    }
    payload.update(overrides)
    return payload


def _load_temp_registry(directory, payload):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / "FACTORY-REGISTRY.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return identity.load_registry(path)


def _manifest_bytes(manifest):
    return (
        json.dumps(
            manifest,
            ensure_ascii=False,
            allow_nan=False,
            indent=2,
            sort_keys=True,
        )
        + "\n"
    ).encode("utf-8")


class TestStrictIdentityTrustBoundaries(unittest.TestCase):
    def test_noncanonical_physical_factory_path_never_gains_registry_authority(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "source"
            physical_factory = root / f" {FABLE_ACT}"
            physical_factory.mkdir(parents=True)
            source_path = physical_factory / "records.jsonl"
            source_path.write_text(
                identity.canonical_json(episode(FABLE_ACT)) + "\n",
                encoding="utf-8",
            )

            records = identity.iter_source_records(root)
            self.assertEqual(
                records[0].source_path,
                f" {FABLE_ACT}/records.jsonl",
            )
            with self.assertRaisesRegex(
                identity.IdentityCurationError,
                "exact normalized POSIX",
            ):
                identity.curate_records(records)

            dest = Path(tmp) / "dest"
            with self.assertRaisesRegex(
                identity.IdentityCurationError,
                "exact normalized POSIX",
            ):
                identity.write_run(root, dest)
            self.assertFalse(dest.exists())

    def test_only_json_whitespace_source_lines_are_blank(self):
        with tempfile.TemporaryDirectory() as tmp:
            source_path = Path(tmp) / FABLE_ACT / "records.jsonl"
            source_path.parent.mkdir()
            valid_line = identity.canonical_json(episode(FABLE_ACT)).encode("utf-8")
            source_path.write_bytes(b" \t\r\n" + valid_line + b"\n\t\r")

            records = identity.iter_source_records(source_path)
            self.assertEqual(len(records), 1)
            self.assertEqual(records[0].source_line, 2)

            for separator in ("\u0085", "\u2028", "\u2029"):
                with self.subTest(separator=f"U+{ord(separator):04X}"):
                    source_path.write_bytes(separator.encode("utf-8") + b"\n")
                    with self.assertRaisesRegex(
                        identity.IdentityCurationError,
                        rf"JSON parse error at {FABLE_ACT}/records\.jsonl:1",
                    ):
                        identity.iter_source_records(source_path)

            source_path.write_bytes("\u2028".encode("utf-8") + b"\n")
            dest = Path(tmp) / "dest"
            stderr = io.StringIO()
            with mock.patch("sys.stderr", stderr):
                self.assertEqual(
                    identity.main([str(source_path), "--out", str(dest)]),
                    1,
                )
            self.assertIn(f"{FABLE_ACT}/records.jsonl:1", stderr.getvalue())
            self.assertFalse(dest.exists())

    def test_float_overflow_is_rejected_by_registry_source_and_cli_apis(self):
        for payload in ("1e400", "-1e400", '{"nested":[1e400]}'):
            with self.subTest(payload=payload):
                with self.assertRaisesRegex(ValueError, "finitely representable"):
                    identity._strict_json_loads(payload)
        self.assertEqual(identity._strict_json_loads("1e308"), 1e308)

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            registry_path = root / "registry.json"
            reviewed_registry = identity.FACTORY_REGISTRY_PATH.read_text(encoding="utf-8")
            overflow_registry = reviewed_registry.replace(
                '"generator": "fable-5"',
                '"generator": 1e400',
                1,
            )
            self.assertNotEqual(overflow_registry, reviewed_registry)
            registry_path.write_text(overflow_registry, encoding="utf-8")
            with self.assertRaisesRegex(
                identity.IdentityCurationError,
                "finitely representable",
            ):
                identity.load_registry(registry_path)

            raw = episode(FABLE_ACT)
            source_json = identity.canonical_json(raw)[:-1] + ',"metric":1e400}'
            source_digest = hashlib.sha256(source_json.encode("utf-8")).hexdigest()
            with self.assertRaisesRegex(
                identity.IdentityCurationError,
                "source_json is not strict JSON.*finitely representable",
            ):
                identity.curate_record(
                    identity.SourceRecord(
                        raw,
                        f"{FABLE_ACT}/records.jsonl",
                        1,
                        source_digest,
                        source_json,
                    )
                )

            source_path = root / FABLE_ACT / "records.jsonl"
            source_path.parent.mkdir()
            source_path.write_text(source_json + "\n", encoding="utf-8")
            with self.assertRaisesRegex(
                identity.IdentityCurationError,
                rf"JSON parse error at {FABLE_ACT}/records\.jsonl:1.*finitely representable",
            ):
                identity.iter_source_records(source_path)

            dest = root / "dest"
            stderr = io.StringIO()
            with mock.patch("sys.stderr", stderr):
                self.assertEqual(
                    identity.main([str(source_path), "--out", str(dest)]),
                    1,
                )
            self.assertIn("finitely representable", stderr.getvalue())
            self.assertFalse(dest.exists())

    def test_tree_parsers_reject_float_overflow_with_tree_errors(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source_path = root / "src" / FABLE_ACT / "records.jsonl"
            source_path.parent.mkdir(parents=True)
            source_path.write_text(
                identity.canonical_json(episode(FABLE_ACT)) + "\n",
                encoding="utf-8",
            )
            dest = root / "dest"
            identity.write_run(source_path, dest)

            registry_path = dest / identity.FACTORY_REGISTRY_SIDECAR
            manifest_path = dest / identity.IDENTITY_MANIFEST_SIDECAR
            output_path = dest / FABLE_ACT / "records.jsonl"
            registry_bytes = registry_path.read_bytes()
            manifest_bytes = manifest_path.read_bytes()
            output_bytes = output_path.read_bytes()

            overflow_registry = registry_bytes.replace(
                b'"generator": "fable-5"',
                b'"generator": 1e400',
                1,
            )
            self.assertNotEqual(overflow_registry, registry_bytes)
            registry_path.write_bytes(overflow_registry)
            with self.assertRaisesRegex(
                identity.IdentityTreeError,
                "FACTORY-REGISTRY.*finitely representable",
            ):
                identity.validate_identity_tree(dest)
            registry_path.write_bytes(registry_bytes)

            overflow_manifest = manifest_bytes.replace(b"{", b'{"overflow":1e400,', 1)
            manifest_path.write_bytes(overflow_manifest)
            with self.assertRaisesRegex(identity.IdentityTreeError, "finitely representable"):
                identity.validate_identity_tree(
                    dest,
                    expected_manifest_digest=hashlib.sha256(overflow_manifest).hexdigest(),
                )

            manifest = json.loads(manifest_bytes)
            source_meta = manifest[0]["source"]
            source_meta["original"] = source_meta["original"][:-1] + ',"overflow":1e400}'
            source_meta["sha256"] = hashlib.sha256(
                source_meta["original"].encode("utf-8")
            ).hexdigest()
            embedded_overflow_manifest = _manifest_bytes(manifest)
            manifest_path.write_bytes(embedded_overflow_manifest)
            with self.assertRaisesRegex(identity.IdentityTreeError, "finitely representable"):
                identity.validate_identity_tree(
                    dest,
                    expected_manifest_digest=hashlib.sha256(embedded_overflow_manifest).hexdigest(),
                )

            manifest_path.write_bytes(manifest_bytes)
            output_line = output_bytes[:-1].decode("utf-8")
            overflow_output = (output_line[:-1] + ',"overflow":1e400}\n').encode("utf-8")
            output_path.write_bytes(overflow_output)
            with self.assertRaisesRegex(identity.IdentityTreeError, "finitely representable"):
                identity.validate_identity_tree(
                    dest,
                    expected_manifest_digest=hashlib.sha256(manifest_bytes).hexdigest(),
                )

    def test_unpaired_surrogates_are_rejected_recursively_but_astral_text_is_valid(self):
        invalid_payloads = (
            r'{"nested":[{"value":"\ud800"}]}',
            r'{"nested":{"\udfff":"value"}}',
            r'{"value":"\ud83d"}',
            r'{"value":"\ude00"}',
        )
        for payload in invalid_payloads:
            with self.subTest(payload=payload):
                with self.assertRaisesRegex(ValueError, "unpaired UTF-16 surrogate"):
                    identity._strict_json_loads(payload)

        astral = identity._strict_json_loads(r'{"escaped":"\ud83d\ude00","literal":"😀"}')
        self.assertEqual(astral, {"escaped": "😀", "literal": "😀"})
        self.assertIn("😀", identity.canonical_json(astral))

        lone = chr(0xD800)
        for malformed in (
            episode(FABLE_ACT, nested={"value": lone}),
            episode(FABLE_ACT, nested={lone: "value"}),
        ):
            with self.subTest(member_names=list(malformed["nested"])):
                with self.assertRaisesRegex(
                    identity.IdentityCurationError,
                    "unpaired UTF-16 surrogate",
                ):
                    identity.canonical_json(malformed)
                with self.assertRaisesRegex(
                    identity.IdentityCurationError,
                    "unpaired UTF-16 surrogate",
                ):
                    identity.curate_record(
                        identity.SourceRecord(
                            malformed,
                            f"{FABLE_ACT}/records.jsonl",
                            1,
                        )
                    )

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            raw = episode(FABLE_ACT)
            source_json = identity.canonical_json(raw).replace(
                '"goal":"repair a deterministic fixture"',
                '"goal":"\\ud800"',
                1,
            )
            source_digest = hashlib.sha256(source_json.encode("utf-8")).hexdigest()
            with self.assertRaisesRegex(
                identity.IdentityCurationError,
                "source_json is not strict JSON.*unpaired UTF-16 surrogate",
            ):
                identity.curate_record(
                    identity.SourceRecord(
                        raw,
                        f"{FABLE_ACT}/records.jsonl",
                        1,
                        source_digest,
                        source_json,
                    )
                )

            source_path = root / FABLE_ACT / "records.jsonl"
            source_path.parent.mkdir()
            source_path.write_text(source_json + "\n", encoding="utf-8")
            with self.assertRaisesRegex(
                identity.IdentityCurationError,
                rf"JSON parse error at {FABLE_ACT}/records\.jsonl:1.*unpaired UTF-16 surrogate",
            ):
                identity.iter_source_records(source_path)

            dest = root / "dest"
            stderr = io.StringIO()
            with mock.patch("sys.stderr", stderr):
                self.assertEqual(
                    identity.main([str(source_path), "--out", str(dest)]),
                    1,
                )
            self.assertIn("unpaired UTF-16 surrogate", stderr.getvalue())
            self.assertFalse(dest.exists())

            registry_path = root / "registry.json"
            registry_text = identity.FACTORY_REGISTRY_PATH.read_text(encoding="utf-8").replace(
                '"generator": "fable-5"',
                '"generator": "\\ud800"',
                1,
            )
            registry_path.write_text(registry_text, encoding="utf-8")
            with self.assertRaisesRegex(
                identity.IdentityCurationError,
                "unpaired UTF-16 surrogate",
            ):
                identity.load_registry(registry_path)

    def test_tree_parsers_wrap_unpaired_surrogates_as_tree_errors(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source_path = root / "src" / FABLE_ACT / "records.jsonl"
            source_path.parent.mkdir(parents=True)
            source_path.write_text(
                identity.canonical_json(episode(FABLE_ACT)) + "\n",
                encoding="utf-8",
            )
            dest = root / "dest"
            identity.write_run(source_path, dest)

            registry_path = dest / identity.FACTORY_REGISTRY_SIDECAR
            manifest_path = dest / identity.IDENTITY_MANIFEST_SIDECAR
            output_path = dest / FABLE_ACT / "records.jsonl"
            registry_bytes = registry_path.read_bytes()
            manifest_bytes = manifest_path.read_bytes()
            output_bytes = output_path.read_bytes()

            surrogate_registry = registry_bytes.replace(
                b'"generator": "fable-5"',
                b'"generator": "\\ud800"',
                1,
            )
            registry_path.write_bytes(surrogate_registry)
            with self.assertRaisesRegex(
                identity.IdentityTreeError,
                "FACTORY-REGISTRY.*unpaired UTF-16 surrogate",
            ):
                identity.validate_identity_tree(dest)
            registry_path.write_bytes(registry_bytes)

            surrogate_member_manifest = manifest_bytes.replace(
                b"{",
                b'{"\\ud800":0,',
                1,
            )
            manifest_path.write_bytes(surrogate_member_manifest)
            with self.assertRaisesRegex(
                identity.IdentityTreeError,
                "unpaired UTF-16 surrogate",
            ):
                identity.validate_identity_tree(
                    dest,
                    expected_manifest_digest=hashlib.sha256(surrogate_member_manifest).hexdigest(),
                )

            manifest = json.loads(manifest_bytes)
            source_meta = manifest[0]["source"]
            source_meta["original"] = source_meta["original"].replace(
                '"goal":"repair a deterministic fixture"',
                '"goal":"\\ud800"',
                1,
            )
            source_meta["sha256"] = hashlib.sha256(
                source_meta["original"].encode("utf-8")
            ).hexdigest()
            embedded_surrogate_manifest = _manifest_bytes(manifest)
            manifest_path.write_bytes(embedded_surrogate_manifest)
            with self.assertRaisesRegex(
                identity.IdentityTreeError,
                "unpaired UTF-16 surrogate",
            ):
                identity.validate_identity_tree(
                    dest,
                    expected_manifest_digest=hashlib.sha256(
                        embedded_surrogate_manifest
                    ).hexdigest(),
                )

            manifest_path.write_bytes(manifest_bytes)
            surrogate_output = output_bytes.replace(
                b'"goal":"repair a deterministic fixture"',
                b'"goal":"\\ud800"',
                1,
            )
            output_path.write_bytes(surrogate_output)
            with self.assertRaisesRegex(
                identity.IdentityTreeError,
                "unpaired UTF-16 surrogate",
            ):
                identity.validate_identity_tree(
                    dest,
                    expected_manifest_digest=hashlib.sha256(manifest_bytes).hexdigest(),
                )


class TestIdentityWriterExcludeAndPin(unittest.TestCase):
    def test_registry_rejects_training_ready_and_invalid_rows(self):
        with tempfile.TemporaryDirectory() as tmp:
            missing = Path(tmp) / "missing.json"
            with self.assertRaisesRegex(identity.IdentityCurationError, "unreadable"):
                identity.load_registry(missing)
            bad_json = Path(tmp) / "bad.json"
            bad_json.write_bytes(b"{")
            with self.assertRaisesRegex(identity.IdentityCurationError, "UTF-8 JSON"):
                identity.load_registry(bad_json)
            not_object = Path(tmp) / "list.json"
            not_object.write_text("[]\n", encoding="utf-8")
            with self.assertRaisesRegex(identity.IdentityCurationError, "JSON object"):
                identity.load_registry(not_object)

            ready = _registry_payload([_valid_row(training_ready=True)])
            with self.assertRaisesRegex(identity.IdentityCurationError, "training_ready"):
                _load_temp_registry(tmp, ready)
            nested_list = _registry_payload(
                [_valid_row()],
                notes=[{"training_ready": True}],
            )
            with self.assertRaisesRegex(identity.IdentityCurationError, "training_ready"):
                _load_temp_registry(Path(tmp) / "nested", nested_list)

            cases = (
                (
                    {
                        "schema_version": "other",
                        "lookup_key": "path_id",
                        "factories": [_valid_row()],
                    },
                    "schema_version",
                ),
                (
                    {
                        "schema_version": "factory-registry-v0.1",
                        "lookup_key": "slug",
                        "factories": [_valid_row()],
                    },
                    "lookup_key",
                ),
                (
                    {
                        "schema_version": "factory-registry-v0.1",
                        "lookup_key": "path_id",
                        "factories": [],
                    },
                    "non-empty list",
                ),
                (_registry_payload(["not-an-object"]), "must be an object"),
                (_registry_payload([{"path_id": "x"}]), "missing fields"),
                (_registry_payload([_valid_row(path_id="")]), "path_id must be a string"),
                (
                    _registry_payload([_valid_row(payload_factory="")]),
                    "payload_factory must be a string",
                ),
                (
                    _registry_payload([_valid_row(generator=7)]),
                    "generator must be a non-empty normalized string",
                ),
                (
                    _registry_payload([_valid_row(generator_version=" version ")]),
                    "generator_version must be a non-empty normalized string",
                ),
                (_registry_payload([_valid_row(record_kinds=[])]), "non-empty list"),
                (_registry_payload([_valid_row(record_kinds=[1])]), "must be strings"),
                (
                    _registry_payload(
                        [
                            _valid_row(
                                record_kinds=["episdoe"],
                                provenance_contract_by_kind={
                                    "episdoe": "synthetic_shape_implies_designed"
                                },
                            )
                        ]
                    ),
                    "unsupported kinds",
                ),
                (
                    _registry_payload([_valid_row(record_kinds=["episode", "episode"])]),
                    "must not contain duplicates",
                ),
                (
                    _registry_payload([_valid_row(identity_authoritative="yes")]),
                    "must be a boolean",
                ),
                (_registry_payload([_valid_row(publication_target=17)]), "null or a string"),
                (
                    _registry_payload([_valid_row(training_ready_policy="always")]),
                    "never or compose_eligible",
                ),
                (
                    _registry_payload([_valid_row(allowed_curation_lanes="identity")]),
                    "list of strings",
                ),
                (
                    _registry_payload([_valid_row(provenance_contract_by_kind="episode")]),
                    "must be an object",
                ),
                (
                    _registry_payload(
                        [_valid_row(provenance_contract_by_kind={"episode": "invent-designed"})]
                    ),
                    "missing allowed provenance_contract",
                ),
                (
                    _registry_payload(
                        [
                            _valid_row(
                                identity_authoritative=False,
                                provenance_contract_by_kind={
                                    "episode": "synthetic_shape_implies_designed"
                                },
                            )
                        ]
                    ),
                    "requires identity_authoritative",
                ),
                (
                    _registry_payload([_valid_row(), _valid_row()]),
                    "duplicate registry path_id",
                ),
                (
                    _registry_payload(
                        [
                            _valid_row(
                                record_kinds=["preference"],
                                provenance_contract_by_kind={
                                    "preference": "synthetic_shape_implies_designed"
                                },
                            )
                        ]
                    ),
                    "preference_side_kinds must be a non-empty list",
                ),
                (
                    _registry_payload(
                        [
                            _valid_row(
                                record_kinds=["preference"],
                                preference_side_kinds=["bridge_pair"],
                                provenance_contract_by_kind={
                                    "preference": "synthetic_shape_implies_designed"
                                },
                            )
                        ]
                    ),
                    "contains unsupported kinds",
                ),
            )
            for payload, needle in cases:
                with self.subTest(needle=needle):
                    with self.assertRaisesRegex(identity.IdentityCurationError, needle):
                        _load_temp_registry(Path(tmp) / needle.replace(" ", "_"), payload)

            for case_index, path_id in enumerate(
                (
                    "group/factory",
                    "../factory",
                    "factory/",
                    ".",
                    "..",
                    " factory",
                    "factory ",
                    "group\\factory",
                    "/factory",
                )
            ):
                with self.subTest(path_id=path_id):
                    with self.assertRaisesRegex(
                        identity.IdentityCurationError,
                        "exactly one normalized directory component",
                    ):
                        _load_temp_registry(
                            Path(tmp) / f"invalid-path-id-{case_index}",
                            _registry_payload([_valid_row(path_id=path_id)]),
                        )

            accepted = _load_temp_registry(
                Path(tmp) / "ok",
                _registry_payload(
                    [
                        _valid_row(
                            publication_target="rmems/example",
                            training_ready_policy="compose_eligible",
                        )
                    ]
                ),
            )
            row = accepted.by_path_id["tmp-factory"]
            self.assertEqual(row.publication_target, "rmems/example")
            self.assertEqual(row.training_ready_policy, "compose_eligible")

    def test_exclude_unsupported_shape_and_missing_payload_factory(self):
        unknown = identity.curate_record(
            source({"meta": {"factory": FABLE_THALAMIC}}, f"{FABLE_THALAMIC}/odd.jsonl", 1)
        )
        self.assertEqual(unknown.action, "exclude")
        self.assertEqual(
            unknown.mapping["reason_codes"],
            ["identity.unsupported_record_shape"],
        )
        missing_meta = episode(FABLE_ACT)
        missing_meta["meta"] = {"round": 2}
        mismatch = identity.curate_record(source(missing_meta, f"{FABLE_ACT}/episodes.jsonl", 1))
        self.assertEqual(mismatch.action, "exclude")
        self.assertEqual(
            mismatch.mapping["reason_codes"],
            ["identity.factory_path_payload_mismatch"],
        )
        mismatch_blank = episode(FABLE_ACT)
        mismatch_blank["meta"] = {"factory": "  "}
        blank = identity.curate_record(source(mismatch_blank, f"{FABLE_ACT}/episodes.jsonl", 1))
        self.assertEqual(
            blank.mapping["reason_codes"],
            ["identity.factory_path_payload_mismatch"],
        )
        no_meta = episode(FABLE_ACT)
        no_meta["meta"] = "not-an-object"
        self.assertEqual(
            identity.curate_record(source(no_meta, f"{FABLE_ACT}/episodes.jsonl", 1)).mapping[
                "reason_codes"
            ],
            ["identity.factory_path_payload_mismatch"],
        )

    def test_write_run_replays_all_non_object_json_as_outputless_exclusions(self):
        values = ([], 17, "text", None)
        source_lines = tuple(identity.canonical_json(value) for value in values)

        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "src"
            dest = Path(tmp) / "dest"
            factory = src / FABLE_ACT
            factory.mkdir(parents=True)
            (factory / "records.jsonl").write_text(
                "\n".join(source_lines) + "\n",
                encoding="utf-8",
            )

            dry_results = identity.curate_records(identity.iter_source_records(src))
            self.assertEqual(
                tuple(
                    identity.canonical_json(record.record)
                    for record in identity.iter_source_records(src)
                ),
                source_lines,
            )
            self.assertEqual([result.action for result in dry_results], ["exclude"] * 4)
            self.assertEqual(
                [result.mapping["reason_codes"] for result in dry_results],
                [["identity.unsupported_record_shape"]] * 4,
            )

            stdout = io.StringIO()
            with mock.patch("sys.stdout", stdout):
                self.assertEqual(identity.main([str(src)]), 0)
            self.assertEqual(
                json.loads(stdout.getvalue()),
                {
                    "transform": {
                        "name": identity.TRANSFORM_NAME,
                        "version": identity.TRANSFORM_VERSION,
                    },
                    "registry": {
                        "schema_version": identity.default_registry().schema_version,
                        "sha256": identity.default_registry().sha256,
                    },
                    "records": 4,
                    "retained": 0,
                    "excluded": 4,
                    "reason_codes": {"identity.unsupported_record_shape": 4},
                },
            )

            with mock.patch.object(
                identity,
                "validate_identity_tree",
                wraps=identity.validate_identity_tree,
            ) as immediate_validate:
                written_results = identity.write_run(src, dest)
            immediate_validate.assert_called_once()
            self.assertEqual(
                [result.mapping for result in written_results],
                [result.mapping for result in dry_results],
            )

            manifest_path = dest / identity.IDENTITY_MANIFEST_SIDECAR
            registry_path = dest / identity.FACTORY_REGISTRY_SIDECAR
            manifest_bytes = manifest_path.read_bytes()
            manifest_digest = hashlib.sha256(manifest_bytes).hexdigest()
            registry_digest = hashlib.sha256(registry_path.read_bytes()).hexdigest()
            registry = identity.validate_identity_tree(
                dest,
                expected_registry_digest=registry_digest,
                expected_manifest_digest=manifest_digest,
            )
            manifest = json.loads(manifest_bytes)
            self.assertEqual(manifest, [result.mapping for result in written_results])
            self.assertEqual(list(dest.rglob("*.jsonl")), [])

            for index, (mapping, source_line) in enumerate(zip(manifest, source_lines), 1):
                with self.subTest(source_value=source_line):
                    self.assertEqual(mapping["action"], "exclude")
                    self.assertEqual(
                        mapping["reason_codes"],
                        ["identity.unsupported_record_shape"],
                    )
                    self.assertEqual(mapping["record_kind"], "unknown")
                    self.assertEqual(mapping["details"], ["record must be a JSON object"])
                    self.assertEqual(mapping["source"]["line"], index)
                    self.assertEqual(mapping["source"]["original"], source_line)
                    self.assertEqual(
                        mapping["source"]["sha256"],
                        hashlib.sha256(source_line.encode("utf-8")).hexdigest(),
                    )
                    self.assertNotIn("output_id", mapping)
                    self.assertNotIn("output_sha256", mapping)
                    self.assertIsNone(written_results[index - 1].record)

                    replay = identity._replay_manifest_mapping(mapping, index - 1, registry)
                    self.assertEqual(replay.result.action, "exclude")
                    self.assertIsNone(replay.result.record)
                    self.assertEqual(replay.result.mapping, mapping)

    def test_non_object_manifest_snapshot_cannot_be_relabelled_retained(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "src"
            dest = Path(tmp) / "dest"
            factory = src / FABLE_ACT
            factory.mkdir(parents=True)
            (factory / "records.jsonl").write_text("null\n", encoding="utf-8")
            identity.write_run(src, dest)

            manifest_path = dest / identity.IDENTITY_MANIFEST_SIDECAR
            registry_path = dest / identity.FACTORY_REGISTRY_SIDECAR
            original_bytes = manifest_path.read_bytes()
            original_digest = hashlib.sha256(original_bytes).hexdigest()
            registry_digest = hashlib.sha256(registry_path.read_bytes()).hexdigest()
            manifest = json.loads(original_bytes)
            self.assertEqual(manifest[0]["source"]["original"], "null")
            self.assertEqual(manifest[0]["action"], "exclude")

            tampered = copy.deepcopy(manifest)
            tampered[0]["action"] = "retained"
            tampered_bytes = _manifest_bytes(tampered)
            manifest_path.write_bytes(tampered_bytes)
            with self.assertRaisesRegex(identity.IdentityTreeError, "action does not match"):
                identity.validate_identity_tree(
                    dest,
                    expected_registry_digest=registry_digest,
                    expected_manifest_digest=hashlib.sha256(tampered_bytes).hexdigest(),
                )
            self.assertEqual(list(dest.rglob("*.jsonl")), [])

            manifest_path.write_bytes(original_bytes)
            identity.validate_identity_tree(
                dest,
                expected_registry_digest=registry_digest,
                expected_manifest_digest=original_digest,
            )

    def test_exclude_not_authoritative_and_invalid_contract(self):
        with tempfile.TemporaryDirectory():
            not_auth = identity.FactoryRow(
                path_id=FABLE_THALAMIC,
                payload_factory=FABLE_THALAMIC,
                generator="fable-5",
                generator_version="fable-5",
                record_kinds=frozenset({"thalamic"}),
                identity_authoritative=False,
                publication_target=None,
                training_ready_policy="never",
                allowed_curation_lanes=("curate_identity",),
                provenance_contract_by_kind={"thalamic": "require_state_claim"},
            )
            registry = identity.FactoryRegistry(
                schema_version="factory-registry-v0.1",
                sha256="a" * 64,
                raw_bytes=b"{}",
                by_path_id={FABLE_THALAMIC: not_auth},
            )
            result = identity.curate_record(source(thalamic()), registry=registry)
            self.assertEqual(result.action, "exclude")
            self.assertEqual(
                result.mapping["reason_codes"],
                ["identity.factory_not_identity_authoritative"],
            )

            missing_contract = identity.FactoryRow(
                path_id=FABLE_ACT,
                payload_factory=FABLE_ACT,
                generator="fable-5",
                generator_version="fable-5",
                record_kinds=frozenset({"episode"}),
                identity_authoritative=True,
                publication_target=None,
                training_ready_policy="never",
                allowed_curation_lanes=("curate_identity",),
                provenance_contract_by_kind={},
            )
            registry = identity.FactoryRegistry(
                schema_version="factory-registry-v0.1",
                sha256="b" * 64,
                raw_bytes=b"{}",
                by_path_id={FABLE_ACT: missing_contract},
            )
            result = identity.curate_record(
                source(episode(FABLE_ACT), f"{FABLE_ACT}/episodes.jsonl", 1),
                registry=registry,
            )
            self.assertEqual(result.action, "exclude")
            self.assertEqual(
                result.mapping["reason_codes"],
                ["identity.factory_contract_invalid"],
            )

            thalamic_shape = identity.FactoryRow(
                path_id=FABLE_THALAMIC,
                payload_factory=FABLE_THALAMIC,
                generator="fable-5",
                generator_version="fable-5",
                record_kinds=frozenset({"thalamic"}),
                identity_authoritative=True,
                publication_target=None,
                training_ready_policy="never",
                allowed_curation_lanes=("curate_identity",),
                provenance_contract_by_kind={"thalamic": "synthetic_shape_implies_designed"},
            )
            registry = identity.FactoryRegistry(
                schema_version="factory-registry-v0.1",
                sha256="c" * 64,
                raw_bytes=b"{}",
                by_path_id={FABLE_THALAMIC: thalamic_shape},
            )
            raw = thalamic()
            raw["state"] = {"episode_id": "legacy-episode-17"}
            result = identity.curate_record(source(raw), registry=registry)
            self.assertEqual(result.action, "exclude")
            self.assertEqual(
                result.mapping["reason_codes"],
                ["identity.factory_contract_invalid"],
            )

    def test_invalid_bridge_and_preference_shapes_exclude(self):
        bad_view = {
            "language_view": "not-an-object",
            "spike_events": [],
            "meta": {"factory": FABLE_BRIDGE},
        }
        result = identity.curate_record(source(bad_view, f"{FABLE_BRIDGE}/bad.jsonl", 1))
        self.assertEqual(result.action, "exclude")
        self.assertEqual(
            result.mapping["reason_codes"],
            ["identity.invalid_nested_shape"],
        )
        bad_traj = {
            "language_view": {},
            "spike_events": [],
            "meta": {"factory": FABLE_BRIDGE},
        }
        result = identity.curate_record(source(bad_traj, f"{FABLE_BRIDGE}/bad.jsonl", 1))
        self.assertEqual(
            result.mapping["reason_codes"],
            ["identity.invalid_nested_shape"],
        )
        pair = {
            "chosen": {"note": "no state"},
            "rejected": {"note": "no state"},
            "meta": {"factory": FABLE_FFPC},
        }
        result = identity.curate_record(source(pair, f"{FABLE_FFPC}/batch.jsonl", 1))
        self.assertEqual(result.action, "exclude")
        self.assertEqual(
            result.mapping["reason_codes"],
            ["identity.invalid_nested_shape"],
        )

    def test_preference_mixed_claims_and_state_wins_on_sides(self):
        mixed = {
            "chosen": factory_thalamic(FABLE_FFPC, "designed"),
            "rejected": factory_thalamic(FABLE_FFPC, "simulated"),
            "meta": {"factory": FABLE_FFPC},
        }
        result = identity.curate_record(source(mixed, f"{FABLE_FFPC}/batch.jsonl", 1))
        self.assertEqual(result.action, "retained")
        self.assertEqual(result.record["provenance"]["kind"], "unknown")

        pref = grok_pref()
        pref["chosen"]["state"] = {"sim_or_real": "designed"}
        pref["rejected"]["state"] = {"sim_or_real": "designed"}
        result = identity.curate_record(source(pref, "tool-use-preference-factory/batch.jsonl", 1))
        self.assertEqual(result.action, "retained")
        self.assertEqual(result.record["provenance"]["kind"], "designed")
        self.assertEqual(result.record["chosen"]["state"]["sim_or_real"], "designed")

    def test_record_kind_and_caller_contract_errors(self):
        with self.assertRaisesRegex(identity.IdentityCurationError, "JSON object"):
            identity.record_kind("not-a-record")
        with self.assertRaisesRegex(identity.IdentityCurationError, "unsupported"):
            identity.record_kind({"meta": {}})
        with self.assertRaisesRegex(identity.IdentityCurationError, "SourceRecord"):
            identity.curate_record({"goal": "x", "steps": []})
        with self.assertRaisesRegex(identity.IdentityCurationError, "canonical JSON"):
            identity.canonical_json({1, 2})
        with self.assertRaisesRegex(identity.IdentityCurationError, "64 hexadecimal"):
            identity.curate_record(source(thalamic(), digest="not-a-digest"))
        with self.assertRaises(identity.IdentityCurationError):
            identity.curate_record(source(thalamic(), path=""))

    def test_never_emit_real_is_enforced(self):
        raw = episode(FABLE_ACT)
        raw["state"] = {"sim_or_real": "simulated"}
        with mock.patch.object(identity, "_map_claim", return_value="real"):
            with self.assertRaisesRegex(identity.IdentityCurationError, "never emit"):
                identity.curate_record(source(raw, f"{FABLE_ACT}/episodes.jsonl", 1))

        def stamp_real(curated, *_args, **_kwargs):
            curated["provenance"] = {"kind": "real"}
            return [], []

        with mock.patch.object(identity, "_apply_shape_designed", stamp_real):
            result = identity.curate_record(
                source(episode(FABLE_ACT), f"{FABLE_ACT}/episodes.jsonl", 1)
            )
        self.assertEqual(result.action, "exclude")
        self.assertEqual(result.mapping["reason_codes"], ["identity.unowned_real_claim"])
        curated = episode(FABLE_ACT)
        curated["state"] = {"sim_or_real": "simulated"}
        source_id = identity._source_identity(source(curated, f"{FABLE_ACT}/episodes.jsonl", 1))
        with self.assertRaisesRegex(identity.IdentityCurationError, "never emit"):
            identity._apply_resolved_state(
                curated,
                curated,
                source_id,
                "episode",
                [],
                [("/", curated)],
                [
                    {
                        "owner_path": "/",
                        "state_path": "/state",
                        "kind": "real",
                        "claimed": "real",
                        "basis": "state.sim_or_real",
                        "original": {},
                    }
                ],
                "sfcur-episode-record-" + "a" * 64,
                [],
            )

    def test_write_run_refuses_existing_and_raw_and_cleans_up(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "src"
            dest = Path(tmp) / "dest"
            (src / FABLE_ACT).mkdir(parents=True)
            # Blank line plus a path/payload mismatch so write_run retains one
            # record and skips the excluded mapping.
            (src / FABLE_ACT / "episodes.jsonl").write_text(
                identity.canonical_json(episode(FABLE_ACT))
                + "\n\n"
                + identity.canonical_json(episode("never-reviewed-factory"))
                + "\n",
                encoding="utf-8",
            )
            dest.mkdir()
            with self.assertRaisesRegex(identity.IdentityCurationError, "already exists"):
                identity.write_run(src, dest)
            dest.rmdir()
            raw_dest = Path(tmp) / "outputs" / "raw" / "cleaned"
            raw_dest.parent.mkdir(parents=True)
            with self.assertRaisesRegex(identity.IdentityCurationError, "raw evidence"):
                identity.write_run(src, raw_dest)

            original = identity._write_exclusive

            def boom_before_manifest(path, payload):
                if path.name == identity.IDENTITY_MANIFEST_SIDECAR:
                    raise OSError("sidecar vanished")
                original(path, payload)

            with mock.patch.object(identity, "_write_exclusive", boom_before_manifest):
                with self.assertRaises(OSError):
                    identity.write_run(src, dest)
            self.assertFalse(dest.exists())

            def boom_on_records(path, payload):
                if path.suffix == ".jsonl":
                    raise OSError("fsync failed")
                original(path, payload)

            with mock.patch.object(identity, "_write_exclusive", boom_on_records):
                with self.assertRaises(OSError):
                    identity.write_run(src, dest)
            self.assertFalse(dest.exists())

            with mock.patch.object(
                identity,
                "validate_identity_tree",
                side_effect=identity.IdentityTreeError("post-write rejection"),
            ):
                with self.assertRaisesRegex(identity.IdentityTreeError, "post-write rejection"):
                    identity.write_run(src, dest)
            self.assertFalse(dest.exists())

            results = identity.write_run(src, dest)
            self.assertEqual(sum(1 for item in results if item.action == "retained"), 1)
            self.assertTrue((dest / FABLE_ACT / "episodes.jsonl").is_file())
            identity.validate_identity_tree(dest)

    def test_validate_identity_tree_pin_mismatch_and_sidecar_errors(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "src"
            dest = Path(tmp) / "dest"
            (src / FABLE_ACT).mkdir(parents=True)
            (src / FABLE_ACT / "episodes.jsonl").write_text(
                identity.canonical_json(episode(FABLE_ACT)) + "\n",
                encoding="utf-8",
            )
            identity.write_run(src, dest)
            manifest_path = dest / "IDENTITY-MANIFEST.json"
            sidecar = dest / "FACTORY-REGISTRY.json"

            manifest_path.unlink()
            with self.assertRaisesRegex(identity.IdentityTreeError, "IDENTITY-MANIFEST"):
                identity.validate_identity_tree(dest)
            manifest_path.write_text("not-json", encoding="utf-8")
            with self.assertRaisesRegex(identity.IdentityTreeError, "not readable JSON"):
                identity.validate_identity_tree(dest)
            manifest_path.write_text("{}\n", encoding="utf-8")
            with self.assertRaisesRegex(identity.IdentityTreeError, "list of mappings"):
                identity.validate_identity_tree(dest)
            manifest_path.write_text("[1]\n", encoding="utf-8")
            with self.assertRaisesRegex(identity.IdentityTreeError, "must be an object"):
                identity.validate_identity_tree(dest)
            manifest_path.write_text(
                json.dumps([{"registry": {"sha256": "0" * 64}}]) + "\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(identity.IdentityTreeError, "does not match sidecar pin"):
                identity.validate_identity_tree(dest)
            manifest_path.write_text(json.dumps([{"action": "retained"}]) + "\n", encoding="utf-8")
            with self.assertRaisesRegex(identity.IdentityTreeError, "does not match sidecar pin"):
                identity.validate_identity_tree(dest)
            self.assertTrue(sidecar.is_file())

    def test_validate_identity_tree_replays_exclusions_before_trusting_action(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "src"
            dest = Path(tmp) / "dest"
            factory = src / FABLE_ACT
            factory.mkdir(parents=True)
            (factory / "episodes.jsonl").write_text(
                identity.canonical_json(episode(FABLE_ACT))
                + "\n"
                + identity.canonical_json(episode("never-reviewed-factory"))
                + "\n",
                encoding="utf-8",
            )
            identity.write_run(src, dest)
            manifest_path = dest / identity.IDENTITY_MANIFEST_SIDECAR
            output_path = dest / FABLE_ACT / "episodes.jsonl"
            original_bytes = manifest_path.read_bytes()
            original = json.loads(original_bytes)

            corrupted_exclusion = copy.deepcopy(original)
            excluded = next(item for item in corrupted_exclusion if item["action"] == "exclude")
            excluded["source"]["original"] = "{}"
            manifest_path.write_text(json.dumps(corrupted_exclusion) + "\n", encoding="utf-8")
            with self.assertRaisesRegex(
                identity.IdentityTreeError,
                "source.original does not match source.sha256",
            ):
                identity.validate_identity_tree(dest)

            manifest_path.write_bytes(original_bytes)
            fabricated_exclusion = copy.deepcopy(original)
            excluded = next(item for item in fabricated_exclusion if item["action"] == "exclude")
            excluded["reason_codes"] = ["identity.fabricated"]
            manifest_path.write_text(json.dumps(fabricated_exclusion) + "\n", encoding="utf-8")
            with self.assertRaisesRegex(identity.IdentityTreeError, "exclusion mapping"):
                identity.validate_identity_tree(dest)

            manifest_path.write_bytes(original_bytes)
            relabeled = copy.deepcopy(original)
            retained = next(item for item in relabeled if item["action"] == "retained")
            retained["action"] = "exclude"
            output_path.unlink()
            manifest_path.write_text(json.dumps(relabeled) + "\n", encoding="utf-8")
            with self.assertRaisesRegex(identity.IdentityTreeError, "action does not match"):
                identity.validate_identity_tree(dest)

    def test_validate_identity_tree_reconciles_output_paths_and_hashes(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "src"
            dest = Path(tmp) / "dest"
            (src / FABLE_ACT).mkdir(parents=True)
            (src / FABLE_ACT / "episodes.jsonl").write_text(
                identity.canonical_json(episode(FABLE_ACT)) + "\n",
                encoding="utf-8",
            )
            identity.write_run(src, dest)
            output = dest / FABLE_ACT / "episodes.jsonl"
            original = output.read_bytes()

            output.write_text(
                identity.canonical_json(episode(FABLE_ACT, goal="tampered")) + "\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(identity.IdentityTreeError, "output hashes"):
                identity.validate_identity_tree(dest)

            output.write_bytes(original)
            output.unlink()
            with self.assertRaisesRegex(identity.IdentityTreeError, "output paths"):
                identity.validate_identity_tree(dest)

            output.write_bytes(original)
            extra = dest / FABLE_ACT / "extra.jsonl"
            extra.write_bytes(original)
            with self.assertRaisesRegex(identity.IdentityTreeError, "output paths"):
                identity.validate_identity_tree(dest)

    def test_validate_identity_tree_binds_canonical_json_types_to_replay(self):
        cases = ((2, 2.0, "int-vs-float"), (1, True, "int-vs-bool"))
        for source_value, tampered_value, label in cases:
            with self.subTest(label=label), tempfile.TemporaryDirectory() as tmp:
                src = Path(tmp) / "src"
                dest = Path(tmp) / "dest"
                factory = src / FABLE_ACT
                factory.mkdir(parents=True)
                raw = episode(FABLE_ACT)
                raw["meta"]["round"] = source_value
                (factory / "episodes.jsonl").write_text(
                    identity.canonical_json(raw) + "\n",
                    encoding="utf-8",
                )
                identity.write_run(src, dest)
                manifest_path = dest / identity.IDENTITY_MANIFEST_SIDECAR
                output_path = dest / FABLE_ACT / "episodes.jsonl"
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                retained = next(item for item in manifest if item["action"] == "retained")
                output = json.loads(output_path.read_text(encoding="utf-8"))
                output["meta"]["round"] = tampered_value
                retained["output_sha256"] = identity._sha256_json(output)
                output_path.write_text(
                    identity.canonical_json(output) + "\n",
                    encoding="utf-8",
                )
                manifest_path.write_text(json.dumps(manifest) + "\n", encoding="utf-8")

                with self.assertRaisesRegex(identity.IdentityTreeError, "output hashes"):
                    identity.validate_identity_tree(dest)

    def test_validate_identity_tree_reconciles_root_and_nested_ids(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "src"
            dest = Path(tmp) / "dest"
            factory = src / "tool-use-preference-factory"
            factory.mkdir(parents=True)
            (factory / "preferences.jsonl").write_text(
                identity.canonical_json(grok_pref()) + "\n", encoding="utf-8"
            )
            identity.write_run(src, dest)
            manifest_path = dest / identity.IDENTITY_MANIFEST_SIDECAR
            original = json.loads(manifest_path.read_text(encoding="utf-8"))
            retained = next(item for item in original if item["action"] == "retained")

            tampered = copy.deepcopy(original)
            next(item for item in tampered if item["action"] == "retained")["output_id"] = (
                "sfcur-tampered"
            )
            manifest_path.write_text(json.dumps(tampered) + "\n", encoding="utf-8")
            with self.assertRaisesRegex(identity.IdentityTreeError, "output_id"):
                identity.validate_identity_tree(dest)

            tampered = copy.deepcopy(original)
            retained_copy = next(item for item in tampered if item["action"] == "retained")
            chosen = next(
                item for item in retained_copy["id_mappings"] if item["owner_path"] == "/chosen"
            )
            chosen["output_id"] = "sfcur-tampered-nested"
            manifest_path.write_text(json.dumps(tampered) + "\n", encoding="utf-8")
            with self.assertRaisesRegex(identity.IdentityTreeError, r"id[_ ]mapping"):
                identity.validate_identity_tree(dest)

            self.assertEqual(retained["output_id"], retained["id_mappings"][0]["output_id"])

    def test_validate_identity_tree_replays_complete_original_id_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "src"
            dest = Path(tmp) / "dest"
            factory = src / FABLE_THALAMIC
            factory.mkdir(parents=True)
            (factory / "trajectories.jsonl").write_text(
                identity.canonical_json(thalamic("simulated")) + "\n",
                encoding="utf-8",
            )
            identity.write_run(src, dest)
            manifest_path = dest / identity.IDENTITY_MANIFEST_SIDECAR
            original = json.loads(manifest_path.read_text(encoding="utf-8"))

            fabricated = copy.deepcopy(original)
            retained = next(item for item in fabricated if item["action"] == "retained")
            retained["original_ids"][0]["value"] = "fabricated"
            manifest_path.write_text(json.dumps(fabricated) + "\n", encoding="utf-8")
            with self.assertRaisesRegex(identity.IdentityTreeError, r"\.original_ids"):
                identity.validate_identity_tree(dest)

            deleted = copy.deepcopy(original)
            retained = next(item for item in deleted if item["action"] == "retained")
            retained["id_mappings"][0].pop("original_ids")
            manifest_path.write_text(json.dumps(deleted) + "\n", encoding="utf-8")
            with self.assertRaisesRegex(identity.IdentityTreeError, r"\.id_mappings"):
                identity.validate_identity_tree(dest)

    def test_validate_identity_tree_reconciles_every_provenance_mapping(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "src"
            dest = Path(tmp) / "dest"
            factory = src / "tool-use-preference-factory"
            factory.mkdir(parents=True)
            (factory / "preferences.jsonl").write_text(
                identity.canonical_json(grok_pref()) + "\n", encoding="utf-8"
            )
            identity.write_run(src, dest)
            manifest_path = dest / identity.IDENTITY_MANIFEST_SIDECAR
            original = json.loads(manifest_path.read_text(encoding="utf-8"))

            def retained_mapping(manifest):
                return next(item for item in manifest if item["action"] == "retained")

            def reseal(provenance_mapping):
                provenance_mapping["mapping_sha256"] = identity._provenance_mapping_sha256(
                    provenance_mapping
                )

            tampered = copy.deepcopy(original)
            root = retained_mapping(tampered)["provenance_mappings"][0]
            root["canonical"]["kind"] = "real"
            reseal(root)
            manifest_path.write_text(json.dumps(tampered) + "\n", encoding="utf-8")
            with self.assertRaisesRegex(identity.IdentityTreeError, "canonical"):
                identity.validate_identity_tree(dest)

            tampered = copy.deepcopy(original)
            root = retained_mapping(tampered)["provenance_mappings"][0]
            root["owner_path"] = "/missing"
            reseal(root)
            manifest_path.write_text(json.dumps(tampered) + "\n", encoding="utf-8")
            with self.assertRaisesRegex(identity.IdentityTreeError, "owner_path"):
                identity.validate_identity_tree(dest)

            tampered = copy.deepcopy(original)
            root = retained_mapping(tampered)["provenance_mappings"][0]
            root["original"]["owner_provenance"]["value"] = "invented"
            reseal(root)
            manifest_path.write_text(json.dumps(tampered) + "\n", encoding="utf-8")
            with self.assertRaisesRegex(identity.IdentityTreeError, "value must be null"):
                identity.validate_identity_tree(dest)

            tampered = copy.deepcopy(original)
            retained_mapping(tampered)["provenance_mappings"][0]["mapping_sha256"] = "0" * 64
            manifest_path.write_text(json.dumps(tampered) + "\n", encoding="utf-8")
            with self.assertRaisesRegex(identity.IdentityTreeError, "mapping digest"):
                identity.validate_identity_tree(dest)

            tampered = copy.deepcopy(original)
            retained_mapping(tampered)["provenance_mappings"].pop()
            manifest_path.write_text(json.dumps(tampered) + "\n", encoding="utf-8")
            with self.assertRaisesRegex(identity.IdentityTreeError, "owner paths"):
                identity.validate_identity_tree(dest)

    def test_validate_identity_tree_binds_provenance_mapping_json_types_to_replay(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "src"
            dest = Path(tmp) / "dest"
            factory = src / FABLE_ACT
            factory.mkdir(parents=True)
            raw = episode(FABLE_ACT)
            raw["state"] = {"sim_or_real": "simulated"}
            raw["provenance"] = {
                "kind": "simulated",
                "claimed": "simulated",
                "rank": 1,
            }
            (factory / "episodes.jsonl").write_text(
                identity.canonical_json(raw) + "\n",
                encoding="utf-8",
            )
            identity.write_run(src, dest)
            manifest_path = dest / identity.IDENTITY_MANIFEST_SIDECAR
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            retained = next(item for item in manifest if item["action"] == "retained")
            state_mapping = next(
                item
                for item in retained["provenance_mappings"]
                if item.get("state_path") == "/state"
            )
            state_mapping["original"]["owner_provenance"]["value"]["rank"] = True
            state_mapping["mapping_sha256"] = identity._provenance_mapping_sha256(state_mapping)
            manifest_path.write_text(json.dumps(manifest) + "\n", encoding="utf-8")

            with self.assertRaisesRegex(identity.IdentityTreeError, "provenance mapping"):
                identity.validate_identity_tree(dest)

    def test_validate_identity_tree_requires_complete_root_provenance_targets(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "src"
            dest = Path(tmp) / "dest"
            factory = src / FABLE_ACT
            factory.mkdir(parents=True)
            stateful_episode = episode(FABLE_ACT)
            stateful_episode["state"] = {"sim_or_real": "simulated"}
            (factory / "episodes.jsonl").write_text(
                identity.canonical_json(stateful_episode) + "\n", encoding="utf-8"
            )
            identity.write_run(src, dest)
            manifest_path = dest / identity.IDENTITY_MANIFEST_SIDECAR
            original = json.loads(manifest_path.read_text(encoding="utf-8"))

            def retained_mapping(manifest):
                return next(item for item in manifest if item["action"] == "retained")

            provenance_mappings = retained_mapping(original)["provenance_mappings"]
            self.assertEqual(
                {(item["owner_path"], item.get("state_path")) for item in provenance_mappings},
                {("/", "/state"), ("/", None)},
            )

            for missing_target in (("/", "/state"), ("/", None)):
                with self.subTest(missing_target=missing_target):
                    tampered = copy.deepcopy(original)
                    retained = retained_mapping(tampered)
                    retained["provenance_mappings"] = [
                        item
                        for item in retained["provenance_mappings"]
                        if (item["owner_path"], item.get("state_path")) != missing_target
                    ]
                    manifest_path.write_text(json.dumps(tampered) + "\n", encoding="utf-8")
                    with self.assertRaisesRegex(
                        identity.IdentityTreeError, "provenance mapping targets"
                    ):
                        identity.validate_identity_tree(dest)

            tampered = copy.deepcopy(original)
            root_owner_mapping = next(
                item
                for item in retained_mapping(tampered)["provenance_mappings"]
                if item["owner_path"] == "/" and "state_path" not in item
            )
            root_owner_mapping["basis"] = "state.provenance.kind"
            root_owner_mapping["canonical"]["basis"] = "state.provenance.kind"
            root_owner_mapping["mapping_sha256"] = identity._provenance_mapping_sha256(
                root_owner_mapping
            )
            output_path = dest / FABLE_ACT / "episodes.jsonl"
            tampered_output = json.loads(output_path.read_text(encoding="utf-8"))
            tampered_output["provenance"]["basis"] = "state.provenance.kind"
            retained_mapping(tampered)["output_sha256"] = identity._sha256_json(tampered_output)
            output_path.write_text(
                identity.canonical_json(tampered_output) + "\n", encoding="utf-8"
            )
            manifest_path.write_text(json.dumps(tampered) + "\n", encoding="utf-8")
            with self.assertRaisesRegex(
                identity.IdentityTreeError,
                "output hashes",
            ):
                identity.validate_identity_tree(dest)

    def test_validate_identity_tree_accepts_hash_verified_stateful_and_stateless_sources(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "src"
            dest = Path(tmp) / "dest"
            factory = src / FABLE_ACT
            factory.mkdir(parents=True)
            stateful = episode(FABLE_ACT)
            stateful["state"] = {"sim_or_real": "simulated"}
            stateless = episode(FABLE_ACT, outcome="fixed without explicit state")
            source_lines = [identity.canonical_json(stateful), identity.canonical_json(stateless)]
            (factory / "episodes.jsonl").write_text(
                "\n".join(source_lines) + "\n", encoding="utf-8"
            )

            identity.write_run(src, dest)
            identity.validate_identity_tree(dest)

            manifest = json.loads(
                (dest / identity.IDENTITY_MANIFEST_SIDECAR).read_text(encoding="utf-8")
            )
            retained_by_line = {
                item["source"]["line"]: item for item in manifest if item["action"] == "retained"
            }
            self.assertEqual(set(retained_by_line), {1, 2})
            for line_no, source_line in enumerate(source_lines, 1):
                with self.subTest(line_no=line_no):
                    source_meta = retained_by_line[line_no]["source"]
                    self.assertEqual(source_meta["original"], source_line)
                    self.assertEqual(
                        source_meta["sha256"], hashlib.sha256(source_line.encode()).hexdigest()
                    )

            stateful_mappings = retained_by_line[1]["provenance_mappings"]
            self.assertEqual(
                {(item["owner_path"], item.get("state_path")) for item in stateful_mappings},
                {("/", "/state"), ("/", None)},
            )
            self.assertEqual({item["basis"] for item in stateful_mappings}, {"state.sim_or_real"})
            stateless_mappings = retained_by_line[2]["provenance_mappings"]
            self.assertEqual(
                {(item["owner_path"], item.get("state_path")) for item in stateless_mappings},
                {("/", None)},
            )
            self.assertEqual(stateless_mappings[0]["basis"], identity.SHAPE_BASIS["episode"])

    def test_validate_identity_tree_external_manifest_pin_rejects_coordinated_reseal(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "src"
            dest = Path(tmp) / "dest"
            factory = src / FABLE_ACT
            factory.mkdir(parents=True)
            stateful = episode(FABLE_ACT)
            stateful["state"] = {"sim_or_real": "simulated"}
            (factory / "episodes.jsonl").write_text(
                identity.canonical_json(stateful) + "\n", encoding="utf-8"
            )
            identity.write_run(src, dest)
            manifest_path = dest / identity.IDENTITY_MANIFEST_SIDECAR
            output_path = dest / FABLE_ACT / "episodes.jsonl"
            original_manifest_bytes = manifest_path.read_bytes()
            original_manifest_digest = hashlib.sha256(original_manifest_bytes).hexdigest()
            original_manifest = json.loads(original_manifest_bytes)
            identity.validate_identity_tree(
                dest,
                expected_manifest_digest=original_manifest_digest,
            )
            with self.assertRaisesRegex(
                identity.IdentityTreeError,
                "expected manifest digest",
            ):
                identity.validate_identity_tree(dest, expected_manifest_digest="not-a-sha256")

            retained = next(item for item in original_manifest if item["action"] == "retained")
            modified_source = json.loads(retained["source"]["original"])
            modified_source.pop("state")
            modified_line = identity.canonical_json(modified_source)
            modified_digest = hashlib.sha256(modified_line.encode("utf-8")).hexdigest()
            replayed = identity.curate_record(
                identity.SourceRecord(
                    modified_source,
                    retained["source"]["path"],
                    retained["source"]["line"],
                    modified_digest,
                    modified_line,
                )
            )
            self.assertEqual(replayed.action, "retained")
            self.assertIsNotNone(replayed.record)
            tampered_manifest = copy.deepcopy(original_manifest)
            tampered_index = tampered_manifest.index(
                next(item for item in tampered_manifest if item["action"] == "retained")
            )
            tampered_manifest[tampered_index] = replayed.mapping
            output_path.write_text(
                identity.canonical_json(replayed.record) + "\n",
                encoding="utf-8",
            )
            manifest_path.write_text(json.dumps(tampered_manifest) + "\n", encoding="utf-8")

            identity.validate_identity_tree(dest)
            with self.assertRaisesRegex(identity.IdentityTreeError, "manifest digest mismatch"):
                identity.validate_identity_tree(
                    dest,
                    expected_manifest_digest=original_manifest_digest,
                )

    def test_validate_identity_tree_rejects_duplicate_keys_with_exact_pins(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "src"
            dest = Path(tmp) / "dest"
            factory = src / FABLE_ACT
            factory.mkdir(parents=True)
            stateful = episode(FABLE_ACT)
            stateful["state"] = {"sim_or_real": "simulated"}
            (factory / "episodes.jsonl").write_text(
                identity.canonical_json(stateful) + "\n",
                encoding="utf-8",
            )
            identity.write_run(src, dest)

            registry_path = dest / identity.FACTORY_REGISTRY_SIDECAR
            manifest_path = dest / identity.IDENTITY_MANIFEST_SIDECAR
            output_path = dest / FABLE_ACT / "episodes.jsonl"
            registry_digest = hashlib.sha256(registry_path.read_bytes()).hexdigest()
            manifest_bytes = manifest_path.read_bytes()
            manifest_digest = hashlib.sha256(manifest_bytes).hexdigest()
            output_bytes = output_path.read_bytes()

            output_mutations = {
                "root-id": output_bytes.replace(
                    b"{",
                    b'{"id":"FORGED-FIRST-ID",',
                    1,
                ),
                "nested-provenance-kind": output_bytes.replace(
                    b'"provenance":{',
                    b'"provenance":{"kind":"real",',
                    1,
                ),
                "factory-declaration": output_bytes.replace(
                    b'"meta":{"factory":',
                    b'"meta":{"factory":"attacker-factory","factory":',
                    1,
                ),
            }
            for label, mutated_output in output_mutations.items():
                with self.subTest(boundary="output", duplicate=label):
                    self.assertNotEqual(mutated_output, output_bytes)
                    output_path.write_bytes(mutated_output)
                    with self.assertRaisesRegex(
                        identity.IdentityTreeError,
                        "duplicate JSON object key",
                    ):
                        identity.validate_identity_tree(
                            dest,
                            expected_registry_digest=registry_digest,
                            expected_manifest_digest=manifest_digest,
                        )
                    output_path.write_bytes(output_bytes)

            duplicate_manifest = manifest_bytes.decode("utf-8").replace(
                '"action": "retained"',
                '"action": "exclude", "action": "retained"',
                1,
            )
            duplicate_manifest_bytes = duplicate_manifest.encode("utf-8")
            self.assertNotEqual(duplicate_manifest_bytes, manifest_bytes)
            manifest_path.write_bytes(duplicate_manifest_bytes)
            duplicate_manifest_digest = hashlib.sha256(duplicate_manifest_bytes).hexdigest()
            with self.assertRaisesRegex(
                identity.IdentityTreeError,
                "duplicate JSON object key",
            ):
                identity.validate_identity_tree(
                    dest,
                    expected_registry_digest=registry_digest,
                    expected_manifest_digest=duplicate_manifest_digest,
                )

            manifest = json.loads(manifest_bytes)
            retained = next(item for item in manifest if item["action"] == "retained")
            source_original = retained["source"]["original"]
            duplicate_source_original = source_original.replace(
                '"meta":{"factory":',
                '"meta":{"factory":"attacker-factory","factory":',
                1,
            )
            self.assertNotEqual(duplicate_source_original, source_original)
            retained["source"]["original"] = duplicate_source_original
            retained["source"]["sha256"] = hashlib.sha256(
                duplicate_source_original.encode("utf-8")
            ).hexdigest()
            duplicate_source_manifest_bytes = (
                json.dumps(
                    manifest,
                    ensure_ascii=False,
                    allow_nan=False,
                    indent=2,
                    sort_keys=True,
                )
                + "\n"
            ).encode("utf-8")
            manifest_path.write_bytes(duplicate_source_manifest_bytes)
            duplicate_source_manifest_digest = hashlib.sha256(
                duplicate_source_manifest_bytes
            ).hexdigest()
            with self.assertRaisesRegex(
                identity.IdentityTreeError,
                "duplicate JSON object key",
            ):
                identity.validate_identity_tree(
                    dest,
                    expected_registry_digest=registry_digest,
                    expected_manifest_digest=duplicate_source_manifest_digest,
                )

    def test_duplicate_keys_are_rejected_at_non_tree_trust_boundaries(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            registry_path = root / "FACTORY-REGISTRY.json"
            registry_text = json.dumps(_registry_payload([_valid_row()]))
            duplicate_registry = registry_text.replace(
                '"lookup_key": "path_id"',
                '"lookup_key": "slug", "lookup_key": "path_id"',
                1,
            )
            registry_path.write_text(duplicate_registry, encoding="utf-8")
            with self.assertRaisesRegex(
                identity.IdentityCurationError,
                "duplicate JSON object key",
            ):
                identity.load_registry(registry_path)

            raw = episode(FABLE_ACT)
            source_json = identity.canonical_json(raw)
            duplicate_source_json = source_json.replace(
                '"meta":{"factory":',
                '"meta":{"factory":"attacker-factory","factory":',
                1,
            )
            duplicate_source_digest = hashlib.sha256(
                duplicate_source_json.encode("utf-8")
            ).hexdigest()
            with self.assertRaisesRegex(
                identity.IdentityCurationError,
                "duplicate JSON object key",
            ):
                identity.curate_record(
                    identity.SourceRecord(
                        raw,
                        f"{FABLE_ACT}/episodes.jsonl",
                        1,
                        duplicate_source_digest,
                        duplicate_source_json,
                    )
                )

            source_path = root / FABLE_ACT / "episodes.jsonl"
            source_path.parent.mkdir()
            source_path.write_bytes(duplicate_source_json.encode("utf-8") + b"\n")
            with self.assertRaisesRegex(
                identity.IdentityCurationError,
                "duplicate JSON object key",
            ):
                identity.iter_source_records(source_path)

            stderr = io.StringIO()
            with mock.patch("sys.stderr", stderr):
                self.assertEqual(identity.main([str(source_path)]), 1)
            self.assertIn("duplicate JSON object key", stderr.getvalue())

    def test_validate_identity_tree_requires_exact_canonical_output_bytes(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "src"
            dest = Path(tmp) / "dest"
            factory = src / FABLE_ACT
            factory.mkdir(parents=True)
            (factory / "episodes.jsonl").write_text(
                identity.canonical_json(episode(FABLE_ACT)) + "\n",
                encoding="utf-8",
            )
            identity.write_run(src, dest)

            registry_digest = hashlib.sha256(
                (dest / identity.FACTORY_REGISTRY_SIDECAR).read_bytes()
            ).hexdigest()
            manifest_digest = hashlib.sha256(
                (dest / identity.IDENTITY_MANIFEST_SIDECAR).read_bytes()
            ).hexdigest()
            output_path = dest / FABLE_ACT / "episodes.jsonl"
            canonical_output = output_path.read_bytes()
            mutations = {
                "leading-space": b" " + canonical_output,
                "crlf": canonical_output[:-1] + b"\r\n",
                "missing-final-lf": canonical_output[:-1],
                "extra-trailing-blank": canonical_output + b"\n",
            }
            for label, payload in mutations.items():
                with self.subTest(mutation=label):
                    output_path.write_bytes(payload)
                    with self.assertRaisesRegex(
                        identity.IdentityTreeError,
                        r"canonical|LF",
                    ):
                        identity.validate_identity_tree(
                            dest,
                            expected_registry_digest=registry_digest,
                            expected_manifest_digest=manifest_digest,
                        )
            output_path.write_bytes(canonical_output)
            identity.validate_identity_tree(
                dest,
                expected_registry_digest=registry_digest,
                expected_manifest_digest=manifest_digest,
            )

    def test_write_run_accepts_unicode_line_separators_inside_json_strings(self):
        separators = ("\u0085", "\u2028", "\u2029")
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "src"
            dest = Path(tmp) / "dest"
            factory = src / FABLE_ACT
            factory.mkdir(parents=True)
            source_records = []
            for index, separator in enumerate(separators, 1):
                raw = episode(
                    FABLE_ACT,
                    goal=f"root{separator}goal-{index}",
                )
                raw["steps"][0]["observation"] = f"nested{separator}observation-{index}"
                source_records.append(raw)
            source_bytes = (
                "\n".join(identity.canonical_json(record) for record in source_records) + "\n"
            ).encode("utf-8")
            (factory / "episodes.jsonl").write_bytes(source_bytes)

            results = identity.write_run(src, dest)
            self.assertEqual([result.action for result in results], ["retained"] * 3)
            registry_digest = hashlib.sha256(
                (dest / identity.FACTORY_REGISTRY_SIDECAR).read_bytes()
            ).hexdigest()
            manifest_digest = hashlib.sha256(
                (dest / identity.IDENTITY_MANIFEST_SIDECAR).read_bytes()
            ).hexdigest()
            identity.validate_identity_tree(
                dest,
                expected_registry_digest=registry_digest,
                expected_manifest_digest=manifest_digest,
            )

            output_bytes = (dest / FABLE_ACT / "episodes.jsonl").read_bytes()
            output_lines = output_bytes[:-1].split(b"\n")
            self.assertEqual(len(output_lines), 3)
            for index, (separator, line_bytes) in enumerate(zip(separators, output_lines), 1):
                with self.subTest(separator=f"U+{ord(separator):04X}"):
                    self.assertIn(separator.encode("utf-8"), line_bytes)
                    output_record = identity._strict_json_loads(line_bytes.decode("utf-8"))
                    self.assertEqual(output_record["goal"], f"root{separator}goal-{index}")
                    self.assertEqual(
                        output_record["steps"][0]["observation"],
                        f"nested{separator}observation-{index}",
                    )

    def test_write_run_preserves_physical_source_lines_across_recuration(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "src"
            first = Path(tmp) / "first"
            second = Path(tmp) / "second"
            factory = src / FABLE_ACT
            factory.mkdir(parents=True)
            (factory / "episodes.jsonl").write_text(
                "\n"
                + identity.canonical_json(episode("never-reviewed-factory"))
                + "\n"
                + identity.canonical_json(episode(FABLE_ACT))
                + "\n",
                encoding="utf-8",
            )
            first_results = identity.write_run(src, first)
            output = first / FABLE_ACT / "episodes.jsonl"
            self.assertEqual(output.read_text(encoding="utf-8").splitlines()[:2], ["", ""])
            retained_first = next(item for item in first_results if item.action == "retained")
            self.assertEqual(retained_first.mapping["source"]["line"], 3)
            identity.validate_identity_tree(first)

            second_results = identity.write_run(first, second)
            retained_second = next(item for item in second_results if item.action == "retained")
            self.assertEqual(retained_second.mapping["source"]["line"], 3)
            self.assertEqual(retained_second.record["id"], retained_first.record["id"])
            identity.validate_identity_tree(second)

    def test_expected_registry_digest_distinguishes_pin_from_self_consistency(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "src"
            dest = Path(tmp) / "dest"
            factory = src / FABLE_ACT
            factory.mkdir(parents=True)
            (factory / "episodes.jsonl").write_text(
                identity.canonical_json(episode(FABLE_ACT)) + "\n",
                encoding="utf-8",
            )
            identity.write_run(src, dest)
            sidecar = dest / identity.FACTORY_REGISTRY_SIDECAR
            reviewed_digest = hashlib.sha256(sidecar.read_bytes()).hexdigest()
            replacement = json.loads(sidecar.read_text(encoding="utf-8"))
            replacement["notes"] += " Replacement fixture."
            replacement_bytes = (json.dumps(replacement, indent=2) + "\n").encode()
            replacement_digest = hashlib.sha256(replacement_bytes).hexdigest()
            sidecar.write_bytes(replacement_bytes)
            manifest_path = dest / identity.IDENTITY_MANIFEST_SIDECAR
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            for mapping in manifest:
                mapping["registry"]["sha256"] = replacement_digest
            manifest_path.write_text(json.dumps(manifest) + "\n", encoding="utf-8")

            identity.validate_identity_tree(dest)
            with self.assertRaisesRegex(identity.IdentityTreeError, "digest mismatch"):
                identity.validate_identity_tree(dest, expected_registry_digest=reviewed_digest)

    def test_identity_tree_rejects_symlinks_and_nonstandard_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "src"
            dest = Path(tmp) / "dest"
            factory = src / FABLE_ACT
            factory.mkdir(parents=True)
            source_file = factory / "episodes.jsonl"
            raw = episode(FABLE_ACT)
            raw["metric"] = float("nan")
            source_file.write_text(json.dumps(raw) + "\n", encoding="utf-8")
            with self.assertRaisesRegex(identity.IdentityCurationError, "non-standard"):
                identity.iter_source_records(src)

            source_file.write_text(
                identity.canonical_json(episode(FABLE_ACT)) + "\n",
                encoding="utf-8",
            )
            identity.write_run(src, dest)
            output = dest / FABLE_ACT / "episodes.jsonl"
            external = Path(tmp) / "external.jsonl"
            output.replace(external)
            output.symlink_to(external)
            with self.assertRaisesRegex(identity.IdentityTreeError, "symlinks"):
                identity.validate_identity_tree(dest)

    def test_manifest_parser_rejects_nonstandard_json_constants(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "src"
            dest = Path(tmp) / "dest"
            factory = src / FABLE_ACT
            factory.mkdir(parents=True)
            (factory / "episodes.jsonl").write_text(
                identity.canonical_json(episode(FABLE_ACT)) + "\n",
                encoding="utf-8",
            )
            identity.write_run(src, dest)
            manifest_path = dest / identity.IDENTITY_MANIFEST_SIDECAR
            payload = manifest_path.read_text(encoding="utf-8").replace(
                '"action": "retained"',
                '"nonstandard": NaN, "action": "retained"',
                1,
            )
            manifest_path.write_text(payload, encoding="utf-8")
            with self.assertRaisesRegex(identity.IdentityTreeError, "non-standard"):
                identity.validate_identity_tree(dest)

    def test_iter_source_records_file_blank_lines_and_parse_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / FABLE_ACT / "episodes.jsonl"
            path.parent.mkdir()
            path.write_text(
                identity.canonical_json(episode(FABLE_ACT)) + "\n\nnot-json\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(identity.IdentityCurationError, "JSON parse error"):
                identity.iter_source_records(path)
            path.write_text(
                identity.canonical_json(episode(FABLE_ACT)) + "\n\n",
                encoding="utf-8",
            )
            records = identity.iter_source_records(path)
            self.assertEqual(len(records), 1)
            self.assertEqual(records[0].source_path, f"{FABLE_ACT}/episodes.jsonl")
            factory_records = identity.iter_source_records(path.parent)
            self.assertEqual(factory_records[0].source_path, records[0].source_path)
            run_records = identity.iter_source_records(Path(tmp))
            self.assertEqual(run_records[0].source_path, records[0].source_path)

    def test_iter_source_records_hashes_normalized_physical_line_payload(self):
        payload = identity.canonical_json(episode(FABLE_ACT)).encode("utf-8")
        cases = (
            ("payload", payload, payload),
            ("lf", payload + b"\n", payload),
            ("crlf", payload + b"\r\n", payload),
            ("bare-cr", payload + b"\r", payload + b"\r"),
            ("crcrlf", payload + b"\r\r\n", payload + b"\r"),
        )

        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / FABLE_ACT / "episodes.jsonl"
            source.parent.mkdir()
            for label, physical_bytes, expected_payload in cases:
                with self.subTest(line_ending=label):
                    source.write_bytes(physical_bytes)
                    records = identity.iter_source_records(source)

                    self.assertEqual(len(records), 1)
                    self.assertEqual(records[0].source_json.encode("utf-8"), expected_payload)
                    self.assertEqual(
                        records[0].source_sha256,
                        hashlib.sha256(expected_payload).hexdigest(),
                    )

                    dest = Path(tmp) / f"dest-{label}"
                    identity.write_run(source, dest)
                    identity.validate_identity_tree(dest)
                    manifest = json.loads(
                        (dest / identity.IDENTITY_MANIFEST_SIDECAR).read_text(encoding="utf-8")
                    )
                    source_evidence = manifest[0]["source"]
                    self.assertEqual(
                        source_evidence["original"].encode("utf-8"),
                        expected_payload,
                    )
                    self.assertEqual(
                        source_evidence["sha256"],
                        hashlib.sha256(expected_payload).hexdigest(),
                    )

    def test_iter_source_records_rejects_missing_non_jsonl_and_empty_sources(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with self.assertRaisesRegex(identity.IdentityCurationError, "does not exist"):
                identity.iter_source_records(root / "missing")

            text_file = root / FABLE_ACT / "records.txt"
            text_file.parent.mkdir()
            text_file.write_text("{}\n", encoding="utf-8")
            with self.assertRaisesRegex(identity.IdentityCurationError, "not a JSONL file"):
                identity.iter_source_records(text_file)

            empty = root / "empty"
            empty.mkdir()
            with self.assertRaisesRegex(identity.IdentityCurationError, "no JSONL files"):
                identity.iter_source_records(empty)

    def test_write_run_preserves_factory_segment_for_file_and_factory_inputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            factory = root / FABLE_ACT
            factory.mkdir()
            source_file = factory / "episodes.jsonl"
            source_file.write_text(
                identity.canonical_json(episode(FABLE_ACT)) + "\n",
                encoding="utf-8",
            )
            for index, source_input in enumerate((source_file, factory), 1):
                with self.subTest(source_input=source_input):
                    dest = root / f"dest-{index}"
                    results = identity.write_run(source_input, dest)
                    self.assertEqual(results[0].action, "retained")
                    self.assertTrue((dest / FABLE_ACT / "episodes.jsonl").is_file())
                    identity.validate_identity_tree(dest)

    def test_root_jsonl_does_not_shift_registered_factory_coordinates(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = Path(tmp) / "run"
            nested = run / FABLE_ACT
            nested.mkdir(parents=True)
            (run / "root.jsonl").write_text(
                identity.canonical_json(episode("run")) + "\n",
                encoding="utf-8",
            )
            (nested / "episodes.jsonl").write_text(
                identity.canonical_json(episode(FABLE_ACT)) + "\n",
                encoding="utf-8",
            )
            records = identity.iter_source_records(run)
            self.assertEqual(
                {record.source_path for record in records},
                {"run/root.jsonl", f"{FABLE_ACT}/episodes.jsonl"},
            )
            results = identity.curate_records(records)
            nested_result = next(
                result
                for result in results
                if result.mapping["source"]["path"].startswith(FABLE_ACT)
            )
            self.assertEqual(nested_result.action, "retained")

    def test_nested_inputs_preserve_the_registered_factory_segment(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            nested = root / FABLE_ACT / "data"
            nested.mkdir(parents=True)
            source_file = nested / "episodes.jsonl"
            source_file.write_text(
                identity.canonical_json(episode(FABLE_ACT)) + "\n",
                encoding="utf-8",
            )
            expected = f"{FABLE_ACT}/data/episodes.jsonl"
            for source_input in (source_file, nested):
                with self.subTest(source_input=source_input):
                    records = identity.iter_source_records(source_input)
                    self.assertEqual(records[0].source_path, expected)

    def test_marker_mode_scan_excludes_uncommitted_batches(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            factory = root / FABLE_ACT
            factory.mkdir()
            (factory / round_txn.MODE_FILE).write_text(
                '{"version":1,"legacy_baseline":0,"commit_point":"ROUND-rNN.complete.json"}\n',
                encoding="utf-8",
            )
            committed = factory / "batch-r01.jsonl"
            committed_record = episode(FABLE_ACT)
            committed_record["id"] = "agentic-coding-r01-0001"
            committed_record["reward"] = {"success": True}
            committed_record["steps"][0]["decision_basis"] = (
                "Observation: deterministic fixture failed"
            )
            committed.write_text(
                identity.canonical_json(committed_record) + "\n",
                encoding="utf-8",
            )
            notes = factory / "NOTES-r01.md"
            notes.write_text("Novel coverage: 80%\n", encoding="utf-8")
            (factory / "ROUND-r01.complete.json").write_text(
                json.dumps(
                    {
                        "version": 1,
                        "factory": factory.name,
                        "round": 1,
                        "records": 1,
                        "expected_records": 1,
                        "commit_point": "ROUND-r01.complete.json",
                        "files": [
                            {
                                "name": committed.name,
                                "sha256": hashlib.sha256(committed.read_bytes()).hexdigest(),
                            },
                            {
                                "name": notes.name,
                                "sha256": hashlib.sha256(notes.read_bytes()).hexdigest(),
                            },
                        ],
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            (factory / "batch-r02.jsonl").write_text(
                identity.canonical_json(episode(FABLE_ACT)) + "\n",
                encoding="utf-8",
            )

            for source_input in (factory, root):
                with self.subTest(source_input=source_input):
                    records = identity.iter_source_records(source_input)
                    self.assertEqual(
                        [item.source_path for item in records],
                        [f"{FABLE_ACT}/batch-r01.jsonl"],
                    )

    def test_write_exclusive_unlinks_partial_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sidecar.json"

            def bad_fdopen(*_args, **_kwargs):
                raise OSError("fdopen failed")

            real_close = identity.os.close
            with (
                mock.patch.object(identity.os, "fdopen", bad_fdopen),
                mock.patch.object(identity.os, "close", wraps=real_close) as close,
            ):
                with self.assertRaises(OSError):
                    identity._write_exclusive(path, b"{}")
            close.assert_called_once()
            self.assertFalse(path.exists())

    def test_write_exclusive_fsyncs_file_and_parent_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sidecar.json"
            real_fsync = identity.os.fsync
            with mock.patch.object(identity.os, "fsync", wraps=real_fsync) as fsync:
                identity._write_exclusive(path, b"{}")
            self.assertEqual(fsync.call_count, 2)

    def test_destination_creation_race_never_deletes_the_other_creator(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "src"
            dest = Path(tmp) / "dest"
            factory = src / FABLE_ACT
            factory.mkdir(parents=True)
            (factory / "episodes.jsonl").write_text(
                identity.canonical_json(episode(FABLE_ACT)) + "\n",
                encoding="utf-8",
            )
            original_mkdir = Path.mkdir

            def racing_mkdir(path, mode=0o777, parents=False, exist_ok=False):
                if path == dest:
                    original_mkdir(path, mode=mode, parents=parents, exist_ok=exist_ok)
                    (path / "foreign.txt").write_text("other process\n", encoding="utf-8")
                    raise FileExistsError("destination won by another creator")
                return original_mkdir(path, mode=mode, parents=parents, exist_ok=exist_ok)

            with mock.patch.object(Path, "mkdir", racing_mkdir):
                with self.assertRaisesRegex(FileExistsError, "another creator"):
                    identity.write_run(src, dest)
            self.assertEqual(
                (dest / "foreign.txt").read_text(encoding="utf-8"),
                "other process\n",
            )

    def test_main_dry_run_write_and_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "src"
            dest = Path(tmp) / "dest"
            (src / FABLE_ACT).mkdir(parents=True)
            (src / FABLE_ACT / "episodes.jsonl").write_text(
                identity.canonical_json(episode(FABLE_ACT)) + "\n",
                encoding="utf-8",
            )
            stdout = io.StringIO()
            with mock.patch("sys.stdout", stdout):
                self.assertEqual(identity.main([str(src)]), 0)
            summary = json.loads(stdout.getvalue())
            self.assertEqual(summary["retained"], 1)
            stdout = io.StringIO()
            with mock.patch("sys.stdout", stdout):
                self.assertEqual(identity.main([str(src), "--out", str(dest)]), 0)
            identity.validate_identity_tree(dest)
            stderr = io.StringIO()
            with mock.patch("sys.stderr", stderr):
                self.assertEqual(identity.main([str(src), "--out", str(dest)]), 1)
            self.assertIn("already exists", stderr.getvalue())

            missing_dest = Path(tmp) / "missing-dest"
            stderr = io.StringIO()
            with mock.patch("sys.stderr", stderr):
                self.assertEqual(
                    identity.main([str(Path(tmp) / "missing-source"), "--out", str(missing_dest)]),
                    1,
                )
            self.assertIn("source does not exist", stderr.getvalue())
            self.assertFalse(missing_dest.exists())

    def test_internal_empty_owner_and_root_shape_designed_paths(self):
        self.assertEqual(identity._curated_resolve_owners({}, "episode", []), [])
        curated = episode(FABLE_ACT)
        source_id = identity._source_identity(source(curated, f"{FABLE_ACT}/episodes.jsonl", 1))
        ids, mappings = identity._apply_shape_designed(
            curated,
            curated,
            source_id,
            "episode",
            [("/", curated)],
            "sfcur-episode-record-" + "b" * 64,
            [],
        )
        self.assertEqual(ids[0]["owner_path"], "/")
        self.assertEqual(mappings[0]["canonical"]["kind"], "designed")
        excluded = identity.curate_record(
            source(episode("never-reviewed-factory"), "never-reviewed-factory/e.jsonl", 1)
        )
        retained = identity.curate_record(
            source(episode(FABLE_ACT), f"{FABLE_ACT}/episodes.jsonl", 1)
        )
        summary = identity._summary(
            (excluded, retained),
            identity.default_registry(),
        )
        self.assertEqual(summary["retained"], 1)
        self.assertEqual(summary["excluded"], 1)


if __name__ == "__main__":
    unittest.main()
