#!/usr/bin/env python3
"""MAOS commands: catalog, catalog-check, and generate.

Read-only catalog listing, plus optional JSONL generation into a brand-new
destination. This command does not reserve or publish a raw round. Exit 0
on success, 2 on a coded refusal or usage error.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from . import _contract, generate
from . import catalog as cat

# ``python3 -m`` runs this module as ``__main__``, so the import form comes from ``__package__``;
# type checkers follow the package form.
if TYPE_CHECKING or __package__.startswith("pipelines."):
    from ..family_cli import runner
else:
    from family_cli import runner

__all__ = ["build_parser", "run"]


def _plant_line(plant: Any) -> str:
    return f"{plant.source_round:2d} {plant.record_id} {plant.scenario}"


_COMMANDS = runner.PlantCatalogCommands(
    prog="maos",
    description=__doc__,
    family=runner.PlantFamily(_contract, cat, generate, generate.record),
    helps=(
        "print the recovered MAOS plant catalog",
        "fail closed unless the first slice is intact",
        "emit one identity (never raw, never publish)",
    ),
    plant_line=_plant_line,
    check_line="catalog-check ok: {plants} plants r{first_round}-r{last_round}",
)
build_parser = _COMMANDS.build_parser
run = _COMMANDS.run
main = _COMMANDS.main


_contract.bind_import_twin(__name__)


if __name__ == "__main__":
    main()
