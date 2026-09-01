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
from typing import Any, Mapping, Sequence, TypeGuard

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


def _is_json_integer(value: Any) -> TypeGuard[int]:
    """Accept JSON integers without Python's boolean-as-integer coercion."""

    return isinstance(value, int) and not isinstance(value, bool)


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


@dataclass(frozen=True)
class _ComposeEvidence:
    """Authenticated manifest and sidecar descriptors plus decoded rows."""

    manifest: dict[str, Any]
    manifest_documents: Sequence[Any]
    reward_sidecars: dict[str, Any]
    sidecar_documents: Sequence[Any]
    sidecars_by_id: Mapping[str, dict[str, Any]]


@dataclass(frozen=True)
class _OutputAuthentication:
    """Captured output evidence shared while authenticating declarations."""

    curated_root: Path
    actual_outputs: Mapping[str, CuratedFile]
    seen_output_paths: set[str]


@dataclass(frozen=True)
class _ManifestAuthentication:
    """Captured output and sidecar evidence shared across manifest rows."""

    coordinates: set[tuple[str, int]]
    actual_outputs: Mapping[str, CuratedFile]
    sidecars_by_id: Mapping[str, dict[str, Any]]


@dataclass(frozen=True)
class _ExportedCompose:
    """All authenticated evidence needed to format exported compose metadata."""

    summary_payload: bytes
    summary: Mapping[str, Any]
    source_snapshot: Mapping[str, Any]
    authenticated_outputs: Sequence[Mapping[str, Any]]
    evidence: _ComposeEvidence


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


def _require_equal(actual: Any, expected: Any, message: str) -> None:
    """Reject an authenticated declaration that differs from its evidence."""

    if actual != expected:
        raise ExportError(message)


def _require_compose_contract(summary: dict[str, Any], curated_root: Path) -> None:
    """Require the summary to declare exactly this compose contract and root."""

    _require_equal(
        summary.get("compose_name"),
        compose_curated.COMPOSE_NAME,
        "COMPOSE.json: unexpected compose_name",
    )
    _require_equal(
        summary.get("compose_version"),
        compose_curated.COMPOSE_VERSION,
        "COMPOSE.json: compose_version does not match this export contract",
    )
    _require_equal(
        summary.get("lane_order"),
        list(compose_curated.LANE_ORDER),
        "COMPOSE.json: lane_order does not match the compose contract",
    )
    _require_equal(
        summary.get("destination"),
        str(curated_root.resolve()),
        "COMPOSE.json: destination does not name this curated root",
    )


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
    for curated in curated_files:
        compose_path = _compose_output_path(curated)
        _add_captured_output(actual_outputs, compose_path, curated)
    return actual_outputs


def _compose_output_path(curated: CuratedFile) -> str:
    """Translate one captured export path into its compose output path."""

    prefix = f"{CURATED_DIRNAME}/"
    if not curated.source_file.startswith(prefix):
        raise ExportError(f"invalid curated source path: {curated.source_file}")
    return f"{compose_curated.RECORDS_DIRNAME}/{curated.source_file.removeprefix(prefix)}"


def _add_captured_output(
    outputs: dict[str, CuratedFile], compose_path: str, curated: CuratedFile
) -> None:
    """Bind one compose path to one and only one captured byte snapshot."""

    if compose_path in outputs:
        raise ExportError(f"duplicate captured output path {compose_path!r}")
    outputs[compose_path] = curated


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
    _require_equal(
        entry.get("sha256"),
        digest,
        f"COMPOSE.json: output digest mismatch for {raw_path}",
    )
    records = _positive_output_record_count(entry, raw_path)
    _require_equal(
        records,
        len(curated.rows),
        f"COMPOSE.json: output record count mismatch for {raw_path}",
    )
    return {"path": raw_path, "records": records, "sha256": digest}


