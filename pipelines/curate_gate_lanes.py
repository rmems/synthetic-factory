#!/usr/bin/env python3
"""Lane authentication for the curation gate.

Split out of ``curate_gate.py`` (CodeScene: Lines of Code in a Single File) by
responsibility; ``_prepare_lane`` and ``prepare_lanes`` are re-exported from
``curate_gate`` so existing call sites resolve unchanged.

Every lane must pair its output tree with a record-level manifest. Preparing
a lane authenticates each manifest entry against the immutable source record
it names, reads every emitted output record, proves the two sides agree by
``(path, digest)`` multiset, binds each emitted record to its manifest entry,
and captures the lane's governance artifacts. The refusals fire in exactly the
order the phases below are named.
"""

from __future__ import annotations

import copy
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, NamedTuple

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("curate_gate_lanes")
    from . import curate_gate_contract as _contract
    from . import curate_gate_digest as _digest
    from . import curate_gate_evidence as _evidence
    from . import curate_gate_identity_gate as _identity_gate
    from . import curate_gate_manifests as _manifests
    from . import curate_gate_merge as _merge
    from . import curate_gate_paths as _paths
    from . import curate_rewards
    from .check_records import canonical_record_id, reject_json_constant
    from .exact_json import parse_finite_json_float
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "curate_gate_lanes"
    )
    _PIPELINES = Path(__file__).resolve().parent
    if str(_PIPELINES) not in sys.path:
        sys.path.insert(0, str(_PIPELINES))
    import curate_gate_contract as _contract
    import curate_gate_digest as _digest
    import curate_gate_evidence as _evidence
    import curate_gate_identity_gate as _identity_gate
    import curate_gate_manifests as _manifests
    import curate_gate_merge as _merge
    import curate_gate_paths as _paths
    import curate_rewards
    from check_records import canonical_record_id, reject_json_constant
    from exact_json import parse_finite_json_float

GateError = _contract.GateError
EXCLUSION_ACTIONS = _contract.EXCLUSION_ACTIONS
QUARANTINE_ACTIONS = _contract.QUARANTINE_ACTIONS
REPAIR_ACTIONS = _contract.REPAIR_ACTIONS
NO_OUTPUT_ACTIONS = _contract.NO_OUTPUT_ACTIONS
OUTPUT_ACTIONS = _contract.OUTPUT_ACTIONS
KNOWN_ACTIONS = _contract.KNOWN_ACTIONS
REWARD_CALIBRATION_KIND = _contract.REWARD_CALIBRATION_KIND
record_sha256 = _digest.record_sha256
_all_jsonl_paths = _digest._all_jsonl_paths
_lf_lines = _digest._lf_lines
_normalized_sha256 = _digest._normalized_sha256
_read_regular_file_snapshot = _digest._read_regular_file_snapshot
_assert_no_symlink = _paths._assert_no_symlink
_logical_source_path = _paths._logical_source_path
_load_source_records = _merge._load_source_records
_manifest_entries = _manifests._manifest_entries
_normalize_entry = _manifests._normalize_entry
_load_reward_sidecars = _evidence._load_reward_sidecars
_authenticate_identity_source_claims = _identity_gate._authenticate_identity_source_claims

# The preference lane's outputs are matched by digest alone: its records are
# re-paired across source files, so the source path is not part of identity.
_PATHLESS_MATCH_TRANSFORM = "same-context-preference-curation"

_PathHash = tuple[str, str]
_SourceKey = tuple[str, int]


def _lane_tag(lane: dict[str, Any]) -> str:
    return f"lane {lane['order']} ({lane['transform']})"


def _match_path(lane: dict[str, Any], path: str) -> str:
    return "" if lane["transform"] == _PATHLESS_MATCH_TRANSFORM else path


# ---------------------------------------------------------------------------
# manifest side: one authenticated entry per source identity
# ---------------------------------------------------------------------------


def _entry_action(entry: dict[str, Any], label: str) -> str:
    """The normalized action, with its reason codes checked against the action class."""
    raw_action = entry.get("action")
    if not isinstance(raw_action, str) or not raw_action.strip():
        raise GateError(f"{label} needs an explicit action")
    action = raw_action.strip().lower()
    if action not in KNOWN_ACTIONS:
        raise GateError(f"{label} has unsupported action {raw_action!r}")
    entry["action"] = action
    reasons = entry.get("reason_codes")
    if not isinstance(reasons, list) or any(
        not isinstance(reason, str) or not reason.strip() for reason in reasons
    ):
        raise GateError(f"{label} reason_codes must be a list of non-empty strings")
    if action in REPAIR_ACTIONS | NO_OUTPUT_ACTIONS and not reasons:
        raise GateError(f"{label} action {action!r} needs at least one reason code")
    return action


