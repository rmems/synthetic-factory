#!/usr/bin/env python3
"""The `nir_equivalence.py` command line: availability, generate, validate,
training-view.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

if __package__:
    # Import-twin helpers join the package import lock; import-order tests cover this edge.
    from . import _assert_direct_sibling, _expose_package_sibling  # pylint: disable=cyclic-import

    _assert_direct_sibling("nir_equivalence_cli")
    from .oracle_grounded.parity_jsonl import read_jsonl, write_jsonl  # noqa: E402,F401
    from .nir_equivalence_catalog import MINIMUM_STEPS  # noqa: E402
    from .nir_equivalence_record import generate_records  # noqa: E402
    from .nir_equivalence_runtimes import availability_report  # noqa: E402
    from .nir_equivalence_terms import (  # noqa: E402
        FACTORY_SLUG,
        contract,
    )
    from .nir_equivalence_validate_result import validate_records  # noqa: E402
    from .nir_equivalence_views import build_training_views  # noqa: E402
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "nir_equivalence_cli"
    )
    from oracle_grounded.parity_jsonl import read_jsonl, write_jsonl  # noqa: E402,F401
    from nir_equivalence_catalog import MINIMUM_STEPS  # noqa: E402
    from nir_equivalence_record import generate_records  # noqa: E402
    from nir_equivalence_runtimes import availability_report  # noqa: E402
    from nir_equivalence_terms import (  # noqa: E402
        FACTORY_SLUG,
        contract,
    )
    from nir_equivalence_validate_result import validate_records  # noqa: E402
    from nir_equivalence_views import build_training_views  # noqa: E402

def _window_steps(text):
    """`--steps`: an integer no shorter than the catalog's divergence window.

    Checked here, at the argument boundary, so `generate` never builds a
    round whose window is too short to show the divergences it catalogues.
    """
    try:
        steps = int(text)
    except ValueError:
        raise argparse.ArgumentTypeError(f"steps must be an integer, got {text!r}") from None
    if steps < MINIMUM_STEPS:
        raise argparse.ArgumentTypeError(
            f"steps must be >= {MINIMUM_STEPS}; a shorter window reports catalogued "
            "divergences as matches [WINDOW_TOO_SHORT]"
        )
    return steps


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("availability", help="report which runtimes can execute here")
    gen = sub.add_parser("generate", help="write one round of cross-runtime records")
    gen.add_argument("out_dir")
    gen.add_argument("--round", type=int, default=1)
    gen.add_argument("--steps", type=_window_steps, default=10)
    val = sub.add_parser("validate", help="validate a JSONL file of records")
    val.add_argument("path")
    view = sub.add_parser("training-view", help="emit training views for a JSONL file")
    view.add_argument("path")
    return parser.parse_args(argv)


def _print_errors(errors):
    """Report findings on stderr, one per line, in the order given."""
    for error in errors:
        print("ERROR:", error, file=sys.stderr)


def _cmd_generate(args):
    """Write one validated round, refusing raw-tree destinations and overwrites."""
    out = Path(args.out_dir) / FACTORY_SLUG / f"batch-r{args.round:02d}.jsonl"
    raw_error = contract.raw_tree_destination_error(out)
    if raw_error:
        print(f"nir_equivalence: {raw_error}", file=sys.stderr)
        return 2
    if out.exists():
        print(
            f"nir_equivalence: refusing to overwrite existing round {out}",
            file=sys.stderr,
        )
        return 2
    records = generate_records(round_number=args.round, steps=args.steps)
    errors = validate_records(records, source="generated")
    if errors:
        _print_errors(errors)
        print("nir_equivalence: refusing to write invalid records", file=sys.stderr)
        return 1
    try:
        write_jsonl(out, records)
    except FileExistsError:
        print(
            f"nir_equivalence: refusing to overwrite existing round {out}",
            file=sys.stderr,
        )
        return 2
    verdicts = {}
    for record in records:
        verdict = record["result"]["verdict"]
        verdicts[verdict] = verdicts.get(verdict, 0) + 1
    print(json.dumps({"written": str(out), "records": len(records),
                      "by_verdict": verdicts}, indent=2, sort_keys=True))
    return 0


def _cmd_validate(records, parse_errors, source):
    errors = parse_errors + validate_records(records, source=source)
    print(json.dumps({"records": len(records), "errors": len(errors)}, indent=2))
    _print_errors(errors)
    return 1 if errors else 0


def _cmd_training_view(records, parse_errors, source):
    views, errors = build_training_views(records, source=source)
    if parse_errors or errors:
        _print_errors(parse_errors + errors)
        return 1
    for view in views:
        print(json.dumps(view, sort_keys=True))
    return 0


def main(argv=None):
    args = parse_args(argv)
    if args.command == "availability":
        print(json.dumps(availability_report(), indent=2, sort_keys=True))
        return 0
    if args.command == "generate":
        return _cmd_generate(args)
    records, parse_errors = read_jsonl(args.path)
    if args.command == "validate":
        return _cmd_validate(records, parse_errors, Path(args.path).name)
    return _cmd_training_view(records, parse_errors, Path(args.path).name)


if __package__:
    _expose_package_sibling(__name__)
