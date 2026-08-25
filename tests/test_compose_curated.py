#!/usr/bin/env python3
"""Tests for composing the five curation lanes into one curated destination."""

import copy
import hashlib
import io
import json
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "pipelines"))

import compose_curated  # noqa: E402
import curate_bridge  # noqa: E402
import curate_coding  # noqa: E402
import curate_preferences  # noqa: E402
import curate_rewards  # noqa: E402
import training_audit  # noqa: E402


def trajectory(action="noop", provenance="designed", domain="compose-test"):
    """A complete Thalamic trajectory body that clears the shape validator."""

    return {
        "state": {"sim_or_real": provenance, "domain": domain},
        "proposed_action": {"action": action, "decision_basis": "fixture"},
        "safety_decision": {"decision": "ACCEPT", "rationale": "bounded fixture"},
        "executed_action": {"action": action},
        "future_outcome": {"success": True},
        "reward_components": {"task_progress": 0.5, "safety": 0.5, "total": 1.0},
        "meta": {"tags": ["compose", "fixture"], "round": 1},
    }


def thalamic(tag):
    record = trajectory(domain=f"compose-{tag}")
    record["id"] = f"legacy-{tag}"
    record["meta"]["factory"] = "thalamic-trajectory-factory"
    return record


def spike(time_ms, index):
    return {
        "t_rel_ms": time_ms,
        "channel": f"ch{index}",
        "amplitude": 0.5,
        "neuron_id": index,
    }


def bridge_pair(*, unsorted=False):
    times = [3.0, 1.0, 2.0] if unsorted else [1.0, 2.0, 3.0]
    return {
        "id": "legacy-bridge-1",
        "language_view": {
            "summary": "three relay events",
            "trajectory": trajectory(
                action="relay", provenance="simulated", domain="bridge"
            ),
        },
        "spike_events": [spike(value, index) for index, value in enumerate(times)],
        "meta": {
            "factory": "neuromorphic-event-language-bridge",
            "tags": ["bridge"],
            "round": 1,
        },
    }


def preference_pair(*, pure=True):
    return {
        "id": "legacy-pref-pure" if pure else "legacy-pref-impure",
        "chosen": trajectory(action="noop", domain="pref"),
        "rejected": trajectory(action="noop" if pure else "other", domain="pref"),
        "critique": "chosen is safer",
        "meta": {
            "factory": "failure-as-fuel-preference-cascade",
            "tags": ["preference"],
            "round": 1,
        },
    }


def episode(tag="1"):
    return {
        "id": f"legacy-episode-{tag}",
        "goal": "fix the failing test",
        "steps": [
            {
                "thought": "hidden chain of thought",
                "plan": f"read failing test {tag}",
                "tool_call": {"name": "rg", "args": {"pattern": "fail"}},
                "observation": "one failing assertion",
            }
        ],
        "outcome": "test fixed",
        "reward": {"success": True},
        "meta": {
            "factory": "agentic-coding-trajectory-factory",
            "tags": ["coding"],
            "round": 1,
        },
    }


def trajectory_preference_pair():
    """A homogeneous episode pair satisfying the reviewed trajectory gate."""

    shared_step = {
        "n": 1,
        "decision_basis": "Inspect the shared failure.",
        "tool_call": {"name": "read", "args": {"path": "failing.py"}},
        "observation": "The same failing assertion is visible.",
    }

    def side(label, success):
        return {
            "steps": [
                copy.deepcopy(shared_step),
                {
                    "n": 2,
                    "decision_basis": f"Take the {label} branch.",
                    "tool_call": {
                        "name": "edit",
                        "args": {"path": "failing.py", "branch": label},
                    },
                    "observation": f"{label} outcome",
                },
            ],
            "outcome": f"{label} outcome",
            "reward": {"success": success},
        }

    return {
        "id": "trajectory-pref-1",
        "goal": "Fix the shared failing assertion",
        "chosen": side("fixed", True),
        "rejected": side("failed", False),
        "meta": {
            "factory": "tool-use-preference-factory",
            "round": 1,
        },
    }


