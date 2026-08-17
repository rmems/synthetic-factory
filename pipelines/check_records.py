#!/usr/bin/env python3
"""Deep-check factory JSONL records in a run directory.

Recurses *.jsonl and checks parse, record shape (same routing as
validate_run), globally non-decreasing spike times, reward_components
arithmetic, duplicate meta.id, and missing sim_or_real on expected
state objects. Prints totals JSON to stdout and findings to stderr.
Does not write into run_dir.

Usage: python3 pipelines/check_records.py [--strict] <run_dir>
"""

import argparse
import json
import sys
from pathlib import Path

_PIPELINES = Path(__file__).resolve().parent
if str(_PIPELINES) not in sys.path:
    sys.path.insert(0, str(_PIPELINES))
from validate_run import check_line  # noqa: E402

TOL = 1e-4
UNWEIGHTED_EXCLUDE = frozenset({"total", "notes"})
WEIGHTED_SKIP_KEYS = frozenset({"total", "weights", "notes"})


def is_number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def walk_key(obj, name, path=""):
    """Yield (path, value) for every dict entry named `name`."""
    if isinstance(obj, dict):
        for key, val in obj.items():
            child = f"{path}.{key}" if path else key
            if key == name:
                yield child, val
            yield from walk_key(val, name, child)
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            yield from walk_key(item, name, f"{path}[{i}]")


def event_time(event):
    if not isinstance(event, dict):
        return None
    for key in ("t_rel_ms", "t_ms"):
        val = event.get(key)
        if is_number(val):
            return key, float(val)
    return None


def check_spikes(events, where):
    """Require globally non-decreasing times when events carry t_rel_ms/t_ms."""
    if not isinstance(events, list):
        return []
    timed = []
    for i, event in enumerate(events):
        got = event_time(event)
        if got is not None:
            timed.append((i, got[0], got[1]))
    if len(timed) < 2:
        return []
    for (i0, key0, t0), (i1, key1, t1) in zip(timed, timed[1:]):
        if t1 < t0:
            key = key1 if key1 == key0 else f"{key0}/{key1}"
            return [
                f"{where}: spike_events not globally non-decreasing "
                f"at index {i1} ({key} {t0} -> {t1})"
            ]
    return []


def check_reward(rc, where):
    """Recompute total from numeric siblings / weights. Interval totals warn."""
    errors, warnings = [], []
    if not isinstance(rc, dict):
        return errors, warnings
    total = rc.get("total")
    if isinstance(total, (list, tuple, str)):
        warnings.append(
            f"{where}.total is an interval/string; skipped arithmetic check"
        )
        return errors, warnings
    if not is_number(total):
        return errors, warnings

    weights = rc.get("weights")
    if isinstance(weights, dict):
        recomputed = 0.0
        used = False
        for key, weight in weights.items():
            if key in WEIGHTED_SKIP_KEYS:
                continue
            if key in rc and is_number(rc[key]) and is_number(weight):
                recomputed += rc[key] * weight
                used = True
        if not used and not any(
            k not in WEIGHTED_SKIP_KEYS and is_number(w) for k, w in weights.items()
        ):
            return errors, warnings
        if abs(recomputed - total) > TOL:
            errors.append(
                f"{where}.total {total} != recomputed {recomputed} "
                f"(weighted, diff {abs(recomputed - total)} > {TOL})"
            )
        return errors, warnings

    siblings = {
        key: val
        for key, val in rc.items()
        if key not in UNWEIGHTED_EXCLUDE and is_number(val)
    }
    if not siblings:
        return errors, warnings
    recomputed = sum(siblings.values())
    if abs(recomputed - total) > TOL:
        errors.append(
            f"{where}.total {total} != recomputed {recomputed} "
            f"(unweighted, diff {abs(recomputed - total)} > {TOL})"
        )
    return errors, warnings


def expected_states(obj, kind):
    if kind == "thalamic":
        yield "state", obj.get("state")
    elif kind == "preference":
        for side in ("chosen", "rejected"):
            sub = obj.get(side)
            if isinstance(sub, dict):
                yield f"{side}.state", sub.get("state")
    elif kind == "bridge_pair":
        lv = obj.get("language_view")
        if isinstance(lv, dict):
            traj = lv.get("trajectory")
            if isinstance(traj, dict):
                yield "language_view.trajectory.state", traj.get("state")


