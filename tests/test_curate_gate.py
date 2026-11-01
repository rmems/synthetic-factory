#!/usr/bin/env python3
"""Tests for pipelines/curate_gate.py — the sf-c5l.7 integration/promotion gate.

This module covers what `integrate` composes and records: the record-level
composition of the six lanes into one cleaned tree, the manifest's counts,
hashes, exclusions, quarantines, repairs, identity mappings and review
candidates, and the rights gate verdict that keeps the result out of training.
Plan loading, lane authentication, the cleaned destination and evidence
snapshots live in the sibling test_curate_gate_*.py modules.
"""

import copy
import json
import sys
import unittest
from pathlib import Path
from unittest import mock

_TESTS = Path(__file__).resolve().parent
if str(_TESTS) not in sys.path:
    sys.path.insert(0, str(_TESTS))

from curate_gate_test_support import required_item, temp_root  # noqa: E402
from gate_fixture import (  # noqa: E402
    PIPELINES,
    GateFixture,
    _bridge,
    _captured_main,
    _lane_manifest_entry,
    _read_jsonl,
    _write_jsonl,
)

if str(PIPELINES) not in sys.path:
    sys.path.insert(0, str(PIPELINES))

import curate_gate  # noqa: E402
import curate_gate_gates  # noqa: E402
import curate_rewards  # noqa: E402


