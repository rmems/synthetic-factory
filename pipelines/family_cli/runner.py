"""Subcommand dispatch, exit codes and output for the plant-family ``cli`` modules.

:func:`run_commands` parses argv, calls the handler its subcommand names, and
decides the exit code in one place: 0 once the handler returns, 2 when it
raises a coded ``ContractError`` (argparse already exits 2 on a usage error).
Handlers print their own output and return nothing.

:class:`PlantCatalogCommands` is the ``catalog`` / ``catalog-check`` /
``generate`` command set of the nelb, maos, pkg and ffpc families: a read-only
catalog listing, a fail-closed catalog check, and one round of JSONL
generation, printed or written into a brand-new destination. It never
reserves or publishes a raw round. A family's ``cli`` supplies only what
differs: its ``prog`` and docstring, the help lines, how it prints a plant and
a catalog-check report, and the generator that renders one plant's record.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from pathlib import Path
from types import ModuleType
from typing import TYPE_CHECKING, Any

# Type checkers follow the package form.
if TYPE_CHECKING or __name__.startswith("pipelines."):
    from ..exact_json import dumps_exact_json
    from ..oracle_grounded import envelope
    from ..oracle_grounded.import_twins import bind_import_twin
else:
    from exact_json import dumps_exact_json
    from oracle_grounded import envelope
    from oracle_grounded.import_twins import bind_import_twin

__all__ = [
    "EXIT_OK",
    "EXIT_REFUSED",
    "PlantCatalogCommands",
    "PlantFamily",
    "bind_import_twin",
    "run_commands",
]

EXIT_OK = 0
EXIT_REFUSED = 2

Handler = Callable[[argparse.Namespace], None]

_CATALOG_COMMANDS = ("catalog", "catalog-check", "generate")
_OUT_HELP = "new destination; omit to print JSONL"


def _report_refusal(
    args: argparse.Namespace, refusal: envelope.ContractError, as_json: bool
) -> None:
    """Print a refusal as one compact JSON object on stdout, else its prose on stderr."""

    if as_json:
        payload = {
            "command": args.command,
            "status": "refused",
            "code": getattr(refusal, "code", None),
            "message": str(refusal),
        }
        print(json.dumps(payload, sort_keys=True))
    else:
        print(str(refusal), file=sys.stderr)


def run_commands(
    parser: argparse.ArgumentParser,
    handlers: Mapping[str, Handler],
    argv: list[str] | None = None,
    *,
    json_refusals: bool = True,
) -> int:
    """Parse ``argv``, run the named handler, and return the exit code.

    A refusal is reported as JSON when ``json_refusals`` is set and the
    command was given ``--json``; otherwise its prose goes to stderr.
    """

    args = parser.parse_args(argv)
    try:
        handlers[args.command](args)
    except envelope.ContractError as refusal:
        _report_refusal(args, refusal, json_refusals and getattr(args, "json", False))
        return EXIT_REFUSED
    return EXIT_OK


def _emit(payload: dict[str, Any], as_json: bool, text: str) -> None:
    print(dumps_exact_json(payload, ensure_ascii=True, indent=2, sort_keys=True) if as_json else text)


@dataclass(frozen=True)
class PlantFamily:
    """One family's ``_contract``, ``catalog`` and ``generate`` modules.

    ``record`` renders one plant as its JSONL record. The catalog listing
    names the family by its contract's source pin, prefix and factory, plus
    ``extra_identity`` where the family pins more (nelb's source slice).
    """

    contract: ModuleType
    catalog: ModuleType
    generate: ModuleType
    record: Callable[[Any], dict[str, Any]]
    extra_identity: Mapping[str, Any] = field(default_factory=dict)

    def identity(self) -> dict[str, Any]:
        return {
            "source_ref": self.contract.SOURCE_REF,
            "source_commit": self.contract.SOURCE_COMMIT,
            "family_prefix": self.contract.FAMILY_PREFIX,
            "factory": self.contract.FACTORY,
            **self.extra_identity,
        }


@dataclass(frozen=True)
class PlantCatalogCommands:
    """``catalog``, ``catalog-check`` and ``generate --round`` for one plant family.

    ``helps`` gives the three subcommands' help lines in that order;
    ``plant_line`` prints one plant of the text listing, and ``check_line`` is
    a :meth:`str.format_map` template over the catalog-check report.
    """

    prog: str
    description: str | None
    family: PlantFamily
    helps: tuple[str, str, str]
    plant_line: Callable[[Any], str]
    check_line: str

    def build_parser(self) -> argparse.ArgumentParser:
        parser = argparse.ArgumentParser(prog=self.prog, description=self.description)
        commands = parser.add_subparsers(dest="command", required=True)
        subparsers = [
            commands.add_parser(name, help=help_text)
            for name, help_text in zip(_CATALOG_COMMANDS, self.helps, strict=True)
        ]
        subparsers[-1].add_argument("--round", type=int, required=True)
        subparsers[-1].add_argument("--out", type=Path, default=None, help=_OUT_HELP)
        for subparser in subparsers:
            subparser.add_argument("--json", action="store_true")
        return parser

    def run(self, argv: list[str] | None = None) -> int:
        handlers = dict(
            zip(_CATALOG_COMMANDS, (self._catalog, self._catalog_check, self._generate), strict=True)
        )
        return run_commands(self.build_parser(), handlers, argv)

    def main(self) -> None:
        raise SystemExit(self.run())

    def _catalog(self, args: argparse.Namespace) -> None:
        loaded = self.family.catalog.load_catalog()
        if args.json:
            payload = {
                "command": "catalog",
                **self.family.identity(),
                "catalog_id": loaded.catalog_id,
                "plants": [plant.as_mapping() for plant in loaded.plants],
            }
            print(dumps_exact_json(payload, indent=2))
            return
        print(f"{loaded.catalog_id} {self.family.contract.FACTORY} {len(loaded.plants)} plants")
        for plant in loaded.plants:
            print(self.plant_line(plant))

    def _catalog_check(self, args: argparse.Namespace) -> None:
        report = self.family.catalog.catalog_check()
        text = self.check_line.format_map(report)
        _emit({"command": "catalog-check", **report}, args.json, text)

    def _generate(self, args: argparse.Namespace) -> None:
        if args.out is None:
            for plant in self.family.catalog.plants_for_round(args.round):
                print(dumps_exact_json(self.family.record(plant), sort_keys=False))
            return
        generator = self.family.generate
        summary = generator.run(generator.RunRequest(args.round, args.out))
        text = f"generated {summary['records']} records into {args.out}"
        _emit({"command": "generate", "status": "ok", "summary": summary}, args.json, text)


bind_import_twin(__name__)
