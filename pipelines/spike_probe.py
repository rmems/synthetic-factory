#!/usr/bin/env python3
"""Load spike rasters for SNN distillation without parsing prose.

A distillation probe needs execution-grounded spikes, not sentences such as
"366 vs 301, margin 0.097".  This loader reads a run tree (or explicit JSONL
files) and returns one normalized raster per Bridge record: ``(neuron_id,
t_us)`` events sorted in time, the population and routing metadata, the
third-factor eligibility channel, the checked spike budget, and the
spike-implemented gate head when the record carries one.  Every field is read
from structured JSON; no free text is ever inspected.

Records whose raster sidecar is missing or fails ``curate_bridge``'s spike
arithmetic are reported as problems instead of being silently emitted, so a
probe never trains on a raster it could not verify.  Missing, unreadable,
invalid-UTF-8, and unparsable inputs are also named problems, which makes
``--strict`` fail closed even when ``validate_run.py`` was not run first.

Usage::

    python3 pipelines/spike_probe.py [--jsonl] [--strict] <run_dir_or_jsonl...>
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Iterable, Iterator

_PIPELINES = Path(__file__).resolve().parent
if str(_PIPELINES) not in sys.path:
    sys.path.insert(0, str(_PIPELINES))

from curate_bridge import (  # noqa: E402
    RASTER_ENERGY_PJ_PER_SPIKE,
    REASON_INVALID_JSON,
    REASON_INVALID_UTF8,
    REASON_NOT_BRIDGE,
    gate_snn_sidecar,
    is_bridge_record,
    is_thalamic_record,
    raster_sidecar,
    raster_status,
)
from round_txn_raster import RASTER_FACTORY_SLUGS  # noqa: E402
from validate_run import reject_json_constant  # noqa: E402

# Rasters are declared in milliseconds; probes want integer microseconds so a
# 1 ms refractory window and a 1 ms Loihi barrier stay exactly representable.
US_PER_MS = 1000
REASON_INPUT_UNREADABLE = "BRIDGE_SOURCE_UNREADABLE"


def _is_exact_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _json_integer(value: Any) -> int | None:
    """Return the integer represented by a schema-valid JSON number."""

    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if not isinstance(value, float):
        return None
    if not math.isfinite(value):
        return None
    if not value.is_integer():
        return None
    return int(value)


def _finite(value: Any) -> bool:
    if _is_exact_int(value):
        return True
    return isinstance(value, float) and math.isfinite(value)


def _window_us(raster: dict[str, Any]) -> int | None:
    window_ms = raster.get("window_ms")
    if not _finite(window_ms):
        window_s = raster.get("window_s")
        if not _finite(window_s):
            return None
        window_ms = float(window_s) * 1000.0
    return int(round(float(window_ms) * US_PER_MS))


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
        # that this module's own reader (reject_json_constant) refuses.
        "energy_pJ": spikes * RASTER_ENERGY_PJ_PER_SPIKE if spikes is not None else None,
        "routing": _routing(raster),
        "gate_snn": gate_snn if isinstance(gate_snn, dict) else None,
        "events": _events_us(raster),
    }
    return normalized


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


def _expanded_jsonl_targets(targets: Iterable[str | Path]) -> Iterator[Path]:
    """Yield each explicit file or sorted JSONL member of a directory."""

    for target in targets:
        path = Path(target)
        yield from sorted(path.rglob("*.jsonl")) if path.is_dir() else (path,)


def _is_raster_factory_path(path: Path) -> bool:
    """Return whether a JSONL path is enclosed by a raster-gated factory."""

    supplied_parts = path.parts
    resolved_parts = path.resolve(strict=False).parts
    return any(part in RASTER_FACTORY_SLUGS for part in (*supplied_parts, *resolved_parts))


def _is_bridge_near_match(record: Any) -> bool:
    """Recognize an unmistakable Bridge declaration with malformed carriers."""

    if not isinstance(record, dict):
        return False
    view = record.get("language_view")
    return isinstance(view, dict) and "trajectory" in view and "spike_events" in record


def _is_supported_raster_record(record: Any) -> bool:
    return is_bridge_record(record) or is_thalamic_record(record)


def _malformed_raster_problem(
    where: str,
    record: Any,
    *,
    raster_gated_path: bool,
) -> dict[str, Any] | None:
    if not raster_gated_path and not _is_bridge_near_match(record):
        return None
    return _problem(
        where,
        "bridge_record",
        (REASON_NOT_BRIDGE,),
        record_id=_record_id(record),
    )


def jsonl_paths(targets: Iterable[str | Path]) -> list[Path]:
    """Expand run directories into sorted JSONL paths; keep explicit files.

    An input reached twice -- named twice, or named once directly and once
    through a containing directory -- is expanded once. Reading it twice
    emitted every raster twice and silently doubled the spike and energy
    totals, changing the weighting of a distillation dataset with no report
    that anything was wrong. Identity is the resolved path, so two names for
    one file (a symlink, ``./x`` vs ``x``) also count once.
    """

    unique: dict[Path, Path] = {}
    for path in _expanded_jsonl_targets(targets):
        unique.setdefault(path.resolve(strict=False), path)
    return list(unique.values())


def _read_jsonl(path: Path) -> tuple[str | None, str | None]:
    """Read UTF-8 without universal-newline translation."""

    try:
        payload = path.read_bytes()
    except OSError:
        return None, REASON_INPUT_UNREADABLE
    try:
        return payload.decode("utf-8"), None
    except UnicodeDecodeError:
        return None, REASON_INVALID_UTF8


def _parse_finite_json_float(text: str) -> float:
    """Reject a finite JSON token such as ``1e999`` that overflows to infinity."""

    value = float(text)
    if not math.isfinite(value):
        raise ValueError(f"non-finite JSON number {text}")
    return value


def _parse_record(line: str) -> tuple[Any, str | None]:
    """Parse one physical JSONL record using strict numeric hooks."""

    try:
        record = json.loads(
            line,
            parse_constant=reject_json_constant,
            parse_float=_parse_finite_json_float,
        )
    except (json.JSONDecodeError, ValueError):
        return None, REASON_INVALID_JSON
    return record, None


def _records_in_path(path: Path) -> Iterator[tuple[str, Any, str | None]]:
    """Yield parsed records and named input problems from one JSONL path."""

    text, read_problem = _read_jsonl(path)
    if read_problem is not None:
        yield f"{path}:0", None, read_problem
        return
    for line_number, line in enumerate(text.split("\n"), 1):
        if line.strip():
            record, parse_problem = _parse_record(line)
            yield f"{path}:{line_number}", record, parse_problem


def iter_records(paths: Iterable[Path]) -> Iterator[tuple[str, Any, str | None]]:
    """Yield ``(where, record, problem_code)`` for every JSONL input line."""

    for path in paths:
        yield from _records_in_path(path)


def _problem(
    where: str,
    scope: str,
    reason_codes: Iterable[str],
    *,
    record_id: str | None = None,
) -> dict[str, Any]:
    """Build the stable problem envelope shared by input and record failures."""

    return {
        "source": where,
        "record_id": record_id,
        "scope": scope,
        "reason_codes": list(reason_codes),
    }


def _probe_record(
    where: str,
    record: Any,
    input_problem: str | None,
    *,
    raster_gated_path: bool = False,
) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    """Classify one parsed input as a raster, a problem, or out of scope."""

    if input_problem is not None:
        return None, _problem(where, "input", (input_problem,))
    if not _is_supported_raster_record(record):
        return None, _malformed_raster_problem(
            where,
            record,
            raster_gated_path=raster_gated_path,
        )
    normalized = normalize_raster(record, source=where)
    if normalized is not None:
        return normalized, None
    status = raster_status(record)
    reason_codes = list(status["reason_codes"])
    if status["raster_valid"] and status["routing_table_entries"] < 1:
        reason_codes.append("BRIDGE_RASTER_ROUTING_MISSING")
    return None, _problem(
        where,
        "bridge_record",
        reason_codes,
        record_id=_record_id(record),
    )


def load_rasters(
    targets: Iterable[str | Path],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Return ``(rasters, problems)`` for every Bridge record under ``targets``."""

    rasters: list[dict[str, Any]] = []
    problems: list[dict[str, Any]] = []
    for path in jsonl_paths(targets):
        raster_gated_path = _is_raster_factory_path(path)
        for item in _records_in_path(path):
            normalized, problem = _probe_record(
                *item,
                raster_gated_path=raster_gated_path,
            )
            if normalized is not None:
                rasters.append(normalized)
            if problem is not None:
                problems.append(problem)
    return rasters, problems


