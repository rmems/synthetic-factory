#!/usr/bin/env python3
"""Execution-grounded verification for synthetic-factory records.

Distinguishes verified / inconclusive / failed. Never treats
`cannot-verify` as `verified` (Ouroboros #1991, Codex #37278).

Frontier gate integration:
  pipelines/round_txn.py owns the frontier commit point
  (ROUND-rNN.complete.json). Execution verification is a live co-gate:
  round_txn.validate_stage() calls verify_batch_for_frontier(strict=True)
  through round_txn.execution_gate() and refuses to publish while any
  record is failed or inconclusive. round_txn remains the commit-point
  owner; verify_execution remains the source of truth for
  verified / inconclusive / failed. See docs/verify-execution.md.

Usage:
  python3 pipelines/verify_execution.py <run_dir> [--strict]
  python3 pipelines/verify_execution.py --record <jsonl> --line N
  # frontier gate (import hook, no CLI coupling):
  #   from verify_execution import verify_batch_for_frontier
  #   counts, findings, blocked = verify_batch_for_frontier(batch_path, strict=True)

Co-authored-by: Muse Code powered by Muse Spark <muse-spark@meta.com>
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

# Reuse the existing validator vocabulary as ground truth.
try:
    from check_records import ALLOWED_SIM_OR_REAL
except ImportError:  # pragma: no cover - depends on sys.path of the caller
    print(
        "verify_execution: check_records unavailable — falling back to the "
        "built-in state.sim_or_real set",
        file=sys.stderr,
    )
    ALLOWED_SIM_OR_REAL = frozenset({"designed", "simulated", "hil"})

try:
    from validate_run import (
        THALAMIC_CORE_KEYS,
        check_episode,
        check_line,
        check_safety_case,
    )
except ImportError:  # pragma: no cover - publish imports from the repo tree
    THALAMIC_CORE_KEYS = (
        "state",
        "proposed_action",
        "safety_decision",
        "executed_action",
        "future_outcome",
        "reward_components",
    )
    check_episode = None
    check_line = None
    check_safety_case = None


KNOWN_TOOLS = frozenset({
    "bash", "read_file", "edit_file", "write_file", "search",
    "gh", "kubectl", "gate-cli", "tofu", "tenv", "tflint", "aws", "jq", "hcl2json",
    # safety-calibration-factory records a refusal as a first-class step with a
    # decision_basis and an observation; the refusal itself is the observable
    # outcome, so it is verifiable rather than cannot-verify.
    "refuse",
})

OBSERVABLE_OUTCOME_METRICS = frozenset({
    "divergence_detected_ms",
    "latency_ms",
    "min_clearance_m",
    "reward_inflection_t_us",
    "slip_arrested_ms",
})
NONNEGATIVE_OUTCOME_METRICS = OBSERVABLE_OUTCOME_METRICS - {"min_clearance_m"}

# ---------------------------------------------------------------------------
# Frontier gate — integration with pipelines/round_txn.py
# ---------------------------------------------------------------------------
# pipelines/round_txn.py:validate_stage() is the training-ready gate that
# runs check_jsonl() and quota checks before publish() links
# ROUND-rNN.complete.json. Execution verification is a live co-gate there:
# a round must not become visible to frontier readers when its records lack
# observable execution evidence.
#
# Live call site (pipelines/round_txn.py:execution_gate, invoked from
# validate_stage() after the envelope check):
#
#   verify_batch_for_frontier = load_execution_verifier()
#   counts, findings, blocked = verify_batch_for_frontier(batch, strict=True)
#   # failed        -> TransactionError, never waivable
#   # inconclusive  -> TransactionError unless the operator passed
#   #                  --allow-inconclusive "<reason>", which is recorded in
#   #                  ROUND-rNN.complete.json
#
# publish() links ROUND-rNN.complete.json only if both gates pass, so an
# unverifiable round cannot advance frontier_status().next_round.
#
# This keeps a clean separation: round_txn owns the atomic commit point
# and filesystem invariants; verify_execution owns the verified /
# inconclusive / failed taxonomy and never promotes cannot-verify.
# The import is on-demand so verify_execution can audit any run_dir without a
# round_txn reservation — but a missing verifier fails the publish closed
# rather than skipping the gate.
#
# See docs/verify-execution.md for the full contract, strict vs non-strict
# semantics, the waiver format, and the test matrix.
# ---------------------------------------------------------------------------


def verify_episode_steps(steps, _where):
    """Verify coding episode steps have observable execution evidence."""
    if not isinstance(steps, list) or not steps:
        return "failed", "steps missing or empty"
    inconclusive_reasons = []
    for i, step in enumerate(steps):
        if not isinstance(step, dict):
            return "failed", f"step {i} not an object"
        tool = step.get("tool_call")
        obs = step.get("observation")
        basis = step.get("decision_basis")
        thought = step.get("thought")

        # Hidden thought without observable basis is inconclusive, not verified
        if thought is not None and basis is None:
            inconclusive_reasons.append(f"step {i} has hidden thought without decision_basis")

        if isinstance(tool, dict):
            name = tool.get("name")
        elif isinstance(tool, str) and tool.strip():
            # Curated coding episodes keep a visible string tool call
            # (pipelines/curate_coding.py); the shape validator accepts it, so
            # normalize to its leading token rather than blocking the record.
            name = tool.strip().split()[0]
        else:
            inconclusive_reasons.append(f"step {i} missing tool_call")
            continue
        if name not in KNOWN_TOOLS:
            inconclusive_reasons.append(f"step {i} unknown tool {name!r}")
        if not isinstance(obs, str) or not obs.strip():
            # Observation is the execution evidence; missing = cannot-verify
            inconclusive_reasons.append(f"step {i} missing observation")
    if inconclusive_reasons:
        return "inconclusive", "; ".join(inconclusive_reasons[:3])
    return "verified", "all steps have tool_call + observation + decision_basis"


def _step_index_from_shape_error(error, where):
    prefix = f"{where} step "
    if not error.startswith(prefix):
        return None
    index_text, separator, _tail = error[len(prefix) :].partition(":")
    if not separator:
        return None
    try:
        return int(index_text.strip())
    except ValueError:
        return None


def _omitted_tool_call_type_error(error, where, obj):
    """True when a type error is only the companion of an omitted tool_call."""
    if not error.endswith(": tool_call must be an object"):
        return False
    if not isinstance(obj, dict):
        return False
    index = _step_index_from_shape_error(error, where)
    steps = obj.get("steps")
    if index is None:
        return False
    if not isinstance(steps, list):
        return False
    if index < 0 or index >= len(steps):
        return False
    step = steps[index]
    if not isinstance(step, dict):
        return False
    return "tool_call" not in step


def _is_missing_execution_evidence(error, where, obj=None):
    """Return whether a shape error belongs to the cannot-verify taxonomy.

    Strict-turn checking emits both ``missing 'tool_call'`` and
    ``tool_call must be an object`` when the key is omitted. Suppress the
    companion type error only for an absent key so a present malformed
    ``tool_call`` remains a structural failure.
    """
    if not error.startswith(f"{where} step "):
        return False
    if error.endswith(
        (
            ": missing 'tool_call'",
            ": missing 'observation'",
            ": observation must be a non-empty string",
        )
    ):
        return True
    return _omitted_tool_call_type_error(error, where, obj)


def verify_episode(obj, where, *, require_goal=True, strict_turns=False):
    """Validate an episode envelope before accepting its step evidence.

    ``validate_run.check_episode`` owns the repository's episode shape. Its
    per-step execution-evidence findings remain the responsibility of
    ``verify_episode_steps`` so a missing observation stays ``inconclusive``
    rather than being promoted to a structural failure.
    """
    if not isinstance(obj, dict):
        return "failed", f"{where} episode is not an object"
    if check_episode is None:
        return "failed", "episode shape checker unavailable"
    shape_errors = [
        error
        for error in check_episode(
            obj,
            where,
            require_goal=require_goal,
            forbid_hidden_thought=strict_turns,
        )
        if not _is_missing_execution_evidence(error, where, obj)
    ]
    if shape_errors:
        return "failed", f"episode shape invalid: {shape_errors[0]}"
    return verify_episode_steps(obj.get("steps"), where)


_REFUSAL_TOOL_NAMES = frozenset({"block", "decline", "deny", "refuse"})
_REFUSAL_OBSERVATION_MARKERS = ("blocked", "declined", "denied", "refus")
_COMPLIANCE_OBSERVATION_MARKERS = (
    "complied",
    "disclosed",
    "exfiltrat",
    "exposed",
    "leaked",
    "leakage",
    "revealed",
)
_COMPLIANCE_OR_LEAKAGE_DECISIONS = frozenset(
    {"comply", "disclose", "leak", "leakage"}
)
_REFUSAL_CASE_TYPES = frozenset({"correct_refusal"})


def _tool_call_name(tool):
    if isinstance(tool, dict):
        name = tool.get("name")
        return name.strip().casefold() if isinstance(name, str) else ""
    if isinstance(tool, str) and tool.strip():
        return tool.strip().split()[0].casefold()
    return ""


def _step_observation_text(step):
    if not isinstance(step, dict):
        return ""
    observation = step.get("observation")
    return observation.casefold() if isinstance(observation, str) else ""


def _observation_has_marker(text, markers):
    return any(marker in text for marker in markers)


def _step_records_refusal(step):
    """True when a step's known refuse action is also observed as a refusal."""
    if not isinstance(step, dict):
        return False
    if _tool_call_name(step.get("tool_call")) not in _REFUSAL_TOOL_NAMES:
        return False
    return _observation_has_marker(
        _step_observation_text(step), _REFUSAL_OBSERVATION_MARKERS
    )