def _assert_entry_transform(entry: dict[str, Any], lane: dict[str, Any], label: str) -> None:
    """An entry must declare the lane's own transform at the lane's own version."""
    if entry["declared_transform"] != lane["transform"]:
        raise GateError(
            f"{label} declares transform {entry['declared_transform']!r}; "
            f"expected {lane['transform']!r}"
        )
    if entry["declared_version"] != lane["version"]:
        raise GateError(
            f"{label} declares version {entry['declared_version']!r}; "
            f"expected {lane['version']!r}"
        )


def _bind_entry_source(
    entry: dict[str, Any],
    label: str,
    source_records: dict[_SourceKey, dict[str, Any]],
    seen_sources: set[_SourceKey],
) -> dict[str, Any]:
    """Resolve the entry's source identity to one authenticated source record."""
    source_path = _logical_source_path(entry["source_path"], f"{label} source_path")
    source_line = entry["source_line"]
    if not isinstance(source_line, int) or isinstance(source_line, bool) or source_line < 1:
        raise GateError(f"{label} source_line must be a positive integer")
    source_key = (source_path, source_line)
    if source_key in seen_sources:
        raise GateError(f"{label} duplicates source identity {source_path}:{source_line}")
    seen_sources.add(source_key)
    entry["source_path"] = source_path
    entry["source_hash"] = _normalized_sha256(entry.get("source_hash"), f"{label} source hash")
    source = source_records.get(source_key)
    if source is None:
        raise GateError(f"{label} source identity is absent from the declared source_run")
    if entry["source_hash"] != source["source_hash"]:
        raise GateError(f"{label} source hash does not match the declared source_run bytes")
    entry["_source_key"] = source_key
    entry["_source_record"] = source["record"]
    entry["_source_bytes"] = source.get("source_bytes")
    return source


class _EntryScope(NamedTuple):
    """One manifest entry's lane, its resolved source line, and how it is labelled."""

    lane: dict[str, Any]
    source: dict[str, Any]
    action: str
    label: str


def _entry_output_hash(entry: dict[str, Any], scope: _EntryScope) -> str | None:
    """The normalized output digest, or ``None`` for an action that emits nothing."""
    lane, source, action, label = scope
    output_hash = entry.get("output_hash")
    if output_hash is None:
        if action not in NO_OUTPUT_ACTIONS:
            raise GateError(f"{label} action {action!r} has no authenticated output hash")
        return None
    if action not in OUTPUT_ACTIONS:
        raise GateError(f"{label} action {action!r} cannot declare an output hash")
    if source["record"] is None:
        raise GateError(
            f"{label} cannot emit a record for an unparseable source line: "
            f"{source['parse_error']}"
        )
    output_hash = _normalized_sha256(output_hash, f"{label} output hash")
    entry["output_hash"] = output_hash
    if lane["transform"] == "curate_identity":
        entry["_source_originals_sha256"] = _authenticate_identity_source_claims(
            entry,
            source["record"],
            label,
        )
    return output_hash


def _authenticate_manifest(
    lane: dict[str, Any],
    manifest_payload: bytes,
    source_records: dict[_SourceKey, dict[str, Any]],
) -> tuple[list[dict[str, Any]], dict[_PathHash, list[dict[str, Any]]]]:
    """Every manifest entry in order, plus the emitting ones keyed by (path, digest)."""
    manifest_path = lane["manifest_path"]
    entries: list[dict[str, Any]] = []
    expected_by_path_hash: dict[_PathHash, list[dict[str, Any]]] = defaultdict(list)
    seen_sources: set[_SourceKey] = set()
    raw_entries = _manifest_entries(
        manifest_path,
        lane["manifest_format"],
        payload=manifest_payload,
    )
    for index, raw_entry in enumerate(raw_entries, 1):
        entry = _normalize_entry(raw_entry, lane)
        label = f"{manifest_path}: entry {index}"
        action = _entry_action(entry, label)
        _assert_entry_transform(entry, lane, label)
        source = _bind_entry_source(entry, label, source_records, seen_sources)
        output_hash = _entry_output_hash(entry, _EntryScope(lane, source, action, label))
        if output_hash is not None:
            match_path = _match_path(lane, entry["source_path"])
            expected_by_path_hash[(match_path, output_hash)].append(entry)
        entries.append(entry)
    return entries, expected_by_path_hash


# ---------------------------------------------------------------------------
# output side: every emitted record, keyed the same way
# ---------------------------------------------------------------------------


