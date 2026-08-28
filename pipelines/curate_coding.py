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
import json
import os
import sys
from collections import Counter
from pathlib import Path
from typing import Any

_PIPELINES = Path(__file__).resolve().parent
if str(_PIPELINES) not in sys.path:
    sys.path.insert(0, str(_PIPELINES))

from coding_common import (  # noqa: E402
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
    REASON_STEP_NOT_OBJECT,
    REASON_STEPS_EXCLUDED,
    REASON_STEPS_NOT_ARRAY,
    REASON_THOUGHT_REMOVED,
    REASON_WRAP_RECORD,
    RUN_MANIFEST_FILENAME,
    TRANSFORM_NAME,
    TRANSFORM_VERSION,
    canonical_json,
    contains_hidden_reasoning_key,
    contains_thought_key,
    curate_episode,
    curate_jsonl,
    curate_step,
    hash_value,
    is_hidden_reasoning_key,
    normalized_key_name,
)
from coding_verify import verify_curation, verify_manifest  # noqa: E402

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


def _build_parser() -> argparse.ArgumentParser:
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
    return parser


def _is_verifying(args: argparse.Namespace) -> bool:
    if args.verify:
        return True
    return args.expect_source_steps is not None


def _reject_negative_expected_steps(
    parser: argparse.ArgumentParser,
    args: argparse.Namespace,
) -> None:
    if args.expect_source_steps is None:
        return
    if args.expect_source_steps >= 0:
        return
    parser.error("--expect-source-steps must not be negative")


def _directory_option_conflicts(
    parser: argparse.ArgumentParser,
    args: argparse.Namespace,
    verifying: bool,
) -> None:
    if args.output_jsonl is not None:
        parser.error("--output-dir cannot be combined with file output options")
    if args.manifest_jsonl is not None:
        parser.error("--output-dir cannot be combined with file output options")
    if verifying:
        parser.error("--output-dir cannot be combined with --verify")
    if not args.source.is_dir():
        parser.error("--output-dir requires a source directory")


def _main_output_dir(parser: argparse.ArgumentParser, args: argparse.Namespace) -> int:
    _reject_negative_expected_steps(parser, args)
    _directory_option_conflicts(parser, args, _is_verifying(args))
    try:
        result = curate_run(args.source, args.output_dir)
    except (FileExistsError, OSError, ValueError) as exc:
        parser.error(str(exc))
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


def _output_replaces_source(output_jsonl: Path | None, source: Path) -> bool:
    if output_jsonl is None:
        return False
    return output_jsonl.resolve(strict=False) == source.resolve()


def _requested_destinations(args: argparse.Namespace) -> list[Path]:
    destinations = []
    if args.output_jsonl is not None:
        destinations.append(args.output_jsonl)
    if args.manifest_jsonl is not None:
        destinations.append(args.manifest_jsonl)
    return destinations


def _write_curation_outputs(
    args: argparse.Namespace,
    result: dict[str, Any],
    summary: dict[str, Any],
) -> int:
    if args.output_jsonl is not None:
        _write_new_jsonl(args.output_jsonl, result["records"])
    if args.manifest_jsonl is not None:
        _write_new_jsonl(args.manifest_jsonl, result["manifest"])
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


def _print_violations(violations: list[str]) -> None:
    for violation in violations:
        print(f"VIOLATION: {violation}", file=sys.stderr)


def _verified_file_run(args: argparse.Namespace, result: dict[str, Any]) -> int:
    violations = verify_curation(
        result, expected_source_steps=args.expect_source_steps
    )
    summary = dict(result["summary"])
    summary["verification"] = {
        "expected_source_steps": args.expect_source_steps,
        "violations": violations,
    }
    if not violations:
        return _write_curation_outputs(args, result, summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    _print_violations(violations)
    return 2


def _main_source_file(parser: argparse.ArgumentParser, args: argparse.Namespace) -> int:
    _reject_negative_expected_steps(parser, args)
    if args.source.is_dir():
        parser.error("a source directory requires --output-dir")
    if _output_replaces_source(args.output_jsonl, args.source):
        parser.error("output must not replace the source")
    try:
        _preflight_destinations(_requested_destinations(args))
    except (FileExistsError, ValueError) as exc:
        parser.error(str(exc))
    result = curate_jsonl(args.source)
    if not _is_verifying(args):
        return _write_curation_outputs(args, result, result["summary"])
    return _verified_file_run(args, result)


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    if args.output_dir is not None:
        return _main_output_dir(parser, args)
    return _main_source_file(parser, args)


if __name__ == "__main__":
    raise SystemExit(main())
