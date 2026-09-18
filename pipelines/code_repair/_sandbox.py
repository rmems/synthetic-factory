#!/usr/bin/env python3
"""Landlock allowlist for the code-repair child.

The parent still confines with ``bwrap-ro-netns-v1``. This module then denies
host paths the read-only root bind still exposes. It imports nothing of the
factory package: the executor copies it next to ``_harness.py``.
"""

from __future__ import annotations

import ctypes
import os
import sys

MECHANISM = "landlock"
MIN_ABI = 3
LANDLOCK_SYSCALLS = {"x86_64": (444, 445, 446), "aarch64": (444, 445, 446)}
LANDLOCK_CREATE_RULESET_VERSION = 1 << 0
LANDLOCK_RULE_PATH_BENEATH = 1
PR_SET_NO_NEW_PRIVS = 38
FS_EXECUTE = 1 << 0
FS_WRITE_FILE = 1 << 1
FS_READ_FILE = 1 << 2
FS_READ_DIR = 1 << 3
FS_REMOVE_DIR = 1 << 4
FS_REMOVE_FILE = 1 << 5
FS_MAKE_CHAR = 1 << 6
FS_MAKE_DIR = 1 << 7
FS_MAKE_REG = 1 << 8
FS_MAKE_SOCK = 1 << 9
FS_MAKE_FIFO = 1 << 10
FS_MAKE_BLOCK = 1 << 11
FS_MAKE_SYM = 1 << 12
FS_REFER = 1 << 13
FS_TRUNCATE = 1 << 14
FS_IOCTL_DEV = 1 << 15
NET_BIND_TCP = 1 << 0
NET_CONNECT_TCP = 1 << 1
SCOPE_ABSTRACT_UNIX_SOCKET = 1 << 0
FS_ABI1 = (
    FS_EXECUTE | FS_WRITE_FILE | FS_READ_FILE | FS_READ_DIR | FS_REMOVE_DIR | FS_REMOVE_FILE
    | FS_MAKE_CHAR | FS_MAKE_DIR | FS_MAKE_REG | FS_MAKE_SOCK | FS_MAKE_FIFO | FS_MAKE_BLOCK
    | FS_MAKE_SYM
)
RO_ACCESS = FS_EXECUTE | FS_READ_FILE | FS_READ_DIR
RW_ACCESS = (
    FS_EXECUTE | FS_WRITE_FILE | FS_READ_FILE | FS_READ_DIR | FS_REMOVE_DIR | FS_REMOVE_FILE
    | FS_MAKE_DIR | FS_MAKE_REG | FS_MAKE_SYM
)
DEV_NODES = ("/dev/null", "/dev/zero", "/dev/urandom", "/dev/random")
SYSTEM_LIB_ROOTS = ("/lib", "/lib64", "/usr/lib", "/usr/lib64")
HOST_CANARIES = ("/etc/passwd", "/etc/hosts", "/proc/1/environ")

__all__ = ["MECHANISM", "MIN_ABI", "applied", "apply", "available", "token_for"]


class _RulesetAttr(ctypes.Structure):
    _fields_ = [
        ("handled_access_fs", ctypes.c_uint64),
        ("handled_access_net", ctypes.c_uint64),
        ("scoped", ctypes.c_uint64),
    ]


class _PathBeneath(ctypes.Structure):
    _fields_ = [("allowed_access", ctypes.c_uint64), ("parent_fd", ctypes.c_int32)]


def token_for(abi: int) -> str:
    return f"{MECHANISM}-abi{abi}"


def applied(token: object) -> bool:
    prefix = MECHANISM + "-abi"
    if not isinstance(token, str) or not token.startswith(prefix):
        return False
    suffix = token[len(prefix):]
    return suffix.isdigit() and int(suffix) >= MIN_ABI


def available() -> bool:
    """True when this kernel reports a Landlock ABI that mediates truncate."""

    try:
        abi = _landlock_abi()
    except (OSError, ValueError, AttributeError):
        return False
    return abi is not None and abi >= MIN_ABI


def apply(workdir: str) -> str | None:
    """Restrict this process, or return None when Landlock cannot be applied."""

    try:
        return _apply(os.path.realpath(workdir))
    except (OSError, ValueError, AttributeError):
        return None


def _apply(workdir: str) -> str | None:
    abi = _landlock_abi()
    if abi is None or abi < MIN_ABI:
        return None
    if not _restrict_filesystem(workdir, abi):
        return None
    if not _host_paths_are_closed(workdir):
        return None
    return token_for(abi)


def _libc():
    libc = ctypes.CDLL(None, use_errno=True)
    libc.syscall.restype = ctypes.c_long
    libc.prctl.restype = ctypes.c_int
    return libc


def _landlock_abi() -> int | None:
    numbers = LANDLOCK_SYSCALLS.get(os.uname().machine)
    if numbers is None:
        return None
    version = int(_libc().syscall(
        numbers[0], None, ctypes.c_size_t(0), LANDLOCK_CREATE_RULESET_VERSION,
    ))
    return version if version >= 1 else None


