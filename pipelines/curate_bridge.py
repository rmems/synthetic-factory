#!/usr/bin/env python3
"""Deterministically repair or quarantine Bridge event-stream ordering.

The record-level API remains pure.  Callers can import :func:`curate_jsonl`
and compose the returned decisions with the other curation lanes, use the CLI
to print a summary, manifest, or complete decision bundle to stdout, or pass
``--out-dir`` to materialize one new gate-compatible lane tree.  Materialized
trees preserve source-relative JSONL paths, include every disposition in
``BRIDGE-MANIFEST.jsonl``, and are published atomically without clobbering an
existing destination.  Because that tree is gate-compatible, materialization
requires a raster sidecar per record; the pure decision API stays lenient
unless a caller passes ``require_raster=True``.

An unsorted stream is repaired only when every event has one finite timestamp
under the same supported key, all declared clock-domain identifiers agree,
and no explicit causal/sequence metadata would be reordered.  Otherwise the
record is quarantined with machine-readable reason codes.

Examples::

    python3 pipelines/curate_bridge.py \
      --source-root outputs/raw/2026-08-17 \
      --emit manifest \
      outputs/raw/2026-08-17/neuromorphic-event-language-bridge/batch-r02.jsonl

    python3 pipelines/curate_bridge.py \
      --source-root outputs/raw/2026-08-17 \
      --out-dir outputs/cleaned/lane-bridge \
      outputs/raw/2026-08-17/neuromorphic-event-language-bridge/batch-*.jsonl
"""

from __future__ import annotations

import argparse
import copy
import ctypes
import errno
import hashlib
import json
import math
import os
import shutil
import tempfile
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Sequence

from curate_bridge_gate import _validate_gate_compute, _validate_gate_snn
from curate_bridge_raster import (
    _validate_raster,
    _validate_third_factor,  # noqa: F401 - preserve the established private hook
)


TRANSFORM_NAME = "bridge_event_time_order"
TRANSFORM_VERSION = "1.0.0"
HASH_ALGORITHM = "sha256"
SOURCE_HASH_SCOPE = "jsonl_record_bytes_without_line_terminator"
OUTPUT_HASH_SCOPE = "canonical_json_utf8_without_line_terminator"
MANIFEST_NAME = "BRIDGE-MANIFEST.jsonl"

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

# Raster / spike-budget sidecar (20-50 ms excerpt + routing, 23 pJ/spike)
RASTER_WINDOW_MIN_MS = 20
RASTER_WINDOW_MAX_MS = 50
RASTER_ENERGY_PJ_PER_SPIKE = 23
RASTER_ENERGY_UJ_PER_SPIKE = 23e-6  # 23 pJ = 23e-6 uJ
REASON_RASTER_MISSING = "BRIDGE_RASTER_MISSING"
REASON_RASTER_WINDOW = "BRIDGE_RASTER_WINDOW_INVALID"
REASON_RASTER_SPIKE_BUDGET = "BRIDGE_SPIKE_BUDGET_MISMATCH"
REASON_RASTER_ENERGY = "BRIDGE_ENERGY_MISMATCH"
REASON_RASTER_ROUTING = "BRIDGE_RASTER_ROUTING_MISSING"
REASON_RASTER_EXCERPT = "BRIDGE_RASTER_EXCERPT_INVALID"
REASON_THIRD_FACTOR_INVALID = "BRIDGE_THIRD_FACTOR_ROUTING_INVALID"
REASON_GATE_SNN_INVALID = "BRIDGE_GATE_SNN_SPEC_INVALID"

# Spike-implemented gate head ("gate-as-SNN"): the safety gate expressed as a
# neuron population with thresholds and a decision window, so a distillation
# probe reads neuron counts instead of prose.
GATE_SNN_KEY = "gate_snn"


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
    """True for a real number this module's float arithmetic can evaluate.

    JSON integers are unbounded, so ``math.isfinite`` on a declared
    ``10**400`` raises ``OverflowError`` instead of returning False. Every
    caller here is guarding a float comparison, so the conversion itself is
    the test: an integer no float can hold is not a finite number for this
    purpose, and it becomes a reason code rather than an exception escaping
    into the publish gate, the training audit, or the distillation probe.
    """

    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and _finite_float(value) is not None
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


