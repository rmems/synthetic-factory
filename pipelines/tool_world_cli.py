#!/usr/bin/env python3
"""Operator entry point for the tool-world families (see ``tool_world/cli.py``)."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import TYPE_CHECKING

# Type checkers read the package spelling; at run time TYPE_CHECKING is False.
# The finalizer is imported under ``if __package__`` alone. Importing it under
# ``TYPE_CHECKING or __package__`` and calling it under a later ``if __package__``
# is the same path at run time, but pylint reports E0601 because it will not
# relate the two conditions.
if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("tool_world_cli")
    from .tool_world import cli as _cli
elif TYPE_CHECKING:
    from .tool_world import cli as _cli
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "tool_world_cli"
    )
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from tool_world import cli as _cli

main = _cli.run

if __package__:
    _expose_package_sibling(__name__)


if __name__ == "__main__":
    sys.exit(main())
