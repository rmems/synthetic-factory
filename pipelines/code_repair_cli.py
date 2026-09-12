#!/usr/bin/env python3
"""Argparse entry for the code-repair family (``pipelines/code_repair``).

Direct execution puts ``pipelines/`` on ``sys.path`` and imports the package
flat, the way every other pipeline CLI does; the package binds both import
spellings to one object.
"""

from __future__ import annotations

import sys
from pathlib import Path

_PIPELINES = Path(__file__).resolve().parent
if str(_PIPELINES) not in sys.path:
    sys.path.insert(0, str(_PIPELINES))

from code_repair import cli  # noqa: E402

if __name__ == "__main__":
    sys.exit(cli.run())
