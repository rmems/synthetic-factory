#!/usr/bin/env python3
"""Per-record checks and the report builder for distillation validation.

Owns the family-check map, ``check_record`` routing, the run tallies, and
``validate_path`` itself.
"""

from __future__ import annotations

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
from oracle_grounded import distill_contract as oc  # noqa: E402

if __package__:
    from .distill_manifest import _manifest_findings, jsonl_paths
else:
    from distill_manifest import _manifest_findings, jsonl_paths

VALIDATOR_NAME = "validate_distill"
VALIDATOR_VERSION = "1.0.0"

FAMILY_CHECKS: dict[str, Callable[[dict[str, Any], str], list[str]]] = {
    fault_recovery.FAMILY: fault_recovery.check_family,
    energy_preferences.FAMILY: energy_preferences.check_family,
    moe_router.FAMILY: moe_router.check_family,
}

# The families this validator owns. `oc.FAMILIES` is the envelope's whole
# vocabulary and is deliberately wider: `python-function-repair` also rides
# the envelope, and its run validator is `pipelines/code_repair/`. A record
# of an envelope family with no checker here is reported, never passed --
# see `check_record`.
DISTILLATION_FAMILIES = frozenset(FAMILY_CHECKS)

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

    tally.findings += _manifest_findings(root, paths, records_per_file, tally)
    return _build_report(root, paths, tally, strict)


