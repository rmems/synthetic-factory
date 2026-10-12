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

import copy
import hashlib
import json
import os
import re
import sys
import unicodedata
from collections import Counter
from collections.abc import Iterable, Iterator
from pathlib import Path
from typing import Any, cast

if __package__:
    from .coding_constants import (
        HIDDEN_REASONING_KEYS,
        HIDDEN_REASONING_PREFIX,
        MAX_DECISION_BASIS_CHARS,
        REASON_BASIS_CONCISED,
        REASON_BASIS_FROM_OBSERVATION,
        REASON_BASIS_FROM_PLAN,
        REASON_BASIS_FROM_REFLECTION,
        REASON_BASIS_FROM_TOOL_CALL,
        REASON_HIDDEN_REASONING_REMOVED,
        REASON_INVALID_JSON,
        REASON_INVALID_UTF8,
        REASON_NO_RETAINABLE_STEPS,
        REASON_NO_VISIBLE_EVIDENCE,
        REASON_RECORD_NOT_OBJECT,
        REASON_STEP_NOT_OBJECT,
        REASON_STEPS_EXCLUDED,
        REASON_STEPS_MIGRATED,
        REASON_STEPS_NOT_ARRAY,
        REASON_THOUGHT_REMOVED,
        REASON_WRAP_RECORD,
        RUN_MANIFEST_FILENAME,
        TRANSFORM_NAME,
        TRANSFORM_VERSION,
        WRAP_STEPS_PARENT,
        _EVIDENCE_REASON,
    )
    from .record_kind import classify_kind
else:
    _PIPELINES = Path(__file__).resolve().parent
    if str(_PIPELINES) not in sys.path:
        sys.path.insert(0, str(_PIPELINES))
    from coding_constants import (
        HIDDEN_REASONING_KEYS,
        HIDDEN_REASONING_PREFIX,
        MAX_DECISION_BASIS_CHARS,
        REASON_BASIS_CONCISED,
        REASON_BASIS_FROM_OBSERVATION,
        REASON_BASIS_FROM_PLAN,
        REASON_BASIS_FROM_REFLECTION,
        REASON_BASIS_FROM_TOOL_CALL,
        REASON_HIDDEN_REASONING_REMOVED,
        REASON_INVALID_JSON,
        REASON_INVALID_UTF8,
        REASON_NO_RETAINABLE_STEPS,
        REASON_NO_VISIBLE_EVIDENCE,
        REASON_RECORD_NOT_OBJECT,
        REASON_STEP_NOT_OBJECT,
        REASON_STEPS_EXCLUDED,
        REASON_STEPS_MIGRATED,
        REASON_STEPS_NOT_ARRAY,
        REASON_THOUGHT_REMOVED,
        REASON_WRAP_RECORD,
        RUN_MANIFEST_FILENAME,
        TRANSFORM_NAME,
        TRANSFORM_VERSION,
        WRAP_STEPS_PARENT,
        _EVIDENCE_REASON,
    )
    from record_kind import classify_kind


def canonical_json(value: Any) -> str:
    """Return the stable JSON representation used for output hashes."""
    return json.dumps(
        value,
        allow_nan=False,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )


def hash_value(value: Any) -> str:
    """Hash a parsed value deterministically."""
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def _reject_json_constant(value: str) -> None:
    raise ValueError(f"non-standard JSON numeric constant {value}")


_KEY_CONFUSABLES = str.maketrans({"о": "o", "ο": "o", "а": "a", "е": "e", "і": "i", "ѕ": "s"})


def normalized_key_name(value: Any) -> str:
    """Normalize JSON keys across case, separators, camel-case, and lookalikes."""
    text = unicodedata.normalize("NFKC", str(value))
    text = "".join(char for char in text if unicodedata.category(char) != "Cf")
    separated = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", "_", text)
    separated = re.sub(r"(?<=[A-Z])(?=[A-Z][a-z])", "_", separated)
    return re.sub(r"[^a-z0-9]+", "_", separated.casefold().translate(_KEY_CONFUSABLES)).strip("_")


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


