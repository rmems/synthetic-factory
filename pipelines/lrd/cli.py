#!/usr/bin/env python3
"""LRD mill commands: catalog-check, generate, audit.

Exit codes: 0 on success, 1 when audit/catalog-check reports findings, 2 on a
coded refusal or usage error. ``--json`` prints one object so an agent never
parses prose. ``generate`` writes only into a brand-new ``--out`` tree and
never names ``outputs/raw``. There is no hopper / publish / ``round_txn``
path: ``dpr-lrd-hopper*`` stay with dpr.
"""

from __future__ import annotations

import argparse
import ast
import sys
from pathlib import Path
from typing import Any

if __package__:
    from . import catalog as cat
    from . import generate as gen
    from ._contract import (
        FINDING_HOPPER_REFUSED,
        FINDING_PACKAGE_EXEC,
        LrdRefusal,
        bind_import_twin,
        dumps_exact_json,
    )
else:
    _PIPELINES = Path(__file__).resolve().parents[1]
    if str(_PIPELINES) not in sys.path:
        sys.path.insert(0, str(_PIPELINES))
    from lrd import catalog as cat
    from lrd import generate as gen
    from lrd._contract import (
        FINDING_HOPPER_REFUSED,
        FINDING_PACKAGE_EXEC,
        LrdRefusal,
        bind_import_twin,
        dumps_exact_json,
    )

__all__ = ["build_parser", "run"]

BANNED_IMPORTS = frozenset({"subprocess", "hopper"})
BANNED_DEFS = frozenset({"txn", "mill_and_publish"})


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="lrd.cli", description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)

    check = commands.add_parser("catalog-check", help="load the pinned catalog and verify pins")
    check.add_argument("--catalog", type=Path, default=None)
    check.add_argument("--json", action="store_true")

    gen_cmd = commands.add_parser("generate", help="episode pairs into a new directory")
    gen_cmd.add_argument("--catalog", type=Path, default=None)
    gen_cmd.add_argument("--out", type=Path, required=True)
    gen_cmd.add_argument("--plant", default=None, help="exact plant_id (mill_id:slug)")
    gen_cmd.add_argument("--mill", default=None, help="one mill_id, every pair in order")
    gen_cmd.add_argument("--all", action="store_true", help="every pair in the catalog")
    gen_cmd.add_argument("--round", type=int, default=None, help="id round; only with --plant")
    gen_cmd.add_argument("--json", action="store_true")

    audit = commands.add_parser("audit", help="load catalog and scan the package for exec")
    audit.add_argument("--catalog", type=Path, default=None)
    audit.add_argument("--json", action="store_true")
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
    text = (
        f"generated {summary['records']} records "
        f"({summary['pairs']} pairs) into {args.out}"
    )
    _emit({"command": "generate", "status": "ok", "summary": summary}, args.json, text)
    return 0


def _scan_exec_surface() -> list[dict[str, Any]]:
    """AST-scan every module under pipelines/lrd/ for hopper/exec primitives."""

    findings: list[dict[str, Any]] = []
    package_dir = Path(__file__).resolve().parent
    for path in sorted(package_dir.glob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    head = alias.name.split(".")[0]
                    if head in BANNED_IMPORTS:
                        code = (
                            FINDING_HOPPER_REFUSED if head == "hopper" else FINDING_PACKAGE_EXEC
                        )
                        findings.append(
                            {
                                "file": path.name,
                                "code": code,
                                "name": alias.name,
                                "line": node.lineno,
                            }
                        )
            elif isinstance(node, ast.ImportFrom):
                if node.module and node.module.split(".")[0] in BANNED_IMPORTS:
                    head = node.module.split(".")[0]
                    code = FINDING_HOPPER_REFUSED if head == "hopper" else FINDING_PACKAGE_EXEC
                    findings.append(
                        {"file": path.name, "code": code, "name": node.module, "line": node.lineno}
                    )
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if node.name in BANNED_DEFS:
                    code = (
                        FINDING_HOPPER_REFUSED
                        if node.name == "mill_and_publish"
                        else FINDING_PACKAGE_EXEC
                    )
                    findings.append(
                        {"file": path.name, "code": code, "name": node.name, "line": node.lineno}
                    )
    return findings


def _audit(args: argparse.Namespace) -> int:
    loaded = cat.load_catalog(_catalog_dir(args))
    findings = _scan_exec_surface()
    status = "findings" if findings else "ok"
    _emit(
        {
            "command": "audit",
            "status": status,
            "catalog_id": loaded.catalog_id,
            "plants": len(loaded.plants),
            "findings": findings,
        },
        args.json,
        f"audit {status}: {len(findings)} findings, {len(loaded.plants)} plants",
    )
    return 1 if findings else 0


def _refused(args: argparse.Namespace | None, refusal: LrdRefusal) -> int:
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


_COMMANDS = {"catalog-check": _catalog_check, "generate": _generate, "audit": _audit}


def run(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return _COMMANDS[args.command](args)
    except LrdRefusal as exc:
        return _refused(args, exc)


if __name__ == "__main__":
    raise SystemExit(run())
elif __package__:
    bind_import_twin(__name__)
