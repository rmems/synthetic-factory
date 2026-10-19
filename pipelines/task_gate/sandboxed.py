#!/usr/bin/env python3
"""The sandboxed harness: the gate's doctests run inside ``code_repair``'s OS boundary.

``SubprocessHarness`` stops accidents; this harness is for untrusted mutants (the model-backed
proposer). It reuses the ``code_repair`` boundary instead of reimplementing it: bwrap with a
read-only root, unshared user/net/pid namespaces, a private tmp, the seccomp filter and an
unprivileged uid (``Isolation.os_boundary``), then the Landlock allowlist the child applies to
itself. The network is denied by the kernel (an empty network namespace plus EPERM on
``connect``), not by patching ``socket``.

The report cannot be forged by writing to an inherited descriptor. A per-run nonce travels on
the child's stdin only and is consumed before ``program.py`` is read; the report must echo it
(see ``_sandboxed_child.py``). Reflectively recovering the nonce from the child's own frames is
the same hostile-introspection class as the AST tamper check and is not claimed closed.

It never falls back: an unavailable boundary refuses at construction, and a run whose limits or
Landlock were not attested on the real stdout refuses instead of producing a verdict.
"""

from __future__ import annotations

import hashlib
import hmac
import os
import secrets
import subprocess  # nosec B404
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from . import _executor_contract as ec
from . import vocabulary as cv
from ._contract import bind_import_twin, load_strict_json
from .harness import (
    INTERPRETER_FLAGS, MAX_REPORT_BYTES, HarnessResult, checked_timeout, child_environment,
    report_result, selfcheck,
)

CHILD_NAME = "_sandboxed_child.py"
CHILD_FILES = (
    ("_child.py", Path(__file__).with_name("_child.py")),
    (CHILD_NAME, Path(__file__).with_name(CHILD_NAME)),
    ("_sandbox.py", Path(ec.landlock.__file__)),
    ("_sandbox_paths.py", Path(ec.landlock.__file__).with_name("_sandbox_paths.py")),
)

__all__ = ["SandboxedHarness"]


def _refuse(detail: str) -> cv.GateRefusal:
    return cv.GateRefusal(cv.REFUSE_HARNESS_UNAVAILABLE, detail)


def _os_boundary(isolation: Any) -> Any:
    """The OS-boundary isolation, or a refusal: a sandbox that was asked for is never skipped."""

    try:
        active = isolation if isolation is not None else ec.sandbox.Isolation.os_boundary()
    except ec.RepairRefusal as exc:
        raise _refuse(f"sandbox requested but unavailable: {exc}") from exc
    cv.refuse_when(
        not active.is_os_boundary, cv.REFUSE_HARNESS_UNAVAILABLE,
        "sandbox requested but the isolation is not an OS boundary",
    )
    return active


def _child_bytes() -> dict[str, bytes]:
    try:
        return {name: path.read_bytes() for name, path in CHILD_FILES}
    except OSError as exc:
        raise _refuse(f"sandboxed child files are unreadable: {exc}") from exc


def _bundle_sha256(files: dict[str, bytes]) -> str:
    digest = hashlib.sha256()
    for name in sorted(files):
        for part in (name.encode("utf-8"), files[name]):
            digest.update(len(part).to_bytes(8, "big") + part)
    return digest.hexdigest()


def _require_attested(stdout: bytes) -> None:
    """Refuse the run unless both startup proofs were written before the program was read."""

    limits = ec.harness_report.limits_attested(stdout)
    cv.refuse_when(limits is not True, cv.REFUSE_HARNESS_UNAVAILABLE,
                   f"resource limits not attested: {limits}")
    token = ec.harness_report.landlock_attested(stdout)
    cv.refuse_when(not ec.landlock.applied(token), cv.REFUSE_HARNESS_UNAVAILABLE,
                   f"landlock not attested: {token}")


def _crashed(detail: str) -> HarnessResult:
    return HarnessResult(cv.OUTCOME_CRASHED, detail=detail)


def _parsed(body: bytes) -> object:
    try:
        return load_strict_json(body.decode("utf-8"))
    except (ValueError, RecursionError):
        return None


