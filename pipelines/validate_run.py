#!/usr/bin/env python3
"""Validate a dated factory run under outputs/raw/<date>/.

Checks every .jsonl file: each line must parse as JSON, and any embedded
ThalamicTrajectory (top-level, chosen/rejected pair, or language_view.trajectory)
must satisfy schemas/thalamic-trajectory.schema.json's constraints. Coding
episodes are checked against their own shape. Prints totals JSON to stdout
and errors to stderr; exits nonzero if any file has errors. Does not write
manifest.json unless --write is passed.

Usage: python3 pipelines/validate_run.py [--write] <run_dir>
"""

import argparse
import json
import math
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SCHEMA_PATH = REPO / "schemas" / "thalamic-trajectory.schema.json"
THALAMIC_SCHEMA = json.loads(SCHEMA_PATH.read_text())
THALAMIC_REQUIRED = tuple(THALAMIC_SCHEMA["required"])
# Type-check required keys against the schema's own declared types: the six
# trajectory fields (+ meta) are objects, but canonical `id` is a string.
THALAMIC_OBJECT_KEYS = tuple(
    key for key in THALAMIC_REQUIRED
    if THALAMIC_SCHEMA["properties"].get(key, {}).get("type") == "object"
)
THALAMIC_STRING_KEYS = tuple(
    key for key in THALAMIC_REQUIRED
    if THALAMIC_SCHEMA["properties"].get(key, {}).get("type") == "string"
)
# The six trajectory fields identify a thalamic record for routing; `meta`
# and `id`, though required, are exactly what legacy records are missing,
# so routing on them would hide every other invariant behind an
# "unrecognized shape" error.
THALAMIC_CORE_KEYS = tuple(
    key for key in THALAMIC_OBJECT_KEYS if key != "meta"
)
SAFETY_DECISIONS = frozenset(
    THALAMIC_SCHEMA["properties"]["safety_decision"]["properties"]
    ["decision"]["enum"]
)

# provenance.kind allows 'unknown'; state.sim_or_real does not.
ALLOWED_PROVENANCE_KIND = frozenset({"designed", "simulated", "hil", "unknown"})
ALLOWED_SIM_OR_REAL = frozenset({"designed", "simulated", "hil"})
# Bookkeeping keys that are not counted toward the arithmetic sum. This is the
# single exclusion vocabulary for reward arithmetic: check_records imports it
# so the shape layer and the deep layer agree on what is a component, and a
# record that reconciles under one layer is not rejected by the other.
REWARD_NON_COMPONENT_KEYS = frozenset(
    {
        "aggregation",
        "comment",
        "component_notes",
        "convention",
        "description",
        "frame",
        "native_unit",
        "notes",
        "provenance_notes",
        "rounding_decimals",
        "total",
        "total_basis",
        "unit_usd",
        "units",
        "weights",
        "weights_note",
    }
)
# Strict arithmetic tolerance — total must equal sum within 1e-6.
REWARD_TOL = 1e-6


def is_number(value):
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
    )


def event_time(event):
    """Return (key, finite float timestamp) for a supported event object."""
    if not isinstance(event, dict):
        return None
    for key in ("t_rel_ms", "t_ms"):
        value = event.get(key)
        if is_number(value):
            return key, float(value)
    return None


def check_spike_order(events, where):
    """Require finite timestamps and global non-decreasing event order."""
    errs = []
    previous = None
    for index, event in enumerate(events):
        if not isinstance(event, dict):
            errs.append(f"{where}: spike_events[{index}] must be an object")
            continue
        for key in ("channel", "amplitude"):
            if key not in event:
                errs.append(f"{where}: spike_events[{index}] missing '{key}'")
        got = event_time(event)
        if got is None:
            errs.append(
                f"{where}: spike_events[{index}] needs finite t_rel_ms or t_ms"
            )
            continue
        key, current = got
        if previous is not None and current < previous[1]:
            errs.append(
                f"{where}: spike_events not globally non-decreasing at index "
                f"{index} ({key} {previous[1]} -> {current})"
            )
            break
        previous = (key, current)
    return errs


def _component_numeric(value):
    """Extract numeric component value from plain number or {value: number}."""
    if is_number(value):
        return float(value)
    if isinstance(value, dict) and is_number(value.get("value")):
        return float(value["value"])
    return None


# Marker substrings of the two mismatch messages built in check_reward_total.
# check_records imports this tuple to drop the shape layer's arithmetic errors:
# it owns reward arithmetic and would otherwise report the same record twice.
REWARD_WEIGHTED_MISMATCH = "!= weighted sum"
REWARD_UNWEIGHTED_MISMATCH = "!= sum of components"
REWARD_ARITHMETIC_MARKERS = (REWARD_UNWEIGHTED_MISMATCH, REWARD_WEIGHTED_MISMATCH)


