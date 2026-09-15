#!/usr/bin/env python3
"""FFD mill commands: catalog-check and generate.

Exit codes: 0 when the command succeeded, 1 when catalog-check reports findings,
2 on a coded refusal or a usage error. ``--json`` prints one object.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from . import catalog as cat
from . import generate
from ._contract import (
    SOURCES,
    bind_import_twin,
    default_catalog_dir,
    dumps_exact_json,
    envelope,
)

__all__ = ["build_parser", "run"]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="ffd.cli", description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)

    check = commands.add_parser("catalog-check", help="structural catalog check plus one build per pair")
    check.add_argument("--catalog", type=Path, default=None)
    check.add_argument("--json", action="store_true")

    gen = commands.add_parser("generate", help="one catalog pair into a new destination")
    gen.add_argument("--catalog", type=Path, default=None)
    gen.add_argument("--source", choices=SOURCES, required=True)
    gen.add_argument("--round", type=int, required=True)
    gen.add_argument("--out", type=Path, required=True)
    gen.add_argument("--pair", type=int, default=None)
    gen.add_argument("--json", action="store_true")
    return parser


def _emit(payload: dict[str, Any], as_json: bool, text: str) -> None:
    rendered = dumps_exact_json(payload, ensure_ascii=True, indent=2, sort_keys=True) if as_json else text
    print(rendered)


def _catalog_dir(args: argparse.Namespace) -> Path:
    return args.catalog if args.catalog is not None else default_catalog_dir()


def _catalog_check(args: argparse.Namespace) -> int:
    loaded = cat.load_catalog(_catalog_dir(args))
    findings = list(cat.catalog_check(loaded))
    for source_id in SOURCES:
        first = loaded.catalog_first(source_id)
        for index, _pair in enumerate(loaded.pairs_of(source_id)):
            try:
                records, notes = generate.build_round(loaded, source_id, first + index, index)
            except Exception as exc:
                findings.append({
                    "code": getattr(exc, "code", "CATALOG_FIELD_INVALID"),
                    "source": source_id,
                    "detail": str(exc),
                })
                continue
            if "Novel coverage:" not in notes:
                findings.append({
                    "code": "CATALOG_FIELD_INVALID",
                    "source": source_id,
                    "detail": f"{source_id} pair {index} notes omit Novel coverage",
                })
            for record in records:
                if not str(record["id"]).startswith("ffd-r"):
                    findings.append({
                        "code": "CATALOG_FIELD_INVALID",
                        "source": source_id,
                        "detail": f"id {record['id']!r} is not an ffd mill id",
                    })
    status = "findings" if findings else "ok"
    counts = {source_id: len(loaded.pairs_of(source_id)) for source_id in SOURCES}
    text = "\n".join(f"{item['code']} {item.get('source', '')}: {item['detail']}" for item in findings)
    if not text:
        text = f"catalog-check ok: leftover3={counts['leftover3']} lll={counts['lll']} hop={counts['hop']}"
    payload = {
        "command": "catalog-check",
        "status": status,
        "catalog_id": loaded.catalog_id,
        "sources": counts,
        "findings": findings,
    }
    _emit(payload, args.json, text)
    return 1 if findings else 0


def _generate(args: argparse.Namespace) -> int:
    summary = generate.run(generate.GenerateRequest(
        _catalog_dir(args), args.out, args.source, args.round, args.pair,
    ))
    text = (
        f"generated {len(summary['ids'])} records into {summary['out']} "
        f"({summary['source']} r{summary['round']}: {', '.join(summary['ids'])})"
    )
    _emit({"command": "generate", "status": "ok", "summary": summary}, args.json, text)
    return 0


_COMMANDS = {"catalog-check": _catalog_check, "generate": _generate}


def _refused(args: argparse.Namespace, refusal: envelope.ContractError) -> int:
    if getattr(args, "json", False):
        payload = {
            "command": args.command, "status": "refused",
            "code": getattr(refusal, "code", None), "message": str(refusal),
        }
        print(json.dumps(payload, sort_keys=True))
    else:
        print(str(refusal), file=sys.stderr)
    return 2


def run(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return _COMMANDS[args.command](args)
    except envelope.ContractError as refusal:
        return _refused(args, refusal)
    except Exception as exc:
        message = f"{type(exc).__name__}: {exc}"
        if getattr(args, "json", False):
            print(json.dumps({"command": args.command, "status": "error", "message": message},
                             sort_keys=True))
        else:
            print(message, file=sys.stderr)
        return 2


bind_import_twin(__name__)


if __name__ == "__main__":
    pipelines = Path(__file__).resolve().parents[1]
    if str(pipelines) not in sys.path:
        sys.path.insert(0, str(pipelines))
    if not __package__:
        import ffd.cli as pkg
        raise SystemExit(pkg.run())
    raise SystemExit(run())
