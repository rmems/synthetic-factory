#!/usr/bin/env python3
"""wsr commands: catalog-check and generate into a new destination.

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
    from ._contract import FINDING_USAGE, WsrRefusal, bind_import_twin, dumps_exact_json, refuse
    from . import catalog as cat
    from . import generate as gen
else:
    _ROOT = Path(__file__).resolve().parents[2]
    if str(_ROOT / "pipelines") not in sys.path:
        sys.path.insert(0, str(_ROOT / "pipelines"))
    from wsr._contract import FINDING_USAGE, WsrRefusal, bind_import_twin, dumps_exact_json, refuse
    from wsr import catalog as cat
    from wsr import generate as gen


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="wsr.cli", description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    check = commands.add_parser("catalog-check", help="load and pin the leftover3 catalog")
    check.add_argument("--catalog", type=Path, default=None)
    check.add_argument("--json", action="store_true")
    emit = commands.add_parser("generate", help="write leftover3 batches into a new directory")
    emit.add_argument("--catalog", type=Path, default=None)
    emit.add_argument("--out", type=Path, required=True)
    emit.add_argument("--round", type=int, action="append", dest="rounds")
    emit.add_argument("--json", action="store_true")
    return parser


def _catalog_payload(loaded: cat.Catalog) -> dict[str, Any]:
    return {
        "schema_id": "wsr-catalog/v2",
        "family_prefix": loaded.family_prefix,
        "factory": loaded.factory,
        "generator": loaded.generator,
        "start_round": loaded.start_round,
        "n_rounds": loaded.n_rounds,
        "quota_per_round": loaded.quota_per_round,
        "pair_count": len(loaded.pairs),
        "rounds": [pair.round_n for pair in loaded.pairs],
        "slugs": [
            str(pair.ok["slug"])
            if pair.source_format == "leftover3-v1"
            else str((pair.plant or {})["slug"])
            for pair in loaded.pairs
        ],
        "source": dict(loaded.source),
    }


def _generate_payload(built: tuple[gen.BuiltPair, ...], out_dir: Path) -> dict[str, Any]:
    return {
        "out": str(out_dir),
        "rounds": [
            {"round": item.round_n, "ok": item.ok["id"], "bad": item.bad["id"]}
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
                start = payload["start_round"]
                last = start + payload["n_rounds"] - 1
                print(f"catalog-check ok: {payload['pair_count']} leftover3 pairs r{start}-r{last}")
            return 0
        if args.command == "generate":
            rounds = tuple(args.rounds) if args.rounds else None
            built = gen.generate(args.out, catalog_path=args.catalog, rounds=rounds)
            payload = _generate_payload(built, args.out)
            if args.json:
                print(dumps_exact_json(payload, indent=2))
            else:
                print(f"generate ok: {payload['episodes']} episodes -> {args.out}")
            return 0
        refuse(FINDING_USAGE, f"unknown command {args.command!r}")
    except WsrRefusal as exc:
        print(str(exc), file=sys.stderr)
        if getattr(args, "json", False):
            print(json.dumps({"code": exc.code, "message": exc.message}, sort_keys=True))
        return 2


def main() -> None:
    raise SystemExit(run())


if __package__:
    bind_import_twin(__name__)


if __name__ == "__main__":
    main()
