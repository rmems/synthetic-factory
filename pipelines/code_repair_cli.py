#!/usr/bin/env python3
"""Argparse entry for the code-repair family (``pipelines/code_repair``).

Direct execution puts ``pipelines/`` on ``sys.path`` and imports the package
flat, the way every other pipeline CLI does; the package binds both import
spellings to one object.
"""

from __future__ import annotations

import sys
from pathlib import Path

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("code_repair_cli")
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "code_repair_cli"
    )

_PIPELINES = Path(__file__).resolve().parent
if str(_PIPELINES) not in sys.path:
    sys.path.insert(0, str(_PIPELINES))

from code_repair import cli  # noqa: E402

if __package__:
    _expose_package_sibling(__name__)


if __name__ == "__main__":
    sys.exit(cli.run())
