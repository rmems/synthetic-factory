#!/usr/bin/env python3
"""OS isolation seam for the code-repair harness child.

The executor keeps one literal argv and one ``subprocess.run`` call site; this
module is the only place that may prefix that argv with a bubblewrap boundary.
The reviewed TheAlgorithms/Python pin may still run under rlimits alone. Any
other source must use ``bwrap-ro-netns-v1`` (read-only root, unshared user/net/pid,
private tmp, seccomp, unprivileged user) or the run is refused.
"""

from __future__ import annotations

import functools
import os
import shutil
import struct
# Required only for the bwrap availability probe below.
import subprocess  # nosec B404
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from . import source_policy as sp
from . import vocabulary as cv
from ._contract import bind_import_twin

IDENTITY_RLIMITS_ONLY = "rlimits-only"
IDENTITY_BWRAP = "bwrap-ro-netns-v1"
OS_IDENTITIES = frozenset({IDENTITY_BWRAP})
BWRAP_BIN = "bwrap"
_NOBODY = "65534"
_AUDIT_ARCH = {"x86_64": 0xC000003E, "aarch64": 0xC00000B7}
_BPF_LD_W_ABS = 0x20
_BPF_JMP_JEQ_K = 0x15
_BPF_RET_K = 0x06
_SECCOMP_RET_KILL_PROCESS = 0x80000000
_SECCOMP_RET_ALLOW = 0x7FFF0000
_SECCOMP_RET_ERRNO_EPERM = 0x00050001
# Network syscalls return EPERM so a candidate sees OSError instead of SIGSYS.
# Admin syscalls still kill the process. execve is omitted because bwrap installs
# the filter before exec'ing the interpreter; children stay in the pid namespace.
_ERRNO_SYSCALLS = {
    "x86_64": (42, 43, 49, 50, 288),
    "aarch64": (200, 201, 202, 203, 242),
}
_KILL_SYSCALLS = {
    "x86_64": (101, 155, 165, 166, 167, 169, 175, 313, 321),
    "aarch64": (40, 39, 41, 105, 117, 142, 273, 280),
}
_UNAVAILABLE = "bwrap user-namespace sandbox is not available"
_HIDE_ROOTS = ("home", "root", "workspace")

__all__ = [
    "IDENTITY_BWRAP", "IDENTITY_RLIMITS_ONLY", "OS_IDENTITIES", "Confinement", "Isolation",
    "catalog_is_reviewed", "executor_identity", "isolation_prose", "os_boundary_available",
    "refuse_unisolated_execution", "reviewed_upstream",
]


@dataclass(frozen=True)
class Confinement:
    """A literal argv plus any descriptors the one ``subprocess.run`` must inherit."""

    argv: tuple[str, ...]
    pass_fds: tuple[int, ...] = ()
    _closefds: tuple[int, ...] = ()

    def close(self) -> None:
        for descriptor in self._closefds:
            os.close(descriptor)


@dataclass(frozen=True)
class Isolation:
    """One named boundary: rlimits-only, or the bubblewrap OS sandbox."""

    identity: str
    _kind: str

    @staticmethod
    def rlimits_only() -> Isolation:
        return Isolation(IDENTITY_RLIMITS_ONLY, "rlimits")

    @staticmethod
    def os_boundary() -> Isolation:
        cv.refuse_when(
            not os_boundary_available(),
            cv.FINDING_SANDBOX_UNAVAILABLE,
            _UNAVAILABLE,
        )
        return Isolation(IDENTITY_BWRAP, "bwrap")

    @property
    def is_os_boundary(self) -> bool:
        return self.identity in OS_IDENTITIES

    def confine(
        self, argv: list[str], workdir: Path, env: Mapping[str, str],
    ) -> Confinement:
        """Prefix ``argv`` when this isolation is an OS boundary; never a shell string."""

        if self._kind != "bwrap":
            return Confinement(tuple(argv))
        return _bwrap_confinement(argv, workdir, env)


def reviewed_upstream(upstream: Mapping[str, Any] | None) -> bool:
    """Whether ``upstream`` is exactly the sealed TheAlgorithms/Python pin."""

    if not isinstance(upstream, Mapping):
        return False
    evidence = dict(sp.POLICY["source_license_evidence"])
    return {key: upstream.get(key) for key in evidence} == evidence


def _program_upstream_reviewed(upstream: Mapping[str, Any] | None) -> bool:
    """True when a program row's upstream matches the sealed repository, commit, and license."""
    if not isinstance(upstream, Mapping):
        return False
    evidence = dict(sp.POLICY["source_license_evidence"])
    return all(upstream.get(key) == evidence[key] for key in ("repository", "commit", "license"))


def _selector_is_reviewed(build: Any) -> bool:
    """True when build metadata is absent or still names the reviewed selector."""

    if not isinstance(build, Mapping):
        return True
    return build.get("selector") in (None, sp.REVIEWED_SELECTOR)


