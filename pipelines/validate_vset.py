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

_PIPELINES = Path(__file__).resolve().parent
if str(_PIPELINES) not in sys.path:
    sys.path.insert(0, str(_PIPELINES))

from vset_constants import (  # noqa: E402
    IDENTITY_UNRESOLVED_PROVENANCE,
    MANIFEST_ROLES,
    VSetValidationError,
    iter_record_paths,
    load_json,
    pack_snapshot_hash,
    registry_pin,
    summarize,
)
from vset_manifest import (  # noqa: E402
    _is_invalid_or_impossible,
    manifest_body_hash,
    manifest_entry_from_record,
    validate_manifest,
)
from vset_oracle import (  # noqa: E402
    apply_patch,
    record_patch,
    run_oracle,
    validate_record_with_oracle,
)
from vset_oracle_check import oracle_errors  # noqa: E402
from vset_record import validate_record  # noqa: E402
from vset_source import payload_errors, source_kind_errors  # noqa: E402

# Compatibility aliases for the pre-split private names.
_record_patch = record_patch
_oracle_errors = oracle_errors
_payload_errors = payload_errors
_source_kind_errors = source_kind_errors


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
        help="repo-pack directory for --oracle (defaults next to fixtures)",
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


def _run_manifest(target: Path) -> int:
    errors = validate_manifest(load_json(target))
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
            "result_hash": execution["reference"]["result_hash"],
        }
    }


def _run_records(target: Path, args: argparse.Namespace, pack: Path | None) -> int:
    reports = []
    failed = False
    for path in iter_record_paths(target):
        record = load_json(path)
        if args.oracle:
            assert pack is not None
            errors, execution = validate_record_with_oracle(record, pack)
        else:
            errors = validate_record(
                record, require_registry_sha=args.require_registry_sha
            )
            execution = None
        item = {"path": str(path), **summarize(errors), **_execution_summary(execution)}
        reports.append(item)
        if errors:
            failed = True
            _print_errors(path, errors)
    print(json.dumps({"records": reports, "ok": not failed}, indent=2))
    return 1 if failed else 0


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    target = Path(args.target)
    if not target.exists():
        print(f"not found: {target}", file=sys.stderr)
        return 2
    pack = Path(args.pack) if args.pack else None
    if args.oracle and pack is None:
        print("--oracle requires --pack", file=sys.stderr)
        return 2
    if args.manifest:
        return _run_manifest(target)
    return _run_records(target, args, pack)


if __name__ == "__main__":
    raise SystemExit(main())
