"""Run the acceptance judge in a fresh interpreter."""

from __future__ import annotations

import os
import signal
import subprocess  # nosec B404
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

from . import vocabulary as cv
from ._contract import bind_import_twin, load_strict_json

__all__ = ["GateReport", "run_gate"]

CHILD_PATH = Path(__file__).with_name("_child.py")
PIPELINES = Path(__file__).resolve().parents[1]
INTERPRETER_FLAGS = ("-P", "-s", "-B", "-X", "utf8")
MAX_REPORT_BYTES = 64 * 1024
KILL_GRACE_S = 5


@dataclass(frozen=True)
class GateReport:
    """The child's decision. ``accepted`` is true only for a consistent pass."""

    accepted: bool
    code: str
    measured_blocker: bool | None
    counterfactual_holds: bool | None


def _child_environment(workdir: str) -> dict[str, str]:
    return {
        "PYTHONPATH": str(PIPELINES),
        "PYTHONHASHSEED": "0",
        "PYTHONDONTWRITEBYTECODE": "1",
        "HOME": workdir,
        "TMPDIR": workdir,
        "LANG": "C.UTF-8",
    }


def _refuse(code: str) -> GateReport:
    return GateReport(False, code, None, None)


def _kill_group(process: subprocess.Popen) -> None:
    try:
        os.killpg(process.pid, signal.SIGKILL)
    except ProcessLookupError, PermissionError:
        pass


def _launch(payload: bytes, timeout_s: float) -> bytes | None:
    with tempfile.TemporaryDirectory(prefix="honest-stop-") as workdir:
        Path(workdir, "record.json").write_bytes(payload)
        argv = [sys.executable, *INTERPRETER_FLAGS, str(CHILD_PATH), workdir]
        out_path = Path(workdir, "report.txt")
        try:
            with out_path.open("wb") as sink:
                process = subprocess.Popen(  # nosemgrep: python.lang.security.audit.dangerous-subprocess-use-audit.dangerous-subprocess-use-audit  # nosec B603
                    argv,
                    cwd=workdir,
                    env=_child_environment(workdir),
                    stdin=subprocess.DEVNULL,
                    stdout=sink,
                    stderr=subprocess.DEVNULL,
                    start_new_session=True,
                    close_fds=True,
                )
                timed_out = _wait(process, timeout_s)
        except OSError as exc:
            raise cv.FamilyError("harness.unavailable", f"cannot start child: {exc}") from exc
        if timed_out:
            return None
        return out_path.read_bytes()[:MAX_REPORT_BYTES]


def _wait(process: subprocess.Popen, timeout_s: float) -> bool:
    timed_out = False
    try:
        process.wait(timeout=timeout_s)
    except subprocess.TimeoutExpired:
        timed_out = True
    _kill_group(process)
    try:
        process.wait(timeout=KILL_GRACE_S)
    except subprocess.TimeoutExpired:
        timed_out = True
    return timed_out


def _marker_line(raw: bytes) -> str | None:
    lines = [
        line
        for line in raw.decode("utf-8", "replace").splitlines()
        if line.startswith(cv.GATE_MARKER)
    ]
    if len(lines) != 1:
        return None
    return lines[0][len(cv.GATE_MARKER) :]


def _consistent(report: dict) -> bool:
    if report.get("accepted") is not True:
        return True
    return (
        report.get("code") == cv.CODE_OK
        and report.get("measured_blocker") is True
        and report.get("counterfactual_holds") is False
    )


def _optional_bool(value: object) -> bool | None:
    if value is None or isinstance(value, bool):
        return value
    return None


def _from_report(report: object) -> GateReport:
    if not isinstance(report, dict) or report.get("protocol") != cv.GATE_PROTOCOL:
        return _refuse("harness.report")
    if not isinstance(report.get("accepted"), bool) or not isinstance(report.get("code"), str):
        return _refuse("harness.report")
    if not _consistent(report):
        return _refuse("harness.report")
    measured = _optional_bool(report.get("measured_blocker"))
    holds = _optional_bool(report.get("counterfactual_holds"))
    if report["accepted"]:
        return GateReport(True, cv.CODE_OK, True, False)
    return GateReport(False, report["code"], measured, holds)


def _parse(raw: bytes | None) -> GateReport:
    if raw is None:
        return _refuse("harness.timeout")
    line = _marker_line(raw)
    if line is None:
        return _refuse("harness.report")
    try:
        report = load_strict_json(line)
    except ValueError, RecursionError:
        return _refuse("harness.report")
    return _from_report(report)


def run_gate(payload: bytes, *, timeout_s: float = cv.DEFAULT_TIMEOUT_S) -> GateReport:
    """Judge ``payload`` in a child process. There is no in-process fallback."""

    if len(payload) > cv.MAX_RECORD_BYTES:
        return _refuse("record.too_large")
    try:
        raw = _launch(payload, timeout_s)
    except cv.FamilyError:
        return _refuse("harness.unavailable")
    return _parse(raw)


bind_import_twin(__name__)
