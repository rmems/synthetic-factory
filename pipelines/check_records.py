#!/usr/bin/env python3
"""Deep-check factory JSONL records in a run directory.

Recurses *.jsonl and checks parse, record shape (same routing as
validate_run), globally non-decreasing spike times, reward_components
arithmetic, duplicate record IDs, and missing/non-training provenance on expected
state objects. Prints totals JSON to stdout and findings to stderr.
Does not write into run_dir.

Usage: python3 pipelines/check_records.py [--strict] <run_dir>
"""

import argparse
import json
import math
import re
import sys
from pathlib import Path

_PIPELINES = Path(__file__).resolve().parent
if str(_PIPELINES) not in sys.path:
    sys.path.insert(0, str(_PIPELINES))
from validate_run import (  # noqa: E402
    ALLOWED_SIM_OR_REAL,
    BRIDGE_SPIKE_EVENT_KEYS,
    REWARD_ARITHMETIC_MARKERS,
    REWARD_NON_COMPONENT_KEYS,
    _episode_like,
    check_line,
    check_spike_order,
    event_time,
    reject_json_constant,
)

TOL = 1e-6
# Ceiling on a record-declared rounding tolerance (see reward_tolerance).
# 0.05 == a one-decimal rounding step; anything coarser would make the
# arithmetic gate vacuous for rewards of order 1.
MAX_DECLARED_TOL = 0.05
# One exclusion vocabulary for both layers — defined in validate_run so the
# shape layer and this deep layer never disagree about what is a component.
UNWEIGHTED_EXCLUDE = REWARD_NON_COMPONENT_KEYS
WEIGHTED_SKIP_KEYS = frozenset({"total", "weights", "notes"})
WEIGHTED_CONTAINERS = (
    "components",
    "actual",
    "components_executed",
    "components_realized",
    "components_realized_inworld",
    "components_executed_realized_inworld",
)
WEIGHT_ALIASES = {
    "task": ("task", "task_progress", "task_outcome"),
    "safety": ("safety", "safety_alignment", "safety_process"),
    "incentive": ("incentive", "incentive_integrity"),
    "coord": ("coord", "coordination", "coordination_integrity"),
}
# Legacy alias: pipelines/training_audit.py imports this name for the same
# state.sim_or_real vocabulary.
ALLOWED_PROVENANCE = ALLOWED_SIM_OR_REAL
ROUNDING_RE = re.compile(r"(?:rounded?\s+(?:to\s+)?)?(\d+)[- ]decimal", re.I)


def is_number(value):
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
    )


def claims_real(value):
    """True when a provenance value claims real-world origin.

    Matches the exact value 'real' or a 'real'-prefixed variant
    ('real_world', 'real-world'). Values that merely contain the substring,
    such as 'not_real' or 'non-real', are not real-world claims.
    """
    if not isinstance(value, str):
        return False
    lowered = value.strip().lower()
    return lowered == "real" or lowered.startswith(("real_", "real-", "real "))


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


def check_spike_stream_shape(events, where, *, require_keys=(), require_nonempty=False):
    """Strict shape/order validation for one discovered ``spike_events`` stream.

    The deep record checker uses this for every stream it discovers — the
    shape layer's own copies are dropped so each stream is reported exactly
    once (see the single-owner comment on ``check_record``).
    """
    if not isinstance(events, list):
        return [f"{where}: spike_events must be an array"]
    if require_nonempty and not events:
        return [f"{where}: spike_events must be a non-empty array"]
    return check_spike_order(events, where, require_keys=require_keys)


def _timed_spike_events(events):
    """Return ``(index, key, value)`` for every event with one finite timestamp.

    Untimed or ambiguously-timed (dual-key) events are silently excluded —
    the caller decides what an incomplete result means.
    """
    timed = []
    for i, event in enumerate(events):
        got = event_time(event)
        if got is not None:
            timed.append((i, got[0], got[1]))
    return timed


def _first_spike_order_violation(where, timed):
    """The first global non-decreasing-order violation among timed events, if any."""
    for (i0, key0, t0), (i1, key1, t1) in zip(timed, timed[1:]):
        if t1 < t0:
            key = key1 if key1 == key0 else f"{key0}/{key1}"
            return [
                f"{where}: spike_events not globally non-decreasing "
                f"at index {i1} ({key} {t0} -> {t1})"
            ]
    return []


def check_spikes(events, where):
    """Probe whether a stream is unambiguously, safely out of order.

    Used by promotion's safe sorter (and directly by tests) to decide
    whether resorting is safe: reports an error only for a genuine global
    order violation on a single, unambiguous timestamp key. Untimed,
    mixed-key, non-array, or too-short streams are silently accepted (empty
    result) since they are neither compared nor resorted by the caller.
    """
    if not isinstance(events, list):
        return []
    timed = _timed_spike_events(events)
    if len(timed) < 2:
        return []
    time_keys = {key for _, key, _ in timed}
    if len(time_keys) > 1:
        return []
    return _first_spike_order_violation(where, timed)


