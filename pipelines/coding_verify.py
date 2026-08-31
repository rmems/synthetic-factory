"""Verify curated coding records against their manifests."""

from __future__ import annotations

from collections import Counter
from typing import Any, NamedTuple

from coding_constants import (
    MAX_DECISION_BASIS_CHARS,
    REASON_BASIS_CONCISED,
    VISIBLE_BASIS_LABELS,
    WRAP_STEPS_PARENT,
)
from coding_verify_manifest import _verify_one_manifest
from coding_verify_steps import (
    _dual_removal_mismatch,
    _hidden_removed,
    _is_nonnegative_int,
    _is_positive_int,
)


def _derive_decision_basis(step: dict[str, Any]):
    from curate_coding import _derive_decision_basis as impl

    return impl(step)


def _record_id(record: Any) -> str | None:
    from curate_coding import _record_id as impl

    return impl(record)


def _record_steps(record: Any):
    from curate_coding import _record_steps as impl

    return impl(record)


def contains_thought_key(value: Any) -> bool:
    from curate_coding import contains_thought_key as impl

    return impl(value)


def hash_value(value: Any) -> str:
    from curate_coding import hash_value as impl

    return impl(value)


class _ManifestTotals(NamedTuple):
    counts: Counter
    thought_fields_removed: int
    evidence_sources: Counter
    wrap_records: int


def _decision_basis_grounding_violation(
    step: dict[str, Any],
    basis: str,
    step_where: str,
) -> str | None:
    expected_basis, _, _ = _derive_decision_basis(step)
    if expected_basis is None:
        return f"{step_where}: decision_basis has no visible evidence to ground it"
    if basis == expected_basis:
        return None
    return f"{step_where}: decision_basis is not grounded in its visible evidence"


def _curated_step_violations(step: Any, step_where: str) -> list[str]:
    if not isinstance(step, dict):
        return [f"{step_where}: curated step is not an object"]
    basis = step.get("decision_basis")
    if not isinstance(basis, str):
        return [f"{step_where}: missing a non-empty decision_basis"]
    if not basis.strip():
        return [f"{step_where}: missing a non-empty decision_basis"]
    violations = []
    if not basis.startswith(VISIBLE_BASIS_LABELS):
        violations.append(
            f"{step_where}: decision_basis does not open with a visible evidence label"
        )
    grounding = _decision_basis_grounding_violation(step, basis, step_where)
    if grounding:
        violations.append(grounding)
    if len(basis) > MAX_DECISION_BASIS_CHARS:
        violations.append(
            f"{step_where}: decision_basis exceeds {MAX_DECISION_BASIS_CHARS} chars"
        )
    return violations


def _curated_record_violations(record: Any, where: str) -> list[str]:
    """Return acceptance violations for one curated output record."""
    violations = []
    if contains_thought_key(record):
        violations.append(f"{where}: curated record still exposes a thought key")
    steps = _record_steps(record)
    if not isinstance(steps, list):
        violations.append(f"{where}: curated record has no retained steps")
        return violations
    if not steps:
        violations.append(f"{where}: curated record has no retained steps")
        return violations
    for index, step in enumerate(steps, 1):
        violations.extend(_curated_step_violations(step, f"{where} step {index}"))
    return violations


def _as_record_list(result: dict[str, Any], violations: list[str]) -> list[Any]:
    record_value = result.get("records")
    if isinstance(record_value, list):
        return record_value
    violations.append("curated records are not a list")
    return []


def _all_curated_record_violations(records: list[Any]) -> list[str]:
    violations = []
    for index, record in enumerate(records, 1):
        violations.extend(_curated_record_violations(record, f"record {index}"))
    return violations


def _is_emitting_manifest(manifest: Any) -> bool:
    if not isinstance(manifest, dict):
        return False
    return manifest.get("action") in {"modified", "unchanged"}


def _emitting_manifests(manifests: list[Any]) -> list[dict[str, Any]]:
    emitting = []
    for manifest in manifests:
        if _is_emitting_manifest(manifest):
            emitting.append(manifest)
    return emitting


def _record_output_hash(record: Any) -> str | None:
    try:
        return hash_value(record)
    except (TypeError, ValueError, RecursionError):
        return None


def _reports_concised(reasons: Any) -> bool:
    if not isinstance(reasons, list):
        return False
    return REASON_BASIS_CONCISED in reasons


