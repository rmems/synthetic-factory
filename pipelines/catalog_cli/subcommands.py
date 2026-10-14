"""The two subcommand shapes behind the catalog-backed mill packages' ``cli`` modules.

Each shape was copied verbatim into every package that uses it.
``catalog_cli.entry`` now binds ``prog``, the refusal class, and the package's
``catalog`` / ``generate`` modules. Generate-shape ``--help`` text is one
shared docstring; extract-shape CLIs keep their own.

* :class:`GenerateCommands` (``flk``, ``gql``, ``msd``, ``rag``, ``saf``):
  ``catalog-check`` over a pinned plant catalog directory, exit 1 when it
  reports findings, and ``generate`` into a new directory. A coded refusal
  prints one compact exact-JSON object under ``--json`` or its prose on
  stderr; any other exception propagates.
* :class:`ExtractCommands` (``mac``, ``sbox``): ``catalog-check`` of the
  package's committed catalog and an AST ``extract`` from mill source text. A
  refusal prints ``json.dumps`` output, and any other exception is reported
  as ``status: error`` instead of a traceback.

Both exit 2 on a refusal or usage error and print success as one indented
exact-JSON object (``--json``) or one prose line.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType
from typing import Any

if __name__.startswith("pipelines."):
    from ..exact_json import dumps_exact_json
    from ..oracle_grounded.import_twins import bind_import_twin
else:
    from exact_json import dumps_exact_json
    from oracle_grounded.import_twins import bind_import_twin

__all__ = ["ExtractCommands", "GenerateCommands", "bind_import_twin"]

_Encode = Callable[[dict[str, Any]], str]


def _command_parser(
    prog: str, description: str | None
) -> tuple[argparse.ArgumentParser, Any]:
    parser = argparse.ArgumentParser(prog=prog, description=description)
    return parser, parser.add_subparsers(dest="command", required=True)


def _emit(payload: dict[str, Any], as_json: bool, text: str) -> None:
    if as_json:
        rendered = dumps_exact_json(payload, ensure_ascii=True, indent=2, sort_keys=True)
    else:
        rendered = text
    print(rendered)


def _exact_line(payload: dict[str, Any]) -> str:
    return dumps_exact_json(payload, ensure_ascii=True, sort_keys=True)


def _stdlib_line(payload: dict[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True)


def _report(args: argparse.Namespace, fields: dict[str, Any], line: str, encode: _Encode) -> int:
    """Print the failure as one ``encode``d object under ``--json``, else ``line`` on stderr."""

    if getattr(args, "json", False):
        print(encode({"command": args.command, **fields}))
    else:
        print(line, file=sys.stderr)
    return 2


@dataclass(frozen=True)
class GenerateCommands:
    """``catalog-check`` and ``generate`` over a pinned plant catalog directory."""

    prog: str
    description: str | None
    catalog: ModuleType
    generate: ModuleType
    refusal: type[Exception]
    generate_help: str = "success/handoff pairs into a new directory"
    unit: str = "plant"

    def build_parser(self) -> argparse.ArgumentParser:
        """``catalog-check`` and ``generate``. The description is the package CLI docstring."""

        parser, commands = _command_parser(self.prog, self.description)

        check = commands.add_parser("catalog-check", help="load the pinned catalog and verify pins")
        check.add_argument("--catalog", type=Path, default=None)
        check.add_argument("--json", action="store_true")

        gen_cmd = commands.add_parser("generate", help=self.generate_help)
        gen_cmd.add_argument("--catalog", type=Path, default=None)
        gen_cmd.add_argument("--out", type=Path, required=True)
        gen_cmd.add_argument("--plant", default=None, help="exact plant_id (mill_id:slug)")
        gen_cmd.add_argument("--mill", default=None, help=f"one mill_id, every {self.unit} in order")
        gen_cmd.add_argument("--all", action="store_true", help=f"every {self.unit} in the catalog")
        gen_cmd.add_argument("--round", type=int, default=None, help="id round; only with --plant")
        gen_cmd.add_argument("--json", action="store_true")
        return parser

    def run(self, argv: list[str] | None = None) -> int:
        """Parse ``argv`` (or ``sys.argv``) and return the process exit code."""

        parser = self.build_parser()
        args = parser.parse_args(argv)
        try:
            if args.command == "catalog-check":
                return self._catalog_check(args)
            if args.command == "generate":
                return self._generate(args)
        except self.refusal as refusal:
            return self._refused(args, refusal)
        return 2

    @staticmethod
    def _refused(args: argparse.Namespace, refusal: Exception) -> int:
        """A refusal without ``code`` reports ``null``, as the package CLIs did."""

        fields = {
            "status": "refused",
            "code": getattr(refusal, "code", None),
            "message": str(refusal),
        }
        return _report(args, fields, str(refusal), _exact_line)

    def _catalog_dir(self, args: argparse.Namespace) -> Path:
        if args.catalog is not None:
            return Path(args.catalog)
        return self.catalog.default_catalog_dir()

    def _catalog_check(self, args: argparse.Namespace) -> int:
        directory = self._catalog_dir(args)
        findings = self.catalog.catalog_check(directory)
        loaded = self.catalog.load_catalog(directory)
        status = "findings" if findings else "ok"
        text = (
            f"catalog-check {status}: {loaded.catalog_id} "
            f"{len(loaded.plants)} plants / {len(loaded.mills)} mills"
        )
        _emit(
            {
                "command": "catalog-check",
                "status": status,
                "catalog_id": loaded.catalog_id,
                "plants": len(loaded.plants),
                "mills": len(loaded.mills),
                "findings": findings,
            },
            args.json,
            text,
        )
        return 1 if findings else 0

    def _generate(self, args: argparse.Namespace) -> int:
        summary = self.generate.run(
            self.generate.GenerateRequest(
                catalog_dir=self._catalog_dir(args),
                out_dir=args.out,
                plant_id=args.plant,
                mill_id=args.mill,
                all_plants=args.all,
                round=args.round,
            )
        )
        text = (
            f"generated {summary['records']} records "
            f"({summary['pairs']} pairs) into {args.out}"
        )
        _emit({"command": "generate", "status": "ok", "summary": summary}, args.json, text)
        return 0


@dataclass(frozen=True)
class ExtractCommands:
    """``catalog-check`` of the committed catalog and an AST ``extract`` (never exec)."""

    prog: str
    description: str | None
    catalog: ModuleType
    generate: ModuleType
    refusal: type[Exception]

    def build_parser(self) -> argparse.ArgumentParser:
        """``catalog-check`` and ``extract``. The description is the package CLI docstring."""

        parser, commands = _command_parser(self.prog, self.description)

        check = commands.add_parser(
            "catalog-check",
            help="pins, uniqueness, and extract counts hold",
        )
        check.add_argument("--json", action="store_true")

        extract = commands.add_parser(
            "extract",
            help="AST-extract catalog identity from mill source text (never exec)",
        )
        extract.add_argument("--source", type=Path, required=True)
        extract.add_argument("--json", action="store_true")
        return parser

    def run(self, argv: list[str] | None = None) -> int:
        """Parse ``argv`` (or ``sys.argv``) and return the process exit code."""

        args = self.build_parser().parse_args(argv)
        handlers = {"catalog-check": self._catalog_check, "extract": self._extract}
        try:
            return handlers[args.command](args)
        except self.refusal as refusal:
            return self._refused(args, refusal)
        except Exception as exc:
            message = f"{type(exc).__name__}: {exc}"
            return _report(args, {"status": "error", "message": message}, message, _stdlib_line)

    @staticmethod
    def _refused(args: argparse.Namespace, refusal: Exception) -> int:
        """A bare ``ContractError`` has no ``code``; it reports ``null``."""

        fields = {
            "status": "refused",
            "code": getattr(refusal, "code", None),
            "message": str(refusal),
        }
        return _report(args, fields, str(refusal), _stdlib_line)

    def _catalog_check(self, args: argparse.Namespace) -> int:
        report = self.catalog.catalog_check()
        text = (
            f"catalog-check ok: {report['plants']} plants / "
            f"{report['sources']} sources / {report['full_row_count']} full rows"
        )
        _emit({"command": "catalog-check", **report}, args.json, text)
        return 0

    def _extract(self, args: argparse.Namespace) -> int:
        plants = self.generate.plants_from_source(args.source.read_text(encoding="utf-8"))
        text = f"extract ok: {len(plants)} plants from {args.source.name}"
        _emit(
            {
                "command": "extract",
                "status": "ok",
                "source": str(args.source),
                "plants": list(plants),
            },
            args.json,
            text,
        )
        return 0


bind_import_twin(__name__)
