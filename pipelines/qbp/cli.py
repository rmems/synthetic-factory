#!/usr/bin/env python3
"""qbp commands: catalog-check, self-check, generate into a new destination.

Exit codes: 0 on success, 2 on a coded refusal or usage error. ``--json``
prints one object so an agent never parses prose.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

if __package__:
    from ._contract import (
        FINDING_USAGE,
        QbpRefusal,
        bind_import_twin,
        dumps_exact_json,
        envelope,
        refuse,
    )
    from . import catalog as cat
    from . import generate as gen
else:
    _ROOT = Path(__file__).resolve().parents[2]
    if str(_ROOT / "pipelines") not in sys.path:
        sys.path.insert(0, str(_ROOT / "pipelines"))
    from qbp._contract import (  # type: ignore[no-redef]
        FINDING_USAGE,
        QbpRefusal,
        bind_import_twin,
        dumps_exact_json,
        envelope,
        refuse,
    )
    from qbp import catalog as cat  # type: ignore[no-redef]
    from qbp import generate as gen  # type: ignore[no-redef]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="qbp.cli", description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)

    check = commands.add_parser("catalog-check", help="load and pin the leftover catalog")
    check.add_argument("--catalog", type=Path, default=None)
    check.add_argument("--json", action="store_true")

    self_check = commands.add_parser("self-check", help="rebuild every leftover pair through hopper")
    self_check.add_argument("--catalog", type=Path, default=None)
    self_check.add_argument("--json", action="store_true")

    emit = commands.add_parser("generate", help="write leftover batches into a new directory")
    emit.add_argument("--catalog", type=Path, default=None)
    emit.add_argument("--out", type=Path, required=True)
    emit.add_argument("--mill", dest="mill_id", default=None)
    emit.add_argument("--round", type=int, action="append", dest="rounds")
    emit.add_argument("--json", action="store_true")
    return parser


def _catalog_payload(loaded: cat.Catalog) -> dict[str, Any]:
    return {
        "schema_id": "qbp-catalog/v1",
        "family_prefix": loaded.family_prefix,
        "factory": loaded.factory,
        "generator": loaded.generator,
        "n_mills": len(loaded.mills),
        "pair_count": len(loaded.pairs),
        "mills": [mill.mill_id for mill in loaded.mills],
        "slugs": [pair.ok["slug"] for pair in loaded.pairs],
        "source": dict(loaded.source),
        "pairs_sha256": loaded.pairs_sha256,
    }


def _generate_payload(built: tuple[gen.BuiltPair, ...], out_dir: Path) -> dict[str, Any]:
    return {
        "out": str(out_dir),
        "rounds": [
            {
                "mill_id": item.mill_id,
                "round": item.round_n,
                "ok": item.ok["id"],
                "bad": item.bad["id"],
            }
            for item in built
        ],
        "episodes": 2 * len(built),
    }


def run(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "catalog-check":
            loaded = cat.catalog_check(args.catalog)
            payload = _catalog_payload(loaded)
            if args.json:
                print(dumps_exact_json(payload, indent=2))
            else:
                print(f"catalog-check ok: {payload['pair_count']} leftover pairs across {payload['n_mills']} mills")
            return 0
        if args.command == "self-check":
            loaded = cat.catalog_check(args.catalog)
            built = gen.build_catalog(loaded)
            payload = {
                "command": "self-check",
                "status": "ok",
                "pairs": len(built),
                "mills": len(loaded.mills),
            }
            if args.json:
                print(dumps_exact_json(payload, indent=2))
            else:
                print(f"self-check ok: {len(built)} pairs across {len(loaded.mills)} mills")
            return 0
        if args.command == "generate":
            rounds = tuple(args.rounds) if args.rounds else None
            built = gen.generate(
                args.out,
                catalog_path=args.catalog,
                mill_id=args.mill_id,
                rounds=rounds,
            )
            payload = _generate_payload(built, args.out)
            if args.json:
                print(dumps_exact_json(payload, indent=2))
            else:
                print(f"generate ok: {payload['episodes']} episodes -> {args.out}")
            return 0
        refuse(FINDING_USAGE, f"unknown command {args.command!r}")
    except (QbpRefusal, envelope.ContractError) as exc:
        print(str(exc), file=sys.stderr)
        if getattr(args, "json", False):
            print(json.dumps({"code": getattr(exc, "code", None), "message": str(exc)}, sort_keys=True))
        return 2


def main() -> None:
    raise SystemExit(run())


if __package__:
    bind_import_twin(__name__)


if __name__ == "__main__":
    main()
