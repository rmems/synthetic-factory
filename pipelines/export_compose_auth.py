#!/usr/bin/env python3
"""COMPOSE.json authentication: prove published compose evidence byte-exactly.

Split out of ``export_hf.py`` by responsibility. Before anything is exported,
every declared output path, digest, count, coordinate, sidecar, and
annotation link in COMPOSE.json is checked against the emitted bytes, and the
deterministic compose contract is replayed from every current source line.
"""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path
from typing import Any, Mapping, Sequence

_PIPELINES = Path(__file__).resolve().parent
if str(_PIPELINES) not in sys.path:
    sys.path.insert(0, str(_PIPELINES))

import compose_curated  # noqa: E402
import curate_rewards  # noqa: E402
from dataclasses import dataclass  # noqa: E402
from export_contract import (  # noqa: E402
    CURATED_DIRNAME,
    CuratedFile,
    ExportError,
    _loads_json,
)
from export_members import (  # noqa: E402
    _authenticated_descriptor,
    _read_exact_regular_file,
)
from export_replay import _authenticate_source_replay  # noqa: E402

_MANIFEST_OUTPUT_FIELDS = (
    "output_path",
    "output_line",
    "output_id",
    "output_sha256",
    "reward_sidecar_id",
)


@dataclass(frozen=True)
class _ManifestRow:
    """One retained manifest entry bound to the exported row it names."""

    entry: Mapping[str, Any]
    index: int
    coordinate: tuple[str, int]
    record: Any

    @property
    def label(self) -> str:
        return f"compose manifest entry {self.index + 1}"


def _decoded_compose_summary(summary_path: Path, summary_payload: bytes) -> dict[str, Any]:
    """Decode COMPOSE.json's exact bytes into one summary object."""

    try:
        summary_text = summary_payload.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ExportError(f"{summary_path}: compose summary is not UTF-8: {exc}") from exc
    summary = _loads_json(summary_text, str(summary_path))
    if not isinstance(summary, dict):
        raise ExportError(f"{summary_path}: compose summary must be an object")
    return summary


def _require_compose_contract(summary: dict[str, Any], curated_root: Path) -> None:
    """Require the summary to declare exactly this compose contract and root."""

    if summary.get("compose_name") != compose_curated.COMPOSE_NAME:
        raise ExportError("COMPOSE.json: unexpected compose_name")
    if summary.get("compose_version") != compose_curated.COMPOSE_VERSION:
        raise ExportError(
            "COMPOSE.json: compose_version does not match this export contract"
        )
    if summary.get("lane_order") != list(compose_curated.LANE_ORDER):
        raise ExportError("COMPOSE.json: lane_order does not match the compose contract")
    if summary.get("destination") != str(curated_root.resolve()):
        raise ExportError("COMPOSE.json: destination does not name this curated root")


def _authenticated_compose_summary(
    curated_root: Path,
) -> tuple[Path, bytes, dict[str, Any]]:
    """Read COMPOSE.json and prove it declares this compose contract."""

    summary_path, summary_payload = _read_exact_regular_file(
        curated_root,
        compose_curated.SUMMARY_FILENAME,
        "COMPOSE summary",
    )
    summary = _decoded_compose_summary(summary_path, summary_payload)
    _require_compose_contract(summary, curated_root)
    return summary_path, summary_payload, summary


def _curated_outputs_by_compose_path(
    curated_files: Sequence[CuratedFile],
) -> dict[str, CuratedFile]:
    """Key the exported payload files by the compose path that produced them."""

    actual_outputs: dict[str, CuratedFile] = {}
    prefix = f"{CURATED_DIRNAME}/"
    for curated in curated_files:
        if not curated.source_file.startswith(prefix):
            raise ExportError(f"invalid curated source path: {curated.source_file}")
        compose_path = (
            f"{compose_curated.RECORDS_DIRNAME}/"
            f"{curated.source_file.removeprefix(prefix)}"
        )
        actual_outputs[compose_path] = curated
    return actual_outputs


