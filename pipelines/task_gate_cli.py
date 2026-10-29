#!/usr/bin/env python3
"""Argparse entry for the task-verification gate (``pipelines/task_gate``, #496).

Direct execution puts ``pipelines/`` on ``sys.path`` and imports the package flat, the way
every other pipeline CLI does; the package binds both import spellings to one object.
"""

from __future__ import annotations

import importlib
import sys
from pathlib import Path

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("task_gate_cli")
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "task_gate_cli"
    )


def main() -> int:
    pipelines = str(Path(__file__).resolve().parent)
    if pipelines not in sys.path:
        sys.path.insert(0, pipelines)
    return importlib.import_module("task_gate.cli").run()


if __package__:
    _expose_package_sibling(__name__)


if __name__ == "__main__":
    sys.exit(main())
