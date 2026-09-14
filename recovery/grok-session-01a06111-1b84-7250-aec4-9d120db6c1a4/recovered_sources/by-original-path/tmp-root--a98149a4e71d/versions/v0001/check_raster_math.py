#!/usr/bin/env python3
"""Stdlib raster / gate_snn arithmetic checker.

Loads /tmp/batch-r12.jsonl and any /tmp/{nelb-r13,actf-r10,maos-r14,ffpc-r11}/*.jsonl
that exist. Does not read or write outputs/raw/.
"""

from __future__ import annotations

import json
import math
import sys
from collections import defaultdict
from pathlib import Path

BATCH_PATH = Path("/tmp/batch-r12.jsonl")
EXTRA_DIRS = (
    Path("/tmp/nelb-r13"),
    Path("/tmp/actf-r10"),
    Path("/tmp/maos-r14"),
    Path("/tmp/ffpc-r11"),
)
REPORT_PATH = Path("/tmp/raster-math-report.md")

WINDOW_TOL = 1e-9
ENERGY_PJ_TOL = 1e-6
ENERGY_UJ_TOL = 1e-9
TAU_TOL = 1e-9
PJ_PER_SPIKE = 23
UJ_PER_SPIKE = 23e-6
SPIKE_TOL = 1
REFRACTORY_US = 1000

RASTER_CHECKS = (
    "window",
    "spikes",
    "energy_pJ",
    "energy_uJ",
    "excerpt",
    "tau",
)
GATE_CHECKS = ("decision", "pop_budget")


def is_bool(value):
    return isinstance(value, bool)


def as_number(value):
    if is_bool(value) or not isinstance(value, (int, float)):
        return None
    number = float(value)
    return number if math.isfinite(number) else None


def as_int(value):
    if is_bool(value):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float) and math.isfinite(value) and value == int(value):
        return int(value)
    return None


def within(actual, expected, tol):
    actual_n = as_number(actual)
    expected_n = as_number(expected)
    if actual_n is None or expected_n is None:
        return False
    return abs(actual_n - expected_n) <= tol


def mapping(value):
    return value if isinstance(value, dict) else None


def text(value):
    if not isinstance(value, str):
        return None
    stripped = value.strip()
    return stripped if stripped else None


def record_id(record, line_no):
    ident = record.get("id") if isinstance(record, dict) else None
    if isinstance(ident, str) and ident.strip():
        return ident.strip()
    return f"line-{line_no}"


def discover_inputs():
    files = []
    missing_required = []
    if BATCH_PATH.is_file():
        files.append(BATCH_PATH)
    else:
        missing_required.append(str(BATCH_PATH))
    extra_dirs = []
    for directory in EXTRA_DIRS:
        extra_dirs.append((str(directory), directory.is_dir()))
        if directory.is_dir():
            files.extend(sorted(path for path in directory.glob("*.jsonl") if path.is_file()))
    return files, missing_required, extra_dirs


def iter_jsonl(path):
    with path.open(encoding="utf-8") as handle:
        for line_no, raw in enumerate(handle, 1):
            if not raw.strip():
                continue
            try:
                yield line_no, json.loads(raw), None
            except json.JSONDecodeError as exc:
                yield line_no, None, f"JSON parse error: {exc}"


def nested_get(container, *keys):
    current = container
    for key in keys:
        current = mapping(current)
        if current is None or key not in current:
            return False, None
        current = current[key]
    return True, current


def declared_sidecars(record):
    rasters = []
    gates = []
    if not isinstance(record, dict):
        return rasters, gates
    meta = mapping(record.get("meta"))
    view = mapping(record.get("language_view"))
    trajectory = mapping(view.get("trajectory")) if view else None
    lv_safety = mapping(trajectory.get("safety_decision")) if trajectory else None
    for location, container in (
        ("raster", record),
        ("meta.raster", meta),
    ):
        if mapping(container) is not None and "raster" in container:
            rasters.append((location, container.get("raster")))
    for location, container in (
        ("gate_snn", record),
        ("meta.gate_snn", meta),
        ("language_view.trajectory.gate_snn", trajectory),
        ("language_view.trajectory.safety_decision.gate_snn", lv_safety),
    ):
        if mapping(container) is not None and "gate_snn" in container:
            gates.append((location, container.get("gate_snn")))
    return rasters, gates


