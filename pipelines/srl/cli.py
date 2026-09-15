#!/usr/bin/env python3
"""CLI for the sparse-reward long-task family.

Read-only generation: print the AST-extracted catalog or emit episode JSONL
on stdout. This command does not reserve or publish a raw round.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

if __package__:
    from ._contract import (
        FACTORY,
        FAMILY_PREFIX,
        SOURCE_MILL_ID,
        SOURCE_PATH,
        SOURCE_REF,
        SOURCE_ROUND,
        SrlError,
        dumps_exact_json,
    )
    from . import catalog
    from . import generate
else:
    _ROOT = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(_ROOT / "pipelines"))
    from srl._contract import (  # type: ignore[no-redef]
        FACTORY,
        FAMILY_PREFIX,
        SOURCE_MILL_ID,
        SOURCE_PATH,
        SOURCE_REF,
        SOURCE_ROUND,
        SrlError,
        dumps_exact_json,
    )
    from srl import catalog  # type: ignore[no-redef]
    from srl import generate  # type: ignore[no-redef]

__all__ = ["build_parser", "run"]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="srl", description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)

    listed = commands.add_parser("catalog", help="print the srl_r6110 plant catalog")
    listed.add_argument("--json", action="store_true")

    gen = commands.add_parser("generate", help="emit episode JSONL (no publish)")
    gen.add_argument("--round", type=int, default=None, help="single-record round")
    gen.add_argument("--slug", default=None, help="plant slug")
    gen.add_argument("--index", type=int, default=None, help="plant index 0..15")
    gen.add_argument(
        "--window",
        action="store_true",
        help="emit one record per plant starting at --round (default 6110)",
    )
    gen.add_argument("--count", type=int, default=None, help="window length (default 16)")

    notes = commands.add_parser("notes", help="print NOTES markdown for one plant")
    notes.add_argument("--round", type=int, required=True)
    notes.add_argument("--slug", default=None)
    notes.add_argument("--index", type=int, default=None)
    return parser


def _plant(slug: str | None, index: int | None) -> catalog.Plant:
    if slug is not None and index is not None:
        raise SrlError("select_one: pass --slug or --index, not both")
    if slug is not None:
        return catalog.plant_by_slug(slug)
    if index is not None:
        return catalog.plant_at(index)
    return catalog.plant_at(0)


def _catalog_payload() -> dict:
    return {
        "source": SOURCE_MILL_ID,
        "source_ref": SOURCE_REF,
        "source_path": SOURCE_PATH,
        "family_prefix": FAMILY_PREFIX,
        "factory": FACTORY,
        "start_round": SOURCE_ROUND,
        "plants": [
            {"index": index, **plant} for index, plant in enumerate(catalog.PLANTS)
        ],
    }


def run(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "catalog":
            payload = _catalog_payload()
            if args.json:
                print(dumps_exact_json(payload, indent=2))
            else:
                print(f"{SOURCE_MILL_ID} {FACTORY} {len(catalog.PLANTS)} plants")
                for index, plant in enumerate(catalog.PLANTS):
                    print(f"{index:2d} {plant['slug']} {plant['tool']}")
            return 0
        if args.command == "generate":
            if args.window:
                start = SOURCE_ROUND if args.round is None else args.round
                for record in generate.generate_window(start, args.count):
                    print(dumps_exact_json(record))
                return 0
            if args.round is None:
                raise SrlError("missing_round: pass --round or --window")
            if args.count is not None:
                raise SrlError("count_requires_window")
            record = generate.episode(args.round, _plant(args.slug, args.index))
            print(dumps_exact_json(record))
            return 0
        if args.command == "notes":
            print(generate.notes(args.round, _plant(args.slug, args.index)), end="")
            return 0
    except SrlError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    return 2


def main() -> None:
    raise SystemExit(run())


if __name__ == "__main__":
    main()
