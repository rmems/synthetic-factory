#!/usr/bin/env python3
"""CSV mill commands: catalog-check and generate.

Exit codes: 0 on success, 2 on a coded refusal or usage error. ``--json``
prints one object so an agent never parses prose. Invoke as
``python3 -m pipelines.csv_mill.cli`` so the stdlib ``csv`` module stays intact.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

if __package__:
    from . import catalog as cat
    from . import generate as gen
    from ._contract import CsvRefusal, bind_import_twin, dumps_exact_json
else:
    _REPO = Path(__file__).resolve().parents[2]
    if str(_REPO) not in sys.path:
        sys.path.insert(0, str(_REPO))
    from pipelines.csv_mill import catalog as cat
    from pipelines.csv_mill import generate as gen
    from pipelines.csv_mill._contract import CsvRefusal, bind_import_twin, dumps_exact_json

__all__ = ["build_parser", "run"]


class _Parser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise CsvRefusal("USAGE", message)


def build_parser() -> argparse.ArgumentParser:
    parser = _Parser(prog="pipelines.csv_mill.cli", description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)

    check = commands.add_parser("catalog-check", help="load the pinned catalog and verify pins")
    check.add_argument("--catalog", type=Path, default=None)
    check.add_argument("--json", action="store_true")

    gen_cmd = commands.add_parser("generate", help="success/handoff pairs into a new directory")
    gen_cmd.add_argument("--catalog", type=Path, default=None)
    gen_cmd.add_argument("--out", type=Path, required=True)
    gen_cmd.add_argument("--plant", default=None, help="exact plant_id (mill_id:slug)")
    gen_cmd.add_argument("--mill", default=None, help="one mill_id, every plant in order")
    gen_cmd.add_argument("--all", action="store_true", help="every plant in the catalog")
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


def _catalog_check(args: argparse.Namespace) -> int:
    directory = _catalog_dir(args)
    findings = cat.catalog_check(directory)
    loaded = cat.load_catalog(directory)
    status = "findings" if findings else "ok"
    text = (
        f"catalog-check {status}: {loaded.catalog_id} "
        f"{len(loaded.plants)} plants / {len(loaded.mills)} mills"
    )
    _emit(
        {
            "command": "catalog-check",
            "status": status,
            "catalog_id": loaded.catalog_id,
            "plants": len(loaded.plants),
            "mills": len(loaded.mills),
            "findings": findings,
        },
        args.json,
        text,
    )
    return 1 if findings else 0


def _generate(args: argparse.Namespace) -> int:
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
    text = f"generated {summary['records']} records ({summary['pairs']} pairs) into {args.out}"
    _emit({"command": "generate", "status": "ok", "summary": summary}, args.json, text)
    return 0


def _refused(args: argparse.Namespace | None, refusal: CsvRefusal) -> int:
    command = getattr(args, "command", None) if args is not None else None
    as_json = bool(getattr(args, "json", False)) if args is not None else False
    if as_json:
        payload = {
            "command": command,
            "status": "refused",
            "code": refusal.code,
            "message": str(refusal),
        }
        print(dumps_exact_json(payload, ensure_ascii=True, sort_keys=True))
    else:
        print(str(refusal), file=sys.stderr)
    return 2


def run(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    parser = build_parser()
    args = argparse.Namespace(json="--json" in argv, command=None)
    try:
        args = parser.parse_args(argv)
        if args.command == "catalog-check":
            return _catalog_check(args)
        if args.command == "generate":
            return _generate(args)
    except CsvRefusal as exc:
        return _refused(args, exc)
    return 2


def main() -> None:
    raise SystemExit(run())


if __name__ == "__main__":
    main()
elif __package__:
    bind_import_twin(__name__)
