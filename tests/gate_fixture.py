#!/usr/bin/env python3
"""Shared six-lane fixtures for curation-gate tests."""

import io
import copy
import json
import sys
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PIPELINES = REPO / "pipelines"
GATE_SCRIPT = PIPELINES / "curate_gate.py"

if str(PIPELINES) not in sys.path:
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

