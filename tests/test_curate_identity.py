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


def episode(factory=FABLE_ACT, **overrides):
    record = {
        "goal": "repair a deterministic fixture",
        "steps": [{"tool_call": "inspect", "observation": "failing"}],
        "outcome": "fixed",
        "reward": 1.0,
        "meta": {"factory": factory, "round": 2},
    }
    record.update(overrides)
    return record


def safety_case(factory="safety-calibration-factory", **overrides):
    record = {
        "case_type": "correct_refusal",
        "goal": "refuse the unsafe request",
        "steps": [{"tool_call": "refuse", "observation": "refused"}],
        "meta": {"factory": factory},
    }
    record.update(overrides)
    return record


def multi_agent(factory="multi-agent-coordination-factory", **overrides):
    record = {
        "transcript": [{"role": "planner", "text": "plan"}],
        "agents": [{"name": "planner"}],
        "goal": "coordinate a repair",
        "steps": [{"tool_call": "talk", "observation": "ok"}],
        "meta": {"factory": factory},
    }
    record.update(overrides)
    return record


def grok_pref(factory="tool-use-preference-factory", **overrides):
    side = {
        "goal": "use the tool",
        "steps": [{"tool_call": "search", "observation": "hit"}],
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
            "chosen": thalamic("high-fidelity simulation", meta={"id": "chosen-old"}),
            "rejected": thalamic("high-fidelity simulation", meta={"id": "rejected-old"}),
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
            "chosen": thalamic(),
            "rejected": None,
            "critique": "bad shape",
            "meta": {"factory": FABLE_FFPC},
        }
        result = identity.curate_record(
            source(pair, f"{FABLE_FFPC}/bad.jsonl", 1)
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
            "meta": {"id": "pair-legacy", "factory": FABLE_FFPC},
        }
        result = identity.curate_record(
            source(pair, f"{FABLE_FFPC}/preferences.jsonl", 1)
        )
        self.assertEqual(result.action, "exclude")
        paths = {item["path"] for item in result.mapping["original_ids"]}
        self.assertIn("/meta/id", paths)
        self.assertIn("/chosen/meta/id", paths)
        self.assertIn("/rejected/meta/id", paths)


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

    def test_existing_fable_ouroboros_factory_retains_thalamic_records(self):
        raw = thalamic(
            "designed",
            meta={"factory": FABLE_OUROBOROS, "round": 1},
        )
        result = identity.curate_record(
            source(raw, f"{FABLE_OUROBOROS}/batch-r01.jsonl", 1)
        )
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
                    "chosen": thalamic("designed"),
                    "rejected": thalamic("designed"),
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
                    "chosen": thalamic(None),
                    "rejected": thalamic(None),
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
            identity.write_run(src, dest)
            sidecar = dest / "FACTORY-REGISTRY.json"
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

    def test_registry_onboard_rows_are_not_training_ready(self):
        payload = json.loads(identity.FACTORY_REGISTRY_PATH.read_text(encoding="utf-8"))
        self.assertEqual(len(payload["factories"]), 51)
        self.assertEqual(payload["lookup_key"], "path_id")
        for row in payload["factories"]:
            self.assertNotIn("training_ready", row)
            self.assertIsNone(row["publication_target"])
            self.assertEqual(row["training_ready_policy"], "never")
            self.assertTrue(row["identity_authoritative"])
        grok_rows = [
            row for row in payload["factories"] if row["generator"] == "grok-4.6"
        ]
        self.assertEqual(len(grok_rows), 44)
        for row in grok_rows:
            self.assertEqual(row["path_id"], row["payload_factory"])
        eval_row = next(
            item
            for item in payload["factories"]
            if item["path_id"] == "eval-harness-trajectory-factory"
        )
        self.assertEqual(eval_row["payload_factory"], "eval-harness-trajectory-factory")
        ffpc = next(
            item
            for item in payload["factories"]
            if item["path_id"] == FABLE_FFPC
        )
        self.assertIn("curate_preferences", ffpc["allowed_curation_lanes"])
        grok_pref_row = next(
            item
            for item in payload["factories"]
            if item["path_id"] == "tool-use-preference-factory"
        )
        self.assertNotIn("curate_preferences", grok_pref_row["allowed_curation_lanes"])


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
                ({"schema_version": "other", "lookup_key": "path_id", "factories": [_valid_row()]}, "schema_version"),
                ({"schema_version": "factory-registry-v0.1", "lookup_key": "slug", "factories": [_valid_row()]}, "lookup_key"),
                ({"schema_version": "factory-registry-v0.1", "lookup_key": "path_id", "factories": []}, "non-empty list"),
                (_registry_payload(["not-an-object"]), "must be an object"),
                (_registry_payload([{"path_id": "x"}]), "missing fields"),
                (_registry_payload([_valid_row(path_id="")]), "path_id must be a string"),
                (_registry_payload([_valid_row(payload_factory="")]), "payload_factory must be a string"),
                (_registry_payload([_valid_row(record_kinds=[])]), "non-empty list"),
                (_registry_payload([_valid_row(record_kinds=[1])]), "must be strings"),
                (_registry_payload([_valid_row(identity_authoritative="yes")]), "must be a boolean"),
                (_registry_payload([_valid_row(publication_target=17)]), "null or a string"),
                (_registry_payload([_valid_row(training_ready_policy="always")]), "never or compose_eligible"),
                (_registry_payload([_valid_row(allowed_curation_lanes="identity")]), "list of strings"),
                (_registry_payload([_valid_row(provenance_contract_by_kind="episode")]), "must be an object"),
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
            )
            for payload, needle in cases:
                with self.subTest(needle=needle):
                    with self.assertRaisesRegex(identity.IdentityCurationError, needle):
                        _load_temp_registry(Path(tmp) / needle.replace(" ", "_"), payload)

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
        mismatch = identity.curate_record(
            source(missing_meta, f"{FABLE_ACT}/episodes.jsonl", 1)
        )
        self.assertEqual(mismatch.action, "exclude")
        self.assertEqual(
            mismatch.mapping["reason_codes"],
            ["identity.factory_path_payload_mismatch"],
        )
        mismatch_blank = episode(FABLE_ACT)
        mismatch_blank["meta"] = {"factory": "  "}
        blank = identity.curate_record(
            source(mismatch_blank, f"{FABLE_ACT}/episodes.jsonl", 1)
        )
        self.assertEqual(
            blank.mapping["reason_codes"],
            ["identity.factory_path_payload_mismatch"],
        )
        no_meta = episode(FABLE_ACT)
        no_meta["meta"] = "not-an-object"
        self.assertEqual(
            identity.curate_record(
                source(no_meta, f"{FABLE_ACT}/episodes.jsonl", 1)
            ).mapping["reason_codes"],
            ["identity.factory_path_payload_mismatch"],
        )

    def test_exclude_not_authoritative_and_invalid_contract(self):
        with tempfile.TemporaryDirectory() as tmp:
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
                provenance_contract_by_kind={
                    "thalamic": "synthetic_shape_implies_designed"
                },
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

    def test_invalid_bridge_and_missing_state_object_exclude(self):
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
            result.mapping["unresolved_provenance"][0]["reason"],
            "missing_or_non_object_state",
        )

    def test_preference_mixed_claims_and_state_wins_on_sides(self):
        mixed = {
            "chosen": thalamic("designed"),
            "rejected": thalamic("simulated"),
            "meta": {"factory": FABLE_FFPC},
        }
        result = identity.curate_record(source(mixed, f"{FABLE_FFPC}/batch.jsonl", 1))
        self.assertEqual(result.action, "retained")
        self.assertEqual(result.record["provenance"]["kind"], "unknown")

        pref = grok_pref()
        pref["chosen"]["state"] = {"sim_or_real": "designed"}
        pref["rejected"]["state"] = {"sim_or_real": "designed"}
        result = identity.curate_record(
            source(pref, "tool-use-preference-factory/batch.jsonl", 1)
        )
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
            with self.assertRaisesRegex(identity.IdentityCurationError, "never emit"):
                identity.curate_record(
                    source(episode(FABLE_ACT), f"{FABLE_ACT}/episodes.jsonl", 1)
                )
        curated = episode(FABLE_ACT)
        curated["state"] = {"sim_or_real": "simulated"}
        source_id = identity._source_identity(
            source(curated, f"{FABLE_ACT}/episodes.jsonl", 1)
        )
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

            def boom_after_manifest(path, payload):
                original(path, payload)
                if path.name == identity.IDENTITY_MANIFEST_SIDECAR:
                    (dest / identity.FACTORY_REGISTRY_SIDECAR).unlink()
                    raise OSError("sidecar vanished")

            with mock.patch.object(identity, "_write_exclusive", boom_after_manifest):
                with self.assertRaises(OSError):
                    identity.write_run(src, dest)
            self.assertFalse(dest.exists())

            def boom_on_records(path, payload):
                original(path, payload)
                if path.suffix == ".jsonl":
                    raise OSError("fsync failed")
                return None

            with mock.patch.object(identity, "_write_exclusive", boom_on_records):
                with self.assertRaises(OSError):
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

    def test_write_exclusive_unlinks_partial_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sidecar.json"

            def bad_fdopen(*_args, **_kwargs):
                raise OSError("fdopen failed")

            with mock.patch("os.fdopen", bad_fdopen):
                with self.assertRaises(OSError):
                    identity._write_exclusive(path, b"{}")
            self.assertFalse(path.exists())

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
                    identity.main(
                        [str(Path(tmp) / "missing-source"), "--out", str(missing_dest)]
                    ),
                    1,
                )
            self.assertIn("source does not exist", stderr.getvalue())
            self.assertFalse(missing_dest.exists())

    def test_internal_empty_owner_and_root_shape_designed_paths(self):
        self.assertEqual(identity._curated_resolve_owners({}, "episode", []), [])
        curated = episode(FABLE_ACT)
        source_id = identity._source_identity(
            source(curated, f"{FABLE_ACT}/episodes.jsonl", 1)
        )
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