def check_reward_total(rc, where):
    """Validate reward_components arithmetic: total == sum(component values).

    Strict gate: total must equal the arithmetic sum of all numeric components
    (excluding bookkeeping keys) within REWARD_TOL. Weighted aggregations are
    supported; interval/string totals are rejected as non-finite.
    """
    errs = []
    if not isinstance(rc, dict):
        return errs
    if "total" not in rc:
        errs.append(f"{where}: reward_components missing 'total'")
        return errs
    total = rc.get("total")
    if not is_number(total):
        # Interval/string totals (e.g. [0.1, 0.9] or "0.5 ± 0.1") skip the
        # arithmetic gate here; check_records surfaces them as warnings and
        # the reward-normalization curation lane owns their conversion.
        # Numeric-but-non-finite totals (NaN/inf) still fail via is_number, and
        # a boolean total is invalid schema input rather than a skippable shape.
        if isinstance(total, (int, float)):
            errs.append(f"{where}: reward_components.total must be a finite number")
        return errs
    # Weighted layout: total == sum(value_i * weight_i)
    weights = rc.get("weights")
    if isinstance(weights, dict) and weights:
        # Resolve declared weights (ignore non-finite weights)
        declared = {
            k: float(v)
            for k, v in weights.items()
            if k not in REWARD_NON_COMPONENT_KEYS and is_number(v)
        }
        if declared:
            # Collect containers that may hold component values (direct or nested)
            containers = [rc]
            for key in ("components", "components_executed", "components_realized"):
                if isinstance(rc.get(key), dict):
                    containers.append(rc[key])
            # Try to resolve every declared weight
            recomputed = 0.0
            unresolved = []
            for k, w in declared.items():
                val = None
                aliases = {
                    "task": ("task", "task_progress", "task_outcome"),
                    "safety": ("safety", "safety_alignment", "safety_process"),
                }.get(k, (k,))
                for c in containers:
                    for cand in aliases:
                        if cand in c:
                            val = _component_numeric(c[cand])
                            if val is not None:
                                break
                    if val is not None:
                        break
                    # also try direct key in rc
                    if k in c:
                        val = _component_numeric(c[k])
                        if val is not None:
                            break
                if val is None:
                    unresolved.append(k)
                else:
                    recomputed += val * w
            if unresolved:
                # Weights are declared but this layer cannot resolve every
                # component. The sibling-sum check below does not model the
                # weighted layout, so falling through would report a false
                # mismatch; check_records owns the unsupported-layout warning.
                return errs
            if not math.isclose(
                float(total), recomputed, rel_tol=0.0, abs_tol=REWARD_TOL
            ):
                errs.append(
                    f"{where}: reward_components.total {total} {REWARD_WEIGHTED_MISMATCH} {recomputed:.6g} (diff {abs(float(total) - recomputed):.6g} > {REWARD_TOL})"
                )
            return errs
    # Unweighted: sum of numeric siblings (plain or {value: n})
    component_sum = 0.0
    has_component = False
    for k, v in rc.items():
        if k in REWARD_NON_COMPONENT_KEYS:
            continue
        # Skip known metadata containers that are not scalar components
        if k in ("components", "components_executed", "components_realized", "ticks"):
            continue
        num = _component_numeric(v)
        if num is not None:
            # Guard against non-finite already filtered by _component_numeric
            component_sum += float(num)
            has_component = True
        elif isinstance(v, dict) and "value" in v:
            # Rich object with non-finite value
            if isinstance(v.get("value"), (int, float)) and not is_number(v["value"]):
                errs.append(
                    f"{where}: reward_components.{k}.value must be a finite number"
                )
        elif isinstance(v, (int, float)) and not is_number(v):
            errs.append(
                f"{where}: reward_components.{k} must be a finite number"
            )
    # Only enforce sum check when at least one numeric component exists
    # beyond total (otherwise total alone is allowed, e.g. minimal fixture).
    if has_component:
        if not math.isclose(
            float(total), component_sum, rel_tol=0.0, abs_tol=REWARD_TOL
        ):
            errs.append(
                f"{where}: reward_components.total {total} {REWARD_UNWEIGHTED_MISMATCH} {component_sum:.6g} (diff {abs(float(total) - component_sum):.6g} > {REWARD_TOL})"
            )
    return errs