def _snapshot_bound_output(
    raw_path: Any,
    current_payload: bytes,
    actual_outputs: Mapping[str, CuratedFile],
) -> CuratedFile:
    """Bind one declared output path to the snapshot already captured."""

    curated = actual_outputs.get(raw_path)
    if curated is None:
        raise ExportError(f"COMPOSE.json: undeclared or non-payload output {raw_path!r}")
    if current_payload != curated.payload:
        raise ExportError(
            f"COMPOSE.json: output identity changed after snapshot capture: {raw_path}"
        )
    return curated


def _authenticated_output_row(
    raw_path: Any, entry: Mapping[str, Any], curated: CuratedFile
) -> dict[str, Any]:
    """Prove one output's declared digest and record count against the snapshot.

    The digest binds to the same immutable snapshot already parsed into
    ``curated`` and later written to the export, avoiding a second file read
    with different bytes under a concurrent source mutation.
    """

    digest = hashlib.sha256(curated.payload).hexdigest()
    if entry.get("sha256") != digest:
        raise ExportError(f"COMPOSE.json: output digest mismatch for {raw_path}")
    records = entry.get("records")
    if isinstance(records, bool) or not isinstance(records, int) or records < 1:
        raise ExportError(f"COMPOSE.json: invalid record count for {raw_path}")
    if records != len(curated.rows):
        raise ExportError(
            f"COMPOSE.json: output record count mismatch for {raw_path}"
        )
    return {"path": raw_path, "records": records, "sha256": digest}


def _authenticated_output_declarations(
    curated_root: Path,
    summary: Mapping[str, Any],
    actual_outputs: Mapping[str, CuratedFile],
) -> list[dict[str, Any]]:
    """Prove every declared output against the snapshot already captured."""

    declared_outputs = summary.get("outputs")
    if not isinstance(declared_outputs, list):
        raise ExportError("COMPOSE.json: outputs must be a list")
    authenticated_outputs: list[dict[str, Any]] = []
    seen_output_paths: set[str] = set()
    for index, entry in enumerate(declared_outputs):
        if not isinstance(entry, dict):
            raise ExportError(f"COMPOSE.json: outputs[{index}] must be an object")
        raw_path = entry.get("path")
        _path, current_payload = _read_exact_regular_file(
            curated_root, raw_path, f"COMPOSE outputs[{index}]"
        )
        if raw_path in seen_output_paths:
            raise ExportError(f"COMPOSE.json: duplicate output path {raw_path!r}")
        seen_output_paths.add(raw_path)
        curated = _snapshot_bound_output(raw_path, current_payload, actual_outputs)
        authenticated_outputs.append(
            _authenticated_output_row(raw_path, entry, curated)
        )
    if seen_output_paths != set(actual_outputs):
        missing = sorted(set(actual_outputs) - seen_output_paths)
        raise ExportError(f"COMPOSE.json: payload outputs missing from summary: {missing}")
    return authenticated_outputs


def _validated_sidecars_by_id(
    sidecar_documents: Sequence[Any],
) -> dict[str, dict[str, Any]]:
    """Every reward sidecar, ontology-validated and unique by sidecar id."""

    sidecars_by_id: dict[str, dict[str, Any]] = {}
    for index, document in enumerate(sidecar_documents):
        try:
            curate_rewards.validate_ontology_document(document)
        except curate_rewards.RewardOntologyError as exc:
            raise ExportError(f"reward sidecar {index + 1} is invalid: {exc}") from exc
        sidecar_id = document["sidecar_id"]
        if sidecar_id in sidecars_by_id:
            raise ExportError(f"duplicate reward sidecar id {sidecar_id}")
        sidecars_by_id[sidecar_id] = document
    return sidecars_by_id


def _assert_manifest_entry_contract(entry: Any, index: int) -> None:
    """Every manifest entry must declare the compose contract being exported."""

    if not isinstance(entry, dict):
        raise ExportError(f"compose manifest entry {index + 1} must be an object")
    for field_name, expected in (
        ("compose_name", compose_curated.COMPOSE_NAME),
        ("compose_version", compose_curated.COMPOSE_VERSION),
        ("lane_order", list(compose_curated.LANE_ORDER)),
    ):
        if entry.get(field_name) != expected:
            raise ExportError(
                f"compose manifest entry {index + 1} has an unexpected {field_name}"
            )