def _handled_rights(abi: int) -> tuple[int, int, int, int]:
    handled_fs = FS_ABI1 | FS_REFER | FS_TRUNCATE
    if abi >= 5:
        handled_fs |= FS_IOCTL_DEV
    handled_net = (NET_BIND_TCP | NET_CONNECT_TCP) if abi >= 4 else 0
    scoped = SCOPE_ABSTRACT_UNIX_SOCKET if abi >= 6 else 0
    size = 8 + (8 if abi >= 4 else 0) + (8 if abi >= 6 else 0)
    return handled_fs, handled_net, scoped, size


def _open_ruleset(abi: int) -> tuple[object, int, tuple[int, int, int]] | None:
    numbers = LANDLOCK_SYSCALLS.get(os.uname().machine)
    if numbers is None:
        return None
    libc = _libc()
    handled_fs, handled_net, scoped, size = _handled_rights(abi)
    attr = _RulesetAttr(handled_fs, handled_net, scoped)
    ruleset = int(libc.syscall(numbers[0], ctypes.byref(attr), ctypes.c_size_t(size), 0))
    if ruleset < 0:
        return None
    return libc, ruleset, numbers


def _runtime_prefixes() -> set[str]:
    prefixes = {
        os.path.realpath(path)
        for path in (
            sys.prefix, sys.base_prefix, sys.exec_prefix, sys.base_exec_prefix, sys.executable,
        )
        if path
    }
    resolved = {path if os.path.isdir(path) else os.path.dirname(path) for path in prefixes}
    return {path for path in resolved if path and path != "/"}


def _read_roots() -> set[str]:
    """Interpreter prefixes plus fixed system library roots; never ``/``."""

    roots = set(_runtime_prefixes())
    for root in SYSTEM_LIB_ROOTS:
        if os.path.isdir(root):
            resolved = os.path.realpath(root)
            if resolved and resolved != "/":
                roots.add(resolved)
    return roots


class _ActiveRuleset:
    libc = None
    fd = 0
    add_rule = 0
    restrict = 0
    handled_fs = 0
    ioctl = 0


def _bind_ruleset(opened, abi: int) -> _ActiveRuleset:
    libc, ruleset, numbers = opened
    active = _ActiveRuleset()
    active.libc = libc
    active.fd = ruleset
    active.add_rule = numbers[1]
    active.restrict = numbers[2]
    active.handled_fs = _handled_rights(abi)[0]
    active.ioctl = FS_IOCTL_DEV if abi >= 5 else 0
    return active


def _open_allowed(path: str, allowed: set[str]) -> int | None:
    """Open ``path`` only when it is a device node or sits under an allowed root."""

    resolved = os.path.realpath(path)
    if resolved not in DEV_NODES and not any(_beneath(resolved, root) for root in allowed):
        return None
    return os.open(resolved, os.O_PATH | os.O_CLOEXEC)


def _add_path(active: _ActiveRuleset, path: str, access: int, allowed: set[str]) -> bool:
    fd = _open_allowed(path, allowed)
    if fd is None:
        return False
    try:
        attr = _PathBeneath(access, fd)
        rule = active.libc.syscall(
            active.add_rule, active.fd, LANDLOCK_RULE_PATH_BENEATH, ctypes.byref(attr), 0,
        )
        return int(rule) == 0
    finally:
        os.close(fd)


def _allow_roots(active: _ActiveRuleset, workdir: str) -> bool:
    ro = (RO_ACCESS | FS_REFER) & active.handled_fs
    rw = (RW_ACCESS | FS_REFER | FS_TRUNCATE) & active.handled_fs
    work = {os.path.realpath(workdir)}
    if not _add_path(active, workdir, rw, work):
        return False
    for prefix in _read_roots():
        if not os.path.isdir(prefix) or not _add_path(active, prefix, ro, {prefix}):
            return False
    return True


def _allow_devices(active: _ActiveRuleset) -> bool:
    access = FS_READ_FILE | active.ioctl
    for node in DEV_NODES:
        if os.path.exists(node) and not _add_path(active, node, access, set(DEV_NODES)):
            return False
    return True


def _restrict_filesystem(workdir: str, abi: int) -> bool:
    opened = _open_ruleset(abi)
    if opened is None:
        return False
    active = _bind_ruleset(opened, abi)
    try:
        if not _allow_roots(active, workdir) or not _allow_devices(active):
            return False
        if active.libc.prctl(PR_SET_NO_NEW_PRIVS, 1, 0, 0, 0) != 0:
            return False
        return int(active.libc.syscall(active.restrict, active.fd, 0)) == 0
    finally:
        os.close(active.fd)


def _beneath(path: str, root: str) -> bool:
    root = os.path.realpath(root)
    path = os.path.realpath(path)
    return path == root or path.startswith(root.rstrip("/") + "/")


def _host_paths_are_closed(workdir: str) -> bool:
    """True when host files cannot be read; ``stat`` is not a Landlock denial."""

    denied = False
    for path in HOST_CANARIES:
        if not os.path.lexists(path):
            continue
        try:
            with open(path, "rb") as handle:
                handle.read(1)
            return False
        except OSError:
            denied = True
    if not os.path.isdir(workdir) or not os.access(workdir, os.R_OK | os.W_OK):
        return False
    return denied
