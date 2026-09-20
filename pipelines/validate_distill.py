#!/usr/bin/env python3
"""Validate oracle-grounded distillation records (issue #78 families).

Routes each record to its family checker on top of the distillation contract
in ``pipelines/oracle_grounded/distill_contract.py``, then reports what is
structurally valid and, separately, what is actually curation-eligible. The
three ``DISTILLATION_FAMILIES`` are the ones this tool checks; the other
families sharing the envelope carry their own run validators, and a record
of one reaching this tool is reported rather than waved through.
Structural validity is never treated as training-readiness: a
``reference_only`` oracle produces valid records that this tool refuses to
call curation-eligible.

Prints a totals JSON to stdout and findings to stderr, like the other
validators in ``pipelines/``. Exits nonzero when any record has findings.

Usage::

    python3 pipelines/validate_distill.py <path> [--json] [--strict]
    python3 pipelines/validate_distill.py <path> --stamp-output <new.jsonl>

``<path>`` may be a single JSONL file or a directory scanned recursively.


This module is the stable entry point and compatibility facade. The
implementation is split into responsibility-named siblings:

* ``distill_manifest.py`` -- MANIFEST.json binding and summary reconciliation.
* ``distill_records.py`` -- per-record checks, run tallies, ``validate_path``.

Every public name any of them defines is re-exported here, so existing
``import validate_distill`` call sites resolve unchanged.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

_PIPELINES = Path(__file__).resolve().parent
if str(_PIPELINES) not in sys.path:
    sys.path.insert(0, str(_PIPELINES))

from oracle_grounded import distill_contract as oc  # noqa: E402

if __package__:
    from . import distill_manifest as _distill_manifest
    from . import distill_records as _distill_records
    from .distill_records import validate_path
else:
    import distill_manifest as _distill_manifest
    import distill_records as _distill_records
    from distill_records import validate_path


def _reexport(module: Any, names: str) -> None:
    globals().update({name: getattr(module, name) for name in names.split()})


_reexport(
    _distill_manifest,
    """
    _load_manifest_files _manifest_entry_errors _manifest_findings
    _manifest_summary_findings
    """,
)
_reexport(
    _distill_records,
    """
    DISTILLATION_FAMILIES FAMILY_CHECKS VALIDATOR_NAME VALIDATOR_VERSION
    check_record jsonl_paths validate_path
    _check_stamp_binding _duplicate_id_errors _process_record
    """,
)

del _reexport, _distill_manifest, _distill_records


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("path", help="JSONL file or directory to validate")
    parser.add_argument("--json", action="store_true", help="emit the full report")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="also fail when a valid record is not curation-eligible",
    )
    parser.add_argument(
        "--stamp-output",
        help="write validator-stamped records to this new JSONL path",
    )
    args = parser.parse_args(argv)

    try:
        report = validate_path(Path(args.path), strict=args.strict, stamp=bool(args.stamp_output))
    except FileNotFoundError as exc:
        print(json.dumps({"error": str(exc)}, indent=2), file=sys.stderr)
        return 2

    stamped = report.pop("_stamped", [])

    # Report first. Writing the stamp output can fail (the destination must not
    # already exist), and losing the findings to that failure would be the
    # worst possible trade.
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        summary = {key: value for key, value in report.items() if key != "findings"}
        print(json.dumps(summary, indent=2, sort_keys=True))
    for finding in report["findings"]:
        print(
            f"INVALID: {finding['file']}:{finding['line']} — {finding['error']}",
            file=sys.stderr,
        )

    if args.stamp_output:
        try:
            oc.write_jsonl(args.stamp_output, stamped)
        except oc.ContractError as exc:
            print(f"stamp output not written: {exc}", file=sys.stderr)
            return 2
    return 1 if report["blocked"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
