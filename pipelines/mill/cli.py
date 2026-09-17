#!/usr/bin/env python3
"""Mill commands: catalog-check, generate, publish, render.

Exit codes: 0 when the command succeeded with nothing to report, 2 on a
coded refusal or a usage error. ``--json`` prints one object.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from . import catalog_load
from . import generate
from . import publication
from . import vocabulary as cv
from ._contract import bind_import_twin, dumps_exact_json, envelope, load_strict_json

__all__ = ["build_parser", "run"]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="mill_cli.py", description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)

    check = commands.add_parser("catalog-check", help="load the pinned plant catalog")
    check.add_argument("--catalog", type=Path, required=True)
    check.add_argument("--json", action="store_true")

    gen = commands.add_parser("generate", help="seeded pairs into a new run directory")
    gen.add_argument("--catalog", type=Path, required=True)
    gen.add_argument("--seed", type=int, required=True)
    gen.add_argument("--count", type=int, required=True)
    gen.add_argument("--out", type=Path, required=True)
    gen.add_argument("--produced-at", default=None)
    gen.add_argument("--start-round", type=int, default=1)
    gen.add_argument("--json", action="store_true")

    pub = commands.add_parser("publish", help="copy a validated run to a new destination")
    pub.add_argument("--run", type=Path, required=True)
    pub.add_argument("--catalog", type=Path, required=True)
    pub.add_argument("--out", type=Path, required=True)
    pub.add_argument("--factory-id", default=cv.FACTORY_ID)
    pub.add_argument("--hop-factory", default=None)
    pub.add_argument("--json", action="store_true")

    render = commands.add_parser("render", help="print one record from a run")
    render.add_argument("run_dir", type=Path)
    render.add_argument("record_id")
    render.add_argument("--json", action="store_true")
    return parser


def _print(payload: dict[str, Any], as_json: bool) -> int:
    if as_json:
        sys.stdout.write(dumps_exact_json(payload, indent=2) + "\n")
        return 0
    sys.stdout.write(json.dumps(payload, indent=2) + "\n")
    return 0


def _catalog_check(args: argparse.Namespace) -> int:
    loaded = catalog_load.load_catalog(args.catalog)
    return _print(
        {
            "catalog_id": loaded.catalog_id,
            "family": loaded.family,
            "plant_count": loaded.plant_count,
            "plants_sha256": loaded.plants_sha256,
            "plant_ids": list(loaded.ids()),
        },
        args.json,
    )


def _generate(args: argparse.Namespace) -> int:
    summary = generate.run(
        generate.RunRequest(
            catalog_dir=args.catalog,
            out_dir=args.out,
            seed=args.seed,
            count=args.count,
            produced_at=args.produced_at,
            start_round=args.start_round,
        )
    )
    return _print(summary, args.json)


def _publish(args: argparse.Namespace) -> int:
    receipt = publication.publish(
        publication.PublishRequest(
            run_dir=args.run,
            out_dir=args.out,
            catalog_dir=args.catalog,
            factory_id=args.factory_id,
            hop_factory=args.hop_factory,
        )
    )
    return _print(receipt, args.json)


def _render(args: argparse.Namespace) -> int:
    pairs = args.run_dir / generate.PAIRS_FILENAME
    cv.refuse_when(not pairs.is_file(), cv.FINDING_RUN_FILE_MISSING, f"missing {generate.PAIRS_FILENAME}")
    for line in pairs.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        record = load_strict_json(line)
        if isinstance(record, dict) and record.get("id") == args.record_id:
            return _print(record, args.json)
    cv.refuse(cv.FINDING_RECORD_NOT_FOUND, f"record {args.record_id} is not in {pairs}")


def run(argv: list[str] | None = None) -> int:
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
        handlers = {
            "catalog-check": _catalog_check,
            "generate": _generate,
            "publish": _publish,
            "render": _render,
        }
        return handlers[args.command](args)
    except envelope.ContractError as exc:
        sys.stderr.write(f"{exc}\n")
        return 2


bind_import_twin(__name__)