def _positive_output_record_count(entry: Mapping[str, Any], raw_path: Any) -> int:
    """Require one declared output count to be a positive integer."""

    records = entry.get("records")
    if not _is_json_integer(records):
        raise ExportError(f"COMPOSE.json: invalid record count for {raw_path}")
    if records < 1:
        raise ExportError(f"COMPOSE.json: invalid record count for {raw_path}")
    return records


def _declared_output_entries(summary: Mapping[str, Any]) -> list[Any]:
    """Return the summary's output declarations after validating the container."""

    declared_outputs = summary.get("outputs")
    if not isinstance(declared_outputs, list):
        raise ExportError("COMPOSE.json: outputs must be a list")
    return declared_outputs


def _authenticated_output_declaration(
    authentication: _OutputAuthentication,
    entry: Any,
    index: int,
) -> dict[str, Any]:
    """Authenticate one summary declaration against its captured output."""

    if not isinstance(entry, dict):
        raise ExportError(f"COMPOSE.json: outputs[{index}] must be an object")
    raw_path = entry.get("path")
    _path, current_payload = _read_exact_regular_file(
        authentication.curated_root, raw_path, f"COMPOSE outputs[{index}]"
    )
    if raw_path in authentication.seen_output_paths:
        raise ExportError(f"COMPOSE.json: duplicate output path {raw_path!r}")
    authentication.seen_output_paths.add(raw_path)
    curated = _snapshot_bound_output(raw_path, current_payload, authentication.actual_outputs)
    return _authenticated_output_row(raw_path, entry, curated)


def _require_complete_output_set(
    seen_output_paths: set[str], actual_outputs: Mapping[str, CuratedFile]
) -> None:
    """Require the summary to declare every captured payload exactly once."""

    expected_paths = set(actual_outputs)
    if seen_output_paths != expected_paths:
        missing = sorted(expected_paths - seen_output_paths)
        raise ExportError(f"COMPOSE.json: payload outputs missing from summary: {missing}")


def _authenticated_output_declarations(
    curated_root: Path,
    summary: Mapping[str, Any],
    actual_outputs: Mapping[str, CuratedFile],
) -> list[dict[str, Any]]:
    """Prove every declared output against the snapshot already captured."""

    authenticated_outputs: list[dict[str, Any]] = []
    seen_output_paths: set[str] = set()
    authentication = _OutputAuthentication(curated_root, actual_outputs, seen_output_paths)
    for index, entry in enumerate(_declared_output_entries(summary)):
        authenticated_outputs.append(
            _authenticated_output_declaration(authentication, entry, index)
        )
    _require_complete_output_set(seen_output_paths, actual_outputs)
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
        _require_equal(
            entry.get(field_name),
            expected,
            f"compose manifest entry {index + 1} has an unexpected {field_name}",
        )


def _assert_excluded_row_claims_no_output(entry: Mapping[str, Any], index: int) -> None:
    """An excluded row may not claim an output, an id, or a reward sidecar."""

    if any(entry.get(field_name) is not None for field_name in _MANIFEST_OUTPUT_FIELDS):
        raise ExportError(f"compose manifest entry {index + 1} gives an excluded row output")


def _manifest_output_coordinate(
    entry: Mapping[str, Any], index: int, seen: set[tuple[str, int]]
) -> tuple[str, int]:
    """The unique ``(path, line)`` coordinate a retained row occupies."""

    output_path = _manifest_output_path(entry, index)
    output_line = _manifest_output_line(entry, index)
    coordinate = (output_path, output_line)
    if coordinate in seen:
        raise ExportError(f"duplicate compose manifest coordinate {coordinate}")
    return coordinate


def _invalid_coordinate(index: int) -> ExportError:
    """Build the stable error for a malformed manifest coordinate."""

    return ExportError(f"compose manifest entry {index + 1} has an invalid output coordinate")


def _manifest_output_path(entry: Mapping[str, Any], index: int) -> str:
    """Require a retained manifest entry to name a string output path."""

    output_path = entry.get("output_path")
    if not isinstance(output_path, str):
        raise _invalid_coordinate(index)
    return output_path


