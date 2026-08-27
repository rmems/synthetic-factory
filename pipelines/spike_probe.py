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
import sys
from pathlib import Path
from typing import Any, Iterable, Iterator

_PIPELINES = Path(__file__).resolve().parent
if str(_PIPELINES) not in sys.path:
    sys.path.insert(0, str(_PIPELINES))

from curate_bridge import (  # noqa: E402
    RASTER_ENERGY_PJ_PER_SPIKE,
    REASON_INVALID_JSON,
    REASON_INVALID_UTF8,
    gate_snn_sidecar,
    is_bridge_record,
    is_thalamic_record,
    raster_sidecar,
    raster_status,
)
from validate_run import reject_json_constant  # noqa: E402

# Rasters are declared in milliseconds; probes want integer microseconds so a
# 1 ms refractory window and a 1 ms Loihi barrier stay exactly representable.
US_PER_MS = 1000
REASON_INPUT_UNREADABLE = "BRIDGE_SOURCE_UNREADABLE"


def _finite(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _window_us(raster: dict[str, Any]) -> int | None:
    window_ms = raster.get("window_ms")
    if not _finite(window_ms):
        window_s = raster.get("window_s")
        if not _finite(window_s):
            return None
        window_ms = float(window_s) * 1000.0
    return int(round(float(window_ms) * US_PER_MS))


def _events_us(raster: dict[str, Any]) -> list[dict[str, int]]:
    """Return excerpt events as integer-microsecond (neuron_id, t_us) pairs."""

    excerpt = raster.get("excerpt")
    if not isinstance(excerpt, list):
        return []
    events = []
    for item in excerpt:
        if not isinstance(item, dict):
            continue
        t_ms = item.get("t_ms")
        neuron_id = item.get("neuron_id")
        if not _finite(t_ms) or not isinstance(neuron_id, int) or isinstance(neuron_id, bool):
            continue
        event = {"neuron_id": neuron_id, "t_us": int(round(float(t_ms) * US_PER_MS))}
        channel = item.get("channel")
        if isinstance(channel, str) and channel:
            event["channel"] = channel
        events.append(event)
    events.sort(key=lambda event: (event["t_us"], event["neuron_id"]))
    return events


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
    spikes = raster.get("spikes")
    normalized: dict[str, Any] = {
        "record_id": _record_id(record),
        "source": source,
        "window_us": _window_us(raster),
        "neurons": raster.get("neurons"),
        "mean_rate_hz": raster.get("mean_rate_hz"),
        "spikes": spikes,
        "energy_pJ": (
            float(spikes) * RASTER_ENERGY_PJ_PER_SPIKE
            if isinstance(spikes, int) and not isinstance(spikes, bool)
            else None
        ),
        "routing": _routing(raster),
        "gate_snn": gate_snn if isinstance(gate_snn, dict) else None,
        "events": _events_us(raster),
    }
    return normalized


def _record_id(record: Any) -> str | None:
    if not isinstance(record, dict):
        return None
    value = record.get("id")
    if isinstance(value, str) and value.strip():
        return value.strip()
    meta = record.get("meta")
    if isinstance(meta, dict):
        value = meta.get("id")
        if isinstance(value, str) and value.strip():
            return value.strip()
    view = record.get("language_view")
    trajectory = view.get("trajectory") if isinstance(view, dict) else None
    state = trajectory.get("state") if isinstance(trajectory, dict) else None
    if isinstance(state, dict):
        value = state.get("episode_id")
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def jsonl_paths(targets: Iterable[str | Path]) -> list[Path]:
    """Expand run directories into sorted JSONL paths; keep explicit files."""

    paths: list[Path] = []
    for target in targets:
        path = Path(target)
        if path.is_dir():
            paths.extend(sorted(path.rglob("*.jsonl")))
        else:
            paths.append(path)
    return paths


def iter_records(paths: Iterable[Path]) -> Iterator[tuple[str, Any, str | None]]:
    """Yield ``(where, record, problem_code)`` for every JSONL input line."""

    for path in paths:
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            yield f"{path}:0", None, REASON_INVALID_UTF8
            continue
        except OSError:
            yield f"{path}:0", None, REASON_INPUT_UNREADABLE
            continue
        for line_number, line in enumerate(text.splitlines(), 1):
            if not line.strip():
                continue
            where = f"{path}:{line_number}"
            try:
                yield where, json.loads(line, parse_constant=reject_json_constant), None
            except (json.JSONDecodeError, ValueError):
                yield where, None, REASON_INVALID_JSON


def load_rasters(
    targets: Iterable[str | Path],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Return ``(rasters, problems)`` for every Bridge record under ``targets``."""

    rasters: list[dict[str, Any]] = []
    problems: list[dict[str, Any]] = []
    for where, record, input_problem in iter_records(jsonl_paths(targets)):
        if input_problem is not None:
            problems.append(
                {
                    "source": where,
                    "record_id": None,
                    "scope": "input",
                    "reason_codes": [input_problem],
                }
            )
            continue
        if not is_bridge_record(record) and not is_thalamic_record(record):
            continue
        normalized = normalize_raster(record, source=where)
        if normalized is None:
            status = raster_status(record)
            reason_codes = list(status["reason_codes"])
            if status["raster_valid"] and status["routing_table_entries"] < 1:
                reason_codes.append("BRIDGE_RASTER_ROUTING_MISSING")
            problems.append(
                {
                    "source": where,
                    "record_id": _record_id(record),
                    "scope": "bridge_record",
                    "reason_codes": reason_codes,
                }
            )
            continue
        rasters.append(normalized)
    return rasters, problems


def summarize(rasters, problems, targets):
    """Aggregate loaded rasters into a machine-readable probe report."""

    spikes = sum(
        raster["spikes"]
        for raster in rasters
        if isinstance(raster["spikes"], int) and not isinstance(raster["spikes"], bool)
    )
    bridge_problems = [
        problem for problem in problems if problem.get("scope") == "bridge_record"
    ]
    input_problems = [problem for problem in problems if problem.get("scope") == "input"]
    return {
        "targets": [str(target) for target in targets],
        "bridge_records": len(rasters) + len(bridge_problems),
        "loaded": len(rasters),
        "unloadable": len(bridge_problems),
        "input_errors": len(input_problems),
        "events": sum(len(raster["events"]) for raster in rasters),
        "spikes": spikes,
        "energy_pJ": spikes * RASTER_ENERGY_PJ_PER_SPIKE,
        "routing_tables": sum(
            1 for raster in rasters if raster["routing"]["table"]
        ),
        "third_factor_routes": sum(
            1 for raster in rasters if raster["routing"]["third_factor"]
        ),
        "gate_snn_records": sum(1 for raster in rasters if raster["gate_snn"]),
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
            print(json.dumps(raster, ensure_ascii=False, sort_keys=True))
        for problem in problems:
            print(
                json.dumps(
                    {"unloadable": True, **problem},
                    ensure_ascii=False,
                    sort_keys=True,
                ),
                file=sys.stderr,
            )
    else:
        print(
            json.dumps(
                summarize(rasters, problems, args.targets),
                indent=2,
                ensure_ascii=False,
            )
        )
    return 1 if problems and (args.strict or args.jsonl) else 0


if __name__ == "__main__":
    raise SystemExit(main())