def _step_records_compliance(step):
    """True when a non-refusal step observes compliance or leakage."""
    if not isinstance(step, dict):
        return False
    if _tool_call_name(step.get("tool_call")) in _REFUSAL_TOOL_NAMES:
        return False
    return _observation_has_marker(
        _step_observation_text(step), _COMPLIANCE_OBSERVATION_MARKERS
    )


def _calibrated_outcome_is_compliance_or_leakage(obj):
    """Return whether the training label is compliance or leakage, not refusal.

    Recovered ``incorrect_refusal`` uses ``decision=comply`` after an initial
    refuse step, so it is not this contradiction. ``missed_refusal`` is the
    calibrated leakage/compliance label and must not carry refuse evidence.
    """
    if not isinstance(obj, dict):
        return False
    case_type = obj.get("case_type")
    if case_type == "incorrect_refusal":
        return False
    if case_type == "missed_refusal":
        return True
    decision = obj.get("decision")
    if not isinstance(decision, str):
        return False
    return decision.strip().casefold() in _COMPLIANCE_OR_LEAKAGE_DECISIONS


def _calibrated_outcome_is_refusal(obj):
    """Return whether the training label is a refusal, not recovered compliance."""
    if not isinstance(obj, dict):
        return False
    case_type = obj.get("case_type")
    if case_type in _REFUSAL_CASE_TYPES:
        return True
    if case_type != "incorrect_refusal":
        return False
    decision = obj.get("decision")
    if not isinstance(decision, str):
        return False
    return decision.strip().casefold() == "refuse"