def expected_decision(record):
    if not isinstance(record, dict):
        return None
    safety = mapping(record.get("safety_decision"))
    if safety is not None:
        decision = text(safety.get("decision"))
        if decision:
            return decision
    declared, view_safety = nested_get(
        record, "language_view", "trajectory", "safety_decision"
    )
    if not declared:
        return None
    if isinstance(view_safety, str):
        return text(view_safety)
    safety = mapping(view_safety)
    if safety is None:
        return None
    return text(safety.get("decision"))


def alias_pair(container, primary_key, alias_key, scale, tol):
    """Return (ok, primary, detail). Missing both fails. One present derives."""

    if not isinstance(container, dict):
        return False, None, f"{primary_key}/{alias_key} carrier is not an object"
    has_primary = primary_key in container
    has_alias = alias_key in container
    primary = as_number(container.get(primary_key)) if has_primary else None
    alias = as_number(container.get(alias_key)) if has_alias else None
    if has_primary and primary is None:
        return False, None, f"{primary_key} is not a finite number"
    if has_alias and alias is None:
        return False, None, f"{alias_key} is not a finite number"
    if has_primary and has_alias:
        expected_primary = alias * scale
        if abs(primary - expected_primary) > tol:
            return (
                False,
                primary,
                f"{primary_key}={primary} vs {alias_key}/{1/scale:g}={expected_primary} "
                f"delta={abs(primary - expected_primary)}",
            )
        return True, primary, f"{primary_key}={primary} {alias_key}={alias}"
    if has_primary:
        return True, primary, f"{primary_key}={primary} ({alias_key} derived)"
    if has_alias:
        derived = alias * scale
        return True, derived, f"{alias_key}={alias} -> {primary_key}={derived}"
    return False, None, f"missing {primary_key} and {alias_key}"


def check_window(raster):
    return alias_pair(raster, "window_s", "window_ms", 0.001, WINDOW_TOL)


def check_spikes(raster, window_s):
    neurons = as_int(raster.get("neurons")) if isinstance(raster, dict) else None
    rate = as_number(raster.get("mean_rate_hz")) if isinstance(raster, dict) else None
    if rate is None and isinstance(raster, dict):
        rate = as_number(raster.get("rate_hz"))
    spikes = as_int(raster.get("spikes")) if isinstance(raster, dict) else None
    if neurons is None or neurons <= 0:
        return False, "neurons must be a positive integer"
    if rate is None or rate <= 0:
        return False, "mean_rate_hz must be a positive finite number"
    if spikes is None or spikes < 0:
        return False, "spikes must be a non-negative integer"
    if window_s is None:
        return False, "window_s unavailable for spike budget"
    expected = round(neurons * rate * window_s)
    delta = abs(spikes - expected)
    detail = f"spikes={spikes} expected={expected} delta={delta}"
    return delta <= SPIKE_TOL, detail


def check_energy(raster, key, per_spike, tol):
    if not isinstance(raster, dict) or key not in raster:
        return None, f"{key} absent"
    spikes = as_int(raster.get("spikes"))
    if spikes is None or spikes < 0:
        return False, f"{key} declared but spikes is not a non-negative integer"
    expected = spikes * per_spike
    actual = raster.get(key)
    ok = within(actual, expected, tol)
    return ok, f"{key}={actual} expected={expected} delta={abs(as_number(actual) - expected) if as_number(actual) is not None else 'n/a'}"


def check_excerpt(raster, window_s):
    if not isinstance(raster, dict):
        return False, "raster is not an object"
    excerpt = raster.get("excerpt")
    if not isinstance(excerpt, list) or not excerpt:
        return False, "excerpt must be a non-empty array"
    neurons = as_int(raster.get("neurons"))
    window_ms = as_number(raster.get("window_ms"))
    if window_ms is None and window_s is not None:
        window_ms = window_s * 1000.0
    if window_ms is None:
        return False, "window unavailable for excerpt bounds"
    max_t = window_ms * 1000.0
    times = []
    by_neuron = defaultdict(list)
    problems = []
    prev_t = None
    for index, item in enumerate(excerpt):
        if not isinstance(item, dict):
            problems.append(f"[{index}] not an object")
            continue
        t_us = item.get("t_us")
        neuron_id = item.get("neuron_id")
        t_int = as_int(t_us)
        n_int = as_int(neuron_id)
        if t_int is None:
            problems.append(f"[{index}] t_us={t_us!r} is not an integer")
            continue
        if t_int < 0 or t_int > max_t:
            problems.append(f"[{index}] t_us={t_int} outside [0, {max_t:g}]")
        if prev_t is not None and t_int < prev_t:
            problems.append(f"[{index}] t_us={t_int} not sorted (prev={prev_t})")
        prev_t = t_int
        times.append(t_int)
        if n_int is None:
            problems.append(f"[{index}] neuron_id={neuron_id!r} is not an integer")
            continue
        if neurons is not None and not (0 <= n_int < neurons):
            problems.append(f"[{index}] neuron_id={n_int} outside [0, {neurons})")
        by_neuron[n_int].append(t_int)
    min_gap = None
    for neuron_id, neuron_times in by_neuron.items():
        ordered = sorted(neuron_times)
        for left, right in zip(ordered, ordered[1:]):
            gap = right - left
            min_gap = gap if min_gap is None else min(min_gap, gap)
            if gap < REFRACTORY_US:
                problems.append(
                    f"neuron {neuron_id} gap {gap}us < {REFRACTORY_US} ({left}->{right})"
                )
    if problems:
        return False, "; ".join(problems[:8]) + (f" (+{len(problems) - 8} more)" if len(problems) > 8 else "")
    bound_detail = f"n={len(excerpt)} t_us=[{min(times)}, {max(times)}] bound={max_t:g}"
    if min_gap is None:
        return True, bound_detail + " same-neuron=n/a"
    return True, bound_detail + f" min_same_neuron_gap_us={min_gap}"


