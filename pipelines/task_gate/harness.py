#!/usr/bin/env python3
"""The reference harness: one program's doctests in a scrubbed, time-boxed child interpreter.

The child is ``python3 -P -s -S -B -X utf8 _child.py`` started in a fresh working directory
holding only ``program.py``. ``-P -s -S`` keep the working directory, user site and every
site-packages (so no solver module, #160) off ``sys.path``; the environment is rebuilt from
scratch, so no proxy variable or API key reaches the program; the parent enforces a
wall-clock timeout and kills the whole process group; the child applies CPU, address-space
and file-size limits and replaces the socket entry points before the program is imported.

This is a harness, not a security sandbox: the network block is in-process and best effort,
and a hostile program can forge the report line. It stops accidents and keeps the oracle away
from solver code; the bwrap/Landlock executor in ``code_repair`` remains the stronger
boundary for untrusted catalogs. The ``Harness`` seam in ``gate.py`` takes either.
"""

from __future__ import annotations

import math
import os
import signal
import subprocess  # nosec B404
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from . import vocabulary as cv
from ._contract import bind_import_twin, load_strict_json
from .checks import is_count

CHILD_PATH = Path(__file__).with_name("_child.py")
INTERPRETER_FLAGS = ("-P", "-s", "-S", "-B", "-X", "utf8")
MARKER = "TASK-GATE-REPORT "
MAX_REPORT_BYTES = 64 * 1024
KILL_GRACE_S = 5

__all__ = [
    "HarnessResult", "SubprocessHarness", "checked_timeout", "child_environment",
    "report_result", "selfcheck",
]


@dataclass(frozen=True)
class HarnessResult:
    """What one child run observed. ``attempted`` counts doctest examples that ran."""

    outcome: str
    attempted: int = 0
    failed: int = 0
    detail: str = ""


def child_environment(workdir: str) -> dict[str, str]:
    """The whole child environment: nothing is inherited from the parent."""

    return {
        "PYTHONHASHSEED": "0",
        "PYTHONDONTWRITEBYTECODE": "1",
        "HOME": workdir,
        "TMPDIR": workdir,
        "LANG": "C.UTF-8",
    }


def _kill_group(process: subprocess.Popen) -> None:
    try:
        os.killpg(process.pid, signal.SIGKILL)
    except (ProcessLookupError, PermissionError):
        pass


def _report_of(raw: bytes) -> HarnessResult:
    lines = [
        line for line in raw.decode("utf-8", "replace").splitlines() if line.startswith(MARKER)
    ]
    if len(lines) != 1:
        return HarnessResult(cv.OUTCOME_CRASHED, detail="no_single_report")
    try:
        report = load_strict_json(lines[0][len(MARKER):])
    except (ValueError, RecursionError):
        return HarnessResult(cv.OUTCOME_CRASHED, detail="report_not_json")
    return _result_of(report)


def report_result(report: object) -> HarnessResult:
    """The result a child's parsed report stands for; a malformed report is ``crashed``."""

    return _result_of(report)


def _both_counts(attempted: object, failed: object) -> bool:
    return is_count(attempted) and is_count(failed)


def _counts_are_sound(attempted: object, failed: object) -> bool:
    return _both_counts(attempted, failed) and failed <= attempted


def _detail_of(report: dict) -> str:
    detail = report.get("detail")
    return detail if isinstance(detail, str) else ""


def _is_protocol_report(report: object) -> bool:
    return isinstance(report, dict) and report.get("protocol") == cv.HARNESS_PROTOCOL


def _result_of(report: object) -> HarnessResult:
    if not _is_protocol_report(report):
        return HarnessResult(cv.OUTCOME_CRASHED, detail="report_protocol")
    detail = _detail_of(report)
    if report.get("outcome") == "load_error":
        return HarnessResult(cv.OUTCOME_LOAD_ERROR, detail=detail)
    attempted, failed = report.get("attempted"), report.get("failed")
    if report.get("outcome") != "ran" or not _counts_are_sound(attempted, failed):
        return HarnessResult(cv.OUTCOME_CRASHED, detail=detail or "report_shape")
    return HarnessResult(
        cv.OUTCOME_FAILED if failed else cv.OUTCOME_PASSED, attempted, failed, detail,
    )