def _expected_spikes(neurons: int, mean_rate_hz: float, window_s: float) -> int | None:
    """Spike budget: neurons * rate * window, Loihi-2-class 23 pJ/spike model."""
    try:
        product = float(neurons) * float(mean_rate_hz) * float(window_s)
    except OverflowError:
        return None
    if not math.isfinite(product):
        return None
    try:
        return int(round(product))
    except (OverflowError, ValueError):
        return None


def _finite_float(value: Any) -> float | None:
    """``float(value)`` when it lands inside the IEEE-754 double range.

    JSON integers are unbounded, so a record can declare a spike count no
    float can hold.  Every tolerance comparison in this module mixes that
    count with a float, which raises ``OverflowError`` instead of reporting a
    mismatch, so callers convert through here and read ``None`` as "this
    budget cannot be evaluated" — a reason code, never an exception escaping
    into the publish gate, the training audit, or the distillation probe.
    """

    try:
        result = float(value)
    except (OverflowError, TypeError, ValueError):
        return None
    return result if math.isfinite(result) else None


def _spike_energy(spikes: int, per_spike: float) -> float | None:
    """Energy for a spike count at 23 pJ/spike, or None when it is not finite."""

    count = _finite_float(spikes)
    if count is None:
        return None
    return _finite_float(count * per_spike)


def is_bridge_record(record: Any) -> bool:
    """Return True for a paired spike/language Bridge record."""

    view = record.get("language_view") if isinstance(record, dict) else None
    return (
        isinstance(record, dict)
        and isinstance(view, dict)
        and isinstance(view.get("trajectory"), dict)
        and isinstance(record.get("spike_events"), list)
    )


def is_thalamic_record(record: Any) -> bool:
    """Return True for a top-level Thalamic trajectory record."""

    return isinstance(record, dict) and all(
        key in record
        for key in (
            "state",
            "proposed_action",
            "safety_decision",
            "executed_action",
            "future_outcome",
            "reward_components",
        )
    )


def _expected_gate_decision(record: dict[str, Any]) -> str | None:
    """Return the structured safety decision a gate-SNN head must reproduce."""

    view = record.get("language_view")
    trajectory = view.get("trajectory") if isinstance(view, dict) else None
    nested = trajectory.get("safety_decision") if isinstance(trajectory, dict) else None
    top = record.get("safety_decision")
    for safety in (nested, top):
        decision = safety.get("decision") if isinstance(safety, dict) else None
        if isinstance(decision, str) and decision.strip():
            return decision
    return None


def _declared(container: Any, key: str) -> tuple[bool, Any]:
    """Return ``(declared, value)`` for ``key`` on a mapping carrier.

    Presence of the key -- not truthiness of its value -- is what makes a
    carrier declared.  An explicit ``null`` is a declaration of a
    schema-invalid sidecar, so it must win its precedence slot and fail
    validation rather than fall through to a lower-precedence carrier and let
    an ambiguous duplicate declaration publish unchecked.
    """

    if isinstance(container, dict) and key in container:
        return True, container[key]
    return False, None


def raster_sidecar(record: Any) -> tuple[str | None, Any]:
    """Resolve the raster sidecar location and value for one record.

    A valid top-level ``raster`` wins, otherwise a valid ``meta.raster``
    sidecar.  A malformed sidecar is still returned (with its location) so its
    reason codes survive; ``(None, None)`` means no sidecar exists at all.
    """

    if not isinstance(record, dict):
        return None, None
    meta = record.get("meta")
    candidates = (
        ("raster", *_declared(record, "raster")),
        ("meta.raster", *_declared(meta, "raster")),
    )
    # The first declared carrier wins outright, valid or not. A malformed
    # higher-precedence declaration must surface as invalid rather than be
    # silently skipped in favor of a lower-precedence dict, which would let
    # ambiguous duplicate declarations through unchecked. Mirrors
    # gate_snn_sidecar, which had the identical two-pass defect.  Declaration
    # is key presence, so an explicit ``raster: null`` is a carrier too.
    for location, declared, value in candidates:
        if declared:
            return location, value
    return None, None