def _safety_step_contradicts_calibrated_outcome(obj, where):
    steps = obj.get("steps")
    if not isinstance(steps, list):
        return None
    refuse_label = _calibrated_outcome_is_refusal(obj)
    comply_label = _calibrated_outcome_is_compliance_or_leakage(obj)
    if refuse_label:
        for index, step in enumerate(steps):
            if _step_records_compliance(step):
                return (
                    "failed",
                    f"{where} safety step {index} records compliance or leakage "
                    "evidence that contradicts the calibrated refusal outcome",
                )
        return None
    if not comply_label:
        return None
    for index, step in enumerate(steps):
        if _step_records_refusal(step):
            return (
                "failed",
                f"{where} safety step {index} records refuse/refused evidence "
                "that contradicts the calibrated compliance or leakage outcome",
            )
    return None


def _safety_refusal_contradicts_calibrated_outcome(obj, where):
    """Backward-compatible alias for the bidirectional safety-step check."""
    return _safety_step_contradicts_calibrated_outcome(obj, where)


def verify_safety_episode(obj, where):
    """Validate the safety-case envelope before accepting its step evidence."""
    if check_safety_case is None or check_episode is None:
        return "failed", "safety-case shape checker unavailable"
    errors = [
        *check_safety_case(obj, where, factory_staging=True),
        *check_episode(
            obj,
            where,
            require_goal=False,
            forbid_hidden_thought=True,
        ),
    ]
    shape_errors = [
        error
        for error in dict.fromkeys(errors)
        if not _is_missing_execution_evidence(error, where, obj)
    ]
    if shape_errors:
        return "failed", f"safety-case shape invalid: {shape_errors[0]}"
    contradiction = _safety_step_contradicts_calibrated_outcome(obj, where)
    if contradiction is not None:
        return contradiction
    return verify_episode_steps(obj.get("steps"), where)


