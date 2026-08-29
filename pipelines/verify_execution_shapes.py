"""Record-shape helpers for pipelines/verify_execution.py.

Patchable checker names live on the host module so tests that patch
``verify_execution.check_line`` (and related validators) keep working.
"""

from __future__ import annotations

import json
import math
import re


def _host():
    import verify_execution as host
    return host


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

def _extract_step_tool_name(tool):
    if isinstance(tool, dict):
        return tool.get("name")
    if isinstance(tool, str) and tool.strip():
        return tool.strip().split()[0]
    return None


def _step_observation_failure(i, step, observation):
    if "observation" in step and not isinstance(observation, str):
        return "failed", f"step {i} observation must be a string"
    return None


def _step_tool_name_failure(i, tool_name):
    if tool_name is not None and not isinstance(tool_name, str):
        return "failed", f"step {i} tool_call.name must be a string"
    return None


def _step_inconclusive_reasons(i, step, tool_name, observation):
    reasons = []
    if step.get("thought") is not None and step.get("decision_basis") is None:
        reasons.append(f"step {i} has hidden thought without decision_basis")
    if tool_name is None:
        reasons.append(f"step {i} missing tool_call")
        return reasons
    if tool_name not in KNOWN_TOOLS:
        reasons.append(f"step {i} unknown tool {tool_name!r}")
    if not isinstance(observation, str) or not observation.strip():
        reasons.append(f"step {i} missing observation")
    return reasons


def _validate_single_episode_step(i, step):
    if not isinstance(step, dict):
        return "failed", f"step {i} not an object"
    name = _extract_step_tool_name(step.get("tool_call"))
    observation = step.get("observation")
    failure = _step_observation_failure(i, step, observation)
    if failure is not None:
        return failure
    failure = _step_tool_name_failure(i, name)
    if failure is not None:
        return failure
    reasons = _step_inconclusive_reasons(i, step, name, observation)
    if name is None:
        return "inconclusive", reasons
    return "inconclusive" if reasons else "verified", reasons


def verify_episode_steps(steps, _where):
    """Verify coding episode steps have observable execution evidence."""
    if not isinstance(steps, list) or not steps:
        return "failed", "steps missing or empty"
    inconclusive_reasons = []
    for i, step in enumerate(steps):
        status, reasons = _validate_single_episode_step(i, step)
        if status == "failed":
            return status, reasons
        inconclusive_reasons.extend(reasons)
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


def _is_valid_step_index(index, steps):
    if index is None or not isinstance(steps, list):
        return False
    return 0 <= index < len(steps)


def _step_from_shape_error(error, where, obj):
    if not isinstance(obj, dict):
        return None
    index = _step_index_from_shape_error(error, where)
    steps = obj.get("steps")
    if not _is_valid_step_index(index, steps):
        return None
    step = steps[index]
    return step if isinstance(step, dict) else None


def _omitted_tool_call_type_error(error, where, obj):
    """True when a type error is only the companion of an omitted tool_call."""
    if not error.endswith(": tool_call must be an object"):
        return False
    step = _step_from_shape_error(error, where, obj)
    return step is not None and "tool_call" not in step


def _missing_or_empty_observation_error(error, where, obj):
    """Keep absent/blank observations inconclusive, but reject wrong types."""
    if not error.endswith(": observation must be a non-empty string"):
        return False
    step = _step_from_shape_error(error, where, obj)
    if step is None or "observation" not in step:
        return True
    observation = step["observation"]
    return isinstance(observation, str) and not observation.strip()


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
        )
    ):
        return True
    return _omitted_tool_call_type_error(
        error, where, obj
    ) or _missing_or_empty_observation_error(error, where, obj)


