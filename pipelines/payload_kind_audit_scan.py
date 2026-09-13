#!/usr/bin/env python3
"""Record classification, row emission, and payload scanning for payload-kind audit.

Extracted from ``payload_kind_audit`` so each module's total complexity stays
under the qlty High threshold. Public callers still import through
``payload_kind_audit``.
"""

from __future__ import annotations

import hashlib
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping

sys.path.insert(0, str(Path(__file__).resolve().parent))

from curate_identity import (  # noqa: E402
    LEGACY_ID_KEYS,
    IdentityCurationError,
    record_kind,
)
from payload_kind_audit_parse import (  # noqa: E402
    PayloadKindAuditError,
    _is_json_whitespace,
    _jsonl_lines,
    _load_payload_bytes,
    _parse_json_record,
    _reject_rounded_fields,
)

EPISODE_MARKERS = ("goal", "steps")

# Step-level reasoning fields. ``decision_basis`` is the observable form this
# factory's curation contract requires; ``thought`` is the legacy hidden form.
REASONING_FIELDS = ("thought", "decision_basis", "reflection")
SUPPORTED_RECORD_KINDS = frozenset({"episode", "thalamic"})


def _is_episode_shaped(value: Any) -> bool:
    return isinstance(value, Mapping) and all(key in value for key in EPISODE_MARKERS)


def _required_mapping(record: Mapping[str, Any], key: str, where: str) -> Mapping[str, Any]:
    value = record.get(key)
    if not isinstance(value, Mapping):
        raise PayloadKindAuditError(f"{where}.{key} must be a JSON object")
    return value


def _steps(value: Mapping[str, Any], where: str) -> list[Mapping[str, Any]]:
    steps = value.get("steps")
    if not isinstance(steps, list):
        raise PayloadKindAuditError(f"{where}.steps must be a JSON array")
    for index, step in enumerate(steps):
        if not isinstance(step, Mapping):
            raise PayloadKindAuditError(f"{where}.steps[{index}] must be a JSON object")
    return steps


def _coding_steps(record: Mapping[str, Any], kind: str, where: str) -> list[Mapping[str, Any]]:
    if kind == "episode":
        return _steps(record, where)
    if kind == "thalamic":
        executed = record.get("executed_action")
        if not _is_episode_shaped(executed):
            return []
        return _steps(executed, f"{where}.executed_action")
    raise PayloadKindAuditError(
        f"{where}: payload kind {kind!r} is outside this episode/thalamic audit"
    )


# ``curate_identity._legacy_ids`` collects every ``LEGACY_ID_KEYS`` form from
# the owner, its ``meta``, and its ``state``. The audit searches the same three
# containers in the same order so it cannot render ``—`` for an identifier the
# curation lane would recognize.
_LEGACY_ID_CONTAINERS = ("meta", "state")


def _legacy_id_containers(record: Mapping[str, Any]) -> Iterable[Mapping[str, Any]]:
    yield record
    for name in _LEGACY_ID_CONTAINERS:
        nested = record.get(name)
        if isinstance(nested, Mapping):
            yield nested


def _first_legacy_id(record: Mapping[str, Any]) -> Any:
    """Return the first present non-null identifier supported by identity curation.

    Precedence is container-major then key-minor, matching
    ``curate_identity._legacy_ids``: every top-level alias outranks every
    ``meta`` alias, which outranks every ``state`` alias.

    JSON ``id: null`` is present-but-empty: it must not shadow a later
    ``record_id`` / ``trajectory_id`` / ``episode_id`` / ``pair_id`` the way a
    membership-only lookup would (NULL-ALIAS-ID-SHADOW).
    """
    for container in _legacy_id_containers(record):
        for key in LEGACY_ID_KEYS:
            if key in container and container[key] is not None:
                return container[key]
    return None


@dataclass(frozen=True)
class _ParsedLine:
    """One classified JSONL record, ready to become a row and feed stats."""

    record: Mapping[str, Any]
    kind: str
    steps: list[Mapping[str, Any]]
    source_file: str
    line: int
    digest: str


def _thalamic_row_fields(parsed: _ParsedLine) -> dict:
    where = f"{parsed.source_file}:{parsed.line}"
    state = _required_mapping(parsed.record, "state", where)
    gate = _required_mapping(parsed.record, "safety_decision", where)
    # The schema's canonical, globally unique identifier is the top-level
    # ``id``. ``state.episode_id`` is a legacy fallback for records that
    # predate it.
    top_level_id = parsed.record.get("id")
    return {
        "id": top_level_id if top_level_id is not None else state.get("episode_id"),
        "domain": state.get("domain"),
        "supervisor_id": gate.get("supervisor_id"),
        "gate_decision": gate.get("decision"),
        "wraps_coding_episode": _is_episode_shaped(parsed.record.get("executed_action")),
        "coding_steps": len(parsed.steps),
    }