def _nonempty_string_or_object(value):
    if isinstance(value, dict):
        return bool(value)
    if not isinstance(value, str):
        return False
    return bool(value.strip())


def _sequence_entries_are_objects(value):
    return all(isinstance(item, dict) and item for item in value)


def _sequence_entries_are_text_or_objects(value):
    return all(_nonempty_string_or_object(item) for item in value)


def _malformed_outcome_array(value, field, *, objects_only):
    if not isinstance(value, list):
        return f"future_outcome.{field} must be an array"
    if not value:
        return None
    if objects_only and not _sequence_entries_are_objects(value):
        return f"future_outcome.{field} entries must be objects"
    if not objects_only and not _sequence_entries_are_text_or_objects(value):
        return (
            f"future_outcome.{field} entries must be non-empty strings or objects"
        )
    return None


def _append_if_truthy(observable_fields, field, value):
    if value:
        observable_fields.append(field)
    return None


def _collect_timeline(fo, observable_fields):
    if "timeline" not in fo:
        return None
    value = fo["timeline"]
    error = _malformed_outcome_array(value, "timeline", objects_only=True)
    if error:
        return error
    return _append_if_truthy(observable_fields, "timeline", value)


def _collect_observed_effects(fo, observable_fields):
    if "observed_effects" not in fo:
        return None
    value = fo["observed_effects"]
    error = _malformed_outcome_array(value, "observed_effects", objects_only=False)
    if error:
        return error
    return _append_if_truthy(observable_fields, "observed_effects", value)


def _collect_new_state(fo, observable_fields):
    if "new_state" not in fo:
        return None
    value = fo["new_state"]
    if not isinstance(value, dict):
        return "future_outcome.new_state must be an object"
    return _append_if_truthy(observable_fields, "new_state", value)


def _collect_state_delta(fo, observable_fields):
    value = fo.get("state_delta")
    if value is None:
        return None
    if isinstance(value, dict):
        return _append_if_truthy(observable_fields, "state_delta", value)
    if isinstance(value, list):
        error = _malformed_outcome_array(value, "state_delta", objects_only=False)
        if error:
            return error
        return _append_if_truthy(observable_fields, "state_delta", value)
    return "future_outcome.state_delta must be an object or array"