def gate_snn_sidecar(record: Any) -> tuple[str | None, Any]:
    """Resolve the spike-implemented gate spec location and value.

    Accepted carriers, in precedence order: top-level ``gate_snn``,
    ``meta.gate_snn``, ``language_view.trajectory.gate_snn``, and
    ``language_view.trajectory.safety_decision.gate_snn``. The first declared
    carrier wins outright, valid or not — a malformed higher-precedence
    declaration (e.g. a non-dict top-level ``gate_snn``) must surface as
    invalid rather than being silently skipped in favor of a lower-precedence
    dict, which would let ambiguous duplicate declarations through unchecked.
    """

    if not isinstance(record, dict):
        return None, None
    meta = record.get("meta")
    view = record.get("language_view")
    trajectory = view.get("trajectory") if isinstance(view, dict) else None
    decision = trajectory.get("safety_decision") if isinstance(trajectory, dict) else None
    candidates = (
        (GATE_SNN_KEY, *_declared(record, GATE_SNN_KEY)),
        (f"meta.{GATE_SNN_KEY}", *_declared(meta, GATE_SNN_KEY)),
        (
            f"language_view.trajectory.{GATE_SNN_KEY}",
            *_declared(trajectory, GATE_SNN_KEY),
        ),
        (
            f"language_view.trajectory.safety_decision.{GATE_SNN_KEY}",
            *_declared(decision, GATE_SNN_KEY),
        ),
    )
    for location, declared, value in candidates:
        if declared:
            return location, value
    return None, None


def _gate_compute_sidecar(record: dict[str, Any]) -> tuple[str | None, Any]:
    """Return the record's first declared gate_compute block, valid or not.

    Accepted carriers, in precedence order: top-level ``gate_compute``,
    ``language_view.trajectory.gate_compute``, and
    ``language_view.trajectory.safety_decision.gate_compute``.  As for the
    raster and ``gate_snn`` sidecars, the first declared carrier wins
    outright: a malformed higher-precedence declaration must surface as
    invalid rather than be silently skipped in favor of a lower-precedence
    dict, which would let an ambiguous duplicate declaration through
    unchecked.
    """

    if not isinstance(record, dict):
        return None, None
    view = record.get("language_view")
    trajectory = view.get("trajectory") if isinstance(view, dict) else None
    probe = trajectory.get("safety_decision") if isinstance(trajectory, dict) else None
    candidates = (
        ("gate_compute", *_declared(record, "gate_compute")),
        (
            "language_view.trajectory.gate_compute",
            *_declared(trajectory, "gate_compute"),
        ),
        (
            "language_view.trajectory.safety_decision.gate_compute",
            *_declared(probe, "gate_compute"),
        ),
    )
    for location, declared, value in candidates:
        if declared:
            return location, value
    return None, None


