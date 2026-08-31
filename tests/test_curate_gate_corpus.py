#!/usr/bin/env python3
"""Corpus-authentication tests for the curation integration gate."""

import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path

_TESTS = Path(__file__).resolve().parent
if str(_TESTS) not in sys.path:
    sys.path.insert(0, str(_TESTS))

from gate_fixture import (  # noqa: E402
    PIPELINES,
    GateFixture,
    _captured_main,
    _lane_manifest_entry,
    _read_jsonl,
    _reward_annotated,
    _thalamic,
    _write_jsonl,
)

if str(PIPELINES) not in sys.path:
    sys.path.insert(0, str(PIPELINES))

import curate_gate  # noqa: E402
import curate_rewards  # noqa: E402


class CorpusGateTests(unittest.TestCase):
    def setUp(self):
        self._temp = tempfile.TemporaryDirectory(prefix="curate-gate-")
        self.addCleanup(self._temp.cleanup)
        self.root = Path(self._temp.name)

    def test_exact_duplicate_records_block_the_gate(self):
        duplicate = _reward_annotated([_thalamic("t-dup")], "thalamic-mini/batch-r02.jsonl")[0]
        fixture = GateFixture(
            self.root,
            thalamic_records=[duplicate, json.loads(json.dumps(duplicate))],
            canonical_ids=False,
        )
        # The preference lane does not own these Thalamic records. Keep one
        # path-independent retained fixture record and explicitly skip the
        # second so its consolidated-output authentication does not mask the
        # later corpus-level exact-duplicate gate this test exercises.
        _write_jsonl(
            fixture.lane_preference / "thalamic-mini" / "batch-r02.jsonl",
            [duplicate],
        )
        fixture.sync_lane_manifest(
            2,
            extras=(
                _lane_manifest_entry(
                    "skipped",
                    2,
                    ["PREFERENCE_CONTEXT_NOT_OWNED"],
                    transform="same-context-preference-curation",
                    version="1.0.0",
                    source_path="thalamic-mini/batch-r02.jsonl",
                    source_hash=fixture.source_hash("thalamic-mini/batch-r02.jsonl", 2),
                ),
            ),
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
        fixture = GateFixture(
            self.root, thalamic_records=[first, second], canonical_ids=False
        )
        self.assertEqual(fixture.integrate(), 1)
        manifest = fixture.manifest()

        self.assertFalse(manifest["gates"]["canonical_id_collisions"]["passed"])
        self.assertTrue(manifest["gates"]["exact_duplicates"]["passed"])
        self.assertTrue(
            any(blocker.startswith("CANONICAL_ID_COLLISIONS:") for blocker in manifest["blockers"])
        )

    def test_records_without_canonical_top_level_ids_block_the_gate(self):
        anonymous = _thalamic("t-anon")
        anonymous.pop("id")
        anonymous["meta"].pop("id", None)
        fixture = GateFixture(
            self.root, thalamic_records=[anonymous], canonical_ids=False
        )
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

    def test_reward_bearing_record_without_ontology_annotation_blocks_the_gate(self):
        fixture = GateFixture(self.root)
        reward_output = fixture.lane_reward / "thalamic-mini" / "batch-r02.jsonl"
        records = [json.loads(line) for line in reward_output.read_text().split("\n") if line]
        records[0].pop("reward_training")
        _write_jsonl(reward_output, records)
        fixture.sync_lane_manifest(3)

        self.assertEqual(fixture.integrate(), 1)
        manifest = fixture.manifest()
        gate = manifest["gates"]["reward_ontology"]
        self.assertFalse(gate["passed"])
        self.assertEqual(gate["missing_annotations"], 1)
        self.assertFalse(manifest["training_ready"])
        self.assertTrue(
            any(blocker.startswith("REWARD_ONTOLOGY_COVERAGE:") for blocker in manifest["blockers"])
        )

    def test_invalid_reward_ontology_annotation_blocks_the_gate(self):
        fixture = GateFixture(self.root)
        reward_output = fixture.lane_reward / "thalamic-mini" / "batch-r02.jsonl"
        records = [json.loads(line) for line in reward_output.read_text().split("\n") if line]
        records[0]["reward_training"]["ontology_version"] = "unsafe-v0"
        _write_jsonl(reward_output, records)
        fixture.sync_lane_manifest(3)

        self.assertEqual(fixture.integrate(), 1)
        gate = fixture.manifest()["gates"]["reward_ontology"]
        self.assertFalse(gate["passed"])
        self.assertEqual(gate["invalid_annotations"], 1)

    def test_identity_replay_rejects_self_consistent_arbitrary_canonical_outputs(self):
        fixture = GateFixture(self.root)
        forged = "self-consistent-but-not-coordinate-derived"
        for lane_dir in (
            fixture.lane_core,
            fixture.lane_preference,
            fixture.lane_reward,
            fixture.lane_coding,
            fixture.lane_tag,
        ):
            path = lane_dir / "thalamic-mini" / "batch-r02.jsonl"
            records = _read_jsonl(path)
            records[0]["id"] = forged
            _write_jsonl(path, records)
        for index in range(len(fixture.lanes)):
            fixture.sync_lane_manifest(index)

        self.assertEqual(fixture.integrate(), 1)
        gate = fixture.manifest()["gates"]["identity_mappings"]
        self.assertFalse(gate["passed"])
        self.assertTrue(
            any(
                "deterministic canonical identity" in item["error"]
                for item in gate["examples"]
            )
        )

    def test_retained_identity_id_mapping_must_resolve_to_final_record(self):
        fixture = GateFixture(self.root)
        entries = json.loads(fixture.manifest_paths[1].read_text())
        entries[0]["id_mappings"][0]["output_id"] = "forged-mapped-id"
        fixture.manifest_paths[1].write_text(json.dumps(entries))

        self.assertEqual(fixture.integrate(), 1)
        gate = fixture.manifest()["gates"]["identity_mappings"]
        self.assertFalse(gate["passed"])
        self.assertTrue(
            any(
                "output_id does not match output owner" in item["error"]
                for item in gate["examples"]
            )
        )

    def test_retained_provenance_mapping_must_match_final_record(self):
        fixture = GateFixture(self.root)
        entries = json.loads(fixture.manifest_paths[1].read_text())
        entries[0]["provenance_mappings"][0]["canonical"]["basis"] = "forged"
        fixture.manifest_paths[1].write_text(json.dumps(entries))

        self.assertEqual(fixture.integrate(), 1)
        gate = fixture.manifest()["gates"]["identity_mappings"]
        self.assertFalse(gate["passed"])
        self.assertTrue(
            any(
                "canonical does not match output provenance" in item["error"]
                for item in gate["examples"]
            )
        )

    def test_retained_identity_original_ids_must_match_source_record(self):
        fixture = GateFixture(self.root)
        entries = json.loads(fixture.manifest_paths[1].read_text())
        entries[0]["id_mappings"][0]["original_ids"][0]["value"] = "forged-original"
        fixture.manifest_paths[1].write_text(json.dumps(entries), encoding="utf-8")

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
        self.assertIn("original identity evidence does not match the source record", stderr)
        self.assertFalse(fixture.cleaned.exists())

    def test_retained_identity_original_provenance_must_match_source_record(self):
        fixture = GateFixture(self.root)
        entries = json.loads(fixture.manifest_paths[1].read_text())
        entries[0]["provenance_mappings"][0]["original"]["owner_provenance"] = {
            "present": True,
            "value": {"kind": "forged"},
        }
        fixture.manifest_paths[1].write_text(json.dumps(entries), encoding="utf-8")

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
        self.assertIn("original identity evidence does not match the source record", stderr)
        self.assertFalse(fixture.cleaned.exists())

    def test_retained_identity_mapping_must_cover_every_nested_owner(self):
        fixture = GateFixture(self.root)
        entries = json.loads(fixture.manifest_paths[1].read_text())
        preference = next(
            entry
            for entry in entries
            if entry["source_path"] == "thalamic-mini/batch-r02.jsonl" and entry["source_line"] == 2
        )
        preference["id_mappings"] = [
            mapping for mapping in preference["id_mappings"] if mapping["owner_path"] == "/"
        ]
        preference["provenance_mappings"] = [
            mapping
            for mapping in preference["provenance_mappings"]
            if mapping["owner_path"] == "/" and mapping.get("state_path") is None
        ]
        fixture.manifest_paths[1].write_text(json.dumps(entries), encoding="utf-8")

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
        self.assertIn("or is incomplete", stderr)
        self.assertFalse(fixture.cleaned.exists())

    def test_every_retained_record_requires_identity_lane_evidence(self):
        fixture = GateFixture(self.root)
        identity_bridge = fixture.lane_core / "bridge-factory" / "batch-r02.jsonl"
        identity_bridge.unlink()
        fixture.sync_lane_manifest(1)

        self.assertEqual(fixture.integrate(), 1)
        gate = fixture.manifest()["gates"]["identity_mappings"]
        self.assertFalse(gate["passed"])
        self.assertTrue(
            any(
                "retained record has no authenticated identity mapping" in item["error"]
                for item in gate["examples"]
            )
        )

    def test_external_calibration_is_authenticated_from_the_migration_catalog(self):
        record = {
            "id": "ffpc-r2-001",
            "chosen": {
                "reward_components": {
                    "task_progress": 3.0,
                    "safety": 0.6,
                    "total": 3.6,
                    "units": "1.0 = $2,000; audited_true_reward basis",
                }
            },
            "rejected": {
                "reward_components": {
                    "task_progress": 0.2,
                    "safety": -0.8,
                    "total": -0.6,
                    "units": "1.0 = $2,000; risk-adjusted terms",
                }
            },
            "critique": "chosen is preferred on observable process evidence",
        }
        calibration = {
            "source_unit_usd": 2000,
            "canonical_factor": 0.2,
            "evidence_ref": "units-migration.json#/records/1",
        }
        curated, sidecar = curate_rewards.curate_record(
            record, source_path="ffpc/preferences.jsonl", source_line=1, calibration=calibration
        )
        catalog = {"ffpc-r2-001": calibration}

        derived = curate_gate._derived_reward_contract(  # noqa: SLF001
            curated, sidecar, catalog, record
        )
        self.assertEqual(derived["classification"]["comparability"], "magnitude_comparable")
        self.assertIn(
            "external_calibration_evidence",
            derived["classification"]["reason_codes"],
        )

        with self.assertRaisesRegex(
            curate_rewards.RewardOntologyError,
            "no matching record in the migration artifact",
        ):
            curate_gate._derived_reward_contract(curated, sidecar, {}, record)  # noqa: SLF001

    def test_migration_catalog_does_not_require_calibration_on_excluded_records(self):
        units = "1.0 reward unit = USD 10,000 (risk-adjusted); deltas vs baseline"
        record = {
            "id": "ffpc-r2-042",
            "chosen": {
                "reward_components": {
                    "task_progress": 1.0,
                    "safety": 0.0,
                    "total": 1.0,
                    "unit_usd": 10000,
                    "units": units,
                }
            },
            "rejected": {
                "reward_components": {
                    "task_progress": 0.0,
                    "safety": 0.0,
                    "total": 0.0,
                    "unit_usd": 10000,
                    "units": units,
                }
            },
        }
        artifact = {
            "source_unit_usd": 2000,
            "canonical_factor": 0.2,
            "evidence_ref": "units-migration.json#/records/9",
        }
        curated, sidecar = curate_rewards.curate_record(
            record,
            source_path="ffpc/preferences.jsonl",
            source_line=1,
            calibration=artifact,
        )
        self.assertEqual(
            curated["reward_training"]["comparability"],
            "sign_order_only",
        )
        self.assertNotIn("calibration", sidecar)
        catalog = {"ffpc-r2-042": artifact}
        derived = curate_gate._derived_reward_contract(  # noqa: SLF001
            curated, sidecar, catalog, record
        )
        self.assertEqual(
            derived["classification"]["comparability"],
            "sign_order_only",
        )

    def test_excluded_reward_class_is_valid_gate_coverage(self):
        fixture = GateFixture(self.root)
        self.assertEqual(fixture.integrate(), 0)
        gate = fixture.manifest()["gates"]["reward_ontology"]

        self.assertTrue(gate["passed"])
        self.assertEqual(gate["reward_bearing_records"], 4)
        self.assertEqual(gate["annotated_records"], 4)
        self.assertGreater(gate["comparability"]["exclude_from_reward_training"], 0)

    def test_dangling_reward_sidecar_reference_blocks_the_gate(self):
        fixture = GateFixture(self.root)
        sidecar_path = fixture.lane_reward / "reward-sidecars.jsonl"
        documents = [line for line in sidecar_path.read_text().split("\n") if line.strip()]
        sidecar_path.write_text("\n".join(documents[1:]) + "\n")

        self.assertEqual(fixture.integrate(), 1)
        gate = fixture.manifest()["gates"]["reward_sidecars"]
        self.assertFalse(gate["passed"])
        self.assertEqual(gate["missing_sidecars"], 1)
        self.assertTrue(
            any(
                blocker.startswith("REWARD_SIDECAR_AUTHENTICATION:")
                for blocker in fixture.manifest()["blockers"]
            )
        )

    def test_tampered_reward_sidecar_is_rejected_before_publication(self):
        fixture = GateFixture(self.root)
        sidecar_path = fixture.lane_reward / "reward-sidecars.jsonl"
        documents = _read_jsonl(sidecar_path)
        documents[0]["classification"]["reason_codes"] = ["tampered"]
        _write_jsonl(sidecar_path, documents)

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
        self.assertIn("sidecar_id content hash mismatch", stderr)
        self.assertFalse(fixture.cleaned.exists())

    def test_self_consistent_sidecar_still_authenticates_its_embedded_reward_value(self):
        fixture = GateFixture(self.root)
        reward_output = fixture.lane_reward / "thalamic-mini" / "batch-r02.jsonl"
        records = [json.loads(line) for line in reward_output.read_text().split("\n") if line]
        old_id = records[0]["reward_training"]["source_sidecar_id"]

        sidecar_path = fixture.lane_reward / "reward-sidecars.jsonl"
        documents = _read_jsonl(sidecar_path)
        target = next(document for document in documents if document["sidecar_id"] == old_id)
        target["source_rewards"][0]["value"] = "forged but self-consistently sealed"
        body = dict(target)
        body.pop("sidecar_id")
        target["sidecar_id"] = "sha256:" + curate_gate.record_sha256(body)
        records[0]["reward_training"]["source_sidecar_id"] = target["sidecar_id"]
        _write_jsonl(sidecar_path, documents)
        _write_jsonl(reward_output, records)
        fixture.sync_lane_manifest(3)

        self.assertEqual(fixture.integrate(), 1)
        gate = fixture.manifest()["gates"]["reward_sidecars"]
        self.assertFalse(gate["passed"])
        self.assertGreaterEqual(gate["invalid_links"], 1)
        self.assertTrue(
            any(
                "source_rewards do not match independently enumerated reward values"
                in item["error"]
                for item in gate["examples"]
            )
        )

    def test_forged_reward_keeping_original_source_digest_is_rejected(self):
        fixture = GateFixture(self.root)
        reward_output = fixture.lane_reward / "thalamic-mini" / "batch-r02.jsonl"
        records = _read_jsonl(reward_output)
        old_id = records[0]["reward_training"]["source_sidecar_id"]
        sidecar_path = fixture.lane_reward / "reward-sidecars.jsonl"
        documents = _read_jsonl(sidecar_path)
        target = next(document for document in documents if document["sidecar_id"] == old_id)
        original_digest = target["source"]["record_sha256"]
        forged = 0.8
        if isinstance(records[0].get("reward_components"), dict):
            records[0]["reward_components"]["task_progress"] = forged
            records[0]["reward_components"]["total"] = forged
        for reward in target["source_rewards"]:
            pointer = reward.get("json_pointer")
            if pointer == "/reward_components":
                reward["value"] = copy.deepcopy(records[0]["reward_components"])
            elif pointer in ("/reward_components/task_progress", "/reward_components/total"):
                reward["value"] = forged
            reward["value_sha256"] = "sha256:" + curate_gate.record_sha256(reward["value"])
        target["source"]["record_sha256"] = original_digest
        body = dict(target)
        body.pop("sidecar_id")
        target["sidecar_id"] = "sha256:" + curate_gate.record_sha256(body)
        records[0]["reward_training"]["source_sidecar_id"] = target["sidecar_id"]
        _write_jsonl(sidecar_path, documents)
        _write_jsonl(reward_output, records)
        fixture.sync_lane_manifest(3)

        self.assertEqual(fixture.integrate(), 1)
        gate = fixture.manifest()["gates"]["reward_sidecars"]
        self.assertFalse(gate["passed"])
        self.assertTrue(
            any(
                "authenticated source" in item["error"]
                or "independent" in item["error"]
                for item in gate["examples"]
            )
        )

    def test_self_resealed_forged_reward_class_fails_independent_derivation(self):
        fixture = GateFixture(self.root)
        reward_output = fixture.lane_reward / "thalamic-mini" / "batch-r02.jsonl"
        records = _read_jsonl(reward_output)
        annotation = records[0]["reward_training"]
        old_id = annotation["source_sidecar_id"]

        sidecar_path = fixture.lane_reward / "reward-sidecars.jsonl"
        documents = _read_jsonl(sidecar_path)
        target = next(document for document in documents if document["sidecar_id"] == old_id)
        forged_reasons = [
            "explicit_usd_unit_calibration",
            "reward_arithmetic_verified",
        ]
        target["classification"] = {
            "comparability": curate_rewards.MAGNITUDE_COMPARABLE,
            "reason_codes": list(forged_reasons),
        }
        body = dict(target)
        body.pop("sidecar_id")
        target["sidecar_id"] = "sha256:" + curate_gate.record_sha256(body)
        annotation.update(
            {
                "comparability": curate_rewards.MAGNITUDE_COMPARABLE,
                "reason_codes": list(forged_reasons),
                "source_sidecar_id": target["sidecar_id"],
                "magnitude": {
                    "canonical_unit": curate_rewards.CANONICAL_UNIT,
                    "aggregation": "linear_unit_conversion_only",
                    "values": [
                        {
                            "json_pointer": "/reward_components",
                            "source_total": 0.5,
                            "source_unit_usd": 10000,
                            "conversion_factor": 1,
                            "canonical_value": 0.5,
                        }
                    ],
                },
            }
        )
        annotation.pop("order", None)
        curate_rewards.validate_ontology_document(annotation)
        curate_rewards.validate_ontology_document(target)
        _write_jsonl(sidecar_path, documents)
        _write_jsonl(reward_output, records)
        fixture.sync_lane_manifest(3)

        self.assertEqual(fixture.integrate(), 1)
        gate = fixture.manifest()["gates"]["reward_sidecars"]
        self.assertFalse(gate["passed"])
        self.assertTrue(
            any(
                "classification does not match independent derivation" in item["error"]
                for item in gate["examples"]
            )
        )

    def test_same_reward_sidecar_swap_fails_source_identity_binding(self):
        fixture = GateFixture(
            self.root,
            thalamic_records=[_thalamic("same-reward-a"), _thalamic("same-reward-b")],
        )
        reward_output = fixture.lane_reward / "thalamic-mini" / "batch-r02.jsonl"
        records = _read_jsonl(reward_output)
        first_id = records[0]["reward_training"]["source_sidecar_id"]
        second_id = records[1]["reward_training"]["source_sidecar_id"]
        records[0]["reward_training"]["source_sidecar_id"] = second_id
        records[1]["reward_training"]["source_sidecar_id"] = first_id
        _write_jsonl(reward_output, records)
        fixture.sync_lane_manifest(3)

        self.assertEqual(fixture.integrate(), 1)
        gate = fixture.manifest()["gates"]["reward_sidecars"]
        self.assertFalse(gate["passed"])
        self.assertGreaterEqual(gate["invalid_links"], 2)
        self.assertTrue(
            sum(
                "source identity mismatches final record binding" in item["error"]
                for item in gate["examples"]
            )
            == 2
        )



if __name__ == '__main__':
    unittest.main()
