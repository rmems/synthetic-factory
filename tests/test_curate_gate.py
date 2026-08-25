#!/usr/bin/env python3
"""Tests for pipelines/curate_gate.py — the sf-c5l.7 integration/promotion gate."""

import io
import json
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock

REPO = Path(__file__).resolve().parents[1]
PIPELINES = REPO / "pipelines"
GATE_SCRIPT = PIPELINES / "curate_gate.py"

sys.path.insert(0, str(PIPELINES))
import curate_gate  # noqa: E402


def _thalamic(record_id, **overrides):
    record = {
        "id": record_id,
        "state": {"sim_or_real": "designed", "env": "curation gate fixture"},
        "proposed_action": {"action": "noop", "decision_basis": "fixture"},
        "safety_decision": {"decision": "ACCEPT", "rationale": "bounded fixture"},
        "executed_action": {"action": "noop"},
        "future_outcome": {"ok": True},
        "reward_components": {"task_progress": 0.5, "total": 0.5},
        "meta": {"factory": "fixture", "round": 2, "tags": ["fixture"]},
    }
    record.update(overrides)
    return record


def _preference(record_id="pref-1"):
    return {
        "id": record_id,
        "failure_mode": "test",
        "rejected": _thalamic(f"{record_id}-rejected"),
        "chosen": _thalamic(f"{record_id}-chosen"),
        "critique": "chosen gate is bounded",
        "reward_delta": {"total": 0.8},
    }


def _bridge(record_id="bridge-1"):
    return {
        "id": record_id,
        "spike_events": [
            {"channel": "c0", "t_rel_ms": 1.0, "amplitude": 0.4},
            {"channel": "c0", "t_rel_ms": 2.0, "amplitude": 0.3},
        ],
        "language_view": {
            "description": "two sparse events",
            "trajectory": _thalamic(f"{record_id}-trajectory"),
        },
        "bridge_notes": {"mapping": "fixture", "training_value": "routing"},
    }


def _episode(record_id="episode-1"):
    return {
        "id": record_id,
        "goal": "fix fixture",
        "steps": [
            {
                "n": 1,
                "decision_basis": "observable file is missing",
                "tool_call": {"name": "rg", "args": {"q": "fixture"}},
                "observation": "no match",
                "reflection": "create bounded fixture",
            }
        ],
        "outcome": "fixed",
        "reward": {"success": True},
    }


def _write_jsonl(path, records):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(record) + "\n" for record in records))


def _quiet_main(argv):
    """Run the gate CLI in-process without leaking its report into test output."""
    with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
        return curate_gate.main(argv)


def _lane_manifest_entry(action, line, reasons=(), transform="bridge_event_time_order"):
    return {
        "source_path": "outputs/raw/2026-08-17/bridge/batch-r02.jsonl",
        "source_line": line,
        "source_hash": f"hash-{line}",
        "transform_name": transform,
        "transform_version": "1.0.0",
        "action": action,
        "reason_codes": list(reasons),
        "output_id": f"out-{line}" if action == "retained" else None,
        "output_hash": f"out-hash-{line}" if action == "retained" else None,
    }