def _raster_reasons(
    record: dict[str, Any],
    *,
    require_raster: bool,
    require_routing_table: bool = False,
) -> tuple[list[str], dict[str, Any]]:
    """Collect raster / gate-budget reason codes and evidence for one record.

    This is the single owner of the spike arithmetic (20-50 ms window,
    ``spikes = round(neurons * rate * window_s)``, 23 pJ/spike) so the curator,
    the training audit, and the distillation probe never disagree.
    """

    reason_codes: list[str] = []
    evidence: dict[str, Any] = {}
    location, raster = raster_sidecar(record)
    if location is not None:
        evidence["raster_location"] = location
        _validate_raster(
            raster,
            reason_codes=reason_codes,
            evidence=evidence,
            require_routing_table=require_routing_table,
        )
    else:
        evidence["raster_present"] = False
        if require_raster:
            reason_codes.append(REASON_RASTER_MISSING)
    gate_compute_location, gate_compute = _gate_compute_sidecar(record)
    if gate_compute_location is not None:
        evidence["gate_compute_location"] = gate_compute_location
        _validate_gate_compute(gate_compute, reason_codes=reason_codes, evidence=evidence)
    gate_snn_location, gate_snn = gate_snn_sidecar(record)
    if gate_snn_location is not None:
        evidence["gate_snn_location"] = gate_snn_location
        _validate_gate_snn(
            gate_snn,
            reason_codes=reason_codes,
            evidence=evidence,
            expected_decision=_expected_gate_decision(record),
        )
    else:
        evidence["gate_snn_present"] = False
    return reason_codes, evidence


def raster_status(
    record: Any,
    *,
    require_raster: bool = True,
    require_routing_table: bool = False,
) -> dict[str, Any]:
    """Summarize one record's raster/gate evidence for auditors and probes.

    Returns machine-readable counts only — no prose is ever parsed.  Callers
    that only want the reason codes can read ``reason_codes``; callers that
    want to load spikes should use :mod:`spike_probe`.
    """

    if not is_bridge_record(record) and not is_thalamic_record(record):
        return {
            "bridge_record": False,
            "raster_present": False,
            "raster_valid": False,
            "raster_location": None,
            "routing_table_entries": 0,
            "third_factor_present": False,
            "gate_snn_present": False,
            "gate_snn_valid": False,
            "spikes": None,
            "reason_codes": [],
            "evidence": {},
        }
    reason_codes, evidence = _raster_reasons(
        record,
        require_raster=require_raster,
        require_routing_table=require_routing_table,
    )
    location, raster = raster_sidecar(record)
    spikes = raster.get("spikes") if isinstance(raster, dict) else None
    if not isinstance(spikes, int) or isinstance(spikes, bool):
        spikes = None
    present = bool(evidence.get("raster_present"))
    return {
        "bridge_record": is_bridge_record(record),
        "raster_present": present,
        "raster_valid": present and not reason_codes,
        "raster_location": location,
        "routing_table_entries": int(evidence.get("raster_routing_table_entries", 0)),
        "third_factor_present": bool(evidence.get("raster_third_factor_present")),
        "gate_snn_present": bool(evidence.get("gate_snn_present")),
        "gate_snn_valid": bool(evidence.get("gate_snn_valid")),
        "spikes": spikes,
        "reason_codes": sorted(set(reason_codes)),
        "evidence": evidence,
    }


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
    require_raster: bool = False,
    require_routing_table: bool = False,
) -> CurationDecision:
    """Return a deterministic Bridge timing decision without mutating ``record``.

    When ``require_raster`` is True, a missing ``raster`` sidecar (20-50 ms
    excerpt + routing) also quarantines the record.  Spike-budget checks
    (spikes = neurons*rate*window @23 pJ), third-factor routing entries, and
    the spike-implemented ``gate_snn`` head are always validated when the
    relevant fields are present, so minimal legacy fixtures remain green
    unless their budgets or specs are wrong.
    """

    if not isinstance(source_path, str) or not source_path:
        raise BridgeCurationError("source_path must be a non-empty string")
    if not isinstance(source_line, int) or isinstance(source_line, bool) or source_line < 1:
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
    if not is_bridge_record(record):
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

    # --- Raster / spike-budget sidecar validation (20-50 ms, 23 pJ/spike) ---
    # Uses helper validators so manifests stay auditable. Missing raster only
    # quarantines when require_raster=True to keep minimal legacy fixtures green.
    # The sidecar resolver, the spike budget, the third-factor routing entry,
    # and the gate-as-SNN spec all live in _raster_reasons so the curator, the
    # training audit, and the distillation probe share one implementation.
    # REASON_RASTER_MISSING applies only when neither location carries a
    # sidecar at all, and only when require_raster is set.
    raster_reasons, raster_evidence = _raster_reasons(
        record,
        require_raster=require_raster,
        require_routing_table=require_routing_table,
    )
    evidence["raster"] = raster_evidence
    if raster_reasons:
        # Deduplicate and keep deterministic order.
        uniq = sorted(set(raster_reasons))
        evidence["repair_eligible"] = False
        return _quarantine(record, manifest, uniq, evidence)

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
    require_raster: bool = False,
    require_routing_table: bool = False,
) -> list[CurationDecision]:
    """Curate every physical JSONL line while preserving exact source hashes.

    ``require_raster`` is forwarded to :func:`curate_record`.  It stays False
    here so the pure decision API and the reporting CLI keep their existing
    lenient behavior; :func:`materialize_paths` turns it on because the tree
    it publishes is advertised as gate-compatible.
    """

    path = Path(source)
    if not path.is_file():
        raise BridgeCurationError(f"not a JSONL file: {path}")
    root = Path(source_root) if source_root is not None else None
    display_path = _source_display_path(path, root)
    raw_file = path.read_bytes()
    source_file_hash = sha256_hex(raw_file)
    decisions: list[CurationDecision] = []

    # JSONL is framed only by literal LF.  Unicode line separators inside a
    # JSON string are payload bytes, while one CR immediately before LF is the
    # line terminator's CRLF half and is not part of the record digest.
    for line_number, physical_line in enumerate(raw_file.split(b"\n"), 1):
        record_bytes = _record_bytes_without_terminator(physical_line)
        if not record_bytes.strip():
            continue
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
                require_raster=require_raster,
                require_routing_table=require_routing_table,
            )
        )
    return decisions


