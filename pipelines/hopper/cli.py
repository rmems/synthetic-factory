#!/usr/bin/env python3
"""Hopper commands: self-check, generate, publish.

Exit codes: 0 on success, 1 when self-check reports findings, 2 on a coded
refusal or usage error. ``--json`` prints one object so an agent never parses
prose. ``generate`` writes only into a brand-new ``--out`` tree and never
names ``outputs/raw``. ``publish`` is opt-in and requires ``--raw-root``.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from ._contract import (
    FINDING_DESTINATION_EXISTS,
    FINDING_DESTINATION_UNDER_RAW,
    FINDING_PUBLISH_FAILED,
    FINDING_UNKNOWN_FACTORY,
    FINDING_UNKNOWN_SLUG,
    FINDING_UNKNOWN_WAVE,
    HopperRefusal,
    bind_import_twin,
    envelope,
    is_under_raw,
    refuse,
    refuse_first,
    refuse_when,
)
from . import episode as ep
from . import plants as pl
from .plants import WAVES, load_catalog

if __name__.startswith("pipelines."):
    from ..round_txn import TransactionError, abort, frontier_status, publish, reserve
else:
    from round_txn import TransactionError, abort, frontier_status, publish, reserve

__all__ = ["build_parser", "main", "run"]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="hopper.cli", description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)

    check = commands.add_parser("self-check", help="validate catalog and rebuild every pair")
    check.add_argument("--catalog", type=Path, default=pl.DEFAULT_CATALOG_DIR)
    check.add_argument("--json", action="store_true")

    gen = commands.add_parser("generate", help="replay selected pairs into a new directory")
    gen.add_argument("--catalog", type=Path, default=pl.DEFAULT_CATALOG_DIR)
    gen.add_argument("--out", type=Path, required=True)
    gen.add_argument("--wave", choices=WAVES, default=None)
    gen.add_argument("--factory", default=None)
    gen.add_argument("--slug", default=None)
    gen.add_argument("--json", action="store_true")

    pub = commands.add_parser("publish", help="reserve/publish one pair against --raw-root")
    pub.add_argument("--catalog", type=Path, default=pl.DEFAULT_CATALOG_DIR)
    pub.add_argument("--raw-root", type=Path, required=True)
    pub.add_argument("--factory", required=True)
    pub.add_argument("--slug", required=True)
    pub.add_argument("--json", action="store_true")
    return parser


def _emit(payload: dict[str, Any], as_json: bool, text: str) -> None:
    print(json.dumps(payload, sort_keys=True) if as_json else text)


def _selected(catalog: pl.Catalog, wave: str | None, factory: str | None, slug: str | None):
    rows = list(catalog.pairs)
    if wave is not None:
        refuse_when(wave not in WAVES, FINDING_UNKNOWN_WAVE, f"unknown hopper wave {wave!r}")
        rows = [row for row in rows if row.wave == wave]
    if factory is not None:
        refuse_when(factory not in catalog.prefixes, FINDING_UNKNOWN_FACTORY, f"unknown factory {factory}")
        rows = [row for row in rows if row.factory == factory]
    if slug is not None:
        rows = [row for row in rows if row.ok["slug"] == slug or row.bad["slug"] == slug]
        refuse_when(not rows, FINDING_UNKNOWN_SLUG, f"no hopper plant with slug {slug!r}")
    return rows


def _self_check(args: argparse.Namespace) -> int:
    catalog = load_catalog(args.catalog)
    built = 0
    for row in catalog.pairs:
        ep.build_pair(row.factory, row.published_round, row.ok, row.bad)
        built += 1
    payload = {
        "command": "self-check",
        "status": "ok",
        "plants": catalog.meta["plants"],
        "pairs": len(catalog.pairs),
        "waves": list(WAVES),
        "built": built,
    }
    _emit(payload, args.json, f"self-check ok: {built} pairs across {len(catalog.cycle)} factories")
    return 0


def _generate(args: argparse.Namespace) -> int:
    out_dir = Path(args.out)
    refuse_first((
        (is_under_raw(out_dir), FINDING_DESTINATION_UNDER_RAW, f"{out_dir} names or aliases the raw tree"),
        (out_dir.exists(), FINDING_DESTINATION_EXISTS, f"{out_dir} already exists"),
    ))
    catalog = load_catalog(args.catalog)
    rows = _selected(catalog, args.wave, args.factory, args.slug)
    refuse_when(not rows, FINDING_UNKNOWN_SLUG, "no hopper pairs match the generate filters")
    out_dir.mkdir(parents=True)
    written = []
    for row in rows:
        stage = out_dir / row.factory
        ids = ep.emit_stage(stage, row.factory, row.published_round, row.ok, row.bad)
        written.append({
            "factory": row.factory,
            "wave": row.wave,
            "round": row.published_round,
            "ids": list(ids),
        })
    payload = {
        "command": "generate",
        "status": "ok",
        "out": str(out_dir),
        "pairs": len(written),
        "written": written,
    }
    _emit(payload, args.json, f"generate ok: {len(written)} pairs -> {out_dir}")
    return 0


def _publish(args: argparse.Namespace) -> int:
    catalog = load_catalog(args.catalog)
    row = catalog.pair_for_slug(args.slug)
    refuse_when(
        row.factory != args.factory,
        FINDING_UNKNOWN_FACTORY,
        f"slug {args.slug} belongs to {row.factory}, not {args.factory}",
    )
    factory_path = ep.factory_dir(args.factory, raw_root=args.raw_root)
    try:
        status = frontier_status(factory_path)
        round_n = status["next_round"]
        payload = reserve(factory_path, round_n, 2)
    except TransactionError as exc:
        refuse(FINDING_PUBLISH_FAILED, str(exc))
    token = payload["token"]
    stage = Path(payload["staging_dir"])
    try:
        ids = ep.emit_stage(stage, row.factory, round_n, row.ok, row.bad)
        manifest = publish(factory_path, round_n, token)
    except (HopperRefusal, TransactionError) as exc:
        try:
            abort(factory_path, round_n, token)
        except TransactionError as abort_exc:
            refuse(FINDING_PUBLISH_FAILED, f"{exc}; abort failed: {abort_exc}")
        refuse(FINDING_PUBLISH_FAILED, str(exc))
    result = {
        "command": "publish",
        "status": "ok",
        "factory": args.factory,
        "round": round_n,
        "ids": list(ids),
        "records": manifest.get("records"),
    }
    _emit(result, args.json, f"publish ok: {args.factory} r{round_n} {ids}")
    return 0


_COMMANDS = {
    "self-check": _self_check,
    "generate": _generate,
    "publish": _publish,
}


def _refused(args: argparse.Namespace, refusal: envelope.ContractError) -> int:
    if getattr(args, "json", False):
        print(json.dumps({
            "command": getattr(args, "command", None),
            "status": "refused",
            "code": getattr(refusal, "code", None),
            "message": str(refusal),
        }, sort_keys=True))
    else:
        print(str(refusal), file=sys.stderr)
    return 2


def run(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return _COMMANDS[args.command](args)
    except envelope.ContractError as refusal:
        return _refused(args, refusal)


def main(argv: list[str] | None = None) -> int:
    return run(argv)


bind_import_twin(__name__)


if __name__ == "__main__":
    raise SystemExit(main())