def _assert_excluded_row_claims_no_output(entry: Mapping[str, Any], index: int) -> None:
    """An excluded row may not claim an output, an id, or a reward sidecar."""

    if any(entry.get(field_name) is not None for field_name in _MANIFEST_OUTPUT_FIELDS):
        raise ExportError(
            f"compose manifest entry {index + 1} gives an excluded row output"
        )


def _manifest_output_coordinate(
    entry: Mapping[str, Any], index: int, seen: set[tuple[str, int]]
) -> tuple[str, int]:
    """The unique ``(path, line)`` coordinate a retained row occupies."""

    output_path = entry.get("output_path")
    output_line = entry.get("output_line")
    if (
        not isinstance(output_path, str)
        or isinstance(output_line, bool)
        or not isinstance(output_line, int)
    ):
        raise ExportError(
            f"compose manifest entry {index + 1} has an invalid output coordinate"
        )
    coordinate = (output_path, output_line)
    if coordinate in seen:
        raise ExportError(f"duplicate compose manifest coordinate {coordinate}")
    return coordinate


def _authenticated_manifest_record(
    entry: Mapping[str, Any],
    coordinate: tuple[str, int],
    actual_outputs: Mapping[str, CuratedFile],
) -> Any:
    """Resolve one coordinate to its exported row and prove digest and id."""

    output_path, output_line = coordinate
    curated = actual_outputs.get(output_path)
    if curated is None or not 1 <= output_line <= len(curated.rows):
        raise ExportError(f"compose manifest coordinate does not resolve: {coordinate}")
    row = curated.rows[output_line - 1]
    digest = hashlib.sha256(row.record_json.encode("utf-8")).hexdigest()
    if entry.get("output_sha256") != digest:
        raise ExportError(f"compose manifest output digest mismatch: {coordinate}")
    record = _loads_json(row.record_json, f"compose output {coordinate}")
    output_id = record.get("id") if isinstance(record, dict) else None
    if not isinstance(output_id, str) or entry.get("output_id") != output_id:
        raise ExportError(f"compose manifest output id mismatch: {coordinate}")
    return record


def _authenticated_manifest_sidecar(
    row: _ManifestRow, sidecars_by_id: Mapping[str, dict[str, Any]]
) -> str | None:
    """Bind one retained row to the reward sidecar it claims, if any."""

    sidecar_id = row.entry.get("reward_sidecar_id")
    if sidecar_id is None:
        # A reward annotation with no sidecar to authenticate it would be an
        # unprovable claim about the record's reward.
        if isinstance(row.record, dict) and curate_rewards.ANNOTATION_FIELD in row.record:
            raise ExportError(
                f"compose output {row.coordinate} has an unmanifested reward annotation"
            )
        return None
    if not isinstance(sidecar_id, str):
        raise ExportError(f"{row.label} has an invalid reward sidecar id")
    if sidecar_id not in sidecars_by_id:
        raise ExportError(
            f"compose manifest references missing reward sidecar {sidecar_id}"
        )
    _require_sidecar_restores(row, sidecar_id, sidecars_by_id[sidecar_id])
    return sidecar_id


def _require_sidecar_restores(
    row: _ManifestRow, sidecar_id: str, sidecar: dict[str, Any]
) -> None:
    """The claimed sidecar must name the same source and restore the record."""

    sidecar_source = sidecar["source"]
    if sidecar_source.get("path") != row.entry.get("source_path") or sidecar_source.get(
        "line"
    ) != row.entry.get("source_line"):
        raise ExportError(
            f"compose manifest and reward sidecar source disagree: {row.coordinate}"
        )
    try:
        curate_rewards.restore_source_record(row.record, sidecar)
    except curate_rewards.RewardOntologyError as exc:
        raise ExportError(
            f"compose output {row.coordinate} does not authenticate its reward "
            f"sidecar: {exc}"
        ) from exc