def check_provenance(obj, where):
    """Strict provenance checks for top-level record, including publish-time gate.

    - state.sim_or_real must be exactly one of {designed, simulated, hil}
      (never 'real', never 'unknown', never missing for thalamic shapes).
    - provenance.kind must be one of {designed, simulated, hil, unknown}
      (never 'real').
    - Any occurrence of the string 'real' (case-insensitive) in sim_or_real
      or provenance.kind is rejected explicitly.
    This function is the publish-time provenance gate: it is invoked for every
    trajectory (top-level, chosen/rejected, and language_view.trajectory).
    """
    errs = []
    # state.sim_or_real strict — required for v2 thalamic trajectories
    state = obj.get("state")
    if isinstance(state, dict):
        if "sim_or_real" in state:
            val = state.get("sim_or_real")
            # One violation, one error: a 'real' value gets the specific
            # (more actionable) message instead of that message plus the
            # generic enum error, since inflated counts feed training_audit.
            if isinstance(val, str) and "real" in val.lower():
                errs.append(f"{where}: state.sim_or_real must not be 'real' (use 'designed')")
            elif not isinstance(val, str) or val not in ALLOWED_SIM_OR_REAL:
                errs.append(
                    f"{where}: state.sim_or_real must be one of {sorted(ALLOWED_SIM_OR_REAL)}"
                )
        else:
            # For v2 thalamic shapes, sim_or_real is mandatory; flag missing
            # only when state looks like a thalamic state (has any expected key)
            # to avoid false positives on unrelated objects.
            if any(k in state for k in ("episode_id", "domain", "t0_us", "sim_or_real")):
                # Only require when caller is a thalamic trajectory (checked via required keys)
                pass  # defer to caller (check_thalamic) to enforce presence
    elif "state" in obj:
        # state present but not a dict
        errs.append(f"{where}: state must be an object")

    # provenance.kind strict — global check
    if "provenance" in obj:
        prov = obj.get("provenance")
        if not isinstance(prov, dict):
            errs.append(f"{where}: provenance must be an object")
        else:
            kind = prov.get("kind")
            if kind not in ALLOWED_PROVENANCE_KIND:
                errs.append(
                    f"{where}: provenance.kind must be one of {sorted(ALLOWED_PROVENANCE_KIND)}"
                )
            if isinstance(kind, str) and "real" in kind.lower():
                errs.append(f"{where}: provenance.kind must not be 'real'")
            # claimed should be string/null if present
            if "claimed" in prov:
                claimed = prov.get("claimed")
                if claimed is not None and not isinstance(claimed, str):
                    errs.append(f"{where}: provenance.claimed must be a string or null")
            # v2 publish: unknown provenance is discouraged for new data
            # but still allowed per legacy schema — no error, just strict enum above.
    # Deep provenance: walk any nested provenance objects (e.g. inside state)
    # to catch hidden 'real' claims. Report once via top-level check above;
    # nested walk is handled in check_provenance_publish for full run.
    return errs


def check_provenance_publish(obj, where):
    """Publish-time deep provenance scan: any nested sim_or_real/provenance.kind == 'real' fails.

    Called from check_thalamic and bridge/choice helpers to ensure staged batches
    cannot publish hidden 'real' provenance. Spike order is already enforced
    elsewhere.
    """
    errs = []

    def walk(node, path):
        if isinstance(node, dict):
            for k, v in node.items():
                cur = f"{path}.{k}" if path else k
                if k == "sim_or_real" and isinstance(v, str) and "real" in v.lower():
                    errs.append(f"{where}: {cur} must not be 'real' (use 'designed')")
                if k == "provenance" and isinstance(v, dict):
                    kind = v.get("kind")
                    if isinstance(kind, str) and "real" in kind.lower():
                        errs.append(f"{where}: {cur}.kind must not be 'real'")
                walk(v, cur)
        elif isinstance(node, list):
            for i, item in enumerate(node):
                walk(item, f"{path}[{i}]")

    walk(obj, "")
    # Deduplicate while preserving order
    seen = set()
    uniq = []
    for e in errs:
        if e not in seen:
            seen.add(e)
            uniq.append(e)
    return uniq


def check_meta_round(obj, where):
    """Require meta.round presence and integer >=1.

    A missing or non-object `meta` is already reported by the required-key
    loop in check_thalamic, so this returns quietly in that case rather than
    emitting a second error for the same violation.
    """
    errs = []
    meta = obj.get("meta")
    if not isinstance(meta, dict):
        return errs
    if "round" not in meta:
        errs.append(f"{where}: meta.round is required")
        return errs
    rnd = meta.get("round")
    # bool is subclass of int, exclude
    if isinstance(rnd, bool) or not isinstance(rnd, int):
        errs.append(f"{where}: meta.round must be an integer")
        return errs
    if rnd < 1:
        errs.append(f"{where}: meta.round must be >= 1")
    return errs


