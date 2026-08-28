#!/usr/bin/env python3
"""Focused tests for reward ontology v1 and conservative conversion."""

import copy
import hashlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from contextlib import redirect_stdout

REPO = Path(__file__).resolve().parents[1]
PIPELINES = REPO / "pipelines"
SCHEMA = REPO / "schemas" / "reward-ontology-v1.schema.json"
sys.path.insert(0, str(PIPELINES))

import curate_gate  # noqa: E402
import curate_rewards  # noqa: E402


def rich(value):
    return {"value": value, "detail": "fixture evidence"}


def components(total, *, unit_usd=None, units=None, rich_values=False):
    values = {
        "task_progress": 1.2,
        "safety": -0.4,
        "efficiency": 0.2,
    }
    if rich_values:
        values = {key: rich(value) for key, value in values.items()}
    values["total"] = total
    if unit_usd is not None:
        values["unit_usd"] = unit_usd
    if units is not None:
        values["units"] = units
    return values


def preference(chosen_reward, rejected_reward):
    return {
        "id": "pref-fixture",
        "chosen": {"reward_components": chosen_reward},
        "rejected": {"reward_components": rejected_reward},
        "critique": "chosen is preferred on observable process evidence",
    }


def write_jsonl(path, records):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(
            json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n"
            for record in records
        ),
        encoding="utf-8",
    )


