#!/usr/bin/env python3
"""Manifest replay indexing and exact identity-output decoding.

The identity facade owns policy and validation callbacks.  It supplies them
for every call so test patches and caller instrumentation remain live after
this responsibility split.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Mapping, Pattern

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("curate_identity_output")
else:
    def _ignore_package_sibling(_name):
        return None


    getattr(
        sys.modules.get("pipelines"),
        "_join_package_sibling",
        _ignore_package_sibling,
    )("curate_identity_output")


@dataclass(frozen=True)
class IdentityOutputDependencies:
    """Live facade-owned operations used while validating identity output."""

    canonical_json: Callable[[Any], str]
    identity_curation_error: type[Exception]
    identity_tree_error: type[Exception]
    replay_manifest_mapping: Callable[..., Any]
    sha256_pattern: Pattern[str]
    strict_json_loads: Callable[..., Any]


@dataclass(frozen=True)
class ManifestEntry:
    """One manifest value paired with its stable list coordinate."""

    index: int
    mapping: Any


@dataclass(frozen=True)
class ExactPayloadCandidate:
    """Decoded output and the exact bytes it must reproduce."""

    line_bytes: bytes
    output_record: Mapping[str, Any]
    where: str
    preserved_payload: bytes | None


def _require_mapping(value, message, dependencies):
    """Return an object-shaped value or raise the facade's tree error."""

    if not isinstance(value, Mapping):
        raise dependencies.identity_tree_error(message)
    return value


def _replay_identity_manifest_entry(entry, registry, dependencies):
    """Validate one manifest entry's type and registry pin before replay."""

    index = entry.index
    mapping = _require_mapping(
        entry.mapping,
        f"IDENTITY-MANIFEST.json[{index}] must be an object",
        dependencies,
    )
    registry_meta = mapping.get("registry")
    pin = registry_meta.get("sha256") if isinstance(registry_meta, Mapping) else None
    if pin != registry.sha256:
        raise dependencies.identity_tree_error(
            f"IDENTITY-MANIFEST.json[{index}] registry.sha256 does not match sidecar pin"
        )
    return dependencies.replay_manifest_mapping(mapping, index, registry)


def _record_source_coordinate(source, entry, seen_coordinates, dependencies):
    """Reject repeated source coordinates while retaining their first index."""

    coordinate = (source.path, source.line)
    if coordinate in seen_coordinates:
        raise dependencies.identity_tree_error(
            f"IDENTITY-MANIFEST.json repeats source coordinate "
            f"{source.path}:{source.line} at entries "
            f"{seen_coordinates[coordinate]} and {entry.index}"
        )
    seen_coordinates[coordinate] = entry.index


def _record_preserved_code_repair_id(expected_mapping, preserved_ids, dependencies):
    """Enforce global identity for retained code-repair evidence."""

    if expected_mapping.get("record_kind") != "code_repair":
        return
    preserved_id = expected_mapping["output_id"]
    if preserved_id in preserved_ids:
        raise dependencies.identity_tree_error(f"duplicate preserved code_repair ID: {preserved_id}")
    preserved_ids.add(preserved_id)


def _index_expected_identity_output(expected, entry, replay, dependencies):
    """Validate and index one replayed retained output."""

    expected_mapping = replay.result.mapping
    output_sha256 = expected_mapping.get("output_sha256")
    try:
        valid_output_sha256 = dependencies.sha256_pattern.fullmatch(output_sha256) is not None
    except TypeError:
        valid_output_sha256 = False
    if not valid_output_sha256:
        raise dependencies.identity_tree_error(
            f"IDENTITY-MANIFEST.json[{entry.index}] source replay produced an invalid output hash"
        )
    source = replay.source
    by_line = expected.setdefault(source.path, {})
    if source.line in by_line:
        raise dependencies.identity_tree_error(
            f"IDENTITY-MANIFEST.json repeats output coordinate {source.path}:{source.line}"
        )
    by_line[source.line] = (entry.index, entry.mapping, replay)


