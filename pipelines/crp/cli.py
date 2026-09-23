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
from . import r538 as r538_cat
from . import leftover3_prior as leftover3_prior_cat
from . import r729 as r729_cat
from . import r817 as r817_cat
from . import r995 as r995_cat
from ._contract import bind_import_twin, dumps_exact_json, envelope

__all__ = ["build_parser", "run"]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="crp.cli", description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)

    check = commands.add_parser(
        "catalog-check",
        help="every CRP catalog row has noun; slugs and families are unique",
    )
    check.add_argument("--json", action="store_true")
    check.add_argument(
        "--wave",
        choices=("leftover3", "leftover3-prior", "r432", "r538", "r729", "r817", "r995"),
        default="leftover3",
        help="leftover3 is the default; other waves are compact JSONL slices",
    )

    gen = commands.add_parser(
        "generate",
        help="one CRP triple into a brand-new destination (never raw)",
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
    report = _CATALOG_CHECKS[args.wave]()
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

_CATALOG_CHECKS = {
    "leftover3": cat.catalog_check,
    "leftover3-prior": leftover3_prior_cat.catalog_check,
    "r432": r432_cat.catalog_check,
    "r538": r538_cat.catalog_check,
    "r729": r729_cat.catalog_check,
    "r817": r817_cat.catalog_check,
    "r995": r995_cat.catalog_check,
}


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
