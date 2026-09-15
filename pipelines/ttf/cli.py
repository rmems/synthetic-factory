#!/usr/bin/env python3
"""TTF commands: catalog, catalog-check, and generate.

Read-only catalog listing, plus optional JSONL generation into a brand-new
destination. This command does not reserve or publish a raw round. Exit 0
on success, 2 on a coded refusal or usage error.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

if __package__:
    from . import catalog as cat
    from . import generate
    from ._contract import (
        FACTORY,
        FAMILY_PREFIX,
        SLICE_ID,
        SOURCE_COMMIT,
        SOURCE_REF,
        bind_import_twin,
        dumps_exact_json,
        envelope,
    )
else:
    _ROOT = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(_ROOT / "pipelines"))
    from ttf import catalog as cat  # type: ignore[no-redef]
    from ttf import generate  # type: ignore[no-redef]
    from ttf._contract import (  # type: ignore[no-redef]
        FACTORY,
        FAMILY_PREFIX,
        SLICE_ID,
        SOURCE_COMMIT,
        SOURCE_REF,
        bind_import_twin,
        dumps_exact_json,
        envelope,
    )

__all__ = ["build_parser", "run"]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="ttf", description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)

    listed = commands.add_parser("catalog", help="print the recovered TTF plant catalog")
    listed.add_argument("--json", action="store_true")

    check = commands.add_parser(
        "catalog-check", help="fail closed unless the catalog is the r02c slice"
    )
    check.add_argument("--json", action="store_true")

    gen = commands.add_parser("generate", help="emit one slice (never raw, never publish)")
    gen.add_argument("--round", type=int, required=True)
    gen.add_argument("--out", type=Path, default=None, help="new destination; omit to print JSONL")
    gen.add_argument("--json", action="store_true")
    return parser


def _emit(payload: dict[str, Any], as_json: bool, text: str) -> None:
    rendered = (
        dumps_exact_json(payload, ensure_ascii=True, indent=2, sort_keys=True)
        if as_json
        else text
    )
    print(rendered)


def _catalog(args: argparse.Namespace) -> int:
    loaded = cat.load_catalog()
    if args.json:
        payload = {
            "command": "catalog",
            "source_ref": SOURCE_REF,
            "source_commit": SOURCE_COMMIT,
            "family_prefix": FAMILY_PREFIX,
            "factory": FACTORY,
            "catalog_id": loaded.catalog_id,
            "slice": SLICE_ID,
            "plants": [plant.as_mapping() for plant in loaded.plants],
        }
        print(dumps_exact_json(payload, indent=2))
        return 0
    print(f"{loaded.catalog_id} {FACTORY} {len(loaded.plants)} plants")
    for plant in loaded.plants:
        print(f"{plant.source_round:2d} {plant.record_id} {plant.domain} {plant.decision}")
    return 0


def _catalog_check(args: argparse.Namespace) -> int:
    report = cat.catalog_check()
    text = (
        f"catalog-check ok: {report['plants']} plants "
        f"{report['slice']} r{report['first_round']}"
    )
    _emit({"command": "catalog-check", **report}, args.json, text)
    return 0


def _generate(args: argparse.Namespace) -> int:
    if args.out is None:
        plants = cat.plants_for_round(args.round)
        for plant in plants:
            print(dumps_exact_json(generate.record(plant), sort_keys=False))
        return 0
    summary = generate.run(generate.RunRequest(args.round, args.out))
    text = f"generated {summary['records']} records into {args.out}"
    _emit({"command": "generate", "status": "ok", "summary": summary}, args.json, text)
    return 0


_COMMANDS = {
    "catalog": _catalog,
    "catalog-check": _catalog_check,
    "generate": _generate,
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


def main() -> None:
    raise SystemExit(run())


bind_import_twin(__name__)


if __name__ == "__main__":
    main()