def _manifest_output_line(entry: Mapping[str, Any], index: int) -> int:
    """Require a retained manifest entry to name an integer output line."""

    output_line = entry.get("output_line")
    if not _is_json_integer(output_line):
        raise _invalid_coordinate(index)
    return output_line


def _resolved_manifest_row(
    coordinate: tuple[str, int], actual_outputs: Mapping[str, CuratedFile]
) -> Any:
    """Resolve one authenticated manifest coordinate to its captured row."""

    output_path, output_line = coordinate
    curated = actual_outputs.get(output_path)
    if curated is None:
        raise ExportError(f"compose manifest coordinate does not resolve: {coordinate}")
    if not 1 <= output_line <= len(curated.rows):
        raise ExportError(f"compose manifest coordinate does not resolve: {coordinate}")
    return curated.rows[output_line - 1]


def _record_output_id(record: Any, coordinate: tuple[str, int]) -> str:
    """Require one decoded compose output to carry a string record id."""

    if not isinstance(record, dict):
        raise ExportError(f"compose manifest output id mismatch: {coordinate}")
    output_id = record.get("id")
    if not isinstance(output_id, str):
        raise ExportError(f"compose manifest output id mismatch: {coordinate}")
    return output_id


def _authenticated_manifest_record(
    entry: Mapping[str, Any],
    coordinate: tuple[str, int],
    actual_outputs: Mapping[str, CuratedFile],
) -> Any:
    """Resolve one coordinate to its exported row and prove digest and id."""

    row = _resolved_manifest_row(coordinate, actual_outputs)
    digest = hashlib.sha256(row.record_json.encode("utf-8")).hexdigest()
    _require_equal(
        entry.get("output_sha256"),
        digest,
        f"compose manifest output digest mismatch: {coordinate}",
    )
    record = _loads_json(row.record_json, f"compose output {coordinate}")
    output_id = _record_output_id(record, coordinate)
    _require_equal(
        entry.get("output_id"),
        output_id,
        f"compose manifest output id mismatch: {coordinate}",
    )
    return record


def _authenticated_manifest_sidecar(
    row: _ManifestRow, sidecars_by_id: Mapping[str, dict[str, Any]]
) -> str | None:
    """Bind one retained row to the reward sidecar it claims, if any."""

    sidecar_id = row.entry.get("reward_sidecar_id")
    if sidecar_id is None:
        _require_no_unmanifested_annotation(row)
        return None
    sidecar = _required_manifest_sidecar(row, sidecar_id, sidecars_by_id)
    _require_sidecar_restores(row, sidecar)
    return sidecar_id


def _require_no_unmanifested_annotation(row: _ManifestRow) -> None:
    """Reject a reward annotation whose evidence is absent from the manifest."""

    if not isinstance(row.record, dict):
        return
    if curate_rewards.ANNOTATION_FIELD in row.record:
        raise ExportError(f"compose output {row.coordinate} has an unmanifested reward annotation")


def _required_manifest_sidecar(
    row: _ManifestRow,
    sidecar_id: Any,
    sidecars_by_id: Mapping[str, dict[str, Any]],
) -> dict[str, Any]:
    """Resolve a manifest sidecar id to its authenticated sidecar document."""

    if not isinstance(sidecar_id, str):
        raise ExportError(f"{row.label} has an invalid reward sidecar id")
    sidecar = sidecars_by_id.get(sidecar_id)
    if sidecar is None:
        raise ExportError(f"compose manifest references missing reward sidecar {sidecar_id}")
    return sidecar


def _require_sidecar_restores(row: _ManifestRow, sidecar: dict[str, Any]) -> None:
    """The claimed sidecar must name the same source and restore the record."""

    sidecar_source = sidecar["source"]
    mismatch = f"compose manifest and reward sidecar source disagree: {row.coordinate}"
    _require_equal(sidecar_source.get("path"), row.entry.get("source_path"), mismatch)
    _require_equal(sidecar_source.get("line"), row.entry.get("source_line"), mismatch)
    try:
        curate_rewards.restore_source_record(row.record, sidecar)
    except curate_rewards.RewardOntologyError as exc:
        raise ExportError(
            f"compose output {row.coordinate} does not authenticate its reward sidecar: {exc}"
        ) from exc


