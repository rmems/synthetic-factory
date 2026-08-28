#!/usr/bin/env python3
"""Tests for pipelines/curate_gate.py — the sf-c5l.7 integration/promotion gate."""

import io
import copy
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
import curate_identity  # noqa: E402
import curate_rewards  # noqa: E402


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
    path.write_text(
        "".join(json.dumps(record, ensure_ascii=False) + "\n" for record in records),
        encoding="utf-8",
    )


def _read_jsonl(path):
    return [json.loads(line) for line in path.read_text().split("\n") if line.strip()]


def _reward_annotated(records, source_path, sidecars=None):
    annotated = []
    known_sidecars = {item["sidecar_id"] for item in (sidecars or []) if isinstance(item, dict)}
    for source_line, record in enumerate(records, 1):
        existing = record.get("reward_training") if isinstance(record, dict) else None
        if existing is not None:
            curate_rewards.validate_ontology_document(existing)
            annotated.append(record)
            continue
        curated, sidecar = curate_rewards.curate_record(
            record, source_path=source_path, source_line=source_line
        )
        annotated.append(curated)
        if sidecars is not None and sidecar["sidecar_id"] not in known_sidecars:
            sidecars.append(sidecar)
            known_sidecars.add(sidecar["sidecar_id"])
    return annotated


def _stamp_canonical_identity_ids(records, relative):
    for line_no, record in enumerate(records, 1):
        if not isinstance(record, dict):
            continue
        kind = curate_identity.record_kind(record)
        record["id"] = curate_gate._canonical_identity_output_id(
            relative, line_no, kind, "/"
        )
        owners = curate_gate._identity_owner_specs(record, kind, "fixture")
        for owner_path, owner in owners:
            if owner_path != "/":
                owner["id"] = curate_gate._canonical_identity_output_id(
                    relative, line_no, kind, owner_path
                )


def _quiet_main(argv):
    """Run the gate CLI in-process without leaking its report into test output."""
    with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
        return curate_gate.main(argv)


def _captured_main(argv):
    stdout = io.StringIO()
    stderr = io.StringIO()
    with redirect_stdout(stdout), redirect_stderr(stderr):
        code = curate_gate.main(argv)
    report = json.loads(stdout.getvalue()) if stdout.getvalue().strip() else None
    return code, report, stderr.getvalue()


