#!/usr/bin/env python3
"""Command line for the task gate: ``verify`` a proposals file or run the ``procedural`` mutator.

Both subcommands build the same :class:`GateRequest`; they differ only in where the proposals
come from. ``--denylist`` is required in substance: a missing or malformed file is a coded
refusal (exit 2) and nothing is written.
"""

from __future__ import annotations

import argparse
import hashlib
import sys
from collections.abc import Sequence
from pathlib import Path

from . import procedural
from . import vocabulary as cv
from ._contract import bind_import_twin, dumps_exact_json
from .proposal import parse_proposals
from .runner import GateRequest, run as run_gate

__all__ = ["main", "run"]


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="task_gate_cli.py", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    for name, text in (("verify", "gate a JSONL file of proposals"),
                       ("procedural", "gate the procedural mutator's seeded proposals")):
        command = sub.add_parser(name, help=text)
        command.add_argument("--catalog", type=Path, required=True)
        command.add_argument("--denylist", type=Path, default=None, help="REQUIRED eval denylist")
        command.add_argument("--prior-index", type=Path, action="append", default=[])
        command.add_argument("--out", type=Path, required=True, help="a new directory")
        command.add_argument("--timeout", type=float, default=cv.DEFAULT_TIMEOUT_S)
        if name == "verify":
            command.add_argument("--proposals", type=Path, required=True)
        else:
            command.add_argument("--seed", type=int, required=True)
            command.add_argument("--count", type=int, required=True)
            command.add_argument("--per-program-cap", type=int, default=3)
    return parser


def _proposals(args: argparse.Namespace, catalog) -> tuple[list, dict]:
    if args.command == "procedural":
        found = procedural.proposals_from_plan(catalog, args.seed, args.count, args.per_program_cap)
        return found, {"proposals": {
            "origin": "procedural", "seed": args.seed, "count": len(found),
            "catalog_id": catalog.catalog_id,
        }}
    try:
        data = args.proposals.read_bytes()
    except OSError as exc:
        raise cv.GateRefusal(cv.REFUSE_PROPOSALS_INVALID, f"{args.proposals}: {exc}") from exc
    found = parse_proposals(data, str(args.proposals))
    return found, {"proposals": {
        "origin": "file", "sha256": hashlib.sha256(data).hexdigest(), "count": len(found),
        "catalog_id": catalog.catalog_id,
    }}


def run(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        catalog = procedural.load_catalog(args.catalog)
        proposals, provenance = _proposals(args, catalog)
        summary = run_gate(GateRequest(
            programs=procedural.programs_from_catalog(catalog), proposals=proposals,
            denylist=args.denylist, out=args.out, prior_index_paths=args.prior_index,
            timeout_s=args.timeout, provenance=provenance,
        ))
    except cv.GateRefusal as exc:
        print(f"refused: {exc}", file=sys.stderr)
        return 2
    print(dumps_exact_json({"total": summary["total"], "verdicts": summary["verdicts"],
                            "survival_rate": summary["survival_rate"]}))
    return 0


main = run

bind_import_twin(__name__)
