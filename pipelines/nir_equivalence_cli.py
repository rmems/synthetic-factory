#!/usr/bin/env python3
"""The `nir_equivalence.py` command line: availability, generate, validate,
training-view.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from pathlib import Path  # noqa: E402
_PIPELINES = Path(__file__).resolve().parent

if __package__:
    # Import-twin helpers join the package import lock; import-order tests cover this edge.
    from . import _assert_direct_sibling, _expose_package_sibling  # pylint: disable=cyclic-import

    _assert_direct_sibling("nir_equivalence_cli")
    from .exact_json import dumps_exact_json  # noqa: E402
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
    if str(_PIPELINES) not in sys.path:
        sys.path.insert(0, str(_PIPELINES))
    from exact_json import dumps_exact_json  # noqa: E402
    from nir_equivalence_record import generate_records  # noqa: E402
    from nir_equivalence_runtimes import availability_report  # noqa: E402
    from nir_equivalence_terms import (  # noqa: E402
        FACTORY_SLUG,
        contract,
    )
    from nir_equivalence_validate_result import validate_records  # noqa: E402
    from nir_equivalence_views import build_training_views  # noqa: E402

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
        # RecursionError: a syntactically valid but absurdly nested line must
        # be a line-level parse error, not a traceback that aborts the scan.
        # json.JSONDecodeError and the reject_* hooks both raise ValueError.
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


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("availability", help="report which runtimes can execute here")
    gen = sub.add_parser("generate", help="write one round of cross-runtime records")
    gen.add_argument("out_dir")
    gen.add_argument("--round", type=int, default=1)
    gen.add_argument("--steps", type=int, default=10)
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
    try:
        records = generate_records(round_number=args.round, steps=args.steps)
    except ValueError as exc:
        print(f"nir_equivalence: {exc} [WINDOW_TOO_SHORT]", file=sys.stderr)
        return 2
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
