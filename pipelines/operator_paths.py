#!/usr/bin/env python3
"""Operator-supplied paths, confined to the trees the operator runs in.

A CLI reads and writes only under the working directory, the home directory or
the temp directory (SonarCloud S8707): a path is resolved with ``realpath`` and
refused unless one of those roots is a prefix of it.

Confine at the CLI boundary, in the flow right after ``parse_args``, and never
as an argparse ``type=`` converter -- Sonar's taint engine does not model
converters, which is why #203 moved the calls out of the parser. Internal APIs
keep taking an unresolved ``Path``: several pipelines reject symlinked
components lexically, and handing them a pre-resolved path would make those
guards vacuous.
"""

from __future__ import annotations

import argparse
import os
import sys
import tempfile
from pathlib import Path

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("operator_paths")
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "operator_paths"
    )


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


if __package__:
    _expose_package_sibling(__name__)