def check_tau(raster):
    routing = mapping(raster.get("routing")) if isinstance(raster, dict) else None
    if routing is None:
        return False, "routing missing"
    if "third_factor" not in routing:
        return False, "routing.third_factor missing"
    third = routing.get("third_factor")
    if not isinstance(third, dict):
        return False, "third_factor is not an object"
    ok, primary, detail = alias_pair(third, "tau_e_s", "tau_e_ms", 0.001, TAU_TOL)
    if not ok:
        return False, detail
    if primary is None or primary <= 0:
        return False, f"tau_e_s must be positive ({detail})"
    return True, detail


def check_raster(raster):
    results = {}
    details = {}
    if not isinstance(raster, dict):
        for name in RASTER_CHECKS:
            results[name] = False
            details[name] = "raster is not an object"
        return results, details, None
    ok, window_s, detail = check_window(raster)
    results["window"] = ok
    details["window"] = detail
    spikes_ok, spikes_detail = check_spikes(raster, window_s if ok else None)
    results["spikes"] = spikes_ok
    details["spikes"] = spikes_detail
    for key, per_spike, tol, name in (
        ("energy_pJ", PJ_PER_SPIKE, ENERGY_PJ_TOL, "energy_pJ"),
        ("energy_uJ", UJ_PER_SPIKE, ENERGY_UJ_TOL, "energy_uJ"),
    ):
        energy_ok, energy_detail = check_energy(raster, key, per_spike, tol)
        results[name] = energy_ok
        details[name] = energy_detail
    excerpt_ok, excerpt_detail = check_excerpt(raster, window_s if ok else None)
    results["excerpt"] = excerpt_ok
    details["excerpt"] = excerpt_detail
    tau_ok, tau_detail = check_tau(raster)
    results["tau"] = tau_ok
    details["tau"] = tau_detail
    return results, details, window_s


def gate_window_s(spec):
    ok, window_s, detail = alias_pair(
        spec, "decision_window_s", "decision_window_ms", 0.001, WINDOW_TOL
    )
    return ok, window_s, detail


def population_rate(population):
    if "mean_rate_hz" in population:
        return as_number(population.get("mean_rate_hz"))
    if "rate_hz" in population:
        return as_number(population.get("rate_hz"))
    return None


def check_population_budgets(spec):
    if not isinstance(spec, dict):
        return False, "gate_snn is not an object"
    window_ok, window_s, window_detail = gate_window_s(spec)
    populations = spec.get("populations")
    if not isinstance(populations, list) or not populations:
        return False, "populations must be a non-empty array"
    checked = 0
    problems = []
    for index, population in enumerate(populations):
        if not isinstance(population, dict):
            problems.append(f"[{index}] not an object")
            continue
        has_rate = "mean_rate_hz" in population or "rate_hz" in population
        has_spikes = "spikes" in population
        if not has_rate and not has_spikes:
            continue
        if has_rate != has_spikes:
            problems.append(
                f"[{index}] {population.get('name', '?')} has "
                f"{'rate' if has_rate else 'spikes'} without "
                f"{'spikes' if has_rate else 'rate'}"
            )
            continue
        if not window_ok or window_s is None:
            problems.append(f"[{index}] decision window invalid ({window_detail})")
            continue
        neurons = as_int(population.get("neurons"))
        rate = population_rate(population)
        spikes = as_int(population.get("spikes"))
        name = population.get("name", f"pop-{index}")
        if neurons is None or neurons <= 0:
            problems.append(f"[{index}] {name} neurons invalid")
            continue
        if rate is None or rate <= 0:
            problems.append(f"[{index}] {name} rate invalid")
            continue
        if spikes is None or spikes < 0:
            problems.append(f"[{index}] {name} spikes invalid")
            continue
        expected = round(neurons * rate * window_s)
        delta = abs(spikes - expected)
        checked += 1
        if delta > SPIKE_TOL:
            problems.append(
                f"[{index}] {name} spikes={spikes} expected={expected} delta={delta}"
            )
    if problems:
        return False, "; ".join(problems[:8])
    return True, f"checked={checked} skipped_no_rate_spikes={len(populations) - checked}"


