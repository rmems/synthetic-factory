#!/usr/bin/env python3
"""Sandboxed execution of one program text: the parent side of the harness protocol.

One ``subprocess.run`` call site, a literal argv over ``sys.executable`` and
the sibling ``_harness.py``, a fresh temporary working directory per phase, a
minimal environment (``PYTHONHASHSEED=0`` for stable set and dict reprs), a
wall-clock timeout, and a strict parse of the child's single JSON report.
Wall time, exit codes and stderr tails go to a volatile execution log the
caller writes beside the run; nothing timing-dependent enters a
:class:`PhaseReport`, so the same program yields the same report bytes.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from . import vocabulary as cv
from ._contract import bind_import_twin, load_strict_json

HARNESS_PATH = Path(__file__).with_name("_harness.py")
INTERPRETER_FLAGS = ("-P", "-s", "-S", "-B", "-X", "utf8")
CHILD_ENV = {"PYTHONHASHSEED": "0", "PYTHONDONTWRITEBYTECODE": "1"}
FLOAT_REL_TOL = 1e-9
FLOAT_ABS_TOL = 1e-12
STDERR_TAIL_CHARS = 400
MAX_OUTPUT_BYTES = 2 * 1024 * 1024  # above the child's file-size limit, so a full read is complete

__all__ = [
    "CHILD_ENV", "Executor", "HARNESS_PATH", "INTERPRETER_FLAGS", "Job", "PhaseReport",
    "harness_sha256", "rows_of",
]


@dataclass(frozen=True)
class Job:
    """One program text to execute: its target function and the pinned hidden cases."""

    label: str
    module_text: str
    function: str
    cases: tuple[dict[str, Any], ...] = ()
    run_public: bool = True
    expected_public: int | None = None


@dataclass(frozen=True)
class PhaseReport:
    """What one execution showed. ``status`` is ``ok``, ``timeout`` or ``harness_error``."""

    status: str
    load_ok: bool
    public: tuple[dict[str, Any], ...]
    hidden: tuple[dict[str, Any], ...]
    environment: dict[str, Any] = field(default_factory=dict)
    detail: str = ""

    @property
    def ok(self) -> bool:
        return self.status == cv.PHASE_OK and self.load_ok


def harness_sha256() -> str:
    return hashlib.sha256(HARNESS_PATH.read_bytes()).hexdigest()


def rows_of(rows: tuple[dict[str, Any], ...]) -> list[dict[str, Any]]:
    """The digestable form of a row list: ``{id, status}`` plus the digest of any ``got``.

    A failing row's ``got`` text is not stored twice, but its digest is, so a
    consumer can check a rendered failure against the row the harness wrote.
    """

    digestable = []
    for row in rows:
        entry: dict[str, Any] = {"id": row["id"], "status": row["status"]}
        if "got" in row:
            entry["got_sha256"] = hashlib.sha256(str(row["got"]).encode("utf-8")).hexdigest()
        digestable.append(entry)
    return sorted(digestable, key=lambda row: row["id"])


def _check_timeout(timeout_s: Any) -> None:
    is_number = isinstance(timeout_s, (int, float)) and not isinstance(timeout_s, bool)
    cv.refuse_when(
        not is_number or not 0 < timeout_s <= cv.MAX_TIMEOUT_S,
        cv.FINDING_TIMEOUT_OUT_OF_DOMAIN,
        f"timeout_s must lie in (0, {cv.MAX_TIMEOUT_S}], got {cv.shown(timeout_s)}",
    )


def _tail(text: bytes) -> str:
    return text.decode("utf-8", "replace")[-STDERR_TAIL_CHARS:]


def _bounded(path: Path) -> bytes:
    """At most ``MAX_OUTPUT_BYTES`` of a child's stream; one byte more marks it oversized."""

    with path.open("rb") as handle:
        return handle.read(MAX_OUTPUT_BYTES + 1)


