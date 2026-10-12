#!/usr/bin/env python3
"""Operator entry point for the tool-world families (see ``tool_world/cli.py``)."""

from __future__ import annotations

import sys
from pathlib import Path

if __package__:
    from .tool_world import cli as _cli
else:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from tool_world import cli as _cli

main = _cli.run

if __name__ == "__main__":
    sys.exit(main())