class GateFixture:
    """A six-lane curation scenario laid out under one temporary root."""

    def __init__(self, root, bridge_records=None, thalamic_records=None):
        self.root = Path(root)
        self.lane_bridge = self.root / "lane-bridge"
        self.lane_core = self.root / "lane-core"
        self.lane_preference = self.root / "lane-preference"
        self.lane_reward = self.root / "lane-reward"
        self.lane_coding = self.root / "lane-coding"
        self.lane_tag = self.root / "lane-tag"
        _write_jsonl(
            self.lane_bridge / "bridge-factory" / "batch-r02.jsonl",
            bridge_records if bridge_records is not None else [_bridge()],
        )
        core_records = (
            thalamic_records
            if thalamic_records is not None
            else [_thalamic("t-1"), _preference(), _episode()]
        )
        for lane_dir in (
            self.lane_core,
            self.lane_preference,
            self.lane_reward,
            self.lane_coding,
            self.lane_tag,
        ):
            _write_jsonl(lane_dir / "thalamic-mini" / "batch-r02.jsonl", core_records)
        (self.lane_bridge / "manifest.jsonl").write_text(
            "".join(
                json.dumps(entry) + "\n"
                for entry in (
                    _lane_manifest_entry("retained", 1),
                    _lane_manifest_entry("quarantine", 2, ["AMBIGUOUS_EVENT_ORDER"]),
                    _lane_manifest_entry("excluded", 3, ["INVALID_JSON"]),
                )
            )
        )
        self.plan_path = self.root / "plan.json"
        self.plan_path.write_text(
            json.dumps(
                {
                    "schema": "curation-integration-plan/v1",
                    "source_run": "outputs/raw/2026-08-17",
                    "lanes": [
                        {
                            "bead": "sf-c5l.1",
                            "transform": "bridge_event_time_order",
                            "version": "1.0.0",
                            "outputs": "lane-bridge",
                            "manifest": "lane-bridge/manifest.jsonl",
                        },
                        {
                            "bead": "sf-c5l.2",
                            "transform": "curate_identity",
                            "version": "identity-provenance-v1",
                            "outputs": "lane-core",
                        },
                        {
                            "bead": "sf-c5l.3",
                            "transform": "same-context-preference-curation",
                            "version": "1.0.0",
                            "outputs": "lane-preference",
                        },
                        {
                            "bead": "sf-c5l.4",
                            "transform": "reward_ontology",
                            "version": "reward-ontology-v1",
                            "outputs": "lane-reward",
                        },
                        {
                            "bead": "sf-c5l.5",
                            "transform": "coding_observability",
                            "version": "1",
                            "outputs": "lane-coding",
                        },
                        {
                            "bead": "sf-c5l.6",
                            "transform": "tag_taxonomy",
                            "version": "1",
                            "outputs": "lane-tag",
                        },
                    ],
                },
                indent=2,
            )
        )
        self.cleaned = self.root / "cleaned-v1"
        self.curated = self.root / "curated-v1"

    def integrate(self, *extra):
        return _quiet_main(
            [
                "integrate",
                "--plan",
                str(self.plan_path),
                "--cleaned-out",
                str(self.cleaned),
                *extra,
            ]
        )

    def manifest(self):
        return json.loads((self.cleaned / curate_gate.MANIFEST_FILENAME).read_text())

    def sample(self):
        return json.loads((self.cleaned / curate_gate.SAMPLE_FILENAME).read_text())

    def accepted_review(self, reviewer="curation-reviewer"):
        template = json.loads((self.cleaned / curate_gate.REVIEW_FILENAME).read_text())
        template["reviewer"] = reviewer
        template["reviewed_at"] = "2026-08-23T00:00:00Z"
        for key in template["verdicts"]:
            template["verdicts"][key] = {"verdict": "accept", "notes": "bounded fixture"}
        path = self.root / "review.json"
        path.write_text(json.dumps(template, indent=2))
        return path

    def promote(self, review_path, curated=None):
        return _quiet_main(
            [
                "promote",
                "--cleaned",
                str(self.cleaned),
                "--review",
                str(review_path),
                "--curated-out",
                str(curated or self.curated),
            ]
        )


