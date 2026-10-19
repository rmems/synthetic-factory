#!/usr/bin/env python3
"""Read the task gate's ``tasks.jsonl`` and rebuild each kept task's broken module.

Only ``kept`` rows are tasks; every other verdict is counted and skipped. A kept row is
re-resolved against the supplied program through the gate's own :func:`mutation.resolve`, and
the program and mutant digests recorded by the gate must match, so a tasks file cannot be
paired with a different catalog than the one that verified it.
"""

from __future__ import annotations

import hashlib
import os
import stat
from collections.abc import Mapping
from pathlib import Path
from typing import Any, NamedTuple

from . import band_vocabulary as bv
from . import mutation
from . import vocabulary as cv
from ._contract import StrictJsonlError, bind_import_twin, load_strict_json, strict_lf_jsonl_lines
from .band_solver import BandTask
from .checks import is_count, is_identifier, is_text
from .proposal import GateProgram, GateProposal

__all__ = ["KeptTask", "LoadedTasks", "load_kept", "rebuild"]

_KEPT_TEXT = ("program_id", "replacement_text", "program_sha256", "mutant_sha256")


class KeptTask(dict):
    """A kept ``tasks.jsonl`` row (a plain mapping, typed so callers can tell it apart)."""


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _invalid(detail: str) -> cv.GateRefusal:
    return cv.GateRefusal(bv.REFUSE_TASKS_INVALID, detail)


def _read(path: Path | str) -> bytes:
    try:
        if not stat.S_ISREG(os.stat(path).st_mode):
            raise _invalid(f"{path} is not a regular file")
        with Path(path).open("rb") as handle:
            data = handle.read(bv.MAX_TASKS_BYTES + 1)
    except OSError as exc:
        raise _invalid(f"{path}: {exc}") from exc
    if len(data) > bv.MAX_TASKS_BYTES:
        raise _invalid(f"{path} is too large")
    return data


def _kept_problem(row: dict) -> str | None:
    ok = all(is_text(row.get(key)) for key in _KEPT_TEXT) and is_identifier(row["program_id"])
    ok = ok and is_count(row.get("start_byte")) and is_count(row.get("end_byte"))
    return None if ok else "kept row lacks its span, program or digests"


def _row_problem(row: object) -> str | None:
    if not isinstance(row, dict) or row.get("format") != cv.TASKS_FORMAT:
        return "not a task-gate row"
    if row.get("verdict") not in cv.VERDICTS or not is_identifier(row.get("proposal_id")):
        return "unknown verdict or proposal_id"
    return _kept_problem(row) if row["verdict"] == cv.VERDICT_KEPT else None


def _rows(path: Path | str, data: bytes) -> list[dict[str, Any]]:
    try:
        rows = [load_strict_json(line) for line in strict_lf_jsonl_lines(data, str(path))]
    except (StrictJsonlError, ValueError, RecursionError) as exc:
        raise _invalid(f"{path}: {exc}") from exc
    for number, row in enumerate(rows, 1):
        problem = _row_problem(row)
        cv.refuse_when(problem is not None, bv.REFUSE_TASKS_INVALID, f"{path}:{number}: {problem}")
    ids = [row["proposal_id"] for row in rows]
    cv.refuse_when(len(set(ids)) != len(ids), bv.REFUSE_TASKS_INVALID, f"{path} repeats a proposal_id")
    return rows


class LoadedTasks(NamedTuple):
    """The kept rows in file order, the count skipped for another verdict, and the file digest."""

    kept: list[KeptTask]
    skipped: int
    sha256: str


def load_kept(path: Path | str) -> LoadedTasks:
    """Read ``tasks.jsonl`` once; only ``kept`` rows are tasks."""

    data = _read(path)
    rows = _rows(path, data)
    kept = [KeptTask(row) for row in rows if row["verdict"] == cv.VERDICT_KEPT]
    return LoadedTasks(kept, len(rows) - len(kept), hashlib.sha256(data).hexdigest())


def _mismatch(row: Mapping[str, Any], detail: str) -> cv.GateRefusal:
    return cv.GateRefusal(bv.REFUSE_TASK_PROGRAM_MISMATCH, f"{row['proposal_id']}: {detail}")


def rebuild(row: KeptTask, programs: Mapping[str, GateProgram]) -> tuple[BandTask, GateProgram]:
    """The task the solver is shown and the program it is scored against."""

    program = programs.get(row["program_id"])
    if program is None:
        raise _mismatch(row, "program is not in the supplied catalog")
    if _sha(program.text) != row["program_sha256"]:
        raise _mismatch(row, "program text differs from the one the gate verified")
    proposal = GateProposal(
        row["proposal_id"], row["program_id"], row["replacement_text"],
        start_byte=row["start_byte"], end_byte=row["end_byte"],
    )
    resolved = mutation.resolve(program, proposal)
    if isinstance(resolved, str) or _sha(resolved.mutant_text) != row["mutant_sha256"]:
        raise _mismatch(row, "mutant does not rebuild to the verified digest")
    return BandTask(row["proposal_id"], row["program_id"], program.function, resolved.mutant_text), program


bind_import_twin(__name__)