def expected_identity_outputs(manifest, registry, dependencies):
    """Replay retained manifest entries and index their expected output slots."""

    expected = {}
    seen_coordinates = {}
    preserved_ids = set()
    for index, mapping in enumerate(manifest):
        entry = ManifestEntry(index, mapping)
        replay = _replay_identity_manifest_entry(entry, registry, dependencies)
        _record_source_coordinate(replay.source, entry, seen_coordinates, dependencies)
        if replay.result.action == "retained":
            _record_preserved_code_repair_id(
                replay.result.mapping,
                preserved_ids,
                dependencies,
            )
            _index_expected_identity_output(
                expected,
                entry,
                replay,
                dependencies,
            )
    return expected


def _read_framed_identity_output(path: Path, rel: str, dependencies) -> list[bytes]:
    """Read one canonical-LF output and return its physical record slots."""

    try:
        output_bytes = path.read_bytes()
    except OSError as exc:
        raise dependencies.identity_tree_error(f"identity output is unreadable: {rel}: {exc}") from exc
    if not output_bytes.endswith(b"\n"):
        raise dependencies.identity_tree_error(
            f"identity output must end with exactly one LF: {rel}"
        )
    framed_payload = output_bytes[:-1]
    if framed_payload[-1:] in (b"", b"\n"):
        raise dependencies.identity_tree_error(
            f"identity output must end with a canonical record: {rel}"
        )
    return framed_payload.split(b"\n")


def _decode_identity_output_line(line_bytes: bytes, where: str, dependencies) -> str:
    """Decode one identity output line as strict UTF-8."""

    try:
        return line_bytes.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise dependencies.identity_tree_error(
            f"identity output UTF-8 decode error at {where}: {exc}"
        ) from exc


def _parse_identity_output_json(line: str, where: str, dependencies):
    """Parse one identity output object without weakening strict JSON rules."""

    try:
        output_record = dependencies.strict_json_loads(line)
    except ValueError as exc:
        raise dependencies.identity_tree_error(
            f"identity output JSON parse error at {where}: {exc}"
        ) from exc
    return _require_mapping(
        output_record,
        f"identity output record at {where} must be an object",
        dependencies,
    )


def _parse_identity_output_record(line_bytes: bytes, rel: str, line_no: int, dependencies):
    """Reject placeholders, then decode and parse one output record."""

    where = f"{rel}:{line_no}"
    if not line_bytes.strip():
        raise dependencies.identity_tree_error(
            f"identity output blank placeholders must be empty: {where}"
        )
    line = _decode_identity_output_line(line_bytes, where, dependencies)
    return _parse_identity_output_json(line, where, dependencies)


def _require_exact_identity_payload(
    candidate: ExactPayloadCandidate,
    dependencies,
) -> None:
    """Require exact source bytes when retained, otherwise canonical JSON."""

    try:
        canonical_payload = dependencies.canonical_json(candidate.output_record).encode("utf-8")
    except (dependencies.identity_curation_error, UnicodeError) as exc:
        raise dependencies.identity_tree_error(
            f"identity output is not canonical JSON data: {candidate.where}: {exc}"
        ) from exc
    preserved = candidate.preserved_payload is not None
    payload_options = (canonical_payload, candidate.preserved_payload)
    basis_options = ("canonical JSON", "preserved source")
    expected_payload = payload_options[preserved]
    if candidate.line_bytes != expected_payload:
        raise dependencies.identity_tree_error(
            f"identity output payload is not exact {basis_options[preserved]}: {candidate.where}"
        )


def read_identity_output(path: Path, rel: str, preserved_sources, dependencies):
    """Read and verify each occupied line of one identity-output file."""

    records = {}
    framed_lines = _read_framed_identity_output(path, rel, dependencies)
    for line_no, line_bytes in enumerate(framed_lines, 1):
        if not line_bytes:
            continue
        output_record = _parse_identity_output_record(
            line_bytes,
            rel,
            line_no,
            dependencies,
        )
        _require_exact_identity_payload(
            ExactPayloadCandidate(
                line_bytes,
                output_record,
                f"{rel}:{line_no}",
                preserved_sources.get(line_no),
            ),
            dependencies,
        )
        records[line_no] = output_record
    return records


if __package__:
    _expose_package_sibling(__name__)
