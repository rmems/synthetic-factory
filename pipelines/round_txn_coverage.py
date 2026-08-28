"""Lane-coverage helpers for pipelines/round_txn.py."""

from __future__ import annotations

import json
import re
import unicodedata

CASCADE_GENERIC_TERMS = frozenset(
    {
        "and",
        "are",
        "error",
        "errors",
        "failed",
        "failure",
        "fault",
        "for",
        "from",
        "has",
        "have",
        "into",
        "issue",
        "not",
        "problem",
        "step",
        "that",
        "the",
        "this",
        "was",
        "were",
        "with",
    }
)


def _nested_dict_key_paths(mapping, key, path):
    for child_key, item in mapping.items():
        child_path = f"{path}.{child_key}" if path else child_key
        if child_key == key:
            yield child_path
        yield from nested_key_paths(item, key, child_path)


def _nested_list_key_paths(items, key, path):
    for index, item in enumerate(items):
        yield from nested_key_paths(item, key, f"{path}[{index}]")


def nested_key_paths(value, key, path=""):
    """Yield every nested occurrence of one forbidden field name."""
    if isinstance(value, dict):
        yield from _nested_dict_key_paths(value, key, path)
    elif isinstance(value, list):
        yield from _nested_list_key_paths(value, key, path)


def nested_strings(value):
    """Yield observable string values from a JSON-compatible value."""
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for item in value.values():
            yield from nested_strings(item)
    elif isinstance(value, list):
        for item in value:
            yield from nested_strings(item)


def _flatten_unit_text(value):
    return " ".join(
        text.strip().casefold()
        for text in nested_strings(value)
        if text.strip()
    )


def _step_units(owner):
    if isinstance(owner, dict):
        steps = owner.get("steps")
        if isinstance(steps, list):
            return steps
    return []


def agentic_trajectory_units(record: dict) -> list[str]:
    """Return separate ordered steps/terminal fields, excluding the task goal."""
    chosen = record.get("chosen")
    rejected = record.get("rejected")
    values = [*_step_units(record)]
    if isinstance(chosen, dict) or isinstance(rejected, dict):
        values.extend(
            (
                *_step_units(chosen),
                *_step_units(rejected),
                record.get("critique"),
                chosen.get("outcome") if isinstance(chosen, dict) else None,
                rejected.get("outcome") if isinstance(rejected, dict) else None,
            )
        )
    values.append(record.get("outcome"))
    return [_flatten_unit_text(v) for v in values if v is not None]


def _find_matching_unit_index(units, alternatives, start_index):
    for index in range(start_index, len(units)):
        if any(term in units[index] for term in alternatives):
            return index
    return None


def _advance_scenario_cursor(matched_index, group_index, phase_start):
    step_offset = 1 if group_index >= phase_start else 0
    return matched_index + step_offset


def demonstrates_ordered_scenario(record: dict, scenario_terms) -> bool:
    """Require failure, correction, and verification in distinct ordered units."""
    units = agentic_trajectory_units(record)
    cursor = 0
    phase_start = max(0, len(scenario_terms) - 3)
    for group_index, alternatives in enumerate(scenario_terms):
        matched_index = _find_matching_unit_index(units, alternatives, cursor)
        if matched_index is None:
            return False
        cursor = _advance_scenario_cursor(matched_index, group_index, phase_start)
    return True


def _normalized_signature_field(*values):
    for value in values:
        if isinstance(value, str) and value.strip():
            return re.sub(r"\s+", " ", value.strip().casefold())
    return None


def long_horizon_scenario_signature(record: dict):
    """Return the required explicit codebase/bug-class category signature."""
    codebase = _normalized_signature_field(record.get("codebase_type"))
    bug_class = _normalized_signature_field(record.get("bug_class"))
    if codebase is None or bug_class is None:
        return None
    return (codebase, bug_class)


def _is_banned_normalized_name(normalized: str) -> bool:
    if normalized in {"spike_events", "raster", "rasters"}:
        return True
    if re.search(r"(?:^|_)rasters?(?:_|$)", normalized) is not None:
        return True
    return "spikenaut" in normalized or "neuromorphic" in normalized


def _normalize_dict_key(key):
    return re.sub(
        r"[^a-z0-9]+",
        "_",
        re.sub(r"(?<=[a-z0-9])(?=[A-Z])", "_", str(key)).casefold(),
    ).strip("_")


def _banned_dict_paths(mapping, path):
    for key, item in mapping.items():
        child_path = f"{path}.{key}" if path else key
        if _is_banned_normalized_name(_normalize_dict_key(key)):
            yield child_path
        yield from banned_agentic_wrapper_paths(item, child_path)


def _banned_list_paths(items, path):
    for index, item in enumerate(items):
        yield from banned_agentic_wrapper_paths(item, f"{path}[{index}]")


