#!/usr/bin/env python3
"""Operator entry point for honest-stop episodes (see ``honest_stop/cli.py``)."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import TYPE_CHECKING

# Type checkers take the package spelling. The finalizer import stays on
# ``if __package__`` so pylint can see the later call is assigned.
if TYPE_CHECKING:
    from .honest_stop import cli as _cli
if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("honest_stop_cli")
    from .honest_stop import cli as _cli
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "honest_stop_cli"
    )
    parent = str(Path(__file__).resolve().parent)
    if parent not in sys.path:
        sys.path.insert(0, parent)
    from honest_stop import cli as _cli


def main() -> int:
    """Run the honest-stop CLI."""

    return _cli.run()


if __package__:
    _expose_package_sibling(__name__)


if __name__ == "__main__":
    sys.exit(main())
