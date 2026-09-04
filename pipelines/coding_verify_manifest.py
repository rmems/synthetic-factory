"""Record-level coding-curation manifest verification."""

from __future__ import annotations

from typing import Any, NamedTuple

if __package__:
    from .coding_constants import (
        EXCLUSION_REASONS,
        PRE_STEP_EXCLUSION_REASONS,
        REASON_NO_RETAINABLE_STEPS,
        REASON_STEPS_EXCLUDED,
        REASON_STEPS_MIGRATED,
        REASON_WRAP_RECORD,
        RECORD_STRUCTURAL_REASONS,
        RECORD_TRANSFORMATION_REASONS,
        STEP_EXCLUSION_REASONS,
        TRANSFORM_NAME,
        TRANSFORM_VERSION,
        WRAP_STEPS_PARENT,
    )
    from .coding_verify_steps import (
        ACCEPTED_TRANSFORM_VERSIONS,
        REMOVAL_REASON_CODES,
        _ManifestSteps,
        _dual_removal_mismatch,
        _has_source_path,
        _hidden_removed,
        _is_nonnegative_int,
        _is_positive_int,
        _is_sha256,
        _reason_code_set,
        _step_action_violations,
    )
else:
    from coding_constants import (
        EXCLUSION_REASONS,
        PRE_STEP_EXCLUSION_REASONS,
        REASON_NO_RETAINABLE_STEPS,
        REASON_STEPS_EXCLUDED,
        REASON_STEPS_MIGRATED,
        REASON_WRAP_RECORD,
        RECORD_STRUCTURAL_REASONS,
        RECORD_TRANSFORMATION_REASONS,
        STEP_EXCLUSION_REASONS,
        TRANSFORM_NAME,
        TRANSFORM_VERSION,
        WRAP_STEPS_PARENT,
    )
    from coding_verify_steps import (
        ACCEPTED_TRANSFORM_VERSIONS,
        REMOVAL_REASON_CODES,
        _ManifestSteps,
        _dual_removal_mismatch,
        _has_source_path,
        _hidden_removed,
        _is_nonnegative_int,
        _is_positive_int,
        _is_sha256,
        _reason_code_set,
        _step_action_violations,
    )


class _ManifestCheck(NamedTuple):
    where: str
    reasons: set[str]
    thought_fields_removed: Any
    steps: _ManifestSteps


def _manifest_where(manifest: dict[str, Any]) -> str:
    return f"{manifest.get('source_path')}:{manifest.get('source_line')}"


def _duplicate_source_location(
    source_path: Any,
    source_line: Any,
    seen_source_locations: set[tuple[str, int]],
    where: str,
) -> str | None:
    if not _has_source_path(source_path):
        return None
    if not _is_positive_int(source_line):
        return None
    location = (source_path, source_line)
    if location in seen_source_locations:
        return f"{where}: duplicate manifest source location"
    seen_source_locations.add(location)
    return None


def _manifest_identity_violations(
    manifest: dict[str, Any],
    where: str,
    seen_source_locations: set[tuple[str, int]],
) -> list[str]:
    violations = []
    source_path = manifest.get("source_path")
    source_line = manifest.get("source_line")
    if not _has_source_path(source_path):
        violations.append(f"{where}: manifest records no source path")
    if not _is_positive_int(source_line):
        violations.append(f"{where}: source line must be a positive integer")
    duplicate = _duplicate_source_location(
        source_path, source_line, seen_source_locations, where
    )
    if duplicate:
        violations.append(duplicate)
    if manifest.get("transform") != TRANSFORM_NAME:
        violations.append(f"{where}: manifest is not a {TRANSFORM_NAME} manifest")
    if str(manifest.get("transform_version")) not in ACCEPTED_TRANSFORM_VERSIONS:
        violations.append(
            f"{where}: manifest transform version is not {TRANSFORM_VERSION}"
        )
    if not _is_sha256(manifest.get("source_hash")):
        violations.append(f"{where}: manifest records no valid source hash")
    return violations


def _excluded_record_step_only_violation(
    reasons: set[str],
    where: str,
) -> str | None:
    step_only = STEP_EXCLUSION_REASONS.intersection(reasons)
    if not step_only:
        return None
    if REASON_NO_RETAINABLE_STEPS in reasons:
        return None
    return f"{where}: excluded with step-only reason codes {sorted(step_only)}"