def banned_agentic_wrapper_paths(value, path=""):
    """Yield nested fields or values that introduce neuromorphic wrappers."""
    if isinstance(value, dict):
        yield from _banned_dict_paths(value, path)
    elif isinstance(value, list):
        yield from _banned_list_paths(value, path)
    elif isinstance(value, str):
        normalized = value.casefold()
        if "spikenaut" in normalized or "neuromorphic" in normalized:
            yield path or "<root>"


def _extract_visible_terms(text):
    if not isinstance(text, str):
        return set()
    return {
        term
        for term in re.findall(r"[a-z0-9][a-z0-9_-]{2,}", text.lower())
        if term not in CASCADE_GENERIC_TERMS
    }


def shares_visible_terms(left, right):
    """Whether two observable strings name at least one meaningful common term."""
    left_terms = _extract_visible_terms(left)
    right_terms = _extract_visible_terms(right)
    return bool(left_terms and right_terms and (left_terms & right_terms))


def normalized_category(value):
    """Normalize a human category so punctuation cannot manufacture diversity."""
    if not isinstance(value, str):
        return ""
    text = unicodedata.normalize("NFC", value).strip()
    return re.sub(
        r"_+", "_", re.sub(r"[^\w]+", "_", text.casefold())
    ).strip("_")


def _prefix_is_negated(tokens):
    for index, token in enumerate(tokens):
        if token in {"no", "never", "without"}:
            return True
        if token == "not":
            if index + 1 < len(tokens) and tokens[index + 1] == "only":
                continue
            return True
    return False


_SUFFIX_NEGATED_RE = re.compile(
    r"(?:(?:is|are|was|were|did)_)?(?:not|never)_"
    r"(?:created|happened|introduced|occurred|present|produced|triggered)"
    r"(?:_|$)|(?:(?:is|are|was|were)_)?(?:avoided|prevented)(?:_|$)"
)


def _match_has_preventive_negation(introduced, match, preventive_terms):
    prefix_tokens = introduced[: match.start()].strip("_").split("_")[-3:]
    if any(token in preventive_terms for token in prefix_tokens):
        return True
    if _prefix_is_negated(prefix_tokens):
        return True
    suffix = introduced[match.end() :].strip("_")
    return _SUFFIX_NEGATED_RE.match(suffix) is not None


def _evidence_match_has_unnegated(introduced, evidence, preventive_terms):
    normalized = normalized_category(evidence)
    if not normalized:
        return False
    for match in re.finditer(rf"(?:^|_){re.escape(normalized)}(?=_|$)", introduced):
        if not _match_has_preventive_negation(introduced, match, preventive_terms):
            return True
    return False


def visibly_names_fault(introduced_text, *fault_evidence):
    """Whether one designated step explicitly names declared fault evidence."""
    introduced = normalized_category(introduced_text)
    if not introduced:
        return False
    preventive_terms = {
        "avoid",
        "avoided",
        "avoiding",
        "prevent",
        "prevented",
        "preventing",
    }
    return any(
        _evidence_match_has_unnegated(introduced, evidence, preventive_terms)
        for evidence in fault_evidence
    )


def numbered_horizon_errors(where, steps, lane, minimum, maximum):
    """Return lane-specific horizon and exact integer numbering errors."""
    if not isinstance(steps, list):
        return []
    errors = []
    if not minimum <= len(steps) <= maximum:
        errors.append(f"{where}: {lane} episodes require {minimum} to {maximum} steps")
    errors.extend(contiguous_step_number_errors(where, steps, lane))
    return errors


def contiguous_step_number_errors(where, steps, lane):
    """Return an error unless list entries use exact integer numbering 1..K."""
    if not isinstance(steps, list):
        return []
    for expected_number, step in enumerate(steps, 1):
        if not isinstance(step, dict):
            return [f"{where}: {lane} steps must be numbered contiguously from 1"]
        number = step.get("n")
        if not isinstance(number, int) or isinstance(number, bool) or number != expected_number:
            return [f"{where}: {lane} steps must be numbered contiguously from 1"]
    return []


def observable_step_text(step):
    """Flatten only publishable tool/basis/observation fields for lane checks."""
    if not isinstance(step, dict):
        return ""
    values = [step.get("decision_basis"), step.get("observation")]
    tool_call = step.get("tool_call")
    if isinstance(tool_call, dict):
        values.extend((tool_call.get("name"), tool_call.get("args")))
    return " ".join(
        value if isinstance(value, str) else json.dumps(value, sort_keys=True)
        for value in values
        if isinstance(value, (str, dict, list))
    ).lower()


def step_observation_text(step):
    """Return only the recorded result of a step, excluding plans and commands."""
    observation = step.get("observation") if isinstance(step, dict) else None
    return observation.casefold() if isinstance(observation, str) else ""


def _has_matching_verify_step(texts, observations, fix_index):
    test_terms = ("test", "pytest", "cargo test", "npm test")
    verify_terms = ("pass", "success", "green", "verified", "fixed")
    return any(
        any(t in texts[verify_index] for t in test_terms)
        and any(v in observations[verify_index] for v in verify_terms)
        for verify_index in range(fix_index + 1, len(texts))
    )


