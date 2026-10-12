#!/usr/bin/env python3
"""SBOX commands: catalog-check and AST extract.

Read-only. This command does not reserve or publish a raw round and does
not write mill scripts. Exit 0 on success, 2 on a coded refusal or usage
error. ``--json`` prints one object so an agent never parses prose.
"""

from __future__ import annotations

from . import catalog as cat
from . import generate
from ._contract import bind_import_twin, envelope

# ``python3 -m`` runs this module as ``__main__``, so the import form comes from ``__package__``.
if (__package__ or "").startswith("pipelines."):
    from ..catalog_cli import subcommands
else:
    from catalog_cli import subcommands

__all__ = ["build_parser", "run"]

_COMMANDS = subcommands.ExtractCommands(
    prog="sbox.cli",
    description=__doc__,
    catalog=cat,
    generate=generate,
    refusal=envelope.ContractError,
)
build_parser = _COMMANDS.build_parser
run = _COMMANDS.run


bind_import_twin(__name__)


if __name__ == "__main__":
    raise SystemExit(run())
