#!/usr/bin/env python3
"""Distributed-lock mill introspection commands.

Three read-only subcommands over the cleaned ``config/dlk/`` catalog and the
pure builders in :mod:`.generate`:

* ``catalog`` -- print the pinned catalog index (preserved rounds, plant
  counts and sha256 prefixes).
* ``show``   -- build one episode (or its NOTES) in memory for a round and a
  plant index/slug and print it. Nothing is written and nothing is executed.
* ``audit``  -- load every preserved round, refuse a sha256 drift, a duplicate
  or cross-round slug, or a factory/generator mismatch, and scan the package
  source for the exec primitives the legacy scripts carried (``subprocess``,
  ``txn``, ``main``). Findings exit 1; a clean audit exits 0.

This CLI never imports ``subprocess`` and never publishes a raw round. The
legacy ``txn``/``main`` exec path is not reproduced anywhere in this package.

Exit codes: 0 ok, 1 audit findings, 2 usage error.
"""

from __future__ import annotations

import argparse
import ast
import sys
from pathlib import Path
from typing import Any

if __package__:
    from . import _contract as c
    from . import catalog as cat
    from . import generate
    from ._contract import bind_import_twin
else:  # direct execution: python3 pipelines/dlk/cli.py
    _pipelines = Path(__file__).resolve().parents[1]
    if str(_pipelines) not in sys.path:
        sys.path.insert(0, str(_pipelines))
    from dlk import _contract as c
    from dlk import catalog as cat
    from dlk import generate
    from dlk._contract import bind_import_twin

__all__ = ["build_parser", "run"]

# The exec surface the legacy scripts carried and the cleaned package must not.
# ``audit`` AST-scans every module under pipelines/dlk/ for these and fails if
# any appear: importing ``subprocess`` would let a builder shell out, and a
# ``txn``/``main`` definition is the publish path itself.
BANNED_IMPORTS = {"subprocess"}
BANNED_DEFS = {"txn", "main"}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="dlk", description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)

    catalog_cmd = commands.add_parser("catalog", help="print the pinned dlk catalog index")
    catalog_cmd.add_argument("--config-dir", type=Path, default=None,
                              help="override config/dlk path")

    show = commands.add_parser("show", help="build one episode in memory and print it")
    show.add_argument("--round", type=int, required=True, help="preserved round (e.g. 1214)")
    show.add_argument("--config-dir", type=Path, default=None, help="override config/dlk path")
    which = show.add_mutually_exclusive_group()
    which.add_argument("--index", type=int, help="plant index in the round (0-based)")
    which.add_argument("--slug", help="plant slug in the round")
    show.add_argument("--kind", choices=("success", "fail", "notes"), default="success",
                      help="what to build (default: success)")

    audit = commands.add_parser("audit", help="load every round and scan for exec primitives")
    audit.add_argument("--config-dir", type=Path, default=None, help="override config/dlk path")
    return parser


def _emit(payload: dict[str, Any], text: str) -> None:
    print(c.dumps_exact_json(payload, ensure_ascii=True, indent=2, sort_keys=True))


def _catalog(args: argparse.Namespace) -> int:
    index = cat.catalog_index(args.config_dir)
    plant_files = index["plant_files"]
    text_lines = [
        (f"dlk catalog: prefix={index['prefix']} factory={index['factory']} "
         f"generator={index['generator']} distinct_plants={index['distinct_plants']}"),
    ]
    for key in sorted(plant_files):
        entry = plant_files[key]
        text_lines.append(
            f"  r{entry['round']:04d}: {entry['plants']} plants "
            f"({entry['file']}, sha256={entry['sha256'][:12]}...)"
        )
    payload = {"command": "catalog", "status": "ok", "index": index}
    _emit(payload, "\n".join(text_lines))
    return 0


def _resolve_plant(catalog: cat.Catalog, args: argparse.Namespace) -> cat.Plant:
    if args.index is None and args.slug is None:
        raise SystemExit("show: --index or --slug is required")
    if args.index is not None:
        if not 0 <= args.index < len(catalog.plants):
            raise SystemExit(f"show: --index {args.index} out of range for r{catalog.round:04d}")
        return catalog.plants[args.index]
    return catalog.plant(args.slug)


def _show(args: argparse.Namespace) -> int:
    catalog = cat.load_catalog(args.round, args.config_dir)
    plant = _resolve_plant(catalog, args)
    if args.kind == "notes":
        s = generate.success_ep(catalog.round, plant)
        f = generate.fail_ep(catalog.round, plant)
        text = generate.notes(catalog.round, plant, s, f)
        print(text, end="")
        return 0
    builder = generate.success_ep if args.kind == "success" else generate.fail_ep
    record = builder(catalog.round, plant)
    _emit({"command": "show", "status": "ok", "record": record}, "")
    return 0


def _scan_exec_surface() -> list[dict[str, Any]]:
    """AST-scan every module under pipelines/dlk/ for the banned exec surface."""
    findings: list[dict[str, Any]] = []
    package_dir = Path(__file__).resolve().parent
    for path in sorted(package_dir.glob("*.py")):
        src = path.read_text(encoding="utf-8")
        tree = ast.parse(src, filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.split(".")[0] in BANNED_IMPORTS:
                        findings.append({"file": path.name, "code": "banned_import",
                                         "name": alias.name, "line": node.lineno})
            elif isinstance(node, ast.ImportFrom):
                if node.module and node.module.split(".")[0] in BANNED_IMPORTS:
                    findings.append({"file": path.name, "code": "banned_import",
                                     "name": node.module, "line": node.lineno})
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name in BANNED_DEFS:
                findings.append({"file": path.name, "code": "banned_def",
                                 "name": node.name, "line": node.lineno})
    return findings


def _audit(args: argparse.Namespace) -> int:
    findings: list[dict[str, Any]] = []
    try:
        catalogs = cat.load_all(args.config_dir)
    except (TypeError, ValueError, KeyError) as exc:
        refused = {"command": "audit", "status": "refused",
                    "findings": [{"code": "catalog_load", "detail": str(exc)}]}
        _emit(refused, "")
        return 2
    index = cat.catalog_index(args.config_dir)
    all_slugs: list[str] = []
    for catalog in catalogs:
        all_slugs.extend(catalog.slugs)
        if catalog.factory != c.FACTORY:
            findings.append({"code": "factory_mismatch", "round": catalog.round,
                              "factory": catalog.factory})
        if catalog.generator != c.GEN:
            findings.append({"code": "generator_mismatch", "round": catalog.round,
                              "generator": catalog.generator})
        if len(catalog.slugs) != len(set(catalog.slugs)):
            findings.append({"code": "duplicate_slug", "round": catalog.round})
    if len(all_slugs) != len(set(all_slugs)):
        findings.append({"code": "cross_round_slug_overlap"})
    if len(catalogs) != len(index["preserved_rounds"]):
        findings.append({"code": "round_count", "expected": len(index["preserved_rounds"]),
                         "got": len(catalogs)})
    findings.extend(_scan_exec_surface())
    payload = {
        "command": "audit", "status": "findings" if findings else "ok",
        "rounds": [cat.round for cat in catalogs], "plants": len(all_slugs),
        "findings": findings,
    }
    _emit(payload, "")
    return 1 if findings else 0


_COMMANDS = {"catalog": _catalog, "show": _show, "audit": _audit}


def run(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return _COMMANDS[args.command](args)


bind_import_twin(__name__)


if __name__ == "__main__":
    sys.exit(run())
