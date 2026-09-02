#!/usr/bin/env python3
"""Direct-CLI support for the composed-run implementation module."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Mapping

if __package__:
    from .compose_curated_run_bootstrap import (
        CLI_DESCRIPTION,
        ComposeCliServices,
        ComposeRunContext,
        ComposeRunHooks,
        compose_run,
        expose_run_adapter,
    )
else:
    from compose_curated_run_bootstrap import (
        CLI_DESCRIPTION,
        ComposeCliServices,
        ComposeRunContext,
        ComposeRunHooks,
        compose_run,
        expose_run_adapter,
    )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=CLI_DESCRIPTION)
    parser.add_argument("source_run", help="source run directory (read-only)")
    parser.add_argument("destination", help="new curated destination (must not exist)")
    parser.add_argument(
        "--units-migration",
        help="explicit reward calibration sidecar; defaults to the FFPC sidecar",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="exit 1 when the composed tree is not training_ready",
    )
    return parser.parse_args(argv)


def _print_strict_blockers(summary: Mapping[str, Any]) -> None:
    for blocker in summary["audit"]["blockers"]:
        print(f"blocker: {blocker}", file=sys.stderr)


def main(
    argv: list[str] | None, services: ComposeCliServices, hooks: ComposeRunHooks | None = None
) -> int:
    args = parse_args(argv)
    context = ComposeRunContext(
        Path(args.source_run),
        Path(args.destination),
        Path(args.units_migration) if args.units_migration is not None else None,
    )
    try:
        summary = compose_run(context, services.run, hooks)
    except services.caught_errors as exc:
        print(f"compose_curated: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    if args.strict and not summary["audit"]["training_ready"]:
        _print_strict_blockers(summary)
        return 1
    return 0


expose_run_adapter(__name__)
