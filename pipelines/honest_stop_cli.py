#!/usr/bin/env python3
"""Operator entry point for honest-stop episodes (see ``honest_stop/cli.py``)."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING or __package__:
    from .honest_stop import cli as _cli
else:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from honest_stop import cli as _cli

main = _cli.run

if __name__ == "__main__":
    sys.exit(main())