def _exact_integer(value: Any) -> int:
    """Return an exact JSON integer, treating booleans and other types as zero."""

    return value if _is_exact_int(value) else 0


def summarize(rasters, problems, targets):
    """Aggregate loaded rasters into a machine-readable probe report."""

    spikes = sum(_exact_integer(raster["spikes"]) for raster in rasters)
    scope_counts = Counter(problem.get("scope") for problem in problems)
    return {
        "targets": [str(target) for target in targets],
        "bridge_records": len(rasters) + scope_counts["bridge_record"],
        "loaded": len(rasters),
        "unloadable": scope_counts["bridge_record"],
        "input_errors": scope_counts["input"],
        "events": sum(len(raster["events"]) for raster in rasters),
        "spikes": spikes,
        "energy_pJ": spikes * RASTER_ENERGY_PJ_PER_SPIKE,
        "routing_tables": sum(bool(raster["routing"]["table"]) for raster in rasters),
        "third_factor_routes": sum(bool(raster["routing"]["third_factor"]) for raster in rasters),
        "gate_snn_records": sum(bool(raster["gate_snn"]) for raster in rasters),
        "problems": problems[:20],
    }


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--jsonl",
        action="store_true",
        help="emit one normalized raster per line instead of a summary",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="exit 1 when any input is unreadable or any bridge record is unloadable",
    )
    parser.add_argument("targets", nargs="+", help="run directories or JSONL files")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    rasters, problems = load_rasters(args.targets)
    if args.jsonl:
        for raster in rasters:
            print(json.dumps(raster, ensure_ascii=True, sort_keys=True, allow_nan=False))
        for problem in problems:
            print(
                json.dumps(
                    {"unloadable": True, **problem},
                    ensure_ascii=True,
                    sort_keys=True,
                    allow_nan=False,
                ),
                file=sys.stderr,
            )
    else:
        print(
            json.dumps(
                summarize(rasters, problems, args.targets),
                indent=2,
                ensure_ascii=True,
                allow_nan=False,
            )
        )
    return 1 if problems and (args.strict or args.jsonl) else 0


if __name__ == "__main__":
    raise SystemExit(main())