def _collect_surprises(fo, observable_fields):
    value = fo.get("surprises")
    if value is None:
        return None
    error = _malformed_outcome_array(value, "surprises", objects_only=False)
    if error:
        return error
    return _append_if_truthy(observable_fields, "surprises", value)


def _collect_named_events(fo, observable_fields):
    for field in ("hazard_avoided", "incident"):
        value = fo.get(field)
        if value is None:
            continue
        if not _nonempty_string_or_object(value):
            return f"future_outcome.{field} must be a non-empty string or object"
        observable_fields.append(field)
    return None


def _finite_number(value):
    if isinstance(value, bool):
        return False
    if not isinstance(value, (int, float)):
        return False
    try:
        return math.isfinite(value)
    except OverflowError:
        return False


def _collect_outcome_metrics(fo, observable_fields):
    for field in OBSERVABLE_OUTCOME_METRICS:
        if field not in fo:
            continue
        value = fo[field]
        if not _finite_number(value):
            return f"future_outcome.{field} must be a finite number"
        if field in NONNEGATIVE_OUTCOME_METRICS:
            if value < 0:
                return f"future_outcome.{field} must be a non-negative finite number"
        observable_fields.append(field)
    return None


def _future_outcome_evidence(fo):
    observable_fields = []
    collectors = (
        _collect_timeline,
        _collect_observed_effects,
        _collect_new_state,
        _collect_state_delta,
        _collect_surprises,
        _collect_named_events,
        _collect_outcome_metrics,
    )
    for collector in collectors:
        error = collector(fo, observable_fields)
        if error:
            return observable_fields, error
    return observable_fields, None


def _thalamic_core_verdict(obj, where):
    """Return an early verdict, or None when the core envelope is usable."""
    # Callers include the bridge path, which can hand us a non-object
    # language_view.trajectory. Return a verdict rather than raising.
    if not isinstance(obj, dict):
        return "inconclusive", f"{where} is not an object — cannot verify"
    state = obj.get("state", {})
    prov = state.get("sim_or_real") if isinstance(state, dict) else None
    if prov not in ALLOWED_SIM_OR_REAL:
        return (
            "inconclusive",
            f"non-training provenance {prov!r} on {where}.state.sim_or_real",
        )
    sd = obj.get("safety_decision", {})
    # A non-string rationale (object/number/null) must not raise here — this
    # gate runs over untrusted generated records and a crash would take down
    # the frontier check instead of returning a verdict.
    rationale = sd.get("rationale") if isinstance(sd, dict) else None
    if not isinstance(rationale, str) or not rationale.strip():
        return "failed", "missing safety_decision.rationale"
    fo = obj.get("future_outcome")
    if not isinstance(fo, dict):
        return "inconclusive", "future_outcome not an object — cannot verify outcome"
    return None


def verify_thalamic(obj, where):
    """Thalamic record: needs provenance + gate rationale + future outcome that is not hallucinated."""
    core = _thalamic_core_verdict(obj, where)
    if core is not None:
        return core
    observable_fields, error = _future_outcome_evidence(obj["future_outcome"])
    if error:
        return "failed", error
    # Narrative-only or empty outcome containers are cannot-verify, not proof.
    if not observable_fields:
        return "inconclusive", "future_outcome lacks observable execution evidence"
    return "verified", "thalamic checks pass"


def _combine_preference_side_verdicts(first, second):
    status_one, reason_one = first
    status_two, reason_two = second
    if status_one == "failed":
        return "failed", f"preference side failed: {reason_one}"
    if status_two == "failed":
        return "failed", f"preference side failed: {reason_two}"
    if status_one == "inconclusive":
        return "inconclusive", f"preference side inconclusive: {reason_one}"
    if status_two == "inconclusive":
        return "inconclusive", f"preference side inconclusive: {reason_two}"
    return "verified", "both preference sides verified"


def _side_is_thalamic(side):
    if not isinstance(side, dict):
        return False
    return all(key in side for key in THALAMIC_CORE_KEYS)


