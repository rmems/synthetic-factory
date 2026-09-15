#!/usr/bin/env python3
"""KCL mill commands: catalog-check, generate, and hopper g46c hop-replay.

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
    from ._contract import (
        HOPPER_WAVE,
        KclRefusal,
        bind_import_twin,
        dumps_exact_json,
    )
else:
    _PIPELINES = Path(__file__).resolve().parents[1]
    if str(_PIPELINES) not in sys.path:
        sys.path.insert(0, str(_PIPELINES))
    from kcl import catalog as cat
    from kcl import generate as gen
    from kcl._contract import (
        HOPPER_WAVE,
        KclRefusal,
        bind_import_twin,
        dumps_exact_json,
    )

__all__ = ["build_parser", "main", "run"]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="kcl.cli", description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)

    check = commands.add_parser("catalog-check", help="load the pinned catalog and verify pins")
    check.add_argument("--catalog", type=Path, default=None)
    check.add_argument("--json", action="store_true")

    emit = commands.add_parser("generate", help="leftover CrashLoop pairs into a new directory")
    emit.add_argument("--catalog", type=Path, default=None)
    emit.add_argument("--out", type=Path, required=True)
    emit.add_argument("--plant", default=None, help="exact plant_id (mill_id:slug)")
    emit.add_argument("--mill", default=None, help="one mill_id, every plant in order")
    emit.add_argument("--all", action="store_true", dest="all_plants")
    emit.add_argument("--round", type=int, default=None)
    emit.add_argument("--json", action="store_true")

    hop = commands.add_parser("hop-replay", help="replay hopper g46c pairs via hopper on main")
    hop.add_argument("--out", type=Path, required=True)
    hop.add_argument("--wave", default=HOPPER_WAVE)
    hop.add_argument("--factory", default=None)
    hop.add_argument("--slug", default=None)
    hop.add_argument("--json", action="store_true")
    return parser


def _emit(payload: dict[str, Any], as_json: bool, text: str) -> None:
    print(dumps_exact_json(payload, indent=2, sort_keys=True) if as_json else text)


def _catalog_check(args: argparse.Namespace) -> int:
    loaded = cat.catalog_check(args.catalog)
    payload = {
        "command": "catalog-check",
        "status": "ok",
        "catalog_id": loaded.catalog_id,
        "plants": len(loaded.plants),
        "mills": len(loaded.mills),
        "factory": loaded.factory,
    }
    _emit(
        payload,
        args.json,
        f"catalog-check ok: {loaded.catalog_id} {len(loaded.plants)} plants / {len(loaded.mills)} mills",
    )
    return 0


def _generate(args: argparse.Namespace) -> int:
    built = gen.generate(
        args.out,
        catalog_dir=args.catalog,
        plant_id=args.plant,
        mill_id=args.mill,
        all_plants=args.all_plants,
        round_n=args.round,
    )
    payload = {
        "command": "generate",
        "status": "ok",
        "out": str(args.out),
        "pairs": len(built),
        "episodes": 2 * len(built),
        "ids": [{"ok": item.ok["id"], "bad": item.bad["id"]} for item in built],
    }
    _emit(payload, args.json, f"generate ok: {len(built)} pairs -> {args.out}")
    return 0


def _hop_replay(args: argparse.Namespace) -> int:
    written = gen.hop_replay(
        args.out,
        wave=args.wave,
        factory=args.factory,
        slug=args.slug,
    )
    payload = {
        "command": "hop-replay",
        "status": "ok",
        "wave": args.wave,
        "out": str(args.out),
        "pairs": len(written),
        "written": [
            {"factory": item.factory, "round": item.round_n, "ids": list(item.ids)}
            for item in written
        ],
    }
    _emit(payload, args.json, f"hop-replay ok: {len(written)} {args.wave} pairs -> {args.out}")
    return 0


def _refused(args: argparse.Namespace | None, refusal: KclRefusal) -> int:
    command = getattr(args, "command", None) if args is not None else None
    as_json = bool(getattr(args, "json", False)) if args is not None else False
    if as_json:
        print(
            dumps_exact_json(
                {
                    "command": command,
                    "status": "refused",
                    "code": refusal.code,
                    "message": str(refusal),
                },
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
        if args.command == "catalog-check":
            return _catalog_check(args)
        if args.command == "generate":
            return _generate(args)
        if args.command == "hop-replay":
            return _hop_replay(args)
    except KclRefusal as exc:
        return _refused(args, exc)
    return 2


def main() -> None:
    raise SystemExit(run())


if __name__ == "__main__":
    main()
elif __package__:
    bind_import_twin(__name__)