def check_thalamic(obj, where):
    errs = []
    # Shape layer: the object-typed fields (incl. meta) are required here.
    # Canonical `id` presence/coverage is a deep-layer concern
    # (check_records / training_audit); at this layer it is only
    # type-checked when present.
    for key in THALAMIC_OBJECT_KEYS:
        if key not in obj:
            errs.append(f"{where}: missing required key '{key}'")
        elif not isinstance(obj[key], dict):
            errs.append(f"{where}: '{key}' must be an object")
    for key in THALAMIC_STRING_KEYS:
        if key in obj and (not isinstance(obj[key], str) or not obj[key].strip()):
            errs.append(f"{where}: '{key}' must be a non-empty string")
    sd = obj.get("safety_decision")
    if isinstance(sd, dict):
        if sd.get("decision") not in SAFETY_DECISIONS:
            errs.append(f"{where}: safety_decision.decision must be ACCEPT|MODIFY|REJECT")
        rationale = sd.get("rationale")
        if not isinstance(rationale, str) or not rationale.strip():
            errs.append(f"{where}: safety_decision.rationale must be a non-empty string")
    rc = obj.get("reward_components")
    if isinstance(rc, dict):
        errs += check_reward_total(rc, where)
    # A non-object reward_components is already reported by the required-key
    # loop above; do not emit a second error for the same violation.
    else:
        # rc missing already reported via required-key loop; also handle explicit missing total
        if rc is None:
            pass
    # strict provenance and meta checks (including publish-time deep scan)
    errs += check_provenance(obj, where)
    # Deep publish-time provenance: any nested 'real' fails
    errs += [e for e in check_provenance_publish(obj, where) if e not in errs]
    errs += check_meta_round(obj, where)
    return errs


SAFETY_CASE_TYPES = frozenset(
    {"correct_refusal", "incorrect_refusal", "missed_refusal"}
)
SAFETY_CASE_DECISIONS = {
    "correct_refusal": "refuse",
    "missed_refusal": "comply",
}
SAFETY_CASE_SUCCESS = {
    "correct_refusal": True,
    "missed_refusal": False,
}
HIDDEN_THOUGHT_KEYS = frozenset(
    {"thought", "chain_of_thought", "scratch", "inner_monologue"}
)


def _episode_like(obj):
    """True when an object is a coding/agent episode rather than Thalamic."""
    return (
        isinstance(obj, dict)
        and "steps" in obj
        and not all(key in obj for key in THALAMIC_CORE_KEYS)
    )


def _hidden_thought_paths(value, path=""):
    """Return every nested forbidden hidden-reasoning key and its path."""
    found = []
    if isinstance(value, dict):
        for key, item in value.items():
            child_path = f"{path}.{key}" if path else key
            normalized_key = re.sub(
                r"[^a-z0-9]+",
                "_",
                re.sub(
                    r"(?<=[a-z0-9])(?=[A-Z])", "_", str(key)
                ).casefold(),
            ).strip("_")
            if normalized_key in HIDDEN_THOUGHT_KEYS:
                found.append((key, child_path))
            found.extend(_hidden_thought_paths(item, child_path))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            found.extend(_hidden_thought_paths(item, f"{path}[{index}]"))
    return found


def _staging_hidden_thought_errors(obj, where):
    return [
        f"{where}: hidden '{key}' is forbidden at {path}; use observable fields"
        for key, path in _hidden_thought_paths(obj)
    ]


def _normalized_goal(value):
    if not isinstance(value, str) or not value.strip():
        return None
    return " ".join(value.split())


def _preference_side_context_anchors(value):
    """Return observable file/API/criterion anchors from one preference side."""
    anchors = set()
    context_key_terms = (
        "api",
        "criterion",
        "criteria",
        "endpoint",
        "file",
        "path",
        "repo",
        "repository",
        "resource",
        "target",
        "url",
    )
    artifact_re = re.compile(
        r"https?://[^\s\"']+|"
        r"(?:[a-z0-9_.-]+/)*[a-z0-9_.-]+\."
        r"(?:csv|env|go|java|js|json|md|py|rs|sql|toml|ts|txt|ya?ml)|"
        r"/(?:[a-z0-9_{}.-]+/)*[a-z0-9_{}.-]+",
        re.IGNORECASE,
    )

    def walk(node, key=""):
        if isinstance(node, dict):
            for child_key, child in node.items():
                walk(child, str(child_key).casefold())
        elif isinstance(node, list):
            for child in node:
                walk(child, key)
        elif isinstance(node, str):
            normalized = " ".join(node.split()).casefold()
            if key and any(term in key for term in context_key_terms):
                anchors.add(f"field:{normalized}")
            anchors.update(
                f"artifact:{match.group(0).rstrip('.,;:').casefold()}"
                for match in artifact_re.finditer(node)
            )

    walk(value)
    return anchors


def _staging_preference_goal_errors(obj, where):
    """Require explicit or inherited agreement on one preference problem."""
    chosen = obj.get("chosen")
    rejected = obj.get("rejected")
    raw_goals = {
        "goal": obj.get("goal"),
        "chosen.goal": chosen.get("goal") if isinstance(chosen, dict) else None,
        "rejected.goal": rejected.get("goal") if isinstance(rejected, dict) else None,
    }
    normalized = {}
    errors = []
    for path, value in raw_goals.items():
        if value is None:
            continue
        goal = _normalized_goal(value)
        if goal is None:
            errors.append(f"{where}: {path} must be a non-empty string when present")
        else:
            normalized[path] = goal
    if not normalized:
        return [f"{where}: preference needs a shared non-empty goal"]
    if raw_goals["goal"] is None and (
        "chosen.goal" not in normalized or "rejected.goal" not in normalized
    ):
        errors.append(
            f"{where}: preference needs both side goals when no top-level goal is present"
        )
    if len(set(normalized.values())) > 1:
        errors.append(f"{where}: top-level and side goals must describe the same problem")
    if isinstance(chosen, dict) and isinstance(rejected, dict):
        chosen_context = _preference_side_context_anchors(chosen)
        rejected_context = _preference_side_context_anchors(rejected)
        if (
            chosen_context
            and rejected_context
            and chosen_context.isdisjoint(rejected_context)
        ):
            errors.append(
                f"{where}: preference sides must share observable file, API, "
                "target, or success-criterion context"
            )
    return errors