def _excluded_record_violations(
    manifest: dict[str, Any],
    where: str,
    reasons: set[str],
) -> list[str]:
    violations = []
    allowed = PRE_STEP_EXCLUSION_REASONS | {REASON_NO_RETAINABLE_STEPS}
    if not allowed.intersection(reasons):
        violations.append(
            f"{where}: record excluded without an exclusion reason code"
        )
    extra_reasons = reasons - EXCLUSION_REASONS - RECORD_STRUCTURAL_REASONS
    if extra_reasons:
        violations.append(
            f"{where}: excluded with unknown reason codes {sorted(extra_reasons)}"
        )
    step_only = _excluded_record_step_only_violation(reasons, where)
    if step_only:
        violations.append(step_only)
    if manifest.get("output_hash") is not None:
        violations.append(f"{where}: excluded record still records an output hash")
    if manifest.get("output_id") is not None:
        violations.append(f"{where}: excluded record still records an output ID")
    return violations


def _retained_record_hash_violations(manifest: dict[str, Any], where: str) -> list[str]:
    if _is_sha256(manifest.get("output_hash")):
        return []
    return [f"{where}: retained record records no valid output hash"]


def _manifest_record_action_violations(
    manifest: dict[str, Any],
    where: str,
    reasons: set[str],
) -> list[str]:
    action = manifest.get("action")
    if action == "excluded":
        return _excluded_record_violations(manifest, where, reasons)
    if action in {"modified", "unchanged"}:
        return _retained_record_hash_violations(manifest, where)
    return [f"{where}: unknown record action {action!r}"]


def _wrap_reason_unbound(
    manifest: dict[str, Any],
    reasons: set[str],
    wrap_path: str,
    where: str,
) -> str | None:
    if REASON_WRAP_RECORD not in reasons:
        return None
    if manifest.get("steps_path") == wrap_path:
        return None
    return f"{where}: wrap reason is not bound to {wrap_path}"


def _wrap_path_unmarked(
    manifest: dict[str, Any],
    reasons: set[str],
    wrap_path: str,
    where: str,
) -> str | None:
    if manifest.get("steps_path") != wrap_path:
        return None
    if REASON_WRAP_RECORD in reasons:
        return None
    return f"{where}: wrap step path is missing {REASON_WRAP_RECORD}"


def _manifest_wrap_violations(
    manifest: dict[str, Any],
    where: str,
    reasons: set[str],
) -> list[str]:
    wrap_path = f"{WRAP_STEPS_PARENT}.steps"
    violations = []
    unbound = _wrap_reason_unbound(manifest, reasons, wrap_path, where)
    if unbound:
        violations.append(unbound)
    unmarked = _wrap_path_unmarked(manifest, reasons, wrap_path, where)
    if unmarked:
        violations.append(unmarked)
    return violations


def _manifest_removal_violations(manifest: dict[str, Any], where: str) -> list[str]:
    violations = []
    if not _is_nonnegative_int(_hidden_removed(manifest)):
        violations.append(
            f"{where}: thought_fields_removed must be a non-negative integer"
        )
    mismatch = _dual_removal_mismatch(manifest, where)
    if mismatch:
        violations.append(mismatch)
    return violations


def _pre_step_exclusion_has_steps(counts: dict[str, Any], actions: list[Any]) -> bool:
    if actions:
        return True
    for key in ("source", "retained", "migrated", "excluded"):
        if counts.get(key) not in (0, None):
            return True
    return False


def _pre_step_exclusion_violation(
    reasons: set[str],
    counts: dict[str, Any],
    actions: list[Any],
    where: str,
) -> str | None:
    if not PRE_STEP_EXCLUSION_REASONS.intersection(reasons):
        return None
    if not _pre_step_exclusion_has_steps(counts, actions):
        return None
    return f"{where}: pre-step exclusion must have zero source steps and no step actions"


def _recorded_step_counts(
    counts: dict[str, Any],
    where: str,
    violations: list[str],
) -> dict[str, int | None]:
    recorded: dict[str, int | None] = {}
    for key in ("source", "retained", "migrated", "excluded"):
        value = counts.get(key)
        if _is_nonnegative_int(value):
            recorded[key] = value
            continue
        violations.append(f"{where}: step_counts.{key} must be a non-negative integer")
        recorded[key] = None
    return recorded


def _source_action_length_mismatch(
    source_count: int | None,
    actions: list[Any],
    where: str,
) -> str | None:
    if source_count is None:
        return None
    if source_count == len(actions):
        return None
    return f"{where}: {source_count} source steps but {len(actions)} step actions"


def _valid_step_actions(
    actions: list[Any],
    where: str,
    violations: list[str],
) -> list[dict[str, Any]]:
    valid_actions = []
    for entry in actions:
        if isinstance(entry, dict):
            valid_actions.append(entry)
            violations.extend(_step_action_violations(entry, where))
            continue
        violations.append(f"{where}: step action {entry!r} is not an object")
    return valid_actions


