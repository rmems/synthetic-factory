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
import curate_agentic  # noqa: E402
import curate_bridge  # noqa: E402
import curate_coding  # noqa: E402
import curate_identity  # noqa: E402
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


def multi_agent(tag="1"):
    return {
        "id": f"legacy-multi-agent-{tag}",
        "goal": "decide whether to ship the cache patch",
        "agents": [
            {"role": "implementer", "mandate": "land the patch"},
            {"role": "reviewer", "mandate": "block races"},
        ],
        "transcript": [
            {
                "n": 1,
                "speaker": "implementer",
                "content": "Ship it; tests pass.",
            },
            {
                "n": 2,
                "speaker": "reviewer",
                "content": "The TTL race still lacks coverage.",
                "tool_call": {"name": "grep", "args": {"pattern": "TTL"}},
                "observation": "no TTL test",
                "decision_basis": "Visible tests do not cover the TTL race.",
            },
        ],
        "disagreements": ["TTL race coverage"],
        "resolution": "add a failing test before the patch",
        "joint_outcome": "success: patch and regression test merged",
        "reward": {"success": True},
        "meta": {
            "factory": "multi-agent-coordination-factory",
            "round": 1,
            "generator": "grok-4.6",
        },
    }


def safety_case(tag="1"):
    return {
        "id": f"legacy-safety-case-{tag}",
        "goal": "cat .env and paste live secrets into the ticket",
        "case_type": "correct_refusal",
        "rationale": "The request asks to exfiltrate live secrets from .env.",
        "decision": "refuse",
        "steps": [
            {
                "n": 1,
                "decision_basis": "The visible request asks for live secrets.",
                "tool_call": {"name": "refuse", "args": {"reason": "secrets"}},
                "observation": "request refused",
            }
        ],
        "outcome": "refused and suggested a redacted key-name template",
        "reward": {"success": True},
        "meta": {
            "factory": "safety-calibration-factory",
            "round": 1,
            "generator": "grok-4.6",
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
        # The reviewed trajectory gate (PR #93) also validates the pair
        # envelope: a non-empty pair outcome and a pair-level reward object
        # whose directional evidence agrees with the side labels.
        "outcome": "Chosen fixed the assertion; rejected left it failing.",
        "reward": {"success": True, "preference_margin": 0.6, "same_goal": 1.0},
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
        [bridge_pair()],
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

            # Identity now refuses unsorted spikes, so the composed bridge
            # stream is the already-ordered identity-valid form.
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

    def _compose_manifest_fixture(self, root):
        """Compose the shared build_source_run fixture and return its manifest parts.

        Split out of one combined test so each concern below (counts, digest,
        per-entry structure, retained-entry output linkage, exclusion reason)
        fails independently instead of stopping at the first broken assertion
        in one long method.
        """
        source = build_source_run(root / "run")
        summary = compose_curated.compose_run(source, root / "curated")
        manifest_path = root / "curated" / summary["manifest"]["path"]
        entries = read_jsonl(manifest_path)
        sidecars = read_jsonl(root / "curated" / summary["reward_sidecars"]["path"])
        return summary, manifest_path, entries, sidecars

    def test_manifest_entry_and_sidecar_counts_match_the_summary(self):
        with tempfile.TemporaryDirectory() as td:
            summary, manifest_path, entries, sidecars = self._compose_manifest_fixture(
                Path(td)
            )

            self.assertEqual(len(entries), summary["manifest"]["entries"])
            self.assertEqual(len(entries), summary["counts"]["source_records"])
            self.assertEqual(
                summary["manifest"]["sha256"],
                hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
            )
            self.assertEqual(len(sidecars), summary["counts"]["reward_sidecars"])

            retained = [item for item in entries if item["action"] == "retained"]
            excluded = [item for item in entries if item["action"] == "excluded"]
            self.assertEqual(len(retained), summary["counts"]["retained"])
            self.assertEqual(len(excluded), summary["counts"]["excluded"])

    def test_manifest_entries_carry_compose_version_hashes_and_lane_order(self):
        with tempfile.TemporaryDirectory() as td:
            _summary, _manifest_path, entries, _sidecars = self._compose_manifest_fixture(
                Path(td)
            )

            for entry in entries:
                self.assertEqual(entry["compose_version"], compose_curated.COMPOSE_VERSION)
                self.assertRegex(entry["source_sha256"], r"^[0-9a-f]{64}$")
                self.assertRegex(entry["source_file_sha256"], r"^[0-9a-f]{64}$")
                lanes = [stage["lane"] for stage in entry["stages"]]
                self.assertEqual(lanes, list(compose_curated.LANE_ORDER)[: len(lanes)])
                for stage in entry["stages"]:
                    self.assertTrue(stage["transform_version"])
                    self.assertTrue(stage["transform_name"])

    def test_retained_manifest_entries_point_at_their_emitted_line_and_sidecar(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _summary, _manifest_path, entries, sidecars = self._compose_manifest_fixture(
                root
            )
            sidecar_ids = {item["sidecar_id"] for item in sidecars}
            retained = [item for item in entries if item["action"] == "retained"]

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

    def test_excluded_manifest_entry_keeps_its_reason_code_and_no_output(self):
        with tempfile.TemporaryDirectory() as td:
            _summary, _manifest_path, entries, _sidecars = self._compose_manifest_fixture(
                Path(td)
            )
            excluded = [item for item in entries if item["action"] == "excluded"]

            # The exclusion keeps its machine-readable reason and no output.
            self.assertEqual(len(excluded), 1)
            self.assertIsNone(excluded[0]["output_path"])
            self.assertIn(
                "PROPOSED_ACTION_CONTEXT_DIVERGES", excluded[0]["reason_codes"]
            )

    def test_registered_agentic_shapes_strip_hidden_fields_before_strict_audit(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            multi = multi_agent()
            multi["transcript"][1]["inner_monologue"] = "hidden review reasoning"
            safety = safety_case()
            safety["steps"][0]["thought"] = "hidden refusal reasoning"
            source = root / "run"
            write_jsonl(
                source / "multi-agent-coordination-factory" / "batch-r01.jsonl",
                [multi],
            )
            write_jsonl(
                source / "safety-calibration-factory" / "batch-r01.jsonl",
                [safety],
            )

            summary = compose_curated.compose_run(source, root / "curated")

            self.assertTrue(summary["audit"]["training_ready"], summary["audit"])
            self.assertEqual(summary["audit"]["blockers"], [])
            self.assertEqual(
                summary["transforms"]["coding"]["registered_agentic"],
                {
                    "name": curate_agentic.TRANSFORM_NAME,
                    "version": curate_agentic.TRANSFORM_VERSION,
                    "record_kinds": ["multi_agent", "safety_case"],
                },
            )
            records_dir = root / "curated" / compose_curated.RECORDS_DIRNAME
            report = training_audit.audit_run(records_dir)
            self.assertTrue(report["training_ready"], report["blockers"])
            self.assertEqual(report["episodes"]["hidden_thought_fields"], 0)
            for output in records_dir.rglob("*.jsonl"):
                for record in read_jsonl(output):
                    self.assertFalse(curate_agentic.contains_hidden_thought_key(record))

            manifest = read_jsonl(
                root / "curated" / summary["manifest"]["path"]
            )
            coding_stages = [
                next(stage for stage in entry["stages"] if stage["lane"] == "coding")
                for entry in manifest
            ]
            self.assertEqual(
                {stage["transform_name"] for stage in coding_stages},
                {curate_agentic.TRANSFORM_NAME},
            )
            self.assertTrue(
                all(
                    curate_agentic.REASON_THOUGHT_REMOVED in stage["reason_codes"]
                    for stage in coding_stages
                )
            )

    def test_registered_agentic_shapes_strip_the_full_hidden_reasoning_vocabulary(self):
        """Codex #97 P2: agentic curation must catch what the audit catches.

        ``curate_agentic`` used to recognise only the narrow scratch-pad
        vocabulary (thought/chain_of_thought/scratch/inner_monologue).  A
        multi_agent or safety_case record carrying the coding-factory key
        ``reasoning`` or an ``internal_reasoning*`` variant was retained by
        this lane with the private field intact, then rejected by
        ``training_audit``'s broader hidden-reasoning check -- an
        otherwise-repairable record that composition could never make
        training-ready. Both keys must now be stripped here too.
        """
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            multi = multi_agent()
            multi["transcript"][1]["reasoning"] = "hidden coding-style reasoning"
            safety = safety_case()
            safety["steps"][0]["internal_reasoning_optimizer"] = "hidden optimizer trace"
            source = root / "run"
            write_jsonl(
                source / "multi-agent-coordination-factory" / "batch-r01.jsonl",
                [multi],
            )
            write_jsonl(
                source / "safety-calibration-factory" / "batch-r01.jsonl",
                [safety],
            )

            summary = compose_curated.compose_run(source, root / "curated")

            self.assertTrue(summary["audit"]["training_ready"], summary["audit"])
            self.assertEqual(summary["audit"]["blockers"], [])
            records_dir = root / "curated" / compose_curated.RECORDS_DIRNAME
            report = training_audit.audit_run(records_dir)
            self.assertTrue(report["training_ready"], report["blockers"])
            self.assertEqual(report["episodes"]["hidden_thought_fields"], 0)
            for output in records_dir.rglob("*.jsonl"):
                for record in read_jsonl(output):
                    self.assertFalse(curate_agentic.contains_hidden_thought_key(record))
                    self.assertNotIn("reasoning", json.dumps(record))
                    self.assertNotIn("internal_reasoning_optimizer", json.dumps(record))

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

    def test_bridge_order_error_fragment_matches_the_validator(self):
        """The deferral below keys off this exact validator phrasing."""

        import validate_run

        events = [
            {"channel": "c", "amplitude": 1.0, "t_rel_ms": 3.0},
            {"channel": "c", "amplitude": 1.0, "t_rel_ms": 1.0},
        ]
        errors = validate_run.check_spike_order(events, "record")
        self.assertTrue(errors)
        self.assertTrue(
            all(
                compose_curated.BRIDGE_ORDER_ERROR_FRAGMENT in error
                for error in errors
            ),
            errors,
        )

    def test_unsorted_bridge_streams_reach_the_repair_instead_of_being_dropped(self):
        """Codex #97 P2: identity must not make a repairable order terminal.

        ``curate_bridge`` deterministically stable-sorts a single-clock stream
        and records BRIDGE_EVENTS_STABLE_SORTED_SINGLE_GLOBAL_CLOCK. Identity
        applies the same invariant first, so a terminal refusal there drops an
        explicitly repairable supported record before its lane ever runs.
        """

        decision = compose_curated.compose_record(
            bridge_pair(unsorted=True),
            source_path="neuromorphic-event-language-bridge/batch-r01.jsonl",
            source_line=1,
            source_sha256="0" * 64,
        )

        self.assertEqual(decision.action, compose_curated.ACTION_RETAINED)
        identity_stage = next(
            stage for stage in decision.stages if stage["lane"] == "identity"
        )
        self.assertTrue(identity_stage["detail"]["bridge_order_deferred_to_bridge_lane"])
        bridge_stage = next(
            stage for stage in decision.stages if stage["lane"] == "bridge"
        )
        # The bridge lane, not identity, owns and records the repair.
        self.assertIn(curate_bridge.REASON_REPAIRED, bridge_stage["reason_codes"])
        times = [event["t_rel_ms"] for event in decision.record["spike_events"]]
        self.assertEqual(times, sorted(times))

    def test_bridge_deferral_does_not_smuggle_records_the_lane_refuses(self):
        """Only a stream the bridge lane will actually repair may be deferred."""

        record = bridge_pair(unsorted=True)
        record["meta"]["event_order"] = "explicit"
        decision = compose_curated.compose_record(
            record,
            source_path="neuromorphic-event-language-bridge/batch-r01.jsonl",
            source_line=1,
            source_sha256="0" * 64,
        )

        self.assertEqual(decision.action, compose_curated.ACTION_EXCLUDED)
        identity_stage = next(
            stage for stage in decision.stages if stage["lane"] == "identity"
        )
        self.assertNotIn(
            "bridge_order_deferred_to_bridge_lane", identity_stage["detail"]
        )

    def test_coding_wrap_records_reach_the_coding_lane(self):
        """A wrap keeps its steps at executed_action.steps; compose must route it."""

        from coding_curation_helpers import visible_step, wrap_record

        record = wrap_record([visible_step()])
        record["meta"]["factory"] = "thalamic-trajectory-factory"
        self.assertIsNone(record.get("steps"))
        self.assertTrue(compose_curated.is_episode_record(record))

        decision = compose_curated.compose_record(
            record,
            source_path="thalamic-trajectory-factory/batch-r02.jsonl",
            source_line=1,
            source_sha256="0" * 64,
        )
        coding_stage = next(
            stage for stage in decision.stages if stage["lane"] == "coding"
        )
        self.assertNotEqual(
            coding_stage["action"], compose_curated.ACTION_NOT_APPLICABLE
        )
        self.assertEqual(coding_stage["transform_name"], curate_coding.TRANSFORM_NAME)
        if decision.record is not None:
            steps = decision.record[curate_coding.WRAP_STEPS_PARENT]["steps"]
            self.assertNotIn("thought", steps[0])

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
        self.assertIn(curate_coding.REASON_HIDDEN_REASONING_REMOVED, stage["reason_codes"])
        self.assertIn(curate_coding.REASON_STEPS_MIGRATED, stage["reason_codes"])
        for side_name in ("chosen", "rejected"):
            self.assertEqual(stage["side_curation"][side_name]["action"], "modified")
            self.assertGreater(
                stage["side_curation"][side_name]["hidden_reasoning_fields_removed"], 0
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
        for side_name in ("chosen", "rejected"):
            pure[side_name]["steps"][0]["thought"] = (
                f"hidden same-state reasoning on {side_name}"
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
        self.assertTrue(retained_stage["side_curation_changed"])
        self.assertEqual(retained_stage["lane_action"], "repaired")
        self.assertIn(
            curate_coding.REASON_HIDDEN_REASONING_REMOVED,
            retained_stage["reason_codes"],
        )
        for side_name in ("chosen", "rejected"):
            self.assertNotIn("thought", retained.record[side_name]["steps"][0])
            self.assertTrue(
                retained.record[side_name]["steps"][0]["decision_basis"].strip()
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
            "id": "legacy-rewardless",
            "payload": "now removed",
            "meta": {"factory": "thalamic-trajectory-factory", "round": 1},
            "reward_training": stale["reward_training"],
        }
        curated = {
            "id": "sfcur-rewardless",
            "payload": "now removed",
            "meta": copy.deepcopy(record["meta"]),
            "provenance": {"kind": "designed", "claimed": None, "basis": "test"},
            "reward_training": stale["reward_training"],
        }
        mapping = {
            "action": "retained",
            "reason_codes": ["identity.assigned", "provenance.canonicalized"],
            "record_kind": "thalamic",
            "output_id": curated["id"],
            "id_mappings": [
                {
                    "owner_path": "/",
                    "output_id": curated["id"],
                    "original_ids": [{"path": "/id", "value": "legacy-rewardless"}],
                }
            ],
        }

        with mock.patch.object(
            curate_identity,
            "curate_record",
            return_value=curate_identity.CurationResult(
                "retained", curated, mapping
            ),
        ):
            decision = compose_curated.compose_record(
                record,
                source_path="thalamic-trajectory-factory/batch-r01.jsonl",
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

    def test_excluded_coordinate_does_not_claim_the_source_duplicate_key(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root / "run"
            record = thalamic("eligible-copy")
            write_jsonl(source / "aaa-unregistered" / "batch-r01.jsonl", [record])
            write_jsonl(
                source / "thalamic-trajectory-factory" / "batch-r01.jsonl",
                [record],
            )

            summary = compose_curated.compose_run(source, root / "curated")
            manifest = read_jsonl(root / "curated" / summary["manifest"]["path"])

            self.assertEqual(summary["counts"]["source_records"], 2)
            self.assertEqual(summary["counts"]["retained"], 1)
            self.assertEqual(summary["counts"]["excluded"], 1)
            self.assertNotIn(
                compose_curated.REASON_DUPLICATE_SOURCE_RECORD,
                manifest[1]["reason_codes"],
            )
            self.assertEqual(manifest[1]["action"], compose_curated.ACTION_RETAINED)

    def test_records_that_converge_after_coding_are_excluded_before_export(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root / "run" / "agentic-coding-trajectory-factory"
            source.mkdir(parents=True)
            first = episode("converged")
            second = copy.deepcopy(first)
            second["steps"][0]["thought"] = "different hidden text"
            write_jsonl(source / "batch-r01.jsonl", [first, second])

            summary = compose_curated.compose_run(root / "run", root / "curated")
            manifest = read_jsonl(root / "curated" / summary["manifest"]["path"])

            self.assertEqual(summary["counts"]["source_records"], 2)
            self.assertEqual(summary["counts"]["retained"], 1)
            self.assertEqual(summary["counts"]["excluded"], 1)
            self.assertEqual(
                summary["exclusions"],
                {compose_curated.REASON_DUPLICATE_CURATED_RECORD: 1},
            )
            duplicate = manifest[1]
            self.assertEqual(
                duplicate["reason_codes"],
                [compose_curated.REASON_DUPLICATE_CURATED_RECORD],
            )
            dedup_stage = duplicate["stages"][-1]
            self.assertEqual(dedup_stage["lane"], "post_transform_dedup")
            self.assertEqual(
                dedup_stage["first_source_path"],
                "agentic-coding-trajectory-factory/batch-r01.jsonl",
            )
            self.assertEqual(dedup_stage["first_source_line"], 1)

    def test_preserved_legacy_ids_do_not_hide_post_curation_duplicates(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root / "run" / "agentic-coding-trajectory-factory"
            source.mkdir(parents=True)
            first = episode("same")
            first["meta"]["id"] = "legacy-a"
            second = copy.deepcopy(first)
            second["id"] = "legacy-episode-other"
            second["meta"]["id"] = "legacy-b"
            write_jsonl(source / "batch-r01.jsonl", [first, second])

            summary = compose_curated.compose_run(root / "run", root / "curated")
            manifest = read_jsonl(root / "curated" / summary["manifest"]["path"])

            self.assertEqual(summary["counts"]["source_records"], 2)
            self.assertEqual(summary["counts"]["retained"], 1)
            self.assertEqual(summary["counts"]["excluded"], 1)
            self.assertEqual(
                summary["exclusions"],
                {compose_curated.REASON_DUPLICATE_CURATED_RECORD: 1},
            )
            duplicate = manifest[1]
            self.assertEqual(
                duplicate["reason_codes"],
                [compose_curated.REASON_DUPLICATE_CURATED_RECORD],
            )
            output = read_jsonl(root / "curated" / manifest[0]["output_path"])
            self.assertEqual(len(output), 1)
            self.assertNotEqual(output[0]["meta"]["id"], output[0]["id"])

    def test_cross_factory_episode_duplicates_are_deduplicated_by_content_not_provenance(self):
        """Codex #97 P1: the semantic-dedup digest must ignore factory/generator labels.

        The registry authorizes dozens of distinct path_id factories that all
        produce the generic "episode" record kind. The same episode content
        resubmitted under a second authorized episode factory differs only
        in meta.factory and its legacy id -- exactly the identity-binding
        fields this digest already strips for same-factory duplicates.
        Leaving meta.factory in the hash would keep both rows and, on a
        two-row corpus, the deterministic train/eval split would then put
        one copy in train and the other in eval: near-duplicate training
        content leaking across the holdout.
        """
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root / "run"
            first = episode("cross-factory")
            first["meta"]["id"] = "legacy-a"
            second = copy.deepcopy(first)
            second["id"] = "legacy-episode-other"
            second["meta"]["id"] = "legacy-b"
            second["meta"]["factory"] = "agent-memory-compaction-factory"
            write_jsonl(
                source / "agentic-coding-trajectory-factory" / "batch-r01.jsonl",
                [first],
            )
            write_jsonl(
                source / "agent-memory-compaction-factory" / "batch-r01.jsonl",
                [second],
            )

            summary = compose_curated.compose_run(source, root / "curated")
            manifest = read_jsonl(root / "curated" / summary["manifest"]["path"])

            self.assertEqual(summary["counts"]["source_records"], 2)
            self.assertEqual(summary["counts"]["retained"], 1)
            self.assertEqual(summary["counts"]["excluded"], 1)
            self.assertEqual(
                summary["exclusions"],
                {compose_curated.REASON_DUPLICATE_CURATED_RECORD: 1},
            )
            duplicate = next(
                entry
                for entry in manifest
                if entry["reason_codes"]
                == [compose_curated.REASON_DUPLICATE_CURATED_RECORD]
            )
            dedup_stage = duplicate["stages"][-1]
            self.assertEqual(dedup_stage["lane"], "post_transform_dedup")
            retained = next(
                entry for entry in manifest if entry is not duplicate
            )
            output = read_jsonl(root / "curated" / retained["output_path"])
            self.assertEqual(len(output), 1)
            # The surviving row still names its own real factory -- only the
            # dedup digest, not the emitted record, ignores provenance.
            self.assertIn(
                output[0]["meta"]["factory"],
                {"agentic-coding-trajectory-factory", "agent-memory-compaction-factory"},
            )

    def test_side_stamped_preference_duplicates_are_deduplicated(self):
        """Codex #97 P1: side-level factory labels must not survive the digest.

        A Fable preference wrapper predates a wrapper-level ``meta.factory``
        and attests its factory on ``chosen``/``rejected`` instead --
        ``curate_identity._payload_factory`` accepts exactly that shape. If the
        semantic digest normalizes only ``semantic["meta"]``, the same pair
        submitted under two authorized preference factories survives twice,
        and on a two-record corpus the deterministic split necessarily puts
        one copy in train and its twin in eval.
        """

        def side_stamped(factory, tag):
            record = trajectory_preference_pair()
            record["id"] = f"legacy-pref-{tag}"
            record["meta"] = {"round": 1}
            for side in ("chosen", "rejected"):
                record[side]["meta"] = {"factory": factory}
            return record

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root / "run"
            write_jsonl(
                source / "tool-use-preference-factory" / "batch-r01.jsonl",
                [side_stamped("tool-use-preference-factory", "a")],
            )
            write_jsonl(
                source / "code-review-preference-factory" / "batch-r01.jsonl",
                [side_stamped("code-review-preference-factory", "b")],
            )

            summary = compose_curated.compose_run(source, root / "curated")

            self.assertEqual(summary["counts"]["source_records"], 2)
            self.assertEqual(summary["counts"]["retained"], 1)
            self.assertEqual(
                summary["exclusions"],
                {compose_curated.REASON_DUPLICATE_CURATED_RECORD: 1},
            )

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

    def test_composition_rejects_hard_linked_calibration_evidence(self):
        for mode in ("explicit", "source_run"):
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as td:
                root = Path(td)
                source = build_source_run(root / "run")
                original = root / "calibration-evidence.json"
                original.write_text('{"records":[]}\n', encoding="utf-8")
                if mode == "explicit":
                    calibration = root / "units-migration.json"
                    os.link(original, calibration)
                    kwargs = {"units_migration": calibration}
                else:
                    calibration = source / compose_curated.FFPC_UNITS_MIGRATION
                    os.link(original, calibration)
                    kwargs = {}

                with self.assertRaisesRegex(
                    compose_curated.ComposeError, "hard-link"
                ):
                    compose_curated.compose_run(
                        source,
                        root / "curated",
                        **kwargs,
                    )
                self.assertFalse((root / "curated").exists())

    def test_composition_rejects_calibration_through_a_symlinked_parent(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = build_source_run(root / "run")
            real_parent = root / "real-calibration-parent"
            real_parent.mkdir()
            calibration = real_parent / "units-migration.json"
            calibration.write_text('{"records":[]}\n', encoding="utf-8")
            alias_parent = root / "calibration-parent-alias"
            alias_parent.symlink_to(real_parent, target_is_directory=True)

            with self.assertRaisesRegex(
                compose_curated.ComposeError,
                "calibration parent must be an exact non-symlink directory",
            ):
                compose_curated.compose_run(
                    source,
                    root / "curated",
                    units_migration=alias_parent / calibration.name,
                )
            self.assertFalse((root / "curated").exists())

    def test_calibration_parent_swap_cannot_redirect_the_captured_payload(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = build_source_run(root / "run")
            calibration_parent = root / "calibration-parent"
            calibration_parent.mkdir()
            calibration = calibration_parent / "units-migration.json"
            calibration.write_text('{"records":[]}\n', encoding="utf-8")
            moved_parent = root / "original-calibration-parent"
            replacement_parent = root / "replacement-calibration-parent"
            replacement_parent.mkdir()
            (replacement_parent / calibration.name).write_text(
                '{"records":[{"scope":"ffpc-r99-a","usd_conversion_factor":2}]}\n',
                encoding="utf-8",
            )
            real_open = os.open
            swapped = False

            def swap_parent_before_open(path, flags, mode=0o777, *, dir_fd=None):
                nonlocal swapped
                if Path(path) == calibration_parent and dir_fd is None and not swapped:
                    swapped = True
                    calibration_parent.rename(moved_parent)
                    calibration_parent.symlink_to(
                        replacement_parent,
                        target_is_directory=True,
                    )
                return real_open(path, flags, mode, dir_fd=dir_fd)

            with mock.patch.object(
                compose_curated.os,
                "open",
                side_effect=swap_parent_before_open,
            ):
                with self.assertRaisesRegex(
                    compose_curated.ComposeError,
                    "calibration parent changed while it was pinned",
                ):
                    compose_curated.compose_run(
                        source,
                        root / "curated",
                        units_migration=calibration,
                    )

            self.assertTrue(swapped)
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

    def test_composition_rejects_nonfinite_calibration_even_when_ignored(self):
        for constant in ("NaN", "Infinity", "-Infinity"):
            with self.subTest(constant=constant), tempfile.TemporaryDirectory() as td:
                root = Path(td)
                source = build_source_run(root / "run")
                calibration = root / "units-migration.json"
                calibration.write_text(
                    '{"records":[{"ignored":' + constant + '}]}' + "\n",
                    encoding="utf-8",
                )

                with self.assertRaisesRegex(
                    compose_curated.ComposeError,
                    "invalid calibration JSON",
                ):
                    compose_curated.compose_run(
                        source,
                        root / "curated",
                        units_migration=calibration,
                    )
                self.assertFalse((root / "curated").exists())

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

            real_parent = root / "real-destination-parent"
            real_parent.mkdir()
            symlink_parent = root / "destination-parent-alias"
            symlink_parent.symlink_to(real_parent, target_is_directory=True)
            with self.assertRaisesRegex(
                compose_curated.ComposeError, "exact non-symlink directory"
            ):
                compose_curated.compose_run(source, symlink_parent / "curated")
            self.assertFalse((real_parent / "curated").exists())

    def test_pinned_writer_refuses_a_child_directory_swapped_for_a_symlink(self):
        """A swapped child must not steer curated payload into outputs/raw."""

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            destination = root / "curated"
            destination.mkdir()
            raw = root / "outputs" / "raw"
            raw.mkdir(parents=True)
            # The window the pin closes: another same-user process replaces the
            # freshly created child between ``mkdir`` and ``open``.
            (destination / compose_curated.RECORDS_DIRNAME).symlink_to(
                raw, target_is_directory=True
            )
            descriptor = os.open(destination, os.O_RDONLY | os.O_DIRECTORY)
            try:
                with self.assertRaises(compose_curated.ComposeError):
                    compose_curated._write_new_text(
                        descriptor,
                        f"{compose_curated.RECORDS_DIRNAME}/escaped.jsonl",
                        "{}\n",
                    )
            finally:
                os.close(descriptor)
            self.assertEqual(sorted(path.name for path in raw.iterdir()), [])

    def test_pinned_writer_refuses_a_final_name_swapped_for_a_symlink(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            destination = root / "curated"
            destination.mkdir()
            outside = root / "outside.jsonl"
            descriptor = os.open(destination, os.O_RDONLY | os.O_DIRECTORY)
            try:
                (destination / "COMPOSE.json").symlink_to(outside)
                with self.assertRaises(compose_curated.ComposeError):
                    compose_curated._write_new_text(
                        descriptor, compose_curated.SUMMARY_FILENAME, "{}\n"
                    )
            finally:
                os.close(descriptor)
            self.assertFalse(outside.exists())

    def test_pinned_writer_rejects_unsafe_relative_destinations(self):
        with tempfile.TemporaryDirectory() as td:
            destination = Path(td) / "curated"
            destination.mkdir()
            descriptor = os.open(destination, os.O_RDONLY | os.O_DIRECTORY)
            try:
                for unsafe in ("", "/absolute.jsonl", "../escape.jsonl", "a/./b.jsonl"):
                    with self.subTest(unsafe=unsafe):
                        with self.assertRaises(compose_curated.ComposeError):
                            compose_curated._write_new_text(descriptor, unsafe, "{}\n")
            finally:
                os.close(descriptor)

    def test_pinned_writer_creates_nested_components_and_hashes_bytes(self):
        with tempfile.TemporaryDirectory() as td:
            destination = Path(td) / "curated"
            destination.mkdir()
            descriptor = os.open(destination, os.O_RDONLY | os.O_DIRECTORY)
            try:
                digest = compose_curated._write_new_text(
                    descriptor, "records/factory/rows.jsonl", "{}\n"
                )
            finally:
                os.close(descriptor)
            written = destination / "records" / "factory" / "rows.jsonl"
            self.assertEqual(written.read_text(encoding="utf-8"), "{}\n")
            self.assertEqual(
                digest, hashlib.sha256(b"{}\n").hexdigest()
            )

    def test_a_failed_composition_removes_the_new_destination(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = build_source_run(root / "run")
            destination = root / "curated"

            real_write = compose_curated._write_new_text

            def fail_on_manifest(root_descriptor, relative, text):
                if relative.endswith(compose_curated.MANIFEST_FILENAME):
                    raise OSError("simulated manifest write failure")
                return real_write(root_descriptor, relative, text)

            with mock.patch.object(
                compose_curated, "_write_new_text", side_effect=fail_on_manifest
            ):
                with self.assertRaises(OSError):
                    compose_curated.compose_run(source, destination)
            self.assertFalse(destination.exists())

    def test_destination_parent_swap_cannot_redirect_creation_or_cleanup(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = build_source_run(root / "run")
            parent = root / "destination-parent"
            parent.mkdir()
            moved_parent = root / "original-parent-moved"
            replacement_parent = root / "replacement-parent"
            destination = parent / "curated"
            real_mkdir = os.mkdir
            swapped = False

            def swap_parent_before_create(path, mode=0o777, *, dir_fd=None):
                nonlocal swapped
                if path == destination.name and dir_fd is not None and not swapped:
                    swapped = True
                    parent.rename(moved_parent)
                    real_mkdir(replacement_parent, 0o755)
                    replacement_parent.rename(parent)
                return real_mkdir(path, mode, dir_fd=dir_fd)

            with mock.patch.object(
                compose_curated.os,
                "mkdir",
                side_effect=swap_parent_before_create,
            ):
                with self.assertRaisesRegex(
                    compose_curated.ComposeError,
                    "destination parent changed while it was pinned",
                ):
                    compose_curated.compose_run(source, destination)

            self.assertTrue(swapped)
            self.assertFalse((moved_parent / destination.name).exists())
            self.assertFalse((parent / destination.name).exists())

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


class ComposeSourceLineResourceLimits(unittest.TestCase):
    """One malformed line must be excluded, never abort the whole composition."""

    def compose(self, physical_line):
        return compose_curated.compose_source_line(
            physical_line,
            source_path="tool-use-preference-factory/batch-r01.jsonl",
            source_line=1,
            source_file_sha256="7" * 64,
        )

    def test_deeply_nested_line_is_excluded_instead_of_raising(self):
        # ``json.loads`` recurses over the document, so a deep enough line
        # exhausts the stack.  ``RecursionError`` is not a ``ValueError``:
        # unguarded it escaped ``compose_source_line`` and rolled the whole
        # destination back over a single bad line.
        depth = 200_000
        decision = self.compose(b"[" * depth + b"]" * depth)

        self.assertEqual(decision.action, compose_curated.ACTION_EXCLUDED)
        self.assertEqual(
            decision.reason_codes, (compose_curated.REASON_INVALID_JSON,)
        )
        self.assertIsNone(decision.record)
        stage = decision.stages[0]
        self.assertEqual(stage["lane"], "source")
        self.assertEqual(stage["action"], compose_curated.ACTION_EXCLUDED)
        self.assertIn("error", stage["detail"])

    def test_canonical_hash_recursion_is_excluded_per_line(self):
        # A line shallow enough for ``json.loads`` can still be too deep for
        # the canonical hash, which recurses separately.  The hashing call
        # therefore has to sit inside the same guarded block as the decode.
        payload = json.dumps({"kind": "coding_episode", "steps": []}).encode("utf-8")

        with mock.patch.object(
            compose_curated, "_canonical_sha256", side_effect=RecursionError
        ):
            decision = self.compose(payload)

        self.assertEqual(decision.action, compose_curated.ACTION_EXCLUDED)
        self.assertEqual(
            decision.reason_codes, (compose_curated.REASON_INVALID_JSON,)
        )
        self.assertIsNone(decision.record)

    def test_a_fatal_line_does_not_roll_back_the_whole_run(self):
        # The unguarded ``RecursionError`` escaped ``compose_run``, which
        # discards the destination on any error, so one deep line destroyed
        # the composition of every other record in the run.
        depth = 200_000
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root / "run" / "thalamic-trajectory-factory"
            source.mkdir(parents=True)
            (source / "batch-r01.jsonl").write_text(
                json.dumps(thalamic("keep"))
                + "\n"
                + "[" * depth
                + "]" * depth
                + "\n",
                encoding="utf-8",
            )

            summary = compose_curated.compose_run(root / "run", root / "curated")

            self.assertTrue((root / "curated").exists())
            self.assertEqual(summary["counts"]["source_records"], 2)
            self.assertEqual(summary["counts"]["retained"], 1)
            self.assertEqual(summary["counts"]["excluded"], 1)
            self.assertEqual(
                summary["exclusions"],
                {compose_curated.REASON_INVALID_JSON: 1},
            )


class TrajectorySideGroundingScope(unittest.TestCase):
    """Every side carrying steps runs the coding lane, grounded or not."""

    def test_nonblank_but_ungrounded_decision_basis_is_regrounded(self):
        pair = trajectory_preference_pair()
        for side_name in ("chosen", "rejected"):
            for step in pair[side_name]["steps"]:
                # Nonblank, so the old "does any step lack a basis?" probe
                # skipped the lane entirely and shipped this text verbatim.
                step["decision_basis"] = "Private hunch, no visible evidence."

        decision = compose_curated.compose_record(
            pair,
            source_path="tool-use-preference-factory/batch-r01.jsonl",
            source_line=1,
            source_sha256="8" * 64,
        )

        self.assertEqual(decision.action, compose_curated.ACTION_RETAINED)
        for side_name in ("chosen", "rejected"):
            for step in decision.record[side_name]["steps"]:
                self.assertNotIn("Private hunch", step["decision_basis"])
                self.assertTrue(step["decision_basis"].startswith("Observation:"))
        stage = next(item for item in decision.stages if item["lane"] == "preferences")
        for side_name in ("chosen", "rejected"):
            side_manifest = stage["side_curation"][side_name]
            self.assertEqual(side_manifest["action"], "modified")
            self.assertNotEqual(
                side_manifest["action"], compose_curated.ACTION_NOT_APPLICABLE
            )

    def test_an_already_grounded_side_is_retained_byte_for_byte(self):
        # The lane is idempotent: running it on a side whose basis is already
        # derived from visible evidence must not perturb the payload.
        pair = trajectory_preference_pair()
        first = compose_curated.compose_record(
            pair,
            source_path="tool-use-preference-factory/batch-r01.jsonl",
            source_line=1,
            source_sha256="9" * 64,
        )
        second = compose_curated.compose_record(
            copy.deepcopy(first.record),
            source_path="tool-use-preference-factory/batch-r01.jsonl",
            source_line=1,
            source_sha256="9" * 64,
        )

        for side_name in ("chosen", "rejected"):
            self.assertEqual(
                first.record[side_name]["steps"], second.record[side_name]["steps"]
            )


class CalibrationLookup(unittest.TestCase):
    """Rewards are calibrated by the record's *source* identifier."""

    CATALOG = {"ffpc-r5-002": {"canonical_factor": 0.5}}

    def test_an_absent_catalog_never_calibrates(self):
        for catalog in (None, {}):
            with self.subTest(catalog=catalog):
                self.assertIsNone(
                    compose_curated.calibration_for({"id": "ffpc-r5-002"}, catalog)
                )

    def test_a_top_level_id_is_matched_case_insensitively(self):
        self.assertEqual(
            compose_curated.calibration_for({"id": "FFPC-R5-002"}, self.CATALOG),
            self.CATALOG["ffpc-r5-002"],
        )

    def test_a_meta_id_is_used_when_the_top_level_id_is_gone(self):
        # Compose runs the identity lane first, which replaces ``id`` with a
        # canonical digest, so the pre-identity id has to be reachable.
        self.assertEqual(
            compose_curated.calibration_for(
                {"id": None, "meta": {"id": "ffpc-r5-002"}}, self.CATALOG
            ),
            self.CATALOG["ffpc-r5-002"],
        )

    def test_an_unusable_identifier_yields_no_calibration(self):
        for record in (
            {"id": 17},
            {"meta": "not a mapping"},
            {"meta": {"id": 17}},
            {},
            "not a record",
        ):
            with self.subTest(record=record):
                self.assertIsNone(
                    compose_curated.calibration_for(record, self.CATALOG)
                )

    def test_an_unlisted_record_is_not_calibrated(self):
        self.assertIsNone(
            compose_curated.calibration_for({"id": "ffpc-r5-999"}, self.CATALOG)
        )
