#!/usr/bin/env python3
"""IRC leftover3 commands: catalog, catalog-check, generate, notes.

Exit codes: 0 on success, 2 on a coded refusal or usage error. ``--json``
prints one object so an agent never parses prose. Generate writes a brand-new
destination and never reserves a raw round.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

if __package__:
    from . import catalog as cat
    from . import generate as gen
    from . import pipe_catalog as pipes
    from ._contract import (
        COMMITTED_SPEC_ROW_COUNT,
        CATALOG_FIRST,
        FACTORY,
        FAMILY_SOURCE_FILES,
        FULL_SPEC_ROW_COUNT,
        GENERATOR,
        N_PAIRS,
        SOURCE_COMMIT,
        SOURCE_MILL_ID,
        SOURCE_PATH,
        SOURCE_REF,
        IrcRefusal,
        bind_import_twin,
        dumps_exact_json,
    )
else:
    _PIPELINES = Path(__file__).resolve().parents[1]
    if str(_PIPELINES) not in sys.path:
        sys.path.insert(0, str(_PIPELINES))
    from irc import catalog as cat
    from irc import generate as gen
    from irc import pipe_catalog as pipes
    from irc._contract import (
        COMMITTED_SPEC_ROW_COUNT,
        CATALOG_FIRST,
        FACTORY,
        FAMILY_SOURCE_FILES,
        FULL_SPEC_ROW_COUNT,
        GENERATOR,
        N_PAIRS,
        SOURCE_COMMIT,
        SOURCE_MILL_ID,
        SOURCE_PATH,
        SOURCE_REF,
        IrcRefusal,
        bind_import_twin,
        dumps_exact_json,
    )

__all__ = ["build_parser", "run"]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="irc.cli", description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)

    listed = commands.add_parser("catalog", help="list leftover3 pair identities")
    listed.add_argument("--json", action="store_true")

    check = commands.add_parser("catalog-check", help="verify the committed leftover3 slice")
    check.add_argument("--json", action="store_true")

    gen_cmd = commands.add_parser("generate", help="episode pairs into a new directory")
    gen_cmd.add_argument("--out", type=Path, required=True)
    gen_cmd.add_argument("--round", type=int, default=None)
    gen_cmd.add_argument("--slug", default=None)
    gen_cmd.add_argument("--index", type=int, default=None)
    gen_cmd.add_argument("--window", action="store_true")
    gen_cmd.add_argument("--json", action="store_true")

    notes = commands.add_parser("notes", help="print NOTES markdown for one pair")
    notes.add_argument("--round", type=int, required=True)
    return parser


def _emit(payload: dict[str, Any], as_json: bool, text: str) -> None:
    print(dumps_exact_json(payload, ensure_ascii=True, indent=2, sort_keys=True) if as_json else text)


def _catalog_payload() -> dict[str, Any]:
    plants = []
    for index, pair in enumerate(cat.PAIRS):
        plants.append(
            {
                "index": index,
                "round": CATALOG_FIRST + index,
                "ok": pair["ok"]["slug"],
                "bad": pair["bad"]["slug"],
            }
        )
    return {
        "command": "catalog",
        "factory": FACTORY,
        "generator": GENERATOR,
        "plants": plants,
        "source": SOURCE_MILL_ID,
        "source_commit": SOURCE_COMMIT,
        "source_path": SOURCE_PATH,
        "source_ref": SOURCE_REF,
        "status": "ok",
    }


def _catalog_list(as_json: bool) -> int:
    payload = _catalog_payload()
    text = f"{SOURCE_MILL_ID} {FACTORY} {N_PAIRS} pairs\n" + "\n".join(
        f"{item['index']:2d} r{item['round']} {item['ok']} / {item['bad']}"
        for item in payload["plants"]
    )
    _emit(payload, as_json, text)
    return 0


def _catalog_check(as_json: bool) -> int:
    family = pipes.catalog_family_check()
    payload = {
        "command": "catalog-check",
        "committed_spec_rows": family.committed_spec_rows,
        "deferred_family_files": FAMILY_SOURCE_FILES,
        "factory": FACTORY,
        "full_spec_rows": FULL_SPEC_ROW_COUNT,
        "plants": N_PAIRS,
        "source": SOURCE_MILL_ID,
        "source_commit": SOURCE_COMMIT,
        "status": "ok",
    }
    text = (
        f"catalog-check ok: {SOURCE_MILL_ID} {N_PAIRS} pair plants; "
        f"{family.committed_spec_rows}/{FULL_SPEC_ROW_COUNT} pipe rows committed"
    )
    _emit(payload, as_json, text)
    return 0


def _generate(args: argparse.Namespace) -> int:
    summary = gen.run(
        gen.GenerateRequest(
            out_dir=args.out,
            round=args.round,
            slug=args.slug,
            index=args.index,
            window=args.window,
        )
    )
    text = f"generated {summary['records']} records ({summary['pairs']} pairs) into {args.out}"
    _emit({"command": "generate", "status": "ok", "summary": summary}, args.json, text)
    return 0


def _notes(rnd: int) -> int:
    ok, bad = gen.pair_records(rnd)
    print(gen.notes_for(rnd, ok, bad), end="")
    return 0


def _refused(args: argparse.Namespace | None, refusal: IrcRefusal) -> int:
    as_json = bool(getattr(args, "json", False)) if args is not None else False
    if as_json:
        print(
            dumps_exact_json(
                {
                    "command": getattr(args, "command", None) if args is not None else None,
                    "status": "refused",
                    "code": refusal.code,
                    "message": str(refusal),
                },
                ensure_ascii=True,
                sort_keys=True,
            )
        )
    else:
        print(str(refusal), file=sys.stderr)
    return 2


def run(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "catalog":
            return _catalog_list(args.json)
        if args.command == "catalog-check":
            return _catalog_check(args.json)
        if args.command == "generate":
            return _generate(args)
        if args.command == "notes":
            return _notes(args.round)
    except IrcRefusal as exc:
        return _refused(args, exc)
    return 2


def main() -> None:
    raise SystemExit(run())


if __name__ == "__main__":
    main()
elif __package__:
    bind_import_twin(__name__)