class SubprocessHarness:
    """Run a program's target-function doctests under a wall-clock timeout."""

    def __init__(self, timeout_s: float = cv.DEFAULT_TIMEOUT_S, python: str | None = None) -> None:
        self.timeout_s = checked_timeout(timeout_s)
        self.python = python or sys.executable

    def describe(self) -> dict[str, object]:
        return {
            "protocol": cv.HARNESS_PROTOCOL, "kind": "subprocess", "interpreter_flags": list(INTERPRETER_FLAGS),
            "timeout_s": self.timeout_s, "environment": sorted(child_environment("")),
        }

    def run(self, program_text: str, function: str) -> HarnessResult:
        with tempfile.TemporaryDirectory(prefix="task-gate-") as workdir:
            Path(workdir, "program.py").write_text(program_text, encoding="utf-8")
            out_path = Path(workdir, ".report")
            argv = [
                self.python, *INTERPRETER_FLAGS, str(CHILD_PATH), workdir, function,
                str(math.ceil(self.timeout_s) + 1),
            ]
            try:
                with out_path.open("wb") as sink:
                    process = subprocess.Popen(  # nosemgrep: python.lang.security.audit.dangerous-subprocess-use-audit.dangerous-subprocess-use-audit  # nosec B603
                        argv, cwd=workdir, env=child_environment(workdir), stdin=subprocess.DEVNULL,
                        stdout=sink, stderr=subprocess.DEVNULL, start_new_session=True,
                        close_fds=True,
                    )
                    timed_out = self._wait(process)
            except OSError as exc:
                raise cv.GateRefusal(cv.REFUSE_HARNESS_UNAVAILABLE, f"cannot start child: {exc}") from exc
            if timed_out:
                return HarnessResult(cv.OUTCOME_TIMEOUT, detail="wall_clock")
            with out_path.open("rb") as source:
                return _report_of(source.read(MAX_REPORT_BYTES))

    def _wait(self, process: subprocess.Popen) -> bool:
        """True when the run counts as a timeout; never blocks past the kill grace period."""

        timed_out = False
        try:
            process.wait(timeout=self.timeout_s)
        except subprocess.TimeoutExpired:
            timed_out = True
        _kill_group(process)  # also reaps stragglers a finished program left in its group
        try:
            process.wait(timeout=KILL_GRACE_S)
        except subprocess.TimeoutExpired:
            timed_out = True
        return timed_out

    def selfcheck(self) -> None:
        """Refuse unless the harness separates a passing program from a failing one."""

        selfcheck(self)


def checked_timeout(timeout_s: object) -> float:
    """The wall-clock budget as a float, or a coded refusal when it is outside the domain."""

    cv.refuse_when(
        isinstance(timeout_s, bool) or not isinstance(timeout_s, (int, float))
        or not math.isfinite(timeout_s) or not 0 < timeout_s <= cv.MAX_TIMEOUT_S,
        cv.REFUSE_TIMEOUT_DOMAIN, f"timeout must be in (0, {cv.MAX_TIMEOUT_S}] seconds",
    )
    return float(timeout_s)


def selfcheck(harness: Any) -> None:
    """Refuse unless ``harness`` separates a passing program from a failing one."""

    template = "def f(x):\n    '''\n    >>> f(1)\n    {want}\n    '''\n    return x\n"
    good = harness.run(template.format(want="1"), "f")
    bad = harness.run(template.format(want="2"), "f")
    cv.refuse_when(
        good != HarnessResult(cv.OUTCOME_PASSED, 1, 0)
        or bad.outcome != cv.OUTCOME_FAILED or bad.failed != 1,
        cv.REFUSE_HARNESS_UNAVAILABLE, f"harness self-check failed: {good} / {bad}",
    )


bind_import_twin(__name__)
