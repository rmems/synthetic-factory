#!/usr/bin/env python3
"""Operator entry point for honest-stop episodes (see ``honest_stop/cli.py``)."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import TYPE_CHECKING

# Same split as ``tool_world_cli``: the finalizer import and its call share
# ``if __package__``, and type checkers take the package spelling on their own.
if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("honest_stop_cli")
    from .honest_stop import cli as _cli
elif TYPE_CHECKING:
    from .honest_stop import cli as _cli
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "honest_stop_cli"
    )
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from honest_stop import cli as _cli

main = _cli.run

if __package__:
    _expose_package_sibling(__name__)


if __name__ == "__main__":
    sys.exit(main())