def _is_sentence_end(text: str, index: int) -> bool:
    """Whether ``text[index]`` closes a sentence: terminal punctuation, then space or end."""
    if text[index] not in ".!?":
        return False
    return index + 1 == len(text) or text[index + 1].isspace()


def _sentence_ends_within(text: str, limit: int) -> list[int]:
    """Every sentence-end offset up to ``limit``; stops at the first one beyond it."""
    sentence_ends = []
    for index in range(len(text)):
        if not _is_sentence_end(text, index):
            continue
        if index + 1 > limit:
            break
        sentence_ends.append(index + 1)
    return sentence_ends


def _word_boundary_excerpt(text: str, limit: int) -> str:
    """Cut at the last word boundary before ``limit`` (or hard-cut) and mark the elision."""
    cut = text.rfind(" ", 0, limit)
    if cut < max(24, limit // 2):
        cut = limit - 1
    return text[:cut].rstrip(" ,;:-") + "…"


def _concise(text: str, limit: int = MAX_DECISION_BASIS_CHARS) -> tuple[str, bool]:
    """Normalize text and retain a bounded visible-evidence excerpt."""
    normalized = " ".join(text.split())
    if len(normalized) <= limit:
        return normalized, False

    sentence_ends = _sentence_ends_within(normalized, limit)
    if sentence_ends and sentence_ends[-1] >= min(48, limit // 2):
        return normalized[: sentence_ends[-1]], True

    return _word_boundary_excerpt(normalized, limit), True


def _visible_value(value: Any) -> str | None:
    """Render a visible evidence field without consulting hidden text."""
    normalized = _normalize_text(value)
    if normalized is not None:
        return normalized
    if isinstance(value, (dict, list)) and value:
        return canonical_json(value)
    return None


def _structured_tool_call_evidence(tool_call: dict[str, Any]) -> str:
    """Render a non-empty tool-call mapping from its visible name and arguments."""
    tool_name = _normalize_text(tool_call.get("name")) or "unnamed tool"
    args = tool_call.get("args")
    if isinstance(args, (dict, list)) and args:
        return f"{tool_name} with visible arguments {canonical_json(args)}"
    return tool_name


def _tool_call_evidence(tool_call: Any) -> str | None:
    """Visible tool-call evidence: a non-empty mapping, else non-blank text, else None."""
    if isinstance(tool_call, dict) and tool_call:
        return _structured_tool_call_evidence(tool_call)
    return _normalize_text(tool_call)


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

    tool_evidence = _tool_call_evidence(step.get("tool_call"))
    if tool_evidence is not None:
        basis, concised = _concise(f"Tool call: {tool_evidence}")
        return basis, "tool_call", concised

    return None, None, False


def _new_step_manifest(step: Any, source_step_index: int) -> dict[str, Any]:
    """The step-level manifest entry before curation decides the step's action."""
    return {
        "source_step_index": source_step_index,
        "source_step_number": step.get("n") if isinstance(step, dict) else None,
        "action": "excluded",
        "reason_codes": [],
        "evidence_source": None,
        "hidden_reasoning_fields_removed": 0,
    }


def _removal_reasons(removed: int) -> list[str]:
    """The leading reason code that reports a hidden-reasoning removal, if any."""
    return [REASON_HIDDEN_REASONING_REMOVED] if removed else []


def curate_step(step: Any, source_step_index: int) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    """Curate one step and return its output plus a step-level manifest entry."""
    manifest = _new_step_manifest(step, source_step_index)
    if not isinstance(step, dict):
        manifest["reason_codes"] = [REASON_STEP_NOT_OBJECT]
        return None, manifest

    cleaned, removed = _strip_hidden_reasoning_keys(step)
    manifest["hidden_reasoning_fields_removed"] = removed
    basis, evidence_source, concised = _derive_decision_basis(cleaned)
    if basis is None:
        manifest["reason_codes"] = _removal_reasons(removed) + [REASON_NO_VISIBLE_EVIDENCE]
        return None, manifest

    prior_basis = cleaned.get("decision_basis")
    cleaned["decision_basis"] = basis
    changed = bool(removed) or prior_basis != basis
    reasons = _removal_reasons(removed)
    reasons.append(_EVIDENCE_REASON[cast(str, evidence_source)])
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


def steps_path(record: dict[str, Any]) -> str | None:
    """Return where this record keeps its coding steps, or None.

    A plain episode holds them at ``steps``. A Thalamic wrap record embeds the
    coding episode under ``executed_action``, so its steps live one level down.
    When a record classifies as a Thalamic wrap and carries both — its wrapped
    episode plus an incidental top-level ``steps`` array — the wrapped episode
    wins: the strict audit grounds a Thalamic record's ``executed_action.steps``
    and never the root array, so curating the root array instead would leave
    the actual wrap ungrounded and block an otherwise repairable corpus.
    """
    parent = record.get(WRAP_STEPS_PARENT)
    wrapped = isinstance(parent, dict) and isinstance(parent.get("steps"), list)
    if wrapped and classify_kind(record) == "thalamic":
        return f"{WRAP_STEPS_PARENT}.steps"
    if isinstance(record.get("steps"), list):
        return "steps"
    if wrapped:
        return f"{WRAP_STEPS_PARENT}.steps"
    return None


def _steps_holder(record: dict[str, Any], record_steps_path: str) -> dict[str, Any]:
    """Return the mapping that owns the step array named by ``record_steps_path``."""
    if record_steps_path == "steps":
        return record
    return record[WRAP_STEPS_PARENT]


def _record_steps(record: Any) -> list[Any] | None:
    """Return the curated step array for a plain or wrap record."""
    if not isinstance(record, dict):
        return None
    record_steps_path = steps_path(record)
    if record_steps_path is None:
        return None
    steps = _steps_holder(record, record_steps_path).get("steps")
    return steps if isinstance(steps, list) else None


def _curate_steps(steps: list[Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Curate every source step; return the retained steps and one action per source step."""
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
    return retained_steps, step_actions


def _step_counts(
    steps: list[Any],
    retained_steps: list[dict[str, Any]],
    step_actions: list[dict[str, Any]],
) -> dict[str, int]:
    """The record-level step accounting: source, retained, migrated, and excluded."""
    migrated = sum(item["action"] == "migrated" for item in step_actions)
    excluded = sum(item["action"] == "excluded" for item in step_actions)
    return {
        "source": len(steps),
        "retained": len(retained_steps),
        "migrated": migrated,
        "excluded": excluded,
    }


def _episode_reasons(
    record_reasoning_removed: int,
    record_steps_path: str,
    step_counts: dict[str, int],
) -> list[str]:
    """Reason codes for an emitted episode, in manifest order."""
    reasons = _removal_reasons(record_reasoning_removed)
    if record_steps_path != "steps":
        reasons.append(REASON_WRAP_RECORD)
    if step_counts["migrated"]:
        reasons.append(REASON_STEPS_MIGRATED)
    if step_counts["excluded"]:
        reasons.append(REASON_STEPS_EXCLUDED)
    return reasons


def _emit_episode(
    manifest: dict[str, Any],
    record: dict[str, Any],
    cleaned_record: dict[str, Any],
    reasons: list[str],
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Record the emitted episode's action, reasons, and output identity."""
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

    record_steps_path = steps_path(record)
    if record_steps_path is None:
        manifest["reason_codes"] = [REASON_STEPS_NOT_ARRAY]
        return None, manifest
    manifest["steps_path"] = record_steps_path
    steps = _steps_holder(record, record_steps_path)["steps"]

    cleaned_record, record_reasoning_removed = _strip_hidden_reasoning_keys(record)
    manifest["hidden_reasoning_fields_removed"] = record_reasoning_removed
    retained_steps, step_actions = _curate_steps(steps)
    manifest["step_counts"] = _step_counts(steps, retained_steps, step_actions)
    manifest["step_actions"] = step_actions

    if not retained_steps:
        manifest["reason_codes"] = [REASON_NO_RETAINABLE_STEPS]
        return None, manifest

    _steps_holder(cleaned_record, record_steps_path)["steps"] = retained_steps
    reasons = _episode_reasons(
        record_reasoning_removed, record_steps_path, manifest["step_counts"]
    )
    return _emit_episode(manifest, record, cleaned_record, reasons)


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


def _record_line_bytes(terminated_line: bytes) -> bytes:
    """Strip one physical line's LF terminator and the single CR paired with it."""
    has_lf_terminator = terminated_line.endswith(b"\n")
    physical_line = (
        terminated_line[:-1]
        if has_lf_terminator
        else terminated_line
    )
    # JSONL is framed by literal LF. Remove only the one CR that is
    # paired with that LF; any additional CR is source payload and is
    # therefore part of the authenticated line digest.
    return (
        physical_line[:-1]
        if has_lf_terminator and physical_line.endswith(b"\r")
        else physical_line
    )


def _nonblank_record_lines(handle: Iterable[bytes]) -> Iterator[tuple[int, bytes]]:
    """Yield each nonblank line's 1-based physical line number and record bytes."""
    for line_number, terminated_line in enumerate(handle, 1):
        raw_line = _record_line_bytes(terminated_line)
        if raw_line.strip():
            yield line_number, raw_line


def _parse_record_line(raw_line: bytes) -> tuple[Any, str | None]:
    """Decode one line as strict UTF-8 JSON; return the record or an exclusion reason."""
    try:
        text = raw_line.decode("utf-8")
    except UnicodeDecodeError:
        return None, REASON_INVALID_UTF8
    try:
        record = json.loads(text, parse_constant=_reject_json_constant)
        hash_value(record)
    except (TypeError, ValueError, RecursionError):  # json.JSONDecodeError included
        return None, REASON_INVALID_JSON
    return record, None


def _curate_jsonl_line(
    raw_line: bytes, source_label: str, line_number: int
) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    """Curate one nonblank source line, excluding undecodable or invalid JSON."""
    source_hash = hashlib.sha256(raw_line).hexdigest()
    record, reason = _parse_record_line(raw_line)
    if reason is not None:
        return None, _excluded_line_manifest(
            source_path=source_label,
            source_line=line_number,
            source_hash=source_hash,
            reason=reason,
        )
    return curate_episode(
        record,
        source_path=source_label,
        source_line=line_number,
        source_hash=source_hash,
    )


def _jsonl_summary(
    source_label: str,
    records: list[dict[str, Any]],
    manifests: list[dict[str, Any]],
) -> dict[str, Any]:
    """Aggregate one source file's record and step dispositions."""
    step_counts: Counter[str] = Counter()
    evidence_sources: Counter[str] = Counter()
    steps_paths: Counter[str] = Counter()
    for manifest in manifests:
        step_counts.update(manifest["step_counts"])
        if manifest["steps_path"]:
            steps_paths[manifest["steps_path"]] += 1
        for action in manifest["step_actions"]:
            evidence = action.get("evidence_source")
            if evidence:
                evidence_sources[evidence] += 1

    return {
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
        for line_number, raw_line in _nonblank_record_lines(handle):
            curated, manifest = _curate_jsonl_line(raw_line, source_label, line_number)
            manifests.append(manifest)
            if curated is not None:
                records.append(curated)

    summary = _jsonl_summary(source_label, records, manifests)
    return {"records": records, "manifest": manifests, "summary": summary}

if __package__:
    from . import coding_run_io as _run_io
    from .coding_verify import verify_curation, verify_manifest
else:
    import coding_run_io as _run_io
    from coding_verify import verify_curation, verify_manifest

__all__ = [
    "HIDDEN_REASONING_KEYS",
    "HIDDEN_REASONING_PREFIX",
    "MAX_DECISION_BASIS_CHARS",
    "REASON_BASIS_CONCISED",
    "REASON_BASIS_FROM_OBSERVATION",
    "REASON_BASIS_FROM_PLAN",
    "REASON_BASIS_FROM_REFLECTION",
    "REASON_BASIS_FROM_TOOL_CALL",
    "REASON_HIDDEN_REASONING_REMOVED",
    "REASON_INVALID_JSON",
    "REASON_INVALID_UTF8",
    "REASON_NO_RETAINABLE_STEPS",
    "REASON_NO_VISIBLE_EVIDENCE",
    "REASON_STEP_NOT_OBJECT",
    "REASON_STEPS_EXCLUDED",
    "REASON_STEPS_NOT_ARRAY",
    "REASON_THOUGHT_REMOVED",
    "REASON_WRAP_RECORD",
    "RUN_MANIFEST_FILENAME",
    "TRANSFORM_NAME",
    "TRANSFORM_VERSION",
    "_derive_decision_basis",
    "_record_id",
    "_record_steps",
    "steps_path",
    "preflight_destinations",
    "write_new_jsonl",
    "canonical_json",
    "contains_hidden_reasoning_key",
    "contains_thought_key",
    "curate_episode",
    "curate_jsonl",
    "curate_run",
    "curate_step",
    "hash_value",
    "is_hidden_reasoning_key",
    "main",
    "normalized_key_name",
    "verify_curation",
    "verify_manifest",
]


_is_under_raw = _run_io.is_under_raw
_created_file_identity = _run_io.created_file_identity
_created_directory_identity = _run_io.created_directory_identity
_unlink_created_file = _run_io.unlink_created_file
_rmdir_created_directory = _run_io.rmdir_created_directory
_preflight_destinations = _run_io.preflight_destinations
_source_jsonl_paths = _run_io.source_jsonl_paths
_new_run_destination = _run_io.new_run_destination
_make_output_directories = _run_io.make_output_directories
_rollback_created = _run_io.rollback_created


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


_RUN_SUMMARY_TOTALS = (
    "input_records",
    "output_records",
    "excluded_records",
    "source_steps",
    "retained_steps",
    "migrated_steps",
    "excluded_steps",
    "hidden_reasoning_fields_removed",
    "wrap_records",
)


def _write_curated_files(
    source_root: Path,
    source_paths: list[Path],
    output_root: Path,
    created_files: list[tuple[Path, tuple[int, int]]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Curate and write each source file at its relative path; return manifests and summaries."""
    manifests: list[dict[str, Any]] = []
    summaries: list[dict[str, Any]] = []
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
    return manifests, summaries


def _run_summary(
    source_root: Path,
    output_root: Path,
    source_paths: list[Path],
    summaries: list[dict[str, Any]],
) -> dict[str, Any]:
    """Aggregate the per-file summaries into the lane-level report."""
    evidence_sources: Counter[str] = Counter()
    for summary in summaries:
        evidence_sources.update(summary["decision_basis_sources"])
    totals = {
        field: sum(summary[field] for summary in summaries) for field in _RUN_SUMMARY_TOTALS
    }
    return {
        "source_path": str(source_root),
        "output_path": str(output_root),
        "manifest_path": str(output_root / RUN_MANIFEST_FILENAME),
        "input_files": len(source_paths),
        **totals,
        "decision_basis_sources": dict(sorted(evidence_sources.items())),
    }


def curate_run(source_dir: str | Path, output_dir: str | Path) -> dict[str, Any]:
    """Write one gate-ready coding lane for every JSONL in a source tree."""
    source_root, source_paths = _source_jsonl_paths(Path(source_dir))
    output_root = _new_run_destination(Path(output_dir), source_root)
    output_root.mkdir(parents=True, exist_ok=False)

    created_files: list[tuple[Path, tuple[int, int]]] = []
    created_directories = [
        (output_root, _created_directory_identity(output_root))
    ]
    try:
        _make_output_directories(output_root, source_root, source_paths, created_directories)
        manifests, summaries = _write_curated_files(
            source_root, source_paths, output_root, created_files
        )
        manifest_path = output_root / RUN_MANIFEST_FILENAME
        identity = _write_new_jsonl(manifest_path, manifests)
        created_files.append((manifest_path, identity))
    except BaseException:
        _rollback_created(created_files, created_directories)
        raise

    return _run_summary(source_root, output_root, source_paths, summaries)


write_new_jsonl = _write_new_jsonl
preflight_destinations = _preflight_destinations


def main(argv: list[str] | None = None) -> int:
    pipelines_dir = str(Path(__file__).resolve().parent)
    if pipelines_dir not in sys.path:
        sys.path.insert(0, pipelines_dir)
    from coding_cli import run

    return run(argv)


if __name__ == "__main__":
    raise SystemExit(main())
