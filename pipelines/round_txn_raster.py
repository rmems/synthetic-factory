#!/usr/bin/env python3
"""Raster and gate-SNN envelope checks for staged round transactions.

This module owns the neuromorphic publication contract and the physical-LF
JSONL reader it shares with the agentic envelope. ``round_txn`` re-exports
the established names while keeping its transaction orchestration focused.
"""

from __future__ import annotations

import json
from pathlib import Path

from check_records import read_utf8_jsonl
from curate_bridge import is_bridge_record, is_thalamic_record, raster_status
from validate_run import reject_json_constant

# Every lane that emits neuromorphic records carries the raster / gate-as-SNN
# publication contract. NELB emits paired Bridge records; TTF and the
# Ouroboros swarm emit top-level Thalamic trajectories against
# schemas/thalamic-trajectory-v2.schema.json. ``spike_probe.py`` already
# refuses those records without a raster, so leaving the swarm out would let
# a round publish as training-ready that no distillation run could load.
BRIDGE_FACTORY_SLUG = "neuromorphic-event-language-bridge"
THALAMIC_FACTORY_SLUG = "thalamic-trajectory-factory"
OUROBOROS_FACTORY_SLUG = "multi-agent-ouroboros-swarm"
RASTER_FACTORY_SLUGS = frozenset(
    {BRIDGE_FACTORY_SLUG, THALAMIC_FACTORY_SLUG, OUROBOROS_FACTORY_SLUG}
)


def _jsonl_records(batch: Path):
    """Return physical-LF-framed JSON records plus fail-closed parse errors."""

    try:
        text = read_utf8_jsonl(batch)
    except (OSError, UnicodeError) as exc:
        return [], [f"{batch.name}: cannot read staged batch as UTF-8: {exc}"]
    records = []
    errors = []
    for lineno, line in enumerate(text.split("\n"), 1):
        if not line.strip():
            continue
        try:
            record = json.loads(line, parse_constant=reject_json_constant)
        except (json.JSONDecodeError, ValueError) as exc:
            errors.append(f"{batch.name}:{lineno}: JSON parse error: {exc}")
            continue
        records.append((lineno, record))
    return records, errors


def _distillation_kind_error(record, factory_slug):
    if factory_slug == BRIDGE_FACTORY_SLUG and not is_bridge_record(record):
        return (
            f"{BRIDGE_FACTORY_SLUG} requires only paired Bridge records "
            "with an object language_view.trajectory"
        )
    if factory_slug != BRIDGE_FACTORY_SLUG and not is_thalamic_record(record):
        return f"{factory_slug} requires Thalamic trajectory records with a raster sidecar"
    return None


def _raster_contract_errors(status, where, label):
    if not status["raster_present"]:
        return [
            f"{where}: {label} records must carry a 20-50 ms raster excerpt "
            "sidecar (raster or meta.raster)"
        ]
    if status["reason_codes"]:
        return [
            f"{where}: raster or spike-budget contract violated "
            f"({', '.join(status['reason_codes'])})"
        ]
    if status["routing_table_entries"] < 1:
        return [
            f"{where}: raster.routing.table must carry at least one per-population routing entry"
        ]
    return []


def _validate_distillation_record(batch, lineno, record, factory_slug):
    where = f"{batch.name}:{lineno}"
    kind_error = _distillation_kind_error(record, factory_slug)
    if kind_error:
        return [f"{where}: {kind_error}"], False, False
    status = raster_status(record)
    label = "bridge" if factory_slug == BRIDGE_FACTORY_SLUG else "thalamic"
    return (
        _raster_contract_errors(status, where, label),
        True,
        bool(status["gate_snn_present"]),
    )


def validate_bridge_envelope(batch: Path, factory_dir: Path):
    """Return the staged lane's raster and gate-SNN contract errors.

    Only newly staged batches are gated. Historical committed markers remain
    readable, while ``training_audit.py`` reports their corpus-level coverage.
    """

    factory_slug = factory_dir.name
    if factory_slug not in RASTER_FACTORY_SLUGS:
        return []
    records, errors = _jsonl_records(batch)
    raster_records = 0
    gate_snn_records = 0
    for lineno, record in records:
        row_errors, is_raster_record, has_gate = _validate_distillation_record(
            batch, lineno, record, factory_slug
        )
        errors.extend(row_errors)
        raster_records += int(is_raster_record)
        gate_snn_records += int(has_gate)
    if raster_records and not gate_snn_records:
        errors.append(
            f"{batch.name}: a {factory_slug} round must contain at least one "
            "spike-implemented gate (gate_snn neuron/threshold spec)"
        )
    return errors


def enforce_bridge_envelope(batch: Path, factory_dir: Path, exception_type):
    """Raise ``exception_type`` when the staged raster envelope is invalid."""

    errors = validate_bridge_envelope(batch, factory_dir)
    if errors:
        raise exception_type(
            "staged batch violates the bridge raster envelope:\n"
            + "\n".join(f"ERROR: {error}" for error in errors)
        )
