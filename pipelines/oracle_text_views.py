"""Operator entry point for the oracle-grounded text views (see ``oracle_views/cli.py``)."""

from __future__ import annotations

import sys
from pathlib import Path

if __package__:
    from .oracle_views import cli as _cli
else:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from oracle_views import cli as _cli

main = _cli.main

if __name__ == "__main__":
    sys.exit(main())