def _lane_payload_paths(lane: dict[str, Any]) -> list[Path]:
    """The lane's corpus files: every *.jsonl that is not the manifest or an artifact."""
    outputs_dir = lane["outputs_dir"]
    excluded_paths = {lane["manifest_path"], *(item["source_path"] for item in lane["artifacts"])}
    payload_paths = [path for path in _all_jsonl_paths(outputs_dir) if path not in excluded_paths]
    if not payload_paths:
        raise GateError(f"{_lane_tag(lane)} contributed no corpus *.jsonl: {outputs_dir}")
    return payload_paths


def _lane_output_record(path: Path, line_number: int, line: str) -> Any:
    try:
        return json.loads(
            line,
            parse_constant=reject_json_constant,
            parse_float=parse_finite_json_float,
        )
    except ValueError as exc:
        raise GateError(f"{path}:{line_number}: invalid lane output JSON: {exc}") from exc


def _read_lane_output(
    lane: dict[str, Any],
    path: Path,
    actual_by_path_hash: dict[_PathHash, list[dict[str, Any]]],
) -> dict[str, Any]:
    """Index one output file's records by (path, digest); return its input-file row."""
    outputs_dir = lane["outputs_dir"]
    _assert_no_symlink(outputs_dir, path, f"{_lane_tag(lane)} output")
    relative = path.relative_to(outputs_dir).as_posix()
    records = 0
    payload, payload_sha256, payload_bytes = _read_regular_file_snapshot(
        path,
        f"{_lane_tag(lane)} output",
    )
    try:
        text = payload.decode("utf-8")
    except UnicodeError as exc:
        raise GateError(f"cannot decode lane output {path}: {exc}") from exc
    for line_number, line in enumerate(_lf_lines(text), 1):
        if not line.strip():
            continue
        records += 1
        record = _lane_output_record(path, line_number, line)
        digest = record_sha256(record)
        actual_by_path_hash[(_match_path(lane, relative), digest)].append(
            {
                "relative_path": relative,
                "output_line": line_number,
                "record": record,
                "output_hash": digest,
            }
        )
    return {
        "lane_order": lane["order"],
        "transform": lane["transform"],
        "path": relative,
        "sha256": payload_sha256,
        "bytes": payload_bytes,
        "records": records,
    }


def _read_lane_outputs(
    lane: dict[str, Any],
) -> tuple[dict[_PathHash, list[dict[str, Any]]], list[dict[str, Any]]]:
    actual_by_path_hash: dict[_PathHash, list[dict[str, Any]]] = defaultdict(list)
    input_files: list[dict[str, Any]] = []
    for path in _lane_payload_paths(lane):
        input_files.append(_read_lane_output(lane, path, actual_by_path_hash))
    return actual_by_path_hash, input_files


# ---------------------------------------------------------------------------
# binding: the two sides must agree as multisets, then pair off in order
# ---------------------------------------------------------------------------


def _assert_output_counts(
    lane: dict[str, Any],
    expected_by_path_hash: dict[_PathHash, list[dict[str, Any]]],
    actual_by_path_hash: dict[_PathHash, list[dict[str, Any]]],
) -> None:
    expected_counts = Counter({key: len(items) for key, items in expected_by_path_hash.items()})
    actual_counts = Counter({key: len(items) for key, items in actual_by_path_hash.items()})
    if expected_counts != actual_counts:
        missing = [
            f"{path}@{digest}"
            for path, digest in sorted((expected_counts - actual_counts).elements())[:10]
        ]
        extra = [
            f"{path}@{digest}"
            for path, digest in sorted((actual_counts - expected_counts).elements())[:10]
        ]
        raise GateError(
            f"{_lane_tag(lane)} output records do not match "
            f"its manifest: missing_hashes={missing}, extra_hashes={extra}"
        )


def _bound_record(
    lane: dict[str, Any], entry: dict[str, Any], emitted: dict[str, Any]
) -> dict[str, Any]:
    """One emitted record joined to the manifest entry that authenticates it."""
    actual_output_id = canonical_record_id(emitted["record"])
    if entry.get("output_id") != actual_output_id:
        raise GateError(
            f"{lane['manifest_path']}: output_id {entry.get('output_id')!r} does not "
            f"match authenticated output record {emitted['relative_path']}:"
            f"{emitted['output_line']} id {actual_output_id!r}"
        )
    source_record_sha256 = record_sha256(entry["_source_record"])
    entry["content_changed"] = emitted["output_hash"] != source_record_sha256
    return {
        **emitted,
        "source_path": entry["source_path"],
        "source_line": entry["source_line"],
        "source_key": entry["_source_key"],
        "source_record": copy.deepcopy(entry["_source_record"]),
        "source_bytes": entry.get("_source_bytes"),
        "source_hash": entry["source_hash"],
        "source_record_sha256": source_record_sha256,
        "output_id": actual_output_id,
        "lane_order": lane["order"],
        "transform": lane["transform"],
        "version": lane["version"],
    }