def _authenticated_manifest_entry(
    entry: Any,
    index: int,
    authentication: _ManifestAuthentication,
) -> tuple[tuple[str, int], str | None] | None:
    """Authenticate one retained entry, or validate one excluded entry."""

    _assert_manifest_entry_contract(entry, index)
    if entry.get("action") != compose_curated.ACTION_RETAINED:
        _assert_excluded_row_claims_no_output(entry, index)
        return None
    coordinate = _manifest_output_coordinate(entry, index, authentication.coordinates)
    record = _authenticated_manifest_record(entry, coordinate, authentication.actual_outputs)
    sidecar_id = _authenticated_manifest_sidecar(
        _ManifestRow(entry, index, coordinate, record),
        authentication.sidecars_by_id,
    )
    return coordinate, sidecar_id


def _authenticate_compose_manifest(
    manifest_documents: Sequence[Any],
    actual_outputs: Mapping[str, CuratedFile],
    sidecars_by_id: Mapping[str, dict[str, Any]],
) -> tuple[set[tuple[str, int]], set[str]]:
    """Authenticate every manifest row against the bytes actually exported."""

    manifest_coordinates: set[tuple[str, int]] = set()
    referenced_sidecars: set[str] = set()
    authentication = _ManifestAuthentication(manifest_coordinates, actual_outputs, sidecars_by_id)
    for index, entry in enumerate(manifest_documents):
        authenticated = _authenticated_manifest_entry(entry, index, authentication)
        if authenticated is None:
            continue
        coordinate, sidecar_id = authenticated
        manifest_coordinates.add(coordinate)
        if sidecar_id is not None:
            referenced_sidecars.add(sidecar_id)
    return manifest_coordinates, referenced_sidecars


def _assert_compose_counts(summary: Mapping[str, Any], expected_counts: Mapping[str, int]) -> None:
    """The declared counts must be the ones the exported bytes produce."""

    counts = _declared_compose_counts(summary)
    for key, expected in expected_counts.items():
        _require_compose_count(counts, key, expected)


def _declared_compose_counts(summary: Mapping[str, Any]) -> dict[str, Any]:
    """Return the summary's count declarations after validating the container."""

    counts = summary.get("counts")
    if not isinstance(counts, dict):
        raise ExportError("COMPOSE.json: counts must be an object")
    return counts


def _require_compose_count(counts: Mapping[str, Any], key: str, expected: int) -> None:
    """Require one compose count to be an integer with the expected value."""

    value = counts.get(key)
    if not _is_json_integer(value):
        raise ExportError(f"COMPOSE.json: counts.{key} {value!r} != {expected}")
    _require_equal(
        value,
        expected,
        f"COMPOSE.json: counts.{key} {value!r} != {expected}",
    )


def _authenticated_compose_evidence(
    curated_root: Path, summary: Mapping[str, Any]
) -> _ComposeEvidence:
    """Read and authenticate the manifest and reward-sidecar descriptors."""

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
        (f"{compose_curated.MANIFEST_DIRNAME}/{compose_curated.REWARD_SIDECAR_FILENAME}"),
    )
    return _ComposeEvidence(
        manifest=manifest,
        manifest_documents=manifest_documents,
        reward_sidecars=reward_sidecars,
        sidecar_documents=sidecar_documents,
        sidecars_by_id=_validated_sidecars_by_id(sidecar_documents),
    )


def _expected_output_coordinates(
    actual_outputs: Mapping[str, CuratedFile],
) -> set[tuple[str, int]]:
    """Return every output coordinate present in the captured payload rows."""

    return {
        (path, row.source_line) for path, curated in actual_outputs.items() for row in curated.rows
    }


