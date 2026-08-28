"""Step-action predicates for coding-curation manifests."""

from __future__ import annotations

from typing import Any, NamedTuple

from coding_constants import (
    REASON_STEP_NOT_OBJECT,
    REASON_THOUGHT_REMOVED,
    STEP_EVIDENCE_REASONS,
    STEP_EXCLUSION_REASONS,
    STEP_RETAINED_REASONS,
    TRANSFORM_VERSION,
    _EVIDENCE_REASON,
)


def _is_nonnegative_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def _is_positive_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def _is_sha256(value: Any) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value)
    )


REMOVAL_REASON_CODES = frozenset(
    {
        REASON_THOUGHT_REMOVED,
        "coding_thought_removed",
        "coding_hidden_reasoning_removed",
    }
)
ACCEPTED_TRANSFORM_VERSIONS = frozenset({str(TRANSFORM_VERSION), "2", "3"})


def _hidden_removed(mapping: Any) -> Any:
    if not isinstance(mapping, dict):
        return None
    if "thought_fields_removed" in mapping:
        return mapping["thought_fields_removed"]
    return mapping.get("hidden_reasoning_fields_removed")


def _dual_removal_mismatch(mapping: Any, where: str) -> str | None:
    """Return a violation when both removal fields exist and disagree."""
    if not isinstance(mapping, dict):
        return None
    if (
        "thought_fields_removed" not in mapping
        or "hidden_reasoning_fields_removed" not in mapping
    ):
        return None
    thought = mapping["thought_fields_removed"]
    hidden = mapping["hidden_reasoning_fields_removed"]
    if thought != hidden:
        return (
            f"{where}: thought_fields_removed {thought!r} disagrees with "
            f"hidden_reasoning_fields_removed {hidden!r}"
        )
    return None


def _reason_code_set(value: Any, where: str, violations: list[str]) -> set[str]:
    if not isinstance(value, list):
        violations.append(f"{where}: reason codes are not a list")
        return set()
    invalid = [item for item in value if not isinstance(item, str) or not item]
    if invalid:
        violations.append(f"{where}: invalid reason codes {invalid!r}")
    return {item for item in value if isinstance(item, str) and item}


class _ManifestSteps(NamedTuple):
    source_count: int | None
    recorded_counts: dict[str, int | None]
    actions: list[Any]
    valid_actions: list[dict[str, Any]]
    retained: int
    migrated: int
    excluded: int


def _has_source_path(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    return bool(value)


def _step_index_and_removal_violations(
    entry: dict[str, Any],
    step_where: str,
    reasons: set[str],
) -> list[str]:
    violations = []
    if not _is_positive_int(entry.get("source_step_index")):
        violations.append(f"{step_where}: source step index must be a positive integer")
    thought_fields_removed = _hidden_removed(entry)
    if not _is_nonnegative_int(thought_fields_removed):
        violations.append(
            f"{step_where}: thought_fields_removed must be a non-negative integer"
        )
        return violations
    reports_removal = bool(REMOVAL_REASON_CODES.intersection(reasons))
    if bool(thought_fields_removed) != reports_removal:
        violations.append(
            f"{step_where}: thought removal count and reason code disagree"
        )
    return violations


def _non_object_step_removal_violations(
    reasons: set[str],
    thought_fields_removed: Any,
    step_where: str,
) -> list[str]:
    if REASON_STEP_NOT_OBJECT not in reasons:
        return []
    violations = []
    if thought_fields_removed:
        violations.append(
            f"{step_where}: non-object step cannot report thought removals"
        )
    if REMOVAL_REASON_CODES.intersection(reasons):
        violations.append(
            f"{step_where}: non-object step cannot claim hidden-reasoning removal"
        )
    return violations


def _excluded_step_action_violations(
    entry: dict[str, Any],
    step_where: str,
    reasons: set[str],
) -> list[str]:
    violations = []
    step_exclusions = STEP_EXCLUSION_REASONS.intersection(reasons)
    if len(step_exclusions) != 1:
        violations.append(
            f"{step_where}: excluded without an exclusion reason code; "
            "expected exactly one step exclusion reason code"
        )
    impossible_reasons = reasons - (STEP_EXCLUSION_REASONS | REMOVAL_REASON_CODES)
    if impossible_reasons:
        violations.append(
            f"{step_where}: excluded with impossible reason codes "
            f"{sorted(impossible_reasons)}"
        )
    if entry.get("evidence_source") is not None:
        violations.append(f"{step_where}: excluded step records an evidence source")
    if entry.get("output_step_index") is not None:
        violations.append(f"{step_where}: excluded step keeps an output index")
    violations.extend(
        _non_object_step_removal_violations(
            reasons, _hidden_removed(entry), step_where
        )
    )
    return violations


def _retained_evidence_violation(
    evidence: Any,
    reasons: set[str],
    step_where: str,
) -> str | None:
    if not isinstance(evidence, str):
        return f"{step_where}: retained without a visible evidence source"
    if evidence not in _EVIDENCE_REASON:
        return f"{step_where}: retained without a visible evidence source"
    if _EVIDENCE_REASON[evidence] in reasons:
        return None
    return f"{step_where}: reason codes do not record the {evidence} evidence source"


def _retained_step_reports_removals(action: Any, thought_fields_removed: Any) -> bool:
    if action != "retained":
        return False
    return thought_fields_removed != 0


def _retained_step_action_violations(
    entry: dict[str, Any],
    step_where: str,
    reasons: set[str],
) -> list[str]:
    violations = []
    if not _is_positive_int(entry.get("output_step_index")):
        violations.append(
            f"{step_where}: retained output step index must be a positive integer"
        )
    evidence_violation = _retained_evidence_violation(
        entry.get("evidence_source"), reasons, step_where
    )
    if evidence_violation:
        violations.append(evidence_violation)
    evidence_reasons = STEP_EVIDENCE_REASONS.intersection(reasons)
    if len(evidence_reasons) != 1:
        violations.append(
            f"{step_where}: retained step must record exactly one evidence reason"
        )
    impossible_reasons = reasons - STEP_RETAINED_REASONS
    if impossible_reasons:
        violations.append(
            f"{step_where}: retained with impossible reason codes "
            f"{sorted(impossible_reasons)}"
        )
    if _retained_step_reports_removals(entry.get("action"), _hidden_removed(entry)):
        violations.append(f"{step_where}: retained step reports thought removals")
    return violations


def _step_action_violations(entry: dict[str, Any], where: str) -> list[str]:
    """Return acceptance violations for one step-level manifest entry."""
    index = entry.get("source_step_index")
    step_where = f"{where} step {index}"
    violations: list[str] = []
    reasons = _reason_code_set(entry.get("reason_codes"), step_where, violations)
    if not reasons:
        violations.append(f"{step_where}: no reason codes recorded")
    violations.extend(_step_index_and_removal_violations(entry, step_where, reasons))
    action = entry.get("action")
    if action == "excluded":
        violations.extend(_excluded_step_action_violations(entry, step_where, reasons))
        return violations
    if action in {"migrated", "retained"}:
        violations.extend(_retained_step_action_violations(entry, step_where, reasons))
        return violations
    violations.append(f"{step_where}: unknown step action {action!r}")
    return violations