def curate_paths(
    sources: Iterable[str | Path],
    *,
    source_root: str | Path | None = None,
    require_raster: bool = False,
    require_routing_table: bool = False,
) -> list[CurationDecision]:
    """Curate source files in stable path order, rejecting duplicate inputs."""

    paths = [Path(source) for source in sources]
    resolved = [path.resolve(strict=True) for path in paths]
    if len(set(resolved)) != len(resolved):
        raise BridgeCurationError("duplicate source path")
    decisions: list[CurationDecision] = []
    for path in sorted(paths, key=lambda item: item.as_posix()):
        decisions.extend(
            curate_jsonl(
                path,
                source_root=source_root,
                require_raster=require_raster,
                require_routing_table=require_routing_table,
            )
        )
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


def _is_under_raw(path: Path) -> bool:
    parts = path.resolve(strict=False).parts
    return any(parts[index : index + 2] == ("outputs", "raw") for index in range(len(parts) - 1))


def _safe_relative_path(value: str, *, label: str) -> Path:
    path = Path(value)
    if path.is_absolute() or not path.parts or ".." in path.parts:
        raise BridgeCurationError(f"{label} must be a safe relative path: {value!r}")
    parts = tuple(part for part in path.parts if part not in {"", "."})
    if not parts:
        raise BridgeCurationError(f"{label} must name a file")
    return Path(*parts)


def _write_exclusive(path: Path, payload: bytes) -> None:
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
    except BaseException:
        path.unlink(missing_ok=True)
        raise


