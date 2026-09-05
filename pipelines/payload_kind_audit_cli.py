"""CLI and --expect drift helpers for the payload-kind audit."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Mapping

from payload_kind_audit_markdown import render_markdown
from payload_kind_audit_parse import (
    PayloadKindAuditError,
    _parse_finite_float,
    _reject_duplicate_object_keys,
    _reject_json_constant,
    _reject_unpaired_surrogates,
)


def _json_equal(left: Any, right: Any) -> bool:
    """Compare JSON values without Python's bool/int/float equivalence."""
    if type(left) is not type(right):
        return False
    if isinstance(left, dict):
        return left.keys() == right.keys() and all(
            _json_equal(left[key], right[key]) for key in left
        )
    if isinstance(left, list):
        return len(left) == len(right) and all(
            _json_equal(first, second) for first, second in zip(left, right)
        )
    return left == right


def _drift(derived: Mapping[str, Any], published: Mapping[str, Any]) -> list[str]:
    problems = []
    for key, value in derived.items():
        if key not in published:
            problems.append(f"published audit is missing {key!r}")
        elif not _json_equal(published[key], value):
            problems.append(f"{key} differs from the published audit")
    return problems


def _snapshot_payload_names(published: Mapping[str, Any]) -> list[str]:
    files = published.get("files")
    if not isinstance(files, list) or not files:
        raise PayloadKindAuditError("published audit files must be a non-empty array")
    names = []
    for index, entry in enumerate(files):
        if not isinstance(entry, Mapping) or not isinstance(entry.get("path"), str):
            raise PayloadKindAuditError(f"published audit files[{index}].path must be a string")
        names.append(entry["path"])
    return names


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


def _load_expected_audit(path: Path) -> tuple[dict, list[str]]:
    """Load and validate one ``--expect`` file, or raise ``PayloadKindAuditError``."""
    try:
        published = json.loads(
            path.read_text(encoding="utf-8"),
            object_pairs_hook=_reject_duplicate_object_keys,
            parse_constant=_reject_json_constant,
            parse_float=_parse_finite_float,
        )
        # A published audit may carry supplementary fields ``_drift`` never
        # compares. Validate the whole document so unpaired surrogates are
        # controlled input errors rather than an exit 0 blessing.
        _reject_unpaired_surrogates(published)
    except (OSError, UnicodeError, ValueError, RecursionError) as exc:
        raise PayloadKindAuditError(f"cannot read {path}: {exc}") from exc
    if not isinstance(published, dict):
        raise PayloadKindAuditError(f"{path} is not a JSON object")
    try:
        payload_names = _snapshot_payload_names(published)
    except PayloadKindAuditError as exc:
        raise PayloadKindAuditError(f"cannot use {path}: {exc}") from exc
    return published, payload_names


def _report_drift(audit: Mapping[str, Any], published: Mapping[str, Any], corpus: Path) -> int:
    problems = _drift(audit, published)
    if problems:
        for problem in problems:
            print(f"DRIFT  {problem}", file=sys.stderr)
        return 1
    print(f"published audit matches a fresh scan of {corpus}")
    return 0


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
            published, payload_names = _load_expected_audit(args.expect)
        except PayloadKindAuditError as exc:
            print(str(exc), file=sys.stderr)
            return 2

    try:
        audit = build_audit(args.corpus, payload_names=payload_names)
    except PayloadKindAuditError as exc:
        print(f"payload-kind audit failed: {exc}", file=sys.stderr)
        return 2

    if published is not None:
        return _report_drift(audit, published, args.corpus)

    _emit_audit(audit, markdown=args.markdown)
    return 0