def check_gate(spec, expected):
    results = {}
    details = {}
    if not isinstance(spec, dict):
        results["decision"] = False
        details["decision"] = "gate_snn is not an object"
        results["pop_budget"] = False
        details["pop_budget"] = "gate_snn is not an object"
        return results, details
    decision = text(spec.get("decision"))
    if expected is None:
        results["decision"] = False
        details["decision"] = f"gate_snn.decision={decision!r} but no safety_decision.decision"
    elif decision is None:
        results["decision"] = False
        details["decision"] = "gate_snn.decision missing"
    elif decision.upper() != expected.upper():
        results["decision"] = False
        details["decision"] = f"gate={decision} safety={expected}"
    else:
        results["decision"] = True
        details["decision"] = f"{decision}"
    pop_ok, pop_detail = check_population_budgets(spec)
    results["pop_budget"] = pop_ok
    details["pop_budget"] = pop_detail
    return results, details


def status_cell(value):
    if value is True:
        return "PASS"
    if value is False:
        return "FAIL"
    return "n/a"


def merge_status(current, incoming):
    if incoming is False or current is False:
        return False
    if incoming is True:
        return True if current is None else current
    return current


def check_record(record):
    rasters, gates = declared_sidecars(record)
    expected = expected_decision(record)
    raster_results = {name: None for name in RASTER_CHECKS}
    raster_details = {name: "no raster" for name in RASTER_CHECKS}
    raster_locations = []
    for location, raster in rasters:
        raster_locations.append(location)
        results, details, _ = check_raster(raster)
        for name in RASTER_CHECKS:
            raster_results[name] = merge_status(raster_results[name], results[name])
            if results[name] is False:
                raster_details[name] = f"{location}: {details[name]}"
            elif raster_results[name] is True and raster_details[name] in ("no raster",):
                raster_details[name] = f"{location}: {details[name]}"
            elif results[name] is True:
                raster_details[name] = f"{location}: {details[name]}"
    gate_results = {name: None for name in GATE_CHECKS}
    gate_details = {name: "no gate_snn" for name in GATE_CHECKS}
    gate_locations = []
    for location, spec in gates:
        gate_locations.append(location)
        results, details = check_gate(spec, expected)
        for name in GATE_CHECKS:
            gate_results[name] = merge_status(gate_results[name], results[name])
            if results[name] is False:
                gate_details[name] = f"{location}: {details[name]}"
            elif gate_results[name] is True:
                gate_details[name] = f"{location}: {details[name]}"
    return {
        "raster_locations": raster_locations,
        "gate_locations": gate_locations,
        "raster": raster_results,
        "raster_details": raster_details,
        "gate": gate_results,
        "gate_details": gate_details,
        "expected_decision": expected,
    }


def row_failed(row):
    values = list(row["raster"].values()) + list(row["gate"].values())
    return any(value is False for value in values)


def format_table(rows):
    headers = (
        "file",
        "line",
        "id",
        *RASTER_CHECKS,
        *GATE_CHECKS,
        "verdict",
    )
    cells = []
    for row in rows:
        verdict = "FAIL" if row.get("parse_error") or row_failed(row) else "PASS"
        if row.get("parse_error"):
            raster_cells = ["FAIL"] * len(RASTER_CHECKS)
            gate_cells = ["FAIL"] * len(GATE_CHECKS)
        else:
            raster_cells = [status_cell(row["raster"][name]) for name in RASTER_CHECKS]
            gate_cells = [status_cell(row["gate"][name]) for name in GATE_CHECKS]
        cells.append(
            [
                row["file"],
                str(row["line"]),
                row["id"],
                *raster_cells,
                *gate_cells,
                verdict,
            ]
        )
    widths = [len(header) for header in headers]
    for row in cells:
        for index, cell in enumerate(row):
            widths[index] = max(widths[index], len(cell))

    def fmt(parts):
        return "  ".join(part.ljust(widths[index]) for index, part in enumerate(parts))

    lines = [fmt(headers), fmt(["-" * width for width in widths])]
    lines.extend(fmt(row) for row in cells)
    return "\n".join(lines)