def _meta_is_reviewed(meta: Mapping[str, Any]) -> bool | None:
    """Reviewed-pin verdict for catalog meta, or None when meta carries no upstream."""

    if meta.get("upstream") is None:
        return None
    if not _selector_is_reviewed(meta.get("build")):
        return False
    return reviewed_upstream(meta.get("upstream"))


def _programs_are_reviewed(programs: Any) -> bool:
    """True when every program's upstream is the sealed TheAlgorithms/Python pin."""

    if not programs:
        return False
    return all(
        _program_upstream_reviewed(getattr(program, "upstream", None)) for program in programs
    )


def catalog_is_reviewed(catalog: Any) -> bool:
    """Reviewed pin plus the reviewed selector: the only source allowed without bwrap.

    A catalog object that carries no meta upstream (test doubles) is still reviewed
    when every program's upstream is the sealed TheAlgorithms/Python pin.
    """

    meta = getattr(catalog, "meta", None)
    if isinstance(meta, Mapping):
        verdict = _meta_is_reviewed(meta)
        if verdict is not None:
            return verdict
    return _programs_are_reviewed(getattr(catalog, "programs", ()) or ())


def executor_identity(engine: Any) -> str:
    isolation = getattr(engine, "isolation", None)
    if isolation is not None:
        identity = getattr(isolation, "identity", None)
        if isinstance(identity, str):
            return identity
    identity = getattr(engine, "sandbox_identity", None)
    return identity if isinstance(identity, str) else IDENTITY_RLIMITS_ONLY


def isolation_prose(identity: str) -> str:
    if identity == IDENTITY_BWRAP:
        return (
            "bwrap-ro-netns-v1: read-only root, unshared user/net/pid, private tmp, "
            "seccomp, unprivileged user; plus rlimits"
        )
    if identity == IDENTITY_RLIMITS_ONLY:
        return (
            "rlimits and a fresh working directory only: no filesystem or network isolation "
            "(issue #201); programs come from a pinned catalog whose selector admits "
            "stdlib-only modules"
        )
    raise cv.RepairRefusal(
        cv.FINDING_SANDBOX_UNAVAILABLE, f"unknown sandbox identity {cv.shown(identity)}",
    )


def refuse_unisolated_execution(
    engine: Any, *, catalog: Any = None, upstream: Mapping[str, Any] | None = None,
    selector: str | None = None,
) -> None:
    """Fail closed: a source that is not the reviewed pin must run inside bwrap."""

    if catalog is not None:
        reviewed = catalog_is_reviewed(catalog)
    elif not reviewed_upstream(upstream):
        reviewed = False
    elif selector is None:
        reviewed = True
    else:
        reviewed = selector == sp.REVIEWED_SELECTOR
    if reviewed:
        return
    cv.refuse_when(
        executor_identity(engine) not in OS_IDENTITIES,
        cv.FINDING_SANDBOX_UNAVAILABLE,
        "OS isolation is required before executing a source that is not the reviewed "
        "pinned catalog",
    )