def verify_episode(obj, where, *, require_goal=True, strict_turns=False):
    """Validate an episode envelope before accepting its step evidence.

    ``validate_run.check_episode`` owns the repository's episode shape. Its
    per-step execution-evidence findings remain the responsibility of
    ``verify_episode_steps`` so a missing observation stays ``inconclusive``
    rather than being promoted to a structural failure.
    """
    if not isinstance(obj, dict):
        return "failed", f"{where} episode is not an object"
    if _host().check_episode is None:
        return "failed", "episode shape checker unavailable"
    shape_errors = [
        error
        for error in _host().check_episode(
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
_REFUSAL_OBSERVATION_MARKERS = (
    r"blocked",
    r"declined",
    r"denied",
    r"prevent(?:ed|ing|s)?",
    r"refus(?:al|als|e|ed|es|ing)?",
)
_COMPLIANCE_OBSERVATION_MARKERS = (
    r"compl(?:y|ies|ied|ying)",
    r"disclos(?:e[ds]?|ing)",
    r"exfiltrat(?:e[ds]?|ing|ions?)?",
    r"expos(?:e[ds]?|ing)",
    r"leak(?:e[ds]?|ing|ages?)?",
    r"reveal(?:e[ds]?|ing)?",
    r"dilut(?:e[ds]?|ing)",
    r"distill(?:e[ds]?|ing)",
    r"memoriz(?:e[ds]?|ing)",
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


_MARKER_NEGATION_PREFIX_RE = re.compile(
    r"\b(?:no|not|never|without|prevent(?:ed|ing|s)?|avoid(?:ed|ing|s)?|"
    r"block(?:ed|ing|s)?|stop(?:ped|ping|s)?|"
    r"rm|removed?s|delet(?:e[ds]?|ing)?|unlink(?:ed|s)?|shred(?:ded|s)?|"
    r"clean(?:ed|ing|s|up)?|eras(?:e|ed|es|ing)?|drop(?:ped|s)?|"
    r"(?:do(?:es)?|did|is|are|was|were|has|have|had|can|could|should|would|will|must)\s+not)"
    r"\s+(?:\w+[ -]+){0,4}$"
)
_BARE_MARKER_NEGATOR_RE = re.compile(r"\b(?:nothing|none)\s+")
_BARE_MARKER_SPAN_TEXT_RE = re.compile(r"[\w -]*")
_BARE_MARKER_SPAN_WORD_RE = re.compile(r"\w+")
# Restore the 4-word window the shared prefix negator uses, so 3-4-word
# negated spans ("none of the files were leaked") are recognized.
_BARE_NEGATOR_WINDOW_WORDS = 4
_BARE_NEGATOR_AUXILIARIES = frozenset(
    {
        "am", "is", "are", "was", "were", "be", "been", "being",
        "has", "have", "had", "do", "does", "did",
        "can", "could", "shall", "should", "will", "would",
        "must", "may", "might",
    }
)
_MARKER_NEGATION_SUFFIX_RE = re.compile(r"^\s+(?:nothing|none)\b")


def _negator_scope_survives(words):
    """True when no completed second clause sits inside the negator window.

    "none of the files were leaked" keeps its negation: "were" is the
    auxiliary of the marker's own passive verb. A span such as
    "was found credentials were" breaks the scope — the auxiliary-plus-
    lexical-verb pair "was found" completes the negator's clause, and the
    later auxiliary opens a new one — so the marker after it stays unnegated
    compliance evidence ("nothing was found credentials were exposed").
    """
    for index in range(len(words) - 1):
        if (
            words[index] in _BARE_NEGATOR_AUXILIARIES
            and words[index + 1] not in _BARE_NEGATOR_AUXILIARIES
        ):
            later = words[index + 2 :]
            return not any(word in _BARE_NEGATOR_AUXILIARIES for word in later)
    return True


def _bare_negator_applies(prefix):
    """True when a bare nothing/none negator still scopes over the marker.

    The negator must connect to the marker through a punctuation-free span
    of at most ``_BARE_NEGATOR_WINDOW_WORDS`` words, so clause boundaries
    ("nothing was found; credentials were exposed") end the scope.
    """
    for match in _BARE_MARKER_NEGATOR_RE.finditer(prefix):
        remainder = prefix[match.end() :]
        span = _BARE_MARKER_SPAN_TEXT_RE.fullmatch(remainder)
        if span is None:
            continue
        words = _BARE_MARKER_SPAN_WORD_RE.findall(span.group(0))
        if len(words) > _BARE_NEGATOR_WINDOW_WORDS:
            continue
        if _negator_scope_survives(words):
            return True
    return False


def _marker_match_is_negated(text, start, end):
    prefix = text[max(0, start - 48) : start]
    suffix = text[end : end + 24]
    if (
        _MARKER_NEGATION_PREFIX_RE.search(prefix) is not None
        or _bare_negator_applies(prefix)
    ):
        return True
    return _MARKER_NEGATION_SUFFIX_RE.search(suffix) is not None


def _unnegated_marker_present(text, marker_pattern):
    # Each marker entry carries its own internal groups and never a top-level
    # alternation, so no extra wrapper group is needed around the pattern.
    for match in re.finditer(rf"\b{marker_pattern}\b", text):
        if not _marker_match_is_negated(text, match.start(), match.end()):
            return True
    return False


def _observation_has_marker(text, markers):
    """True when a marker appears without a local negation window."""
    return any(_unnegated_marker_present(text, marker) for marker in markers)


def _step_records_refusal(step):
    """True when a step observes a refusal or executes a known refuse action."""
    if not isinstance(step, dict):
        return False
    if _observation_has_marker(
        _step_observation_text(step), _REFUSAL_OBSERVATION_MARKERS
    ):
        return True
    return _tool_call_name(step.get("tool_call")) in _REFUSAL_TOOL_NAMES


def _step_records_compliance(step):
    """True when a step observes compliance or leakage."""
    if not isinstance(step, dict):
        return False
    if _observation_has_marker(
        _step_observation_text(step), _COMPLIANCE_OBSERVATION_MARKERS
    ):
        return True
    if _tool_call_name(step.get("tool_call")) in _REFUSAL_TOOL_NAMES:
        return False
    tool = step.get("tool_call")
    if isinstance(tool, dict):
        args = tool.get("args")
        args_text = (
            args if isinstance(args, str)
            else json.dumps(args, sort_keys=True)
            if isinstance(args, (dict, list))
            else ""
        ).casefold()
        if _observation_has_marker(args_text, _COMPLIANCE_OBSERVATION_MARKERS):
            return True
    return False


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


def _first_matching_step(steps, predicate):
    for index, step in enumerate(steps):
        if predicate(step):
            return index
    return None


def _safety_step_contradicts_calibrated_outcome(obj, where):
    steps = obj.get("steps")
    if not isinstance(steps, list):
        return None
    if _calibrated_outcome_is_refusal(obj):
        index = _first_matching_step(steps, _step_records_compliance)
        if index is None:
            return None
        return (
            "failed",
            f"{where} safety step {index} records compliance or leakage "
            "evidence that contradicts the calibrated refusal outcome",
        )
    if not _calibrated_outcome_is_compliance_or_leakage(obj):
        return None
    index = _first_matching_step(steps, _step_records_refusal)
    if index is None:
        return None
    return (
        "failed",
        f"{where} safety step {index} records refuse/refused evidence "
        "that contradicts the calibrated compliance or leakage outcome",
    )


def _safety_refusal_contradicts_calibrated_outcome(obj, where):
    """Backward-compatible alias for the bidirectional safety-step check."""
    return _safety_step_contradicts_calibrated_outcome(obj, where)


def verify_safety_episode(obj, where):
    """Validate the safety-case envelope before accepting its step evidence."""
    if _host().check_safety_case is None or _host().check_episode is None:
        return "failed", "safety-case shape checker unavailable"
    try:
        errors = [
            *_host().check_safety_case(obj, where, factory_staging=True),
            *_host().check_episode(
                obj,
                where,
                require_goal=False,
                forbid_hidden_thought=True,
            ),
        ]
    except (TypeError, ValueError, KeyError) as exc:
        return "failed", f"safety-case shape check error: {exc}"
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


def _collect_timeline(fo, observable_fields):
    if "timeline" not in fo:
        return None
    value = fo["timeline"]
    error = _malformed_outcome_array(value, "timeline", objects_only=True)
    if error:
        return error
    if value:
        observable_fields.append("timeline")
    return None


def _collect_observed_effects(fo, observable_fields):
    if "observed_effects" not in fo:
        return None
    value = fo["observed_effects"]
    error = _malformed_outcome_array(value, "observed_effects", objects_only=False)
    if error:
        return error
    if value:
        observable_fields.append("observed_effects")
    return None


def _collect_new_state(fo, observable_fields):
    if "new_state" not in fo:
        return None
    value = fo["new_state"]
    if not isinstance(value, dict):
        return "future_outcome.new_state must be an object"
    if value:
        observable_fields.append("new_state")
    return None


def _collect_state_delta(fo, observable_fields):
    if "state_delta" not in fo:
        return None
    value = fo["state_delta"]
    if isinstance(value, dict):
        if value:
            observable_fields.append("state_delta")
        return None
    if not isinstance(value, list):
        return "future_outcome.state_delta must be an object or array"
    error = _malformed_outcome_array(value, "state_delta", objects_only=False)
    if error:
        return error
    if value:
        observable_fields.append("state_delta")
    return None


def _collect_surprises(fo, observable_fields):
    if "surprises" not in fo:
        return None
    value = fo["surprises"]
    error = _malformed_outcome_array(value, "surprises", objects_only=False)
    if error:
        return error
    if value:
        observable_fields.append("surprises")
    return None


def _collect_named_events(fo, observable_fields):
    for field in ("hazard_avoided", "incident"):
        if field not in fo:
            continue
        value = fo[field]
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


def _outcome_metric_error(field, value):
    if not _finite_number(value):
        return f"future_outcome.{field} must be a finite number"
    if field not in NONNEGATIVE_OUTCOME_METRICS:
        return None
    if value >= 0:
        return None
    return f"future_outcome.{field} must be a non-negative finite number"


def _collect_outcome_metrics(fo, observable_fields):
    for field in OBSERVABLE_OUTCOME_METRICS:
        if field not in fo:
            continue
        error = _outcome_metric_error(field, fo[field])
        if error:
            return error
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


def _thalamic_provenance_verdict(state, where):
    prov = state.get("sim_or_real") if isinstance(state, dict) else None
    if prov is not None and not isinstance(prov, str):
        return "failed", f"{where}.state.sim_or_real must be a string"
    if prov not in _host().ALLOWED_SIM_OR_REAL:
        return "inconclusive", f"non-training provenance {prov!r} on {where}.state.sim_or_real"
    return None


def _thalamic_safety_decision_error(sd):
    if not isinstance(sd, dict):
        return "safety_decision must be an object"
    decision = sd.get("decision")
    if decision is not None and not isinstance(decision, str):
        return "safety_decision.decision must be a string enum"
    rationale = sd.get("rationale")
    if not isinstance(rationale, str) or not rationale.strip():
        return "missing safety_decision.rationale"
    return None


def _thalamic_core_verdict(obj, where):
    """Return an early verdict, or None when the core envelope is usable."""
    if not isinstance(obj, dict):
        return "inconclusive", f"{where} is not an object — cannot verify"
    prov_verdict = _thalamic_provenance_verdict(obj.get("state", {}), where)
    if prov_verdict:
        return prov_verdict
    sd_error = _thalamic_safety_decision_error(obj.get("safety_decision", {}))
    if sd_error:
        return "failed", sd_error
    if not isinstance(obj.get("future_outcome"), dict):
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
    return all(key in side for key in _host().THALAMIC_CORE_KEYS)


def _side_is_episode(side):
    if not isinstance(side, dict):
        return False
    if "steps" not in side:
        return False
    return not _side_is_thalamic(side)


def _preference_wrapper_verdict(obj, where):
    if _host().check_line is None:
        return "failed", "preference shape checker unavailable"
    try:
        wrapper_errors, wrapper_kind = _host().check_line(
            obj,
            where,
            factory_staging=True,
        )
    except (TypeError, ValueError, KeyError) as exc:
        return "failed", f"preference shape check error: {exc}"
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
    if chosen_episode != rejected_episode:
        return "failed", "preference sides mix episode and Thalamic shapes"
    if chosen_episode:
        return _verify_episode_preference_sides(obj, where, chosen, rejected)
    chosen_thalamic = _side_is_thalamic(chosen)
    rejected_thalamic = _side_is_thalamic(rejected)
    if chosen_thalamic != rejected_thalamic:
        return "failed", "preference sides mix or omit required shape fields"
    if not chosen_thalamic:
        return "failed", "preference sides are not episode or Thalamic records"
    return _combine_preference_side_verdicts(
        verify_record_execution(chosen, f"{where}.chosen"),
        verify_record_execution(rejected, f"{where}.rejected"),
    )


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


def _is_thalamic_record(obj):
    return all(k in obj for k in _host().THALAMIC_CORE_KEYS)


def _is_preference_record(obj):
    return "chosen" in obj and "rejected" in obj


def _is_bridge_record(obj):
    return "language_view" in obj and "spike_events" in obj


def _verify_step_record(obj, where):
    return verify_episode(obj, where)


def _direct_record_envelope_verdict(
    obj, where, expected_kind, *, filter_errors=None
):
    """Validate standalone Thalamic/bridge envelopes before execution evidence."""
    if _host().check_line is None:
        return "failed", "record shape checker unavailable"
    try:
        errors, kind = _host().check_line(obj, where, factory_staging=True)
    except (TypeError, ValueError, KeyError) as exc:
        return "failed", f"record shape check error: {exc}"
    if kind != expected_kind:
        return "failed", f"record was classified as {kind!r}, not {expected_kind!r}"
    if filter_errors is not None:
        errors = filter_errors(errors, obj, where)
    if errors:
        return "failed", f"record envelope invalid: {errors[0]}"
    return None


def _verify_direct_record(
    obj, where, expected_kind, verifier, *, filter_errors=None
):
    envelope = _direct_record_envelope_verdict(
        obj, where, expected_kind, filter_errors=filter_errors
    )
    if envelope is not None:
        return envelope
    return verifier(obj, where)


def _thalamic_provenance_value(obj):
    state = obj.get("state")
    return state.get("sim_or_real") if isinstance(state, dict) else None


def _bridge_provenance_value(obj):
    language_view = obj.get("language_view")
    traj = (
        language_view.get("trajectory")
        if isinstance(language_view, dict)
        else None
    )
    return _thalamic_provenance_value(traj) if isinstance(traj, dict) else None


def _drop_sim_or_real_enum_error(errors, provenance, where):
    """Drop only the generic state.sim_or_real enum error for one location.

    ``check_provenance`` emits the generic enum error exactly for a
    non-allowed value that is not a 'real' string; a 'real' value gets the
    specific "must not be 'real'" message instead (the two are paired with
    elif), so dropping the generic error can never rescue 'real' provenance
    and that case keeps failing closed on its envelope error. A disallowed
    non-'real' value (e.g. 'unknown') belongs to the verifier's
    non-training-provenance cannot-verify taxonomy: the envelope error is
    dropped here and ``verify_thalamic`` re-derives it as ``inconclusive``.
    """
    if not isinstance(provenance, str) or provenance in _host().ALLOWED_SIM_OR_REAL:
        return errors
    enum_error = (
        f"{where}: state.sim_or_real must be one of "
        f"{sorted(_host().ALLOWED_SIM_OR_REAL)}"
    )
    return [error for error in errors if error != enum_error]


def _without_non_training_provenance_error(errors, obj, where):
    return _drop_sim_or_real_enum_error(
        errors, _thalamic_provenance_value(obj), where
    )


def _without_bridge_non_training_provenance_error(errors, obj, where):
    return _drop_sim_or_real_enum_error(
        errors,
        _bridge_provenance_value(obj),
        f"{where}.language_view.trajectory",
    )


def _verify_thalamic_record(obj, where):
    return _verify_direct_record(
        obj,
        where,
        "thalamic",
        verify_thalamic,
        filter_errors=_without_non_training_provenance_error,
    )


def _verify_bridge_record(obj, where):
    return _verify_direct_record(
        obj,
        where,
        "bridge_pair",
        _verify_bridge_execution,
        filter_errors=_without_bridge_non_training_provenance_error,
    )


def _is_step_record(obj):
    return "steps" in obj


def _is_safety_record(obj):
    return "case_type" in obj


_RECORD_VERIFIER_ROUTES = (
    (_is_thalamic_record, _verify_thalamic_record),
    (_is_preference_record, _verify_preference_execution),
    (_is_bridge_record, _verify_bridge_record),
    (_is_safety_record, verify_safety_episode),
    (_is_step_record, _verify_step_record),
)


def verify_record_execution(obj, where="record"):
    """Return (status, reason) in {verified, inconclusive, failed}."""
    if not isinstance(obj, dict):
        return "failed", "not an object"
    for predicate, verifier in _RECORD_VERIFIER_ROUTES:
        if predicate(obj):
            return verifier(obj, where)
    return "inconclusive", f"unrecognized shape keys {sorted(obj)[:6]}"