def _tree_hashes(root):
    return {
        path.relative_to(root).as_posix(): curate_gate.file_sha256(path)
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def _lane_manifest_entry(
    action,
    line,
    reasons=(),
    *,
    transform="bridge_event_time_order",
    version="1.0.0",
    source_path="bridge-factory/batch-r02.jsonl",
    record=None,
    source_record=None,
    identity_mappings=False,
    source_hash=None,
):
    entry = {
        "source_path": source_path,
        "source_line": line,
        "source_hash": source_hash
        or (curate_gate.record_sha256(record) if record is not None else "0" * 64),
        "transform_name": transform,
        "transform_version": version,
        "action": action,
        "reason_codes": list(reasons),
        "output_id": record.get("id") if isinstance(record, dict) else None,
        "output_hash": curate_gate.record_sha256(record) if record is not None else None,
    }
    if identity_mappings:
        original = source_record if isinstance(source_record, dict) else record
        kind = curate_identity.record_kind(original)
        owners = curate_gate._identity_owner_specs(original, kind, "fixture")
        id_owner_paths = ["/", *(path for path, _owner in owners if path != "/")]
        entry["id_mappings"] = []
        for owner_path in id_owner_paths:
            output_owner = curate_gate._mapping_value(record, owner_path, "fixture output owner")
            entry["id_mappings"].append(
                {
                    "owner_path": owner_path,
                    "original_ids": curate_gate._source_original_ids(
                        original,
                        owner_path,
                        "fixture source owner",
                    ),
                    "output_id": output_owner.get("id"),
                }
            )
        state_owners = owners or [("/", original)]
        use_state = any(
            isinstance(state := owner.get("state"), dict)
            and ("sim_or_real" in state or "provenance" in state)
            for _owner_path, owner in state_owners
        )
        provenance_paths = []
        if use_state:
            provenance_paths.extend(
                (owner_path, curate_gate._mapping_pointer(owner_path, "state"))
                for owner_path, _owner in state_owners
            )
            if kind in {"preference", "bridge_pair", "episode", "safety_case", "multi_agent"}:
                provenance_paths.append(("/", None))
        else:
            provenance_paths.append(("/", None))
        entry["provenance_mappings"] = []
        for owner_path, state_path in provenance_paths:
            output_owner = curate_gate._mapping_value(record, owner_path, "fixture output owner")
            entry["provenance_mappings"].append(
                {
                    "owner_path": owner_path,
                    "state_path": state_path,
                    "basis": "fixture",
                    "original": curate_gate._source_original_provenance(
                        original,
                        owner_path,
                        state_path,
                        "fixture source provenance",
                    ),
                    "canonical": copy.deepcopy(output_owner["provenance"]),
                }
            )
    return entry


class GateFixture:
    """A six-lane curation scenario laid out under one temporary root."""

    def __init__(
        self, root, bridge_records=None, thalamic_records=None, *, canonical_ids=True
    ):
        self.root = Path(root)
        self.source_run = self.root / "raw"
        self.lane_bridge = self.root / "lane-bridge"
        self.lane_core = self.root / "lane-core"
        self.lane_preference = self.root / "lane-preference"
        self.lane_reward = self.root / "lane-reward"
        self.lane_coding = self.root / "lane-coding"
        self.lane_tag = self.root / "lane-tag"
        self.reward_sidecars = []
        raw_bridge_records = copy.deepcopy(
            bridge_records if bridge_records is not None else [_bridge()]
        )
        raw_core_records = copy.deepcopy(
            thalamic_records
            if thalamic_records is not None
            else [_thalamic("t-1"), _preference(), _episode()]
        )
        self.bridge_source_records = len(raw_bridge_records)
        raw_bridge_path = self.source_run / "bridge-factory" / "batch-r02.jsonl"
        _write_jsonl(raw_bridge_path, raw_bridge_records)
        with raw_bridge_path.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(json.dumps(_thalamic("bridge-quarantine-source")) + "\n")
            handle.write("{invalid-json\n")
        _write_jsonl(
            self.source_run / "thalamic-mini" / "batch-r02.jsonl",
            raw_core_records,
        )

        identity_bridge_records = copy.deepcopy(raw_bridge_records)
        identity_core_records = copy.deepcopy(raw_core_records)
        if canonical_ids:
            _stamp_canonical_identity_ids(
                identity_bridge_records, "bridge-factory/batch-r02.jsonl"
            )
            _stamp_canonical_identity_ids(
                identity_core_records, "thalamic-mini/batch-r02.jsonl"
            )
        annotated_bridge_records = _reward_annotated(
            raw_bridge_records,
            "bridge-factory/batch-r02.jsonl",
            self.reward_sidecars,
        )
        _write_jsonl(
            self.lane_bridge / "bridge-factory" / "batch-r02.jsonl",
            identity_bridge_records,
        )
        annotated_core_records = _reward_annotated(
            raw_core_records, "thalamic-mini/batch-r02.jsonl", self.reward_sidecars
        )
        for lane_dir in (
            self.lane_core,
            self.lane_preference,
            self.lane_coding,
            self.lane_tag,
        ):
            _write_jsonl(
                lane_dir / "thalamic-mini" / "batch-r02.jsonl", identity_core_records
            )
        _write_jsonl(
            self.lane_reward / "bridge-factory" / "batch-r02.jsonl",
            annotated_bridge_records,
        )
        _write_jsonl(
            self.lane_core / "bridge-factory" / "batch-r02.jsonl",
            identity_bridge_records,
        )
        _write_jsonl(
            self.lane_reward / "thalamic-mini" / "batch-r02.jsonl",
            annotated_core_records,
        )
        self.lanes = [
            (self.lane_bridge, "bridge_event_time_order", "1.0.0"),
            (self.lane_core, "curate_identity", "identity-provenance-v1"),
            (self.lane_preference, "same-context-preference-curation", "1.0.0"),
            (self.lane_reward, "reward_ontology", "reward-ontology-v1"),
            (self.lane_coding, "coding_observability", "1"),
            (self.lane_tag, "tag_taxonomy", "1"),
        ]
        self.manifest_paths = []
        for lane_index in range(len(self.lanes)):
            self.sync_lane_manifest(lane_index)
        with (self.lane_reward / "reward-sidecars.jsonl").open("w", encoding="utf-8") as handle:
            for sidecar in self.reward_sidecars:
                handle.write(json.dumps(sidecar, ensure_ascii=False, sort_keys=True) + "\n")
        self.plan_path = self.root / "plan.json"
        self.plan_path.write_text(
            json.dumps(
                {
                    "schema": "curation-integration-plan/v1",
                    "source_run": "raw",
                    "lanes": [
                        {
                            "bead": "sf-c5l.1",
                            "transform": "bridge_event_time_order",
                            "version": "1.0.0",
                            "outputs": "lane-bridge",
                            "manifest": "lane-bridge/manifest.json",
                        },
                        {
                            "bead": "sf-c5l.2",
                            "transform": "curate_identity",
                            "version": "identity-provenance-v1",
                            "outputs": "lane-core",
                            "manifest": "lane-core/manifest.json",
                        },
                        {
                            "bead": "sf-c5l.3",
                            "transform": "same-context-preference-curation",
                            "version": "1.0.0",
                            "outputs": "lane-preference",
                            "manifest": "lane-preference/manifest.json",
                        },
                        {
                            "bead": "sf-c5l.4",
                            "transform": "reward_ontology",
                            "version": "reward-ontology-v1",
                            "outputs": "lane-reward",
                            "manifest": "lane-reward/manifest.json",
                            "artifacts": [
                                {
                                    "kind": "reward_source_sidecars",
                                    "path": "lane-reward/reward-sidecars.jsonl",
                                    "destination": "reward-sidecars.jsonl",
                                }
                            ],
                        },
                        {
                            "bead": "sf-c5l.5",
                            "transform": "coding_observability",
                            "version": "1",
                            "outputs": "lane-coding",
                            "manifest": "lane-coding/manifest.json",
                        },
                        {
                            "bead": "sf-c5l.6",
                            "transform": "tag_taxonomy",
                            "version": "1",
                            "outputs": "lane-tag",
                            "manifest": "lane-tag/manifest.json",
                        },
                    ],
                },
                indent=2,
            )
        )
        self.cleaned = self.root / "cleaned-v1"
        self.curated = self.root / "curated-v1"

    def source_hash(self, source_path, source_line):
        payload = (self.source_run / source_path).read_bytes().split(b"\n")
        raw_line = payload[source_line - 1]
        if raw_line.endswith(b"\r"):
            raw_line = raw_line[:-1]
        return curate_gate.sha256_hex(raw_line)

    def sync_lane_manifest(self, lane_index, *, extras=()):
        lane_dir, transform, version = self.lanes[lane_index]
        entries = []
        for path in sorted(lane_dir.rglob("*.jsonl")):
            if path.name == "reward-sidecars.jsonl":
                continue
            relative = path.relative_to(lane_dir).as_posix()
            records = _read_jsonl(path)
            if transform == "curate_identity":
                for record in records:
                    canonical = {"kind": "designed", "claimed": None, "basis": "fixture"}
                    kind = curate_identity.record_kind(record)
                    owners = curate_gate._identity_owner_specs(record, kind, "fixture")
                    state_owners = owners or [("/", record)]
                    use_state = any(
                        isinstance(state := owner.get("state"), dict)
                        and ("sim_or_real" in state or "provenance" in state)
                        for _owner_path, owner in state_owners
                    )
                    record["provenance"] = copy.deepcopy(canonical)
                    if use_state:
                        for _owner_path, owner in state_owners:
                            owner["provenance"] = copy.deepcopy(canonical)
                            owner["state"]["provenance"] = copy.deepcopy(canonical)
                    else:
                        for _owner_path, owner in owners:
                            owner["provenance"] = copy.deepcopy(canonical)
                _write_jsonl(path, records)
            for line, record in enumerate(records, 1):
                source_line = (self.source_run / relative).read_bytes().split(b"\n")[line - 1]
                if source_line.endswith(b"\r"):
                    source_line = source_line[:-1]
                entries.append(
                    _lane_manifest_entry(
                        "retained",
                        line,
                        transform=transform,
                        version=version,
                        source_path=relative,
                        record=record,
                        source_record=json.loads(source_line.decode("utf-8")),
                        identity_mappings=transform == "curate_identity",
                        source_hash=self.source_hash(relative, line),
                    )
                )
        if lane_index == 0 and not extras:
            first_excluded = self.bridge_source_records + 1
            extras = (
                _lane_manifest_entry(
                    "quarantine",
                    first_excluded,
                    ["AMBIGUOUS_EVENT_ORDER"],
                ),
                _lane_manifest_entry("excluded", first_excluded + 1, ["INVALID_JSON"]),
            )
        for extra in extras:
            normalized = copy.deepcopy(extra)
            if normalized.get("source_hash") == "0" * 64:
                normalized["source_hash"] = self.source_hash(
                    normalized["source_path"], normalized["source_line"]
                )
            entries.append(normalized)
        manifest_path = lane_dir / "manifest.json"
        manifest_path.write_text(json.dumps(entries, indent=2) + "\n", encoding="utf-8")
        if len(self.manifest_paths) <= lane_index:
            self.manifest_paths.append(manifest_path)
        else:
            self.manifest_paths[lane_index] = manifest_path
        return entries

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

    def promote_report(self, review_path, curated=None):
        return _captured_main(
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
            "version": curate_rewards.ONTOLOGY_VERSION,
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
            (row["factory"], row["kind"], row["decision"])
            for row in sample["strata"]
            if row["evidence"] == "corpus"
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

    def test_sample_stratifies_manifest_evidence_by_exclusion_reason(self):
        fixture = GateFixture(self.root)
        fixture.integrate()
        sample = fixture.sample()

        manifest_strata = [
            row
            for row in sample["strata"]
            if row["evidence"] == "manifest" and row["exclusion_reason"] != "none"
        ]
        self.assertEqual(
            {row["exclusion_reason"] for row in manifest_strata},
            {"AMBIGUOUS_EVENT_ORDER", "INVALID_JSON"},
        )
        self.assertTrue(
            all(
                item.get("manifest_entry")
                for item in sample["items"]
                if item["evidence"] == "manifest"
            )
        )

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
        self.assertFalse((curated / "PROVENANCE.md").exists())

        manifest = json.loads((curated / curate_gate.MANIFEST_FILENAME).read_text())
        self.assertTrue(manifest["training_ready"])
        self.assertEqual(manifest["blockers"], [])
        self.assertEqual(
            curate_gate.manifest_evidence_digest(manifest),
            manifest["evidence_digest"],
        )
        promotion = manifest["promotion"]
        self.assertEqual(promotion["curated_dir"], str(curated))
        self.assertEqual(promotion["records"], 4)
        self.assertEqual(
            promotion["promoter"],
            "pipelines/curate_gate.py immutable-staged-snapshot",
        )
        self.assertEqual(promotion["resorted"], 0)
        self.assertTrue(promotion["corpus_digest"].startswith("sha256:"))
        self.assertEqual(promotion["evidence_digest"], manifest["evidence_digest"])
        self.assertRegex(promotion["integration_manifest_sha256"], r"^[0-9a-f]{64}$")
        self.assertRegex(promotion["review_sample_sha256"], r"^[0-9a-f]{64}$")
        self.assertRegex(promotion["review_sha256"], r"^[0-9a-f]{64}$")
        self.assertRegex(promotion["governance_evidence_digest"], r"^sha256:[0-9a-f]{64}$")
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
        for cleaned_path in curate_gate.jsonl_paths(self.fixture.cleaned):
            relative = cleaned_path.relative_to(self.fixture.cleaned)
            self.assertEqual(
                curate_gate.file_sha256(cleaned_path),
                curate_gate.file_sha256(curated / relative),
            )
        cleaned_governance = self.fixture.cleaned / curate_gate.GOVERNANCE_DIRNAME
        curated_governance = curated / curate_gate.GOVERNANCE_DIRNAME
        self.assertEqual(
            _tree_hashes(cleaned_governance),
            _tree_hashes(curated_governance),
        )
        reward_sidecars = curated_governance / curate_gate.REWARD_SIDECAR_DIRNAME
        self.assertEqual(len(list(reward_sidecars.rglob("*.evidence"))), 1)

    def test_promotion_refuses_an_existing_curated_destination(self):
        review = self.fixture.accepted_review()
        self.fixture.curated.mkdir(parents=True)
        self.assertEqual(self.fixture.promote(review), 2)

    def test_promotion_refuses_a_dangling_destination_symlink(self):
        review = self.fixture.accepted_review()
        target = self.root / "must-not-be-promoted"
        try:
            self.fixture.curated.symlink_to(target, target_is_directory=True)
        except (OSError, NotImplementedError):
            self.skipTest("symlinks are unavailable on this platform")

        code, _report, stderr = self.fixture.promote_report(review)

        self.assertEqual(code, 2)
        self.assertIn("existing curated destination", stderr)
        self.assertFalse(target.exists())

    def test_promotion_atomically_refuses_a_concurrent_destination(self):
        review = self.fixture.accepted_review()
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
            code, _report, stderr = self.fixture.promote_report(review)
        self.assertEqual(code, 2)
        self.assertIn("refusing to overwrite an existing curated destination", stderr)
        self.assertEqual(self.fixture.curated.stat().st_ino, reserved_inodes[0])
        self.assertEqual(list(self.fixture.curated.iterdir()), [])
        self.assertEqual(list(self.root.glob(".curated-v1.staging-*")), [])

    def test_promotion_rejects_a_curated_destination_nested_under_cleaned(self):
        review = self.fixture.accepted_review()
        nested = self.fixture.cleaned / "nested-curated"

        code, _report, stderr = self.fixture.promote_report(review, nested)
        self.assertEqual(code, 2)
        self.assertIn("must be disjoint", stderr)
        self.assertFalse(nested.exists())

    def test_promotion_resolves_symlinked_destination_parents_before_safety_check(self):
        review = self.fixture.accepted_review()
        alias = self.root / "cleaned-alias"
        try:
            alias.symlink_to(self.fixture.cleaned, target_is_directory=True)
        except (OSError, NotImplementedError):
            self.skipTest("symlinks unavailable")
        nested = alias / "nested-curated"

        code, _report, stderr = self.fixture.promote_report(review, nested)
        self.assertEqual(code, 2)
        self.assertIn("must be disjoint", stderr)
        self.assertFalse((self.fixture.cleaned / "nested-curated").exists())

    def test_promotion_refuses_an_unreviewed_sample(self):
        template = self.root / "unreviewed.json"
        template.write_text((self.fixture.cleaned / curate_gate.REVIEW_FILENAME).read_text())
        before = _tree_hashes(self.fixture.cleaned)
        code, report, _stderr = self.fixture.promote_report(template)
        self.assertEqual(code, 1)
        self.assertFalse(self.fixture.curated.exists())
        self.assertTrue(
            any(blocker.startswith("REVIEW_INCOMPLETE:") for blocker in report["blockers"])
        )
        self.assertIn("REVIEW_REVIEWER_MISSING", report["blockers"])
        self.assertEqual(before, _tree_hashes(self.fixture.cleaned))

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
        code, report, _stderr = self.fixture.promote_report(review_path)
        self.assertEqual(code, 1)
        self.assertFalse(self.fixture.curated.exists())
        self.assertIn("REVIEW_REJECTED:1", report["blockers"])

    def test_promotion_refuses_a_review_bound_to_a_different_corpus(self):
        review_path = self.fixture.accepted_review()
        review = json.loads(review_path.read_text())
        review["corpus_digest"] = "sha256:" + "0" * 64
        review_path.write_text(json.dumps(review))
        code, report, _stderr = self.fixture.promote_report(review_path)
        self.assertEqual(code, 1)
        self.assertIn("REVIEW_CORPUS_MISMATCH", report["blockers"])

    def test_promotion_refuses_after_the_corpus_changed_under_the_review(self):
        review = self.fixture.accepted_review()
        extra = self.fixture.cleaned / "thalamic-mini" / "batch-r03.jsonl"
        _write_jsonl(extra, [_thalamic("t-added-after-review")])
        code, report, _stderr = self.fixture.promote_report(review)
        self.assertEqual(code, 1)
        self.assertFalse(self.fixture.curated.exists())
        self.assertIn("REVIEW_CORPUS_MISMATCH", report["blockers"])
        self.assertIn("SAMPLE_CORPUS_MISMATCH", report["blockers"])

    def test_promotion_recomputes_and_rejects_a_reduced_review_sample(self):
        review_path = self.fixture.accepted_review()
        sample_path = self.fixture.cleaned / curate_gate.SAMPLE_FILENAME
        sample = json.loads(sample_path.read_text())
        removed = sample["items"].pop()
        sample["sampled_records"] -= 1
        sample_path.write_text(json.dumps(sample))
        review = json.loads(review_path.read_text())
        review["verdicts"].pop(removed["source"])
        review_path.write_text(json.dumps(review))

        code, report, _stderr = self.fixture.promote_report(review_path)
        self.assertEqual(code, 1)
        self.assertFalse(self.fixture.curated.exists())
        self.assertIn("SAMPLE_SELECTION_MISMATCH", report["blockers"])

    def test_promotion_rebuilds_review_candidates_from_copied_lane_evidence(self):
        manifest_path = self.fixture.cleaned / curate_gate.MANIFEST_FILENAME
        manifest = json.loads(manifest_path.read_text())
        manifest["exclusions"] = []
        manifest["review_candidates"] = []
        manifest["exclusion_reason_codes"] = {}
        manifest["counts"]["exclusions"] = 0
        manifest["evidence_digest"] = curate_gate.manifest_evidence_digest(manifest)

        sample = curate_gate.build_sample(
            self.fixture.cleaned,
            manifest["review_sampling"]["per_stratum"],
            [],
            evidence_digest=manifest["evidence_digest"],
        )
        sample["cleaned_dir"] = str(self.fixture.cleaned)
        manifest["review_sampling"]["sample_sha256"] = curate_gate.sha256_hex(
            curate_gate.training_audit.canonical_blob(sample).encode("utf-8")
        )
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
        (self.fixture.cleaned / curate_gate.SAMPLE_FILENAME).write_text(
            json.dumps(sample, indent=2) + "\n"
        )
        review = curate_gate.review_template(sample)
        review["reviewer"] = "evidence-attacker"
        review["reviewed_at"] = "2026-08-25T00:00:00Z"
        for source in review["verdicts"]:
            review["verdicts"][source] = {"verdict": "accept", "notes": ""}
        review_path = self.root / "tampered-review.json"
        review_path.write_text(json.dumps(review, indent=2) + "\n")

        code, report, _stderr = self.fixture.promote_report(review_path)
        self.assertEqual(code, 1)
        self.assertFalse(self.fixture.curated.exists())
        self.assertIn("LANE_EVIDENCE_SUMMARY_MISMATCH", report["blockers"])
        self.assertIn("SAMPLE_SELECTION_MISMATCH", report["blockers"])

    def test_promotion_rejects_tampered_copied_reward_evidence(self):
        review = self.fixture.accepted_review()
        sidecar = next(
            (
                self.fixture.cleaned
                / curate_gate.GOVERNANCE_DIRNAME
                / curate_gate.REWARD_SIDECAR_DIRNAME
            ).rglob("*.evidence")
        )
        sidecar.write_bytes(sidecar.read_bytes() + b"\n")

        code, _report, stderr = self.fixture.promote_report(review)
        self.assertEqual(code, 2)
        self.assertIn("artifact hash mismatch", stderr)
        self.assertFalse(self.fixture.curated.exists())

    def test_promotion_requires_an_integrated_cleaned_destination(self):
        review = self.fixture.accepted_review()
        (self.fixture.cleaned / curate_gate.MANIFEST_FILENAME).unlink()
        self.assertEqual(self.fixture.promote(review), 2)

    def test_promotion_never_writes_into_the_cleaned_corpus(self):
        review = self.fixture.accepted_review()
        before = _tree_hashes(self.fixture.cleaned)
        self.assertEqual(self.fixture.promote(review), 0)
        after = _tree_hashes(self.fixture.cleaned)
        self.assertEqual(before, after)

    def test_promotion_validates_and_publishes_one_immutable_snapshot(self):
        review = self.fixture.accepted_review()
        corpus_path = self.fixture.cleaned / "thalamic-mini" / "batch-r02.jsonl"
        sidecar_path = next(
            (
                self.fixture.cleaned
                / curate_gate.GOVERNANCE_DIRNAME
                / curate_gate.REWARD_SIDECAR_DIRNAME
            ).rglob("*.evidence")
        )
        manifest_path = self.fixture.cleaned / curate_gate.MANIFEST_FILENAME
        sample_path = self.fixture.cleaned / curate_gate.SAMPLE_FILENAME
        expected_corpus = corpus_path.read_bytes()
        expected_sidecar = sidecar_path.read_bytes()
        expected_review = review.read_bytes()
        expected_manifest = manifest_path.read_bytes()
        expected_sample = sample_path.read_bytes()
        original_run_gates = curate_gate.run_gates
        mutated = False

        def mutate_sources_after_snapshot(cleaned, **kwargs):
            nonlocal mutated
            if not mutated:
                mutated = True
                records = _read_jsonl(corpus_path)
                records[0]["state"]["env"] = "mutated after immutable snapshot"
                _write_jsonl(corpus_path, records)
                sidecar_path.write_bytes(expected_sidecar + b"\n")
                review.write_text('{"reviewer":"attacker"}\n')
            return original_run_gates(cleaned, **kwargs)

        with mock.patch.object(
            curate_gate,
            "run_gates",
            side_effect=mutate_sources_after_snapshot,
        ):
            self.assertEqual(self.fixture.promote(review), 0)

        curated_corpus = self.fixture.curated / corpus_path.relative_to(self.fixture.cleaned)
        curated_sidecar = self.fixture.curated / sidecar_path.relative_to(self.fixture.cleaned)
        self.assertEqual(curated_corpus.read_bytes(), expected_corpus)
        self.assertEqual(curated_sidecar.read_bytes(), expected_sidecar)
        self.assertEqual(
            (self.fixture.curated / curate_gate.REVIEW_FILENAME).read_bytes(),
            expected_review,
        )
        manifest = json.loads((self.fixture.curated / curate_gate.MANIFEST_FILENAME).read_text())
        promotion = manifest["promotion"]
        self.assertEqual(
            promotion["integration_manifest_sha256"],
            curate_gate.sha256_hex(expected_manifest),
        )
        self.assertEqual(
            promotion["review_sample_sha256"],
            curate_gate.sha256_hex(expected_sample),
        )
        self.assertEqual(
            promotion["review_sha256"],
            curate_gate.sha256_hex(expected_review),
        )

    def test_promotion_rejects_a_staged_mutation_during_output_inventory(self):
        review = self.fixture.accepted_review()
        original = curate_gate._promotion_outputs
        mutated = False

        def mutate_after_inventory(staged):
            nonlocal mutated
            entries = original(staged)
            if not mutated:
                mutated = True
                corpus = staged / "thalamic-mini" / "batch-r02.jsonl"
                corpus.write_text("{invalid-json\n", encoding="utf-8")
            return entries

        with mock.patch.object(
            curate_gate,
            "_promotion_outputs",
            side_effect=mutate_after_inventory,
        ):
            code, _report, stderr = self.fixture.promote_report(review)
        self.assertEqual(code, 2)
        self.assertIn("staged corpus changed after final promotion validation", stderr)
        self.assertFalse(self.fixture.curated.exists())

    def test_promotion_publisher_reauthenticates_after_the_final_inventory(self):
        review = self.fixture.accepted_review()
        original = curate_gate._promotion_outputs
        inventories = 0

        def mutate_after_final_inventory(staged):
            nonlocal inventories
            entries = original(staged)
            inventories += 1
            if inventories == 2:
                corpus = staged / "thalamic-mini" / "batch-r02.jsonl"
                corpus.write_text("{invalid-json\n", encoding="utf-8")
            return entries

        with mock.patch.object(
            curate_gate,
            "_promotion_outputs",
            side_effect=mutate_after_final_inventory,
        ):
            code, _report, stderr = self.fixture.promote_report(review)

        self.assertEqual(inventories, 2)
        self.assertEqual(code, 2)
        self.assertIn("staging tree changed after final validation", stderr)
        self.assertFalse(self.fixture.curated.exists())

    def test_promotion_publisher_reauthenticates_the_staging_tree(self):
        review = self.fixture.accepted_review()
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
            code, _report, stderr = self.fixture.promote_report(review)

        self.assertEqual(code, 2)
        self.assertIn("staging tree changed after final validation", stderr)
        self.assertFalse(self.fixture.curated.exists())


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