class IntegrationTests(unittest.TestCase):
    def setUp(self):
        self._temp = tempfile.TemporaryDirectory(prefix="curate-gate-")
        self.addCleanup(self._temp.cleanup)
        self.root = Path(self._temp.name)

    def test_integrate_composes_lanes_and_reports_training_ready(self):
        fixture = GateFixture(self.root)
        self.assertEqual(fixture.integrate(), 0)

        manifest = fixture.manifest()
        self.assertEqual(manifest["schema"], curate_gate.MANIFEST_SCHEMA)
        self.assertTrue(manifest["training_ready"])
        self.assertEqual(
            [lane["transform"] for lane in manifest["composition_order"]],
            [transform for _bead, transform in curate_gate.REQUIRED_LANES],
        )
        self.assertEqual(
            manifest["transform_versions"],
            {
                "bridge_event_time_order": "1.0.0",
                "coding_observability": "1",
                "curate_identity": "identity-provenance-v1",
                "reward_ontology": "reward-ontology-v1",
                "same-context-preference-curation": "1.0.0",
                "tag_taxonomy": "1",
            },
        )
        self.assertEqual(manifest["counts"]["records"], 4)
        self.assertEqual(
            manifest["counts"]["by_kind"],
            {"bridge_pair": 1, "episode": 1, "preference": 1, "thalamic": 1},
        )
        self.assertEqual(
            manifest["counts"]["by_factory"], {"bridge-factory": 1, "thalamic-mini": 3}
        )
        # Every promotion gate that this bead names is evaluated by name.
        for gate in (
            "structural_validator",
            "record_invariants",
            "training_audit",
            "exact_duplicates",
            "canonical_id_collisions",
            "canonical_id_coverage",
        ):
            self.assertTrue(manifest["gates"][gate]["passed"], gate)
        # Composition happened, and both lane trees landed under one destination.
        self.assertTrue((fixture.cleaned / "bridge-factory" / "batch-r02.jsonl").is_file())
        self.assertTrue((fixture.cleaned / "thalamic-mini" / "batch-r02.jsonl").is_file())

    def test_manifest_carries_hashes_exclusions_and_quarantines(self):
        fixture = GateFixture(self.root)
        fixture.integrate()
        manifest = fixture.manifest()

        self.assertTrue(manifest["corpus_digest"].startswith("sha256:"))
        self.assertEqual(manifest["plan"]["sha256"], curate_gate.file_sha256(fixture.plan_path))
        for entry in manifest["inputs"] + manifest["outputs"]:
            self.assertRegex(entry["sha256"], r"^[0-9a-f]{64}$")
        source = fixture.lane_bridge / "bridge-factory" / "batch-r02.jsonl"
        emitted = fixture.cleaned / "bridge-factory" / "batch-r02.jsonl"
        self.assertEqual(
            curate_gate.file_sha256(source), curate_gate.file_sha256(emitted)
        )

        self.assertEqual(len(manifest["exclusions"]), 1)
        self.assertEqual(manifest["exclusions"][0]["reason_codes"], ["INVALID_JSON"])
        self.assertEqual(manifest["exclusions"][0]["source_line"], 3)
        self.assertEqual(len(manifest["quarantines"]), 1)
        self.assertEqual(
            manifest["quarantines"][0]["reason_codes"], ["AMBIGUOUS_EVENT_ORDER"]
        )
        self.assertEqual(manifest["counts"]["exclusions"], 1)
        self.assertEqual(manifest["counts"]["quarantines"], 1)
        self.assertEqual(
            manifest["counts"]["lane_actions"]["bridge_event_time_order"],
            {"excluded": 1, "quarantine": 1, "retained": 1},
        )
        self.assertEqual(
            manifest["lanes_without_record_manifest"],
            [
                "curate_identity",
                "same-context-preference-curation",
                "reward_ontology",
                "coding_observability",
                "tag_taxonomy",
            ],
        )

    def test_later_lane_supersedes_earlier_lane_at_the_same_path(self):
        fixture = GateFixture(self.root)
        # The second lane in plan order also emits the bridge factory's file.
        _write_jsonl(
            fixture.lane_core / "bridge-factory" / "batch-r02.jsonl",
            [_bridge("bridge-repaired")],
        )
        self.assertEqual(fixture.integrate(), 0)
        manifest = fixture.manifest()

        supersession = next(
            item
            for item in manifest["supersessions"]
            if item["path"] == "bridge-factory/batch-r02.jsonl"
        )
        self.assertEqual(supersession["path"], "bridge-factory/batch-r02.jsonl")
        self.assertEqual(supersession["superseded_transform"], "bridge_event_time_order")
        self.assertEqual(supersession["winning_transform"], "curate_identity")
        emitted = (fixture.cleaned / "bridge-factory" / "batch-r02.jsonl").read_text()
        self.assertIn("bridge-repaired", emitted)

    def test_integrate_refuses_an_existing_cleaned_destination(self):
        fixture = GateFixture(self.root)
        fixture.cleaned.mkdir(parents=True)
        self.assertEqual(fixture.integrate(), 2)

    def test_plan_rejects_a_transform_declared_at_two_versions(self):
        fixture = GateFixture(self.root)
        plan = json.loads(fixture.plan_path.read_text())
        plan["lanes"][1]["transform"] = "bridge_event_time_order"
        plan["lanes"][1]["version"] = "9.9.9"
        fixture.plan_path.write_text(json.dumps(plan))
        with self.assertRaises(curate_gate.GateError) as ctx:
            curate_gate.load_plan(fixture.plan_path)
        self.assertIn("two versions", str(ctx.exception))

    def test_plan_rejects_a_missing_lane_output_directory(self):
        fixture = GateFixture(self.root)
        plan = json.loads(fixture.plan_path.read_text())
        plan["lanes"][0]["outputs"] = "lane-does-not-exist"
        fixture.plan_path.write_text(json.dumps(plan))
        with self.assertRaises(curate_gate.GateError):
            curate_gate.load_plan(fixture.plan_path)

    def test_integrate_refuses_a_symlinked_lane_output(self):
        fixture = GateFixture(self.root)
        outside = self.root / "outside.jsonl"
        _write_jsonl(outside, [_thalamic("t-outside")])
        link = fixture.lane_core / "thalamic-mini" / "linked.jsonl"
        try:
            link.symlink_to(outside)
        except (OSError, NotImplementedError):
            self.skipTest("symlinks are unavailable on this platform")
        self.assertEqual(fixture.integrate(), 2)
        self.assertFalse(fixture.cleaned.exists())

    def test_plan_rejects_a_symlinked_outputs_directory_before_resolving(self):
        fixture = GateFixture(self.root)
        outside = self.root / "outside-lane"
        _write_jsonl(outside / "factory" / "batch.jsonl", [_thalamic("outside")])
        linked = self.root / "linked-lane"
        try:
            linked.symlink_to(outside, target_is_directory=True)
        except (OSError, NotImplementedError):
            self.skipTest("symlinks are unavailable on this platform")
        plan = json.loads(fixture.plan_path.read_text())
        plan["lanes"][1]["outputs"] = linked.name
        fixture.plan_path.write_text(json.dumps(plan))

        self.assertEqual(fixture.integrate(), 2)
        self.assertFalse(fixture.cleaned.exists())

    def test_plan_requires_all_six_lane_contracts_in_order(self):
        fixture = GateFixture(self.root)
        plan = json.loads(fixture.plan_path.read_text())
        plan["lanes"].pop(3)
        fixture.plan_path.write_text(json.dumps(plan))

        with self.assertRaises(curate_gate.GateError) as ctx:
            curate_gate.load_plan(fixture.plan_path)
        self.assertIn("six required contracts in order", str(ctx.exception))

    def test_integrate_rejects_a_lane_with_zero_records(self):
        fixture = GateFixture(self.root)
        tag_output = fixture.lane_tag / "thalamic-mini" / "batch-r02.jsonl"
        tag_output.write_text("\n")

        self.assertEqual(fixture.integrate(), 2)
        self.assertFalse(fixture.cleaned.exists())

    def test_destinations_beneath_raw_output_are_rejected(self):
        fixture = GateFixture(self.root)
        raw_root = self.root / "outputs" / "raw"
        raw_root.mkdir(parents=True)
        fixture.cleaned = raw_root / "cleaned-attempt"

        with mock.patch.object(curate_gate, "RAW_OUTPUT_ROOT", raw_root.resolve()):
            self.assertEqual(fixture.integrate(), 2)
        self.assertFalse(fixture.cleaned.exists())

    def test_integrate_rejects_a_non_positive_sample_size(self):
        fixture = GateFixture(self.root)
        self.assertEqual(fixture.integrate("--per-stratum", "0"), 2)
        self.assertFalse(fixture.cleaned.exists())

    def test_a_lane_manifest_inside_the_output_tree_stays_out_of_the_corpus(self):
        fixture = GateFixture(self.root)
        self.assertTrue((fixture.lane_bridge / "manifest.jsonl").is_file())
        self.assertEqual(fixture.integrate(), 0)
        self.assertFalse((fixture.cleaned / "manifest.jsonl").exists())
        manifest = fixture.manifest()
        self.assertNotIn("manifest.jsonl", {entry["path"] for entry in manifest["outputs"]})

    def test_a_failed_plan_leaves_no_partial_destination(self):
        fixture = GateFixture(self.root)
        for path in (fixture.lane_tag / "thalamic-mini").glob("*.jsonl"):
            path.unlink()
        self.assertEqual(fixture.integrate(), 2)
        self.assertFalse(fixture.cleaned.exists())

    def test_integration_failure_removes_the_staged_destination(self):
        fixture = GateFixture(self.root)
        with mock.patch.object(
            curate_gate, "run_gates", side_effect=curate_gate.GateError("gate exploded")
        ):
            self.assertEqual(fixture.integrate(), 2)

        self.assertFalse(fixture.cleaned.exists())
        self.assertEqual(list(self.root.glob(".cleaned-v1.staging-*")), [])


