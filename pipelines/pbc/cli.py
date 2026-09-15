#!/usr/bin/env python3
"""CLI for the PBC mill-usage-burst plan (read-only counts)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

if __package__:
    from .usage_burst_plan import PlanValidationError, load_mill_usage_burst_plan
else:
    _ROOT = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(_ROOT / "pipelines"))
    from pbc.usage_burst_plan import PlanValidationError, load_mill_usage_burst_plan


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="pbc_cli.py", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    plan = sub.add_parser("plan", help="load and print mill-usage-burst counts")
    plan.add_argument("--plan", type=Path, default=None)
    plan.add_argument("--json", action="store_true")
    return parser


def run(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "plan":
        try:
            loaded = load_mill_usage_burst_plan(args.plan)
        except PlanValidationError as exc:
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
                    "id": m.mill_id,
                    "plants_module": m.plants_module,
                    "start_round": m.start_round,
                    "end_round": m.end_round_inclusive,
                    "n_rounds": m.n_rounds,
                    "pair_count": m.pair_count,
                    "episodes": m.episodes,
                }
                for m in loaded.mills
            ],
        }
        if args.json:
            print(json.dumps(payload, indent=2, sort_keys=True))
        else:
            counts = payload["counts"]
            print(
                f"slice {loaded.slice} {loaded.label}: "
                f"{counts['mills']} mills, {counts['rounds']} rounds, "
                f"{counts['episodes']} episodes"
            )
        return 0
    return 2


def main() -> None:
    raise SystemExit(run())


if __name__ == "__main__":
    main()