def _bind_output_records(
    lane: dict[str, Any],
    expected_by_path_hash: dict[_PathHash, list[dict[str, Any]]],
    actual_by_path_hash: dict[_PathHash, list[dict[str, Any]]],
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for path_digest in sorted(expected_by_path_hash):
        expected = sorted(expected_by_path_hash[path_digest], key=lambda item: item["_source_key"])
        actual = sorted(
            actual_by_path_hash[path_digest],
            key=lambda item: (item["relative_path"], item["output_line"]),
        )
        if lane["transform"] == _PATHLESS_MATCH_TRANSFORM and len(expected) > 1:
            sources = [f"{item['source_path']}:{item['source_line']}" for item in expected]
            raise GateError(
                "same-context preference manifest maps multiple source identities to one "
                f"indistinguishable output digest {path_digest[1]}: {sources}"
            )
        for entry, emitted in zip(expected, actual):
            records.append(_bound_record(lane, entry, emitted))
    return records


# ---------------------------------------------------------------------------
# governance artifacts declared by the lane
# ---------------------------------------------------------------------------


def _prepare_artifact(lane: dict[str, Any], artifact: dict[str, Any]) -> dict[str, Any]:
    """Capture one artifact's bytes and validate it by kind."""
    artifact_payload, artifact_sha256, artifact_bytes = _read_regular_file_snapshot(
        artifact["source_path"],
        f"{_lane_tag(lane)} governance artifact",
    )
    catalog: dict[str, dict[str, Any]] | None = None
    if artifact["kind"] == REWARD_CALIBRATION_KIND:
        try:
            catalog = curate_rewards.load_units_migration_bytes(
                artifact_payload,
                label=str(artifact["source_path"]),
            )
        except curate_rewards.RewardOntologyError as exc:
            raise GateError(
                f"lane {lane['order']} calibration artifact is invalid: {exc}"
            ) from exc
        documents = []
    else:
        documents = _load_reward_sidecars(
            artifact["source_path"],
            payload=artifact_payload,
        )
    return {
        **artifact,
        "_payload": artifact_payload,
        "_sha256": artifact_sha256,
        "_bytes": artifact_bytes,
        "_documents": len(documents),
        "_catalog": catalog,
    }


# ---------------------------------------------------------------------------
# the lane, phase by phase
# ---------------------------------------------------------------------------


def _prepare_lane(
    lane: dict[str, Any], source_records: dict[_SourceKey, dict[str, Any]]
) -> dict[str, Any]:
    """Authenticate one lane's emitted records against its declared manifest."""
    manifest_payload, manifest_sha256, manifest_bytes = _read_regular_file_snapshot(
        lane["manifest_path"],
        f"{_lane_tag(lane)} manifest",
    )
    entries, expected_by_path_hash = _authenticate_manifest(lane, manifest_payload, source_records)
    actual_by_path_hash, input_files = _read_lane_outputs(lane)
    _assert_output_counts(lane, expected_by_path_hash, actual_by_path_hash)
    records = _bind_output_records(lane, expected_by_path_hash, actual_by_path_hash)
    if not records:
        raise GateError(f"{_lane_tag(lane)} contributed zero records: {lane['outputs_dir']}")
    prepared_artifacts = [_prepare_artifact(lane, artifact) for artifact in lane["artifacts"]]
    return {
        **lane,
        "artifacts": prepared_artifacts,
        "entries": entries,
        "records": sorted(
            records,
            key=lambda item: (item["relative_path"], item["output_line"]),
        ),
        "input_files": input_files,
        "manifest_payload": manifest_payload,
        "manifest_sha256": manifest_sha256,
        "manifest_bytes": manifest_bytes,
    }


def prepare_lanes(plan: dict[str, Any]) -> list[dict[str, Any]]:
    source_records = _load_source_records(plan["source_run_dir"])
    prepared = [_prepare_lane(lane, source_records) for lane in plan["lanes"]]
    dispositioned = {emitted["source_key"] for lane in prepared for emitted in lane["records"]}
    dispositioned.update(
        entry["_source_key"]
        for lane in prepared
        for entry in lane["entries"]
        if str(entry.get("action") or "").strip().lower() in EXCLUSION_ACTIONS | QUARANTINE_ACTIONS
    )
    missing = sorted(set(source_records) - dispositioned)
    if missing:
        preview = [f"{path}:{line}" for path, line in missing[:10]]
        raise GateError(
            "source_run records lack a retained output or an explicit exclusion/quarantine: "
            f"count={len(missing)}, first={preview}"
        )
    prepared[0]["_completion_source"] = plan["source_run_dir"]
    return prepared


if __package__:
    _expose_package_sibling(__name__)
