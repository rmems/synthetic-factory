#!/usr/bin/env python3
"""Exact retained-coordinate coverage for captured rights manifests."""

from __future__ import annotations

import sys
from collections.abc import Mapping, Sequence

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("training_audit_rights_coverage")
    from .curate_identity_json import sha256_json
    from .rights_mapping import parse_strict_json_bytes
    from .strict_jsonl import strict_lf_jsonl_records
    from .training_audit_rights_manifest import _retained_entries
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "training_audit_rights_coverage"
    )
    from curate_identity_json import sha256_json
    from rights_mapping import parse_strict_json_bytes
    from strict_jsonl import strict_lf_jsonl_records
    from training_audit_rights_manifest import _retained_entries


def _json_line(value: object) -> int:
    """Accept a JSON line number without Python's boolean-as-integer coercion."""

    if isinstance(value, int) and not isinstance(value, bool):
        return value
    raise ValueError("invalid retained output coordinate")


def _file_coordinates(relative: str, lines: Sequence[bytes]):
    return {
        (f"records/{relative}", number): sha256_json(parse_strict_json_bytes(line))
        for number, line in enumerate(lines, 1) if line.strip()
    }


def _output_coordinates(
    files: Mapping[str, bytes], *, preserve_gaps: bool = False,
) -> dict[tuple[str, int], str]:
    coordinates = {}
    for relative, payload in files.items():
        if preserve_gaps:
            lines = payload.split(b"\n")
        else:
            lines = strict_lf_jsonl_records(payload, relative)
        coordinates.update(_file_coordinates(relative, lines))
    return coordinates


def _compose_coordinate(entry: Mapping) -> tuple[str, int]:
    path = entry.get("output_path")
    if not isinstance(path, str):
        raise ValueError("invalid retained output coordinate")
    return path, _json_line(entry.get("output_line"))


def _identity_coordinate(entry: Mapping) -> tuple[str, int]:
    source = entry["source"]
    return f"records/{source['path']}", _json_line(source["line"])


def _unique_outputs(entries: Sequence[Mapping], coordinate_of, *, duplicate: str) -> dict:
    declared = {}
    for entry in _retained_entries(entries):
        coordinate = coordinate_of(entry)
        if coordinate in declared:
            raise ValueError(duplicate)
        declared[coordinate] = entry.get("output_sha256")
    return declared


def _require_compose_coverage(entries: Sequence[Mapping], files: Mapping[str, bytes]) -> None:
    declared = _unique_outputs(
        entries, _compose_coordinate, duplicate="duplicate retained output coordinate",
    )
    if declared != _output_coordinates(files):
        raise ValueError("rights manifest does not cover exact audited records")


def _require_identity_coverage(entries: Sequence[Mapping], files: Mapping[str, bytes]) -> None:
    declared = _unique_outputs(
        entries, _identity_coordinate, duplicate="duplicate identity output coordinate",
    )
    if declared != _output_coordinates(files, preserve_gaps=True):
        raise ValueError("identity manifest does not cover exact audited records")


if __package__:
    _expose_package_sibling(__name__)
