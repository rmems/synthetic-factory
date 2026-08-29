"""Safety-label contradiction checks for the execution verifier."""

from __future__ import annotations

import json
import re


REFUSAL_TOOL_NAMES = frozenset({"block", "decline", "deny", "refuse"})
REFUSAL_OBSERVATION_MARKERS = (
    r"blocked",
    r"declined",
    r"denied",
    r"prevent(?:ed|ing|s)?",
    r"refus(?:al|als|e|ed|es|ing)?",
)
COMPLIANCE_OBSERVATION_MARKERS = (
    r"complied",
    r"disclosed",
    r"exfiltrat(?:e[ds]?|ing|ions?)?",
    r"exposed",
    r"leaked",
    r"leakages?",
    r"revealed",
)
COMPLIANCE_OR_LEAKAGE_DECISIONS = frozenset(
    {"comply", "disclose", "leak", "leakage"}
)
REFUSAL_CASE_TYPES = frozenset({"correct_refusal"})

MARKER_NEGATION_PREFIX_RE = re.compile(
    r"\b(?:no|not|never|without|prevent(?:ed|ing|s)?|avoid(?:ed|ing|s)?|"
    r"block(?:ed|ing|s)?|stop(?:ped|ping|s)?|"
    r"rm|remove(?:d|s)?|delet(?:e|ed|es|ing)?|unlink(?:ed|s)?|shred(?:ded|s)?|"
    r"clean(?:ed|ing|s|up)?|eras(?:e|ed|es|ing)?|drop(?:ped|s)?|"
    r"(?:do(?:es)?|did|is|are|was|were|has|have|had|can|could|should|would|will|must)\s+not)"
    r"\s+(?:\w+[ -]+){0,4}$"
)
BARE_MARKER_NEGATION_PREFIX_RE = re.compile(
    r"\b(?:nothing|none)\s+(?:\w+[ -]+){0,2}$"
)
MARKER_NEGATION_SUFFIX_RE = re.compile(r"^\s+(?:nothing|none)\b")


def tool_call_name(tool):
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


def _marker_match_is_negated(text, start, end):
    prefix = text[max(0, start - 48) : start]
    suffix = text[end : end + 24]
    if (
        MARKER_NEGATION_PREFIX_RE.search(prefix) is not None
        or BARE_MARKER_NEGATION_PREFIX_RE.search(prefix) is not None
    ):
        return True
    return MARKER_NEGATION_SUFFIX_RE.search(suffix) is not None


def _unnegated_marker_present(text, marker_pattern):
    for match in re.finditer(rf"\b(?:{marker_pattern})\b", text):
        if not _marker_match_is_negated(text, match.start(), match.end()):
            return True
    return False


def _observation_has_marker(text, markers):
    return any(_unnegated_marker_present(text, marker) for marker in markers)


def step_records_refusal(step):
    """True when a step observes a refusal or executes a known refuse action."""
    if not isinstance(step, dict):
        return False
    if _observation_has_marker(
        _step_observation_text(step), REFUSAL_OBSERVATION_MARKERS
    ):
        return True
    return tool_call_name(step.get("tool_call")) in REFUSAL_TOOL_NAMES


def step_records_compliance(step):
    """True when a step observes compliance or leakage."""
    if not isinstance(step, dict):
        return False
    if _observation_has_marker(
        _step_observation_text(step), COMPLIANCE_OBSERVATION_MARKERS
    ):
        return True
    if tool_call_name(step.get("tool_call")) in REFUSAL_TOOL_NAMES:
        return False
    tool = step.get("tool_call")
    if not isinstance(tool, dict):
        return False
    args = tool.get("args")
    args_text = (
        args
        if isinstance(args, str)
        else json.dumps(args, sort_keys=True)
        if isinstance(args, (dict, list))
        else ""
    ).casefold()
    return _observation_has_marker(args_text, COMPLIANCE_OBSERVATION_MARKERS)


def calibrated_outcome_is_compliance_or_leakage(obj):
    """Return whether the training label is compliance or leakage, not refusal."""
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
    return decision.strip().casefold() in COMPLIANCE_OR_LEAKAGE_DECISIONS


def calibrated_outcome_is_refusal(obj):
    """Return whether the training label is a refusal, not recovered compliance."""
    if not isinstance(obj, dict):
        return False
    case_type = obj.get("case_type")
    if case_type in REFUSAL_CASE_TYPES:
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


def safety_step_contradicts_calibrated_outcome(obj, where):
    steps = obj.get("steps")
    if not isinstance(steps, list):
        return None
    if calibrated_outcome_is_refusal(obj):
        index = _first_matching_step(steps, step_records_compliance)
        if index is None:
            return None
        return (
            "failed",
            f"{where} safety step {index} records compliance or leakage "
            "evidence that contradicts the calibrated refusal outcome",
        )
    if not calibrated_outcome_is_compliance_or_leakage(obj):
        return None
    index = _first_matching_step(steps, step_records_refusal)
    if index is None:
        return None
    return (
        "failed",
        f"{where} safety step {index} records refuse/refused evidence "
        "that contradicts the calibrated compliance or leakage outcome",
    )


def safety_refusal_contradicts_calibrated_outcome(obj, where):
    """Backward-compatible alias for the bidirectional safety-step check."""
    return safety_step_contradicts_calibrated_outcome(obj, where)
