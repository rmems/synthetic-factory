#!/usr/bin/env python3
"""Manifest-side checks for oracle-grounded distillation runs.

Binds a run directory's ``MANIFEST.json`` to the JSONL files actually
present and reconciles the manifest's validation summary against the
tallies the record pass just computed.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any

_PIPELINES = Path(__file__).resolve().parent
if str(_PIPELINES) not in sys.path:
    sys.path.insert(0, str(_PIPELINES))

from oracle_grounded import distill_contract as oc  # noqa: E402

def jsonl_paths(root: Path) -> list[Path]:
    if root.is_file():
        return [root]
    return sorted(path for path in root.rglob("*.jsonl") if path.is_file())


def _finding(path, error: str) -> dict[str, Any]:
    return {"file": str(path), "line": 0, "error": error}


def _load_manifest_files(manifest_path: Path) -> tuple[dict[str, Any] | None, str | None]:
    """The manifest's ``files`` map, or the reason it cannot bind anything."""

    try:
        # manifest_path is root / "MANIFEST.json" inside the run the operator
        # named; reading that manifest is the validator's purpose.
        manifest = json.loads(  # NOSONAR
            manifest_path.read_text(encoding="utf-8")  # NOSONAR
        )
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
    digest = hashlib.sha256()
    with target.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    actual_sha256 = digest.hexdigest()
    if spec.get("sha256") != actual_sha256:
        errors.append(
            f"MANIFEST.json binds {relative} to sha256 {spec.get('sha256')!r} "
            f"but the file hashes to {actual_sha256!r}"
        )
    declared_records = spec.get("records")
    if not (
        isinstance(declared_records, int)
        and not isinstance(declared_records, bool)
        and declared_records == records
    ):
        # `true` and `1.0` both equal 1 under Python equality, so a boolean or
        # float count would pass — the manifest must bind a genuine integer.
        errors.append(
            f"MANIFEST.json binds {relative} to {spec.get('records')!r} "
            f"records but the file carries {records}"
        )
    return errors


def _manifest_findings(
    root: Path,
    paths: list[Path],
    records_per_file: dict[Path, int],
    tally: _RunTally | None = None,
) -> list[dict[str, Any]]:
    """Reconcile a run manifest's file bindings and summary with the run.

    A run directory's ``MANIFEST.json`` binds each family batch to its path,
    record count and SHA-256. Nothing reconciled those bindings, so removing
    an expected batch — or changing one and rehashing its records — returned
    ``blocked: false`` while the committed manifest still described different
    bytes and totals. The ``validation`` summary is reconciled the same way:
    a manifest claiming different totals than the freshly accumulated tally
    hands consumers a validation-clean run that its own manifest disproves.
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
    if tally is not None:
        findings += _manifest_summary_findings(manifest_path, tally)
    return findings


def _manifest_summary_findings(
    manifest_path: Path, tally: _RunTally
) -> list[dict[str, Any]]:
    """Findings for a manifest validation summary that disagrees with the run."""

    try:
        # manifest_path is root / "MANIFEST.json" inside the run the operator
        # named; reading that manifest is the validator's purpose.
        manifest = json.loads(
            manifest_path.read_text(encoding="utf-8")  # NOSONAR
        )
    except (OSError, ValueError):
        return []  # an unreadable manifest is already a finding upstream
    if not isinstance(manifest, dict):
        return []
    validation = manifest.get("validation")
    if not isinstance(validation, dict):
        return []
    actual = {
        "records": tally.records,
        "valid": tally.valid,
        "invalid": tally.records - tally.valid,
        "curation_eligible": tally.eligible,
        "curation_ineligible_reasons": dict(sorted(tally.ineligible.items())),
        "families": dict(sorted(tally.families.items())),
        "fault_outcomes": dict(sorted(tally.outcomes.items())),
        "preferred_policies": dict(sorted(tally.preferences.items())),
    }
    return [
        _finding(
            manifest_path,
            f"MANIFEST.json validation.{field} is {validation[field]!r} but the "
            f"scanned run tallies {actual[field]!r}",
        )
        for field in sorted(actual)
        # Canonical-JSON comparison: Python's == conflates true with 1.0, so a
        # manifest could claim a boolean where the tally is a number.
        if field in validation
        and oc.canonical_json(validation[field]) != oc.canonical_json(actual[field])
    ]