def _episode_row_fields(parsed: "_ParsedLine") -> dict:
    # The published episodes in this lane carry no top-level identifier, but
    # other episode corpora use legacy aliases. Report the first alias the
    # identity curation contract recognizes; never invent one.
    return {
        "id": _first_legacy_id(parsed.record),
        "domain": None,
        "wraps_coding_episode": False,
        "coding_steps": len(parsed.steps),
    }


def _record_row(parsed: _ParsedLine) -> dict:
    row: dict[str, Any] = {
        "source_file": parsed.source_file,
        "source_line": parsed.line,
        "kind": parsed.kind,
        "sha256": parsed.digest,
    }
    fields = _thalamic_row_fields(parsed) if parsed.kind == "thalamic" else _episode_row_fields(parsed)
    _reject_rounded_fields(fields, f"{parsed.source_file}:{parsed.line}")
    row.update(fields)
    return row


def _reasoning_counts(steps: list[Mapping[str, Any]]) -> dict[str, int]:
    counts = {field: 0 for field in REASONING_FIELDS}
    for step in steps:
        for field in REASONING_FIELDS:
            if field in step:
                counts[field] += 1
    return counts


def _classify_record_kind(record: Mapping[str, Any], source_file: str, line_number: int) -> str:
    """Classify one record, or raise PayloadKindAuditError outside this audit's scope."""
    try:
        kind = record_kind(record)
    except IdentityCurationError as exc:
        raise PayloadKindAuditError(f"{source_file}:{line_number}: {exc}") from exc
    if kind not in SUPPORTED_RECORD_KINDS:
        raise PayloadKindAuditError(
            f"{source_file}:{line_number}: payload kind {kind!r} is outside this episode/thalamic audit"
        )
    return kind


def _parse_payload_line(
    source_file: str, line_number: int, line_bytes: bytes, line: str
) -> _ParsedLine:
    """Parse, validate, and classify one non-blank JSONL line."""
    record = _parse_json_record(source_file, line_number, line)
    digest = hashlib.sha256(line_bytes).hexdigest()
    kind = _classify_record_kind(record, source_file, line_number)
    steps = _coding_steps(record, kind, f"{source_file}:{line_number}")
    return _ParsedLine(record, kind, steps, source_file, line_number, digest)


class _AuditStats:
    """Corpus-wide totals accumulated one classified record at a time."""

    def __init__(self) -> None:
        self.kinds: dict[str, int] = {}
        self.factories: dict[str, int] = {}
        self.native_steps = 0
        self.embedded_steps = 0
        self.wrapping = 0
        self.reasoning = {field: 0 for field in REASONING_FIELDS}

    def add(self, parsed: _ParsedLine, row: Mapping[str, Any]) -> None:
        kind = row["kind"]
        self.kinds[kind] = self.kinds.get(kind, 0) + 1
        meta = parsed.record.get("meta")
        factory = meta.get("factory") if isinstance(meta, Mapping) else None
        if isinstance(factory, str):
            self.factories[factory] = self.factories.get(factory, 0) + 1
        if kind == "thalamic":
            self.embedded_steps += row["coding_steps"]
            if row["wraps_coding_episode"]:
                self.wrapping += 1
        else:
            self.native_steps += row["coding_steps"]
        for field, value in _reasoning_counts(parsed.steps).items():
            self.reasoning[field] += value

    def summary(self, *, files: int, records: int) -> dict:
        return {
            "files": files,
            "records": records,
            "kinds": dict(sorted(self.kinds.items())),
            "meta_factory_stamps": dict(sorted(self.factories.items())),
            "thalamic_records_wrapping_a_coding_episode": self.wrapping,
            "coding_episodes_reachable_at_top_level": self.kinds.get("episode", 0),
            "coding_episodes_including_wrapped": self.kinds.get("episode", 0) + self.wrapping,
            "coding_steps": {
                "native": self.native_steps,
                "wrapped": self.embedded_steps,
                "total": self.native_steps + self.embedded_steps,
            },
            "coding_steps_by_reasoning_field": dict(sorted(self.reasoning.items())),
        }


def _scan_payload_file(path: Path, stats: _AuditStats) -> tuple[list[dict], dict]:
    """Parse one payload file, feeding corpus-wide stats and returning its rows."""
    raw = _load_payload_bytes(path)
    rows: list[dict] = []
    file_kinds: dict[str, int] = {}
    for line_number, line_bytes, line in _jsonl_lines(raw, path.name):
        if not line or _is_json_whitespace(line):
            continue
        parsed = _parse_payload_line(path.name, line_number, line_bytes, line)
        row = _record_row(parsed)
        stats.add(parsed, row)
        file_kinds[row["kind"]] = file_kinds.get(row["kind"], 0) + 1
        rows.append(row)
    file_summary = {
        "path": path.name,
        "bytes": len(raw),
        "sha256": hashlib.sha256(raw).hexdigest(),
        "records": len(rows),
        "kinds": dict(sorted(file_kinds.items())),
    }
    return rows, file_summary