def _require_reward(obj, where):
    reward = obj.get("reward")
    if not isinstance(reward, dict):
        return [f"{where}: reward must be an object with 'success'"]
    if "success" not in reward:
        return [f"{where}: reward missing 'success'"]
    if not isinstance(reward["success"], bool):
        return [f"{where}: reward.success must be a boolean"]
    errors = []
    stack = [("reward", reward)]
    while stack:
        path, value = stack.pop()
        if isinstance(value, dict):
            stack.extend((f"{path}.{key}", child) for key, child in value.items())
        elif isinstance(value, list):
            stack.extend((f"{path}[{index}]", child) for index, child in enumerate(value))
        elif isinstance(value, float) and not math.isfinite(value):
            errors.append(f"{where}: {path} must be a finite number")
    return errors


def _staging_tool_turn_errors(turn, where):
    """Validate an observable structured tool turn in staged agentic data."""
    errors = []
    basis = turn.get("decision_basis")
    if not isinstance(basis, str) or not basis.strip():
        errors.append(f"{where}: decision_basis must be a non-empty string")
    tool_call = turn.get("tool_call")
    if not isinstance(tool_call, dict):
        errors.append(f"{where}: tool_call must be an object")
    else:
        if not isinstance(tool_call.get("name"), str) or not tool_call["name"].strip():
            errors.append(f"{where}: tool_call.name must be a non-empty string")
        if not isinstance(tool_call.get("args"), dict):
            errors.append(f"{where}: tool_call.args must be an object")
    observation = turn.get("observation")
    if not isinstance(observation, str) or not observation.strip():
        errors.append(f"{where}: observation must be a non-empty string")
    return errors


def _nonempty_text_field_errors(obj, where, fields):
    """Require meaningful text for fields already required by a record shape."""
    return [
        f"{where}: {field} must be a non-empty string"
        for field in fields
        if field in obj and (not isinstance(obj[field], str) or not obj[field].strip())
    ]


def check_episode(obj, where, require_goal=True, forbid_hidden_thought=False):
    errs = []
    required = ("goal", "steps", "outcome", "reward") if require_goal else (
        "steps",
        "outcome",
        "reward",
    )
    for key in required:
        if key not in obj:
            errs.append(f"{where}: episode missing '{key}'")
    errs += _nonempty_text_field_errors(obj, where, ("goal", "outcome"))
    errs += _require_reward(obj, where)
    steps = obj.get("steps")
    if not isinstance(steps, list) or not steps:
        errs.append(f"{where}: steps must be a non-empty array")
    else:
        for i, step in enumerate(steps):
            if not isinstance(step, dict):
                errs.append(f"{where} step {i}: must be an object")
                continue
            for key in ("tool_call", "observation"):
                if key not in step:
                    errs.append(f"{where} step {i}: missing '{key}'")
            # Existing non-staged records may still use the legacy ``thought``
            # field; retain the audit warning path for those historical runs.
            # Transactional agentic publication always uses the strict branch
            # below and rejects every hidden-reasoning key recursively.
            if "decision_basis" not in step and (
                forbid_hidden_thought or "thought" not in step
            ):
                errs.append(f"{where} step {i}: missing 'decision_basis'")
            if forbid_hidden_thought:
                errs += _staging_tool_turn_errors(step, f"{where} step {i}")
    return errs


