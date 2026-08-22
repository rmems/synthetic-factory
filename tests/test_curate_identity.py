#!/usr/bin/env python3
"""Focused tests for deterministic identity and provenance curation."""

from __future__ import annotations

import copy
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PIPELINES = REPO / "pipelines"
sys.path.insert(0, str(PIPELINES))

import curate_identity as identity  # noqa: E402
import record_kind  # noqa: E402

FABLE_ACT = "agentic-coding-trajectory-factory"
FABLE_THALAMIC = "thalamic-trajectory-factory"
FABLE_FFPC = "failure-as-fuel-preference-cascade"
FABLE_BRIDGE = "neuromorphic-event-language-bridge"


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
            "long-horizon-coding-trajectories/batch-r08.jsonl",
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
                "long-horizon-coding-trajectories/batch.jsonl",
                1,
            )
        )
        self.assertEqual(result.action, "retained")
        self.assertEqual(result.mapping["record_kind"], "episode")
        self.assertEqual(result.mapping["path_id"], "long-horizon-coding-trajectories")
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
                "safety-calibration-cases/cases.jsonl",
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
                "multi-agent-coordination-transcripts/batch.jsonl",
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

    def test_eval_harness_is_explicit_pair_not_a_glob_rewrite(self):
        retain = identity.curate_record(
            source(
                episode("eval-harness-trajectory-factory"),
                "eval-harness-trajectories/batch.jsonl",
                1,
            )
        )
        self.assertEqual(retain.action, "retained")
        rewritten = identity.curate_record(
            source(
                episode("eval-harness-factory"),
                "eval-harness-trajectories/batch.jsonl",
                1,
            )
        )
        self.assertEqual(rewritten.action, "exclude")
        self.assertEqual(
            rewritten.mapping["reason_codes"],
            ["identity.factory_path_payload_mismatch"],
        )

    def test_grok_trajectory_preference_without_state_retains(self):
        result = identity.curate_record(
            source(
                grok_pref(),
                "tool-use-preference-pairs/batch.jsonl",
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
        self.assertEqual(len(payload["factories"]), 50)
        self.assertEqual(payload["lookup_key"], "path_id")
        for row in payload["factories"]:
            self.assertNotIn("training_ready", row)
            self.assertIsNone(row["publication_target"])
            self.assertEqual(row["training_ready_policy"], "never")
            self.assertTrue(row["identity_authoritative"])
        eval_row = next(
            item
            for item in payload["factories"]
            if item["path_id"] == "eval-harness-trajectories"
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
            if item["path_id"] == "tool-use-preference-pairs"
        )
        self.assertNotIn("curate_preferences", grok_pref_row["allowed_curation_lanes"])


if __name__ == "__main__":
    unittest.main()