class CorpusGateTests(unittest.TestCase):
    def setUp(self):
        self._temp = tempfile.TemporaryDirectory(prefix="curate-gate-")
        self.addCleanup(self._temp.cleanup)
        self.root = Path(self._temp.name)

    def test_exact_duplicate_records_block_the_gate(self):
        duplicate = _thalamic("t-dup")
        fixture = GateFixture(
            self.root, thalamic_records=[duplicate, json.loads(json.dumps(duplicate))]
        )
        self.assertEqual(fixture.integrate(), 1)
        manifest = fixture.manifest()

        self.assertFalse(manifest["training_ready"])
        self.assertFalse(manifest["gates"]["exact_duplicates"]["passed"])
        self.assertEqual(manifest["gates"]["exact_duplicates"]["count"], 1)
        self.assertTrue(
            any(blocker.startswith("EXACT_DUPLICATES:") for blocker in manifest["blockers"])
        )

    def test_canonical_id_collisions_block_the_gate(self):
        first = _thalamic("t-collide")
        second = _thalamic("t-collide", future_outcome={"ok": False})
        fixture = GateFixture(self.root, thalamic_records=[first, second])
        self.assertEqual(fixture.integrate(), 1)
        manifest = fixture.manifest()

        self.assertFalse(manifest["gates"]["canonical_id_collisions"]["passed"])
        self.assertTrue(manifest["gates"]["exact_duplicates"]["passed"])
        self.assertTrue(
            any(
                blocker.startswith("CANONICAL_ID_COLLISIONS:")
                for blocker in manifest["blockers"]
            )
        )

    def test_records_without_canonical_top_level_ids_block_the_gate(self):
        anonymous = _thalamic("t-anon")
        anonymous.pop("id")
        anonymous["meta"].pop("id", None)
        fixture = GateFixture(self.root, thalamic_records=[anonymous])
        self.assertEqual(fixture.integrate(), 1)
        manifest = fixture.manifest()

        self.assertFalse(manifest["gates"]["canonical_id_coverage"]["passed"])
        self.assertEqual(manifest["gates"]["canonical_id_coverage"]["missing_top_level"], 1)

    def test_a_structurally_broken_record_blocks_the_gate(self):
        broken = _thalamic("t-broken")
        broken["safety_decision"] = {"decision": "MAYBE", "rationale": ""}
        fixture = GateFixture(self.root, thalamic_records=[broken])
        self.assertEqual(fixture.integrate(), 1)
        manifest = fixture.manifest()

        self.assertFalse(manifest["gates"]["structural_validator"]["passed"])
        self.assertFalse(manifest["training_ready"])


