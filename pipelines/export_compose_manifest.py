#!/usr/bin/env python3
"""Compose-manifest authentication: bind every manifest row to exported bytes.

Split out of ``export_compose_auth.py`` by responsibility. This module owns
the manifest-row and reward-sidecar checks: each retained row must name an
output coordinate that exists in the captured payload, hash to the exported
record, and link a sidecar that restores that record through the reward
ontology. ``export_compose_auth`` keeps the summary, output-declaration,
count, coverage, and audit checks and calls into this module.
"""

from __future__ import annotations

import hashlib
import sys
from dataclasses import dataclass
from typing import Any, Mapping, Sequence

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("export_compose_manifest")
    from . import compose_curated, curate_rewards
    from .export_contract import (
        CuratedFile,
        ExportError,
        _is_json_integer,
        _loads_json,
        _require_equal,
    )
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "export_compose_manifest"
    )
    import compose_curated
    import curate_rewards
    from export_contract import (
        CuratedFile,
        ExportError,
        _is_json_integer,
        _loads_json,
        _require_equal,
    )

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


@dataclass(frozen=True)
class _ManifestAuthentication:
    """Captured output and sidecar evidence shared across manifest rows."""

    coordinates: set[tuple[str, int]]
    actual_outputs: Mapping[str, CuratedFile]
    sidecars_by_id: Mapping[str, dict[str, Any]]


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


if __package__:
    _expose_package_sibling(__name__)
