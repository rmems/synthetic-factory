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


def rows_of(rows: tuple[dict[str, Any], ...]) -> list[dict[str, str]]:
    """The digestable form of a row list: ``{id, status}`` only, sorted by id."""

    digestable = ({"id": row["id"], "status": row["status"]} for row in rows)
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
        argv = [sys.executable, *INTERPRETER_FLAGS, str(HARNESS_PATH), str(workdir)]
        started = time.monotonic()
        entry: dict[str, Any] = {"label": job.label, "timed_out": False, "returncode": None}
        try:
            completed = subprocess.run(
                argv, cwd=workdir, env=CHILD_ENV, capture_output=True,
                timeout=self.timeout_s, check=False,
            )
        except subprocess.TimeoutExpired as expired:
            entry.update(timed_out=True, stderr_tail=_tail(expired.stderr or b""))
            report = PhaseReport(cv.PHASE_TIMEOUT, False, (), (), {}, "timed out")
        else:
            entry.update(returncode=completed.returncode, stderr_tail=_tail(completed.stderr))
            report = _parse_report(completed.returncode, completed.stdout)
        entry.update(duration_s=round(time.monotonic() - started, 6), status=report.status)
        self.log.append(entry)
        return report


def _dumps(payload: dict[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, allow_nan=False)


def _parse_report(returncode: int, stdout: bytes) -> PhaseReport:
    """The child's report, or a harness error when it is not the protocol's one object."""

    if returncode != 0:
        return PhaseReport(cv.PHASE_HARNESS_ERROR, False, (), (), {}, f"exit status {returncode}")
    try:
        parsed = load_strict_json(stdout.decode("utf-8"))
    except ValueError as exc:
        return PhaseReport(cv.PHASE_HARNESS_ERROR, False, (), (), {}, f"report unreadable: {exc}")
    if not isinstance(parsed, dict) or parsed.get("protocol") != cv.HARNESS_PROTOCOL:
        return PhaseReport(cv.PHASE_HARNESS_ERROR, False, (), (), {}, "report is not the protocol")
    load = parsed.get("load") if isinstance(parsed.get("load"), dict) else {}
    environment = parsed.get("environment") if isinstance(parsed.get("environment"), dict) else {}
    if load.get("status") != "ok":
        detail = str(load.get("error") or "load failed")
        return PhaseReport(cv.PHASE_OK, False, (), (), environment, detail)
    return PhaseReport(
        cv.PHASE_OK, True, _rows(parsed.get("public")), _rows(parsed.get("hidden")), environment
    )


def _rows(value: Any) -> tuple[dict[str, Any], ...]:
    if not isinstance(value, list):
        return ()
    return tuple(row for row in value if isinstance(row, dict) and isinstance(row.get("id"), str))


bind_import_twin(__name__)
