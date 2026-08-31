#!/usr/bin/env python3
"""JSONL, run-lane, and CLI tests for reward ontology conversion."""

import collections
import hashlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from contextlib import redirect_stdout

_TESTS = Path(__file__).resolve().parent
if str(_TESTS) not in sys.path:
    sys.path.insert(0, str(_TESTS))

from reward_test_helpers import (  # noqa: E402
    PIPELINES,
    RAW_RUN,
    components,
    preference,
    write_jsonl,
)

if str(PIPELINES) not in sys.path:
    sys.path.insert(0, str(PIPELINES))

import curate_gate  # noqa: E402
import curate_rewards  # noqa: E402


class RewardOntologyRunTests(unittest.TestCase):
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


@unittest.skipUnless(
    RAW_RUN.is_dir(), "the 2026-08-17 raw run is not present in this checkout"
)
class MappedRunFidelity(unittest.TestCase):
    """Opt-in: the frozen mapping still describes the run it was derived from."""

    @classmethod
    def setUpClass(cls):
        cls.records = []
        for path in sorted(RAW_RUN.rglob("*.jsonl")):
            for line_number, line in enumerate(
                path.read_text(encoding="utf-8").splitlines(), 1
            ):
                if line.strip():
                    cls.records.append(
                        (path.parent.name, path.name, line_number, json.loads(line))
                    )

    def test_the_frozen_vocabulary_matches_the_raw_run(self):
        census = curate_rewards.reward_census(
            record for _f, _n, _l, record in self.records
        )
        frozen = curate_rewards.CONVERSION_POLICY["source_vocabulary"]
        for field in (
            "records",
            "reward_instances",
            "ontology_scope_instances",
            "unique_component_keys",
            "unique_shapes",
            "dispositions",
            "arithmetic",
            "component_keys",
            "shapes",
        ):
            self.assertEqual(census[field], frozen[field], field)

    def test_the_frozen_classification_matches_the_raw_run(self):
        classes = collections.Counter()
        reasons = collections.Counter()
        for factory, name, line_number, record in self.records:
            curated, sidecar = curate_rewards.curate_record(
                record, source_path=f"{factory}/{name}", source_line=line_number
            )
            annotation = curated[curate_rewards.ANNOTATION_FIELD]
            classes[annotation["comparability"]] += 1
            reasons.update(annotation["reason_codes"])
            self.assertEqual(
                curate_rewards.restore_source_record(curated, sidecar),
                record,
                f"{factory}/{name}:{line_number}",
            )
        expected = curate_rewards.CONVERSION_POLICY["expected_classification"]
        self.assertEqual(dict(sorted(classes.items())), expected["comparability"])
        self.assertEqual(dict(sorted(reasons.items())), expected["reason_codes"])


if __name__ == '__main__':
    unittest.main()
