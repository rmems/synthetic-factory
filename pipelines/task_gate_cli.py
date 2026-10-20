#!/usr/bin/env python3
"""Argparse entry for the task-verification gate (``pipelines/task_gate``, #496).

Direct execution puts ``pipelines/`` on ``sys.path`` and imports the package flat, the way
every other pipeline CLI does; the package binds both import spellings to one object.
"""

from __future__ import annotations

import importlib
import sys
from pathlib import Path


def main() -> int:
    pipelines = str(Path(__file__).resolve().parent)
    if pipelines not in sys.path:
        sys.path.insert(0, pipelines)
    return importlib.import_module("task_gate.cli").run()


if __name__ == "__main__":
    sys.exit(main())