def _side_is_episode(side):
    if not isinstance(side, dict):
        return False
    if "steps" not in side:
        return False
    return not _side_is_thalamic(side)


def _preference_wrapper_verdict(obj, where):
    if check_line is None:
        return "failed", "preference shape checker unavailable"
    wrapper_errors, wrapper_kind = check_line(
        obj,
        where,
        factory_staging=True,
    )
    wrapper_errors = [
        error
        for error in wrapper_errors
        if not any(
            _is_missing_execution_evidence(error, f"{where}.{side}", obj.get(side))
            for side in ("chosen", "rejected")
        )
    ]
    if wrapper_kind != "preference":
        return "failed", "preference wrapper was not classified as a preference"
    if wrapper_errors:
        return "failed", f"preference wrapper invalid: {wrapper_errors[0]}"
    return None


def _shared_preference_goal_is_blank(obj):
    if "goal" not in obj:
        return False
    goal = obj["goal"]
    if not isinstance(goal, str):
        return True
    return not goal.strip()


def _verify_episode_preference_sides(obj, where, chosen, rejected):
    if _shared_preference_goal_is_blank(obj):
        return "failed", "preference shared goal must be a non-empty string"
    require_side_goal = "goal" not in obj
    return _combine_preference_side_verdicts(
        verify_episode(
            chosen,
            f"{where}.chosen",
            require_goal=require_side_goal,
            strict_turns=True,
        ),
        verify_episode(
            rejected,
            f"{where}.rejected",
            require_goal=require_side_goal,
            strict_turns=True,
        ),
    )


def _verify_preference_sides(obj, where, chosen, rejected):
    chosen_episode = _side_is_episode(chosen)
    rejected_episode = _side_is_episode(rejected)
    if chosen_episode:
        if not rejected_episode:
            return "failed", "preference sides mix episode and Thalamic shapes"
        return _verify_episode_preference_sides(obj, where, chosen, rejected)
    if rejected_episode:
        return "failed", "preference sides mix episode and Thalamic shapes"
    chosen_thalamic = _side_is_thalamic(chosen)
    rejected_thalamic = _side_is_thalamic(rejected)
    if chosen_thalamic:
        if not rejected_thalamic:
            return "failed", "preference sides mix or omit required shape fields"
        return _combine_preference_side_verdicts(
            verify_record_execution(chosen, f"{where}.chosen"),
            verify_record_execution(rejected, f"{where}.rejected"),
        )
    if rejected_thalamic:
        return "failed", "preference sides mix or omit required shape fields"
    return "failed", "preference sides are not episode or Thalamic records"


def _verify_preference_execution(obj, where):
    wrapper = _preference_wrapper_verdict(obj, where)
    if wrapper is not None:
        return wrapper
    chosen = obj.get("chosen")
    rejected = obj.get("rejected")
    if not isinstance(chosen, dict):
        return "failed", "preference sides must both be objects"
    if not isinstance(rejected, dict):
        return "failed", "preference sides must both be objects"
    return _verify_preference_sides(obj, where, chosen, rejected)


def _verify_bridge_execution(obj, where):
    language_view = obj.get("language_view")
    traj = (
        language_view.get("trajectory", {})
        if isinstance(language_view, dict)
        else {}
    )
    if traj:
        return verify_thalamic(traj, f"{where}.language_view.trajectory")
    return "inconclusive", "bridge missing language_view.trajectory"


def verify_record_execution(obj, where="record"):
    """Return (status, reason) in {verified, inconclusive, failed}."""
    if not isinstance(obj, dict):
        return "failed", "not an object"
    if all(k in obj for k in THALAMIC_CORE_KEYS):
        return verify_thalamic(obj, where)
    if "chosen" in obj and "rejected" in obj:
        return _verify_preference_execution(obj, where)
    if "language_view" in obj and "spike_events" in obj:
        return _verify_bridge_execution(obj, where)
    # Safety-calibration records have their own envelope checker. Ordinary
    # standalone episodes must carry their own goal, while preference sides
    # are routed above with the wrapper's shared-goal context.
    if "steps" in obj:
        if "case_type" in obj:
            return verify_safety_episode(obj, where)
        return verify_episode(obj, where)
    return "inconclusive", f"unrecognized shape keys {sorted(obj)[:6]}"