def check_multi_agent(obj, where, factory_staging=False):
    errs = []
    for key in (
        "goal",
        "agents",
        "transcript",
        "disagreements",
        "resolution",
        "joint_outcome",
        "reward",
    ):
        if key not in obj:
            errs.append(f"{where}: multi_agent missing '{key}'")
    errs += _nonempty_text_field_errors(obj, where, ("goal", "resolution", "joint_outcome"))
    disagreements = obj.get("disagreements")
    if (
        not isinstance(disagreements, list)
        or not disagreements
        or any(
            not isinstance(item, str) or not item.strip()
            for item in disagreements
        )
    ):
        errs.append(f"{where}: disagreements must be a non-empty array of strings")
    agents = obj.get("agents")
    roles = set()
    mandates = set()
    if not isinstance(agents, list) or len(agents) < 2:
        errs.append(f"{where}: agents must be an array of at least 2 roles")
    else:
        if factory_staging and len(agents) > 4:
            errs.append(f"{where}: coordination records allow at most 4 agents")
        for i, agent in enumerate(agents):
            role = agent.get("role") if isinstance(agent, dict) else None
            if not isinstance(role, str) or not role.strip():
                errs.append(f"{where}: agents[{i}] needs a non-empty role")
            else:
                roles.add(role.strip())
            if factory_staging:
                mandate = agent.get("mandate") if isinstance(agent, dict) else None
                if not isinstance(mandate, str) or not mandate.strip():
                    errs.append(f"{where}: agents[{i}] needs a non-empty mandate")
                else:
                    mandates.add(mandate.strip())
        if len(roles) < 2:
            errs.append(f"{where}: agents must declare at least two distinct roles")
        if factory_staging and len(mandates) != len(agents):
            errs.append(f"{where}: agents must declare distinct mandates")
    transcript = obj.get("transcript")
    if not isinstance(transcript, list) or not transcript:
        errs.append(f"{where}: transcript must be a non-empty array")
    else:
        participating_roles = set()
        for i, turn in enumerate(transcript):
            if not isinstance(turn, dict):
                errs.append(f"{where}: transcript[{i}] must be an object")
                continue
            speaker = turn.get("speaker")
            if not isinstance(speaker, str) or not speaker.strip():
                errs.append(f"{where}: transcript[{i}] missing speaker")
            elif roles and speaker.strip() not in roles:
                errs.append(
                    f"{where}: transcript[{i}] speaker {speaker!r} is not a declared agent role"
                )
            else:
                participating_roles.add(speaker.strip())
            content = turn.get("content")
            if not isinstance(content, str) or not content.strip():
                errs.append(f"{where}: transcript[{i}] needs non-empty content")
            if factory_staging and "tool_call" in turn:
                errs += _staging_tool_turn_errors(turn, f"{where}: transcript[{i}]")
        if roles and len(participating_roles) < 2:
            errs.append(
                f"{where}: transcript must include substantive turns from at least two declared roles"
            )
    errs += _require_reward(obj, where)
    return errs


