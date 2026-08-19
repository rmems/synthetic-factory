#!/usr/bin/env python3
"""Curate legacy coding episodes into observable, thought-free records.

The transform is deliberately record-level and side-effect free by default.
It removes every mapping key named ``thought`` and derives a concise
``decision_basis`` only from fields that are visible in the source record:
plan, reflection, observation, or tool call.
Steps without usable visible evidence are excluded with machine-readable
reason codes; the transform never consults the removed thought text.

``curate_jsonl`` returns curated records, a reversible manifest, and summary
counts.  The optional CLI writes only to new, non-raw files.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
from collections import Counter
from pathlib import Path
from typing import Any


TRANSFORM_NAME = "coding_observability"
TRANSFORM_VERSION = "1"
MAX_DECISION_BASIS_CHARS = 240

REASON_THOUGHT_REMOVED = "coding_thought_removed"
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


def _strip_thought_keys(value: Any) -> tuple[Any, int]:
    """Deep-copy ``value`` while removing every mapping key named thought."""
    if isinstance(value, dict):
        cleaned = {}
        removed = 0
        for key, item in value.items():
            if key == "thought":
                removed += 1
                continue
            clean_item, nested_removed = _strip_thought_keys(item)
            cleaned[key] = clean_item
            removed += nested_removed
        return cleaned, removed
    if isinstance(value, list):
        cleaned_items = []
        removed = 0
        for item in value:
            clean_item, nested_removed = _strip_thought_keys(item)
            cleaned_items.append(clean_item)
            removed += nested_removed
        return cleaned_items, removed
    return copy.deepcopy(value), 0


def contains_thought_key(value: Any) -> bool:
    """Return whether any nested mapping exposes a key named thought."""
    if isinstance(value, dict):
        return "thought" in value or any(contains_thought_key(v) for v in value.values())
    if isinstance(value, list):
        return any(contains_thought_key(item) for item in value)
    return False


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
        "thought_fields_removed": 0,
    }
    if not isinstance(step, dict):
        manifest["reason_codes"] = [REASON_STEP_NOT_OBJECT]
        return None, manifest

    cleaned, removed = _strip_thought_keys(step)
    manifest["thought_fields_removed"] = removed
    basis, evidence_source, concised = _derive_decision_basis(cleaned)
    if basis is None:
        reasons = []
        if removed:
            reasons.append(REASON_THOUGHT_REMOVED)
        reasons.append(REASON_NO_VISIBLE_EVIDENCE)
        manifest["reason_codes"] = reasons
        return None, manifest

    prior_basis = cleaned.get("decision_basis")
    cleaned["decision_basis"] = basis
    changed = bool(removed) or prior_basis != basis
    reasons = []
    if removed:
        reasons.append(REASON_THOUGHT_REMOVED)
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
    if contains_thought_key(cleaned):
        raise AssertionError("coding curation emitted a thought key")
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
        "thought_fields_removed": 0,
        "step_counts": {
            "source": 0,
            "retained": 0,
            "migrated": 0,
            "excluded": 0,
        },
        "step_actions": [],
    }


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

    steps = record.get("steps")
    if not isinstance(steps, list):
        manifest["reason_codes"] = [REASON_STEPS_NOT_ARRAY]
        return None, manifest

    cleaned_record, record_thoughts_removed = _strip_thought_keys(record)
    manifest["thought_fields_removed"] = record_thoughts_removed
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

    cleaned_record["steps"] = retained_steps
    reasons = []
    if record_thoughts_removed:
        reasons.append(REASON_THOUGHT_REMOVED)
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
    if contains_thought_key(cleaned_record):
        raise AssertionError("coding curation emitted a thought key")
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


def curate_jsonl(source_path: str | Path) -> dict[str, Any]:
    """Read a JSONL source without mutation and curate every nonblank line."""
    source = Path(source_path)
    records = []
    manifests = []

    with source.open("rb") as handle:
        for line_number, terminated_line in enumerate(handle, 1):
            raw_line = terminated_line.rstrip(b"\r\n")
            if not raw_line.strip():
                continue
            source_hash = hashlib.sha256(raw_line).hexdigest()
            try:
                text = raw_line.decode("utf-8")
            except UnicodeDecodeError:
                manifests.append(
                    _excluded_line_manifest(
                        source_path=str(source),
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
                        source_path=str(source),
                        source_line=line_number,
                        source_hash=source_hash,
                        reason=REASON_INVALID_JSON,
                    )
                )
                continue

            curated, manifest = curate_episode(
                record,
                source_path=str(source),
                source_line=line_number,
                source_hash=source_hash,
            )
            manifests.append(manifest)
            if curated is not None:
                records.append(curated)

    step_counts = Counter()
    evidence_sources = Counter()
    for manifest in manifests:
        step_counts.update(manifest["step_counts"])
        for action in manifest["step_actions"]:
            evidence = action.get("evidence_source")
            if evidence:
                evidence_sources[evidence] += 1

    summary = {
        "source_path": str(source),
        "input_records": len(manifests),
        "output_records": len(records),
        "excluded_records": sum(item["action"] == "excluded" for item in manifests),
        "source_steps": step_counts["source"],
        "retained_steps": step_counts["retained"],
        "migrated_steps": step_counts["migrated"],
        "excluded_steps": step_counts["excluded"],
        "thought_fields_removed": sum(
            manifest["thought_fields_removed"] for manifest in manifests
        ),
        "decision_basis_sources": dict(sorted(evidence_sources.items())),
    }
    return {"records": records, "manifest": manifests, "summary": summary}


def _is_under_raw(path: Path) -> bool:
    parts = path.resolve(strict=False).parts
    return any(
        parts[index : index + 2] == ("outputs", "raw")
        for index in range(len(parts) - 1)
    )


def _write_new_jsonl(path: Path, values: list[dict[str, Any]]) -> None:
    """Write one JSONL file without replacing any pre-existing path."""
    if _is_under_raw(path):
        raise ValueError(f"refusing to write inside immutable raw evidence: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            for value in values:
                handle.write(canonical_json(value))
                handle.write("\n")
    except BaseException:
        path.unlink(missing_ok=True)
        raise


def _preflight_destinations(paths: list[Path]) -> None:
    resolved = [path.resolve(strict=False) for path in paths]
    if len(set(resolved)) != len(resolved):
        raise ValueError("output destinations must be distinct")
    for path in paths:
        if _is_under_raw(path):
            raise ValueError(f"refusing to write inside immutable raw evidence: {path}")
        if path.exists():
            raise FileExistsError(f"refusing to replace existing destination: {path}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="legacy episode JSONL to inspect")
    parser.add_argument("--output-jsonl", type=Path)
    parser.add_argument("--manifest-jsonl", type=Path)
    args = parser.parse_args(argv)

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
    if args.output_jsonl is not None:
        _write_new_jsonl(args.output_jsonl, result["records"])
    if args.manifest_jsonl is not None:
        _write_new_jsonl(args.manifest_jsonl, result["manifest"])
    print(json.dumps(result["summary"], ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
