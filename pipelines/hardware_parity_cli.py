#!/usr/bin/env python3
"""The `hardware_parity.py` command line: availability, generate, validate, training-view.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_PIPELINES = Path(__file__).resolve().parent
if str(_PIPELINES) not in sys.path:
    sys.path.insert(0, str(_PIPELINES))

import neuro_oracle  # noqa: E402
from neuro_oracle import (  # noqa: E402
    FixedPointReferenceAdapter,
    Path,
    RecordedCaptureAdapter,
    get_adapter,
)
from exact_json import dumps_exact_json  # noqa: E402
from hardware_parity_terms import (  # noqa: E402
    FACTORY_SLUG,
    contract,
)
from hardware_parity_record import generate_records  # noqa: E402
from hardware_parity_validate_result import validate_records  # noqa: E402
from hardware_parity_views import build_training_views  # noqa: E402

# `availability_report` is read off the `neuro_oracle` module at call time, not
# bound at import, because it is a live probe of this host: tests fake an
# available FPGA by patching `neuro_oracle.availability_report`, and a bound
# copy here would keep answering the real one. The same reason the validator
# re-probes rather than trusting a record's snapshot.
def availability_report(**kwargs):
    """The oracle's availability probe, resolved through its module each call."""
    return neuro_oracle.availability_report(**kwargs)



_ERROR_PREFIX = "ERROR:"


def read_jsonl(path):
    records = []
    errors = []
    source = Path(path)
    try:
        text = source.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        return [], [f"{source}: cannot read file: {exc}"]
    for lineno, raw_line in enumerate(text.split("\n"), 1):
        line = raw_line[:-1] if raw_line.endswith("\r") else raw_line
        if not line.strip():
            continue
        try:
            records.append(
                json.loads(
                    line,
                    parse_constant=contract.reject_json_constant,
                    parse_float=contract.reject_nonfinite_float,
                )
            )
        # ValueError covers json.JSONDecodeError, which derives from it, and
        # the non-finite/constant refusals the two parse hooks raise directly.
        # RecursionError: a syntactically valid but absurdly nested line must
        # be a line-level parse error, not a traceback that aborts the scan.
        except (ValueError, RecursionError) as exc:
            errors.append(f"{Path(path).name}:{lineno}: JSON parse error: {exc}")
    return records, errors


def write_jsonl(path, records):
    """Write one round as JSONL, through the repository's exact encoder.

    `dumps_exact_json`, not `json.dumps`: a round file is evidence other
    tools digest, and `json.dumps` renders an `ExactJSONFloat` through
    `repr`, silently dropping the decimal token it was read with. Nothing in
    these families produces such a value today, so this changes no number
    now; it keeps the writer honest if one ever reaches it. Its compact form
    also makes each written line the same text `contract.canonical_json`
    hashes, rather than a spaced variant of it.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = "".join(
        dumps_exact_json(record, ensure_ascii=False, sort_keys=True) + "\n"
        for record in records
    )
    with path.open("x", encoding="utf-8") as handle:
        handle.write(payload)


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