class ReviewSampleTests(unittest.TestCase):
    def setUp(self):
        self._temp = tempfile.TemporaryDirectory(prefix="curate-gate-")
        self.addCleanup(self._temp.cleanup)
        self.root = Path(self._temp.name)

    def test_sample_stratifies_by_factory_kind_and_decision(self):
        rejected = _thalamic("t-rejected")
        rejected["safety_decision"] = {"decision": "REJECT", "rationale": "unsafe"}
        fixture = GateFixture(
            self.root,
            thalamic_records=[_thalamic("t-1"), rejected, _preference(), _episode()],
        )
        fixture.integrate()
        sample = fixture.sample()

        strata = {
            (row["factory"], row["kind"], row["decision"]) for row in sample["strata"]
        }
        self.assertEqual(
            strata,
            {
                ("bridge-factory", "bridge_pair", "ACCEPT"),
                ("thalamic-mini", "thalamic", "ACCEPT"),
                ("thalamic-mini", "thalamic", "REJECT"),
                ("thalamic-mini", "preference", "ACCEPT"),
                ("thalamic-mini", "episode", "none"),
            },
        )
        self.assertEqual(sample["sampled_records"], len(sample["items"]))
        self.assertEqual(sample["schema"], curate_gate.SAMPLE_SCHEMA)
        self.assertTrue(sample["corpus_digest"].startswith("sha256:"))

    def test_sample_caps_each_stratum_and_is_deterministic(self):
        records = [_thalamic(f"t-{index}") for index in range(6)]
        fixture = GateFixture(self.root, thalamic_records=records)
        fixture.integrate()
        first = fixture.sample()

        thalamic_rows = [row for row in first["strata"] if row["kind"] == "thalamic"]
        self.assertEqual(len(thalamic_rows), 1)
        self.assertEqual(thalamic_rows[0]["population"], 6)
        self.assertEqual(thalamic_rows[0]["sampled"], curate_gate.DEFAULT_PER_STRATUM)

        # Same corpus, fresh computation: identical selection.
        again = curate_gate.build_sample(fixture.cleaned)
        self.assertEqual(
            [item["source"] for item in first["items"]],
            [item["source"] for item in again["items"]],
        )

    def test_per_stratum_option_widens_the_sample(self):
        records = [_thalamic(f"t-{index}") for index in range(6)]
        fixture = GateFixture(self.root, thalamic_records=records)
        fixture.integrate("--per-stratum", "4")
        sample = fixture.sample()
        thalamic_rows = [row for row in sample["strata"] if row["kind"] == "thalamic"]
        self.assertEqual(thalamic_rows[0]["sampled"], 4)

    def test_review_template_lists_every_sampled_record(self):
        fixture = GateFixture(self.root)
        fixture.integrate()
        sample = fixture.sample()
        template = json.loads((fixture.cleaned / curate_gate.REVIEW_FILENAME).read_text())
        self.assertEqual(
            sorted(template["verdicts"]), sorted(item["source"] for item in sample["items"])
        )
        self.assertEqual(template["corpus_digest"], sample["corpus_digest"])