def component_value(value):
    """Return a numeric reward component from supported compact/rich layouts."""
    if is_number(value):
        return float(value)
    if isinstance(value, dict) and is_number(value.get("value")):
        return float(value["value"])
    return None


def reward_tolerance(rc):
    """Honor an explicit rounding declaration while keeping the default strict.

    Default tolerance is TOL (1e-6). An explicit rounding_decimals — or a
    "N-decimal" rounding note — widens the bound to half of that rounding
    step, matching pipelines/curate_rewards.py; a declaration finer than TOL
    never tightens below it.

    The widening is capped at MAX_DECLARED_TOL. The declaration comes from the
    record being checked, so an uncapped bound would let a generated record
    declare its own arithmetic gate away (rounding_decimals: 0 implies +/-0.5,
    which is vacuous against totals of order 1). The cap still honors every
    rounding declaration of one decimal or finer.
    """
    decimals = rc.get("rounding_decimals")
    if not isinstance(decimals, int) or isinstance(decimals, bool) or decimals < 0:
        decimals = None
        for key in ("notes", "aggregation", "convention"):
            value = rc.get(key)
            if not isinstance(value, str):
                continue
            match = ROUNDING_RE.search(value)
            if match:
                decimals = int(match.group(1))
                break
    if decimals is None:
        return TOL
    requested = 0.5 * (10 ** -decimals) + 1e-12
    return min(MAX_DECLARED_TOL, max(TOL, requested))


def weighted_components(rc, weights):
    """Resolve every declared weight from direct or known nested maps."""
    containers = [rc]
    containers.extend(
        rc[key]
        for key in WEIGHTED_CONTAINERS
        if isinstance(rc.get(key), dict)
    )
    values = {}
    missing = []
    for key, weight in weights.items():
        if key in WEIGHTED_SKIP_KEYS or not is_number(weight):
            continue
        value = None
        aliases = WEIGHT_ALIASES.get(key, (key,))
        for container in containers:
            for candidate in aliases:
                if candidate not in container:
                    continue
                value = component_value(container[candidate])
                if value is not None:
                    break
            if value is not None:
                break
        if value is None:
            missing.append(key)
        else:
            values[key] = value
    return values, missing


def check_reward(rc, where):
    """Recompute total from numeric siblings / weights. Strict total==sum (TOL=1e-6)."""
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
        declared = {
            key: float(weight)
            for key, weight in weights.items()
            if key not in WEIGHTED_SKIP_KEYS and is_number(weight)
        }
        if declared:
            values, missing = weighted_components(rc, weights)
            if missing:
                warnings.append(
                    f"{where}: unsupported weighted reward layout; missing components "
                    f"{', '.join(sorted(missing))}; skipped arithmetic check"
                )
                return errors, warnings
            recomputed = sum(values[key] * declared[key] for key in declared)
            tolerance = reward_tolerance(rc)
            if abs(recomputed - total) > tolerance:
                errors.append(
                    f"{where}.total {total} != recomputed {recomputed} "
                    f"(weighted, diff {abs(recomputed - total)} > {tolerance})"
                )
            return errors, warnings
        # Empty or bookkeeping-only weights: same fallthrough as
        # validate_run.check_reward_total — unweighted sibling sum.

    siblings = {
        key: component_value(val)
        for key, val in rc.items()
        if key not in UNWEIGHTED_EXCLUDE and component_value(val) is not None
    }
    if not siblings:
        return errors, warnings
    recomputed = sum(siblings.values())
    tolerance = reward_tolerance(rc)
    if abs(recomputed - total) > tolerance:
        errors.append(
            f"{where}.total {total} != recomputed {recomputed} "
            f"(unweighted, diff {abs(recomputed - total)} > {tolerance})"
        )
    return errors, warnings


def expected_states(obj, kind):
    if kind == "thalamic":
        yield "state", obj.get("state")
    elif kind == "preference":
        for side in ("chosen", "rejected"):
            sub = obj.get(side)
            if not isinstance(sub, dict):
                continue
            # Episode-sided DPO pairs have no Thalamic state object.
            if _episode_like(sub):
                continue
            yield f"{side}.state", sub.get("state")
    elif kind == "bridge_pair":
        lv = obj.get("language_view")
        if isinstance(lv, dict):
            traj = lv.get("trajectory")
            if isinstance(traj, dict):
                yield "language_view.trajectory.state", traj.get("state")


