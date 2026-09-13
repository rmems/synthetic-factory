"""CLI entry for the payload-kind audit."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Mapping

from payload_kind_audit_expect import load_expected_audit, report_drift
from payload_kind_audit_markdown import render_markdown
from payload_kind_audit_parse import PayloadKindAuditError


def _build_arg_parser(description: str) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("corpus", type=Path, help="directory of published *.jsonl")
    output = parser.add_mutually_exclusive_group()
    output.add_argument("--json", action="store_true", help="emit the full JSON audit (default)")
    output.add_argument("--markdown", action="store_true", help="emit the record table")
    parser.add_argument(
        "--expect",
        type=Path,
        default=None,
        help="compare against a published audit JSON and fail on drift",
    )
    return parser


def _emit_audit(audit: Mapping[str, Any], *, markdown: bool) -> None:
    if markdown:
        sys.stdout.write(render_markdown(audit))
    else:
        json.dump(audit, sys.stdout, indent=2, sort_keys=False, allow_nan=False)
        sys.stdout.write("\n")


def run_main(build_audit, description: str, argv: list[str] | None = None) -> int:
    """CLI entry used by ``payload_kind_audit.main``."""
    args = _build_arg_parser(description).parse_args(argv)

    published = None
    payload_names = None
    if args.expect is not None:
        try:
            published, payload_names = load_expected_audit(args.expect)
        except PayloadKindAuditError as exc:
            print(str(exc), file=sys.stderr)
            return 2

    try:
        audit = build_audit(args.corpus, payload_names=payload_names)
    except PayloadKindAuditError as exc:
        print(f"payload-kind audit failed: {exc}", file=sys.stderr)
        return 2

    if published is not None:
        return report_drift(audit, published, args.corpus)

    _emit_audit(audit, markdown=args.markdown)
    return 0
