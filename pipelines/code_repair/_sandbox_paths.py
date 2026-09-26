#!/usr/bin/env python3
"""Path allowlist helpers for the Landlock child.

Copied next to ``_sandbox.py``. Imports nothing of the factory package.
"""

from __future__ import annotations

import os
import sys
import sysconfig

DEV_NODES = ("/dev/null", "/dev/zero", "/dev/urandom", "/dev/random")
SYSTEM_LIB_ROOTS = ("/lib", "/lib64", "/usr/lib", "/usr/lib64")
HOST_CANARIES = ("/etc/passwd", "/etc/hosts", "/proc/1/environ")

__all__ = [
    "DEV_NODES", "HOST_CANARIES", "SYSTEM_LIB_ROOTS",
    "beneath", "open_allowed", "read_roots", "runtime_prefixes",
]


def runtime_prefixes() -> set[str]:
    """Exact interpreter executable and Python library roots for this layout."""

    layout = sysconfig.get_paths()
    paths = {sys.executable}
    paths.update(
        layout.get(name)
        for name in ("stdlib", "platstdlib", "purelib", "platlib")
    )
    return {
        resolved
        for path in paths
        if path and (resolved := os.path.realpath(path)) != "/" and os.path.exists(resolved)
    }


def read_roots() -> set[str]:
    """Exact interpreter paths plus fixed system library roots; never ``/``."""

    roots = set(runtime_prefixes())
    for root in SYSTEM_LIB_ROOTS:
        if os.path.isdir(root):
            resolved = os.path.realpath(root)
            if resolved and resolved != "/":
                roots.add(resolved)
    return roots


def beneath(path: str, root: str) -> bool:
    root = os.path.realpath(root)
    path = os.path.realpath(path)
    return path == root or path.startswith(root.rstrip("/") + "/")


def open_allowed(path: str, allowed: set[str]) -> int | None:
    """Open ``path`` only when it is a device node or sits under an allowed root."""

    resolved = os.path.realpath(path)
    if resolved not in DEV_NODES and not any(beneath(resolved, root) for root in allowed):
        return None
    return os.open(resolved, os.O_PATH | os.O_CLOEXEC)
