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
import hashlib
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
    errors += _check_stamp_binding(record, where)
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


def _check_stamp_binding(record: dict[str, Any], where: str) -> list[str]:
    """A stamped verdict must be formed over this exact record.

    The digest check proves the record was not edited; nothing invoked
    ``stamp_is_bound_to_content``, so a ``validation`` block lifted from
    another record — or carrying any well-formed 64-hex digest — stayed
    structurally valid despite the dedicated binding helper detecting it.
    """

    validation = record.get("validation")
    validator = validation.get("validator") if isinstance(validation, dict) else None
    if not isinstance(validator, dict):
        return []
    if validator.get("validated_digest") is None:
        return []
    if oc.stamp_is_bound_to_content(record):
        return []
    return [
        f"{where}: validation.validator.validated_digest is not the digest "
        "of this record's content — a stamped verdict must be formed over "
        "the exact record it rides on"
    ]


def jsonl_paths(root: Path) -> list[Path]:
    if root.is_file():
        return [root]
    return sorted(path for path in root.rglob("*.jsonl") if path.is_file())


def _finding(path, error: str) -> dict[str, Any]:
    return {"file": str(path), "line": 0, "error": error}


def _load_manifest_files(manifest_path: Path) -> tuple[dict[str, Any] | None, str | None]:
    """The manifest's ``files`` map, or the reason it cannot bind anything."""

    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        return None, f"MANIFEST.json cannot be read as JSON ({exc})"
    files = manifest.get("files") if isinstance(manifest, dict) else None
    if not isinstance(files, dict):
        return None, "MANIFEST.json does not carry a files object binding the run"
    return files, None


def _manifest_entry_errors(
    spec: Any, target: Path | None, relative: str, records: int
) -> list[str]:
    """One manifest entry against the file it claims to describe."""

    if target is None:
        return [f"MANIFEST.json lists {relative} but the run does not contain it"]
    if not isinstance(spec, dict):
        return [f"MANIFEST.json entry for {relative} must be an object"]
    errors: list[str] = []
    actual_sha256 = hashlib.sha256(target.read_bytes()).hexdigest()
    if spec.get("sha256") != actual_sha256:
        errors.append(
            f"MANIFEST.json binds {relative} to sha256 {spec.get('sha256')!r} "
            f"but the file hashes to {actual_sha256!r}"
        )
    if spec.get("records") != records:
        errors.append(
            f"MANIFEST.json binds {relative} to {spec.get('records')!r} "
            f"records but the file carries {records}"
        )
    return errors


def _manifest_findings(
    root: Path, paths: list[Path], records_per_file: dict[Path, int]
) -> list[dict[str, Any]]:
    """Reconcile a run manifest's file bindings with the scanned files.

    A run directory's ``MANIFEST.json`` binds each family batch to its path,
    record count and SHA-256. Nothing reconciled those bindings, so removing
    an expected batch — or changing one and rehashing its records — returned
    ``blocked: false`` while the committed manifest still described different
    bytes and totals.
    """

    manifest_path = root / "MANIFEST.json"
    if not root.is_dir() or not manifest_path.is_file():
        return []
    files, problem = _load_manifest_files(manifest_path)
    if files is None:
        return [_finding(manifest_path, problem)]
    findings: list[dict[str, Any]] = []
    scanned = {path.relative_to(root).as_posix(): path for path in paths}
    for relative in sorted(files, key=str):
        target = scanned.get(relative) if isinstance(relative, str) else None
        findings += [
            _finding(manifest_path, error)
            for error in _manifest_entry_errors(
                files[relative], target, relative, records_per_file.get(target, 0)
            )
        ]
    for relative in sorted(set(scanned) - set(files)):
        findings.append(
            _finding(
                manifest_path,
                f"{relative} is present in the run but MANIFEST.json does "
                "not bind it",
            )
        )
    return findings


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

    # An empty target is a failure, not a clean run. A typo in the path or a
    # generation step that produced nothing would otherwise be reported as
    # "0 records, 0 invalid" and exit zero. Appended before the report is
    # built, so the report's findings list carries them by construction
    # rather than through a shared-list alias a later copy would sever.
    if not paths:
        tally.findings.append(
            {"file": str(root), "line": 0, "error": "no .jsonl files found"}
        )
    elif not tally.records:
        tally.findings.append(
            {"file": str(root), "line": 0, "error": "no records found in any file"}
        )

    return {
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
        "blocked": bool(tally.findings)
        or (strict and tally.eligible < tally.valid),
        "_stamped": tally.stamped,
    }


def validate_path(root: Path, strict: bool = False, stamp: bool = False) -> dict[str, Any]:
    """Validate every record under ``root``. Returns a report dict."""

    if not root.exists():
        raise FileNotFoundError(f"no such path: {root}")
    paths = jsonl_paths(root)
    tally = _RunTally()
    records_per_file: dict[Path, int] = {}

    for path in paths:
        # Streamed, not buffered: memory stays bounded per record even when
        # a single batch is far larger than this process.
        for lineno, obj in oc.iter_jsonl(path):
            tally.records += 1
            records_per_file[path] = records_per_file.get(path, 0) + 1
            loc = _Location(path, lineno)
            if obj is None:
                tally.findings.append(
                    {"file": str(path), "line": lineno, "error": "JSON parse failure"}
                )
                continue
            _process_record(obj, loc, tally, stamp)

    tally.findings += _manifest_findings(root, paths, records_per_file)
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