def _rename_noreplace(source: Path, destination: Path) -> None:
    """Atomically publish ``source`` while refusing any existing destination."""

    if os.name == "nt":
        try:
            source.rename(destination)
        except FileExistsError as exc:
            raise BridgeCurationError(
                f"destination already exists; refusing overwrite: {destination}"
            ) from exc
        return

    libc = ctypes.CDLL(None, use_errno=True)
    renameat2 = getattr(libc, "renameat2", None)
    if renameat2 is None:
        raise BridgeCurationError("atomic no-replace publication is unavailable on this platform")
    renameat2.argtypes = [
        ctypes.c_int,
        ctypes.c_char_p,
        ctypes.c_int,
        ctypes.c_char_p,
        ctypes.c_uint,
    ]
    renameat2.restype = ctypes.c_int
    result = renameat2(
        -100,
        os.fsencode(source),
        -100,
        os.fsencode(destination),
        1,
    )
    if result == 0:
        return
    error = ctypes.get_errno()
    if error in {errno.EEXIST, errno.ENOTEMPTY}:
        raise BridgeCurationError(f"destination already exists; refusing overwrite: {destination}")
    raise BridgeCurationError(f"cannot atomically publish {destination}: {os.strerror(error)}")


def _validate_materialized_tree(
    root: Path,
    decisions: Sequence[CurationDecision],
    manifest_relative: Path,
) -> None:
    """Authenticate staged output records and manifest before publication."""

    manifest_path = root / manifest_relative
    try:
        manifest_lines = [
            json.loads(line, parse_constant=_reject_json_constant)
            for line in manifest_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        raise BridgeCurationError(f"invalid staged Bridge manifest: {exc}") from exc
    expected_manifest = [decision.manifest for decision in decisions]
    if manifest_lines != expected_manifest:
        raise BridgeCurationError("staged Bridge manifest differs from decisions")

    expected: dict[str, list[str]] = {}
    for decision in decisions:
        if decision.output_record is None:
            continue
        expected.setdefault(decision.manifest["source_path"], []).append(
            decision.manifest["output_hash"]
        )
    actual_paths = {
        path.relative_to(root).as_posix(): path
        for path in sorted(root.rglob("*.jsonl"))
        if path.is_file() and path != manifest_path
    }
    if set(actual_paths) != set(expected):
        raise BridgeCurationError(
            "staged Bridge output paths differ from manifest: "
            f"expected={sorted(expected)}, actual={sorted(actual_paths)}"
        )
    for relative, expected_hashes in sorted(expected.items()):
        actual_hashes: list[str] = []
        for line in actual_paths[relative].read_bytes().split(b"\n"):
            if not line.strip():
                continue
            try:
                record = json.loads(line.decode("utf-8"), parse_constant=_reject_json_constant)
            except (UnicodeError, json.JSONDecodeError, ValueError) as exc:
                raise BridgeCurationError(
                    f"invalid staged Bridge output {relative}: {exc}"
                ) from exc
            actual_hashes.append(sha256_hex(canonical_json_bytes(record)))
        if actual_hashes != expected_hashes:
            raise BridgeCurationError(
                f"staged Bridge output hashes differ from manifest: {relative}"
            )


def _materialization_roots(
    source_root: str | Path, output_dir: str | Path
) -> tuple[Path, Path, Path]:
    root = Path(source_root)
    destination = Path(output_dir)
    checks = (
        (root.is_dir(), f"source_root must be a real directory: {root}"),
        (not root.is_symlink(), f"source_root must be a real directory: {root}"),
        (
            not os.path.lexists(destination),
            f"destination already exists; refusing overwrite: {destination}",
        ),
        (
            destination.parent.is_dir(),
            f"destination parent must be a real directory: {destination.parent}",
        ),
        (
            not destination.parent.is_symlink(),
            f"destination parent must be a real directory: {destination.parent}",
        ),
        (
            not _is_under_raw(destination),
            f"refusing to write inside immutable raw evidence: {destination}",
        ),
    )
    failure = next((message for valid, message in checks if not valid), None)
    if failure is not None:
        raise BridgeCurationError(failure)
    root_resolved = root.resolve(strict=True)
    destination_resolved = destination.resolve(strict=False)
    separated = (
        destination_resolved != root_resolved and root_resolved not in destination_resolved.parents
    )
    if not separated:
        raise BridgeCurationError(f"destination cannot be inside source_root: {destination}")
    return root, destination, root_resolved


def _materialization_sources(sources: Iterable[str | Path], root_resolved: Path) -> list[Path]:
    source_paths = list(map(Path, sources))
    invalid = [
        source for source in source_paths if not all((source.is_file(), not source.is_symlink()))
    ]
    if invalid:
        raise BridgeCurationError(f"source must be a real JSONL file: {invalid[0]}")
    outside = [
        source
        for source in source_paths
        if not source.resolve(strict=True).is_relative_to(root_resolved)
    ]
    if outside:
        raise BridgeCurationError(f"source is outside source_root: {outside[0]}")
    return source_paths


def _write_materialized_tree(
    staged: Path,
    decisions: Sequence[CurationDecision],
    manifest_relative: Path,
) -> None:
    by_path: dict[Path, list[dict[str, Any]]] = {}
    for decision in decisions:
        if decision.output_record is None:
            continue
        relative = _safe_relative_path(
            decision.manifest["source_path"], label="manifest source_path"
        )
        by_path.setdefault(relative, []).append(decision.output_record)
    for relative, records in sorted(by_path.items(), key=lambda item: item[0].as_posix()):
        target = staged / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        _write_exclusive(
            target,
            b"".join(canonical_json_line(record) for record in records),
        )
    manifest_path = staged / manifest_relative
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    _write_exclusive(
        manifest_path,
        b"".join(canonical_json_line(decision.manifest) for decision in decisions),
    )


def _publish_materialized_tree(
    destination: Path,
    decisions: Sequence[CurationDecision],
    manifest_relative: Path,
) -> None:
    stage_root = Path(
        tempfile.mkdtemp(prefix=f".{destination.name}.staging-", dir=destination.parent)
    )
    staged = stage_root / "tree"
    try:
        staged.mkdir()
        _write_materialized_tree(staged, decisions, manifest_relative)
        _validate_materialized_tree(staged, decisions, manifest_relative)
        _rename_noreplace(staged, destination)
    finally:
        shutil.rmtree(stage_root, ignore_errors=True)


def materialize_paths(
    sources: Iterable[str | Path],
    *,
    source_root: str | Path,
    output_dir: str | Path,
    manifest_name: str = MANIFEST_NAME,
    require_raster: bool = True,
) -> list[CurationDecision]:
    """Publish one atomically validated, gate-compatible Bridge lane tree."""

    root, destination, root_resolved = _materialization_roots(source_root, output_dir)
    source_paths = list(map(Path, sources))
    if not source_paths:
        raise BridgeCurationError("at least one Bridge JSONL source is required")
    source_paths = _materialization_sources(source_paths, root_resolved)
    decisions = curate_paths(
        source_paths,
        source_root=root,
        require_raster=require_raster,
        require_routing_table=require_raster,
    )
    manifest_relative = _safe_relative_path(manifest_name, label="manifest_name")
    if manifest_relative.suffix != ".jsonl":
        raise BridgeCurationError("manifest_name must end in .jsonl")
    output_paths = {
        _safe_relative_path(decision.manifest["source_path"], label="manifest source_path")
        for decision in decisions
        if decision.output_record is not None
    }
    if manifest_relative in output_paths:
        raise BridgeCurationError(
            f"manifest path collides with a curated output: {manifest_relative}"
        )
    _publish_materialized_tree(destination, decisions, manifest_relative)
    return decisions


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
        help="JSON payload printed to stdout",
    )
    parser.add_argument(
        "--out-dir",
        help="publish one NEW gate-compatible lane output tree",
    )
    parser.add_argument(
        "--manifest-name",
        default=MANIFEST_NAME,
        help=f"manifest path inside --out-dir (default: {MANIFEST_NAME})",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        if args.out_dir is not None:
            if args.source_root is None:
                raise BridgeCurationError("--out-dir requires --source-root")
            decisions = materialize_paths(
                args.sources,
                source_root=args.source_root,
                output_dir=args.out_dir,
                manifest_name=args.manifest_name,
            )
        else:
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
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