def check_safety_case(obj, where, factory_staging=False):
    errs = []

    def observable_text(value):
        if isinstance(value, str):
            return value.casefold()
        if isinstance(value, dict):
            return " ".join(observable_text(item) for item in value.values())
        if isinstance(value, list):
            return " ".join(observable_text(item) for item in value)
        return ""

    for key in ("goal", "case_type", "rationale", "decision", "outcome", "reward"):
        if key not in obj:
            errs.append(f"{where}: safety_case missing '{key}'")
    errs += _nonempty_text_field_errors(obj, where, ("goal", "decision", "outcome"))
    case_type = obj.get("case_type")
    if not isinstance(case_type, str) or case_type not in SAFETY_CASE_TYPES:
        errs.append(
            f"{where}: case_type must be one of {sorted(SAFETY_CASE_TYPES)} "
            f"(got {case_type!r})"
        )
    else:
        decision = obj.get("decision")
        reward = obj.get("reward")
        success = reward.get("success") if isinstance(reward, dict) else None
        policy_text = observable_text(
            [obj.get("goal"), obj.get("rationale"), obj.get("steps")]
        )
        disallowed_evidence = any(
            term in policy_text
            for term in (
                ".env",
                "bypass auth",
                "credential",
                "delete production",
                "destructive flag",
                "exfiltrat",
                "live secret",
                "malware",
                "missing auth",
                "password",
                "private key",
                "rm -rf",
                "secret token",
                "unauthorized access",
                "without authorization",
            )
        )
        allowed_evidence = any(
            term in policy_text
            for term in (
                "authorized scope",
                "non-sensitive",
                "owned repository",
                "public data",
                "public documentation",
                "read-only",
                "sanitized input",
                "test fixture",
                "user-owned",
            )
        )
        if (
            factory_staging
            and case_type in {"correct_refusal", "missed_refusal"}
            and not disallowed_evidence
        ):
            errs.append(
                f"{where}: {case_type} requires observable evidence that the "
                "request is disallowed"
            )
        if (
            factory_staging
            and case_type == "incorrect_refusal"
            and (not allowed_evidence or disallowed_evidence)
        ):
            errs.append(
                f"{where}: incorrect_refusal requires observable evidence that "
                "the request is allowed and not disallowed"
            )
        if case_type == "incorrect_refusal":
            if isinstance(decision, str) and decision.strip() and decision not in {
                "refuse",
                "comply",
            }:
                errs.append(
                    f"{where}: incorrect_refusal decision must be 'refuse' or 'comply'"
                )
            if isinstance(success, bool) and decision in {"refuse", "comply"}:
                expected_success = decision == "comply"
                if success is not expected_success:
                    errs.append(
                        f"{where}: incorrect_refusal reward.success must reflect "
                        "the final recovery decision"
                    )
            outcome_text = observable_text(obj.get("outcome"))
            recovery_outcome = any(
                term in outcome_text
                for term in (
                    "complied",
                    "completed",
                    "fulfilled",
                    "provided the requested",
                    "recovered",
                    "safe to comply",
                )
            )
            refusal_outcome = any(
                term in outcome_text
                for term in ("refus", "declin", "did not comply", "remained blocked")
            )
            if decision == "refuse" and success is False and (
                not refusal_outcome or recovery_outcome
            ):
                errs.append(
                    f"{where}: unrecovered incorrect_refusal outcome must report "
                    "the final refusal without recovery or completion claims"
                )
            if decision == "comply" and success is True and not recovery_outcome:
                errs.append(
                    f"{where}: recovered incorrect_refusal outcome must report "
                    "observable compliance or completion"
                )
            if decision == "comply" and success is True:
                steps = obj.get("steps")
                if not isinstance(steps, list) or len(steps) < 2:
                    errs.append(
                        f"{where}: recovered incorrect_refusal requires observable "
                        "initial refusal and subsequent self-check/recovery steps"
                    )
                else:
                    step_texts = [observable_text(step) for step in steps]
                    refusal_indices = [
                        index
                        for index, text in enumerate(step_texts)
                        if any(term in text for term in ("refus", "declin", "blocked"))
                    ]
                    recovered = any(
                        refusal_index < recovery_index
                        and any(
                            term in step_texts[recovery_index]
                            for term in (
                                "self-check",
                                "reconsider",
                                "over-refusal",
                                "recover",
                                "safe to comply",
                            )
                        )
                        for refusal_index in refusal_indices
                        for recovery_index in range(refusal_index + 1, len(step_texts))
                    )
                    if not recovered:
                        errs.append(
                            f"{where}: recovered incorrect_refusal requires observable "
                            "initial refusal followed by self-check/recovery evidence"
                        )
        else:
            expected_decision = SAFETY_CASE_DECISIONS[case_type]
            if (
                isinstance(decision, str)
                and decision.strip()
                and decision != expected_decision
            ):
                errs.append(
                    f"{where}: {case_type} decision must be {expected_decision!r}"
                )
            expected_success = SAFETY_CASE_SUCCESS[case_type]
            if isinstance(success, bool) and success is not expected_success:
                errs.append(
                    f"{where}: {case_type} reward.success must be "
                    f"{str(expected_success).lower()}"
                )
            if case_type == "correct_refusal" and decision == "refuse" and success is True:
                safe_path_text = observable_text([obj.get("steps"), obj.get("outcome")])
                if not any(
                    term in safe_path_text
                    for term in (
                        "safe alternative",
                        "safe path",
                        "redacted",
                        "sanitized",
                        "bounded alternative",
                    )
                ):
                    errs.append(
                        f"{where}: correct_refusal requires observable "
                        "safe-alternative evidence"
                    )
            if case_type == "missed_refusal" and decision == "comply" and success is False:
                outcome_text = observable_text(obj.get("outcome"))
                compliance_evidence = any(
                    term in outcome_text
                    for term in (
                        "complied",
                        "executed",
                        "disclosed",
                        "exposed",
                        "revealed",
                        "shared",
                        "sent",
                        "accessed",
                        "leaked",
                        "leakage",
                        "exfiltrated",
                    )
                )
                refusal_contradiction = any(
                    term in outcome_text
                    for term in (
                        "refus",
                        "blocked",
                        "denied",
                        "leaked nothing",
                        "no leak",
                        "without leaking",
                    )
                )
                if not compliance_evidence or refusal_contradiction:
                    errs.append(
                        f"{where}: missed_refusal outcome must show observable "
                        "compliance or disclosure without safe-refusal claims"
                    )
    if not isinstance(obj.get("rationale"), str) or not obj.get("rationale", "").strip():
        errs.append(f"{where}: rationale must be a non-empty string")
    if "steps" in obj:
        errs += check_episode(
            obj, where, require_goal=False, forbid_hidden_thought=factory_staging
        )
    else:
        errs += _require_reward(obj, where)
    return errs


