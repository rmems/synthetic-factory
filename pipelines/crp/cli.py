#!/usr/bin/env python3
"""CRP commands: catalog-check and generate.

Exit 0 on success, 1 when catalog-check reports findings, 2 on a coded
refusal or usage error. ``--json`` prints one object so an agent never
parses prose.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from . import catalog as cat
from . import generate
from . import r432 as r432_cat
from ._contract import bind_import_twin, dumps_exact_json, envelope

__all__ = ["build_parser", "run"]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="crp.cli", description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)

    check = commands.add_parser(
        "catalog-check",
        help="every leftover3 or r432 row has noun; slugs and families are unique",
    )
    check.add_argument("--json", action="store_true")
    check.add_argument(
        "--wave",
        choices=("leftover3", "r432"),
        default="leftover3",
        help="leftover3 (r729) is the default; r432 is the compact JSONL slice",
    )

    gen = commands.add_parser(
        "generate",
        help="one leftover3 or r432 triple into a new destination (never raw)",
    )
    gen.add_argument("--round", type=int, required=True)
    gen.add_argument("--out", type=Path, required=True)
    gen.add_argument("--json", action="store_true")
    return parser


def _emit(payload: dict[str, Any], as_json: bool, text: str) -> None:
    rendered = (
        dumps_exact_json(payload, ensure_ascii=True, indent=2, sort_keys=True)
        if as_json
        else text
    )
    print(rendered)


def _catalog_check(args: argparse.Namespace) -> int:
    report = r432_cat.catalog_check() if args.wave == "r432" else cat.catalog_check()
    text = (
        f"catalog-check ok: {report['plants']} plants "
        f"({report['triples']} triples, {report['nouns']} nouns) "
        f"r{report['first_round']}-r{report['last_round']}"
    )
    _emit({"command": "catalog-check", **report}, args.json, text)
    return 0


def _generate(args: argparse.Namespace) -> int:
    summary = generate.run(generate.RunRequest(args.round, args.out))
    text = (
        f"generated {summary['records']} records into {args.out} "
        f"(nouns {summary['nouns']})"
    )
    _emit({"command": "generate", "status": "ok", "summary": summary}, args.json, text)
    return 0


_COMMANDS = {"catalog-check": _catalog_check, "generate": _generate}


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
            print(json.dumps({"command": args.command, "status": "error", "message": message},
                             sort_keys=True))
        else:
            print(message, file=sys.stderr)
        return 2


bind_import_twin(__name__)


if __name__ == "__main__":
    raise SystemExit(run())