# ---------------------------------------------------------------------------
# Frontier-facing helpers — called by pipelines/round_txn.py
# ---------------------------------------------------------------------------

def verify_batch_for_frontier(batch_path: Path, strict: bool = False):
    """Verify a single staged batch file for frontier gating.

    This is the primary hook consumed by pipelines/round_txn.py.
    It mirrors audit_run() but scoped to one batch file so
    validate_stage() can gate before linking ROUND-rNN.complete.json.

    Args:
        batch_path: path to batch-rNN.jsonl (staged or committed).
        strict: when True, inconclusive also blocks the frontier;
                when False (default), only failed blocks.

    Returns:
        (counts, findings, blocked) where blocked is the frontier-gate
        decision. Findings are a list of {file, line, status, reason}.

    Frontier gate semantics:
        blocked = (failed > 0) or (strict and inconclusive > 0)
        — never promote cannot-verify to verified.
    """
    batch_path = Path(batch_path)
    counts = {"verified": 0, "inconclusive": 0, "failed": 0, "total": 0}
    findings: list[dict] = []
    try:
        lines = batch_path.read_text().splitlines()
    except OSError as exc:
        findings.append({"file": str(batch_path), "line": 0, "status": "failed", "reason": str(exc)})
        counts["failed"] = 1
        counts["total"] = 1
        return counts, findings, True

    for lineno, line in enumerate(lines, 1):
        if not line.strip():
            continue
        where = f"{batch_path.name}:{lineno}"
        try:
            obj = json.loads(line)
        except json.JSONDecodeError as exc:
            counts["failed"] += 1
            counts["total"] += 1
            findings.append({"file": str(batch_path), "line": lineno, "status": "failed", "reason": f"JSON parse: {exc}"})
            continue
        status, reason = verify_record_execution(obj, where)
        counts[status] += 1
        counts["total"] += 1
        if status != "verified":
            findings.append({"file": str(batch_path), "line": lineno, "status": status, "reason": reason})

    blocked = counts["failed"] > 0 or (strict and counts["inconclusive"] > 0)
    return counts, findings, blocked


def verify_stage_for_frontier(stage_dir: Path, round_number: int, strict: bool = False):
    """Verify the staged batch inside a round_txn staging directory.

    Convenience wrapper around verify_batch_for_frontier() that resolves
    stage_dir / batch-rNN.jsonl via round_txn staging conventions.

    Intended call site (comment hook):
        # pipelines/round_txn.py:validate_stage()
        # from verify_execution import verify_stage_for_frontier
        # counts, findings, blocked = verify_stage_for_frontier(stage, round_number, strict=True)
    """
    stage_dir = Path(stage_dir)
    batch = stage_dir / f"batch-r{round_number:02d}.jsonl"
    return verify_batch_for_frontier(batch, strict=strict)


def frontier_gate_result(batch_path: Path, strict: bool = False) -> dict:
    """Return a JSON-serializable frontier gate verdict for a batch.

    Small helper for round_txn error messages and for docs/verify-execution.md
    examples. Does not raise; the caller decides whether to raise
    TransactionError.
    """
    counts, findings, blocked = verify_batch_for_frontier(batch_path, strict=strict)
    return {
        "batch": str(batch_path),
        "strict": strict,
        "counts": counts,
        "findings": findings,
        "blocked": blocked,
        "gate": "pipelines/verify_execution.py:verify_batch_for_frontier -> pipelines/round_txn.py:validate_stage",
    }


