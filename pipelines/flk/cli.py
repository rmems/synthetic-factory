#!/usr/bin/env python3
"""FLK mill commands: catalog-check and generate.

Exit codes: 0 on success, 2 on a coded refusal or usage error. ``--json``
prints one object so an agent never parses prose.
"""

from __future__ import annotations

import sys
from pathlib import Path

if __package__:
    from . import _contract, catalog, generate
else:
    _PIPELINES = Path(__file__).resolve().parents[1]
    if str(_PIPELINES) not in sys.path:
        sys.path.insert(0, str(_PIPELINES))
    from flk import _contract, catalog, generate

# ``python3 -m`` runs this module as ``__main__``, so the import form comes from ``__package__``.
if (__package__ or "").startswith("pipelines."):
    from ..catalog_cli import subcommands
else:
    from catalog_cli import subcommands

__all__ = ["build_parser", "run"]

_COMMANDS = subcommands.GenerateCommands(
    prog="flk.cli",
    description=__doc__,
    catalog=catalog,
    generate=generate,
    refusal=_contract.FlkRefusal,
)
build_parser = _COMMANDS.build_parser
run = _COMMANDS.run


def main() -> None:
    raise SystemExit(run())


if __name__ == "__main__":
    main()
elif __package__:
    _contract.bind_import_twin(__name__)