# The shape layer also recomputes reward sums, with a simpler weighted model
# than this checker's. This layer owns reward arithmetic (its "recomputed"
# errors), so the shape layer's comparison errors are dropped here to
# avoid double or spurious reports on the same record. The markers are the
# producer's own constants, imported from validate_run.
_SHAPE_REWARD_ARITHMETIC = REWARD_ARITHMETIC_MARKERS
# Same layering for publish-time 'real' claims: validate_run already emits
# them, and check_provenance_publish is the single owner here.
_SHAPE_REAL_PROVENANCE = "must not be 'real'"
# And the same for spike stream validity. The shape layer checks the bridge
# stream and direct trajectory streams; this layer walks every nested stream,
# so it is the single owner of array, event, clock, and order errors. Bridge-only
# required fields are supplied below when the walked path is the bridge root.


_WHERE_STEP_INFIX_RE = re.compile(r"^ step \d+: ")


def _after_where(msg, where):
    """Return the diagnostic body with the location prefix removed.

    Findings are ``{where}: {body}``, ``{where}.{nested}: {body}``, or
    ``{where} step {i}: {body}`` (check_episode's per-step form). Matching
    drop markers against the full string lets a relative path such as
    ``bad: spike_events.jsonl`` — or ``spike_events.jsonl`` itself, paired
    with an episode step error — swallow unrelated shape errors.
    """
    if not msg.startswith(where):
        return msg
    rest = msg[len(where):]
    if rest.startswith(": "):
        return rest[2:]
    if rest.startswith("."):
        sep = rest.find(": ")
        if sep != -1:
            return rest[sep + 2:]
    step_match = _WHERE_STEP_INFIX_RE.match(rest)
    if step_match:
        return rest[step_match.end():]
    return msg


def _is_shape_spike_stream(body):
    """True when the diagnostic path names a spike_events stream."""
    path = body.split(" ", 1)[0]
    return (
        path == "spike_events"
        or path.startswith("spike_events[")
        or path.startswith("spike_events.")
        or ".spike_events" in path
    )


def shape_check(obj, where, factory_staging=False):
    if not isinstance(obj, dict):
        return [f"{where}: unrecognized record shape (not an object)"], "unknown"
    try:
        errs, kind = check_line(obj, where, factory_staging=factory_staging)
    except (TypeError, AttributeError) as exc:
        return [f"{where}: unrecognized record shape ({exc})"], "unknown"
    kept = []
    for err in errs:
        body = _after_where(err, where)
        if any(marker in body for marker in _SHAPE_REWARD_ARITHMETIC):
            continue
        if _SHAPE_REAL_PROVENANCE in body:
            continue
        if _is_shape_spike_stream(body):
            continue
        kept.append(err)
    return kept, kind


def canonical_record_id(obj):
    """Prefer a top-level id; accept legacy top-level meta.id."""
    if not isinstance(obj, dict):
        return None
    value = obj.get("id")
    if isinstance(value, str) and value.strip():
        return value.strip()
    meta = obj.get("meta")
    if isinstance(meta, dict):
        value = meta.get("id")
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def root_record_id(obj):
    """Return the canonical v2 top-level ID without legacy fallback."""
    if not isinstance(obj, dict):
        return None
    value = obj.get("id")
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None


def check_provenance_publish(obj, where):
    """Publish-time provenance gate — any 'real' sim_or_real/provenance.kind is an error.

    Spike order is already enforced globally; this gate ensures generative data
    cannot publish with real-world provenance claims.
    """
    errs = []

    def walk(node, path):
        if isinstance(node, dict):
            for k, v in node.items():
                cur = f"{path}.{k}" if path else k
                if k == "sim_or_real" and claims_real(v):
                    # Other invalid values are surfaced as non-training
                    # provenance warnings by check_record; this gate is only
                    # for real-world claims.
                    errs.append(
                        f"{where}: {cur} must not be 'real' (use 'designed') — got {v!r}"
                    )
                if k == "provenance" and isinstance(v, dict):
                    kind = v.get("kind")
                    if claims_real(kind):
                        errs.append(
                            f"{where}: {cur}.kind must not be 'real' — got {kind!r}"
                        )
                walk(v, cur)
        elif isinstance(node, list):
            for i, item in enumerate(node):
                walk(item, f"{path}[{i}]")

    walk(obj, "")
    # Deduplicate
    seen = set()
    out = []
    for e in errs:
        if e not in seen:
            seen.add(e)
            out.append(e)
    return out


