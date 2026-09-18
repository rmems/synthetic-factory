#!/usr/bin/env python3
"""CLI for the browser-tool-use family.

Read-only generation: print the AST-extracted catalog or emit episode JSONL
on stdout. This command does not reserve or publish a raw round and does not
execute leftover mill scripts.
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
        BrwError,
        dumps_exact_json,
    )
    from . import catalog
    from . import generate
else:
    _ROOT = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(_ROOT / "pipelines"))
    from brw._contract import (  # type: ignore[no-redef]
        FACTORY,
        FAMILY_PREFIX,
        SOURCE_MILL_ID,
        SOURCE_PATH,
        SOURCE_REF,
        SOURCE_ROUND,
        BrwError,
        dumps_exact_json,
    )
    from brw import catalog  # type: ignore[no-redef]
    from brw import generate  # type: ignore[no-redef]

__all__ = ["build_parser", "run"]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="brw", description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)

    listed = commands.add_parser("catalog", help="print the brw-mill-r193 pair catalog")
    listed.add_argument("--json", action="store_true")

    gen = commands.add_parser("generate", help="emit episode JSONL (no publish)")
    gen.add_argument("--round", type=int, default=None, help="pair round (193..208)")
    gen.add_argument("--slug", default=None, help="ok_slug")
    gen.add_argument("--index", type=int, default=None, help="pair index 0..15")
    gen.add_argument(
        "--window",
        action="store_true",
        help="emit one success/fail pair per catalog entry starting at --round",
    )
    gen.add_argument("--count", type=int, default=None, help="window length (default 16)")
    side = gen.add_mutually_exclusive_group()
    side.add_argument("--success", action="store_true", help="emit only the success episode")
    side.add_argument("--fail", action="store_true", help="emit only the fail/handoff episode")

    notes = commands.add_parser("notes", help="print NOTES markdown for one pair")
    notes.add_argument("--round", type=int, required=True)
    notes.add_argument("--slug", default=None)
    notes.add_argument("--index", type=int, default=None)
    return parser


def _pair(slug: str | None, index: int | None, rnd: int | None):
    if slug is not None and index is not None:
        raise BrwError("select_one: pass --slug or --index, not both")
    if slug is not None:
        return catalog.pair_by_ok_slug(slug)
    if index is not None:
        return catalog.pair_at(index)
    if rnd is not None:
        return catalog.pair_for_round(rnd)
    return catalog.pair_at(0)


def _catalog_payload() -> dict:
    return {
        "source": SOURCE_MILL_ID,
        "source_ref": SOURCE_REF,
        "source_path": SOURCE_PATH,
        "family_prefix": FAMILY_PREFIX,
        "factory": FACTORY,
        "start_round": SOURCE_ROUND,
        "plants": [
            {"index": index, **pair} for index, pair in enumerate(catalog.PAIRS)
        ],
    }


def _emit(record: dict) -> None:
    print(dumps_exact_json(record))


def run(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "catalog":
            payload = _catalog_payload()
            if args.json:
                print(dumps_exact_json(payload, indent=2))
            else:
                print(f"{SOURCE_MILL_ID} {FACTORY} {len(catalog.PAIRS)} pairs")
                for index, pair in enumerate(catalog.PAIRS):
                    print(
                        f"{index:2d} r{SOURCE_ROUND + index} "
                        f"{pair['ok_slug']} {pair['css_short']}"
                    )
            return 0
        if args.command == "generate":
            if args.window:
                start = SOURCE_ROUND if args.round is None else args.round
                if args.slug is not None or args.index is not None:
                    raise BrwError("window_rejects_slug_index")
                for ok, bad in generate.generate_window(start, args.count):
                    if args.fail:
                        _emit(bad)
                    elif args.success:
                        _emit(ok)
                    else:
                        _emit(ok)
                        _emit(bad)
                return 0
            if args.round is None and args.slug is None and args.index is None:
                raise BrwError("missing_round: pass --round, --slug/--index, or --window")
            if args.count is not None:
                raise BrwError("count_requires_window")
            rnd = SOURCE_ROUND if args.round is None else args.round
            if args.slug is not None or args.index is not None:
                pair = _pair(args.slug, args.index, None)
                ok = generate.build_success(rnd, pair)
                bad = generate.build_fail(rnd, pair)
                generate.validate_pair(rnd, ok, bad, pair)
            else:
                ok, bad = generate.pair_records(rnd)
            if args.fail:
                _emit(bad)
            elif args.success:
                _emit(ok)
            else:
                _emit(ok)
                _emit(bad)
            return 0
        if args.command == "notes":
            pair = _pair(args.slug, args.index, args.round)
            print(generate.notes_for(args.round, pair), end="")
            return 0
    except BrwError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    return 2


def main() -> None:
    raise SystemExit(run())


if __name__ == "__main__":
    main()
