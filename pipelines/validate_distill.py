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
    checker = FAMILY_CHECKS.get(family)
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


def validate_path(root: Path, strict: bool = False, stamp: bool = False) -> dict[str, Any]:
    """Validate every record under ``root``. Returns a report dict."""

    if not root.exists():
        raise FileNotFoundError(f"no such path: {root}")
    paths = jsonl_paths(root)
    findings: list[dict[str, Any]] = []
    families: Counter[str] = Counter()
    outcomes: Counter[str] = Counter()
    preferences: Counter[str] = Counter()
    ineligible: Counter[str] = Counter()
    seen_ids: dict[str, str] = {}
    records = 0
    valid = 0
    eligible = 0
    stamped: list[dict[str, Any]] = []

    for path in paths:
        for lineno, obj in oc.read_jsonl(path):
            records += 1
            where = f"{path}:{lineno}"
            if obj is None:
                findings.append(
                    {"file": str(path), "line": lineno, "error": "JSON parse failure"}
                )
                continue
            errors = check_record(obj, where)
            if isinstance(obj, dict):
                record_id = obj.get("id")
                if isinstance(record_id, str) and record_id:
                    if record_id in seen_ids:
                        errors.append(
                            f"{where}: duplicate record id {record_id!r} "
                            f"(first seen at {seen_ids[record_id]})"
                        )
                    else:
                        seen_ids[record_id] = where
                families[str(obj.get("family"))] += 1
                result = obj.get("result")
                if isinstance(result, dict):
                    if isinstance(result.get("outcome"), str):
                        outcomes[result["outcome"]] += 1
                    preference = result.get("preference")
                    if isinstance(preference, dict) and isinstance(
                        preference.get("preferred"), str
                    ):
                        preferences[preference["preferred"]] += 1
                for error in errors:
                    findings.append({"file": str(path), "line": lineno, "error": error})
                if not errors:
                    valid += 1
                # Eligibility is decided on the findings this validator just
                # produced, never on a validation block the record shipped with.
                ok, reasons = oc.curation_eligible(obj, errors)
                if ok:
                    eligible += 1
                elif not errors:
                    for reason in reasons:
                        ineligible[reason] += 1
                if stamp:
                    stamped.append(
                        oc.stamp_validation(
                            obj,
                            validator=VALIDATOR_NAME,
                            version=VALIDATOR_VERSION,
                            findings=errors,
                        )
                    )
            else:
                for error in errors:
                    findings.append({"file": str(path), "line": lineno, "error": error})

    report = {
        "path": str(root),
        "files": len(paths),
        "records": records,
        "valid": valid,
        "invalid": records - valid,
        "curation_eligible": eligible,
        "curation_ineligible_reasons": dict(sorted(ineligible.items())),
        "families": dict(sorted(families.items())),
        "fault_outcomes": dict(sorted(outcomes.items())),
        "preferred_policies": dict(sorted(preferences.items())),
        "findings": findings,
        "strict": bool(strict),
        "validator": {"name": VALIDATOR_NAME, "version": VALIDATOR_VERSION},
    }
    report["blocked"] = bool(findings) or (strict and eligible < valid)
    report["_stamped"] = stamped
    return report


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
