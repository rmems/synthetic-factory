#!/usr/bin/env python3
"""Validate oracle-grounded distillation records (issue #78 families).

Routes each record to its family checker on top of the shared envelope in
``pipelines/oracle_contract.py``, then reports what is structurally valid and,
separately, what is actually curation-eligible. Structural validity is never
treated as training-readiness: a ``reference_only`` oracle produces valid
records that this tool refuses to call curation-eligible.

Prints a totals JSON to stdout and findings to stderr, like the other
validators in ``pipelines/``. Exits nonzero when any record has findings.

Usage::

    python3 pipelines/validate_distill.py <path> [--json] [--strict]
    python3 pipelines/validate_distill.py <path> --stamp-output <new.jsonl>

``<path>`` may be a single JSONL file or a directory scanned recursively.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Callable

_PIPELINES = Path(__file__).resolve().parent
if str(_PIPELINES) not in sys.path:
    sys.path.insert(0, str(_PIPELINES))

import energy_preferences  # noqa: E402
import fault_recovery  # noqa: E402
import moe_router  # noqa: E402
import oracle_contract as oc  # noqa: E402

VALIDATOR_NAME = "validate_distill"
VALIDATOR_VERSION = "1.0.0"

FAMILY_CHECKS: dict[str, Callable[[dict[str, Any], str], list[str]]] = {
    fault_recovery.FAMILY: fault_recovery.check_family,
    energy_preferences.FAMILY: energy_preferences.check_family,
    moe_router.FAMILY: moe_router.check_family,
}


def check_record(record: Any, where: str) -> list[str]:
    """Envelope + digest + family checks for one record."""

    errors = oc.check_envelope(record, where)
    if not isinstance(record, dict):
        return errors
    errors += oc.check_digest(record, where)
    family = record.get("family")
    # A JSON-valid record can carry an unhashable family (an array or an
    # object); using it as a dict key would raise instead of reporting.
    checker = FAMILY_CHECKS.get(family) if isinstance(family, str) else None
    if checker is None:
        if family not in oc.FAMILIES:
            # check_envelope already reported the unknown family.
            return errors
        errors.append(f"{where}: no family checker registered for {family!r}")
        return errors
    return errors + checker(record, where)


def jsonl_paths(root: Path) -> list[Path]:
    if root.is_file():
        return [root]
    return sorted(path for path in root.rglob("*.jsonl") if path.is_file())


class _Location:
    """Where a record came from, in both forms the report needs."""

    __slots__ = ("path", "lineno")

    def __init__(self, path: Path, lineno: int) -> None:
        self.path = path
        self.lineno = lineno

    @property
    def where(self) -> str:
        return f"{self.path}:{self.lineno}"


class _RunTally:
    """Everything accumulated across a run, in one place."""

    def __init__(self) -> None:
        self.findings: list[dict[str, Any]] = []
        self.families: Counter[str] = Counter()
        self.outcomes: Counter[str] = Counter()
        self.preferences: Counter[str] = Counter()
        self.ineligible: Counter[str] = Counter()
        self.seen_ids: dict[str, str] = {}
        self.records = 0
        self.valid = 0
        self.eligible = 0
        self.stamped: list[dict[str, Any]] = []

    def add_findings(self, loc: _Location, errors: list[str]) -> None:
        for error in errors:
            self.findings.append(
                {"file": str(loc.path), "line": loc.lineno, "error": error}
            )


def _duplicate_id_errors(obj: dict[str, Any], loc: _Location, tally: _RunTally) -> list[str]:
    """Record the id, or report it as already claimed by an earlier line."""

    record_id = obj.get("id")
    if not isinstance(record_id, str) or not record_id:
        return []
    if record_id in tally.seen_ids:
        return [
            f"{loc.where}: duplicate record id {record_id!r} "
            f"(first seen at {tally.seen_ids[record_id]})"
        ]
    tally.seen_ids[record_id] = loc.where
    return []


def _count_record_labels(obj: dict[str, Any], tally: _RunTally) -> None:
    """The census counters the report summarises."""

    family = obj.get("family")
    tally.families[family if isinstance(family, str) else "<unknown>"] += 1
    result = obj.get("result")
    if isinstance(result, dict):
        if isinstance(result.get("outcome"), str):
            tally.outcomes[result["outcome"]] += 1
        preference = result.get("preference")
        if isinstance(preference, dict) and isinstance(
            preference.get("preferred"), str
        ):
            tally.preferences[preference["preferred"]] += 1


def _record_eligibility(
    obj: dict[str, Any], errors: list[str], tally: _RunTally, stamp: bool
) -> None:
    """Validity, curation eligibility, and the optional validator stamp."""

    if not errors:
        tally.valid += 1
    # Eligibility is decided on the findings this validator just
    # produced, never on a validation block the record shipped with.
    ok, reasons = oc.curation_eligible(obj, errors)
    if ok:
        tally.eligible += 1
    elif not errors:
        for reason in reasons:
            tally.ineligible[reason] += 1
    if stamp:
        tally.stamped.append(
            oc.stamp_validation(
                obj,
                validator=VALIDATOR_NAME,
                version=VALIDATOR_VERSION,
                findings=errors,
            )
        )


def _process_record(obj: Any, loc: _Location, tally: _RunTally, stamp: bool) -> None:
    """Check one record and fold it into the tally, in emission order."""

    errors = check_record(obj, loc.where)
    if not isinstance(obj, dict):
        tally.add_findings(loc, errors)
        return
    errors += _duplicate_id_errors(obj, loc, tally)
    _count_record_labels(obj, tally)
    tally.add_findings(loc, errors)
    _record_eligibility(obj, errors, tally, stamp)


def _build_report(
    root: Path, paths: list[Path], tally: _RunTally, strict: bool
) -> dict[str, Any]:
    """Assemble the report, including the empty-target failures."""

    report = {
        "path": str(root),
        "files": len(paths),
        "records": tally.records,
        "valid": tally.valid,
        "invalid": tally.records - tally.valid,
        "curation_eligible": tally.eligible,
        "curation_ineligible_reasons": dict(sorted(tally.ineligible.items())),
        "families": dict(sorted(tally.families.items())),
        "fault_outcomes": dict(sorted(tally.outcomes.items())),
        "preferred_policies": dict(sorted(tally.preferences.items())),
        "findings": tally.findings,
        "strict": bool(strict),
        "validator": {"name": VALIDATOR_NAME, "version": VALIDATOR_VERSION},
    }
    # An empty target is a failure, not a clean run. A typo in the path or a
    # generation step that produced nothing would otherwise be reported as
    # "0 records, 0 invalid" and exit zero.
    if not paths:
        tally.findings.append(
            {"file": str(root), "line": 0, "error": "no .jsonl files found"}
        )
    elif not tally.records:
        tally.findings.append(
            {"file": str(root), "line": 0, "error": "no records found in any file"}
        )

    report["blocked"] = bool(tally.findings) or (strict and tally.eligible < tally.valid)
    report["_stamped"] = tally.stamped
    return report


def validate_path(root: Path, strict: bool = False, stamp: bool = False) -> dict[str, Any]:
    """Validate every record under ``root``. Returns a report dict."""

    if not root.exists():
        raise FileNotFoundError(f"no such path: {root}")
    paths = jsonl_paths(root)
    tally = _RunTally()

    for path in paths:
        for lineno, obj in oc.read_jsonl(path):
            tally.records += 1
            loc = _Location(path, lineno)
            if obj is None:
                tally.findings.append(
                    {"file": str(path), "line": lineno, "error": "JSON parse failure"}
                )
                continue
            _process_record(obj, loc, tally, stamp)

    return _build_report(root, paths, tally, strict)


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
