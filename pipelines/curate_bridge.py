#!/usr/bin/env python3
"""Deterministically repair or quarantine Bridge event-stream ordering.

This lane is intentionally record-level and read-only.  It never writes a
cleaned or curated tree.  Callers can import :func:`curate_jsonl` and compose
the returned decisions with the other curation lanes, or use the CLI to print
a summary, manifest, or complete decision bundle to stdout.

An unsorted stream is repaired only when every event has one finite timestamp
under the same supported key, all declared clock-domain identifiers agree,
and no explicit causal/sequence metadata would be reordered.  Otherwise the
record is quarantined with machine-readable reason codes.

Example (prints a manifest and does not mutate the source)::

    python3 pipelines/curate_bridge.py \
      --source-root outputs/raw/2026-08-17 \
      --emit manifest \
      outputs/raw/2026-08-17/neuromorphic-event-language-bridge/batch-r02.jsonl
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Sequence


TRANSFORM_NAME = "bridge_event_time_order"
TRANSFORM_VERSION = "1.0.0"
HASH_ALGORITHM = "sha256"
SOURCE_HASH_SCOPE = "jsonl_record_bytes_without_line_terminator"
OUTPUT_HASH_SCOPE = "canonical_json_utf8_without_line_terminator"

TIME_KEYS = ("t_rel_ms", "t_ms")
CLOCK_DOMAIN_KEYS = (
    "clock_id",
    "clock_domain",
    "timebase",
    "timebase_id",
    "source_clock",
    "source_clock_id",
)
EXPLICIT_ORDER_KEYS = (
    "burst_id",
    "causal_group",
    "causal_group_id",
    "caused_by",
    "event_group",
    "event_group_id",
    "event_order",
    "event_ordering",
    "event_sequence",
    "follows",
    "group_id",
    "happens_before",
    "parent_event_id",
    "precedes",
    "predecessor_id",
    "segment_id",
    "sequence_id",
    "sequence_index",
    "trial_id",
)

REASON_RETAINED = "BRIDGE_EVENTS_ALREADY_GLOBALLY_ORDERED"
REASON_REPAIRED = "BRIDGE_EVENTS_STABLE_SORTED_SINGLE_GLOBAL_CLOCK"
REASON_NOT_BRIDGE = "BRIDGE_RECORD_SHAPE_INVALID"
REASON_EMPTY_STREAM = "BRIDGE_EVENT_STREAM_MISSING_OR_EMPTY"
REASON_EVENT_NOT_OBJECT = "BRIDGE_EVENT_NOT_OBJECT"
REASON_TIME_KEY_COUNT = "BRIDGE_EVENT_TIMESTAMP_KEY_COUNT_INVALID"
REASON_MIXED_TIME_KEYS = "BRIDGE_EVENT_TIMESTAMP_KEYS_MIXED"
REASON_INVALID_TIME = "BRIDGE_EVENT_TIMESTAMP_NOT_FINITE_NUMBER"
REASON_NEGATIVE_RELATIVE_TIME = "BRIDGE_RELATIVE_TIMESTAMP_NEGATIVE"
REASON_MULTIPLE_CLOCKS = "BRIDGE_MULTIPLE_CLOCK_DOMAINS"
REASON_EXPLICIT_ORDER = "BRIDGE_EXPLICIT_CAUSAL_OR_SEQUENCE_ORDER"
REASON_INVALID_JSON = "BRIDGE_SOURCE_JSON_INVALID"
REASON_INVALID_UTF8 = "BRIDGE_SOURCE_UTF8_INVALID"


class BridgeCurationError(ValueError):
    """The curation input or source-root contract is invalid."""


@dataclass(frozen=True)
class CurationDecision:
    """One deterministic record-level curation decision.

    ``output_record`` is populated for retained and repaired records.
    ``quarantine_record`` preserves a parsed source record when it cannot be
    emitted.  Invalid JSON/UTF-8 has no parsed quarantine record, but remains
    recoverable through the exact source path, line, and hash in ``manifest``.
    """

    action: str
    output_record: dict[str, Any] | None
    quarantine_record: Any | None
    manifest: dict[str, Any]

    def as_dict(self, *, include_records: bool = True) -> dict[str, Any]:
        payload: dict[str, Any] = {"manifest": self.manifest}
        if include_records:
            payload["output_record"] = self.output_record
            payload["quarantine_record"] = self.quarantine_record
        return payload


def sha256_hex(data: bytes) -> str:
    """Return the lowercase SHA-256 digest for exact bytes."""

    return hashlib.sha256(data).hexdigest()


def canonical_json_bytes(value: Any) -> bytes:
    """Serialize JSON deterministically for output and transformation hashes."""

    return json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
        allow_nan=False,
    ).encode("utf-8")


def canonical_json_line(value: Any) -> bytes:
    """Return the exact canonical JSONL bytes expected by an integrator."""

    return canonical_json_bytes(value) + b"\n"


def _evidence_hash(value: Any) -> str:
    """Hash even malformed JSON-like values for quarantine evidence.

    Curated output always uses strict :func:`canonical_json_bytes`.  The
    fallback exists only so a non-finite timestamp or another malformed value
    can still receive deterministic transformation evidence before quarantine.
    """

    try:
        payload = canonical_json_bytes(value)
    except (TypeError, ValueError):
        payload = json.dumps(
            value,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
            allow_nan=True,
            default=repr,
        ).encode("utf-8")
    return sha256_hex(payload)


def _is_finite_number(value: Any) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
    )


def _record_locator(record: Any) -> str | None:
    if not isinstance(record, dict):
        return None
    record_id = record.get("id")
    if isinstance(record_id, str) and record_id.strip():
        return record_id
    view = record.get("language_view")
    if not isinstance(view, dict):
        return None
    trajectory = view.get("trajectory")
    if not isinstance(trajectory, dict):
        return None
    state = trajectory.get("state")
    if not isinstance(state, dict):
        return None
    episode_id = state.get("episode_id")
    if isinstance(episode_id, str) and episode_id.strip():
        return episode_id
    return None


def _canonical_marker(value: Any) -> str:
    """Make arbitrary JSON-compatible clock identifiers comparable."""

    try:
        return canonical_json_bytes(value).decode("utf-8")
    except (TypeError, ValueError):
        return repr(value)


def _declared_clock_domains(record: dict[str, Any], events: list[Any]) -> list[str]:
    values: set[str] = set()
    containers: list[dict[str, Any]] = [record]
    meta = record.get("meta")
    if isinstance(meta, dict):
        containers.append(meta)
    containers.extend(event for event in events if isinstance(event, dict))
    for container in containers:
        for key in CLOCK_DOMAIN_KEYS:
            if key in container:
                values.add(f"{key}={_canonical_marker(container[key])}")

    # Different aliases with the same scalar identify one domain.  Strip the
    # field names for the ambiguity check while preserving full evidence.
    semantic_values = {item.split("=", 1)[1] for item in values}
    if len(semantic_values) <= 1:
        return sorted(values)
    return sorted(values)


def _explicit_order_fields(record: dict[str, Any], events: list[Any]) -> list[str]:
    found: set[str] = set()
    containers: list[dict[str, Any]] = [record]
    meta = record.get("meta")
    if isinstance(meta, dict):
        containers.append(meta)
    containers.extend(event for event in events if isinstance(event, dict))
    for container in containers:
        found.update(key for key in EXPLICIT_ORDER_KEYS if key in container)
    return sorted(found)


def _adjacent_descents(times: Sequence[float]) -> list[dict[str, Any]]:
    return [
        {
            "left_index": index - 1,
            "right_index": index,
            "left_time": times[index - 1],
            "right_time": times[index],
        }
        for index in range(1, len(times))
        if times[index] < times[index - 1]
    ]


def _base_manifest(
    *,
    source_path: str,
    source_line: int,
    source_hash: str,
    source_file_hash: str | None,
    source_record_locator: str | None,
) -> dict[str, Any]:
    return {
        "source_path": source_path,
        "source_line": source_line,
        "source_hash": source_hash,
        "source_file_hash": source_file_hash,
        "source_hash_algorithm": HASH_ALGORITHM,
        "source_hash_scope": SOURCE_HASH_SCOPE,
        "source_record_locator": source_record_locator,
        "transform_name": TRANSFORM_NAME,
        "transform_version": TRANSFORM_VERSION,
        "action": None,
        "reason_codes": [],
        # The identity/provenance lane owns canonical IDs.  This lane exposes
        # the existing top-level ID only and never invents one.
        "output_id": None,
        "output_id_status": "pending_identity_transform",
        "output_hash": None,
        "output_hash_algorithm": HASH_ALGORITHM,
        "output_hash_scope": OUTPUT_HASH_SCOPE,
        "evidence": {},
    }


def _finish_manifest(
    manifest: dict[str, Any],
    *,
    action: str,
    reason_codes: Iterable[str],
    evidence: dict[str, Any],
    output_record: dict[str, Any] | None,
) -> dict[str, Any]:
    finished = dict(manifest)
    finished["action"] = action
    finished["reason_codes"] = list(dict.fromkeys(reason_codes))
    finished["evidence"] = evidence
    if output_record is not None:
        output_id = output_record.get("id")
        if isinstance(output_id, str) and output_id.strip():
            finished["output_id"] = output_id
            finished["output_id_status"] = "present"
        finished["output_hash"] = sha256_hex(canonical_json_bytes(output_record))
    return finished


def _quarantine(
    record: Any,
    manifest: dict[str, Any],
    reason_codes: Iterable[str],
    evidence: dict[str, Any],
) -> CurationDecision:
    finished = _finish_manifest(
        manifest,
        action="quarantine",
        reason_codes=reason_codes,
        evidence=evidence,
        output_record=None,
    )
    return CurationDecision(
        action="quarantine",
        output_record=None,
        quarantine_record=copy.deepcopy(record),
        manifest=finished,
    )


def curate_record(
    record: Any,
    *,
    source_path: str,
    source_line: int,
    source_hash: str,
    source_file_hash: str | None = None,
) -> CurationDecision:
    """Return a deterministic Bridge timing decision without mutating ``record``."""

    if not isinstance(source_path, str) or not source_path:
        raise BridgeCurationError("source_path must be a non-empty string")
    if (
        not isinstance(source_line, int)
        or isinstance(source_line, bool)
        or source_line < 1
    ):
        raise BridgeCurationError("source_line must be a positive integer")
    if not isinstance(source_hash, str) or not source_hash:
        raise BridgeCurationError("source_hash must be a non-empty string")

    manifest = _base_manifest(
        source_path=source_path,
        source_line=source_line,
        source_hash=source_hash,
        source_file_hash=source_file_hash,
        source_record_locator=_record_locator(record),
    )
    if not isinstance(record, dict):
        return _quarantine(record, manifest, [REASON_NOT_BRIDGE], {})

    events = record.get("spike_events")
    if "language_view" not in record or not isinstance(events, list):
        return _quarantine(record, manifest, [REASON_NOT_BRIDGE], {})
    if not events:
        return _quarantine(
            record,
            manifest,
            [REASON_EMPTY_STREAM],
            {"event_count": 0},
        )

    reason_codes: list[str] = []
    event_time_keys: list[str | None] = []
    times: list[float] = []
    invalid_event_indices: list[int] = []
    invalid_time_indices: list[int] = []
    negative_time_indices: list[int] = []

    for index, event in enumerate(events):
        if not isinstance(event, dict):
            reason_codes.append(REASON_EVENT_NOT_OBJECT)
            invalid_event_indices.append(index)
            event_time_keys.append(None)
            continue
        present = [key for key in TIME_KEYS if key in event]
        if len(present) != 1:
            reason_codes.append(REASON_TIME_KEY_COUNT)
            invalid_time_indices.append(index)
            event_time_keys.append(None)
            continue
        key = present[0]
        event_time_keys.append(key)
        value = event[key]
        if not _is_finite_number(value):
            reason_codes.append(REASON_INVALID_TIME)
            invalid_time_indices.append(index)
            continue
        numeric = float(value)
        times.append(numeric)
        if key == "t_rel_ms" and numeric < 0:
            reason_codes.append(REASON_NEGATIVE_RELATIVE_TIME)
            negative_time_indices.append(index)

    valid_keys = {key for key in event_time_keys if key is not None}
    if len(valid_keys) > 1:
        reason_codes.append(REASON_MIXED_TIME_KEYS)

    declared_clocks = _declared_clock_domains(record, events)
    semantic_clocks = {item.split("=", 1)[1] for item in declared_clocks}
    if len(semantic_clocks) > 1:
        reason_codes.append(REASON_MULTIPLE_CLOCKS)

    explicit_order_fields = _explicit_order_fields(record, events)

    evidence: dict[str, Any] = {
        "event_count": len(events),
        "event_time_keys": sorted(valid_keys),
        "declared_clock_domains": declared_clocks,
        "explicit_order_fields": explicit_order_fields,
        "invalid_event_indices": invalid_event_indices,
        "invalid_time_indices": invalid_time_indices,
        "negative_relative_time_indices": negative_time_indices,
        "original_event_order_hash": _evidence_hash(events),
    }

    if reason_codes:
        evidence["repair_eligible"] = False
        return _quarantine(record, manifest, reason_codes, evidence)

    # Every event contributed exactly one valid timestamp at this point.
    time_key = next(iter(valid_keys))
    descents = _adjacent_descents(times)
    permutation = sorted(range(len(events)), key=times.__getitem__)
    sorted_events = [copy.deepcopy(events[index]) for index in permutation]
    sorted_times = [times[index] for index in permutation]
    moved = sum(index != source_index for index, source_index in enumerate(permutation))
    evidence.update(
        {
            "event_time_key": time_key,
            "clock_scope": (
                "record_relative_global" if time_key == "t_rel_ms" else "single_global"
            ),
            "repair_eligible": True,
            "adjacent_descents_before": descents,
            "adjacent_descents_after": _adjacent_descents(sorted_times),
            "stable_sort_permutation": permutation,
            "stable_ties_preserved": True,
            "moved_event_count": moved,
            "time_min": min(times),
            "time_max": max(times),
            "output_event_order_hash": sha256_hex(canonical_json_bytes(sorted_events)),
        }
    )

    if descents and explicit_order_fields:
        evidence["repair_eligible"] = False
        return _quarantine(
            record,
            manifest,
            [REASON_EXPLICIT_ORDER],
            evidence,
        )

    output_record = copy.deepcopy(record)
    if descents:
        output_record["spike_events"] = sorted_events
        action = "repair"
        reasons = [REASON_REPAIRED]
    else:
        action = "retain"
        reasons = [REASON_RETAINED]

    finished = _finish_manifest(
        manifest,
        action=action,
        reason_codes=reasons,
        evidence=evidence,
        output_record=output_record,
    )
    return CurationDecision(
        action=action,
        output_record=output_record,
        quarantine_record=None,
        manifest=finished,
    )


def _source_display_path(path: Path, source_root: Path | None) -> str:
    resolved = path.resolve(strict=True)
    if source_root is None:
        return path.as_posix()
    root = source_root.resolve(strict=True)
    try:
        return resolved.relative_to(root).as_posix()
    except ValueError as exc:
        raise BridgeCurationError(f"source is outside source_root: {path}") from exc


def _record_bytes_without_terminator(line: bytes) -> bytes:
    if line.endswith(b"\n"):
        line = line[:-1]
    if line.endswith(b"\r"):
        line = line[:-1]
    return line


def _reject_json_constant(value: str) -> None:
    raise ValueError(f"non-standard JSON numeric constant: {value}")


def _source_failure_decision(
    *,
    source_path: str,
    source_line: int,
    source_hash: str,
    source_file_hash: str,
    reason_code: str,
    detail: str,
) -> CurationDecision:
    manifest = _base_manifest(
        source_path=source_path,
        source_line=source_line,
        source_hash=source_hash,
        source_file_hash=source_file_hash,
        source_record_locator=None,
    )
    return _quarantine(
        None,
        manifest,
        [reason_code],
        {"parse_error": detail, "repair_eligible": False},
    )


def curate_jsonl(
    source: str | Path,
    *,
    source_root: str | Path | None = None,
) -> list[CurationDecision]:
    """Curate every physical JSONL line while preserving exact source hashes."""

    path = Path(source)
    if not path.is_file():
        raise BridgeCurationError(f"not a JSONL file: {path}")
    root = Path(source_root) if source_root is not None else None
    display_path = _source_display_path(path, root)
    raw_file = path.read_bytes()
    source_file_hash = sha256_hex(raw_file)
    decisions: list[CurationDecision] = []

    for line_number, physical_line in enumerate(raw_file.splitlines(keepends=True), 1):
        record_bytes = _record_bytes_without_terminator(physical_line)
        source_hash = sha256_hex(record_bytes)
        try:
            text = record_bytes.decode("utf-8")
        except UnicodeDecodeError as exc:
            decisions.append(
                _source_failure_decision(
                    source_path=display_path,
                    source_line=line_number,
                    source_hash=source_hash,
                    source_file_hash=source_file_hash,
                    reason_code=REASON_INVALID_UTF8,
                    detail=str(exc),
                )
            )
            continue
        try:
            record = json.loads(text, parse_constant=_reject_json_constant)
        except (json.JSONDecodeError, ValueError) as exc:
            decisions.append(
                _source_failure_decision(
                    source_path=display_path,
                    source_line=line_number,
                    source_hash=source_hash,
                    source_file_hash=source_file_hash,
                    reason_code=REASON_INVALID_JSON,
                    detail=str(exc),
                )
            )
            continue
        decisions.append(
            curate_record(
                record,
                source_path=display_path,
                source_line=line_number,
                source_hash=source_hash,
                source_file_hash=source_file_hash,
            )
        )
    return decisions


def curate_paths(
    sources: Iterable[str | Path],
    *,
    source_root: str | Path | None = None,
) -> list[CurationDecision]:
    """Curate source files in stable path order, rejecting duplicate inputs."""

    paths = [Path(source) for source in sources]
    resolved = [path.resolve(strict=True) for path in paths]
    if len(set(resolved)) != len(resolved):
        raise BridgeCurationError("duplicate source path")
    decisions: list[CurationDecision] = []
    for path in sorted(paths, key=lambda item: item.as_posix()):
        decisions.extend(curate_jsonl(path, source_root=source_root))
    return decisions


def summarize(decisions: Sequence[CurationDecision]) -> dict[str, Any]:
    """Return deterministic action and reason counts for a decision set."""

    actions = Counter(decision.action for decision in decisions)
    reasons = Counter(
        reason for decision in decisions for reason in decision.manifest["reason_codes"]
    )
    return {
        "transform_name": TRANSFORM_NAME,
        "transform_version": TRANSFORM_VERSION,
        "records": len(decisions),
        "actions": dict(sorted(actions.items())),
        "reason_codes": dict(sorted(reasons.items())),
    }


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("sources", nargs="+", help="Bridge JSONL source files")
    parser.add_argument(
        "--source-root",
        help="root used to make source_path stable and workspace-relative",
    )
    parser.add_argument(
        "--emit",
        choices=("summary", "manifest", "bundle"),
        default="summary",
        help="JSON payload printed to stdout; this command never writes files",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        decisions = curate_paths(args.sources, source_root=args.source_root)
    except (BridgeCurationError, OSError) as exc:
        raise SystemExit(f"curate_bridge: {exc}") from exc

    if args.emit == "summary":
        payload: Any = summarize(decisions)
    elif args.emit == "manifest":
        payload = [decision.manifest for decision in decisions]
    else:
        payload = {
            "summary": summarize(decisions),
            "decisions": [decision.as_dict() for decision in decisions],
        }
    print(
        json.dumps(
            payload, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