def _tally_one_action(action: Any) -> tuple[int, int, int]:
    if action == "migrated":
        return 1, 1, 0
    if action == "retained":
        return 1, 0, 0
    if action == "excluded":
        return 0, 0, 1
    return 0, 0, 0


def _action_tallies(valid_actions: list[dict[str, Any]]) -> tuple[int, int, int]:
    retained = 0
    migrated = 0
    excluded = 0
    for entry in valid_actions:
        add_retained, add_migrated, add_excluded = _tally_one_action(entry.get("action"))
        retained += add_retained
        migrated += add_migrated
        excluded += add_excluded
    return retained, migrated, excluded


def _parse_manifest_steps(
    manifest: dict[str, Any],
    where: str,
    reasons: set[str],
    violations: list[str],
) -> _ManifestSteps | None:
    counts = manifest.get("step_counts")
    actions = manifest.get("step_actions")
    if not isinstance(counts, dict):
        violations.append(f"{where}: manifest records no step accounting")
        return None
    if not isinstance(actions, list):
        violations.append(f"{where}: manifest records no step accounting")
        return None
    pre_step = _pre_step_exclusion_violation(reasons, counts, actions, where)
    if pre_step:
        violations.append(pre_step)
    recorded_counts = _recorded_step_counts(counts, where, violations)
    length_mismatch = _source_action_length_mismatch(
        recorded_counts["source"], actions, where
    )
    if length_mismatch:
        violations.append(length_mismatch)
    valid_actions = _valid_step_actions(actions, where, violations)
    retained, migrated, excluded = _action_tallies(valid_actions)
    return _ManifestSteps(
        recorded_counts["source"],
        recorded_counts,
        actions,
        valid_actions,
        retained,
        migrated,
        excluded,
    )


def _unclassified_step_actions(steps: _ManifestSteps) -> bool:
    return steps.retained + steps.excluded != len(steps.actions)


def _excluded_record_retained_steps(
    action: Any,
    where: str,
    retained: int,
) -> str | None:
    if action != "excluded":
        return None
    if not retained:
        return None
    label = "steps"
    if retained == 1:
        label = "step"
    return f"{where}: excluded record retains {retained} {label}"


def _retained_record_missing_steps(
    action: Any,
    retained: int,
    where: str,
) -> str | None:
    if action not in {"modified", "unchanged"}:
        return None
    if retained:
        return None
    return f"{where}: retained record must keep at least one step"


def _thought_removal_underaccounts(
    thought_fields_removed: Any,
    steps: _ManifestSteps,
) -> bool:
    if not _is_nonnegative_int(thought_fields_removed):
        return False
    if len(steps.valid_actions) != len(steps.actions):
        return False
    action_thought_counts = [_hidden_removed(entry) for entry in steps.valid_actions]
    if not all(_is_nonnegative_int(value) for value in action_thought_counts):
        return False
    return thought_fields_removed < sum(action_thought_counts)


def _count_key_disagrees(recorded: int | None, expected: int) -> bool:
    if recorded is None:
        return False
    return recorded != expected


def _counts_disagree(
    recorded_counts: dict[str, int | None],
    expected_counts: dict[str, int],
) -> bool:
    for key, expected in expected_counts.items():
        if _count_key_disagrees(recorded_counts[key], expected):
            return True
    return False


def _unchanged_has_transformed_steps(valid_actions: list[dict[str, Any]]) -> bool:
    for entry in valid_actions:
        if entry.get("action") != "retained":
            return True
    return False


def _unchanged_record_violations(
    reasons: set[str],
    thought_fields_removed: Any,
    steps: _ManifestSteps,
    where: str,
) -> list[str]:
    violations = []
    if thought_fields_removed != 0:
        violations.append(f"{where}: unchanged record reports thought removals")
    if _unchanged_has_transformed_steps(steps.valid_actions):
        violations.append(
            f"{where}: unchanged record reports transformed step actions"
        )
    extra = reasons - RECORD_STRUCTURAL_REASONS
    if extra:
        violations.append(
            f"{where}: unchanged record reports transformation reason codes"
        )
    return violations


def _step_reason_count_mismatch(migrated: int, excluded: int, reasons: set[str]) -> bool:
    if bool(migrated) != (REASON_STEPS_MIGRATED in reasons):
        return True
    return bool(excluded) != (REASON_STEPS_EXCLUDED in reasons)


def _modified_without_evidence(thought_fields_removed: Any, steps: _ManifestSteps) -> bool:
    if thought_fields_removed != 0:
        return False
    if steps.migrated != 0:
        return False
    return steps.excluded == 0


