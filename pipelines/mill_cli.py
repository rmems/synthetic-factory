#!/usr/bin/env python3
"""Argparse entry for the mill family (``pipelines/mill``).

Direct execution puts ``pipelines/`` on ``sys.path`` and imports the package
flat, the way every other pipeline CLI does; the package binds both import
spellings to one object.
"""

from __future__ import annotations

import sys
from pathlib import Path

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("mill_cli")
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)("mill_cli")

_PIPELINES = Path(__file__).resolve().parent
if str(_PIPELINES) not in sys.path:
    sys.path.insert(0, str(_PIPELINES))

from mill import cli  # noqa: E402

if __package__:
    _expose_package_sibling(__name__)


if __name__ == "__main__":
    sys.exit(cli.run())
