#!/usr/bin/env python3
"""Validate VSET actor-provenance records against the #154 contract.

Stdlib-only. Existing factory pipelines import ``validate_record`` /
``run_oracle`` / ``validate_manifest``; this CLI is the operator surface.

Factory trust stays in ``config/FACTORY-REGISTRY.json`` (issue #32).
This module does not classify payload kinds for identity, does not
hard-code generator slugs, and does not write into ``outputs/raw/``.

``identity.unresolved_provenance`` (curate_identity / F-012 /
schemas/provenance.md) means a missing ``state.sim_or_real`` /
``state.provenance`` (designed|simulated|hil|unknown). It is not the
actor graph. Missing task_author / solver / reviewer / oracle keep
``vset.*`` codes; never reuse that identity reason here.

Usage:
  python3 pipelines/validate_vset.py <record.json|records-dir>
  python3 pipelines/validate_vset.py --oracle <record.json> --pack <repo-pack>
  python3 pipelines/validate_vset.py --manifest <manifest.json>
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

if __package__:  # pragma: no cover - package-child import path
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("validate_vset")
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "validate_vset"
    )

import vset_constants
import vset_manifest
import vset_manifest_entry_oracle
import vset_oracle
import vset_oracle_exec
import vset_patch
import vset_oracle_check
import vset_record_checks
import vset_record
import vset_source

ERR_ORACLE_EXECUTION_MISMATCH = vset_constants.ERR_ORACLE_EXECUTION_MISMATCH
IDENTITY_UNRESOLVED_PROVENANCE = vset_constants.IDENTITY_UNRESOLVED_PROVENANCE
MANIFEST_ROLES = vset_constants.MANIFEST_ROLES
VSetValidationError = vset_constants.VSetValidationError
iter_record_paths = vset_constants.iter_record_paths
pack_snapshot_hash = vset_constants.pack_snapshot_hash
registry_pin = vset_constants.registry_pin
summarize = vset_constants.summarize
_is_invalid_or_impossible = vset_manifest_entry_oracle.is_invalid_or_impossible
manifest_body_hash = vset_manifest.manifest_body_hash
manifest_entry_from_record = vset_manifest.manifest_entry_from_record
validate_manifest = vset_manifest.validate_manifest
validate_record_with_oracle = vset_oracle.validate_record_with_oracle
_execution_result_hash = vset_oracle_exec.execution_result_hash
_load_tests = vset_oracle_exec.load_tests
run_oracle = vset_oracle_exec.run_oracle
apply_patch = vset_patch.apply_patch
record_patch = vset_patch.record_patch
oracle_errors = vset_oracle_check.oracle_errors
load_json = vset_record_checks.load_json
validate_record = vset_record.validate_record
payload_errors = vset_source.payload_errors
source_kind_errors = vset_source.source_kind_errors

# Compatibility aliases for the pre-split private names.
_record_patch = record_patch
_oracle_errors = oracle_errors
_payload_errors = payload_errors
_source_kind_errors = source_kind_errors

# Public surface: tests and factory pipelines import these through
# ``import validate_vset as vset``; keep them re-exported here.
__all__ = [
    "IDENTITY_UNRESOLVED_PROVENANCE", "MANIFEST_ROLES", "VSetValidationError",
    "iter_record_paths", "load_json", "pack_snapshot_hash",
    "registry_pin", "summarize", "manifest_body_hash",
    "manifest_entry_from_record", "validate_manifest", "_is_invalid_or_impossible",
    "_execution_result_hash", "_load_tests", "apply_patch",
    "record_patch", "run_oracle", "validate_record_with_oracle",
    "oracle_errors", "validate_record", "payload_errors",
    "source_kind_errors", "parse_args", "main",
]


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate VSET actor-provenance records.")
    parser.add_argument("target", help="record JSON file or directory of records")
    parser.add_argument(
        "--oracle",
        action="store_true",
        help="execute deterministic fixture/reference tests when the record claims an oracle",
    )
    parser.add_argument(
        "--pack",
        help="repo-pack directory; required with --oracle and rejected without it",
    )
    parser.add_argument(
        "--require-registry-sha",
        action="store_true",
        help="require release.factory_registry_sha256 to match the reviewed registry bytes",
    )
    parser.add_argument(
        "--manifest",
        action="store_true",
        help="treat target as a vset-release-manifest-v1 document",
    )
    return parser.parse_args(argv)


def _print_errors(path: Path, errors: list[VSetValidationError]) -> None:
    for error in errors:
        print(f"ERROR: {path}: {error}", file=sys.stderr)


def _unreadable(path: Path, exc: Exception) -> VSetValidationError:
    """A file we cannot decode is a fail-closed record error, not a crash."""

    return VSetValidationError(
        "vset.record_not_object", f"unreadable JSON at {path}: {exc}"
    )


def _load_or_error(path: Path) -> tuple[Any, VSetValidationError | None]:
    try:
        return load_json(path), None
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        return None, _unreadable(path, exc)


def _run_manifest(target: Path) -> int:
    manifest, load_error = _load_or_error(target)
    errors = [load_error] if load_error is not None else validate_manifest(manifest)
    print(json.dumps({"path": str(target), **summarize(errors)}, indent=2))
    _print_errors(target, errors)
    return 1 if errors else 0


def _execution_summary(execution: dict[str, Any] | None) -> dict[str, Any]:
    if execution is None:
        return {}
    hidden = execution["hidden"]
    return {
        "oracle_execution": {
            "reference_ok": execution["reference"]["ok"],
            "hidden_ok": None if hidden is None else hidden["ok"],
            "result_hash": _execution_result_hash(execution),
        }
    }


def _one_record_report(
    path: Path, args: argparse.Namespace, pack: Path | None
) -> tuple[dict[str, Any], list[VSetValidationError]]:
    record, load_error = _load_or_error(path)
    if load_error is not None:
        return {"path": str(path), **summarize([load_error])}, [load_error]
    if args.oracle:
        if pack is None:
            raise VSetValidationError(
                ERR_ORACLE_EXECUTION_MISMATCH, "--oracle requires --pack"
            )
        errors, execution = validate_record_with_oracle(
            record, pack, require_registry_sha=args.require_registry_sha
        )
    else:
        errors = validate_record(record, require_registry_sha=args.require_registry_sha)
        execution = None
    item = {"path": str(path), **summarize(errors), **_execution_summary(execution)}
    return item, errors


def _run_records(target: Path, args: argparse.Namespace, pack: Path | None) -> int:
    """One unreadable record is a reported failure, never a lost report.

    A directory with no JSON inputs is not a quiet pass: validating an
    empty record set must fail closed so a wrong path is never read as
    an all-green run.
    """

    paths = iter_record_paths(target)
    if not paths:
        error = VSetValidationError(
            "vset.record_not_object", f"no JSON record inputs under {target}"
        )
        print(json.dumps({"records": [], "ok": False, **summarize([error])}, indent=2))
        _print_errors(target, [error])
        return 1
    reports = []
    failed = False
    for path in paths:
        item, errors = _one_record_report(path, args, pack)
        reports.append(item)
        if errors:
            failed = True
            _print_errors(path, errors)
    print(json.dumps({"records": reports, "ok": not failed}, indent=2))
    return 1 if failed else 0


_MANIFEST_OPTION_ERROR = "--manifest does not accept --oracle/--pack"


def _manifest_rejected(args: argparse.Namespace) -> bool:
    if not args.manifest:
        return False
    if args.oracle:
        return True
    return bool(args.pack)


def _option_error(args: argparse.Namespace) -> str | None:
    if _manifest_rejected(args):
        return _MANIFEST_OPTION_ERROR
    if args.oracle and not args.pack:
        return "--oracle requires --pack"
    if args.pack and not args.oracle:
        return "--pack requires --oracle"
    return None


def _usage_error(args: argparse.Namespace) -> str | None:
    option_error = _option_error(args)
    if option_error is not None:
        return option_error
    if not Path(args.target).exists():
        return f"not found: {args.target}"
    return None


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    error = _usage_error(args)
    if error is not None:
        print(error, file=sys.stderr)
        return 2
    target = Path(args.target)
    if args.manifest:
        return _run_manifest(target)
    pack = Path(args.pack) if args.pack else None
    return _run_records(target, args, pack)


if __package__:  # pragma: no cover - package-child import path
    _expose_package_sibling(__name__)


if __name__ == "__main__":
    raise SystemExit(main())
