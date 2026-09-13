#!/usr/bin/env python3
"""Operator-supplied paths for the code-repair scripts, confined to where the operator runs.

The scripts read and write only under the working directory, the home directory or the
temp directory (SonarCloud S8707): a path is resolved with ``realpath`` and refused unless
one of those roots is a prefix of it.
"""

from __future__ import annotations

import argparse
import os
import tempfile
from pathlib import Path


def operator_roots() -> tuple[str, ...]:
    return tuple(
        os.path.realpath(root) for root in (os.getcwd(), Path.home(), tempfile.gettempdir())
    )


def operator_path(value: str) -> Path:
    """The resolved path, or an argparse error when it lies outside every operator root."""

    resolved = os.path.realpath(value)
    for root in operator_roots():
        if resolved == root or resolved.startswith(root.rstrip(os.sep) + os.sep):
            return Path(resolved)
    raise argparse.ArgumentTypeError("the path lies outside the working, home and temp trees")
