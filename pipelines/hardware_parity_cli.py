#!/usr/bin/env python3
"""The `hardware_parity.py` command line: availability, generate, validate, training-view.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

if __package__:
    # Import-twin helpers join the package import lock; import-order tests cover this edge.
    from . import _assert_direct_sibling, _expose_package_sibling  # pylint: disable=cyclic-import

    _assert_direct_sibling("hardware_parity_cli")
    from . import neuro_oracle  # noqa: E402
    from .neuro_oracle import (  # noqa: E402
        FixedPointReferenceAdapter,
        RecordedCaptureAdapter,
        get_adapter,
    )
    from .oracle_grounded.parity_jsonl import read_jsonl, write_jsonl  # noqa: E402,F401
    from .hardware_parity_terms import (  # noqa: E402
        FACTORY_SLUG,
        contract,
    )
    from .hardware_parity_record import generate_records  # noqa: E402
    from .hardware_parity_validate_result import validate_records  # noqa: E402
    from .hardware_parity_views import build_training_views  # noqa: E402
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "hardware_parity_cli"
    )
    import neuro_oracle  # noqa: E402
    from neuro_oracle import (  # noqa: E402
        FixedPointReferenceAdapter,
        RecordedCaptureAdapter,
        get_adapter,
    )
    from oracle_grounded.parity_jsonl import read_jsonl, write_jsonl  # noqa: E402,F401
    from hardware_parity_terms import (  # noqa: E402
        FACTORY_SLUG,
        contract,
    )
    from hardware_parity_record import generate_records  # noqa: E402
    from hardware_parity_validate_result import validate_records  # noqa: E402
    from hardware_parity_views import build_training_views  # noqa: E402

def availability_report(**kwargs):
    """The oracle's availability probe, resolved through its module each call."""
    return neuro_oracle.availability_report(**kwargs)



_ERROR_PREFIX = "ERROR:"


def _load_deployment_adapter(target, capture):
    if capture:
        return RecordedCaptureAdapter(capture)
    if target is None or target == FixedPointReferenceAdapter.name:
        return FixedPointReferenceAdapter()
    if target == RecordedCaptureAdapter.name:
        raise KeyError(f"target {target!r} requires --capture PATH")
    return get_adapter(target)


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("availability", help="report which oracles can execute here")
    gen = sub.add_parser("generate", help="write one round of paired records")
    gen.add_argument("out_dir")
    gen.add_argument("--round", type=int, default=1)
    gen.add_argument("--steps", type=int, default=12)
    gen.add_argument("--repeats", type=int, default=3)
    gen.add_argument("--target", default=None, help="deployment-side adapter name")
    gen.add_argument("--capture", default=None, help="recorded hardware capture JSON")
    val = sub.add_parser("validate", help="validate a JSONL file of records")
    val.add_argument("path")
    view = sub.add_parser("training-view", help="emit training views for a JSONL file")
    view.add_argument("path")
    return parser.parse_args(argv)


def _cmd_generate(args):
    """Write one validated round, refusing bad arguments and overwrites."""
    if args.steps < 1:
        print(
            f"hardware_parity: --steps must be a positive integer, got {args.steps}",
            file=sys.stderr,
        )
        return 2
    out = Path(args.out_dir) / FACTORY_SLUG / f"batch-r{args.round:02d}.jsonl"
    raw_error = contract.raw_tree_destination_error(out)
    if raw_error:
        print(f"hardware_parity: {raw_error}", file=sys.stderr)
        return 2
    if out.exists():
        print(
            f"hardware_parity: refusing to overwrite existing round {out}",
            file=sys.stderr,
        )
        return 2
    try:
        adapter = _load_deployment_adapter(args.target, args.capture)
    except (KeyError, TypeError) as exc:
        print(f"hardware_parity: {exc}", file=sys.stderr)
        return 2
    records = generate_records(
        round_number=args.round,
        steps=args.steps,
        deployment_adapter=adapter,
        repeats=args.repeats,
    )
    errors = validate_records(records, source="generated")
    if errors:
        for error in errors:
            print(_ERROR_PREFIX, error, file=sys.stderr)
        print("hardware_parity: refusing to write invalid records", file=sys.stderr)
        return 1
    try:
        write_jsonl(out, records)
    except FileExistsError:
        print(
            f"hardware_parity: refusing to overwrite existing round {out}",
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
    for error in errors:
        print(_ERROR_PREFIX, error, file=sys.stderr)
    return 1 if errors else 0


def _cmd_training_view(records, parse_errors, source):
    views, errors = build_training_views(records, source=source)
    if parse_errors or errors:
        for error in parse_errors + errors:
            print(_ERROR_PREFIX, error, file=sys.stderr)
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
