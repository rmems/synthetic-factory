#!/usr/bin/env python3
"""CLI for the PBC mill-usage-burst catalog (read-only)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

if __package__:
    from . import catalog
    from ._contract import bind_import_twin
else:
    _ROOT = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(_ROOT / "pipelines"))
    from pbc import catalog  # type: ignore[no-redef]
    from pbc._contract import bind_import_twin  # type: ignore[no-redef]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="pbc_cli.py", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    plan = sub.add_parser("plan", help="load and print mill-usage-burst counts")
    plan.add_argument("--plan", type=Path, default=None)
    plan.add_argument("--json", action="store_true")
    sub.add_parser("catalog", help="load CATALOG.json + plants.jsonl and print pin counts")
    return parser


def run(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "plan":
        try:
            loaded = catalog.load_mill_usage_burst_plan(args.plan)
        except catalog.PlanValidationError as exc:
            print(str(exc), file=sys.stderr)
            return 2
        payload = {
            "family_prefix": loaded.family_prefix,
            "factory": loaded.factory,
            "slice": loaded.slice,
            "label": loaded.label,
            "run_label": loaded.run_label,
            "counts": loaded.counts(),
            "mills": [
                {
                    "id": mill.mill_id,
                    "source": mill.source,
                    "start_round": mill.start_round,
                    "end_round": mill.end_round_inclusive,
                    "n_rounds": mill.n_rounds,
                    "pair_count": mill.pair_count,
                    "full_n_rounds": mill.full_n_rounds,
                    "episodes": mill.episodes,
                }
                for mill in loaded.mills
            ],
        }
        if args.json:
            print(json.dumps(payload, indent=2, sort_keys=True))
        else:
            counts = payload["counts"]
            print(
                f"slice {loaded.slice} {loaded.label}: "
                f"{counts['mills']} mills, {counts['rounds']} committed rounds, "
                f"{counts['episodes']} episodes"
            )
        return 0
    if args.command == "catalog":
        try:
            loaded = catalog.load_catalog()
        except catalog.PlanValidationError as exc:
            print(str(exc), file=sys.stderr)
            return 2
        print(
            json.dumps(
                {
                    "catalog_id": loaded.catalog_id,
                    "row_count": len(loaded.pairs),
                    "plants_sha256": loaded.plants_sha256,
                    "mills": [mill.mill_id for mill in loaded.mills],
                },
                indent=2,
                sort_keys=True,
            )
        )
        return 0
    return 2


def main() -> None:
    raise SystemExit(run())


if __name__ == "__main__":
    main()

bind_import_twin(__name__)
