#!/usr/bin/env python3
"""SAF mill commands: catalog-check and generate.

Exit codes: 0 on success, 2 on a coded refusal or usage error. ``--json``
prints one object so an agent never parses prose.
"""

from __future__ import annotations

import sys
from pathlib import Path

if __package__:
    from . import catalog as cat
    from . import generate as gen
    from ._contract import SafRefusal, bind_import_twin
else:
    _PIPELINES = Path(__file__).resolve().parents[1]
    if str(_PIPELINES) not in sys.path:
        sys.path.insert(0, str(_PIPELINES))
    from saf import catalog as cat
    from saf import generate as gen
    from saf._contract import SafRefusal, bind_import_twin

# ``python3 -m`` runs this module as ``__main__``, so the import form comes from ``__package__``.
if (__package__ or "").startswith("pipelines."):
    from ..catalog_cli import subcommands
else:
    from catalog_cli import subcommands

__all__ = ["build_parser", "run"]

_COMMANDS = subcommands.GenerateCommands(
    prog="saf.cli",
    description=__doc__,
    catalog=cat,
    generate=gen,
    refusal=SafRefusal,
    generate_help="safety-case pairs into a new directory",
    unit="pair",
)
build_parser = _COMMANDS.build_parser
run = _COMMANDS.run


def main() -> None:
    raise SystemExit(run())


if __name__ == "__main__":
    main()
elif __package__:
    bind_import_twin(__name__)
