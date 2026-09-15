#!/usr/bin/env python3
"""CLI for the API contract-migration family.

Read-only: print or write an AST-extracted catalog. This command does not
reserve or publish a raw round, and it refuses to vendor ``acm-mill*.py``.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

if __package__:
    from . import catalog
    from . import generate
    from ._contract import bind_import_twin, refuse_vendor_paths
else:
    _ROOT = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(_ROOT / "pipelines"))
    from acm import catalog  # type: ignore[no-redef]
    from acm import generate  # type: ignore[no-redef]
    from acm._contract import bind_import_twin, refuse_vendor_paths  # type: ignore[no-redef]

__all__ = ["build_parser", "main", "run"]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="acm", description=__doc__)
    parser.add_argument("source", type=Path, help="legacy tree that holds the mill scripts")
    parser.add_argument("--write", type=Path, default=None, help="new catalog directory")
    return parser


def run(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    payload = generate.extract_tree(args.source)
    if args.write is None:
        print(catalog.dumps_catalog(payload), end="")
        return
    dest = args.write.resolve()
    dest.mkdir(parents=True, exist_ok=False)
    refuse_vendor_paths(dest.rglob("*"))
    catalog.write_catalog(dest, payload)
    refuse_vendor_paths(dest.rglob("*"))
    print(catalog.dumps_catalog({"row_count": payload["row_count"], "path": str(dest)}))


def main() -> None:
    run()
    raise SystemExit(0)


if __name__ == "__main__":
    main()

bind_import_twin(__name__)