class IntegrationTests(unittest.TestCase):
    def setUp(self):
        self.root = temp_root(self)

    def test_integrate_composes_legacy_lanes_but_refuses_training(self):
        fixture = GateFixture(self.root)
        self.assertEqual(fixture.integrate(), 1)

        manifest = fixture.manifest()
        self.assertEqual(manifest["schema"], curate_gate.MANIFEST_SCHEMA)
        self.assertFalse(manifest["training_ready"])
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
            "output_evidence",
            "identity_mappings",
            "structural_validator",
            "record_invariants",
            "training_audit",
            "exact_duplicates",
            "canonical_id_collisions",
            "canonical_id_coverage",
            "reward_ontology",
            "reward_sidecars",
            "factory_label",
        ):
            self.assertTrue(manifest["gates"][gate]["passed"], gate)
        self.assertFalse(manifest["gates"]["rights"]["passed"])
        self.assertTrue(manifest["blockers"])
        # Composition happened, and both lane trees landed under one destination.
        self.assertTrue((fixture.cleaned / "bridge-factory" / "batch-r02.jsonl").is_file())
        self.assertTrue((fixture.cleaned / "thalamic-mini" / "batch-r02.jsonl").is_file())

    def test_terminal_record_repairs_replay_without_summary_drift(self):
        # Isolate repaired-record summary replay from the independent rights decision.
        self.enterContext(mock.patch.object(curate_gate_gates, "evaluate_rights",
            return_value=({"passed": True, "enforced": False}, [])))
        fixture = GateFixture(self.root)
        repaired_entries = json.loads(fixture.manifest_paths[1].read_text())
        repaired = required_item(entry for entry in repaired_entries if entry["source_line"] == 3)
        repaired["action"] = "repaired"
        repaired["reason_codes"] = ["IDENTITY_REPAIR"]
        fixture.manifest_paths[1].write_text(
            json.dumps(repaired_entries, indent=2) + "\n",
            encoding="utf-8",
        )

        tag_path = fixture.lane_tag / "thalamic-mini" / "batch-r02.jsonl"
        tag_records = _read_jsonl(tag_path)
        _write_jsonl(tag_path, tag_records[:2])
        fixture.sync_lane_manifest(
            5,
            extras=(
                _lane_manifest_entry(
                    "excluded",
                    3,
                    ["TAG_RECORD_EXCLUDED"],
                    transform="tag_taxonomy",
                    version="1",
                    source_path="thalamic-mini/batch-r02.jsonl",
                    source_hash=fixture.source_hash("thalamic-mini/batch-r02.jsonl", 3),
                ),
            ),
        )

        self.assertEqual(fixture.integrate(), 0)
        repair = required_item(
            entry
            for entry in fixture.manifest()["repairs"]
            if entry["source_path"] == "thalamic-mini/batch-r02.jsonl" and entry["source_line"] == 3
        )
        self.assertNotIn("content_changed", repair)

        review = fixture.accepted_review()
        code, report, stderr = fixture.promote_report(review)
        self.assertEqual(code, 0, stderr)
        self.assertTrue(report["promoted"])

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
        source_record = json.loads(source.read_text().split("\n")[0])
        emitted_record = json.loads(emitted.read_text().split("\n")[0])
        self.assertNotIn(curate_rewards.ANNOTATION_FIELD, source_record)
        self.assertIn(curate_rewards.ANNOTATION_FIELD, emitted_record)
        emitted_without_reward = copy.deepcopy(emitted_record)
        emitted_without_reward.pop(curate_rewards.ANNOTATION_FIELD)

        def without_provenance(value):
            if isinstance(value, dict):
                return {
                    key: without_provenance(item)
                    for key, item in value.items()
                    if key != "provenance"
                }
            if isinstance(value, list):
                return [without_provenance(item) for item in value]
            return value

        self.assertEqual(
            without_provenance(source_record),
            without_provenance(emitted_without_reward),
        )

        self.assertEqual(len(manifest["exclusions"]), 1)
        self.assertEqual(manifest["exclusions"][0]["reason_codes"], ["INVALID_JSON"])
        self.assertEqual(manifest["exclusions"][0]["source_line"], 3)
        self.assertEqual(len(manifest["quarantines"]), 1)
        self.assertEqual(manifest["quarantines"][0]["reason_codes"], ["AMBIGUOUS_EVENT_ORDER"])
        self.assertEqual(manifest["counts"]["exclusions"], 1)
        self.assertEqual(manifest["counts"]["quarantines"], 1)
        self.assertEqual(
            manifest["counts"]["lane_actions"]["bridge_event_time_order"],
            {"excluded": 1, "quarantine": 1, "retained": 1},
        )
        self.assertEqual(
            manifest["lanes_without_record_manifest"],
            [],
        )
        self.assertEqual(len(manifest["lane_evidence"]), 6)

    def test_changed_output_claiming_retained_is_still_a_review_candidate(self):
        fixture = GateFixture(self.root)
        tag_output = fixture.lane_tag / "thalamic-mini" / "batch-r02.jsonl"
        records = _read_jsonl(tag_output)
        records[0]["state"]["env"] = "normalized by the tag lane"
        _write_jsonl(tag_output, records)
        fixture.sync_lane_manifest(5)

        self.assertEqual(fixture.integrate("--per-stratum", "100"), 1)
        manifest = fixture.manifest()
        changed = [
            candidate
            for candidate in manifest["review_candidates"]
            if candidate.get("transform") == "tag_taxonomy"
            and candidate.get("source_path") == "thalamic-mini/batch-r02.jsonl"
            and candidate.get("source_line") == 1
        ]

        self.assertEqual(len(changed), 1)
        self.assertEqual(changed[0]["action"], "retained")
        self.assertTrue(changed[0]["content_changed"])
        self.assertEqual(changed[0]["review_action"], "changed")
        self.assertEqual(
            changed[0]["review_reason_codes"],
            [curate_gate.DERIVED_CHANGE_REASON],
        )
        sampled = [
            item
            for item in fixture.sample()["items"]
            if item.get("manifest_entry", {}).get("transform") == "tag_taxonomy"
            and item.get("manifest_entry", {}).get("source_line") == 1
        ]
        self.assertEqual(len(sampled), 1)
        self.assertEqual(sampled[0]["decision"], "changed")

    def test_manifest_preserves_complete_retained_identity_mappings(self):
        fixture = GateFixture(self.root)
        self.assertEqual(fixture.integrate(), 1)

        mappings = fixture.manifest()["identity_mappings"]
        self.assertEqual(len(mappings), 4)
        for mapping in mappings:
            self.assertEqual(mapping["action"], "retained")
            self.assertEqual(mapping["transform"], "curate_identity")
            self.assertEqual(mapping["version"], "identity-provenance-v1")
            self.assertTrue(mapping["id_mappings"])
            self.assertTrue(mapping["provenance_mappings"])
            self.assertRegex(mapping["manifest_entry_sha256"], r"^[0-9a-f]{64}$")

    def test_manifest_normalizes_nested_identity_provenance_fields(self):
        fixture = GateFixture(self.root)
        entries = json.loads(fixture.manifest_paths[1].read_text())
        entry_index = required_item(
            index
            for index, entry in enumerate(entries)
            if entry["source_path"] == "thalamic-mini/batch-r02.jsonl" and entry["source_line"] == 1
        )
        source_hash = entries[entry_index]["source_hash"]
        identity_output = fixture.lane_core / "thalamic-mini" / "batch-r02.jsonl"
        identity_records = [
            json.loads(line) for line in identity_output.read_text().split("\n") if line
        ]
        _write_jsonl(identity_output, identity_records[1:])
        entries[entry_index] = {
            "transform": {
                "name": "curate_identity",
                "version": "identity-provenance-v1",
            },
            "source": {
                "path": "thalamic-mini/batch-r02.jsonl",
                "line": 1,
                "sha256": source_hash,
            },
            "record_kind": "thalamic",
            "action": "exclude",
            "reason_codes": ["IDENTITY_UNRESOLVED"],
            "output_sha256": None,
        }
        fixture.manifest_paths[1].write_text(json.dumps(entries))

        self.assertEqual(fixture.integrate(), 1)
        entry = required_item(
            item
            for item in fixture.manifest()["exclusions"]
            if item["transform"] == "curate_identity"
        )
        self.assertEqual(entry["source_path"], "thalamic-mini/batch-r02.jsonl")
        self.assertEqual(entry["source_line"], 1)
        self.assertEqual(entry["source_hash"], source_hash)
        self.assertIsNone(entry["output_hash"])

    def test_manifest_preserves_repaired_record_provenance(self):
        fixture = GateFixture(self.root)
        entries = json.loads(fixture.manifest_paths[2].read_text())
        source_hash = entries[1]["source_hash"]
        entries[1]["action"] = "repaired"
        entries[1]["reason_codes"] = ["BRANCH_ONLY_PROPOSAL_ANNOTATION_REMOVED"]
        fixture.manifest_paths[2].write_text(json.dumps(entries))

        self.assertEqual(fixture.integrate(), 1)
        manifest = fixture.manifest()
        self.assertEqual(len(manifest["repairs"]), 1)
        repair = manifest["repairs"][0]
        self.assertEqual(repair["source_hash"], source_hash)
        self.assertRegex(repair["output_hash"], r"^[0-9a-f]{64}$")
        self.assertEqual(manifest["counts"]["repairs"], 1)
        self.assertIn(repair, manifest["review_candidates"])

    def test_later_lane_supersedes_earlier_lane_at_the_same_path(self):
        fixture = GateFixture(self.root)
        identity_records = _read_jsonl(
            fixture.lane_core / "bridge-factory" / "batch-r02.jsonl"
        )
        identity_records[0]["bridge_notes"] = {
            "mapping": "identity-supersede",
            "training_value": "routing",
        }
        _write_jsonl(
            fixture.lane_core / "bridge-factory" / "batch-r02.jsonl",
            identity_records,
        )
        fixture.sync_lane_manifest(1)
        self.assertEqual(fixture.integrate(), 1)
        manifest = fixture.manifest()

        supersession = required_item(
            item
            for item in manifest["supersessions"]
            if item["source_path"] == "bridge-factory/batch-r02.jsonl"
        )
        self.assertEqual(supersession["source_line"], 1)
        self.assertEqual(supersession["superseded_transform"], "bridge_event_time_order")
        self.assertEqual(supersession["winning_transform"], "curate_identity")
        emitted = (fixture.cleaned / "bridge-factory" / "batch-r02.jsonl").read_text()
        self.assertIn("identity-supersede", emitted)
        self.assertEqual(fixture.manifest()["counts"]["records"], 4)

    def test_record_level_composition_preserves_unrelated_records_in_the_same_file(self):
        fixture = GateFixture(
            self.root,
            bridge_records=[_bridge("bridge-1"), _bridge("bridge-2")],
        )
        fixture.sync_lane_manifest(
            0,
            extras=(
                _lane_manifest_entry("quarantine", 3, ["AMBIGUOUS_EVENT_ORDER"]),
                _lane_manifest_entry("excluded", 4, ["INVALID_JSON"]),
            ),
        )
        identity_path = fixture.lane_core / "bridge-factory" / "batch-r02.jsonl"
        identity_records = _read_jsonl(identity_path)
        first = copy.deepcopy(identity_records[0])
        first["bridge_notes"] = {
            "mapping": "bridge-1-identity-rewrite",
            "training_value": "routing",
        }
        identity_records[0] = first
        _write_jsonl(identity_path, identity_records)
        fixture.sync_lane_manifest(1)

        self.assertEqual(fixture.integrate(), 1)
        emitted = _read_jsonl(fixture.cleaned / "bridge-factory" / "batch-r02.jsonl")
        self.assertEqual(
            emitted[0]["bridge_notes"]["mapping"],
            "bridge-1-identity-rewrite",
        )
        self.assertNotEqual(
            emitted[1].get("bridge_notes", {}).get("mapping"),
            "bridge-1-identity-rewrite",
        )
        self.assertEqual(fixture.manifest()["counts"]["records"], 5)

    def test_same_source_record_composes_independent_identity_and_reward_fields(self):
        fixture = GateFixture(self.root)
        source_record = json.loads(
            (fixture.source_run / "thalamic-mini" / "batch-r02.jsonl").read_text().split("\n")[0]
        )

        identity_path = fixture.lane_core / "thalamic-mini" / "batch-r02.jsonl"
        identity_records = [
            json.loads(line) for line in identity_path.read_text().split("\n") if line
        ]
        identity_record = copy.deepcopy(identity_records[0])
        identity_record["meta"]["provenance"] = {
            "kind": "simulated",
            "generator": "fixture",
        }
        expected_id = identity_record["id"]
        identity_records[0] = identity_record
        _write_jsonl(identity_path, identity_records)
        fixture.sync_lane_manifest(1)

        preference_path = fixture.lane_preference / "thalamic-mini" / "batch-r02.jsonl"
        preference_records = [
            json.loads(line) for line in preference_path.read_text().split("\n") if line
        ]
        preference_records[0] = copy.deepcopy(source_record)
        _write_jsonl(preference_path, preference_records)
        fixture.sync_lane_manifest(2)

        self.assertEqual(fixture.integrate(), 1)
        final_record = json.loads(
            (fixture.cleaned / "thalamic-mini" / "batch-r02.jsonl").read_text().split("\n")[0]
        )
        self.assertEqual(final_record["id"], expected_id)
        self.assertEqual(
            final_record["meta"]["provenance"],
            {"kind": "simulated", "generator": "fixture"},
        )
        self.assertIn(curate_rewards.ANNOTATION_FIELD, final_record)

    def test_same_source_conflicting_field_mutations_fail_closed(self):
        fixture = GateFixture(self.root)
        for lane_index, value in ((1, "identity-value"), (2, "preference-value")):
            lane_path = fixture.lanes[lane_index][0] / "thalamic-mini" / "batch-r02.jsonl"
            records = [json.loads(line) for line in lane_path.read_text().split("\n") if line]
            records[0]["state"]["env"] = value
            _write_jsonl(lane_path, records)
            fixture.sync_lane_manifest(lane_index)

        code, _report, stderr = _captured_main(
            [
                "integrate",
                "--plan",
                str(fixture.plan_path),
                "--cleaned-out",
                str(fixture.cleaned),
            ]
        )
        self.assertEqual(code, 2)
        self.assertIn("conflicts with an earlier lane", stderr)
        self.assertFalse(fixture.cleaned.exists())

    def test_integrate_rejects_a_non_positive_sample_size(self):
        fixture = GateFixture(self.root)
        self.assertEqual(fixture.integrate("--per-stratum", "0"), 2)
        self.assertFalse(fixture.cleaned.exists())