def _step_evidence_binding_violations(
    entry: dict[str, Any],
    step: dict[str, Any],
    index: int,
    output_index: int,
) -> list[str]:
    violations = []
    _, evidence_source, concised = _derive_decision_basis(step)
    if entry.get("evidence_source") != evidence_source:
        violations.append(
            f"record {index} step {output_index}: visible evidence source "
            "does not match its manifest action"
        )
    if concised != _reports_concised(entry.get("reason_codes")):
        violations.append(
            f"record {index} step {output_index}: concision reason does not "
            "match visible evidence"
        )
    if entry.get("source_step_number") != step.get("n"):
        violations.append(
            f"record {index} step {output_index}: source step number does not "
            "match the retained output step"
        )
    return violations


def _one_retained_step_binding(
    entry: Any,
    steps: list[Any],
    index: int,
) -> list[str]:
    if not isinstance(entry, dict):
        return []
    if entry.get("action") not in {"migrated", "retained"}:
        return []
    output_index = entry.get("output_step_index")
    if not _is_positive_int(output_index):
        return [
            f"record {index}: output step index {output_index!r} is out of range"
        ]
    if output_index > len(steps):
        return [
            f"record {index}: output step index {output_index!r} is out of range"
        ]
    step = steps[output_index - 1]
    if not isinstance(step, dict):
        return []
    return _step_evidence_binding_violations(entry, step, index, output_index)


def _retained_step_binding_violations(
    record: Any,
    manifest: dict[str, Any],
    index: int,
) -> list[str]:
    steps = _record_steps(record)
    actions = manifest.get("step_actions")
    if not isinstance(steps, list):
        return []
    if not isinstance(actions, list):
        return []
    violations = []
    for entry in actions:
        violations.extend(_one_retained_step_binding(entry, steps, index))
    return violations


def _one_record_binding_violations(
    record: Any,
    manifest: dict[str, Any],
    index: int,
) -> list[str]:
    actual_hash = _record_output_hash(record)
    if actual_hash is None:
        return [f"record {index}: curated record is not JSON-serializable"]
    violations = []
    if manifest.get("output_hash") != actual_hash:
        violations.append(
            f"record {index}: output hash does not match its manifest entry"
        )
    if manifest.get("output_id") != _record_id(record):
        violations.append(
            f"record {index}: output ID does not match its manifest entry"
        )
    violations.extend(_retained_step_binding_violations(record, manifest, index))
    return violations


def _record_manifest_binding_violations(
    records: list[Any],
    emitting: list[dict[str, Any]],
) -> list[str]:
    violations = []
    for index, (record, manifest) in enumerate(zip(records, emitting), 1):
        violations.extend(_one_record_binding_violations(record, manifest, index))
    return violations


def _nonnegative_count_slice(counts: dict[str, Any]) -> dict[str, int]:
    sliced: dict[str, int] = {}
    for key in ("source", "retained", "migrated", "excluded"):
        value = counts.get(key)
        if _is_nonnegative_int(value):
            sliced[key] = value
    return sliced


def _retained_evidence_source(entry: Any) -> str | None:
    if not isinstance(entry, dict):
        return None
    if entry.get("action") not in {"migrated", "retained"}:
        return None
    evidence = entry.get("evidence_source")
    if not isinstance(evidence, str):
        return None
    if not evidence:
        return None
    return evidence


def _retained_evidence_sources(manifest: dict[str, Any]) -> Counter:
    evidence_sources: Counter = Counter()
    actions = manifest.get("step_actions")
    if not isinstance(actions, list):
        return evidence_sources
    for entry in actions:
        evidence = _retained_evidence_source(entry)
        if evidence is not None:
            evidence_sources[evidence] += 1
    return evidence_sources


def _one_manifest_totals(manifest: Any) -> _ManifestTotals:
    empty = _ManifestTotals(Counter(), 0, Counter(), 0)
    if not isinstance(manifest, dict):
        return empty
    counts: Counter = Counter()
    step_counts = manifest.get("step_counts")
    if isinstance(step_counts, dict):
        counts.update(_nonnegative_count_slice(step_counts))
    removed = _hidden_removed(manifest)
    thought = removed if _is_nonnegative_int(removed) else 0
    wrap_records = int(manifest.get("steps_path") == f"{WRAP_STEPS_PARENT}.steps")
    return _ManifestTotals(
        counts,
        thought,
        _retained_evidence_sources(manifest),
        wrap_records,
    )


def _manifest_totals(manifests: list[Any]) -> _ManifestTotals:
    counts: Counter = Counter()
    thought_fields_removed = 0
    evidence_sources: Counter = Counter()
    wrap_records = 0
    for manifest in manifests:
        piece = _one_manifest_totals(manifest)
        counts.update(piece.counts)
        thought_fields_removed += piece.thought_fields_removed
        evidence_sources.update(piece.evidence_sources)
        wrap_records += piece.wrap_records
    return _ManifestTotals(
        counts,
        thought_fields_removed,
        evidence_sources,
        wrap_records,
    )