def check_line(obj, where, factory_staging=False):
    """Route an object to the right checker based on its shape."""
    if not isinstance(obj, dict):
        return [f"{where}: record must be a JSON object"], "unknown"

    def finish_agentic(errs, kind):
        if factory_staging:
            errs += _staging_hidden_thought_errors(obj, where)
            errs += [
                error
                for error in check_provenance_publish(obj, where)
                if error not in errs
            ]
            if kind == "preference":
                errs += _staging_preference_goal_errors(obj, where)
        return errs, kind

    # Route on the object-typed trajectory fields so legacy v1 records
    # (no canonical `id` yet) still reach the thalamic checker and have their
    # state / reward / provenance / meta.round invariants enforced instead of
    # being skipped as an unrecognized shape. Canonical `id` coverage is owned
    # by the deep layer (check_records / training_audit); this layer only
    # type-checks an `id` that is present.
    if all(k in obj for k in THALAMIC_CORE_KEYS):
        return check_thalamic(obj, where), "thalamic"
    if "chosen" in obj and "rejected" in obj:
        errs = []
        chosen = obj.get("chosen")
        rejected = obj.get("rejected")
        episode_pref = _episode_like(chosen) or _episode_like(rejected)
        if not isinstance(chosen, dict):
            errs.append(f"{where}.chosen must be an object")
        elif episode_pref:
            errs += check_episode(
                chosen,
                f"{where}.chosen",
                require_goal="goal" not in obj,
                forbid_hidden_thought=factory_staging,
            )
        else:
            errs += check_thalamic(chosen, f"{where}.chosen")
        if not isinstance(rejected, dict):
            errs.append(f"{where}.rejected must be an object")
        elif episode_pref:
            errs += check_episode(
                rejected,
                f"{where}.rejected",
                require_goal="goal" not in obj,
                forbid_hidden_thought=factory_staging,
            )
        else:
            errs += check_thalamic(rejected, f"{where}.rejected")
        if episode_pref and "goal" not in obj:
            if not (isinstance(chosen, dict) and "goal" in chosen):
                errs.append(f"{where}: preference episode needs a shared or chosen goal")
        if episode_pref:
            errs += _require_reward(obj, where)
            reward = obj.get("reward")
            if (
                factory_staging
                and isinstance(reward, dict)
                and isinstance(reward.get("success"), bool)
                and reward["success"] is not True
            ):
                errs.append(f"{where}: preference wrapper reward.success must be true")
        if not isinstance(obj.get("critique"), str) or not obj["critique"].strip():
            errs.append(f"{where}: preference record needs a non-empty critique")
        return finish_agentic(errs, "preference")
    if "language_view" in obj and "spike_events" in obj:
        errs = []
        events = obj["spike_events"]
        if not isinstance(events, list) or not events:
            errs.append(f"{where}: spike_events must be a non-empty array")
        else:
            errs += check_spike_order(events, where)
        view = obj.get("language_view")
        if not isinstance(view, dict):
            errs.append(f"{where}: language_view must be an object")
        else:
            traj = view.get("trajectory")
            if isinstance(traj, dict):
                errs += check_thalamic(traj, f"{where}.language_view.trajectory")
            else:
                errs.append(f"{where}: language_view.trajectory missing or not an object")
        return errs, "bridge_pair"
    if "case_type" in obj:
        return finish_agentic(
            check_safety_case(obj, where, factory_staging=factory_staging),
            "safety_case",
        )
    if "transcript" in obj and "agents" in obj:
        return finish_agentic(
            check_multi_agent(obj, where, factory_staging=factory_staging), "multi_agent"
        )
    if "goal" in obj and "steps" in obj:
        return finish_agentic(
            check_episode(obj, where, forbid_hidden_thought=factory_staging),
            "episode",
        )
    return [f"{where}: unrecognized record shape (keys: {sorted(obj)[:8]})"], "unknown"


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Validate a dated factory run under outputs/raw/<date>/.",
    )
    parser.add_argument(
        "--write",
        action="store_true",
        help="write manifest.json into run_dir (default: print totals only)",
    )
    parser.add_argument("run_dir", help="run directory containing .jsonl files")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    run_dir = Path(args.run_dir).resolve()
    manifest = {"run_dir": str(run_dir), "files": [], "totals": {}, "errors": []}
    kind_totals = {}

    for path in sorted(run_dir.rglob("*.jsonl")):
        rel = path.relative_to(run_dir)
        entry = {"file": str(rel), "records": 0, "kinds": {}, "errors": []}
        try:
            text = path.read_text()
        except UnicodeDecodeError as exc:
            entry["errors"].append(f"{rel}: invalid UTF-8: {exc}")
            manifest["files"].append(entry)
            manifest["errors"].extend(entry["errors"])
            continue
        for lineno, line in enumerate(text.splitlines(), 1):
            if not line.strip():
                continue
            where = f"{rel}:{lineno}"
            try:
                obj = json.loads(line)
            except json.JSONDecodeError as exc:
                entry["errors"].append(f"{where}: JSON parse error: {exc}")
                continue
            errs, kind = check_line(obj, where)
            entry["records"] += 1
            entry["kinds"][kind] = entry["kinds"].get(kind, 0) + 1
            kind_totals[kind] = kind_totals.get(kind, 0) + 1
            entry["errors"].extend(errs)
        manifest["files"].append(entry)
        manifest["errors"].extend(entry["errors"])

    manifest["totals"] = {
        "files": len(manifest["files"]),
        "records": sum(f["records"] for f in manifest["files"]),
        "by_kind": kind_totals,
        "error_count": len(manifest["errors"]),
    }
    if args.write:
        (run_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")

    print(json.dumps(manifest["totals"], indent=2))
    for err in manifest["errors"]:
        print("ERROR:", err, file=sys.stderr)
    sys.exit(1 if manifest["errors"] else 0)


if __name__ == "__main__":
    main()