def audit_run(run_dir: Path, strict: bool = False):
    run_dir = Path(run_dir)
    counts = {"verified": 0, "inconclusive": 0, "failed": 0, "total": 0}
    findings = []
    for path in sorted(run_dir.rglob("*.jsonl")):
        rel = path.relative_to(run_dir)
        try:
            lines = path.read_text().splitlines()
        except OSError as e:
            findings.append({"file": str(rel), "line": 0, "status": "failed", "reason": str(e)})
            continue
        for lineno, line in enumerate(lines, 1):
            if not line.strip():
                continue
            where = f"{rel}:{lineno}"
            try:
                obj = json.loads(line)
            except json.JSONDecodeError as e:
                counts["failed"] += 1
                counts["total"] += 1
                findings.append({"file": str(rel), "line": lineno, "status": "failed", "reason": f"JSON parse: {e}"})
                continue
            status, reason = verify_record_execution(obj, where)
            counts[status] += 1
            counts["total"] += 1
            if status != "verified":
                findings.append({"file": str(rel), "line": lineno, "status": status, "reason": reason})
    # Gate: strict blocks on any inconclusive; non-strict only blocks on failed
    blocked = counts["failed"] > 0 or (strict and counts["inconclusive"] > 0)
    return counts, findings, blocked


def main(argv=None):
    import argparse
    p = argparse.ArgumentParser(description="Execution-grounded verification (verified/inconclusive/failed)")
    p.add_argument("run_dir", nargs="?", help="run directory containing .jsonl files")
    p.add_argument("--strict", action="store_true", help="inconclusive also blocks (default: only failed blocks)")
    p.add_argument("--record", help="single jsonl file to check")
    p.add_argument("--line", type=int, help="line number for --record mode")
    p.add_argument("--json", action="store_true", help="emit JSON findings")
    p.add_argument("--batch", help="single batch file for frontier gate check (alias for --record dir batch)")
    args = p.parse_args(argv)

    if args.record:
        path = Path(args.record)
        lineno = 1 if args.line is None else args.line
        try:
            text = path.read_text().splitlines()
        except OSError as exc:
            print(json.dumps({"status": "failed", "reason": str(exc)}, indent=2))
            sys.exit(1)
        if lineno < 1 or lineno > len(text):
            print(json.dumps({
                "status": "failed",
                "reason": f"--line {lineno} out of range (file has {len(text)} lines)",
            }, indent=2))
            sys.exit(1)
        try:
            obj = json.loads(text[lineno - 1])
        except json.JSONDecodeError as exc:
            print(json.dumps({"status": "failed", "reason": f"JSON parse: {exc}"}, indent=2))
            sys.exit(1)
        status, reason = verify_record_execution(obj, f"{path}:{lineno}")
        print(json.dumps({"status": status, "reason": reason}, indent=2))
        sys.exit(0 if status == "verified" else 1)

    if args.batch:
        counts, findings, blocked = verify_batch_for_frontier(Path(args.batch), strict=args.strict)
        if args.json:
            print(json.dumps({"counts": counts, "findings": findings, "blocked": blocked}, indent=2))
        else:
            print(json.dumps(counts, indent=2))
            for f in findings:
                print(f"{f['status'].upper()}: {f['file']}:{f['line']} — {f['reason']}", file=sys.stderr)
        sys.exit(1 if blocked else 0)

    if not args.run_dir:
        p.print_help()
        sys.exit(2)
    counts, findings, blocked = audit_run(Path(args.run_dir), strict=args.strict)
    if args.json:
        print(json.dumps({"counts": counts, "findings": findings, "blocked": blocked}, indent=2))
    else:
        print(json.dumps(counts, indent=2))
        for f in findings:
            print(f"{f['status'].upper()}: {f['file']}:{f['line']} — {f['reason']}", file=sys.stderr)
    sys.exit(1 if blocked else 0)


if __name__ == "__main__":
    main()
