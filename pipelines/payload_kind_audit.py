#!/usr/bin/env python3
"""Read-only payload-kind audit for one published raw JSONL corpus.

A dataset slug names a *topic*; the records name a *shape*. When a Hub card
advertises one kind of record and the payload holds a mix, a consumer that
trusts the card writes a loader that crashes on the first record of the other
shape. This module measures the mix rather than asserting it: it walks one
corpus directory, classifies every record with the curation lane's own
:func:`curate_identity.record_kind`, and returns a deterministic audit.

It never writes to the corpus. The only output is JSON or Markdown on stdout.

Parse, Markdown, and scan helpers live in sibling modules
(``payload_kind_audit_parse``, ``payload_kind_audit_markdown``,
``payload_kind_audit_scan``) so each file's total complexity stays under the
qlty High threshold. Public callers still ``import payload_kind_audit``.

Usage::

    python3 pipelines/payload_kind_audit.py <corpus-dir> [--json|--markdown]
    python3 pipelines/payload_kind_audit.py <corpus-dir> --expect <audit.json>

``--expect`` re-derives the audit and exits non-zero naming each field that has
drifted from a published audit, so a committed audit cannot quietly go stale.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Iterable, Mapping

sys.path.insert(0, str(Path(__file__).resolve().parent))

from curate_identity import LEGACY_ID_KEYS  # noqa: E402
from payload_kind_audit_markdown import render_markdown  # noqa: E402
from payload_kind_audit_parse import (  # noqa: E402
    PayloadKindAuditError,
    _parse_finite_float,
    _reject_duplicate_object_keys,
    _reject_json_constant,
    _reject_unpaired_surrogates,
    _resolve_payload_paths,
)
from payload_kind_audit_scan import (  # noqa: E402
    _AuditStats,
    _first_legacy_id,
    _scan_payload_file,
)

SCHEMA_VERSION = "1.0.0"

def build_audit(corpus: Path, payload_names: Iterable[str] | None = None) -> dict:
    """Return a deterministic audit of the whole corpus or one named snapshot."""
    corpus = Path(corpus)
    if corpus.is_symlink() or not corpus.is_dir():
        raise PayloadKindAuditError(f"not a readable corpus directory: {corpus}")

    payload_paths = _resolve_payload_paths(corpus, payload_names)

    files: list[dict] = []
    records: list[dict] = []
    stats = _AuditStats()
    for path in payload_paths:
        rows, file_summary = _scan_payload_file(path, stats)
        records.extend(rows)
        files.append(file_summary)

    if not records:
        raise PayloadKindAuditError(f"corpus contains no auditable records: {corpus}")

    return {
        "schema_version": SCHEMA_VERSION,
        "source": corpus.name,
        "summary": stats.summary(files=len(files), records=len(records)),
        "files": files,
        "records": records,
    }


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


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
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
    """Load and validate one ``--expect`` file, or raise ``PayloadKindAuditError``
    with the exact diagnostic ``main`` prints for each failure mode."""
    try:
        published = json.loads(
            path.read_text(encoding="utf-8"),
            object_pairs_hook=_reject_duplicate_object_keys,
            parse_constant=_reject_json_constant,
            parse_float=_parse_finite_float,
        )
        # A published audit may carry supplementary fields ``_drift`` never
        # compares (``card_disclosure.markdown``, for one). Validate the whole
        # document so an unpaired surrogate the corpus parser would reject is
        # a controlled input error here too, rather than an exit 0 blessing
        # evidence this tool could not itself have emitted.
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


def main(argv: list[str] | None = None) -> int:
    args = _build_arg_parser().parse_args(argv)

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


if __name__ == "__main__":
    raise SystemExit(main())