class RewardOntologyV1Tests(unittest.TestCase):
    def test_schema_declares_exclusive_comparability_classes(self):
        schema = json.loads(SCHEMA.read_text())
        annotation = schema["$defs"]["annotation"]
        self.assertEqual(
            annotation["properties"]["comparability"]["enum"],
            [
                "magnitude_comparable",
                "sign_order_only",
                "exclude_from_reward_training",
            ],
        )
        self.assertEqual(
            annotation["properties"]["magnitude"]["properties"]["canonical_unit"]["const"],
            "usd_10000_risk_adjusted_delta",
        )
        self.assertEqual(len(annotation["allOf"]), 2)

    def test_structured_usd_rich_preference_is_magnitude_comparable(self):
        units = "1.0 reward unit = USD 10,000 (risk-adjusted); deltas vs baseline"
        record = preference(
            components(1.0, unit_usd=10000, units=units, rich_values=True),
            components(-1.0, unit_usd=10000, units=units, rich_values=True),
        )
        record["rejected"]["reward_components"]["task_progress"] = rich(-1.2)
        record["rejected"]["reward_components"]["safety"] = rich(0.0)
        record["rejected"]["reward_components"]["efficiency"] = rich(0.2)

        curated, sidecar = curate_rewards.curate_record(
            record, source_path="factory/batch-r03.jsonl", source_line=2
        )

        annotation = curated["reward_training"]
        self.assertEqual(annotation["comparability"], "magnitude_comparable")
        magnitudes = curate_rewards.canonical_magnitudes(curated)
        self.assertEqual(magnitudes["/chosen/reward_components"], 1.0)
        self.assertEqual(magnitudes["/rejected/reward_components"], -1.0)
        self.assertEqual(len(sidecar["source_rewards"]), 2)
        self.assertTrue(all(item["status"] == "valid" for item in sidecar["arithmetic"]))
        self.assertEqual(record["chosen"]["reward_components"], curated["chosen"]["reward_components"])

    def test_text_only_legacy_usd_unit_converts_to_canonical_scale(self):
        chosen = {
            "task_progress": 3.0,
            "safety": 0.6,
            "total": 3.6,
            "units": "1.0 = $2,000; risk-adjusted terms priced by audit",
        }
        rejected = {
            "task_progress": 0.2,
            "safety": -0.8,
            "total": -0.6,
            "units": "1.0 = $2,000; risk-adjusted terms priced by audit",
        }
        curated, _ = curate_rewards.curate_record(preference(chosen, rejected))

        values = curated["reward_training"]["magnitude"]["values"]
        by_pointer = {value["json_pointer"]: value for value in values}
        self.assertEqual(
            by_pointer["/chosen/reward_components"]["conversion_factor"], 0.2
        )
        self.assertEqual(
            by_pointer["/chosen/reward_components"]["canonical_value"], 0.72
        )

    def test_explicit_migration_evidence_calibrates_a_partially_labeled_pair(self):
        record = preference(
            {
                "task_progress": 3.0,
                "safety": 0.6,
                "total": 3.6,
                "units": "1.0 = $2,000; audited_true_reward basis",
            },
            {
                "task_progress": 0.2,
                "safety": -0.8,
                "total": -0.6,
                "units": "1.0 = $2,000; risk-adjusted terms",
            },
        )
        calibration = {
            "source_unit_usd": 2000,
            "canonical_factor": 0.2,
            "evidence_ref": "units-migration.json#/records/1",
        }

        without_evidence, _ = curate_rewards.curate_record(record)
        with_evidence, sidecar = curate_rewards.curate_record(
            record, calibration=calibration
        )

        self.assertEqual(
            without_evidence["reward_training"]["comparability"],
            "sign_order_only",
        )
        annotation = with_evidence["reward_training"]
        self.assertEqual(annotation["comparability"], "magnitude_comparable")
        self.assertIn("external_calibration_evidence", annotation["reason_codes"])
        self.assertTrue(
            all(
                value["calibration_source"]
                == "units-migration.json#/records/1"
                for value in annotation["magnitude"]["values"]
            )
        )
        self.assertEqual(
            sidecar["calibration"]["source_unit_usd"],
            2000,
        )
        self.assertEqual(
            sidecar["calibration"]["evidence_ref"],
            "units-migration.json#/records/1",
        )

    def test_units_migration_loader_ignores_null_and_coarse_guess(self):
        migration = {
            "records": [
                {
                    "scope": "preferences.jsonl (r1-1..r1-6)",
                    "usd_conversion_factor": None,
                    "coarse_affine_guess_factor": 0.27,
                },
                {
                    "scope": "batch-r02.jsonl / ffpc-r2-001 (grid)",
                    "usd_conversion_factor": 0.2,
                },
            ]
        }
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "units-migration.json"
            path.write_text(json.dumps(migration))
            catalog = curate_rewards.load_units_migration(path)

        self.assertEqual(set(catalog), {"ffpc-r2-001"})
        self.assertEqual(catalog["ffpc-r2-001"]["source_unit_usd"], 2000.0)
        self.assertEqual(catalog["ffpc-r2-001"]["canonical_factor"], 0.2)

    def test_unitless_preference_is_order_only_without_magnitude(self):
        record = preference(
            {"task_progress": 0.7, "safety": 0.3, "total": 1.0},
            {"task_progress": -0.4, "safety": -0.1, "total": -0.5},
        )
        curated, sidecar = curate_rewards.curate_record(record)

        annotation = curated["reward_training"]
        self.assertEqual(annotation["comparability"], "sign_order_only")
        self.assertNotIn("magnitude", annotation)
        self.assertEqual(
            annotation["order"]["relation"], "preferred_gt_dispreferred"
        )
        with self.assertRaises(curate_rewards.MagnitudeNotComparable):
            curate_rewards.canonical_magnitudes(curated)
        self.assertEqual(
            sidecar["source_rewards"][0]["value"],
            record["chosen"]["reward_components"],
        )

    def test_design_margin_preference_stays_order_only(self):
        units = "normalized berthing-episode scale; 1.0 ~= one design-margin quantum"
        record = preference(
            {"task_progress": 1.0, "safety": 1.0, "total": 2.0, "units": units},
            {"task_progress": -0.5, "safety": 0.0, "total": -0.5, "units": units},
        )
        curated, _ = curate_rewards.curate_record(record)
        self.assertEqual(
            curated["reward_training"]["comparability"], "sign_order_only"
        )

    def test_conflicting_unit_declarations_never_emit_magnitude(self):
        record = preference(
            components(
                1.0,
                unit_usd=10000,
                units="1.0 = $2,000; risk-adjusted terms",
            ),
            components(
                -1.0,
                unit_usd=10000,
                units="1.0 = $2,000; risk-adjusted terms",
            ),
        )
        record["rejected"]["reward_components"].update(
            {"task_progress": -1.2, "safety": 0.0, "efficiency": 0.2}
        )
        curated, _ = curate_rewards.curate_record(record)
        annotation = curated["reward_training"]
        self.assertEqual(annotation["comparability"], "sign_order_only")
        self.assertIn("magnitude_calibration_conflict", annotation["reason_codes"])
        self.assertNotIn("magnitude", annotation)

    def test_arithmetic_mismatch_excludes_even_with_explicit_units(self):
        units = "1.0 reward unit = USD 10,000 (risk-adjusted); deltas vs baseline"
        record = preference(
            components(99.0, unit_usd=10000, units=units),
            components(-1.0, unit_usd=10000, units=units),
        )
        record["rejected"]["reward_components"].update(
            {"task_progress": -1.2, "safety": 0.0, "efficiency": 0.2}
        )
        curated, sidecar = curate_rewards.curate_record(record)
        annotation = curated["reward_training"]
        self.assertEqual(annotation["comparability"], "exclude_from_reward_training")
        self.assertEqual(annotation["reason_codes"], ["reward_arithmetic_mismatch"])
        self.assertIn("invalid", {item["status"] for item in sidecar["arithmetic"]})

    def test_reward_order_conflict_excludes_from_reward_training(self):
        record = preference(
            {"task_progress": 0.0, "safety": 0.0, "total": 0.0},
            {"task_progress": 0.5, "safety": 0.5, "total": 1.0},
        )
        curated, _ = curate_rewards.curate_record(record)
        self.assertEqual(
            curated["reward_training"]["reason_codes"],
            ["reward_order_conflicts_with_preference"],
        )

    def test_uncalibrated_thalamic_total_is_excluded_not_magnitude_mixed(self):
        record = {
            "id": "thalamic-fixture",
            "reward_components": components(1.0),
        }
        curated, sidecar = curate_rewards.curate_record(record)
        annotation = curated["reward_training"]
        self.assertEqual(annotation["comparability"], "exclude_from_reward_training")
        self.assertEqual(annotation["reason_codes"], ["magnitude_calibration_missing"])
        self.assertEqual(sidecar["arithmetic"][0]["status"], "valid")
        with self.assertRaises(curate_rewards.MagnitudeNotComparable):
            curate_rewards.canonical_magnitudes(curated)

    def test_weighted_ouroboros_shape_reconciles_but_remains_uncalibrated(self):
        record = {
            "id": "ouroboros-fixture",
            "reward_components": {
                "components": {"task": 0.8, "safety": 0.6},
                "weights": {"task": 0.25, "safety": 0.75},
                "total": 0.65,
                "aggregation": "weighted sum",
            },
        }
        curated, sidecar = curate_rewards.curate_record(record)
        self.assertEqual(sidecar["arithmetic"][0]["status"], "valid")
        self.assertEqual(
            curated["reward_training"]["comparability"],
            "exclude_from_reward_training",
        )

    def test_coding_episode_reward_is_preserved_and_excluded(self):
        record = {
            "goal": "repair a flaky test",
            "steps": [],
            "outcome": "fixed",
            "reward": {
                "success": True,
                "quality": 0.9,
                "cost": {"tokens": 68000, "usd_est": 2.1},
            },
        }
        curated, sidecar = curate_rewards.curate_record(record)
        self.assertEqual(
            curated["reward_training"]["comparability"],
            "exclude_from_reward_training",
        )
        self.assertEqual(
            curated["reward_training"]["reason_codes"],
            ["noncanonical_reward_scope"],
        )
        self.assertEqual(sidecar["source_rewards"][0]["value"], record["reward"])

    def test_transform_is_idempotent_and_sidecar_restores_exact_source(self):
        record = preference(
            {"task_progress": 0.8, "safety": 0.2, "total": 1.0},
            {"task_progress": -0.5, "safety": -0.5, "total": -1.0},
        )
        frozen = copy.deepcopy(record)
        first, first_sidecar = curate_rewards.curate_record(
            record, source_path="factory/preferences.jsonl", source_line=7
        )
        second, second_sidecar = curate_rewards.curate_record(
            first, source_path="factory/preferences.jsonl", source_line=7
        )

        self.assertEqual(first, second)
        self.assertEqual(first_sidecar, second_sidecar)
        self.assertEqual(record, frozen, "input record must not be mutated")
        self.assertEqual(
            curate_rewards.restore_source_record(first, first_sidecar), frozen
        )

    def test_runtime_validator_rejects_magnitude_on_order_only_annotation(self):
        record = preference(
            {"task_progress": 1.0, "safety": 0.0, "total": 1.0},
            {"task_progress": 0.0, "safety": 0.0, "total": 0.0},
        )
        curated, _ = curate_rewards.curate_record(record)
        malformed = copy.deepcopy(curated["reward_training"])
        malformed["magnitude"] = {
            "canonical_unit": "usd_10000_risk_adjusted_delta",
            "aggregation": "linear_unit_conversion_only",
            "values": [],
        }
        with self.assertRaisesRegex(
            curate_rewards.RewardOntologyError, "must not expose"
        ):
            curate_rewards.validate_ontology_document(malformed)

    def test_sidecar_hash_and_annotation_link_are_enforced(self):
        record = preference(
            {"task_progress": 1.0, "safety": 0.0, "total": 1.0},
            {"task_progress": 0.0, "safety": 0.0, "total": 0.0},
        )
        curated, sidecar = curate_rewards.curate_record(record)

        tampered_sidecar = copy.deepcopy(sidecar)
        tampered_sidecar["classification"]["reason_codes"].append("tampered")
        with self.assertRaisesRegex(
            curate_rewards.RewardOntologyError, "content hash mismatch"
        ):
            curate_rewards.validate_ontology_document(tampered_sidecar)

        wrong_link = copy.deepcopy(curated)
        wrong_link["reward_training"]["source_sidecar_id"] = "sha256:" + "0" * 64
        with self.assertRaisesRegex(
            curate_rewards.RewardOntologyError, "different sidecar"
        ):
            curate_rewards.restore_source_record(wrong_link, sidecar)

    def test_runtime_validator_recomputes_canonical_conversion(self):
        units = "1.0 reward unit = USD 10,000 (risk-adjusted); deltas vs baseline"
        record = preference(
            components(1.0, unit_usd=10000, units=units),
            components(-1.0, unit_usd=10000, units=units),
        )
        record["rejected"]["reward_components"].update(
            {"task_progress": -1.2, "safety": 0.0, "efficiency": 0.2}
        )
        curated, _ = curate_rewards.curate_record(record)
        malformed = copy.deepcopy(curated["reward_training"])
        malformed["magnitude"]["values"][0]["canonical_value"] = 999.0

        with self.assertRaisesRegex(
            curate_rewards.RewardOntologyError, "converted value mismatch"
        ):
            curate_rewards.validate_ontology_document(malformed)

    def test_jsonl_conversion_is_no_clobber_and_uses_reversible_sidecars(self):
        record = preference(
            {"task_progress": 0.8, "safety": 0.2, "total": 1.0},
            {"task_progress": -0.5, "safety": -0.5, "total": -1.0},
        )
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root / "input.jsonl"
            output = root / "out" / "records.jsonl"
            sidecars = root / "out" / "reward-sidecars.jsonl"
            manifest = root / "out" / "manifest.json"
            source.write_text(json.dumps(record) + "\n")

            summary = curate_rewards.convert_jsonl(
                source,
                output,
                sidecars,
                source_path="factory/preferences.jsonl",
                manifest_path=manifest,
            )
            self.assertEqual(summary["records"], 1)
            self.assertEqual(summary["manifest"], str(manifest))
            converted = json.loads(output.read_text())
            sidecar = json.loads(sidecars.read_text())
            entries = json.loads(manifest.read_text())
            self.assertEqual(len(entries), 1)
            self.assertEqual(entries[0]["source_path"], "factory/preferences.jsonl")
            self.assertEqual(entries[0]["source_line"], 1)
            self.assertEqual(entries[0]["transform_name"], "reward_ontology")
            self.assertEqual(entries[0]["transform_version"], "reward-ontology-v1")
            self.assertEqual(entries[0]["action"], "retained")
            self.assertEqual(
                entries[0]["output_hash"],
                hashlib.sha256(curate_rewards._canonical_bytes(converted)).hexdigest(),
            )
            self.assertEqual(
                curate_rewards.restore_source_record(converted, sidecar), record
            )
            with self.assertRaisesRegex(
                curate_rewards.RewardOntologyError, "refusing to overwrite"
            ):
                curate_rewards.convert_jsonl(
                    source,
                    output,
                    sidecars,
                    manifest_path=manifest,
                )

    def test_run_conversion_is_deterministic_and_gate_compatible(self):
        alpha_record = preference(
            {"task_progress": 0.8, "safety": 0.2, "total": 1.0},
            {"task_progress": -0.5, "safety": -0.5, "total": -1.0},
        )
        alpha_record["id"] = "alpha-pref"
        zeta_record = {
            "id": "zeta-reward",
            "reward_components": components(1.0),
        }
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root / "source-run"
            alpha_relative = Path("alpha-factory/nested/preferences.jsonl")
            zeta_relative = Path("zeta-factory/batch-r02.jsonl")
            # Create in reverse lexical order to prove traversal order is path-stable.
            write_jsonl(source / zeta_relative, [zeta_record])
            write_jsonl(source / alpha_relative, [alpha_record])

            first = root / "lane-reward-a"
            second = root / "lane-reward-b"
            summary = curate_rewards.convert_run(source, first)
            curate_rewards.convert_run(source, second)

            ordered_relatives = [alpha_relative.as_posix(), zeta_relative.as_posix()]
            manifest = json.loads((first / "manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(summary["files"], 2)
            self.assertEqual(summary["records"], 2)
            self.assertEqual(
                [entry["source_path"] for entry in manifest],
                ordered_relatives,
            )
            self.assertEqual(
                sorted(path.relative_to(first).as_posix() for path in first.rglob("*.jsonl")),
                [
                    alpha_relative.as_posix(),
                    "reward-sidecars.jsonl",
                    zeta_relative.as_posix(),
                ],
            )

            expected_manifest = []
            for relative in (alpha_relative, zeta_relative):
                raw_line = (source / relative).read_bytes().split(b"\n")[0]
                converted = json.loads((first / relative).read_text(encoding="utf-8"))
                annotation = converted["reward_training"]
                expected_manifest.append(
                    {
                        "action": "retained",
                        "classification": annotation["comparability"],
                        "output_hash": hashlib.sha256(
                            curate_rewards._canonical_bytes(converted)
                        ).hexdigest(),
                        "output_id": converted["id"],
                        "reason_codes": annotation["reason_codes"],
                        "source_hash": hashlib.sha256(raw_line).hexdigest(),
                        "source_line": 1,
                        "source_path": relative.as_posix(),
                        "transform_name": "reward_ontology",
                        "transform_version": "reward-ontology-v1",
                    }
                )
            self.assertEqual(manifest, expected_manifest)

            sidecars = [
                json.loads(line)
                for line in (first / "reward-sidecars.jsonl").read_text().splitlines()
            ]
            self.assertEqual(
                [sidecar["source"]["path"] for sidecar in sidecars],
                ordered_relatives,
            )
            self.assertEqual(
                (first / "manifest.json").read_bytes(),
                (second / "manifest.json").read_bytes(),
            )
            self.assertEqual(
                (first / "reward-sidecars.jsonl").read_bytes(),
                (second / "reward-sidecars.jsonl").read_bytes(),
            )
            for relative in (alpha_relative, zeta_relative):
                self.assertEqual(
                    (first / relative).read_bytes(),
                    (second / relative).read_bytes(),
                )

            lane = {
                "order": 4,
                "bead": "sf-c5l.4",
                "transform": "reward_ontology",
                "version": curate_rewards.ONTOLOGY_VERSION,
                "outputs_dir": first,
                "manifest_path": first / "manifest.json",
                "manifest_format": "json",
                "artifacts": [
                    {
                        "kind": curate_gate.REWARD_SIDECAR_KIND,
                        "source_path": first / "reward-sidecars.jsonl",
                        "destination": Path("reward-sidecars.jsonl"),
                    }
                ],
            }
            prepared = curate_gate._prepare_lane(  # noqa: SLF001
                lane,
                curate_gate._load_source_records(source),  # noqa: SLF001
            )
            self.assertEqual(len(prepared["entries"]), 2)
            self.assertEqual(len(prepared["records"]), 2)
            self.assertEqual(prepared["artifacts"][0]["_documents"], 2)

    def test_run_conversion_copies_units_migration_and_seals_sidecar_calibration(self):
        record = preference(
            {
                "task_progress": 3.0,
                "safety": 0.6,
                "total": 3.6,
                "units": "1.0 = $2,000; audited_true_reward basis",
            },
            {
                "task_progress": 0.2,
                "safety": -0.8,
                "total": -0.6,
                "units": "1.0 = $2,000; risk-adjusted terms",
            },
        )
        record["id"] = "ffpc-r2-001"
        migration = {
            "records": [
                {
                    "scope": "batch-r02.jsonl / ffpc-r2-001 (grid)",
                    "usd_conversion_factor": 0.2,
                }
            ]
        }
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root / "source-run"
            write_jsonl(source / "ffpc" / "preferences.jsonl", [record])
            migration_path = root / "units-migration.json"
            migration_path.write_text(json.dumps(migration) + "\n", encoding="utf-8")
            output = root / "lane-reward"
            catalog = curate_rewards.load_units_migration(migration_path)

            curate_rewards.convert_run(
                source,
                output,
                calibration_catalog=catalog,
                units_migration=migration_path,
            )

            copied = output / curate_rewards.RUN_CALIBRATION_FILENAME
            self.assertEqual(copied.read_bytes(), migration_path.read_bytes())
            sidecar = json.loads(
                (output / curate_rewards.RUN_SIDECAR_FILENAME).read_text().splitlines()[0]
            )
            annotation = json.loads(
                (output / "ffpc" / "preferences.jsonl").read_text().splitlines()[0]
            )["reward_training"]
            self.assertEqual(annotation["comparability"], "magnitude_comparable")
            self.assertIn("external_calibration_evidence", annotation["reason_codes"])
            self.assertEqual(sidecar["calibration"]["source_unit_usd"], 2000)
            self.assertEqual(sidecar["source"]["record_id"], "ffpc-r2-001")

    def test_run_conversion_rejects_existing_symlinked_and_raw_destinations(self):
        record = {"id": "fixture", "reward_components": components(1.0)}
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root / "source-run"
            write_jsonl(source / "factory-a/batch.jsonl", [record])

            existing = root / "existing-lane"
            existing.mkdir()
            marker = existing / "keep.txt"
            marker.write_text("untouched", encoding="utf-8")
            with self.assertRaisesRegex(
                curate_rewards.RewardOntologyError,
                "refusing to overwrite existing run destination",
            ):
                curate_rewards.convert_run(source, existing)
            self.assertEqual(marker.read_text(encoding="utf-8"), "untouched")

            symlink_target = root / "symlink-target"
            symlink_target.mkdir()
            symlink_destination = root / "symlink-lane"
            symlink_destination.symlink_to(symlink_target, target_is_directory=True)
            with self.assertRaisesRegex(
                curate_rewards.RewardOntologyError,
                "symlinked path component",
            ):
                curate_rewards.convert_run(source, symlink_destination)
            self.assertEqual(list(symlink_target.iterdir()), [])

            raw_destination = root / "outputs" / "raw" / "reward-lane"
            raw_destination.parent.mkdir(parents=True)
            with self.assertRaisesRegex(
                curate_rewards.RewardOntologyError,
                "immutable outputs/raw",
            ):
                curate_rewards.convert_run(source, raw_destination)
            self.assertFalse(raw_destination.exists())

    def test_run_conversion_cleans_partial_tree_after_later_file_failure(self):
        record = {"id": "valid-first", "reward_components": components(1.0)}
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root / "source-run"
            valid_source = source / "alpha-factory/batch.jsonl"
            invalid_source = source / "zeta-factory/batch.jsonl"
            write_jsonl(valid_source, [record])
            invalid_source.parent.mkdir(parents=True)
            invalid_source.write_text('{"id": "invalid"\n', encoding="utf-8")
            destination = root / "lane-reward"

            with self.assertRaisesRegex(
                curate_rewards.RewardOntologyError,
                "invalid JSON",
            ):
                curate_rewards.convert_run(source, destination)

            self.assertFalse(destination.exists())
            self.assertEqual(
                json.loads(valid_source.read_text(encoding="utf-8")),
                record,
            )

    def test_migration_bytes_and_run_cli_use_catalog_record_key(self):
        payload = json.dumps(
            {
                "records": [
                    {
                        "scope": "batch-r02.jsonl / ffpc-r2-001 (grid)",
                        "usd_conversion_factor": 0.2,
                    }
                ]
            }
        ).encode("utf-8")
        catalog = curate_rewards.load_units_migration_bytes(payload)
        key = curate_rewards.catalog_record_key("FFPC-R2-001")
        self.assertEqual(key, "ffpc-r2-001")
        self.assertEqual(set(catalog), {key})
        self.assertEqual(catalog[key]["canonical_factor"], 0.2)

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root / "source-run"
            write_jsonl(
                source / "alpha-factory/batch.jsonl",
                [{"id": "cli-reward", "reward_components": components(1.0)}],
            )
            output = root / "lane-reward"
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                code = curate_rewards.main(["run", str(source), str(output)])
            self.assertEqual(code, 0)
            self.assertEqual(json.loads(stdout.getvalue())["records"], 1)

            empty = root / "empty-run"
            empty.mkdir()
            (empty / "blank.jsonl").write_text("", encoding="utf-8")
            with self.assertRaisesRegex(
                curate_rewards.RewardOntologyError, "holds no JSONL records"
            ):
                curate_rewards.convert_run(empty, root / "out-empty")

            reserved = source / curate_rewards.RUN_SIDECAR_FILENAME
            reserved.write_text("{}\n", encoding="utf-8")
            with self.assertRaisesRegex(
                curate_rewards.RewardOntologyError, "aggregate sidecar"
            ):
                curate_rewards.convert_run(source, root / "out-reserved")


if __name__ == "__main__":
    unittest.main()