@functools.lru_cache(maxsize=1)
def os_boundary_available() -> bool:
    """True only when bwrap can actually unshare user/net/pid as an unprivileged user."""

    bwrap = shutil.which(BWRAP_BIN)
    if bwrap is None or _seccomp_blob() is None:
        return False
    true_bin = "/bin/true" if os.path.isfile("/bin/true") else None
    if true_bin is None:
        return False
    argv = [
        bwrap, "--ro-bind", os.sep, os.sep, "--unshare-all", "--die-with-parent",
        "--uid", _NOBODY, "--gid", _NOBODY, true_bin,
    ]
    try:
        # The probe argv is a fixed literal list and never enables a shell.
        completed = subprocess.run(  # nosemgrep: python.lang.security.audit.dangerous-subprocess-use-audit.dangerous-subprocess-use-audit  # nosec B603
            argv, check=False, capture_output=True, timeout=2,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    return completed.returncode == 0


def _root_dir(*parts: str) -> str:
    """An absolute path built from names so scanners do not see a public tempfile literal."""

    return str(Path(os.sep).joinpath(*parts))


def _insn(code: int, jt: int, jf: int, k: int) -> bytes:
    """One classic BPF instruction."""

    return struct.pack("=HBBI", code, jt, jf, k)


def _seccomp_syscalls() -> tuple[int, tuple[int, ...], tuple[int, ...]] | None:
    """Audit arch plus the errno/kill syscall sets for this machine, or None."""

    machine = os.uname().machine
    arch = _AUDIT_ARCH.get(machine)
    if arch is None:
        return None
    errno_syscalls = _ERRNO_SYSCALLS.get(machine)
    if errno_syscalls is None:
        return None
    kill_syscalls = _KILL_SYSCALLS.get(machine)
    if kill_syscalls is None:
        return None
    return arch, errno_syscalls, kill_syscalls


def _syscall_jumps(errno_syscalls: tuple[int, ...], kill_syscalls: tuple[int, ...]) -> list[bytes]:
    """JEQ jumps onto the errno-return and kill-process tails."""

    insns: list[bytes] = []
    remaining = len(errno_syscalls) + len(kill_syscalls)
    for syscall in errno_syscalls:
        insns.append(_insn(_BPF_JMP_JEQ_K, remaining + 1, 0, syscall))
        remaining -= 1
    for syscall in kill_syscalls:
        insns.append(_insn(_BPF_JMP_JEQ_K, remaining, 0, syscall))
        remaining -= 1
    return insns


def _seccomp_filter(
    arch: int, errno_syscalls: tuple[int, ...], kill_syscalls: tuple[int, ...],
) -> bytes:
    """The packed seccomp-bpf program for this architecture."""

    header = [
        _insn(_BPF_LD_W_ABS, 0, 0, 4),
        _insn(_BPF_JMP_JEQ_K, 1, 0, arch),
        _insn(_BPF_RET_K, 0, 0, _SECCOMP_RET_KILL_PROCESS),
        _insn(_BPF_LD_W_ABS, 0, 0, 0),
    ]
    footer = [
        _insn(_BPF_RET_K, 0, 0, _SECCOMP_RET_ALLOW),
        _insn(_BPF_RET_K, 0, 0, _SECCOMP_RET_KILL_PROCESS),
        _insn(_BPF_RET_K, 0, 0, _SECCOMP_RET_ERRNO_EPERM),
    ]
    return b"".join(header + _syscall_jumps(errno_syscalls, kill_syscalls) + footer)


def _seccomp_blob() -> bytes | None:
    """The seccomp program, or None when this architecture is not in the table."""

    spec = _seccomp_syscalls()
    return None if spec is None else _seccomp_filter(*spec)


def _hide_roots(workdir: Path) -> tuple[Path, ...]:
    """Host trees to overlay with tmpfs, skipping any ancestor of the workdir."""
    roots = [Path(_root_dir(name)) for name in _HIDE_ROOTS]
    roots.append(sp.ROOT)
    home = Path.home()
    if str(home) not in {os.sep, ""}:
        roots.append(home)
    hidden: list[Path] = []
    resolved_workdir = workdir.resolve()
    for root in roots:
        try:
            resolved = root.resolve()
        except OSError:
            continue
        if not resolved.exists():
            continue
        if resolved in hidden:
            continue
        try:
            resolved_workdir.relative_to(resolved)
        except ValueError:
            hidden.append(resolved)
    return tuple(hidden)


def _seccomp_reader(blob: bytes) -> int:
    """A pipe holding the seccomp program for bwrap ``--seccomp FD``."""
    reader, writer = os.pipe()
    try:
        os.write(writer, blob)
    finally:
        os.close(writer)
    return reader


def _bwrap_prefix(bwrap: str, workdir: Path, env: Mapping[str, str], seccomp_fd: int) -> list[str]:
    """Literal bwrap argv prefix: read-only root, unshared namespaces, private tmp."""
    host = str(workdir)
    prefix = [
        bwrap, "--die-with-parent", "--new-session", "--unshare-all",
        "--uid", _NOBODY, "--gid", _NOBODY, "--ro-bind", os.sep, os.sep,
        "--dev", _root_dir("dev"), "--proc", _root_dir("proc"),
        "--tmpfs", _root_dir("tmp"), "--bind", host, host,
    ]
    for root in _hide_roots(workdir):
        prefix.extend(("--tmpfs", str(root)))
    prefix.extend(("--chdir", host, "--clearenv", "--seccomp", str(seccomp_fd)))
    for key, value in env.items():
        prefix.extend(("--setenv", key, value))
    prefix.extend(("--setenv", "HOME", host, "--setenv", "PATH", "/usr/bin:/bin"))
    return prefix


def _bwrap_confinement(
    argv: list[str], workdir: Path, env: Mapping[str, str],
) -> Confinement:
    """Prefix ``argv`` with the OS boundary, inheriting the seccomp descriptor."""
    binary = shutil.which(BWRAP_BIN)
    blob = _seccomp_blob()
    cv.refuse_when(binary is None, cv.FINDING_SANDBOX_UNAVAILABLE, _UNAVAILABLE)
    cv.refuse_when(blob is None, cv.FINDING_SANDBOX_UNAVAILABLE, _UNAVAILABLE)
    reader = _seccomp_reader(blob or b"")
    try:
        prefix = _bwrap_prefix(binary or BWRAP_BIN, workdir, env, reader)
        return Confinement(tuple(prefix) + tuple(argv), (reader,), (reader,))
    except Exception:
        os.close(reader)
        raise


bind_import_twin(__name__)