def _modified_record_violations(
    reasons: set[str],
    thought_fields_removed: Any,
    steps: _ManifestSteps,
    where: str,
) -> list[str]:
    if not _is_nonnegative_int(thought_fields_removed):
        return []
    violations = []
    impossible = reasons - RECORD_TRANSFORMATION_REASONS - RECORD_STRUCTURAL_REASONS
    if impossible:
        violations.append(
            f"{where}: modified record reports impossible reason codes "
            f"{sorted(impossible)}"
        )
    reports_removal = bool(REMOVAL_REASON_CODES.intersection(reasons))
    if bool(thought_fields_removed) != reports_removal:
        violations.append(
            f"{where}: thought removal count and reason code disagree"
        )
    if _step_reason_count_mismatch(steps.migrated, steps.excluded, reasons):
        violations.append(
            f"{where}: step transformation counts and reason codes disagree"
        )
    if _modified_without_evidence(thought_fields_removed, steps):
        violations.append(
            f"{where}: modified record reports no transformation evidence"
        )
    return violations


def _manifest_transform_state_violations(
    action: Any,
    check: _ManifestCheck,
) -> list[str]:
    if action == "unchanged":
        return _unchanged_record_violations(
            check.reasons, check.thought_fields_removed, check.steps, check.where
        )
    if action != "modified":
        return []
    return _modified_record_violations(
        check.reasons, check.thought_fields_removed, check.steps, check.where
    )


def _retained_output_indexes(valid_actions: list[dict[str, Any]]) -> list[Any]:
    indexes = []
    for entry in valid_actions:
        if entry.get("action") in {"migrated", "retained"}:
            indexes.append(entry.get("output_step_index"))
    return indexes


def _manifest_step_index_violations(where: str, steps: _ManifestSteps) -> list[str]:
    violations = []
    source_indexes = [entry.get("source_step_index") for entry in steps.valid_actions]
    expected_source = list(range(1, len(steps.actions) + 1))
    if source_indexes != expected_source:
        violations.append(
            f"{where}: source step indexes {source_indexes} are not sequential "
            f"{expected_source}"
        )
    output_indexes = _retained_output_indexes(steps.valid_actions)
    expected_output = list(range(1, steps.retained + 1))
    if output_indexes != expected_output:
        violations.append(
            f"{where}: retained output step indexes {output_indexes} are not "
            f"sequential {expected_output}"
        )
    return violations


def _manifest_step_consistency_violations(
    manifest: dict[str, Any],
    check: _ManifestCheck,
) -> list[str]:
    where = check.where
    steps = check.steps
    violations = []
    if _unclassified_step_actions(steps):
        violations.append(f"{where}: step actions are neither retained nor excluded")
    retained_msg = _excluded_record_retained_steps(
        manifest.get("action"), where, steps.retained
    )
    if retained_msg:
        violations.append(retained_msg)
    missing = _retained_record_missing_steps(
        manifest.get("action"), steps.retained, where
    )
    if missing:
        violations.append(missing)
    if _thought_removal_underaccounts(check.thought_fields_removed, steps):
        violations.append(
            f"{where}: thought_fields_removed does not account for the step actions"
        )
    expected_counts = {
        "source": len(steps.actions),
        "retained": steps.retained,
        "migrated": steps.migrated,
        "excluded": steps.excluded,
    }
    if _counts_disagree(steps.recorded_counts, expected_counts):
        violations.append(
            f"{where}: step counts {manifest.get('step_counts')} disagree with "
            "the recorded step actions"
        )
    violations.extend(
        _manifest_transform_state_violations(manifest.get("action"), check)
    )
    violations.extend(_manifest_step_index_violations(where, steps))
    return violations


def _verify_one_manifest(
    manifest: Any,
    seen_source_locations: set[tuple[str, int]],
    violations: list[str],
) -> int:
    if not isinstance(manifest, dict):
        violations.append(f"manifest entry {manifest!r} is not an object")
        return 0
    where = _manifest_where(manifest)
    violations.extend(
        _manifest_identity_violations(manifest, where, seen_source_locations)
    )
    reasons = _reason_code_set(manifest.get("reason_codes"), where, violations)
    violations.extend(_manifest_record_action_violations(manifest, where, reasons))
    violations.extend(_manifest_wrap_violations(manifest, where, reasons))
    violations.extend(_manifest_removal_violations(manifest, where))
    steps = _parse_manifest_steps(manifest, where, reasons, violations)
    if steps is None:
        return 0
    violations.extend(
        _manifest_step_consistency_violations(
            manifest,
            _ManifestCheck(where, reasons, _hidden_removed(manifest), steps),
        )
    )
    source_count = steps.source_count
    if source_count is None:
        return 0
    return source_count
