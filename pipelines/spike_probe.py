#!/usr/bin/env python3
"""Load spike rasters for SNN distillation without parsing prose.

A distillation probe needs execution-grounded spikes, not sentences such as
"366 vs 301, margin 0.097".  This loader reads a run tree (or explicit JSONL
files) and returns one normalized raster per Bridge record; the raster shape
itself is produced by :mod:`spike_probe_normalize`, and the fail-closed JSONL
reading lives in :mod:`spike_probe_source`.

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
from collections import Counter
from pathlib import Path
from typing import Any, Iterable, Optional

_PIPELINES = Path(__file__).resolve().parent
if str(_PIPELINES) not in sys.path:
    sys.path.insert(0, str(_PIPELINES))

from curate_bridge import (  # noqa: E402
    RASTER_ENERGY_PJ_PER_SPIKE,
    REASON_NOT_BRIDGE,
    is_bridge_record,
    is_thalamic_record,
    raster_status,
)
from exact_json import dumps_exact_json  # noqa: E402
from spike_probe_normalize import (  # noqa: E402
    _is_exact_int,
    _normalized_event as _normalized_event,
    _record_id,
    normalize_raster,
)
from spike_probe_source import (  # noqa: E402
    _raster_factory_kind,
    _records_in_path,
    iter_records as iter_records,
    jsonl_paths,
)
from validate_run import reject_json_constant as reject_json_constant  # noqa: E402

__all__ = ["_normalized_event", "iter_records", "reject_json_constant"]


def _is_bridge_near_match(record: Any) -> bool:
    """Recognize an unmistakable Bridge declaration with malformed carriers."""

    if not isinstance(record, dict):
        return False
    return "language_view" in record and "spike_events" in record


def _is_supported_raster_record(record: Any) -> bool:
    return is_bridge_record(record) or is_thalamic_record(record)


def _raster_record_kind(record: Any) -> Optional[str]:
    """Return the supported distillation lane kind for one record."""

    if is_bridge_record(record):
        return "bridge"
    if is_thalamic_record(record):
        return "thalamic"
    if _is_bridge_near_match(record):
        return "bridge"
    return None


def _malformed_raster_problem(
    where: str,
    record: Any,
    *,
    raster_path_kind: str | None,
) -> dict[str, Any] | None:
    if raster_path_kind is None and not _is_bridge_near_match(record):
        return None
    problem = _problem(
        where,
        "distillation_record",
        (REASON_NOT_BRIDGE,),
        record=record,
    )
    if "record_kind" not in problem and raster_path_kind is not None:
        problem["record_kind"] = raster_path_kind
    return problem


def _problem(
    where: str,
    scope: str,
    reason_codes: Iterable[str],
    *,
    record: Any = None,
) -> dict[str, Any]:
    """Build the stable problem envelope shared by input and record failures."""

    problem = {
        "source": where,
        "record_id": _record_id(record),
        "scope": scope,
        "reason_codes": list(reason_codes),
    }
    classified_kind = _raster_record_kind(record)
    if classified_kind is not None:
        problem["record_kind"] = classified_kind
    return problem


def _probe_record(
    where: str,
    record: Any,
    input_problem: Optional[str],
    *,
    raster_path_kind: str | None = None,
) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    """Classify one parsed input as a raster, a problem, or out of scope."""

    if input_problem is not None:
        return None, _problem(where, "input", (input_problem,))
    if not _is_supported_raster_record(record):
        return None, _malformed_raster_problem(
            where,
            record,
            raster_path_kind=raster_path_kind,
        )
    record_kind = _raster_record_kind(record)
    normalized = normalize_raster(record, source=where)
    if normalized is not None:
        normalized["record_kind"] = record_kind
        return normalized, None
    status = raster_status(record)
    reason_codes = list(status["reason_codes"])
    if status["raster_valid"] and status["routing_table_entries"] < 1:
        reason_codes.append("BRIDGE_RASTER_ROUTING_MISSING")
    return None, _problem(
        where,
        "distillation_record",
        reason_codes,
        record=record,
    )


def load_rasters(
    targets: Iterable[str | Path],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Return ``(rasters, problems)`` for every Bridge record under ``targets``."""

    rasters: list[dict[str, Any]] = []
    problems: list[dict[str, Any]] = []
    for path in jsonl_paths(targets):
        raster_path_kind = _raster_factory_kind(path)
        for item in _records_in_path(path):
            normalized, problem = _probe_record(
                *item,
                raster_path_kind=raster_path_kind,
            )
            if normalized is not None:
                rasters.append(normalized)
            if problem is not None:
                problems.append(problem)
    return rasters, problems


def _exact_integer(value: Any) -> int:
    """Return an exact JSON integer, treating booleans and other types as zero."""

    return value if _is_exact_int(value) else 0


def _record_kind_counts(rasters, problems):
    """Return loaded and unloadable counts grouped by distillation kind."""

    loaded = Counter(raster.get("record_kind", "bridge") for raster in rasters)
    unloadable = Counter(
        problem.get("record_kind")
        for problem in problems
        if problem.get("scope") == "distillation_record"
    )
    return loaded, unloadable


def summarize(rasters, problems, targets):
    """Aggregate loaded rasters into a machine-readable probe report."""

    spikes = sum(_exact_integer(raster["spikes"]) for raster in rasters)
    scope_counts = Counter(problem.get("scope") for problem in problems)
    loaded_kinds, unloadable_kinds = _record_kind_counts(rasters, problems)
    distillation_records = len(rasters) + scope_counts["distillation_record"]
    return {
        "targets": [str(target) for target in targets],
        "distillation_records": distillation_records,
        "bridge_records": loaded_kinds["bridge"] + unloadable_kinds["bridge"],
        "thalamic_records": loaded_kinds["thalamic"] + unloadable_kinds["thalamic"],
        "loaded": len(rasters),
        "unloadable": scope_counts["distillation_record"],
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
            print(dumps_exact_json(raster, ensure_ascii=True, sort_keys=True))
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
    sys.exit(main())