def _result_of_body(body: bytes, nonce: str) -> HarnessResult:
    """The result of a report that echoes the nonce; anything else is ``crashed``."""

    if len(body) > MAX_REPORT_BYTES:
        return _crashed("report_oversize")
    report = _parsed(body)
    echoed = report.get("nonce") if isinstance(report, dict) else None
    if not isinstance(echoed, str) or not hmac.compare_digest(echoed, nonce):
        return _crashed("report_nonce")
    return report_result(report)


@dataclass(frozen=True)
class _Run:
    """What one child run is started with: its workdir, environment, nonce and capture files."""

    workdir: Path
    env: dict[str, str]
    nonce: str
    out: Any
    report: Any


class SandboxedHarness:
    """Run a program's target-function doctests inside the ``code_repair`` OS boundary."""

    def __init__(
        self, timeout_s: float = cv.DEFAULT_TIMEOUT_S, python: str | None = None,
        isolation: Any = None,
    ) -> None:
        self.timeout_s = checked_timeout(timeout_s)
        self.python = python or sys.executable
        self.isolation = _os_boundary(isolation)
        self._files = _child_bytes()
        self.child_sha256 = _bundle_sha256(self._files)

    def describe(self) -> dict[str, object]:
        return {
            "protocol": cv.HARNESS_PROTOCOL, "kind": "sandboxed",
            "isolation": self.isolation.identity, "interpreter_flags": list(INTERPRETER_FLAGS),
            "timeout_s": self.timeout_s, "environment": sorted(child_environment("")),
            "child_sha256": self.child_sha256,
        }

    def selfcheck(self) -> None:
        """Refuse unless the harness separates a passing program from a failing one."""

        selfcheck(self)

    def run(self, program_text: str, function: str) -> HarnessResult:
        with tempfile.TemporaryDirectory(prefix="task-gate-sbx-") as tmp:
            workdir = Path(tmp)
            workdir.joinpath("program.py").write_text(program_text, encoding="utf-8")
            for name, payload in self._files.items():
                workdir.joinpath(name).write_bytes(payload)
            return self._execute(workdir, function)

    def _argv(self, workdir: Path, function: str, report_fd: int) -> list[str]:
        cpu_seconds = int(self.timeout_s) + 2
        return [
            self.python, *INTERPRETER_FLAGS, str(workdir / CHILD_NAME), str(workdir), function,
            str(cpu_seconds), str(report_fd),
        ]

    def _execute(self, workdir: Path, function: str) -> HarnessResult:
        nonce = secrets.token_hex(32)
        with tempfile.TemporaryFile() as out, tempfile.TemporaryFile() as report:
            os.set_inheritable(report.fileno(), True)
            env = child_environment(str(workdir))
            argv = self._argv(workdir, function, report.fileno())
            confined = self.isolation.confine(argv, workdir, env)
            try:
                code = self._spawn(confined, _Run(workdir, env, nonce, out, report))
            finally:
                confined.close()
            if code is None:
                return HarnessResult(cv.OUTCOME_TIMEOUT, detail="wall_clock")
            out.seek(0)
            report.seek(0)
            stdout, body = out.read(MAX_REPORT_BYTES), report.read(MAX_REPORT_BYTES + 1)
            return self._judged(code, stdout, body, nonce)

    def _spawn(self, confined: Any, run: _Run) -> int | None:
        """The child's exit status, or ``None`` when the wall clock expired."""

        try:
            done = subprocess.run(  # nosemgrep: python.lang.security.audit.dangerous-subprocess-use-audit.dangerous-subprocess-use-audit  # nosec B603
                confined.argv, cwd=run.workdir, env=run.env, input=run.nonce.encode("ascii"),
                stdout=run.out, stderr=subprocess.DEVNULL, timeout=self.timeout_s, check=False,
                pass_fds=(*confined.pass_fds, run.report.fileno()),
            )
        except subprocess.TimeoutExpired:
            return None
        except OSError as exc:
            raise _refuse(f"cannot start the sandbox: {exc}") from exc
        return done.returncode

    @staticmethod
    def _judged(returncode: int, stdout: bytes, body: bytes, nonce: str) -> HarnessResult:
        _require_attested(stdout)
        if returncode != 0:
            return _crashed("exit_status")
        return _result_of_body(body, nonce)


bind_import_twin(__name__)