class PromotionTests(unittest.TestCase):
    def setUp(self):
        self._temp = tempfile.TemporaryDirectory(prefix="curate-gate-")
        self.addCleanup(self._temp.cleanup)
        self.root = Path(self._temp.name)
        self.fixture = GateFixture(self.root)
        self.assertEqual(self.fixture.integrate(), 0)

    def test_promotion_writes_a_new_curated_tree_and_final_manifest(self):
        review = self.fixture.accepted_review()
        self.assertEqual(self.fixture.promote(review), 0)

        curated = self.fixture.curated
        self.assertTrue((curated / "thalamic-mini" / "batch-r02.jsonl").is_file())
        self.assertTrue((curated / "PROVENANCE.md").is_file())

        manifest = json.loads((curated / curate_gate.MANIFEST_FILENAME).read_text())
        self.assertTrue(manifest["training_ready"])
        self.assertEqual(manifest["blockers"], [])
        promotion = manifest["promotion"]
        self.assertEqual(promotion["curated_dir"], str(curated))
        self.assertEqual(promotion["records"], 4)
        self.assertTrue(promotion["corpus_digest"].startswith("sha256:"))
        emitted = {entry["path"] for entry in promotion["outputs"]}
        self.assertIn("thalamic-mini/batch-r02.jsonl", emitted)
        for entry in promotion["outputs"]:
            self.assertRegex(entry["sha256"], r"^[0-9a-f]{64}$")
        self.assertEqual(manifest["review"]["reviewer"], "curation-reviewer")
        self.assertEqual(
            manifest["review"]["sampled_records"], self.fixture.sample()["sampled_records"]
        )
        # Review evidence travels with the curated corpus.
        self.assertTrue((curated / curate_gate.SAMPLE_FILENAME).is_file())
        self.assertTrue((curated / curate_gate.REVIEW_FILENAME).is_file())

    def test_promotion_refuses_an_existing_curated_destination(self):
        review = self.fixture.accepted_review()
        self.fixture.curated.mkdir(parents=True)
        self.assertEqual(self.fixture.promote(review), 2)

    def test_promotion_refuses_an_unreviewed_sample(self):
        template = self.root / "unreviewed.json"
        template.write_text(
            (self.fixture.cleaned / curate_gate.REVIEW_FILENAME).read_text()
        )
        self.assertEqual(self.fixture.promote(template), 1)
        self.assertFalse(self.fixture.curated.exists())
        manifest = self.fixture.manifest()
        self.assertTrue(
            any(blocker.startswith("REVIEW_INCOMPLETE:") for blocker in manifest["blockers"])
        )
        self.assertIn("REVIEW_REVIEWER_MISSING", manifest["blockers"])

    def test_promotion_refuses_a_partially_reviewed_sample(self):
        review_path = self.fixture.accepted_review()
        review = json.loads(review_path.read_text())
        dropped = sorted(review["verdicts"])[0]
        review["verdicts"].pop(dropped)
        review_path.write_text(json.dumps(review))
        self.assertEqual(self.fixture.promote(review_path), 1)
        self.assertFalse(self.fixture.curated.exists())

    def test_promotion_refuses_when_a_sampled_record_is_rejected(self):
        review_path = self.fixture.accepted_review()
        review = json.loads(review_path.read_text())
        target = sorted(review["verdicts"])[0]
        review["verdicts"][target] = {"verdict": "reject", "notes": "invented measurement"}
        review_path.write_text(json.dumps(review))
        self.assertEqual(self.fixture.promote(review_path), 1)
        self.assertFalse(self.fixture.curated.exists())
        manifest = self.fixture.manifest()
        self.assertIn("REVIEW_REJECTED:1", manifest["blockers"])

    def test_promotion_refuses_a_review_bound_to_a_different_corpus(self):
        review_path = self.fixture.accepted_review()
        review = json.loads(review_path.read_text())
        review["corpus_digest"] = "sha256:" + "0" * 64
        review_path.write_text(json.dumps(review))
        self.assertEqual(self.fixture.promote(review_path), 1)
        manifest = self.fixture.manifest()
        self.assertIn("REVIEW_CORPUS_MISMATCH", manifest["blockers"])

    def test_promotion_refuses_after_the_corpus_changed_under_the_review(self):
        review = self.fixture.accepted_review()
        extra = self.fixture.cleaned / "thalamic-mini" / "batch-r03.jsonl"
        _write_jsonl(extra, [_thalamic("t-added-after-review")])
        self.assertEqual(self.fixture.promote(review), 1)
        self.assertFalse(self.fixture.curated.exists())
        manifest = self.fixture.manifest()
        self.assertIn("REVIEW_CORPUS_MISMATCH", manifest["blockers"])
        self.assertIn("SAMPLE_CORPUS_MISMATCH", manifest["blockers"])

    def test_promotion_requires_an_integrated_cleaned_destination(self):
        review = self.fixture.accepted_review()
        (self.fixture.cleaned / curate_gate.MANIFEST_FILENAME).unlink()
        self.assertEqual(self.fixture.promote(review), 2)

    def test_promotion_never_writes_into_the_cleaned_corpus(self):
        review = self.fixture.accepted_review()
        before = {
            path.relative_to(self.fixture.cleaned).as_posix(): curate_gate.file_sha256(path)
            for path in curate_gate.jsonl_paths(self.fixture.cleaned)
        }
        self.assertEqual(self.fixture.promote(review), 0)
        after = {
            path.relative_to(self.fixture.cleaned).as_posix(): curate_gate.file_sha256(path)
            for path in curate_gate.jsonl_paths(self.fixture.cleaned)
        }
        self.assertEqual(before, after)


class CommandLineTests(unittest.TestCase):
    def setUp(self):
        self._temp = tempfile.TemporaryDirectory(prefix="curate-gate-")
        self.addCleanup(self._temp.cleanup)
        self.root = Path(self._temp.name)

    def test_cli_integrate_then_promote(self):
        fixture = GateFixture(self.root)
        integrate = subprocess.run(
            [
                sys.executable,
                str(GATE_SCRIPT),
                "integrate",
                "--plan",
                str(fixture.plan_path),
                "--cleaned-out",
                str(fixture.cleaned),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(integrate.returncode, 0, integrate.stderr)
        summary = json.loads(integrate.stdout)
        self.assertTrue(summary["training_ready"])
        self.assertEqual(summary["gate_blockers"], [])

        review = fixture.accepted_review()
        promoted = subprocess.run(
            [
                sys.executable,
                str(GATE_SCRIPT),
                "promote",
                "--cleaned",
                str(fixture.cleaned),
                "--review",
                str(review),
                "--curated-out",
                str(fixture.curated),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(promoted.returncode, 0, promoted.stderr)
        result = json.loads(promoted.stdout)
        self.assertTrue(result["promoted"])
        self.assertEqual(result["records"], 4)


if __name__ == "__main__":
    unittest.main()
