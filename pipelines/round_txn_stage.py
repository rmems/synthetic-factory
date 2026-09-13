"""Staging inventory and notes validation using transaction-owned policy callbacks."""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from collections.abc import Callable


@dataclass(frozen=True)
class NotesPaths:
    captured_dir: Path
    notes_name: str
    stage: Path
    factory_dir: Path


@dataclass(frozen=True)
class NotesPolicy:
    error_type: type[Exception]
    validate_novel_coverage: Callable[..., str | None]
    coverage_required: bool


def _require_regular_file(path, error_type):
    if not path.is_file() or path.is_symlink():
        raise error_type(f"staging contains a non-regular file: {path}")


def _require_artifact(path, names, artifact_re, error_type):
    batch_name, notes_name, rr = names
    allowed_core = {batch_name, notes_name}
    _require_regular_file(path, error_type)
    if path.suffix == ".jsonl" and path.name != batch_name:
        raise error_type(
            f"staging may contain only the reserved JSONL batch: {path.name}"
        )
    if path.name not in allowed_core and not artifact_re.fullmatch(path.name):
        raise error_type(
            "auxiliary artifacts must be safe round-scoped .md/.json/.txt "
            f"files ending in -r{rr}: {path.name}"
        )


def _list_stage_paths(stage, error_type):
    if not stage.is_dir() or stage.is_symlink():
        raise error_type(f"staging directory missing or unsafe: {stage}")
    try:
        initial_paths = sorted(stage.iterdir())
    except OSError as exc:
        raise error_type(f"cannot inspect staging directory {stage}: {exc}") from exc
    return initial_paths


def inventory(stage: Path, round_number: int, error_type: type[Exception]):
    initial_paths = _list_stage_paths(stage, error_type)
    rr = f"{round_number:02d}"
    batch_name = f"batch-r{rr}.jsonl"
    notes_name = f"NOTES-r{rr}.md"
    artifact_re = re.compile(rf"^[A-Za-z0-9][A-Za-z0-9._-]*-r{re.escape(rr)}\.(?:md|json|txt)$")
    initial_names = {path.name for path in initial_paths}
    for path in initial_paths:
        _require_artifact(path, (batch_name, notes_name, rr), artifact_re, error_type)
    if batch_name not in initial_names:
        raise error_type(f"required staged batch missing or unsafe: {stage / batch_name}")
    if notes_name not in initial_names:
        raise error_type(f"required staged notes missing or unsafe: {stage / notes_name}")

    return initial_paths, initial_names, batch_name, notes_name


def validate_notes(paths: NotesPaths, policy: NotesPolicy):
    captured_dir, notes_name, stage, factory_dir = (
        paths.captured_dir, paths.notes_name, paths.stage, paths.factory_dir,
    )
    notes = captured_dir / notes_name
    try:
        notes_text = notes.read_text()
    except (OSError, UnicodeError) as exc:
        raise policy.error_type(
            f"cannot read staged notes as UTF-8: {stage / notes_name}: {exc}"
        ) from exc
    if not notes_text.strip():
        raise policy.error_type(f"staged notes are empty: {stage / notes_name}")
    # Every newly published registered factory round must carry the line,
    # legacy lanes included: the token-efficiency early-stop cannot latch
    # on rounds that never report their novelty. Unknown custom transaction
    # directories retain round_txn's generic NOTES contract.
    coverage_error = policy.validate_novel_coverage(
        stage / notes_name,
        factory_dir,
        notes_text,
        required=policy.coverage_required,
    )
    if coverage_error:
        raise policy.error_type(coverage_error)