class Executor:
    """Runs jobs through the harness and keeps the volatile execution log."""

    def __init__(self, *, timeout_s: float = cv.DEFAULT_TIMEOUT_S) -> None:
        _check_timeout(timeout_s)
        self.timeout_s = float(timeout_s)
        self.harness_sha256 = harness_sha256()
        self.log: list[dict[str, Any]] = []

    def spec(self, job: Job) -> dict[str, Any]:
        return {
            "protocol": cv.HARNESS_PROTOCOL,
            "function": job.function,
            "run_public": job.run_public,
            "cases": list(job.cases),
            "float_rel_tol": FLOAT_REL_TOL,
            "float_abs_tol": FLOAT_ABS_TOL,
            "cpu_seconds": int(self.timeout_s) + 2,
            "address_space_bytes": cv.ADDRESS_SPACE_MIB * 1024 * 1024,
            "file_size_bytes": cv.FILE_SIZE_KIB * 1024,
        }

    def run(self, job: Job) -> PhaseReport:
        workdir = Path(tempfile.mkdtemp(prefix="code-repair-"))
        try:
            program = workdir / cv.PROGRAM_FILENAME
            program.write_text(job.module_text, encoding="utf-8", newline="\n")
            (workdir / "spec.json").write_text(_dumps(self.spec(job)), encoding="utf-8")
            return self._execute(job, workdir)
        finally:
            shutil.rmtree(workdir, ignore_errors=True)

    def _execute(self, job: Job, workdir: Path) -> PhaseReport:
        """One child run; its output goes to files in the workdir, never to an unbounded pipe.

        The child's file-size limit caps what it can write there, and the parent reads back at
        most ``MAX_OUTPUT_BYTES`` of each stream, so a child that streams forever cannot grow
        the factory process.
        """

        argv = [sys.executable, *INTERPRETER_FLAGS, str(HARNESS_PATH), str(workdir)]
        started = time.monotonic()
        entry: dict[str, Any] = {"label": job.label, "timed_out": False, "returncode": None}
        stdout_path, stderr_path = workdir / "stdout", workdir / "stderr"
        try:
            with stdout_path.open("wb") as out, stderr_path.open("wb") as err:
                completed = subprocess.run(
                    argv, cwd=workdir, env=CHILD_ENV, stdout=out, stderr=err,
                    timeout=self.timeout_s, check=False,
                )
        except subprocess.TimeoutExpired:
            entry.update(timed_out=True, stderr_tail=_tail(_bounded(stderr_path)))
            report = PhaseReport(cv.PHASE_TIMEOUT, False, (), (), {}, "timed out")
        else:
            entry.update(returncode=completed.returncode, stderr_tail=_tail(_bounded(stderr_path)))
            report = _parse_report(job, completed.returncode, _bounded(stdout_path))
        entry.update(duration_s=round(time.monotonic() - started, 6), status=report.status)
        self.log.append(entry)
        return report


def _dumps(payload: dict[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, allow_nan=False)


def _harness_error(detail: str) -> PhaseReport:
    return PhaseReport(cv.PHASE_HARNESS_ERROR, False, (), (), {}, detail)


def _parsed_report(returncode: int, stdout: bytes) -> dict[str, Any] | str:
    """The protocol object the child wrote, or the reason there is none."""

    if returncode != 0:
        return f"exit status {returncode}"
    try:
        parsed = load_strict_json(stdout.decode("utf-8"))
    except ValueError as exc:
        return f"report unreadable: {exc}"
    if not isinstance(parsed, dict) or parsed.get("protocol") != cv.HARNESS_PROTOCOL:
        return "report is not the protocol"
    return parsed


def _parse_report(job: Job, returncode: int, stdout: bytes) -> PhaseReport:
    """The child's report, or a harness error when it is not the protocol's complete object.

    Every row the job asked for must be present and well formed: a truncated
    or malformed suite is a harness error, never a suite with no failures.
    """

    parsed = _parsed_report(returncode, stdout)
    if isinstance(parsed, str):
        return _harness_error(parsed)
    load = parsed.get("load") if isinstance(parsed.get("load"), dict) else {}
    environment = parsed.get("environment") if isinstance(parsed.get("environment"), dict) else {}
    if load.get("status") != "ok":
        detail = str(load.get("error") or "load failed")
        return PhaseReport(cv.PHASE_OK, False, (), (), environment, detail)
    public = _rows("public", parsed.get("public"), job.expected_public if job.run_public else 0)
    hidden = _rows("hidden", parsed.get("hidden"), len(job.cases))
    if public is None or hidden is None:
        return _harness_error("report rows are missing or malformed")
    return PhaseReport(cv.PHASE_OK, True, public, hidden, environment)


def _well_formed(row: Any, expected_id: str) -> bool:
    return (
        isinstance(row, dict) and row.get("id") == expected_id
        and isinstance(row.get("status"), str) and isinstance(row.get("got", ""), str)
    )


def _row_list(value: Any) -> list[Any] | None:
    """The suite as a list: absent means empty, anything but a list is malformed."""

    if value is None:
        return []
    return list(value) if isinstance(value, list) else None


def _rows(prefix: str, value: Any, expected: int | None) -> tuple[dict[str, Any], ...] | None:
    """Rows ``prefix:0..expected-1`` in order, or None when the suite is malformed."""

    rows = _row_list(value)
    if rows is None:
        return None
    if expected is not None and len(rows) != expected:
        return None
    expected_ids = [f"{prefix}:{index}" for index in range(len(rows))]
    if not all(_well_formed(row, row_id) for row, row_id in zip(rows, expected_ids)):
        return None
    return tuple(rows)


bind_import_twin(__name__)
