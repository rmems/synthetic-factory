#!/usr/bin/env python3
"""ACTF AST-extract CLI. Prints a summary; never executes recovered sources."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import records as rec
from . import vocabulary as cv
from ._contract import bind_import_twin, dumps_exact_json

__all__ = ["build_parser", "run"]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="actf_cli.py",
        description="AST-only scan of recovered ACTF generator lineages.",
    )
    commands = parser.add_subparsers(dest="command", required=True)
    scan = commands.add_parser("scan", help="walk a recover-grok tree; print an exact-JSON summary")
    scan.add_argument("recovery_root", type=Path)
    return parser


def run(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command != "scan":
        parser.error("scan is the only command")
    try:
        extracted = rec.scan_recovery_tree(args.recovery_root)
    except cv.ActfRefusal as exc:
        print(str(exc), file=sys.stderr)
        return 2
    print(dumps_exact_json(rec.summarize(extracted)))
    return 0


bind_import_twin(__name__)
