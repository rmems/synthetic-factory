#!/usr/bin/env python3
"""MAC commands: catalog-check and AST extract.

Read-only. This command does not reserve or publish a raw round and does
not write mill scripts. Exit 0 on success, 2 on a coded refusal or usage
error. ``--json`` prints one object so an agent never parses prose.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from . import catalog as cat
from . import generate
from ._contract import bind_import_twin, dumps_exact_json, envelope

__all__ = ["build_parser", "run"]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="mac.cli", description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)

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


def _emit(payload: dict[str, Any], as_json: bool, text: str) -> None:
    rendered = (
        dumps_exact_json(payload, ensure_ascii=True, indent=2, sort_keys=True)
        if as_json
        else text
    )
    print(rendered)


def _catalog_check(args: argparse.Namespace) -> int:
    report = cat.catalog_check()
    text = (
        f"catalog-check ok: {report['plants']} plants / "
        f"{report['sources']} sources / {report['full_row_count']} full rows"
    )
    _emit({"command": "catalog-check", **report}, args.json, text)
    return 0


def _extract(args: argparse.Namespace) -> int:
    plants = generate.plants_from_source(args.source.read_text(encoding="utf-8"))
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


_COMMANDS = {"catalog-check": _catalog_check, "extract": _extract}


def _refused(args: argparse.Namespace, refusal: envelope.ContractError) -> int:
    if getattr(args, "json", False):
        payload = {
            "command": args.command,
            "status": "refused",
            "code": getattr(refusal, "code", None),
            "message": str(refusal),
        }
        print(json.dumps(payload, sort_keys=True))
    else:
        print(str(refusal), file=sys.stderr)
    return 2


def run(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return _COMMANDS[args.command](args)
    except envelope.ContractError as refusal:
        return _refused(args, refusal)
    except Exception as exc:
        message = f"{type(exc).__name__}: {exc}"
        if getattr(args, "json", False):
            print(json.dumps(
                {"command": args.command, "status": "error", "message": message},
                sort_keys=True,
            ))
        else:
            print(message, file=sys.stderr)
        return 2


bind_import_twin(__name__)


if __name__ == "__main__":
    raise SystemExit(run())