def write_jsonl(path, records):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(record, ensure_ascii=False) + "\n" for record in records),
        encoding="utf-8",
    )


def build_source_run(root):
    """Write a small four-factory run that composes to a training-ready tree."""

    run = Path(root)
    write_jsonl(
        run / "thalamic-trajectory-factory" / "batch-r01.jsonl",
        [thalamic("a"), thalamic("b"), thalamic("c")],
    )
    write_jsonl(
        run / "neuromorphic-event-language-bridge" / "batch-r01.jsonl",
        [bridge_pair(unsorted=True)],
    )
    write_jsonl(
        run / "failure-as-fuel-preference-cascade" / "batch-r01.jsonl",
        [preference_pair(pure=True), preference_pair(pure=False)],
    )
    write_jsonl(
        run / "agentic-coding-trajectory-factory" / "batch-r01.jsonl",
        [episode("1"), episode("2")],
    )
    return run


def read_jsonl(path):
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


class ComposeCurated(unittest.TestCase):
    def test_composes_every_lane_into_a_training_ready_tree(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = build_source_run(root / "run")
            summary = compose_curated.compose_run(source, root / "curated")

            self.assertEqual(summary["counts"]["source_records"], 8)
            self.assertEqual(summary["counts"]["retained"], 7)
            self.assertEqual(summary["counts"]["excluded"], 1)
            self.assertEqual(summary["lane_order"], list(compose_curated.LANE_ORDER))
            self.assertEqual(
                summary["transforms"]["preferences"]["trajectory"]["implementation"],
                (
                    "reviewed_module"
                    if compose_curated.curate_trajectory_preferences is not None
                    else "compatible_core"
                ),
            )
            self.assertTrue(summary["audit"]["training_ready"], summary["audit"]["blockers"])
            self.assertEqual(summary["audit"]["blockers"], [])
            self.assertEqual(summary["audit"]["records"], 7)

            records_dir = root / "curated" / compose_curated.RECORDS_DIRNAME
            report = training_audit.audit_run(records_dir)
            self.assertTrue(report["training_ready"], report["blockers"])
            self.assertEqual(report["identity"]["coverage_pct"], 100.0)
            self.assertEqual(report["preferences"]["context_purity_pct"], 100.0)
            self.assertEqual(report["episodes"]["hidden_thought_fields"], 0)

            # Identity ran first: every retained record carries a canonical ID.
            for path in records_dir.rglob("*.jsonl"):
                for record in read_jsonl(path):
                    self.assertTrue(record["id"].startswith("sfcur-"), record["id"])

            # Bridge repaired the out-of-order stream in place.
            bridge = read_jsonl(
                records_dir / "neuromorphic-event-language-bridge" / "batch-r01.jsonl"
            )[0]
            self.assertEqual(
                [event["t_rel_ms"] for event in bridge["spike_events"]], [1.0, 2.0, 3.0]
            )

            # Coding stripped the hidden thought and grounded a decision basis.
            episodes = read_jsonl(
                records_dir / "agentic-coding-trajectory-factory" / "batch-r01.jsonl"
            )
            self.assertEqual(len(episodes), 2)
            for record in episodes:
                self.assertNotIn("thought", record["steps"][0])
                self.assertTrue(record["steps"][0]["decision_basis"].strip())

            # Rewards annotated the records that actually carry reward payloads.
            thalamic_records = read_jsonl(
                records_dir / "thalamic-trajectory-factory" / "batch-r01.jsonl"
            )
            for record in thalamic_records:
                annotation = record["reward_training"]
                self.assertEqual(annotation["ontology_version"], "reward-ontology-v1")
                self.assertTrue(annotation["source_sidecar_id"])

            # The impure preference pair is the only exclusion.
            self.assertEqual(
                sum(summary["exclusions"].values()), summary["counts"]["excluded"]
            )
            self.assertIn(
                "PROPOSED_ACTION_CONTEXT_DIVERGES", summary["exclusions"]
            )

    def test_manifest_carries_hashes_transform_versions_and_exclusions(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = build_source_run(root / "run")
            summary = compose_curated.compose_run(source, root / "curated")

            manifest_path = root / "curated" / summary["manifest"]["path"]
            entries = read_jsonl(manifest_path)
            self.assertEqual(len(entries), summary["manifest"]["entries"])
            self.assertEqual(len(entries), summary["counts"]["source_records"])
            self.assertEqual(
                summary["manifest"]["sha256"],
                hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
            )

            sidecars = read_jsonl(root / "curated" / summary["reward_sidecars"]["path"])
            sidecar_ids = {item["sidecar_id"] for item in sidecars}
            self.assertEqual(len(sidecars), summary["counts"]["reward_sidecars"])

            retained = [item for item in entries if item["action"] == "retained"]
            excluded = [item for item in entries if item["action"] == "excluded"]
            self.assertEqual(len(retained), summary["counts"]["retained"])
            self.assertEqual(len(excluded), summary["counts"]["excluded"])

            for entry in entries:
                self.assertEqual(entry["compose_version"], compose_curated.COMPOSE_VERSION)
                self.assertRegex(entry["source_sha256"], r"^[0-9a-f]{64}$")
                self.assertRegex(entry["source_file_sha256"], r"^[0-9a-f]{64}$")
                lanes = [stage["lane"] for stage in entry["stages"]]
                self.assertEqual(lanes, list(compose_curated.LANE_ORDER)[: len(lanes)])
                for stage in entry["stages"]:
                    self.assertTrue(stage["transform_version"])
                    self.assertTrue(stage["transform_name"])

            # Retained entries point at the exact emitted line and its digest.
            for entry in retained:
                emitted = (root / "curated" / entry["output_path"]).read_text(
                    encoding="utf-8"
                ).splitlines()[entry["output_line"] - 1]
                self.assertEqual(
                    entry["output_sha256"],
                    hashlib.sha256(emitted.encode("utf-8")).hexdigest(),
                )
                self.assertEqual(json.loads(emitted)["id"], entry["output_id"])
                if "reward_sidecar_id" in entry:
                    self.assertIn(entry["reward_sidecar_id"], sidecar_ids)

            # The exclusion keeps its machine-readable reason and no output.
            self.assertEqual(len(excluded), 1)
            self.assertIsNone(excluded[0]["output_path"])
            self.assertIn(
                "PROPOSED_ACTION_CONTEXT_DIVERGES", excluded[0]["reason_codes"]
            )

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
                curate_bridge.REASON_NOT_BRIDGE
                in bridge_decision.manifest["reason_codes"]
            )
            self.assertEqual(
                compose_curated.is_bridge_record(sample), not rejected_as_bridge, sample
            )
            _curated, coding_manifest = curate_coding.curate_episode(sample)
            rejected_as_episode = coding_manifest["reason_codes"] == [
                curate_coding.REASON_STEPS_NOT_ARRAY
            ]
            self.assertEqual(
                compose_curated.is_episode_record(sample),
                not rejected_as_episode,
                sample,
            )

    def test_episode_preference_pairs_are_retained_and_mixed_families_are_explicit(self):
        pair = trajectory_preference_pair()
        decision = compose_curated.compose_record(
            pair,
            source_path="tool-use-preference-factory/batch-r01.jsonl",
            source_line=1,
            source_sha256="0" * 64,
        )

        self.assertEqual(decision.action, compose_curated.ACTION_RETAINED)
        preference_stage = next(
            stage for stage in decision.stages if stage["lane"] == "preferences"
        )
        self.assertEqual(preference_stage["side_kinds"], ["episode", "episode"])
        self.assertEqual(
            preference_stage["classification"], "trajectory_pair_gate_passed"
        )
        self.assertEqual(
            preference_stage["implementation"],
            (
                "reviewed_module"
                if compose_curated.curate_trajectory_preferences is not None
                else "compatible_core"
            ),
        )
        self.assertIn(
            compose_curated.REASON_TRAJECTORY_GATE_PASSED,
            preference_stage["reason_codes"],
        )

        mixed = trajectory_preference_pair()
        mixed["rejected"] = trajectory(action="reject", domain="mixed")
        rejected = compose_curated.compose_record(
            mixed,
            source_path="tool-use-preference-factory/batch-r01.jsonl",
            source_line=2,
            source_sha256="1" * 64,
        )
        self.assertEqual(rejected.action, compose_curated.ACTION_EXCLUDED)
        self.assertEqual(
            rejected.reason_codes,
            (compose_curated.REASON_MIXED_PREFERENCE_FAMILIES,),
        )
        self.assertEqual(
            rejected.stages[0]["detail"]["preference_side_kinds"],
            ["episode", "thalamic"],
        )

        malformed = trajectory_preference_pair()
        malformed.pop("rejected")
        malformed_decision = compose_curated.compose_record(
            malformed,
            source_path="tool-use-preference-factory/batch-r01.jsonl",
            source_line=3,
            source_sha256="2" * 64,
        )
        self.assertEqual(malformed_decision.action, compose_curated.ACTION_EXCLUDED)
        self.assertNotIn(
            compose_curated.REASON_MIXED_PREFERENCE_FAMILIES,
            malformed_decision.reason_codes,
        )
        self.assertEqual(
            malformed_decision.stages[0]["detail"]["preference_side_kinds"],
            ["episode", "unknown"],
        )

        whitespace = trajectory_preference_pair()
        whitespace["goal"] = "Fix shared assertion"
        whitespace["chosen"]["goal"] = " Fix  shared assertion "
        whitespace["rejected"]["goal"] = "Fix\tshared assertion"
        repaired = compose_curated.compose_record(
            whitespace,
            source_path="tool-use-preference-factory/batch-r01.jsonl",
            source_line=4,
            source_sha256="3" * 64,
        )
        preference_stage = next(
            stage for stage in repaired.stages if stage["lane"] == "preferences"
        )
        self.assertEqual(preference_stage["lane_action"], "repaired")
        self.assertIn(
            compose_curated.REASON_TRAJECTORY_GOAL_NORMALIZED,
            preference_stage["reason_codes"],
        )
        self.assertEqual(repaired.record["goal"], "Fix shared assertion")
        self.assertEqual(repaired.record["chosen"]["goal"], "Fix shared assertion")
        self.assertEqual(repaired.record["rejected"]["goal"], "Fix shared assertion")

    def test_episode_preference_sides_migrate_legacy_thought_before_validation(self):
        pair = trajectory_preference_pair()
        for side_name in ("chosen", "rejected"):
            for index, step in enumerate(pair[side_name]["steps"], 1):
                step.pop("decision_basis")
                step["thought"] = f"hidden {side_name} reasoning {index}"
        source = copy.deepcopy(pair)

        decision = compose_curated.compose_record(
            pair,
            source_path="tool-use-preference-factory/batch-r01.jsonl",
            source_line=1,
            source_sha256="6" * 64,
        )

        self.assertEqual(decision.action, compose_curated.ACTION_RETAINED)
        self.assertEqual(pair, source)
        for side_name in ("chosen", "rejected"):
            for step in decision.record[side_name]["steps"]:
                self.assertNotIn("thought", step)
                self.assertTrue(step["decision_basis"].startswith("Observation:"))
        stage = next(item for item in decision.stages if item["lane"] == "preferences")
        self.assertTrue(stage["side_curation_changed"])
        self.assertEqual(stage["lane_action"], "repaired")
        self.assertIn(curate_coding.REASON_THOUGHT_REMOVED, stage["reason_codes"])
        self.assertIn(curate_coding.REASON_STEPS_MIGRATED, stage["reason_codes"])
        for side_name in ("chosen", "rejected"):
            self.assertEqual(stage["side_curation"][side_name]["action"], "modified")
            self.assertGreater(
                stage["side_curation"][side_name]["thought_fields_removed"], 0
            )

    def test_same_state_schema_precedes_episode_fields_and_matches_pr93(self):
        impure = trajectory_preference_pair()
        impure["chosen"].update(
            {
                "state": {"tick": 1},
                "proposed_action": {"action": "chosen"},
            }
        )
        impure["rejected"].update(
            {
                "state": {"tick": 2},
                "proposed_action": {"action": "rejected"},
            }
        )
        direct = curate_preferences.curate_preference_record(impure)
        decision = compose_curated.compose_record(
            impure,
            source_path="tool-use-preference-factory/batch-r01.jsonl",
            source_line=1,
            source_sha256="4" * 64,
        )

        self.assertIsNone(direct.record)
        self.assertEqual(decision.action, compose_curated.ACTION_EXCLUDED)
        self.assertEqual(decision.reason_codes, direct.reason_codes)
        preference_stage = next(
            stage for stage in decision.stages if stage["lane"] == "preferences"
        )
        self.assertEqual(preference_stage["schema"], "same_state_pair")
        self.assertEqual(
            preference_stage["transform_name"], curate_preferences.TRANSFORM_NAME
        )
        self.assertEqual(
            preference_stage["classification"], direct.classification
        )
        self.assertNotIn("implementation", preference_stage)

        pure = copy.deepcopy(impure)
        pure["rejected"]["state"] = copy.deepcopy(pure["chosen"]["state"])
        pure["rejected"]["proposed_action"] = copy.deepcopy(
            pure["chosen"]["proposed_action"]
        )
        retained = compose_curated.compose_record(
            pure,
            source_path="tool-use-preference-factory/batch-r01.jsonl",
            source_line=2,
            source_sha256="5" * 64,
        )
        retained_stage = next(
            stage for stage in retained.stages if stage["lane"] == "preferences"
        )
        direct_pure = curate_preferences.curate_preference_record(pure)
        self.assertEqual(retained.action, compose_curated.ACTION_RETAINED)
        self.assertEqual(retained_stage["schema"], "same_state_pair")
        self.assertEqual(
            retained_stage["classification"], direct_pure.classification
        )

    def test_reviewed_trajectory_module_is_used_when_the_stack_provides_it(self):
        pair = trajectory_preference_pair()

        class ReviewedModule:
            TRANSFORM_NAME = "reviewed-trajectory-contract"
            TRANSFORM_VERSION = "reviewed-v1"

            @staticmethod
            def curate_trajectory_pair(record):
                return compose_curated._TrajectoryPreferenceDecision(
                    action="retained",
                    classification="reviewed_contract_called",
                    reason_codes=(compose_curated.REASON_TRAJECTORY_GATE_PASSED,),
                    record=copy.deepcopy(record),
                    shared_goal=True,
                    overlap={"shared_steps": 1},
                )

        with mock.patch.object(
            compose_curated, "curate_trajectory_preferences", ReviewedModule
        ):
            decision = compose_curated.compose_record(
                pair,
                source_path="tool-use-preference-factory/batch-r01.jsonl",
                source_line=1,
                source_sha256="0" * 64,
            )

        stage = next(item for item in decision.stages if item["lane"] == "preferences")
        self.assertEqual(stage["transform_name"], ReviewedModule.TRANSFORM_NAME)
        self.assertEqual(stage["transform_version"], ReviewedModule.TRANSFORM_VERSION)
        self.assertEqual(stage["implementation"], "reviewed_module")
        self.assertEqual(stage["classification"], "reviewed_contract_called")

    def test_rewardless_record_adopts_the_curators_annotation_stripped_result(self):
        stale, _sidecar = curate_rewards.curate_record({"payload": "now removed"})
        record = {
            "id": "legacy-multi-agent",
            "transcript": [{"agent": "a", "message": "coordinate"}],
            "agents": ["a", "b"],
            "meta": {"factory": "multi-agent-coordination-factory", "round": 1},
            "reward_training": stale["reward_training"],
        }

        decision = compose_curated.compose_record(
            record,
            source_path="multi-agent-coordination-factory/batch-r01.jsonl",
            source_line=1,
            source_sha256="0" * 64,
        )

        self.assertEqual(decision.action, compose_curated.ACTION_RETAINED)
        self.assertNotIn(curate_rewards.ANNOTATION_FIELD, decision.record)
        self.assertIsNone(decision.reward_sidecar)
        rewards = next(stage for stage in decision.stages if stage["lane"] == "rewards")
        self.assertEqual(rewards["action"], compose_curated.ACTION_NOT_APPLICABLE)
        self.assertEqual(rewards["source_reward_count"], 0)

    def test_reward_sidecar_restores_the_final_post_coding_record(self):
        decision = compose_curated.compose_record(
            episode("final-hash"),
            source_path="agentic-coding-trajectory-factory/batch-r01.jsonl",
            source_line=1,
            source_sha256="0" * 64,
        )

        self.assertEqual(decision.stages[-1]["lane"], "rewards")
        self.assertNotIn("thought", decision.record["steps"][0])
        expected = copy.deepcopy(decision.record)
        expected.pop(curate_rewards.ANNOTATION_FIELD)
        self.assertEqual(
            curate_rewards.restore_source_record(
                decision.record, decision.reward_sidecar
            ),
            expected,
        )

    def test_source_jsonl_uses_lf_only_and_preserves_unicode_separators(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root / "run" / "thalamic-trajectory-factory"
            source.mkdir(parents=True)
            first = thalamic("unicode-separators")
            first["state"]["domain"] = "line\u2028separator\u2029paragraph"
            write_jsonl(source / "batch-r01.jsonl", [first, thalamic("plain")])

            summary = compose_curated.compose_run(root / "run", root / "curated")
            output = (
                root
                / "curated"
                / compose_curated.RECORDS_DIRNAME
                / "thalamic-trajectory-factory"
                / "batch-r01.jsonl"
            ).read_text(encoding="utf-8")
            records = [json.loads(line) for line in output.split("\n") if line]

            self.assertEqual(summary["counts"]["source_records"], 2)
            self.assertEqual(summary["audit"]["records"], 2)
            self.assertTrue(
                summary["audit"]["training_ready"], summary["audit"]["blockers"]
            )
            self.assertEqual(len(records), 2)
            self.assertEqual(
                records[0]["state"]["domain"], first["state"]["domain"]
            )

    def test_semantic_source_duplicates_are_excluded_before_identity(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root / "run" / "thalamic-trajectory-factory"
            source.mkdir(parents=True)
            record = thalamic("semantic-duplicate")
            first = json.dumps(record, ensure_ascii=False)
            duplicate = json.dumps(
                record,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            )
            (source / "batch-r01.jsonl").write_text(
                first + "\n" + duplicate + "\n", encoding="utf-8"
            )

            summary = compose_curated.compose_run(root / "run", root / "curated")
            manifest = read_jsonl(root / "curated" / summary["manifest"]["path"])

            self.assertEqual(summary["counts"]["source_records"], 2)
            self.assertEqual(summary["counts"]["retained"], 1)
            self.assertEqual(summary["counts"]["excluded"], 1)
            self.assertEqual(
                summary["exclusions"],
                {compose_curated.REASON_DUPLICATE_SOURCE_RECORD: 1},
            )
            self.assertEqual(
                manifest[1]["reason_codes"],
                [compose_curated.REASON_DUPLICATE_SOURCE_RECORD],
            )
            duplicate_stage = manifest[1]["stages"][0]
            self.assertEqual(duplicate_stage["lane"], "source")
            self.assertEqual(
                duplicate_stage["detail"]["first_source_path"],
                "thalamic-trajectory-factory/batch-r01.jsonl",
            )
            self.assertEqual(duplicate_stage["detail"]["first_source_line"], 1)
            output = read_jsonl(root / "curated" / manifest[0]["output_path"])
            self.assertEqual(len(output), 1)

    def test_composition_rejects_source_symlink_and_hardlink_aliases(self):
        for mutation in (
            "source_root_symlink",
            "directory_symlink",
            "file_symlink",
            "file_hardlink",
        ):
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as td:
                root = Path(td)
                source = build_source_run(root / "run")
                source_argument = source
                if mutation == "source_root_symlink":
                    source_argument = root / "source-alias"
                    source_argument.symlink_to(source, target_is_directory=True)
                elif mutation == "directory_symlink":
                    factory = source / "thalamic-trajectory-factory"
                    target = root / "outside-factory"
                    factory.replace(target)
                    factory.symlink_to(target, target_is_directory=True)
                else:
                    path = source / "thalamic-trajectory-factory" / "batch-r01.jsonl"
                    target = root / "outside-source.jsonl"
                    path.replace(target)
                    if mutation == "file_symlink":
                        path.symlink_to(target)
                    else:
                        os.link(target, path)

                with self.assertRaisesRegex(
                    compose_curated.ComposeError, "symlink|hard-link"
                ):
                    compose_curated.compose_run(source_argument, root / "curated")
                self.assertFalse((root / "curated").exists())

    def test_composition_rejects_a_source_file_changed_during_pinned_read(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root / "run"
            target = source / "thalamic-trajectory-factory" / "batch-r01.jsonl"
            write_jsonl(target, [thalamic("pinned-read")])
            original = target.read_bytes()
            real_read = compose_curated.os.read
            mutated = False

            def read_then_mutate(descriptor, size):
                nonlocal mutated
                chunk = real_read(descriptor, size)
                if chunk and not mutated:
                    mutated = True
                    target.write_bytes(original + b" ")
                return chunk

            with mock.patch.object(
                compose_curated.os, "read", side_effect=read_then_mutate
            ):
                with self.assertRaisesRegex(
                    compose_curated.ComposeError, "identity changed while reading"
                ):
                    compose_curated.compose_run(source, root / "curated")
            self.assertFalse((root / "curated").exists())

    def test_unsupported_and_unparseable_lines_are_excluded_with_reasons(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root / "run" / "thalamic-trajectory-factory"
            source.mkdir(parents=True)
            (source / "batch-r01.jsonl").write_text(
                json.dumps(thalamic("keep"))
                + "\n"
                + "{not json\n"
                + '{"nan": NaN}\n'
                + json.dumps({"unknown": "shape"})
                + "\n"
                + "\n",
                encoding="utf-8",
            )
            summary = compose_curated.compose_run(root / "run", root / "curated")

            self.assertEqual(summary["counts"]["source_records"], 4)
            self.assertEqual(summary["counts"]["blank_lines"], 1)
            self.assertEqual(summary["counts"]["retained"], 1)
            self.assertEqual(summary["counts"]["excluded"], 3)
            self.assertEqual(
                summary["exclusions"],
                {
                    compose_curated.REASON_INVALID_JSON: 2,
                    "identity.unsupported_record_shape": 1,
                },
            )

    def test_empty_composition_is_never_training_ready(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root / "run" / "thalamic-trajectory-factory"
            source.mkdir(parents=True)
            (source / "batch-r01.jsonl").write_text(
                json.dumps({"unknown": "shape"}) + "\n", encoding="utf-8"
            )
            summary = compose_curated.compose_run(root / "run", root / "curated")

            self.assertEqual(summary["counts"]["retained"], 0)
            self.assertFalse(summary["audit"]["training_ready"])
            self.assertEqual(
                summary["audit"]["blockers"], [compose_curated.REASON_EMPTY_CORPUS]
            )

    def test_composition_is_deterministic_and_leaves_the_source_untouched(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = build_source_run(root / "run")
            before = {
                path: path.read_bytes() for path in sorted(source.rglob("*.jsonl"))
            }

            first = compose_curated.compose_run(source, root / "curated-a")
            second = compose_curated.compose_run(source, root / "curated-b")

            self.assertEqual(first["manifest"]["sha256"], second["manifest"]["sha256"])
            self.assertEqual(
                first["reward_sidecars"]["sha256"], second["reward_sidecars"]["sha256"]
            )
            self.assertEqual(
                [item["sha256"] for item in first["outputs"]],
                [item["sha256"] for item in second["outputs"]],
            )
            self.assertEqual(first["counts"], second["counts"])
            self.assertEqual(
                {path: path.read_bytes() for path in sorted(source.rglob("*.jsonl"))},
                before,
            )

    def test_refuses_unsafe_destinations(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = build_source_run(root / "run")
            compose_curated.compose_run(source, root / "curated")

            with self.assertRaises(compose_curated.ComposeError):
                compose_curated.compose_run(source, root / "curated")
            with self.assertRaises(compose_curated.ComposeError):
                compose_curated.compose_run(source, source / "nested")
            with self.assertRaises(compose_curated.ComposeError):
                compose_curated.compose_run(source, source)
            with self.assertRaises(compose_curated.ComposeError):
                compose_curated.compose_run(source, root / "missing-parent" / "dest")
            with self.assertRaises(compose_curated.ComposeError):
                compose_curated.compose_run(root / "absent-run", root / "other")

            raw = root / "outputs" / "raw"
            raw.mkdir(parents=True)
            safe = root / "safe"
            safe.mkdir()
            lexical_alias = raw / ".." / ".." / "safe" / "lexical-curated"
            with self.assertRaisesRegex(
                compose_curated.ComposeError, "immutable raw"
            ):
                compose_curated.compose_run(source, lexical_alias)
            self.assertFalse((safe / "lexical-curated").exists())

    def test_a_failed_composition_removes_the_new_destination(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = build_source_run(root / "run")
            destination = root / "curated"

            real_write = compose_curated._write_new_text

            def fail_on_manifest(path, text):
                if path.name == compose_curated.MANIFEST_FILENAME:
                    raise OSError("simulated manifest write failure")
                return real_write(path, text)

            with mock.patch.object(
                compose_curated, "_write_new_text", side_effect=fail_on_manifest
            ):
                with self.assertRaises(OSError):
                    compose_curated.compose_run(source, destination)
            self.assertFalse(destination.exists())

    def test_cli_reports_strict_blockers_and_refuses_existing_destinations(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = build_source_run(root / "run")

            stdout = io.StringIO()
            with redirect_stdout(stdout):
                status = compose_curated.main(
                    ["--strict", str(source), str(root / "curated")]
                )
            self.assertEqual(status, 0)
            self.assertTrue(json.loads(stdout.getvalue())["audit"]["training_ready"])

            stderr = io.StringIO()
            with redirect_stdout(io.StringIO()), redirect_stderr(stderr):
                status = compose_curated.main([str(source), str(root / "curated")])
            self.assertEqual(status, 2)
            self.assertIn("refusing to overwrite", stderr.getvalue())

            blocked = root / "blocked-run" / "thalamic-trajectory-factory"
            blocked.mkdir(parents=True)
            (blocked / "batch-r01.jsonl").write_text(
                json.dumps({"unknown": "shape"}) + "\n", encoding="utf-8"
            )
            stderr = io.StringIO()
            with redirect_stdout(io.StringIO()), redirect_stderr(stderr):
                status = compose_curated.main(
                    ["--strict", str(root / "blocked-run"), str(root / "curated-blocked")]
                )
            self.assertEqual(status, 1)
            self.assertIn(compose_curated.REASON_EMPTY_CORPUS, stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