def _is_reward_narrative_spike_events(path):
    """True when a walked ``spike_events`` key is reward-component narration.

    ``reward_components.spike_events`` is a documented string-valued
    narrative annotation in the reward ontology
    (schemas/reward-ontology-v1.mapping.json: disposition
    "narrative_annotation", observed type "string"), not an event stream.
    ``walk_key`` matches by key name only, so this path-aware guard keeps it
    from being misread as a malformed stream.
    """
    parts = path.split(".")
    return len(parts) >= 2 and parts[-2] == "reward_components"


def check_record(obj, where, factory_staging=False):
    errors, warnings = [], []
    shape_errs, kind = shape_check(obj, where, factory_staging=factory_staging)
    errors.extend(shape_errs)

    if isinstance(obj, dict):
        for path, events in walk_key(obj, "spike_events"):
            if _is_reward_narrative_spike_events(path):
                continue
            # Single owner of stream validity: shape_check drops the shape
            # layer's copies, so every stream — top-level, bridge, or nested —
            # is reported exactly once from here. Only the bridge root requires
            # channel/amplitude and a non-empty array.
            bridge_root = kind == "bridge_pair" and path == "spike_events"
            errors.extend(
                check_spike_stream_shape(
                    events,
                    f"{where}: {path}",
                    require_keys=(BRIDGE_SPIKE_EVENT_KEYS if bridge_root else ()),
                    require_nonempty=bridge_root,
                )
            )
        for path, rc in walk_key(obj, "reward_components"):
            rc_errs, rc_warns = check_reward(rc, f"{where}: {path}")
            errors.extend(rc_errs)
            warnings.extend(rc_warns)
        # Strict provenance: expected states missing or invalid
        for path, state in expected_states(obj, kind):
            if isinstance(state, dict) and "sim_or_real" not in state:
                warnings.append(f"{where}: missing sim_or_real on {path}")
            elif isinstance(state, dict):
                value = state.get("sim_or_real")
                # 'real' claims are owned by check_provenance_publish so a
                # single violation is not reported twice with different wording.
                if not claims_real(value) and value not in ALLOWED_SIM_OR_REAL:
                    warnings.append(
                        f"{where}: non-training provenance {value!r} on {path}"
                    )
        # Publish-time deep provenance scan — owns every nested 'real' claim
        errors.extend(check_provenance_publish(obj, where))
        if kind == "episode":
            steps = obj.get("steps")
            for index, step in enumerate(steps if isinstance(steps, list) else ()):
                if (
                    isinstance(step, dict)
                    and "thought" in step
                    and "decision_basis" not in step
                ):
                    warnings.append(
                        f"{where}: step {index} uses legacy 'thought' without "
                        "observable decision_basis"
                    )

    record_id = canonical_record_id(obj)
    if record_id is None:
        warnings.append(f"{where}: missing canonical record id")
    elif root_record_id(obj) is None:
        warnings.append(f"{where}: missing top-level id (legacy meta.id only)")
    return errors, warnings, kind, record_id


def check_jsonl(path, rel, seen_ids=None, factory_staging=False):
    errors, warnings = [], []
    kinds = {}
    records = 0
    if seen_ids is None:
        seen_ids = {}
    try:
        text = Path(path).read_text()
    except UnicodeDecodeError as exc:
        return [f"{rel}: invalid UTF-8: {exc}"], warnings, kinds, records
    # JSONL record boundaries are literal LF only.  U+2028 and U+2029 remain
    # ordinary JSON string data and must not be treated as line separators.
    for lineno, line in enumerate(text.split("\n"), 1):
        if not line.strip():
            continue
        where = f"{rel}:{lineno}"
        try:
            obj = json.loads(line, parse_constant=reject_json_constant)
        except (json.JSONDecodeError, ValueError) as exc:
            errors.append(f"{where}: JSON parse error: {exc}")
            continue
        rec_errs, rec_warns, kind, record_id = check_record(
            obj, where, factory_staging=factory_staging
        )
        records += 1
        kinds[kind] = kinds.get(kind, 0) + 1
        errors.extend(rec_errs)
        warnings.extend(rec_warns)
        if record_id is not None:
            if record_id in seen_ids:
                errors.append(
                    f"{where}: duplicate record id {record_id!r} "
                    f"(first {seen_ids[record_id]})"
                )
            else:
                seen_ids[record_id] = where
    return errors, warnings, kinds, records


def check_run(run_dir, strict=False):
    run_dir = Path(run_dir).resolve()
    errors, warnings = [], []
    kind_totals = {}
    file_count = 0
    record_count = 0
    seen_ids = {}

    for path in sorted(run_dir.rglob("*.jsonl")):
        file_count += 1
        rel = path.relative_to(run_dir)
        file_errs, file_warns, kinds, records = check_jsonl(
            path, rel, seen_ids=seen_ids
        )
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
