#!/usr/bin/env python3
"""Curate legacy coding episodes into observable, reasoning-free records.

The transform is deliberately record-level and side-effect free by default.
It removes every mapping key that carries model-private reasoning -- the
shared scratch-pad vocabulary (``thought``, ``chain_of_thought``, ``scratch``,
and ``inner_monologue``), the coding-factory key ``reasoning``,
``internal_reasoning``, ``internal_reasoning_verbatim``, and any other
``internal_reasoning*`` variant -- and derives a concise
``decision_basis`` only from fields that are visible in the source record:
plan, reflection, observation, or tool call.
Steps without usable visible evidence are excluded with machine-readable
reason codes; the transform never consults the removed reasoning text.

Two source shapes are handled. A plain coding episode carries its turns in a
top-level ``steps`` array. A *wrap* record (a Thalamic gate record whose
``executed_action`` embeds the coding episode) carries them in
``executed_action.steps`` and holds its own hidden reasoning in
``proposed_action.internal_reasoning``. Both are curated with the same
step rule; only the location of the step array differs.

``curate_jsonl`` returns curated records, a reversible manifest, and summary
counts.  The optional CLI writes only to new, non-raw files.  ``--output-dir``
curates every JSONL beneath a source directory, preserves relative paths, and
emits one aggregate manifest for the complete lane.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import sys
import re
from collections import Counter
from pathlib import Path
from typing import Any

from validate_run import HIDDEN_THOUGHT_KEYS


TRANSFORM_NAME = "coding_observability"
# Version 3 keeps the version-2 wrap support and additionally aligns the
# transform with the structural audit's complete hidden-thought vocabulary.
TRANSFORM_VERSION = "3"
MAX_DECISION_BASIS_CHARS = 240
RUN_MANIFEST_FILENAME = "manifest.jsonl"

# Exact key names that never reach a curated record, plus the
# ``internal_reasoning`` prefix that covers ``internal_reasoning_verbatim``,
# ``internal_reasoning_optimizer``, and every other published variant.
# ``reasoning`` is the coding-factory contract key
# (prompts/04-agentic-coding-trajectory-factory.md) and is an exact match
# only, so nearby names such as ``reasoning_flaw`` stay visible.
HIDDEN_REASONING_KEYS = HIDDEN_THOUGHT_KEYS | frozenset(
    {"internal_reasoning", "internal_reasoning_verbatim", "reasoning"}
)
HIDDEN_REASONING_PREFIX = "internal_reasoning"

WRAP_STEPS_PARENT = "executed_action"

REASON_HIDDEN_REASONING_REMOVED = "coding_hidden_reasoning_removed"
REASON_BASIS_CONCISED = "coding_basis_concised"
REASON_BASIS_FROM_PLAN = "coding_basis_from_plan"
REASON_BASIS_FROM_REFLECTION = "coding_basis_from_reflection"
REASON_BASIS_FROM_OBSERVATION = "coding_basis_from_observation"
REASON_BASIS_FROM_TOOL_CALL = "coding_basis_from_tool_call"
REASON_STEP_NOT_OBJECT = "coding_step_not_object"
REASON_NO_VISIBLE_EVIDENCE = "coding_no_visible_decision_evidence"
REASON_NO_RETAINABLE_STEPS = "coding_no_retainable_steps"
REASON_STEPS_MIGRATED = "coding_steps_migrated"
REASON_STEPS_EXCLUDED = "coding_steps_excluded"
REASON_WRAP_RECORD = "coding_wrap_record"
REASON_RECORD_NOT_OBJECT = "coding_record_not_object"
REASON_STEPS_NOT_ARRAY = "coding_steps_not_array"
REASON_INVALID_JSON = "coding_invalid_json"
REASON_INVALID_UTF8 = "coding_invalid_utf8"

_EVIDENCE_REASON = {
    "plan": REASON_BASIS_FROM_PLAN,
    "reflection": REASON_BASIS_FROM_REFLECTION,
    "observation": REASON_BASIS_FROM_OBSERVATION,
    "tool_call": REASON_BASIS_FROM_TOOL_CALL,
}

REASON_THOUGHT_REMOVED = "coding_thought_removed"

VISIBLE_BASIS_LABELS = ("Plan: ", "Reflection: ", "Observation: ", "Tool call: ")
EXCLUSION_REASONS = frozenset(
    {
        REASON_STEP_NOT_OBJECT,
        REASON_NO_VISIBLE_EVIDENCE,
        REASON_NO_RETAINABLE_STEPS,
        REASON_RECORD_NOT_OBJECT,
        REASON_STEPS_NOT_ARRAY,
        REASON_INVALID_JSON,
        REASON_INVALID_UTF8,
    }
)
STEP_EXCLUSION_REASONS = frozenset(
    {REASON_STEP_NOT_OBJECT, REASON_NO_VISIBLE_EVIDENCE}
)
PRE_STEP_EXCLUSION_REASONS = frozenset(
    {
        REASON_RECORD_NOT_OBJECT,
        REASON_STEPS_NOT_ARRAY,
        REASON_INVALID_JSON,
        REASON_INVALID_UTF8,
    }
)
STEP_EVIDENCE_REASONS = frozenset(_EVIDENCE_REASON.values())
STEP_RETAINED_REASONS = frozenset(
    {
        *STEP_EVIDENCE_REASONS,
        REASON_THOUGHT_REMOVED,
        REASON_HIDDEN_REASONING_REMOVED,
        REASON_BASIS_CONCISED,
    }
)
STEP_ALLOWED_REASONS = frozenset({*STEP_EXCLUSION_REASONS, *STEP_RETAINED_REASONS})
RECORD_TRANSFORMATION_REASONS = frozenset(
    {
        REASON_THOUGHT_REMOVED,
        REASON_HIDDEN_REASONING_REMOVED,
        REASON_STEPS_MIGRATED,
        REASON_STEPS_EXCLUDED,
    }
)
RECORD_STRUCTURAL_REASONS = frozenset({REASON_WRAP_RECORD})



def canonical_json(value: Any) -> str:
    """Return the stable JSON representation used for output hashes."""
    return json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )


def hash_value(value: Any) -> str:
    """Hash a parsed value deterministically."""
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def normalized_key_name(value: Any) -> str:
    """Normalize JSON keys across case, separators, and camel-case boundaries."""
    return re.sub(
        r"[^a-z0-9]+",
        "_",
        re.sub(r"(?<=[a-z0-9])(?=[A-Z])", "_", str(value)).casefold(),
    ).strip("_")


def is_hidden_reasoning_key(key: Any) -> bool:
    """Return whether ``key`` names model-private reasoning text.

    Matches the structural audit's scratch-pad vocabulary, the exact
    coding-factory key ``reasoning``, and the whole ``internal_reasoning*``
    family so a published private-reasoning variant cannot slip into a
    curated record unnoticed.
    """
    normalized = normalized_key_name(key)
    return normalized in HIDDEN_REASONING_KEYS or normalized.startswith(
        HIDDEN_REASONING_PREFIX
    )


def _strip_hidden_reasoning_keys(value: Any) -> tuple[Any, int]:
    """Deep-copy ``value`` while removing every hidden-reasoning mapping key."""
    if isinstance(value, dict):
        cleaned = {}
        removed = 0
        for key, item in value.items():
            if is_hidden_reasoning_key(key):
                removed += 1
                continue
            clean_item, nested_removed = _strip_hidden_reasoning_keys(item)
            cleaned[key] = clean_item
            removed += nested_removed
        return cleaned, removed
    if isinstance(value, list):
        cleaned_items = []
        removed = 0
        for item in value:
            clean_item, nested_removed = _strip_hidden_reasoning_keys(item)
            cleaned_items.append(clean_item)
            removed += nested_removed
        return cleaned_items, removed
    return copy.deepcopy(value), 0


def contains_hidden_reasoning_key(value: Any) -> bool:
    """Return whether any nested mapping still exposes hidden reasoning."""
    if isinstance(value, dict):
        return any(is_hidden_reasoning_key(key) for key in value) or any(
            contains_hidden_reasoning_key(item) for item in value.values()
        )
    if isinstance(value, list):
        return any(contains_hidden_reasoning_key(item) for item in value)
    return False


contains_thought_key = contains_hidden_reasoning_key


def _normalize_text(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    normalized = " ".join(value.split())
    return normalized or None


def _concise(text: str, limit: int = MAX_DECISION_BASIS_CHARS) -> tuple[str, bool]:
    """Normalize text and retain a bounded visible-evidence excerpt."""
    normalized = " ".join(text.split())
    if len(normalized) <= limit:
        return normalized, False

    sentence_ends = []
    for index, character in enumerate(normalized):
        if character in ".!?" and (
            index + 1 == len(normalized) or normalized[index + 1].isspace()
        ):
            if index + 1 <= limit:
                sentence_ends.append(index + 1)
            else:
                break

    if sentence_ends and sentence_ends[-1] >= min(48, limit // 2):
        return normalized[: sentence_ends[-1]], True

    cut = normalized.rfind(" ", 0, limit)
    if cut < max(24, limit // 2):
        cut = limit - 1
    return normalized[:cut].rstrip(" ,;:-") + "…", True


def _visible_value(value: Any) -> str | None:
    """Render a visible evidence field without consulting hidden text."""
    normalized = _normalize_text(value)
    if normalized is not None:
        return normalized
    if isinstance(value, (dict, list)) and value:
        return canonical_json(value)
    return None


def _derive_decision_basis(step: dict[str, Any]) -> tuple[str | None, str | None, bool]:
    for field, label in (
        ("plan", "Plan"),
        ("reflection", "Reflection"),
        ("observation", "Observation"),
    ):
        evidence = _visible_value(step.get(field))
        if evidence is None:
            continue
        basis, concised = _concise(f"{label}: {evidence}")
        return basis, field, concised

    tool_call = step.get("tool_call")
    if isinstance(tool_call, dict) and tool_call:
        tool_name = _normalize_text(tool_call.get("name")) or "unnamed tool"
        args = tool_call.get("args")
        if isinstance(args, (dict, list)) and args:
            evidence = f"{tool_name} with visible arguments {canonical_json(args)}"
        else:
            evidence = tool_name
        basis, concised = _concise(f"Tool call: {evidence}")
        return basis, "tool_call", concised

    tool_text = _normalize_text(tool_call)
    if tool_text is not None:
        basis, concised = _concise(f"Tool call: {tool_text}")
        return basis, "tool_call", concised

    return None, None, False


def curate_step(step: Any, source_step_index: int) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    """Curate one step and return its output plus a step-level manifest entry."""
    manifest: dict[str, Any] = {
        "source_step_index": source_step_index,
        "source_step_number": step.get("n") if isinstance(step, dict) else None,
        "action": "excluded",
        "reason_codes": [],
        "evidence_source": None,
        "hidden_reasoning_fields_removed": 0,
    }
    if not isinstance(step, dict):
        manifest["reason_codes"] = [REASON_STEP_NOT_OBJECT]
        return None, manifest

    cleaned, removed = _strip_hidden_reasoning_keys(step)
    manifest["hidden_reasoning_fields_removed"] = removed
    basis, evidence_source, concised = _derive_decision_basis(cleaned)
    if basis is None:
        reasons = []
        if removed:
            reasons.append(REASON_HIDDEN_REASONING_REMOVED)
        reasons.append(REASON_NO_VISIBLE_EVIDENCE)
        manifest["reason_codes"] = reasons
        return None, manifest

    prior_basis = cleaned.get("decision_basis")
    cleaned["decision_basis"] = basis
    changed = bool(removed) or prior_basis != basis
    reasons = []
    if removed:
        reasons.append(REASON_HIDDEN_REASONING_REMOVED)
    reasons.append(_EVIDENCE_REASON[evidence_source])
    if concised:
        reasons.append(REASON_BASIS_CONCISED)

    manifest.update(
        {
            "action": "migrated" if changed else "retained",
            "reason_codes": reasons,
            "evidence_source": evidence_source,
        }
    )
    if contains_hidden_reasoning_key(cleaned):
        raise AssertionError("coding curation emitted a hidden-reasoning key")
    return cleaned, manifest


def _record_id(record: Any) -> str | None:
    if not isinstance(record, dict):
        return None
    value = record.get("id")
    if isinstance(value, str) and value.strip():
        return value.strip()
    meta = record.get("meta")
    if isinstance(meta, dict):
        value = meta.get("id")
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def _base_manifest(
    *,
    source_path: str,
    source_line: int,
    source_hash: str,
) -> dict[str, Any]:
    return {
        "source_path": source_path,
        "source_line": source_line,
        "source_hash": source_hash,
        "transform": TRANSFORM_NAME,
        "transform_version": TRANSFORM_VERSION,
        "action": "excluded",
        "reason_codes": [],
        "output_id": None,
        "output_hash": None,
        "hidden_reasoning_fields_removed": 0,
        "steps_path": None,
        "step_counts": {
            "source": 0,
            "retained": 0,
            "migrated": 0,
            "excluded": 0,
        },
        "step_actions": [],
    }


def _steps_path(record: dict[str, Any]) -> str | None:
    """Return where this record keeps its coding steps, or None.

    A plain episode holds them at ``steps``. A Thalamic wrap record embeds the
    coding episode under ``executed_action``, so its steps live one level down.
    """
    if isinstance(record.get("steps"), list):
        return "steps"
    parent = record.get(WRAP_STEPS_PARENT)
    if isinstance(parent, dict) and isinstance(parent.get("steps"), list):
        return f"{WRAP_STEPS_PARENT}.steps"
    return None


def _steps_holder(record: dict[str, Any], steps_path: str) -> dict[str, Any]:
    """Return the mapping that owns the step array named by ``steps_path``."""
    if steps_path == "steps":
        return record
    return record[WRAP_STEPS_PARENT]


def _record_steps(record: Any) -> list[Any] | None:
    """Return the curated step array for a plain or wrap record."""
    if not isinstance(record, dict):
        return None
    steps_path = _steps_path(record)
    if steps_path is None:
        return None
    steps = _steps_holder(record, steps_path).get("steps")
    return steps if isinstance(steps, list) else None


def curate_episode(
    record: Any,
    *,
    source_path: str = "<memory>",
    source_line: int = 1,
    source_hash: str | None = None,
) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    """Curate one episode and emit a deterministic record-level manifest."""
    digest = source_hash or hash_value(record)
    manifest = _base_manifest(
        source_path=source_path,
        source_line=source_line,
        source_hash=digest,
    )
    if not isinstance(record, dict):
        manifest["reason_codes"] = [REASON_RECORD_NOT_OBJECT]
        return None, manifest

    steps_path = _steps_path(record)
    if steps_path is None:
        manifest["reason_codes"] = [REASON_STEPS_NOT_ARRAY]
        return None, manifest
    manifest["steps_path"] = steps_path
    steps = _steps_holder(record, steps_path)["steps"]

    cleaned_record, record_reasoning_removed = _strip_hidden_reasoning_keys(record)
    manifest["hidden_reasoning_fields_removed"] = record_reasoning_removed
    retained_steps = []
    step_actions = []
    for source_index, step in enumerate(steps, 1):
        curated_step, step_manifest = curate_step(step, source_index)
        if curated_step is not None:
            retained_steps.append(curated_step)
            step_manifest["output_step_index"] = len(retained_steps)
        else:
            step_manifest["output_step_index"] = None
        step_actions.append(step_manifest)

    migrated = sum(item["action"] == "migrated" for item in step_actions)
    excluded = sum(item["action"] == "excluded" for item in step_actions)
    manifest["step_counts"] = {
        "source": len(steps),
        "retained": len(retained_steps),
        "migrated": migrated,
        "excluded": excluded,
    }
    manifest["step_actions"] = step_actions

    if not retained_steps:
        manifest["reason_codes"] = [REASON_NO_RETAINABLE_STEPS]
        return None, manifest

    _steps_holder(cleaned_record, steps_path)["steps"] = retained_steps
    reasons = []
    if record_reasoning_removed:
        reasons.append(REASON_HIDDEN_REASONING_REMOVED)
    if steps_path != "steps":
        reasons.append(REASON_WRAP_RECORD)
    if migrated:
        reasons.append(REASON_STEPS_MIGRATED)
    if excluded:
        reasons.append(REASON_STEPS_EXCLUDED)

    changed = cleaned_record != record
    manifest.update(
        {
            "action": "modified" if changed else "unchanged",
            "reason_codes": reasons,
            "output_id": _record_id(cleaned_record),
            "output_hash": hash_value(cleaned_record),
        }
    )
    if contains_hidden_reasoning_key(cleaned_record):
        raise AssertionError("coding curation emitted a hidden-reasoning key")
    return cleaned_record, manifest


def _excluded_line_manifest(
    *, source_path: str, source_line: int, source_hash: str, reason: str
) -> dict[str, Any]:
    manifest = _base_manifest(
        source_path=source_path,
        source_line=source_line,
        source_hash=source_hash,
    )
    manifest["reason_codes"] = [reason]
    return manifest


def curate_jsonl(
    source_path: str | Path,
    *,
    logical_source_path: str | None = None,
) -> dict[str, Any]:
    """Read a JSONL source without mutation and curate every nonblank line."""
    source = Path(source_path)
    source_label = logical_source_path or str(source)
    records = []
    manifests = []

    with source.open("rb") as handle:
        for line_number, terminated_line in enumerate(handle, 1):
            has_lf_terminator = terminated_line.endswith(b"\n")
            physical_line = (
                terminated_line[:-1]
                if has_lf_terminator
                else terminated_line
            )
            # JSONL is framed by literal LF. Remove only the one CR that is
            # paired with that LF; any additional CR is source payload and is
            # therefore part of the authenticated line digest.
            raw_line = (
                physical_line[:-1]
                if has_lf_terminator and physical_line.endswith(b"\r")
                else physical_line
            )
            if not raw_line.strip():
                continue
            source_hash = hashlib.sha256(raw_line).hexdigest()
            try:
                text = raw_line.decode("utf-8")
            except UnicodeDecodeError:
                manifests.append(
                    _excluded_line_manifest(
                        source_path=source_label,
                        source_line=line_number,
                        source_hash=source_hash,
                        reason=REASON_INVALID_UTF8,
                    )
                )
                continue
            try:
                record = json.loads(text)
            except json.JSONDecodeError:
                manifests.append(
                    _excluded_line_manifest(
                        source_path=source_label,
                        source_line=line_number,
                        source_hash=source_hash,
                        reason=REASON_INVALID_JSON,
                    )
                )
                continue

            curated, manifest = curate_episode(
                record,
                source_path=source_label,
                source_line=line_number,
                source_hash=source_hash,
            )
            manifests.append(manifest)
            if curated is not None:
                records.append(curated)

    step_counts = Counter()
    evidence_sources = Counter()
    steps_paths = Counter()
    for manifest in manifests:
        step_counts.update(manifest["step_counts"])
        if manifest["steps_path"]:
            steps_paths[manifest["steps_path"]] += 1
        for action in manifest["step_actions"]:
            evidence = action.get("evidence_source")
            if evidence:
                evidence_sources[evidence] += 1

    summary = {
        "source_path": source_label,
        "input_records": len(manifests),
        "output_records": len(records),
        "excluded_records": sum(item["action"] == "excluded" for item in manifests),
        "source_steps": step_counts["source"],
        "retained_steps": step_counts["retained"],
        "migrated_steps": step_counts["migrated"],
        "excluded_steps": step_counts["excluded"],
        "hidden_reasoning_fields_removed": sum(
            manifest["hidden_reasoning_fields_removed"] for manifest in manifests
        ),
        "wrap_records": steps_paths[f"{WRAP_STEPS_PARENT}.steps"],
        "decision_basis_sources": dict(sorted(evidence_sources.items())),
    }
    return {"records": records, "manifest": manifests, "summary": summary}


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


def _step_action_violations(entry: dict[str, Any], where: str) -> list[str]:
    """Return acceptance violations for one step-level manifest entry."""
    violations = []
    index = entry.get("source_step_index")
    step_where = f"{where} step {index}"
    action = entry.get("action")
    reasons = _reason_code_set(entry.get("reason_codes"), step_where, violations)
    if not reasons:
        violations.append(f"{step_where}: no reason codes recorded")
    evidence = entry.get("evidence_source")

    if not _is_positive_int(index):
        violations.append(f"{step_where}: source step index must be a positive integer")
    thought_fields_removed = _hidden_removed(entry)
    if not _is_nonnegative_int(thought_fields_removed):
        violations.append(
            f"{step_where}: thought_fields_removed must be a non-negative integer"
        )
    else:
        reports_removal = bool(REMOVAL_REASON_CODES.intersection(reasons))
        if bool(thought_fields_removed) != reports_removal:
            violations.append(
                f"{step_where}: thought removal count and reason code disagree"
            )

    if action == "excluded":
        step_exclusions = STEP_EXCLUSION_REASONS.intersection(reasons)
        if len(step_exclusions) != 1:
            violations.append(
                f"{step_where}: excluded without an exclusion reason code; "
                "expected exactly one step exclusion reason code"
            )
        impossible_reasons = reasons - (
            STEP_EXCLUSION_REASONS | REMOVAL_REASON_CODES
        )
        if impossible_reasons:
            violations.append(
                f"{step_where}: excluded with impossible reason codes "
                f"{sorted(impossible_reasons)}"
            )
        if evidence is not None:
            violations.append(f"{step_where}: excluded step records an evidence source")
        if entry.get("output_step_index") is not None:
            violations.append(f"{step_where}: excluded step keeps an output index")
    elif action == "migrated" or action == "retained":
        if not _is_positive_int(entry.get("output_step_index")):
            violations.append(
                f"{step_where}: retained output step index must be a positive integer"
            )
        if not isinstance(evidence, str) or evidence not in _EVIDENCE_REASON:
            violations.append(
                f"{step_where}: retained without a visible evidence source"
            )
        elif _EVIDENCE_REASON[evidence] not in reasons:
            violations.append(
                f"{step_where}: reason codes do not record the {evidence} evidence source"
            )
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
        if action == "retained" and thought_fields_removed != 0:
            violations.append(f"{step_where}: retained step reports thought removals")
    else:
        violations.append(f"{step_where}: unknown step action {action!r}")
    return violations


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
    violations = []
    if not isinstance(manifests, list):
        return ["manifest collection is not a list"]
    total_source = 0
    seen_source_locations = set()
    for manifest in manifests:
        if not isinstance(manifest, dict):
            violations.append(f"manifest entry {manifest!r} is not an object")
            continue
        source_path = manifest.get("source_path")
        source_line = manifest.get("source_line")
        where = f"{source_path}:{source_line}"
        if not isinstance(source_path, str) or not source_path:
            violations.append(f"{where}: manifest records no source path")
        if not _is_positive_int(source_line):
            violations.append(f"{where}: source line must be a positive integer")
        if isinstance(source_path, str) and source_path and _is_positive_int(source_line):
            source_location = (source_path, source_line)
            if source_location in seen_source_locations:
                violations.append(f"{where}: duplicate manifest source location")
            else:
                seen_source_locations.add(source_location)
        if manifest.get("transform") != TRANSFORM_NAME:
            violations.append(f"{where}: manifest is not a {TRANSFORM_NAME} manifest")
        if str(manifest.get("transform_version")) not in ACCEPTED_TRANSFORM_VERSIONS:
            violations.append(
                f"{where}: manifest transform version is not {TRANSFORM_VERSION}"
            )
        if not _is_sha256(manifest.get("source_hash")):
            violations.append(f"{where}: manifest records no valid source hash")

        action = manifest.get("action")
        reasons = _reason_code_set(manifest.get("reason_codes"), where, violations)
        if action == "excluded":
            if not EXCLUSION_REASONS.intersection(reasons):
                violations.append(
                    f"{where}: record excluded without an exclusion reason code"
                )
            if manifest.get("output_hash") is not None:
                violations.append(
                    f"{where}: excluded record still records an output hash"
                )
            if manifest.get("output_id") is not None:
                violations.append(f"{where}: excluded record still records an output ID")
        elif action == "modified" or action == "unchanged":
            if not _is_sha256(manifest.get("output_hash")):
                violations.append(
                    f"{where}: retained record records no valid output hash"
                )
        else:
            violations.append(f"{where}: unknown record action {action!r}")

        thought_fields_removed = _hidden_removed(manifest)
        if not _is_nonnegative_int(thought_fields_removed):
            violations.append(
                f"{where}: thought_fields_removed must be a non-negative integer"
            )
        mismatch = _dual_removal_mismatch(manifest, where)
        if mismatch:
            violations.append(mismatch)

        counts = manifest.get("step_counts")
        actions = manifest.get("step_actions")
        if not isinstance(counts, dict) or not isinstance(actions, list):
            violations.append(f"{where}: manifest records no step accounting")
            continue
        if PRE_STEP_EXCLUSION_REASONS.intersection(reasons):
            if actions or any(
                counts.get(key) not in (0, None)
                for key in ("source", "retained", "migrated", "excluded")
            ):
                violations.append(
                    f"{where}: pre-step exclusion must have zero source steps and no step actions"
                )
        recorded_counts = {}
        for key in ("source", "retained", "migrated", "excluded"):
            value = counts.get(key)
            if not _is_nonnegative_int(value):
                violations.append(
                    f"{where}: step_counts.{key} must be a non-negative integer"
                )
                recorded_counts[key] = None
            else:
                recorded_counts[key] = value

        source_count = recorded_counts["source"]
        if source_count is not None:
            total_source += source_count
        if source_count is not None and source_count != len(actions):
            violations.append(
                f"{where}: {source_count} source steps but {len(actions)} step actions"
            )

        valid_actions = []
        for entry in actions:
            if not isinstance(entry, dict):
                violations.append(f"{where}: step action {entry!r} is not an object")
                continue
            valid_actions.append(entry)
            violations.extend(_step_action_violations(entry, where))

        retained = sum(
            entry.get("action") == "migrated" or entry.get("action") == "retained"
            for entry in valid_actions
        )
        migrated = sum(entry.get("action") == "migrated" for entry in valid_actions)
        excluded = sum(entry.get("action") == "excluded" for entry in valid_actions)
        if retained + excluded != len(actions):
            violations.append(f"{where}: step actions are neither retained nor excluded")
        if action == "excluded" and retained:
            retained_label = "step" if retained == 1 else "steps"
            violations.append(
                f"{where}: excluded record retains {retained} {retained_label}"
            )
        if action in {"modified", "unchanged"} and retained == 0:
            violations.append(
                f"{where}: retained record must keep at least one step"
            )
        action_thought_counts = [
            _hidden_removed(entry) for entry in valid_actions
        ]
        if (
            _is_nonnegative_int(thought_fields_removed)
            and len(valid_actions) == len(actions)
            and all(_is_nonnegative_int(value) for value in action_thought_counts)
            and thought_fields_removed < sum(action_thought_counts)
        ):
            violations.append(
                f"{where}: thought_fields_removed does not account for the step actions"
            )
        expected_counts = {
            "source": len(actions),
            "retained": retained,
            "migrated": migrated,
            "excluded": excluded,
        }
        if any(
            recorded_counts[key] is not None
            and recorded_counts[key] != expected_counts[key]
            for key in expected_counts
        ):
            violations.append(
                f"{where}: step counts {counts} disagree with the recorded step actions"
            )

        if action == "unchanged":
            if thought_fields_removed != 0:
                violations.append(
                    f"{where}: unchanged record reports thought removals"
                )
            if any(entry.get("action") != "retained" for entry in valid_actions):
                violations.append(
                    f"{where}: unchanged record reports transformed step actions"
                )
            if reasons - RECORD_STRUCTURAL_REASONS:
                violations.append(
                    f"{where}: unchanged record reports transformation reason codes"
                )
        elif action == "modified" and _is_nonnegative_int(thought_fields_removed):
            impossible_reasons = reasons - RECORD_TRANSFORMATION_REASONS - RECORD_STRUCTURAL_REASONS
            if impossible_reasons:
                violations.append(
                    f"{where}: modified record reports impossible reason codes "
                    f"{sorted(impossible_reasons)}"
                )
            reports_removal = bool(REMOVAL_REASON_CODES.intersection(reasons))
            if bool(thought_fields_removed) != reports_removal:
                violations.append(
                    f"{where}: thought removal count and reason code disagree"
                )
            reason_expectations = (
                (migrated, REASON_STEPS_MIGRATED),
                (excluded, REASON_STEPS_EXCLUDED),
            )
            for count, reason in reason_expectations:
                if bool(count) != (reason in reasons):
                    violations.append(
                        f"{where}: step transformation counts and reason codes disagree"
                    )
                    break
            if thought_fields_removed == 0 and migrated == 0 and excluded == 0:
                violations.append(
                    f"{where}: modified record reports no transformation evidence"
                )

        source_indexes = [entry.get("source_step_index") for entry in valid_actions]
        expected_source_indexes = list(range(1, len(actions) + 1))
        if source_indexes != expected_source_indexes:
            violations.append(
                f"{where}: source step indexes {source_indexes} are not sequential "
                f"{expected_source_indexes}"
            )
        output_indexes = [
            entry.get("output_step_index")
            for entry in valid_actions
            if entry.get("action") == "migrated" or entry.get("action") == "retained"
        ]
        expected_output_indexes = list(range(1, retained + 1))
        if output_indexes != expected_output_indexes:
            violations.append(
                f"{where}: retained output step indexes {output_indexes} are not "
                f"sequential {expected_output_indexes}"
            )

    if expected_source_steps is not None and total_source != expected_source_steps:
        violations.append(
            f"expected {expected_source_steps} source steps, manifest accounts for "
            f"{total_source}"
        )
    return violations


def _curated_record_violations(record: Any, where: str) -> list[str]:
    """Return acceptance violations for one curated output record."""
    violations = []
    if contains_thought_key(record):
        violations.append(f"{where}: curated record still exposes a thought key")
    steps = _record_steps(record)
    if not isinstance(steps, list) or not steps:
        violations.append(f"{where}: curated record has no retained steps")
        return violations
    for index, step in enumerate(steps, 1):
        step_where = f"{where} step {index}"
        if not isinstance(step, dict):
            violations.append(f"{step_where}: curated step is not an object")
            continue
        basis = step.get("decision_basis")
        if not isinstance(basis, str) or not basis.strip():
            violations.append(f"{step_where}: missing a non-empty decision_basis")
            continue
        if not basis.startswith(VISIBLE_BASIS_LABELS):
            violations.append(
                f"{step_where}: decision_basis does not open with a visible evidence label"
            )
        expected_basis, _, _ = _derive_decision_basis(step)
        if expected_basis is None:
            violations.append(
                f"{step_where}: decision_basis has no visible evidence to ground it"
            )
        elif basis != expected_basis:
            violations.append(
                f"{step_where}: decision_basis is not grounded in its visible evidence"
            )
        if len(basis) > MAX_DECISION_BASIS_CHARS:
            violations.append(
                f"{step_where}: decision_basis exceeds {MAX_DECISION_BASIS_CHARS} chars"
            )
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

    record_value = result.get("records")
    if not isinstance(record_value, list):
        violations.append("curated records are not a list")
        records = []
    else:
        records = record_value
    for index, record in enumerate(records, 1):
        violations.extend(_curated_record_violations(record, f"record {index}"))

    emitting_manifests = [
        manifest
        for manifest in manifests
        if isinstance(manifest, dict)
        and (
            manifest.get("action") == "modified"
            or manifest.get("action") == "unchanged"
        )
    ]
    if len(records) != len(emitting_manifests):
        violations.append(
            f"curated output has {len(records)} records but the manifest emits "
            f"{len(emitting_manifests)}"
        )

    for index, (record, manifest) in enumerate(
        zip(records, emitting_manifests), 1
    ):
        try:
            actual_hash = hash_value(record)
        except (TypeError, ValueError, RecursionError):
            violations.append(f"record {index}: curated record is not JSON-serializable")
            continue
        if manifest.get("output_hash") != actual_hash:
            violations.append(
                f"record {index}: output hash does not match its manifest entry"
            )
        if manifest.get("output_id") != _record_id(record):
            violations.append(
                f"record {index}: output ID does not match its manifest entry"
            )

        steps = _record_steps(record)
        actions = manifest.get("step_actions")
        if not isinstance(steps, list) or not isinstance(actions, list):
            continue
        for entry in actions:
            if not isinstance(entry, dict) or not (
                entry.get("action") == "migrated" or entry.get("action") == "retained"
            ):
                continue
            output_index = entry.get("output_step_index")
            if not _is_positive_int(output_index) or output_index > len(steps):
                continue
            step = steps[output_index - 1]
            if not isinstance(step, dict):
                continue
            _, evidence_source, concised = _derive_decision_basis(step)
            if entry.get("evidence_source") != evidence_source:
                violations.append(
                    f"record {index} step {output_index}: visible evidence source "
                    "does not match its manifest action"
                )
            reasons = entry.get("reason_codes")
            reports_concised = (
                isinstance(reasons, list) and REASON_BASIS_CONCISED in reasons
            )
            if bool(concised) != reports_concised:
                violations.append(
                    f"record {index} step {output_index}: concision reason does not "
                    "match visible evidence"
                )
            if entry.get("source_step_number") != step.get("n"):
                violations.append(
                    f"record {index} step {output_index}: source step number does not "
                    "match the retained output step"
                )

    manifest_totals = Counter()
    manifest_thought_fields_removed = 0
    manifest_evidence_sources = Counter()
    for manifest in manifests:
        if not isinstance(manifest, dict):
            continue
        counts = manifest.get("step_counts")
        if isinstance(counts, dict):
            for key in ("source", "retained", "migrated", "excluded"):
                value = counts.get(key)
                if _is_nonnegative_int(value):
                    manifest_totals[key] += value
        removed = _hidden_removed(manifest)
        if _is_nonnegative_int(removed):
            manifest_thought_fields_removed += removed
        actions = manifest.get("step_actions")
        if isinstance(actions, list):
            for entry in actions:
                if not isinstance(entry, dict):
                    continue
                if entry.get("action") not in {"migrated", "retained"}:
                    continue
                evidence = entry.get("evidence_source")
                if isinstance(evidence, str) and evidence:
                    manifest_evidence_sources[evidence] += 1

    retained = sum(
        len(steps)
        for record in records
        if (steps := _record_steps(record)) is not None
    )
    if retained != manifest_totals["retained"]:
        violations.append(
            f"curated output has {retained} steps but the manifest retains "
            f"{manifest_totals['retained']}"
        )

    summary = result.get("summary")
    if not isinstance(summary, dict):
        violations.append("curation summary is not an object")
    else:
        expected_summary = {
            "input_records": len(manifests),
            "output_records": len(emitting_manifests),
            "excluded_records": sum(
                isinstance(manifest, dict) and manifest.get("action") == "excluded"
                for manifest in manifests
            ),
            "source_steps": manifest_totals["source"],
            "retained_steps": manifest_totals["retained"],
            "migrated_steps": manifest_totals["migrated"],
            "excluded_steps": manifest_totals["excluded"],
            "decision_basis_sources": dict(sorted(manifest_evidence_sources.items())),
        }
        if "hidden_reasoning_fields_removed" in summary:
            expected_summary["hidden_reasoning_fields_removed"] = (
                manifest_thought_fields_removed
            )
        if "thought_fields_removed" in summary:
            expected_summary["thought_fields_removed"] = (
                manifest_thought_fields_removed
            )
        if (
            "hidden_reasoning_fields_removed" not in summary
            and "thought_fields_removed" not in summary
        ):
            expected_summary["hidden_reasoning_fields_removed"] = (
                manifest_thought_fields_removed
            )
        mismatch = _dual_removal_mismatch(summary, "summary")
        if mismatch:
            violations.append(mismatch)
        for key, expected in expected_summary.items():
            if summary.get(key) != expected:
                violations.append(
                    f"summary {key} {summary.get(key)!r} does not match {expected}"
                )
    return violations



def _is_under_raw(path: Path) -> bool:
    parts = path.resolve(strict=False).parts
    return any(
        parts[index : index + 2] == ("outputs", "raw")
        for index in range(len(parts) - 1)
    )


def _created_file_identity(descriptor: int) -> tuple[int, int]:
    metadata = os.fstat(descriptor)
    return metadata.st_dev, metadata.st_ino


def _created_directory_identity(path: Path) -> tuple[int, int]:
    metadata = os.lstat(path)
    return metadata.st_dev, metadata.st_ino


def _unlink_created_file(path: Path, identity: tuple[int, int]) -> bool:
    """Remove ``path`` only while it still names the file this process created."""
    try:
        metadata = os.lstat(path)
    except FileNotFoundError:
        return False
    if (metadata.st_dev, metadata.st_ino) != identity:
        return False
    path.unlink()
    return True


def _rmdir_created_directory(path: Path, identity: tuple[int, int]) -> bool:
    """Remove an empty directory only while its pathname retains our inode."""
    try:
        metadata = os.lstat(path)
    except FileNotFoundError:
        return False
    if (metadata.st_dev, metadata.st_ino) != identity:
        return False
    try:
        path.rmdir()
    except OSError:
        return False
    return True


def _write_new_jsonl(
    path: Path,
    values: list[dict[str, Any]],
) -> tuple[int, int]:
    """Write one JSONL file without replacing any pre-existing path."""
    if _is_under_raw(path):
        raise ValueError(f"refusing to write inside immutable raw evidence: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    identity = _created_file_identity(descriptor)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            for value in values:
                handle.write(canonical_json(value))
                handle.write("\n")
    except BaseException:
        _unlink_created_file(path, identity)
        raise
    return identity


def _preflight_destinations(paths: list[Path]) -> None:
    resolved = [path.resolve(strict=False) for path in paths]
    if len(set(resolved)) != len(resolved):
        raise ValueError("output destinations must be distinct")
    for path in paths:
        if _is_under_raw(path):
            raise ValueError(f"refusing to write inside immutable raw evidence: {path}")
        if path.exists():
            raise FileExistsError(f"refusing to replace existing destination: {path}")


def _source_jsonl_paths(source_root: Path) -> tuple[Path, list[Path]]:
    declared = Path(os.path.abspath(source_root))
    if declared.is_symlink():
        raise ValueError(f"source run must not be a symlink: {declared}")
    try:
        resolved = declared.resolve(strict=True)
    except OSError as exc:
        raise ValueError(f"source run is not a directory: {declared}") from exc
    if not resolved.is_dir():
        raise ValueError(f"source run is not a directory: {declared}")
    paths = []
    for path in resolved.rglob("*"):
        if path.is_symlink():
            raise ValueError(f"source run contains a symlinked path: {path}")
        if path.is_file() and path.suffix == ".jsonl":
            paths.append(path)
    paths.sort(key=lambda jsonl_path: jsonl_path.relative_to(resolved).as_posix())
    if not paths:
        raise ValueError(f"source run holds no JSONL files: {resolved}")
    if resolved / RUN_MANIFEST_FILENAME in paths:
        raise ValueError(
            f"source JSONL conflicts with aggregate manifest name: {RUN_MANIFEST_FILENAME}"
        )
    return resolved, paths


def _new_run_destination(destination: Path, source_root: Path) -> Path:
    declared = Path(os.path.abspath(destination))
    if _is_under_raw(declared):
        raise ValueError(f"refusing to write inside immutable raw evidence: {declared}")
    if os.path.lexists(declared):
        raise FileExistsError(f"refusing to replace existing destination: {declared}")
    resolved = declared.resolve(strict=False)
    if resolved == source_root or source_root in resolved.parents:
        raise ValueError(f"output directory must be outside the source run: {declared}")
    return declared


def curate_run(source_dir: str | Path, output_dir: str | Path) -> dict[str, Any]:
    """Write one gate-ready coding lane for every JSONL in a source tree."""
    source_root, source_paths = _source_jsonl_paths(Path(source_dir))
    output_root = _new_run_destination(Path(output_dir), source_root)
    output_root.mkdir(parents=True, exist_ok=False)

    manifests: list[dict[str, Any]] = []
    summaries: list[dict[str, Any]] = []
    created_files: list[tuple[Path, tuple[int, int]]] = []
    created_directories = [
        (output_root, _created_directory_identity(output_root))
    ]
    try:
        relative_directories = {
            parent
            for source_path in source_paths
            for parent in source_path.relative_to(source_root).parents
            if parent != Path(".")
        }
        for relative in sorted(
            relative_directories,
            key=lambda relative_path: (len(relative_path.parts), relative_path.parts),
        ):
            directory = output_root / relative
            directory.mkdir()
            created_directories.append(
                (directory, _created_directory_identity(directory))
            )
        for source_path in source_paths:
            relative = source_path.relative_to(source_root)
            result = curate_jsonl(
                source_path,
                logical_source_path=relative.as_posix(),
            )
            output_path = output_root / relative
            identity = _write_new_jsonl(output_path, result["records"])
            created_files.append((output_path, identity))
            manifests.extend(result["manifest"])
            summaries.append(result["summary"])
        manifest_path = output_root / RUN_MANIFEST_FILENAME
        identity = _write_new_jsonl(manifest_path, manifests)
        created_files.append((manifest_path, identity))
    except BaseException:
        for path, identity in reversed(created_files):
            _unlink_created_file(path, identity)
        for path, identity in reversed(created_directories):
            _rmdir_created_directory(path, identity)
        raise

    evidence_sources = Counter()
    for summary in summaries:
        evidence_sources.update(summary["decision_basis_sources"])
    return {
        "source_path": str(source_root),
        "output_path": str(output_root),
        "manifest_path": str(output_root / RUN_MANIFEST_FILENAME),
        "input_files": len(source_paths),
        "input_records": sum(summary["input_records"] for summary in summaries),
        "output_records": sum(summary["output_records"] for summary in summaries),
        "excluded_records": sum(summary["excluded_records"] for summary in summaries),
        "source_steps": sum(summary["source_steps"] for summary in summaries),
        "retained_steps": sum(summary["retained_steps"] for summary in summaries),
        "migrated_steps": sum(summary["migrated_steps"] for summary in summaries),
        "excluded_steps": sum(summary["excluded_steps"] for summary in summaries),
        "hidden_reasoning_fields_removed": sum(
            summary["hidden_reasoning_fields_removed"] for summary in summaries
        ),
        "wrap_records": sum(summary["wrap_records"] for summary in summaries),
        "decision_basis_sources": dict(sorted(evidence_sources.items())),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="legacy episode JSONL to inspect")
    parser.add_argument("--output-jsonl", type=Path)
    parser.add_argument("--manifest-jsonl", type=Path)
    parser.add_argument(
        "--output-dir",
        type=Path,
        help="new lane root for directory-wide curation",
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="fail when any curated step or manifest entry breaks the lane contract",
    )
    parser.add_argument(
        "--expect-source-steps",
        type=int,
        help="require the manifest to account for exactly this many source steps",
    )
    args = parser.parse_args(argv)

    if args.expect_source_steps is not None and args.expect_source_steps < 0:
        parser.error("--expect-source-steps must not be negative")
    verifying = args.verify or args.expect_source_steps is not None
    if args.output_dir is not None:
        if args.output_jsonl is not None or args.manifest_jsonl is not None:
            parser.error("--output-dir cannot be combined with file output options")
        if verifying:
            parser.error("--output-dir cannot be combined with --verify")
        if not args.source.is_dir():
            parser.error("--output-dir requires a source directory")
        try:
            result = curate_run(args.source, args.output_dir)
        except (FileExistsError, OSError, ValueError) as exc:
            parser.error(str(exc))
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
        return 0
    if args.source.is_dir():
        parser.error("a source directory requires --output-dir")

    if args.output_jsonl is not None and args.output_jsonl.resolve(strict=False) == args.source.resolve():
        parser.error("output must not replace the source")
    destinations = [
        path
        for path in (args.output_jsonl, args.manifest_jsonl)
        if path is not None
    ]
    try:
        _preflight_destinations(destinations)
    except (FileExistsError, ValueError) as exc:
        parser.error(str(exc))

    result = curate_jsonl(args.source)
    summary = result["summary"]
    if verifying:
        violations = verify_curation(
            result, expected_source_steps=args.expect_source_steps
        )
        summary = dict(summary)
        summary["verification"] = {
            "expected_source_steps": args.expect_source_steps,
            "violations": violations,
        }
        if violations:
            # A failed gate must not leave a curated artifact behind for the
            # integration lane to pick up as if it had passed.
            print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
            for violation in violations:
                print(f"VIOLATION: {violation}", file=sys.stderr)
            return 2

    if args.output_jsonl is not None:
        _write_new_jsonl(args.output_jsonl, result["records"])
    if args.manifest_jsonl is not None:
        _write_new_jsonl(args.manifest_jsonl, result["manifest"])
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
