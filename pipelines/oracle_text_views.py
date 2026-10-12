"""Operator entry point for the oracle-grounded text views (see ``oracle_views/cli.py``)."""

from __future__ import annotations

import sys
from pathlib import Path

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("oracle_text_views")
    from .oracle_views import cli as _cli
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "oracle_text_views"
    )
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from oracle_views import cli as _cli

main = _cli.main

if __package__:
    _expose_package_sibling(__name__)

if __name__ == "__main__":
    sys.exit(main())
