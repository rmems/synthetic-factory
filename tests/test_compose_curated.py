#!/usr/bin/env python3
"""Tests for composing the five curation lanes into one curated destination."""

import hashlib
import io
import json
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
        "meta": {"tags": ["bridge"], "round": 1},
    }


def preference_pair(*, pure=True):
    return {
        "id": "legacy-pref-pure" if pure else "legacy-pref-impure",
        "chosen": trajectory(action="noop", domain="pref"),
        "rejected": trajectory(action="noop" if pure else "other", domain="pref"),
        "critique": "chosen is safer",
        "meta": {"tags": ["preference"], "round": 1},
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
        "meta": {"tags": ["coding"], "round": 1},
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
