#!/usr/bin/env python3
"""Normalize one validated Bridge record into a machine-readable raster.

Every field is read from structured JSON; no free text is ever inspected.
The normalized raster keeps ``(neuron_id, t_us)`` events sorted in time, the
population and routing metadata, the third-factor eligibility channel, the
checked spike budget, and the spike-implemented gate head when the record
carries one.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path
from typing import Any

_PIPELINES = Path(__file__).resolve().parent
if str(_PIPELINES) not in sys.path:
    sys.path.insert(0, str(_PIPELINES))

from curate_bridge import (  # noqa: E402
    RASTER_ENERGY_PJ_PER_SPIKE,
    gate_snn_sidecar,
    raster_sidecar,
    raster_status,
    spike_energy,
)
from exact_json import (  # noqa: E402
    exact_fraction,
    exact_json_integer,
    json_number_from_fraction,
)

# Excerpt events stay on the contract's integer-microsecond grid.  A raster
# window may contain a schema-valid fractional microsecond, however, so the
# normalized duration preserves that precision for spike-budget reconstruction.
US_PER_MS = 1000
US_PER_S = 1_000_000


def _is_exact_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _json_integer(value: Any) -> int | None:
    """Return the integer represented by a schema-valid JSON number."""

    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return exact_json_integer(value)


def _normalized_gate_population(value: Any) -> Any:
    """Copy one gate population with schema-integer fields normalized."""

    if not isinstance(value, dict):
        return value
    normalized = dict(value)
    for key in ("neurons", "spikes"):
        if key in value:
            integer = _json_integer(value[key])
            if integer is not None:
                normalized[key] = integer
    return normalized


def _normalized_gate_snn(value: Any) -> dict[str, Any] | None:
    """Copy a validated gate head with schema-integer fields normalized."""

    if not isinstance(value, dict):
        return None
    normalized = dict(value)
    decision = value.get("decision")
    if isinstance(decision, str):
        normalized["decision"] = decision.strip().upper()
    populations = value.get("populations")
    if isinstance(populations, list):
        normalized["populations"] = [
            _normalized_gate_population(population) for population in populations
        ]
    return normalized


def _finite(value: Any) -> bool:
    if _is_exact_int(value):
        return True
    return isinstance(value, float) and math.isfinite(value)


def _window_us(raster: dict[str, Any]) -> Any:
    """Return the validated window in microseconds without rounding it."""

    window_s = raster.get("window_s")
    if _finite(window_s):
        window = exact_fraction(window_s)
        scale = US_PER_S
    else:
        window_ms = raster.get("window_ms")
        if not _finite(window_ms):
            return None
        window = exact_fraction(window_ms)
        scale = US_PER_MS
    if window is None:
        return None
    return json_number_from_fraction(window * scale)


def _normalized_event(item: Any) -> dict[str, Any] | None:
    """Normalize one well-shaped excerpt event into integer microseconds."""

    if not isinstance(item, dict):
        return None
    t_us = _json_integer(item.get("t_us"))
    neuron_id = _json_integer(item.get("neuron_id"))
    if t_us is None or neuron_id is None:
        return None
    event: dict[str, Any] = {
        "neuron_id": neuron_id,
        "t_us": t_us,
    }
    if "channel" in item:
        channel = item["channel"]
        if not isinstance(channel, str):
            return None
        event["channel"] = channel
    return event


def _events_us(raster: dict[str, Any]) -> list[dict[str, Any]]:
    """Return excerpt events as integer-microsecond (neuron_id, t_us) pairs."""

    excerpt = raster.get("excerpt")
    items = excerpt if isinstance(excerpt, list) else []
    events = filter(None, map(_normalized_event, items))
    return sorted(events, key=lambda event: (event["t_us"], event["neuron_id"]))


def _routing(raster: dict[str, Any]) -> dict[str, Any]:
    routing = raster.get("routing")
    if not isinstance(routing, dict):
        return {"source": None, "target": None, "table": [], "third_factor": None}
    table = routing.get("table")
    third_factor = routing.get("third_factor")
    return {
        "source": routing.get("source"),
        "target": routing.get("target"),
        "table": [entry for entry in table if isinstance(entry, dict)]
        if isinstance(table, list)
        else [],
        "third_factor": third_factor if isinstance(third_factor, dict) else None,
    }


def _mapping(value: Any) -> dict[str, Any]:
    """Return mapping-shaped JSON data, or an empty read-only fallback."""

    return value if isinstance(value, dict) else {}


def _nonblank_text(value: Any) -> str | None:
    """Return stripped non-blank text without coercing another JSON type."""

    text = value.strip() if isinstance(value, str) else ""
    return text or None


def _record_id(record: Any) -> str | None:
    """Return the first documented record identifier carrier."""

    root = _mapping(record)
    meta = _mapping(root.get("meta"))
    view = _mapping(root.get("language_view"))
    trajectory = _mapping(view.get("trajectory"))
    state = _mapping(trajectory.get("state"))
    candidates = (root.get("id"), meta.get("id"), state.get("episode_id"))
    for candidate in candidates:
        identifier = _nonblank_text(candidate)
        if identifier is not None:
            return identifier
    return None


def normalize_raster(record: Any, *, source: str | None = None) -> dict[str, Any] | None:
    """Return one machine-readable raster, or None when the record has none.

    ``None`` means the caller must treat the record as unloadable: either it is
    not a Bridge record, or its sidecar failed the shared spike arithmetic.
    """

    status = raster_status(record)
    if not status["raster_valid"] or status["routing_table_entries"] < 1:
        return None
    _location, raster = raster_sidecar(record)
    _gate_location, gate_snn = gate_snn_sidecar(record)
    neurons = _json_integer(raster.get("neurons"))
    spikes = _json_integer(raster.get("spikes"))
    normalized: dict[str, Any] = {
        "record_id": _record_id(record),
        "source": source,
        "window_us": _window_us(raster),
        "neurons": neurons,
        "mean_rate_hz": raster.get("mean_rate_hz"),
        "spikes": spikes,
        # Exact integer picojoules.  Converting the spike count to a float
        # first overflows to ``inf`` for an extreme but schema-valid raster,
        # and ``--jsonl`` would then emit the non-standard ``Infinity`` token
        # that the probe's own reader (reject_json_constant) refuses.
        "energy_pJ": (
            spike_energy(spikes, RASTER_ENERGY_PJ_PER_SPIKE)
            if spikes is not None
            else None
        ),
        "routing": _routing(raster),
        "gate_snn": _normalized_gate_snn(gate_snn),
        "events": _events_us(raster),
    }
    return normalized