def shape_check(obj, where):
    if not isinstance(obj, dict):
        return [f"{where}: unrecognized record shape (not an object)"], "unknown"
    try:
        return check_line(obj, where)
    except (TypeError, AttributeError) as exc:
        return [f"{where}: unrecognized record shape ({exc})"], "unknown"


def check_record(obj, where):
    errors, warnings = [], []
    shape_errs, kind = shape_check(obj, where)
    errors.extend(shape_errs)

    if isinstance(obj, dict):
        for path, events in walk_key(obj, "spike_events"):
            errors.extend(check_spikes(events, where))
        for path, rc in walk_key(obj, "reward_components"):
            rc_errs, rc_warns = check_reward(rc, f"{where}: {path}")
            errors.extend(rc_errs)
            warnings.extend(rc_warns)
        for path, state in expected_states(obj, kind):
            if isinstance(state, dict) and "sim_or_real" not in state:
                warnings.append(f"{where}: missing sim_or_real on {path}")

    meta_id = None
    if isinstance(obj, dict):
        meta = obj.get("meta")
        if isinstance(meta, dict) and "id" in meta:
            meta_id = meta["id"]
    return errors, warnings, kind, meta_id


def check_jsonl(path, rel):
    errors, warnings = [], []
    kinds = {}
    records = 0
    seen_ids = {}
    text = Path(path).read_text()
    for lineno, line in enumerate(text.splitlines(), 1):
        if not line.strip():
            continue
        where = f"{rel}:{lineno}"
        try:
            obj = json.loads(line)
        except json.JSONDecodeError as exc:
            errors.append(f"{where}: JSON parse error: {exc}")
            continue
        rec_errs, rec_warns, kind, meta_id = check_record(obj, where)
        records += 1
        kinds[kind] = kinds.get(kind, 0) + 1
        errors.extend(rec_errs)
        warnings.extend(rec_warns)
        if meta_id is not None:
            if meta_id in seen_ids:
                errors.append(
                    f"{where}: duplicate meta.id {meta_id!r} "
                    f"(first {seen_ids[meta_id]})"
                )
            else:
                seen_ids[meta_id] = where
    return errors, warnings, kinds, records


def check_run(run_dir, strict=False):
    run_dir = Path(run_dir).resolve()
    errors, warnings = [], []
    kind_totals = {}
    file_count = 0
    record_count = 0

    for path in sorted(run_dir.rglob("*.jsonl")):
        file_count += 1
        rel = path.relative_to(run_dir)
        file_errs, file_warns, kinds, records = check_jsonl(path, rel)
        errors.extend(file_errs)
        warnings.extend(file_warns)
        record_count += records
        for kind, n in kinds.items():
            kind_totals[kind] = kind_totals.get(kind, 0) + n

    totals = {
        "files": file_count,
        "records": record_count,
        "by_kind": kind_totals,
        "error_count": len(errors),
        "warning_count": len(warnings),
    }
    exit_code = 1 if errors or (strict and warnings) else 0
    return {
        "errors": errors,
        "warnings": warnings,
        "totals": totals,
        "exit_code": exit_code,
    }


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Deep-check JSONL records in a factory run directory.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="treat warnings as errors (exit 1)",
    )
    parser.add_argument("run_dir", help="run directory to recurse for *.jsonl")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    run_dir = Path(args.run_dir).resolve()
    if not run_dir.is_dir():
        print(f"not a directory: {run_dir}", file=sys.stderr)
        sys.exit(2)
    result = check_run(run_dir, strict=args.strict)
    print(json.dumps(result["totals"], indent=2))
    for err in result["errors"]:
        print("ERROR:", err, file=sys.stderr)
    for warn in result["warnings"]:
        print("WARNING:", warn, file=sys.stderr)
    sys.exit(result["exit_code"])


if __name__ == "__main__":
    main()