def _has_matching_fix_step(texts, observations, read_index):
    fix_terms = ("fix", "repair", "patch", "edit", "write", "apply")
    for fix_index in range(read_index + 1, len(texts)):
        if any(term in texts[fix_index] for term in fix_terms):
            if _has_matching_verify_step(texts, observations, fix_index):
                return True
    return False


def _find_debug_read_fix_verify(texts, observations, failure_index):
    read_terms = ("re-read", "reread", "inspect", "read", "cat ", "sed ", "rg ")
    for read_index in range(failure_index + 1, len(texts)):
        if any(term in texts[read_index] for term in read_terms):
            if _has_matching_fix_step(texts, observations, read_index):
                return True
    return False


def _is_failure_step(text, observation):
    test_terms = ("test", "pytest", "cargo test", "npm test")
    failure_terms = ("fail", "error", "nonzero", "red")
    return any(t in text for t in test_terms) and any(f in observation for f in failure_terms)


def _find_debug_failure_loop(texts, observations, edit_index):
    for failure_index in range(edit_index + 1, len(texts)):
        if _is_failure_step(texts[failure_index], observations[failure_index]):
            if _find_debug_read_fix_verify(texts, observations, failure_index):
                return True
    return False


def has_long_horizon_debug_loop(steps):
    """Whether observable steps contain edit, failing test, re-read, fix, verify."""
    if not isinstance(steps, list):
        return False
    texts = [observable_step_text(step) for step in steps]
    observations = [step_observation_text(step) for step in steps]
    edit_terms = ("edit", "write", "patch", "apply")
    return any(
        any(term in text for term in edit_terms)
        and _find_debug_failure_loop(texts, observations, edit_index)
        for edit_index, text in enumerate(texts)
    )


def _step_failed_hypothesis(index, step, failure_terms):
    observation = step.get("observation") if isinstance(step, dict) else None
    if not isinstance(observation, str):
        return []
    obs_lower = observation.lower()
    if not any(term in obs_lower for term in failure_terms):
        return []
    return [
        (index, match.group(1))
        for match in re.finditer(
            r"\bhypothesis\s*[:#_-]?\s*([a-z0-9][a-z0-9_-]{2,})",
            obs_lower,
        )
    ]


def _hypothesis_abandoned_later(label, remaining_steps, abandonment_terms):
    for step in remaining_steps:
        basis = step.get("decision_basis") if isinstance(step, dict) else None
        if (
            isinstance(basis, str)
            and label in basis.lower()
            and any(term in basis.lower() for term in abandonment_terms)
        ):
            return True
    return False


def _collect_failed_hypotheses(steps):
    failure_terms = ("fail", "disproved", "ruled out", "not the cause")
    return [
        item
        for index, step in enumerate(steps)
        for item in _step_failed_hypothesis(index, step, failure_terms)
    ]


def abandoned_failed_hypotheses(steps):
    """Return distinct explicit hypothesis labels failed then abandoned later."""
    if not isinstance(steps, list):
        return set()
    abandonment_terms = ("abandon", "discard", "reject", "disproved", "ruled out")
    return {
        label
        for failure_index, label in _collect_failed_hypotheses(steps)
        if _hypothesis_abandoned_later(label, steps[failure_index + 1 :], abandonment_terms)
    }


_SPARSE_PROGRESS_TERMS = re.compile(
    r"\b(?:added|changed|created|deleted|disproved|edited|evidence|failed|"
    r"fixed|found|hypothesis|learned|measured|patched|removed|reproduced|"
    r"tested|updated|verified|wrote)\b"
)
_SPARSE_STALL_TERMS = re.compile(
    r"\b(?:no[ -]?op|no change|nothing changed|unchanged)\b"
)


def _step_sparse_progress_error(where, index, step, previous_obs):
    text = observable_step_text(step)
    if (
        _SPARSE_STALL_TERMS.search(text) is not None
        or _SPARSE_PROGRESS_TERMS.search(text) is None
    ):
        return (
            f"{where}: sparse long-task steps[{index}] must show observable "
            "file, test, or belief progress rather than padding",
            None,
        )
    observation = step.get("observation") if isinstance(step, dict) else None
    normalized_obs = (
        re.sub(r"\s+", " ", observation.strip().casefold())
        if isinstance(observation, str) and observation.strip()
        else None
    )
    if normalized_obs is not None and normalized_obs == previous_obs:
        return (
            f"{where}: sparse long-task steps[{index}] repeats the prior "
            "observation without observable progress",
            normalized_obs,
        )
    return None, normalized_obs


def sparse_step_progress_errors(where, steps):
    """Reject sparse-horizon padding that changes neither state nor belief."""
    if not isinstance(steps, list):
        return []
    previous_obs = None
    for index, step in enumerate(steps):
        error, previous_obs = _step_sparse_progress_error(where, index, step, previous_obs)
        if error:
            return [error]
    return []
