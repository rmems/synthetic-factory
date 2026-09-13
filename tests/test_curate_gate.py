#!/usr/bin/env python3
"""Tests for pipelines/curate_gate.py — the sf-c5l.7 integration/promotion gate."""

import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

_TESTS = Path(__file__).resolve().parent
if str(_TESTS) not in sys.path:
    sys.path.insert(0, str(_TESTS))

from gate_fixture import (  # noqa: E402
    PIPELINES,
    GateFixture,
    _bridge,
    _captured_main,
    _lane_manifest_entry,
    _preference,
    _read_jsonl,
    _thalamic,
    _write_jsonl,
)

if str(PIPELINES) not in sys.path:
    sys.path.insert(0, str(PIPELINES))

import curate_gate  # noqa: E402
import curate_rewards  # noqa: E402


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
        ):
            self.assertTrue(manifest["gates"][gate]["passed"], gate)
        # Composition happened, and both lane trees landed under one destination.
        self.assertTrue((fixture.cleaned / "bridge-factory" / "batch-r02.jsonl").is_file())
        self.assertTrue((fixture.cleaned / "thalamic-mini" / "batch-r02.jsonl").is_file())

    def test_reward_converter_emits_a_manifest_the_gate_can_authenticate(self):
        source_run = self.root / "raw"
        source = source_run / "thalamic-mini" / "batch-r01.jsonl"
        record = _thalamic("reward-cli")
        _write_jsonl(source, [record])
        outputs = self.root / "lane-reward"
        output = outputs / "thalamic-mini" / "batch-r01.jsonl"
        sidecars = outputs / "reward-sidecars.jsonl"
        manifest = outputs / "manifest.json"

        curate_rewards.convert_jsonl(
            source,
            output,
            sidecars,
            source_path="thalamic-mini/batch-r01.jsonl",
            manifest_path=manifest,
        )
        lane = {
            "order": 4,
            "bead": "sf-c5l.4",
            "transform": "reward_ontology",
            "version": curate_rewards.REWARD_TRANSFORM_VERSION,
            "outputs_dir": outputs,
            "manifest_path": manifest,
            "manifest_format": "json",
            "artifacts": [
                {
                    "kind": curate_gate.REWARD_SIDECAR_KIND,
                    "source_path": sidecars,
                    "destination": Path("reward-sidecars.jsonl"),
                }
            ],
        }

        prepared = curate_gate._prepare_lane(  # noqa: SLF001
            lane,
            curate_gate._load_source_records(source_run),  # noqa: SLF001
        )

        self.assertEqual(len(prepared["entries"]), 1)
        self.assertEqual(len(prepared["records"]), 1)
        self.assertEqual(prepared["entries"][0]["action"], "retained")
        self.assertEqual(
            prepared["records"][0]["record"][curate_rewards.ANNOTATION_FIELD]["ontology_version"],
            curate_rewards.ONTOLOGY_VERSION,
        )

    def test_terminal_record_repairs_replay_without_summary_drift(self):
        fixture = GateFixture(self.root)
        repaired_entries = json.loads(fixture.manifest_paths[1].read_text())
        repaired = next(entry for entry in repaired_entries if entry["source_line"] == 3)
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
        repair = next(
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

        self.assertEqual(fixture.integrate("--per-stratum", "100"), 0)
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
        self.assertEqual(fixture.integrate(), 0)

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
        entry_index = next(
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

        self.assertEqual(fixture.integrate(), 0)
        entry = next(
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

        self.assertEqual(fixture.integrate(), 0)
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
        self.assertEqual(fixture.integrate(), 0)
        manifest = fixture.manifest()

        supersession = next(
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

        self.assertEqual(fixture.integrate(), 0)
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

        self.assertEqual(fixture.integrate(), 0)
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

    def test_integrate_requires_a_manifest_for_every_lane(self):
        fixture = GateFixture(self.root)
        plan = json.loads(fixture.plan_path.read_text())
        plan["lanes"][4].pop("manifest")
        fixture.plan_path.write_text(json.dumps(plan))

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
        self.assertIn("needs a non-empty string 'manifest'", stderr)
        self.assertFalse(fixture.cleaned.exists())

    def test_integrate_rejects_unaccounted_source_records(self):
        fixture = GateFixture(self.root)
        _write_jsonl(
            fixture.source_run / "unaccounted" / "batch-r03.jsonl",
            [_thalamic("missing-disposition")],
        )

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
        self.assertIn("lack a retained output or an explicit exclusion/quarantine", stderr)
        self.assertIn("unaccounted/batch-r03.jsonl:1", stderr)
        self.assertFalse(fixture.cleaned.exists())

    def test_integrate_requires_known_actions_and_reason_codes(self):
        for name, mutate, message in (
            (
                "missing-action",
                lambda entries: entries[0].pop("action"),
                "needs an explicit action",
            ),
            (
                "unknown-action",
                lambda entries: entries[0].update(action="invented"),
                "unsupported action",
            ),
            (
                "terminal-without-reason",
                lambda entries: entries[-1].update(reason_codes=[]),
                "needs at least one reason code",
            ),
            (
                "scalar-reason-code",
                lambda entries: entries[-1].update(reason_codes="INVALID_JSON"),
                "must be a list of non-empty strings",
            ),
        ):
            with self.subTest(name=name):
                fixture = GateFixture(self.root / name)
                entries = json.loads(fixture.manifest_paths[0].read_text())
                mutate(entries)
                fixture.manifest_paths[0].write_text(json.dumps(entries))

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
                self.assertIn(message, stderr)
                self.assertFalse(fixture.cleaned.exists())

    def test_plan_rejects_ambiguous_lane_manifest_formats(self):
        for suffix in ("", ".txt"):
            with self.subTest(suffix=suffix or "extensionless"):
                fixture = GateFixture(self.root / (suffix.removeprefix(".") or "none"))
                ambiguous = fixture.lane_bridge / f"manifest{suffix}"
                fixture.manifest_paths[0].rename(ambiguous)
                plan = json.loads(fixture.plan_path.read_text())
                plan["lanes"][0]["manifest"] = ambiguous.relative_to(fixture.root).as_posix()
                fixture.plan_path.write_text(json.dumps(plan))

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
                self.assertIn("must end in .json or .jsonl", stderr)
                self.assertFalse(fixture.cleaned.exists())

    def test_repository_relative_raw_source_matches_documented_plan(self):
        project = self.root / "project"
        plan_dir = project / "outputs" / "curation"
        fixture = GateFixture(plan_dir)
        raw_root = project / "outputs" / "raw"
        production_source = raw_root / "2026-08-17"
        raw_root.mkdir(parents=True)
        fixture.source_run.rename(production_source)
        fixture.source_run = production_source
        plan = json.loads(fixture.plan_path.read_text())
        plan["source_run"] = "outputs/raw/2026-08-17"
        fixture.plan_path.write_text(json.dumps(plan, indent=2) + "\n")

        with (
            mock.patch.object(curate_gate, "_REPO", project.resolve()),
            mock.patch.object(curate_gate, "RAW_OUTPUT_ROOT", raw_root.resolve()),
        ):
            self.assertEqual(fixture.integrate(), 0)
        self.assertTrue((fixture.cleaned / curate_gate.MANIFEST_FILENAME).is_file())

    def test_integrate_rejects_output_tampered_after_manifest_creation(self):
        fixture = GateFixture(self.root)
        output = fixture.lane_core / "thalamic-mini" / "batch-r02.jsonl"
        records = _read_jsonl(output)
        records[0]["state"]["env"] = "tampered after identity manifest"
        _write_jsonl(output, records)

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
        self.assertIn("output records do not match its manifest", stderr)
        self.assertFalse(fixture.cleaned.exists())

    def test_integrate_rejects_manifest_source_hash_not_matching_source_run(self):
        fixture = GateFixture(self.root)
        entries = json.loads(fixture.manifest_paths[1].read_text())
        entries[0]["source_hash"] = "f" * 64
        fixture.manifest_paths[1].write_text(json.dumps(entries))

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
        self.assertIn("source hash does not match", stderr)
        self.assertFalse(fixture.cleaned.exists())

    def test_integrate_rejects_manifest_output_id_not_matching_output_record(self):
        fixture = GateFixture(self.root)
        entries = json.loads(fixture.manifest_paths[1].read_text())
        entries[0]["output_id"] = "self-resealed-forged-output-id"
        fixture.manifest_paths[1].write_text(json.dumps(entries))

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
        self.assertIn("output_id", stderr)
        self.assertIn("does not match authenticated output record", stderr)
        self.assertFalse(fixture.cleaned.exists())

    def test_integrate_rejects_output_moved_to_an_undeclared_path(self):
        fixture = GateFixture(self.root)
        source = fixture.lane_core / "thalamic-mini" / "batch-r02.jsonl"
        moved = fixture.lane_core / "other-factory" / "batch-r02.jsonl"
        moved.parent.mkdir(parents=True)
        source.rename(moved)

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
        self.assertIn("output records do not match its manifest", stderr)
        self.assertFalse(fixture.cleaned.exists())

    def test_integrate_rejects_a_manifest_from_another_lane(self):
        fixture = GateFixture(self.root)
        plan = json.loads(fixture.plan_path.read_text())
        plan["lanes"][1]["manifest"] = "lane-tag/manifest.json"
        fixture.plan_path.write_text(json.dumps(plan))

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
        self.assertIn("declares transform 'tag_taxonomy'", stderr)
        self.assertFalse(fixture.cleaned.exists())

    def test_jsonl_lane_manifest_remains_parseable_as_promoted_evidence(self):
        fixture = GateFixture(self.root)
        entries = json.loads(fixture.manifest_paths[0].read_text())
        entries[0]["reason_codes"] = ["literal\u2028separator\u2029evidence"]
        jsonl_manifest = fixture.lane_bridge / "manifest.jsonl"
        jsonl_manifest.write_text(
            "".join(
                json.dumps(entry, ensure_ascii=False, sort_keys=True) + "\n" for entry in entries
            ),
            encoding="utf-8",
        )
        plan = json.loads(fixture.plan_path.read_text())
        plan["lanes"][0]["manifest"] = "lane-bridge/manifest.jsonl"
        fixture.plan_path.write_text(json.dumps(plan, indent=2) + "\n")

        self.assertEqual(fixture.integrate(), 0)
        review = fixture.accepted_review()
        self.assertEqual(fixture.promote(review), 0)
        copied = (
            fixture.curated
            / curate_gate.GOVERNANCE_DIRNAME
            / curate_gate.LANE_MANIFEST_DIRNAME
            / "01"
            / "manifest.jsonl.evidence"
        )
        self.assertEqual(copied.read_bytes(), jsonl_manifest.read_bytes())

    def test_jsonl_readers_keep_unicode_line_separators_inside_one_record(self):
        record = _thalamic("unicode-separators")
        record["state"]["env"] = "before\u2028middle\u2029after"
        record["reward_components"]["note"] = "reward\u2028evidence\u2029value"
        fixture = GateFixture(self.root, thalamic_records=[record])
        self.assertEqual(fixture.integrate(), 0)
        manifest = fixture.manifest()
        for gate in ("structural_validator", "record_invariants", "training_audit"):
            self.assertTrue(manifest["gates"][gate]["passed"], gate)

        output = fixture.cleaned / "thalamic-mini" / "batch-r02.jsonl"
        self.assertEqual(curate_gate.count_records(output), 1)
        parsed = list(curate_gate.iter_records(fixture.cleaned))
        self.assertEqual(len(parsed), 2)
        thalamic = next(item for item in parsed if item[0].startswith("thalamic-mini/"))
        self.assertEqual(thalamic[2]["state"]["env"], "before\u2028middle\u2029after")
        self.assertEqual(
            thalamic[2]["reward_components"]["note"],
            "reward\u2028evidence\u2029value",
        )
        review = fixture.accepted_review()
        self.assertEqual(fixture.promote(review), 0)
        promoted = list(curate_gate.iter_records(fixture.curated))
        promoted_thalamic = next(item for item in promoted if item[0].startswith("thalamic-mini/"))
        self.assertEqual(
            promoted_thalamic[2]["state"]["env"],
            "before\u2028middle\u2029after",
        )

    def test_integrate_refuses_an_existing_cleaned_destination(self):
        fixture = GateFixture(self.root)
        fixture.cleaned.mkdir(parents=True)
        self.assertEqual(fixture.integrate(), 2)

    def test_integrate_refuses_a_dangling_destination_symlink(self):
        fixture = GateFixture(self.root)
        target = self.root / "must-not-be-created"
        try:
            fixture.cleaned.symlink_to(target, target_is_directory=True)
        except (OSError, NotImplementedError):
            self.skipTest("symlinks are unavailable on this platform")

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
        self.assertIn("existing cleaned destination", stderr)
        self.assertFalse(target.exists())

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

    def test_plan_fields_and_digest_come_from_one_captured_snapshot(self):
        fixture = GateFixture(self.root)
        original = fixture.plan_path.read_bytes()
        original_digest = curate_gate.sha256_hex(original)
        real_resolve = curate_gate._resolve_source_run_path
        changed = False

        def mutate_after_snapshot(*args, **kwargs):
            nonlocal changed
            resolved = real_resolve(*args, **kwargs)
            if not changed:
                changed = True
                fixture.plan_path.write_bytes(original + b"\n")
            return resolved

        with mock.patch.object(
            curate_gate,
            "_resolve_source_run_path",
            side_effect=mutate_after_snapshot,
        ):
            loaded = curate_gate.load_plan(fixture.plan_path)

        self.assertTrue(changed)
        self.assertEqual(loaded["plan_sha256"], original_digest)
        self.assertNotEqual(
            loaded["plan_sha256"],
            curate_gate.file_sha256(fixture.plan_path),
        )

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

    def test_cleaned_destination_must_be_disjoint_from_source_run(self):
        for name, destination in (
            ("equal", lambda fixture: fixture.source_run),
            ("inside", lambda fixture: fixture.source_run / "cleaned"),
            ("containing", lambda fixture: fixture.root),
        ):
            with self.subTest(name=name):
                fixture = GateFixture(self.root / name)
                cleaned = destination(fixture)
                code, _report, stderr = _captured_main(
                    [
                        "integrate",
                        "--plan",
                        str(fixture.plan_path),
                        "--cleaned-out",
                        str(cleaned),
                    ]
                )
                self.assertEqual(code, 2)
                self.assertIn("must be disjoint after symlink resolution", stderr)

    def test_cleaned_destination_symlink_alias_of_source_run_is_rejected(self):
        fixture = GateFixture(self.root)
        alias = self.root / "raw-alias"
        try:
            alias.symlink_to(fixture.source_run, target_is_directory=True)
        except (OSError, NotImplementedError):
            self.skipTest("symlinks are unavailable on this platform")
        destination = alias / "cleaned"

        code, _report, stderr = _captured_main(
            [
                "integrate",
                "--plan",
                str(fixture.plan_path),
                "--cleaned-out",
                str(destination),
            ]
        )
        self.assertEqual(code, 2)
        self.assertIn("must be disjoint after symlink resolution", stderr)
        self.assertFalse((fixture.source_run / "cleaned").exists())

    def test_integrate_rejects_a_non_positive_sample_size(self):
        fixture = GateFixture(self.root)
        self.assertEqual(fixture.integrate("--per-stratum", "0"), 2)
        self.assertFalse(fixture.cleaned.exists())

    def test_a_lane_manifest_inside_the_output_tree_stays_out_of_the_corpus(self):
        fixture = GateFixture(self.root)
        self.assertTrue(fixture.manifest_paths[0].is_file())
        self.assertEqual(fixture.integrate(), 0)
        self.assertFalse((fixture.cleaned / "manifest.json").exists())
        manifest = fixture.manifest()
        self.assertNotIn("manifest.json", {entry["path"] for entry in manifest["outputs"]})
        copied = fixture.cleaned / curate_gate.GOVERNANCE_DIRNAME / "lane-manifests"
        self.assertEqual(len(list(copied.rglob("*.evidence"))), 6)

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

    def test_integration_atomically_refuses_a_concurrent_destination(self):
        fixture = GateFixture(self.root)
        original = curate_gate._rename_noreplace
        reserved_inodes = []

        def reserve_then_publish(source, destination, label, expected_tree):
            destination.mkdir(parents=True)
            reserved_inodes.append(destination.stat().st_ino)
            return original(source, destination, label, expected_tree)

        with mock.patch.object(
            curate_gate,
            "_rename_noreplace",
            side_effect=reserve_then_publish,
        ):
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
        self.assertIn("refusing to overwrite an existing cleaned destination", stderr)
        self.assertEqual(fixture.cleaned.stat().st_ino, reserved_inodes[0])
        self.assertEqual(list(fixture.cleaned.iterdir()), [])
        self.assertEqual(list(self.root.glob(".cleaned-v1.staging-*")), [])

    def test_integration_publisher_reauthenticates_the_staging_tree(self):
        fixture = GateFixture(self.root)
        original = curate_gate._rename_noreplace

        def mutate_then_publish(source, destination, label, expected_tree):
            corpus = source / "thalamic-mini" / "batch-r02.jsonl"
            corpus.write_text("{invalid-json\n", encoding="utf-8")
            return original(source, destination, label, expected_tree)

        with mock.patch.object(
            curate_gate,
            "_rename_noreplace",
            side_effect=mutate_then_publish,
        ):
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
        self.assertIn("staging tree changed after final validation", stderr)
        self.assertFalse(fixture.cleaned.exists())
        self.assertEqual(list(self.root.glob(".cleaned-v1.staging-*")), [])

    def test_staging_tree_snapshot_rejects_a_symlink(self):
        staged = self.root / "staged"
        staged.mkdir()
        target = self.root / "target.jsonl"
        target.write_text("{}\n", encoding="utf-8")
        try:
            (staged / "alias.jsonl").symlink_to(target)
        except (OSError, NotImplementedError):
            self.skipTest("symlinks are unavailable on this platform")

        with self.assertRaisesRegex(curate_gate.GateError, "contains a symlink"):
            curate_gate._tree_snapshot(staged)

    def test_staging_tree_snapshot_rejects_a_hardlink(self):
        staged = self.root / "staged"
        staged.mkdir()
        target = self.root / "target.jsonl"
        target.write_text("{}\n", encoding="utf-8")
        try:
            (staged / "alias.jsonl").hardlink_to(target)
        except (OSError, NotImplementedError):
            self.skipTest("hard links are unavailable on this platform")

        with self.assertRaisesRegex(curate_gate.GateError, "multiply linked"):
            curate_gate._tree_snapshot(staged)

    def test_lane_snapshot_rejects_a_path_replaced_during_read(self):
        path = self.root / "lane.jsonl"
        replacement = self.root / "replacement.jsonl"
        path.write_text('{"id":"before"}\n', encoding="utf-8")
        replacement.write_text('{"id":"after"}\n', encoding="utf-8")
        original_fstat = curate_gate.os.fstat
        calls = 0

        def replace_before_second_fstat(descriptor):
            nonlocal calls
            calls += 1
            if calls == 2:
                replacement.replace(path)
            return original_fstat(descriptor)

        with mock.patch.object(
            curate_gate.os,
            "fstat",
            side_effect=replace_before_second_fstat,
        ):
            with self.assertRaisesRegex(curate_gate.GateError, "changed while"):
                curate_gate._read_regular_file_snapshot(path, "lane output")

    def test_source_loader_rejects_a_path_replaced_during_read(self):
        source_run = self.root / "raw"
        path = source_run / "factory" / "batch-r01.jsonl"
        replacement = self.root / "replacement.jsonl"
        _write_jsonl(path, [_thalamic("before")])
        _write_jsonl(replacement, [_thalamic("after")])
        original_fstat = curate_gate.os.fstat
        calls = 0

        def replace_before_second_fstat(descriptor):
            nonlocal calls
            calls += 1
            if calls == 2:
                replacement.replace(path)
            return original_fstat(descriptor)

        with mock.patch.object(
            curate_gate.os,
            "fstat",
            side_effect=replace_before_second_fstat,
        ):
            with self.assertRaisesRegex(curate_gate.GateError, "changed while"):
                curate_gate._load_source_records(source_run)

    def test_lane_manifest_evidence_uses_the_authenticated_snapshot(self):
        fixture = GateFixture(self.root)
        prepared = curate_gate.prepare_lanes(curate_gate.load_plan(fixture.plan_path))
        original = prepared[0]["manifest_payload"]
        fixture.manifest_paths[0].write_text("[]", encoding="utf-8")
        destination = self.root / "evidence"
        destination.mkdir()

        lane_evidence, _governance = curate_gate.copy_lane_evidence(prepared, destination)

        copied = destination / lane_evidence[0]["manifest"]["path"]
        self.assertEqual(copied.read_bytes(), original)
        self.assertNotEqual(copied.read_bytes(), fixture.manifest_paths[0].read_bytes())

    def test_reward_artifact_evidence_uses_the_authenticated_snapshot(self):
        fixture = GateFixture(self.root)
        prepared = curate_gate.prepare_lanes(curate_gate.load_plan(fixture.plan_path))
        reward_lane = next(lane for lane in prepared if lane["transform"] == "reward_ontology")
        artifact = reward_lane["artifacts"][0]
        original = artifact["_payload"]
        artifact["source_path"].write_text("{}\n", encoding="utf-8")
        destination = self.root / "evidence"
        destination.mkdir()

        lane_evidence, _governance = curate_gate.copy_lane_evidence(prepared, destination)

        reward_evidence = next(
            lane for lane in lane_evidence if lane["transform"] == "reward_ontology"
        )["artifacts"][0]
        copied = destination / reward_evidence["path"]
        self.assertEqual(copied.read_bytes(), original)
        self.assertNotEqual(copied.read_bytes(), artifact["source_path"].read_bytes())

    def test_preference_lane_authenticates_consolidated_outputs_by_source_identity(self):
        source_run = self.root / "raw"
        outputs = self.root / "lane-preference"
        manifest_path = outputs / "manifest.json"
        first = _preference("pref-first")
        second = _preference("pref-second")
        _write_jsonl(source_run / "factory-a" / "batch-r01.jsonl", [first])
        _write_jsonl(source_run / "factory-b" / "batch-r02.jsonl", [second])
        _write_jsonl(outputs / "consolidated" / "preferences.jsonl", [first, second])
        source_records = curate_gate._load_source_records(source_run)
        entries = [
            _lane_manifest_entry(
                "retained",
                1,
                transform="same-context-preference-curation",
                version="1.0.0",
                source_path=source_path,
                record=record,
                source_hash=source_records[(source_path, 1)]["source_hash"],
            )
            for source_path, record in (
                ("factory-a/batch-r01.jsonl", first),
                ("factory-b/batch-r02.jsonl", second),
            )
        ]
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        manifest_path.write_text(json.dumps(entries), encoding="utf-8")
        lane = {
            "order": 3,
            "bead": "sf-c5l.3",
            "transform": "same-context-preference-curation",
            "version": "1.0.0",
            "outputs_dir": outputs,
            "manifest_path": manifest_path,
            "manifest_format": "json",
            "artifacts": [],
        }

        prepared = curate_gate._prepare_lane(lane, source_records)

        self.assertEqual(
            [record["source_path"] for record in prepared["records"]],
            ["factory-a/batch-r01.jsonl", "factory-b/batch-r02.jsonl"],
        )
        self.assertEqual(
            {record["relative_path"] for record in prepared["records"]},
            {"consolidated/preferences.jsonl"},
        )

    def test_preference_lane_rejects_ambiguous_duplicate_consolidated_outputs(self):
        source_run = self.root / "raw"
        outputs = self.root / "lane-preference"
        manifest_path = outputs / "manifest.json"
        record = _preference("same-preference")
        _write_jsonl(source_run / "factory-a" / "batch-r01.jsonl", [record])
        _write_jsonl(source_run / "factory-b" / "batch-r02.jsonl", [record])
        _write_jsonl(outputs / "consolidated" / "preferences.jsonl", [record, record])
        source_records = curate_gate._load_source_records(source_run)
        entries = [
            _lane_manifest_entry(
                "retained",
                1,
                transform="same-context-preference-curation",
                version="1.0.0",
                source_path=source_path,
                record=record,
                source_hash=source_records[(source_path, 1)]["source_hash"],
            )
            for source_path in (
                "factory-a/batch-r01.jsonl",
                "factory-b/batch-r02.jsonl",
            )
        ]
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        manifest_path.write_text(json.dumps(entries), encoding="utf-8")
        lane = {
            "order": 3,
            "bead": "sf-c5l.3",
            "transform": "same-context-preference-curation",
            "version": "1.0.0",
            "outputs_dir": outputs,
            "manifest_path": manifest_path,
            "manifest_format": "json",
            "artifacts": [],
        }

        with self.assertRaisesRegex(curate_gate.GateError, "multiple source identities"):
            curate_gate._prepare_lane(lane, source_records)



if __name__ == '__main__':
    unittest.main()
