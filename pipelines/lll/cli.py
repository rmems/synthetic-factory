#!/usr/bin/env python3
"""Leftover leftover leftover mill commands: catalog, catalog-check, generate.

Exit codes: 0 on success, 2 on a coded refusal or usage error. ``--json``
prints one object so an agent never parses prose.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

if __package__:
    from . import catalog as cat
    from . import generate as gen
    from ._contract import LllRefusal, bind_import_twin, dumps_exact_json
else:
    _REPO = Path(__file__).resolve().parents[2]
    if str(_REPO) not in sys.path:
        sys.path.insert(0, str(_REPO))
    from pipelines.lll import catalog as cat
    from pipelines.lll import generate as gen
    from pipelines.lll._contract import LllRefusal, bind_import_twin, dumps_exact_json

__all__ = ["build_parser", "run"]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="pipelines.lll.cli", description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)

    listing = commands.add_parser("catalog", help="list pinned leftover leftover leftover pairs")
    listing.add_argument("--catalog", type=Path, default=None)
    listing.add_argument("--json", action="store_true")

    check = commands.add_parser("catalog-check", help="load the pinned catalog and verify pins")
    check.add_argument("--catalog", type=Path, default=None)
    check.add_argument("--json", action="store_true")

    gen_cmd = commands.add_parser("generate", help="replay pair identities into a new directory")
    gen_cmd.add_argument("--catalog", type=Path, default=None)
    gen_cmd.add_argument("--out", type=Path, required=True)
    gen_cmd.add_argument("--plant", default=None, help="exact plant_id (mill_id:success_slug)")
    gen_cmd.add_argument("--mill", default=None, help="one mill_id, every pair in order")
    gen_cmd.add_argument("--all", action="store_true", help="every pair in the catalog")
    gen_cmd.add_argument("--round", type=int, default=None, help="id round; only with --plant")
    gen_cmd.add_argument("--json", action="store_true")
    return parser


def _emit(payload: dict[str, Any], as_json: bool, text: str) -> None:
    if as_json:
        rendered = dumps_exact_json(payload, ensure_ascii=True, indent=2, sort_keys=True)
    else:
        rendered = text
    print(rendered)


def _catalog_dir(args: argparse.Namespace) -> Path:
    return Path(args.catalog) if args.catalog is not None else cat.default_catalog_dir()


def _catalog_list(args: argparse.Namespace) -> int:
    directory = _catalog_dir(args)
    loaded = cat.load_catalog(directory)
    payload = {
        "status": "ok",
        "catalog_id": loaded.catalog_id,
        "factory": loaded.factory,
        "pair_count": len(loaded.plants),
        "plant_count": len(loaded.plants) * 2,
        "mills": [mill.mill_id for mill in loaded.mills],
        "plants": [plant.plant_id for plant in loaded.plants],
    }
    text = "\n".join(
        [
            f"{loaded.catalog_id} {len(loaded.plants)} leftover leftover leftover pairs",
            *[f"{plant.plant_id}\t{plant.title}" for plant in loaded.plants],
        ]
    )
    _emit(payload, args.json, text)
    return 0


def _catalog_check(args: argparse.Namespace) -> int:
    directory = _catalog_dir(args)
    findings = cat.catalog_check(directory)
    loaded = None if findings else cat.load_catalog(directory)
    status = "findings" if findings else "ok"
    payload = {
        "status": status,
        "findings": findings,
        "pair_count": 0 if loaded is None else len(loaded.plants),
        "mills": [] if loaded is None else [mill.mill_id for mill in loaded.mills],
    }
    text = status if not findings else "\n".join(findings)
    _emit(payload, args.json, text)
    return 2 if findings else 0


def _generate(args: argparse.Namespace) -> int:
    if args.round is not None and args.plant is None:
        raise LllRefusal("USAGE", "--round is only valid with --plant")
    summary = gen.run(
        gen.GenerateRequest(
            catalog_dir=_catalog_dir(args),
            out_dir=args.out,
            plant_id=args.plant,
            mill_id=args.mill,
            all_plants=args.all,
            round=args.round,
        )
    )
    dest = summary["destination"]
    text = f"wrote {summary['records']} leftover leftover leftover identities to {dest}"
    _emit(summary, args.json, text)
    return 0


def run(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "catalog":
            return _catalog_list(args)
        if args.command == "catalog-check":
            return _catalog_check(args)
        if args.command == "generate":
            return _generate(args)
    except LllRefusal as exc:
        print(exc, file=sys.stderr)
        return 2
    parser.error(f"unknown command {args.command}")
    return 2


def main() -> None:
    raise SystemExit(run())


if __name__ == "__main__":
    main()

bind_import_twin(__name__)