def _record_step_count(record: Any) -> int:
    steps = _record_steps(record)
    if steps is None:
        return 0
    return len(steps)


def _is_excluded_manifest(manifest: Any) -> bool:
    if not isinstance(manifest, dict):
        return False
    return manifest.get("action") == "excluded"


def _expected_summary(
    summary: dict[str, Any],
    manifests: list[Any],
    emitting: list[dict[str, Any]],
    totals: _ManifestTotals,
) -> dict[str, Any]:
    expected: dict[str, Any] = {
        "input_records": len(manifests),
        "output_records": len(emitting),
        "excluded_records": sum(
            _is_excluded_manifest(manifest) for manifest in manifests
        ),
        "source_steps": totals.counts["source"],
        "retained_steps": totals.counts["retained"],
        "migrated_steps": totals.counts["migrated"],
        "excluded_steps": totals.counts["excluded"],
        "decision_basis_sources": dict(sorted(totals.evidence_sources.items())),
    }
    has_hidden = "hidden_reasoning_fields_removed" in summary
    has_thought = "thought_fields_removed" in summary
    if has_hidden:
        expected["hidden_reasoning_fields_removed"] = totals.thought_fields_removed
    if "wrap_records" in summary:
        expected["wrap_records"] = totals.wrap_records
    if has_thought:
        expected["thought_fields_removed"] = totals.thought_fields_removed
        return expected
    if has_hidden:
        return expected
    expected["hidden_reasoning_fields_removed"] = totals.thought_fields_removed
    return expected


def _summary_reconcile_violations(
    result: dict[str, Any],
    manifests: list[Any],
    emitting: list[dict[str, Any]],
    totals: _ManifestTotals,
) -> list[str]:
    summary = result.get("summary")
    if not isinstance(summary, dict):
        return ["curation summary is not an object"]
    violations = []
    mismatch = _dual_removal_mismatch(summary, "summary")
    if mismatch:
        violations.append(mismatch)
    expected = _expected_summary(summary, manifests, emitting, totals)
    for key, value in expected.items():
        if summary.get(key) != value:
            violations.append(
                f"summary {key} {summary.get(key)!r} does not match {value}"
            )
    return violations


def _expected_source_step_mismatch(
    expected_source_steps: int | None,
    total_source: int,
) -> str | None:
    if expected_source_steps is None:
        return None
    if total_source == expected_source_steps:
        return None
    return (
        f"expected {expected_source_steps} source steps, manifest accounts for "
        f"{total_source}"
    )


def verify_manifest(
    manifests: Any,
    *,
    expected_source_steps: int | None = None,
) -> list[str]:
    """Return acceptance violations found in a curation manifest.

    The manifest alone proves the migration accounting: every source step is
    either migrated/retained with a visible evidence source or excluded with a
    reason code, and the per-record counts reconcile with the step actions.
    """
    if not isinstance(manifests, list):
        return ["manifest collection is not a list"]
    violations: list[str] = []
    total_source = 0
    seen_source_locations: set[tuple[str, int]] = set()
    for manifest in manifests:
        total_source += _verify_one_manifest(
            manifest, seen_source_locations, violations
        )
    mismatch = _expected_source_step_mismatch(expected_source_steps, total_source)
    if mismatch:
        violations.append(mismatch)
    return violations


def verify_curation(
    result: Any,
    *,
    expected_source_steps: int | None = None,
) -> list[str]:
    """Return every acceptance violation in a :func:`curate_jsonl` result.

    A clean run proves the lane contract: no curated step exposes a thought
    field, every retained step carries a concise decision_basis grounded in a
    visible label, and every source step is migrated or excluded with a reason
    code.
    """
    if not isinstance(result, dict):
        return ["curation result is not an object"]
    manifest_value = result.get("manifest")
    violations = verify_manifest(
        manifest_value, expected_source_steps=expected_source_steps
    )
    manifests = manifest_value if isinstance(manifest_value, list) else []
    records = _as_record_list(result, violations)
    violations.extend(_all_curated_record_violations(records))
    emitting = _emitting_manifests(manifests)
    if len(records) != len(emitting):
        violations.append(
            f"curated output has {len(records)} records but the manifest emits "
            f"{len(emitting)}"
        )
    violations.extend(_record_manifest_binding_violations(records, emitting))
    totals = _manifest_totals(manifests)
    retained = sum(_record_step_count(record) for record in records)
    if retained != totals.counts["retained"]:
        violations.append(
            f"curated output has {retained} steps but the manifest retains "
            f"{totals.counts['retained']}"
        )
    violations.extend(
        _summary_reconcile_violations(result, manifests, emitting, totals)
    )
    return violations