class RightsGateTests(unittest.TestCase):
    def test_unauthenticated_research_envelope_blocks_the_gate(self):
        log = curate_gate_gates._GateLog({}, [])
        mapping = {
            "action": "retained",
            "rights": {
                "intended_use": "research_only",
                "project_training_policy": "blocked",
                "provider_training_status": "blocked",
                "source_sha256": "sha256:" + ("a" * 64),
                "factory_registry_sha256": "sha256:" + ("b" * 64),
            },
        }
        curate_gate_gates._rights_gate([mapping], log)
        self.assertTrue(log.gates["rights"]["enforced"])
        self.assertFalse(log.gates["rights"]["passed"])
        self.assertTrue(
            any(item.startswith("RIGHTS_INVALID_ENVELOPE:") for item in log.blockers),
            log.blockers,
        )

    def test_forged_allowed_envelope_requires_authenticated_source(self):
        log = curate_gate_gates._GateLog({}, [])
        envelope = {
            "authority": "procedural", "intended_use": "training_candidate",
            "project_training_policy": "allowed", "provider_training_status": "allowed",
            "eligible_training_candidate": True,
            **{field: "sha256:" + "a" * 64 for field in (
                "source_sha256", "factory_registry_sha256", "procedural_policy_sha256",
                "catalog_sha256", "programs_sha256")},
        }
        curate_gate_gates._rights_gate([{"action": "retained", "rights": envelope}], log)
        self.assertFalse(log.gates["rights"]["passed"])
        self.assertTrue(log.blockers)

    def test_mappings_without_envelopes_fail_closed(self):
        log = curate_gate_gates._GateLog({}, [])
        curate_gate_gates._rights_gate([{"action": "retained", "output_id": "x"}], log)
        self.assertTrue(log.gates["rights"]["enforced"])
        self.assertFalse(log.gates["rights"]["passed"])
        self.assertTrue(log.blockers)


if __name__ == '__main__':
    unittest.main()
