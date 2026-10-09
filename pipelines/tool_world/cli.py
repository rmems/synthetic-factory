#!/usr/bin/env python3
"""Tool-world commands: catalog-check, generate, replay, render, tools.

Exit codes: 0 when the command succeeded with nothing to report, 1 when a
replay found a disagreeing record, 2 on a coded refusal or a usage error.
``--json`` prints one object.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from . import catalog as cat
from . import env as environment
from . import generate, replay
from . import vocabulary as cv
from ._contract import bind_import_twin, dumps_exact_json, envelope

__all__ = ["build_parser", "run"]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="tool_world_cli.py", description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)

    check = commands.add_parser("catalog-check", help="load the pinned world-pack catalog")
    check.add_argument("--catalog", type=Path, default=None)
    check.add_argument(
        "--write-pins",
        action="store_true",
        help="re-pin every pack from its current bytes in CATALOG.json before loading",
    )
    check.add_argument("--json", action="store_true")

    gen = commands.add_parser("generate", help="seeded records into a new run directory")
    gen.add_argument("--catalog", type=Path, default=None)
    gen.add_argument("--seed", type=int, required=True)
    gen.add_argument("--count", type=int, required=True)
    gen.add_argument("--out", type=Path, required=True)
    gen.add_argument("--factory", default=None, choices=sorted(cv.FACTORY_BY_SURFACE.values()))
    gen.add_argument("--variants", default="all", choices=("gold", "all"))
    gen.add_argument("--produced-at", default=None)
    gen.add_argument("--json", action="store_true")

    rep = commands.add_parser("replay", help="freshly replay every record of a run")
    rep.add_argument("run_dir", type=Path)
    rep.add_argument("--catalog", type=Path, default=None)
    rep.add_argument("--record", default=None, help="replay only the record with this id")
    rep.add_argument("--json", action="store_true")

    render = commands.add_parser("render", help="print one record from a run")
    render.add_argument("run_dir", type=Path)
    render.add_argument("record_id")
    render.add_argument("--json", action="store_true")

    tools = commands.add_parser("tools", help="print the tools a task exposes")
    tools.add_argument("--catalog", type=Path, default=None)
    tools.add_argument("--pack", required=True)
    tools.add_argument("--task", required=True)
    tools.add_argument("--json", action="store_true")
    return parser


def _print(payload: dict[str, Any], as_json: bool) -> int:
    if as_json:
        sys.stdout.write(dumps_exact_json(payload, indent=2) + "\n")
    else:
        sys.stdout.write(json.dumps(payload, indent=2) + "\n")
    return 0


def _catalog_check(args: argparse.Namespace) -> int:
    loaded = cat.write_pins(args.catalog) if args.write_pins else cat.load_catalog(args.catalog)
    return _print(
        {
            "catalog_id": loaded.catalog_id,
            "catalog_sha256": loaded.catalog_sha256,
            "packs": [
                {
                    "pack_id": pack.pack_id,
                    "pack_sha256": pack.pack_sha256,
                    "surfaces": list(pack.surfaces),
                    "tasks": [task.task_id for task in pack.tasks],
                    "license": dict(pack.license),
                }
                for pack in loaded.packs
            ],
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
            factory=args.factory,
            variants=args.variants,
            produced_at=args.produced_at,
        )
    )
    return _print(summary, args.json)


def _replay(args: argparse.Namespace) -> int:
    summary = replay.replay_run(args.run_dir, cat.load_catalog(args.catalog), args.record)
    _print(summary, args.json)
    return 0 if summary["passed"] else 1


def _render(args: argparse.Namespace) -> int:
    for record in replay.load_records(args.run_dir):
        if record.get("id") == args.record_id:
            return _print(record, args.json)
    cv.refuse(
        cv.FINDING_RECORD_NOT_FOUND,
        f"record {args.record_id} is not in {args.run_dir / replay.CANDIDATES_FILENAME}",
    )


def _tools(args: argparse.Namespace) -> int:
    loaded = cat.load_catalog(args.catalog)
    pack = loaded.pack(args.pack)
    env = environment.Environment(pack, pack.task(args.task), 0)
    return _print(
        {
            "pack_id": pack.pack_id,
            "task_id": args.task,
            "tools": [spec.declared() for spec in env.tools()],
        },
        args.json,
    )


def run(argv: list[str] | None = None) -> int:
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
        handlers = {
            "catalog-check": _catalog_check,
            "generate": _generate,
            "replay": _replay,
            "render": _render,
            "tools": _tools,
        }
        return handlers[args.command](args)
    except envelope.ContractError as exc:
        sys.stderr.write(f"{exc}\n")
        return 2


bind_import_twin(__name__)