def failure_lines(rows):
    lines = []
    for row in rows:
        if row.get("parse_error"):
            lines.append(f"- {row['file']}:{row['line']} {row['id']}: {row['parse_error']}")
            continue
        if not row_failed(row):
            continue
        for name in RASTER_CHECKS:
            if row["raster"][name] is False:
                lines.append(
                    f"- {row['file']}:{row['line']} {row['id']} raster.{name}: "
                    f"{row['raster_details'][name]}"
                )
        for name in GATE_CHECKS:
            if row["gate"][name] is False:
                lines.append(
                    f"- {row['file']}:{row['line']} {row['id']} gate_snn.{name}: "
                    f"{row['gate_details'][name]}"
                )
    return lines


def write_report(path, files, extra_dirs, missing_required, rows, table, failures):
    n_records = len(rows)
    n_fail = sum(1 for row in rows if row.get("parse_error") or row_failed(row))
    n_pass = n_records - n_fail
    n_raster = sum(1 for row in rows if row.get("raster_locations"))
    n_gate = sum(1 for row in rows if row.get("gate_locations"))
    verdict = "PASS" if not missing_required and n_fail == 0 else "FAIL"
    extra_notes = []
    for directory, exists in extra_dirs:
        if exists:
            extra_notes.append(f"- `{directory}` present")
        else:
            extra_notes.append(f"- `{directory}` absent (skipped)")
    body = [
        "# Raster math report",
        "",
        f"Verdict: **{verdict}**",
        "",
        "## Inputs",
        "",
        f"- Required: `{BATCH_PATH}`",
        *extra_notes,
        "",
        "Files loaded:",
        "",
    ]
    if files:
        body.extend(f"- `{path}`" for path in files)
    else:
        body.append("- (none)")
    if missing_required:
        body.extend(["", "Missing required files:", ""])
        body.extend(f"- `{path}`" for path in missing_required)
    body.extend(
        [
            "",
            "## Counts",
            "",
            f"- records: {n_records}",
            f"- with raster: {n_raster}",
            f"- with gate_snn: {n_gate}",
            f"- pass: {n_pass}",
            f"- fail: {n_fail}",
            "",
            "## Table",
            "",
            "```",
            table if rows else "(no records)",
            "```",
            "",
            "## Failures",
            "",
        ]
    )
    if missing_required:
        body.extend(f"- missing {path}" for path in missing_required)
    if failures:
        body.extend(failures)
    elif not missing_required:
        body.append("- none")
    body.append("")
    path.write_text("\n".join(body), encoding="utf-8")
    return verdict


def main():
    files, missing_required, extra_dirs = discover_inputs()
    rows = []
    for path in files:
        rel = str(path)
        for line_no, record, error in iter_jsonl(path):
            if error:
                rows.append(
                    {
                        "file": rel,
                        "line": line_no,
                        "id": f"line-{line_no}",
                        "parse_error": error,
                        "raster_locations": [],
                        "gate_locations": [],
                        "raster": {name: False for name in RASTER_CHECKS},
                        "raster_details": {name: error for name in RASTER_CHECKS},
                        "gate": {name: False for name in GATE_CHECKS},
                        "gate_details": {name: error for name in GATE_CHECKS},
                    }
                )
                continue
            checked = check_record(record)
            rows.append(
                {
                    "file": rel,
                    "line": line_no,
                    "id": record_id(record, line_no),
                    **checked,
                }
            )
    table = format_table(rows) if rows else "(no records)"
    failures = failure_lines(rows)
    if missing_required:
        failures = [f"- missing required file {path}" for path in missing_required] + failures
    print(table)
    if extra_dirs:
        print()
        for directory, exists in extra_dirs:
            print(f"{directory}: {'present' if exists else 'absent'}")
    print()
    if failures:
        print("FAILURES")
        print("\n".join(failures))
    else:
        print("FAILURES: none")
    verdict = write_report(
        REPORT_PATH, files, extra_dirs, missing_required, rows, table, failures
    )
    print()
    print(f"report: {REPORT_PATH}")
    print(f"verdict: {verdict}")
    return 0 if verdict == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
