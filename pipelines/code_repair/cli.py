#!/usr/bin/env python3
"""The agent surface of the code-repair family: ``catalog-check``, ``generate``, ``render``.

Exit codes: 0 when the command succeeded with nothing to report, 1 when it
ran and reports findings (catalog findings, a record that is not a positive
example), 2 on a coded refusal or a usage error. ``--json`` prints one object
with a ``code`` field per finding so an agent never parses prose.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from . import catalog as cat
from . import executor as ex
from . import vocabulary as cv
from ._contract import bind_import_twin, envelope

__all__ = ["build_parser", "run"]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="code_repair_cli.py", description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)

    check = commands.add_parser("catalog-check", help="every original passes; references agree")
    check.add_argument("--catalog", type=Path, required=True)
    check.add_argument("--timeout-s", type=float, default=cv.DEFAULT_TIMEOUT_S)
    check.add_argument("--json", action="store_true")

    return parser


def _emit(payload: dict[str, Any], as_json: bool, text: str) -> None:
    print(json.dumps(payload, indent=2, sort_keys=True) if as_json else text)


def _catalog_check(args: argparse.Namespace) -> int:
    catalog = cat.load_catalog(args.catalog)
    findings = cat.catalog_check(catalog, ex.Executor(timeout_s=args.timeout_s))
    status = "findings" if findings else "ok"
    lines = [f"{f['code']} {f['program_id']}: {f['detail']}" for f in findings]
    text = "\n".join(lines) or f"catalog-check ok: {len(catalog.programs)} programs pass"
    payload = {
        "command": "catalog-check", "status": status, "catalog_id": catalog.catalog_id,
        "programs": len(catalog.programs), "findings": findings,
    }
    _emit(payload, args.json, text)
    return 1 if findings else 0


_COMMANDS = {"catalog-check": _catalog_check}


def _refused(args: argparse.Namespace, refusal: envelope.ContractError) -> int:
    """A coded refusal: one JSON object on stdout under ``--json``, else ``CODE: prose``."""

    if getattr(args, "json", False):
        payload = {
            "command": args.command, "status": "refused",
            "code": getattr(refusal, "code", None), "message": str(refusal),
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


bind_import_twin(__name__)