def _authenticate_compose_manifest(
    manifest_documents: Sequence[Any],
    actual_outputs: Mapping[str, CuratedFile],
    sidecars_by_id: Mapping[str, dict[str, Any]],
) -> tuple[set[tuple[str, int]], set[str]]:
    """Authenticate every manifest row against the bytes actually exported."""

    manifest_coordinates: set[tuple[str, int]] = set()
    referenced_sidecars: set[str] = set()
    for index, entry in enumerate(manifest_documents):
        _assert_manifest_entry_contract(entry, index)
        if entry.get("action") != compose_curated.ACTION_RETAINED:
            _assert_excluded_row_claims_no_output(entry, index)
            continue
        coordinate = _manifest_output_coordinate(entry, index, manifest_coordinates)
        manifest_coordinates.add(coordinate)
        record = _authenticated_manifest_record(entry, coordinate, actual_outputs)
        sidecar_id = _authenticated_manifest_sidecar(
            _ManifestRow(entry, index, coordinate, record), sidecars_by_id
        )
        if sidecar_id is not None:
            referenced_sidecars.add(sidecar_id)
    return manifest_coordinates, referenced_sidecars


def _assert_compose_counts(
    summary: Mapping[str, Any], expected_counts: Mapping[str, int]
) -> None:
    """The declared counts must be the ones the exported bytes produce."""

    counts = summary.get("counts")
    if not isinstance(counts, dict):
        raise ExportError("COMPOSE.json: counts must be an object")
    for key, expected in expected_counts.items():
        value = counts.get(key)
        if isinstance(value, bool) or not isinstance(value, int) or value != expected:
            raise ExportError(f"COMPOSE.json: counts.{key} {value!r} != {expected}")


def _compose_metadata(
    curated_root: Path,
    curated_files: Sequence[CuratedFile],
    audit_report: Mapping[str, Any],
) -> dict[str, Any]:
    """Authenticate COMPOSE paths, bytes, coordinates, and reward links."""

    _summary_path, summary_payload, summary = _authenticated_compose_summary(
        curated_root
    )
    actual_outputs = _curated_outputs_by_compose_path(curated_files)
    authenticated_outputs = _authenticated_output_declarations(
        curated_root, summary, actual_outputs
    )

    manifest, manifest_documents = _authenticated_descriptor(
        curated_root,
        summary,
        "manifest",
        f"{compose_curated.MANIFEST_DIRNAME}/{compose_curated.MANIFEST_FILENAME}",
    )
    reward_sidecars, sidecar_documents = _authenticated_descriptor(
        curated_root,
        summary,
        "reward_sidecars",
        (
            f"{compose_curated.MANIFEST_DIRNAME}/"
            f"{compose_curated.REWARD_SIDECAR_FILENAME}"
        ),
    )
    sidecars_by_id = _validated_sidecars_by_id(sidecar_documents)

    expected_coordinates = {
        (path, row.source_line)
        for path, curated in actual_outputs.items()
        for row in curated.rows
    }
    manifest_coordinates, referenced_sidecars = _authenticate_compose_manifest(
        manifest_documents, actual_outputs, sidecars_by_id
    )
    if manifest_coordinates != expected_coordinates:
        missing = sorted(expected_coordinates - manifest_coordinates)
        extra = sorted(manifest_coordinates - expected_coordinates)
        raise ExportError(
            f"compose manifest/output coordinate mismatch; missing={missing}, extra={extra}"
        )
    if referenced_sidecars != set(sidecars_by_id):
        raise ExportError("compose manifest and reward sidecar sets do not match")

    _assert_compose_counts(
        summary,
        {
            "source_records": len(manifest_documents),
            "retained": len(expected_coordinates),
            "excluded": len(manifest_documents) - len(expected_coordinates),
            "output_files": len(actual_outputs),
            "reward_sidecars": len(sidecar_documents),
        },
    )

    source_snapshot = _authenticate_source_replay(
        curated_root,
        summary,
        actual_outputs,
        manifest_documents,
        sidecar_documents,
    )
    expected_audit = compose_curated.compact_audit_report(
        audit_report, len(expected_coordinates)
    )
    if summary.get("audit") != expected_audit:
        raise ExportError("COMPOSE.json: audit declaration does not match exported bytes")

    return {
        "present": True,
        "summary": {
            "path": compose_curated.SUMMARY_FILENAME,
            "sha256": hashlib.sha256(summary_payload).hexdigest(),
        },
        "compose_version": summary.get("compose_version"),
        "lane_order": summary.get("lane_order"),
        "transforms": compose_curated.transform_contract(),
        "source": source_snapshot,
        "outputs": authenticated_outputs,
        "manifest": manifest,
        "reward_sidecars": reward_sidecars,
    }
