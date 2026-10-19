#!/usr/bin/env python3
"""The sandboxed harness: the gate's doctests run inside ``code_repair``'s OS boundary.

``SubprocessHarness`` stops accidents; this harness is for untrusted mutants (the model-backed
proposer). It reuses the ``code_repair`` boundary instead of reimplementing it: bwrap with a
read-only root, unshared user/net/pid namespaces, a private tmp, the seccomp filter and an
unprivileged uid (``Isolation.os_boundary``), then the Landlock allowlist the child applies to
itself. The network is denied by the kernel (an empty network namespace plus EPERM on
``connect``), not by patching ``socket``.

The verdict is made here, never in the process that loads the program. This process parses the
target's doctests (``sandboxed_plan.py``), gives the child the program with that docstring
emptied plus each example's source, and compares what the child reports each example produced
with the expected output it kept (``sandboxed_judge.py``). So:

* A pass cannot be forged. The expected outputs never enter the sandbox; a program passes only
  by producing them, or by guessing them from the example source alone.
* Writing to the report file from outside the child's own code (a forked poller, a write to an
  inherited descriptor, a truncation) makes the run ``crashed``, never a verdict: each record
  is sealed with a per-run key that reaches the child on stdin only, is consumed before
  ``program.py`` is read, and is never written to any file, argument or environment variable.
* Not closed: a program that tampers with the interpreter it runs in (rebinding the child's
  checker or channel, reading the key out of the child's memory) can make its own run report
  ``failed`` or ``crashed``. It still cannot report a pass. This is the hostile-introspection
  class the AST tamper check in ``mutation.py`` also leaves open.

It never falls back: an unavailable boundary refuses at construction, and a run whose limits or
Landlock were not attested on the real stdout refuses instead of producing a verdict.
"""

from __future__ import annotations

import hashlib
import os
import secrets
import subprocess  # nosec B404
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from . import _executor_contract as ec
from . import _sandboxed_record as record
from . import vocabulary as cv
from ._contract import bind_import_twin
from .harness import (
    INTERPRETER_FLAGS, MAX_REPORT_BYTES, HarnessResult, checked_timeout, child_environment,
    selfcheck,
)
from .sandboxed_judge import judged, report_limit
from .sandboxed_plan import Plan, plan_for

CHILD_NAME = "_sandboxed_child.py"
CHILD_FILES = (
    ("_child.py", Path(__file__).with_name("_child.py")),
    (CHILD_NAME, Path(__file__).with_name(CHILD_NAME)),
    ("_sandboxed_record.py", Path(__file__).with_name("_sandboxed_record.py")),
    ("_sandbox.py", ec.executor.SANDBOX_PATH),
    ("_sandbox_paths.py", ec.executor.SANDBOX_PATHS_PATH),
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
    cv.refuse_when(not ec.executor.landlock_applied(token), cv.REFUSE_HARNESS_UNAVAILABLE,
                   f"landlock not attested: {token}")


@dataclass(frozen=True)
class _Run:
    """What one child run is started with: its workdir, environment, stdin and capture files."""

    workdir: Path
    env: dict[str, str]
    stdin: bytes
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
        plan = plan_for(program_text, function)
        if plan.outcome:  # decided from the text alone; no program code runs
            return HarnessResult(plan.outcome, detail=plan.detail)
        with tempfile.TemporaryDirectory(prefix="task-gate-sbx-") as tmp:
            workdir = Path(tmp)
            workdir.joinpath("program.py").write_text(plan.text, encoding="utf-8")
            for name, payload in self._files.items():
                workdir.joinpath(name).write_bytes(payload)
            return self._execute(workdir, function, plan)

    def _argv(self, workdir: Path, function: str, report_fd: int) -> list[str]:
        cpu_seconds = int(self.timeout_s) + 2
        return [
            self.python, *INTERPRETER_FLAGS, str(workdir / CHILD_NAME), str(workdir), function,
            str(cpu_seconds), str(report_fd),
        ]

    def _execute(self, workdir: Path, function: str, plan: Plan) -> HarnessResult:
        key = secrets.token_bytes(record.KEY_BYTES)
        limit = report_limit(len(plan.examples))
        with tempfile.TemporaryFile() as out, tempfile.TemporaryFile() as report:
            os.set_inheritable(report.fileno(), True)
            env = child_environment(str(workdir))
            argv = self._argv(workdir, function, report.fileno())
            confined = self.isolation.confine(argv, workdir, env)
            try:
                finished = self._spawn(confined, _Run(workdir, env, plan.child_input(key), out, report))
            finally:
                confined.close()
            out.seek(0)
            report.seek(0)
            stdout, body = out.read(MAX_REPORT_BYTES), report.read(limit + 1)
        _require_attested(stdout)  # unattested means the program never ran
        if not finished:
            return HarnessResult(cv.OUTCOME_TIMEOUT, detail="wall_clock")
        if len(body) > limit:
            return HarnessResult(cv.OUTCOME_CRASHED, detail="report_oversize")
        return judged(plan.examples, body, key)

    def _spawn(self, confined: Any, run: _Run) -> bool:
        """True when the child ended within the wall clock.

        Its exit status is not consulted: the program controls it, and the sealed report is
        the only account of the run.
        """

        try:
            subprocess.run(  # nosemgrep: python.lang.security.audit.dangerous-subprocess-use-audit.dangerous-subprocess-use-audit  # nosec B603
                confined.argv, cwd=run.workdir, env=run.env, input=run.stdin,
                stdout=run.out, stderr=subprocess.DEVNULL, timeout=self.timeout_s, check=False,
                pass_fds=(*confined.pass_fds, run.report.fileno()),
            )
        except subprocess.TimeoutExpired:
            return False
        except OSError as exc:
            raise _refuse(f"cannot start the sandbox: {exc}") from exc
        return True


bind_import_twin(__name__)