def _require_manifest_coverage(
    actual: set[tuple[str, int]], expected: set[tuple[str, int]]
) -> None:
    """Require the manifest to cover exactly the captured output coordinates."""

    if actual != expected:
        missing = sorted(expected - actual)
        extra = sorted(actual - expected)
        raise ExportError(
            f"compose manifest/output coordinate mismatch; missing={missing}, extra={extra}"
        )


def _require_sidecar_coverage(
    referenced_sidecars: set[str], sidecars_by_id: Mapping[str, dict[str, Any]]
) -> None:
    """Require every authenticated sidecar to be referenced exactly once or more."""

    _require_equal(
        referenced_sidecars,
        set(sidecars_by_id),
        "compose manifest and reward sidecar sets do not match",
    )


def _expected_compose_counts(
    evidence: _ComposeEvidence,
    actual_outputs: Mapping[str, CuratedFile],
    expected_coordinates: set[tuple[str, int]],
) -> dict[str, int]:
    """Derive the aggregate counts from authenticated bytes and coordinates."""

    source_records = len(evidence.manifest_documents)
    retained = len(expected_coordinates)
    return {
        "source_records": source_records,
        "retained": retained,
        "excluded": source_records - retained,
        "output_files": len(actual_outputs),
        "reward_sidecars": len(evidence.sidecar_documents),
    }


def _require_compose_audit(
    summary: Mapping[str, Any],
    audit_report: Mapping[str, Any],
    retained: int,
) -> None:
    """Bind the declared audit to the supplied report and retained count."""

    expected_audit = compose_curated.compact_audit_report(audit_report, retained)
    _require_equal(
        summary.get("audit"),
        expected_audit,
        "COMPOSE.json: audit declaration does not match exported bytes",
    )


def _exported_compose_metadata(
    authenticated: _ExportedCompose,
) -> dict[str, Any]:
    """Format metadata only after all compose evidence has authenticated."""

    return {
        "present": True,
        "summary": {
            "path": compose_curated.SUMMARY_FILENAME,
            "sha256": hashlib.sha256(authenticated.summary_payload).hexdigest(),
        },
        "compose_version": authenticated.summary.get("compose_version"),
        "lane_order": authenticated.summary.get("lane_order"),
        "transforms": compose_curated.transform_contract(),
        "source": authenticated.source_snapshot,
        "outputs": authenticated.authenticated_outputs,
        "manifest": authenticated.evidence.manifest,
        "reward_sidecars": authenticated.evidence.reward_sidecars,
    }


def _compose_metadata(
    curated_root: Path,
    curated_files: Sequence[CuratedFile],
    audit_report: Mapping[str, Any],
) -> dict[str, Any]:
    """Authenticate COMPOSE paths, bytes, coordinates, and reward links."""

    _summary_path, summary_payload, summary = _authenticated_compose_summary(curated_root)
    actual_outputs = _curated_outputs_by_compose_path(curated_files)
    authenticated_outputs = _authenticated_output_declarations(
        curated_root, summary, actual_outputs
    )
    evidence = _authenticated_compose_evidence(curated_root, summary)
    expected_coordinates = _expected_output_coordinates(actual_outputs)
    manifest_coordinates, referenced_sidecars = _authenticate_compose_manifest(
        evidence.manifest_documents, actual_outputs, evidence.sidecars_by_id
    )
    _require_manifest_coverage(manifest_coordinates, expected_coordinates)
    _require_sidecar_coverage(referenced_sidecars, evidence.sidecars_by_id)
    _assert_compose_counts(
        summary,
        _expected_compose_counts(evidence, actual_outputs, expected_coordinates),
    )

    source_snapshot = _authenticate_source_replay(
        summary,
        actual_outputs,
        evidence.manifest_documents,
        evidence.sidecar_documents,
    )
    _require_compose_audit(summary, audit_report, retained=len(expected_coordinates))
    return _exported_compose_metadata(
        _ExportedCompose(
            summary_payload,
            summary,
            source_snapshot,
            authenticated_outputs,
            evidence,
        )
    )
