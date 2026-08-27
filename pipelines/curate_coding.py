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
        "thought_fields_removed": sum(
            summary["thought_fields_removed"] for summary in summaries
        ),
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
    args = parser.parse_args(argv)

    if args.output_dir is not None:
        if args.output_jsonl is not None or args.manifest_jsonl is not None:
            parser.error("--output-dir cannot be combined with file output options")
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
    if args.output_jsonl is not None:
        _write_new_jsonl(args.output_jsonl, result["records"])
    if args.manifest_jsonl is not None:
        _write_new_jsonl(args.manifest_jsonl, result["manifest"])
    print(json.dumps(result["summary"], ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
