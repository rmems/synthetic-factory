#!/usr/bin/env python3
"""Conservatively map legacy rewards into reward ontology v1.

This module is intentionally record-level. It never edits raw data and it does
not infer a common magnitude merely because component arithmetic reconciles.
Callers receive:

* a deep-copied record with a top-level ``reward_training`` annotation; and
* a hash-addressed sidecar containing exact copies of every source reward.

Only ``magnitude_comparable`` annotations expose canonical numeric values.
``canonical_magnitudes`` refuses both other comparability classes, and
``magnitude_training_cohort`` refuses a whole cohort the moment one member is
uncalibrated, so a magnitude-weighted set cannot be mixed by accident.

The optional CLI writes only caller-specified, previously nonexistent files:

    python3 pipelines/curate_rewards.py classify input.jsonl
    python3 pipelines/curate_rewards.py convert input.jsonl output.jsonl sidecars.jsonl \
        --manifest manifest.json
    python3 pipelines/curate_rewards.py run source-run new-reward-lane
    python3 pipelines/curate_rewards.py census input.jsonl --tables

The conversion policy itself is not hard-coded here. Scopes, arithmetic
methods, unit-calibration evidence, comparability classes, reason codes, and
the ordered classification rules are all read from the machine-readable mapping
at ``schemas/reward-ontology-v1.mapping.json``, which also freezes the
2026-08-17 run's 510 reward component keys and 140 structural shapes. The
read-only census subcommand recomputes that vocabulary from any JSONL corpus.

The run mode preserves every source JSONL's relative path and writes one
``reward-sidecars.jsonl`` artifact plus one aggregate ``manifest.json`` at the
new lane root.  When ``--units-migration`` is supplied, its exact bytes are
copied into the lane as ``units-migration.json`` and every applied calibration
is sealed onto the matching sidecar.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
from collections import Counter
from pathlib import Path

# Re-export the historical curate_rewards surface for tests and curate_gate.
# Every binding is a static import (not a dynamic getattr loop) so linters and
# readers can see exactly which sibling owns each name; ``__all__`` below
# declares the re-exported surface.
if __package__:
    from .exact_json import dumps_exact_json, parse_finite_json_float
    from .reward_calibration import _entry_calibrations
    from .reward_document import (
        canonical_magnitudes,
        comparability_of,
        curate_record,
        magnitude_training_cohort,
        restore_source_record,
        reward_census,
        validate_ontology_document,
    )
    from .reward_mapping import (
        ARITHMETIC_STATUSES,
        COMPONENT_DISPOSITIONS,
        DISPOSITION_AMBIGUOUS,
        DISPOSITION_DECLARED_TOTAL,
        DISPOSITION_MAGNITUDE_TERM,
        EXCLUDE,
        MAGNITUDE_COMPARABLE,
        MAPPING_PATH,
        ONTOLOGY_VERSION,
        REWARD_TRANSFORM_VERSION,
        REQUIRED_ARITHMETIC_METHODS,
        RUN_CALIBRATION_FILENAME,
        RUN_MANIFEST_FILENAME,
        RUN_SIDECAR_FILENAME,
        SIGN_ORDER_ONLY,
        MagnitudeNotComparable,
        RewardOntologyError,
        _UNSET as _UNSET,
        _canonical_bytes as _canonical_bytes,
        _canonical_record_id as _canonical_record_id,
        _decimal as _decimal,
        _json_number as _json_number,
        _reject_nonfinite_numbers as _reject_nonfinite_numbers,
        _sha256 as _sha256,
        canonical_bytes,
        canonical_source_record_id,
    )
    from .reward_ontology import (
        _classify as _classify,
        _require_declared_rule as _require_declared_rule,
        _walk_rewards as _walk_rewards,
        classify_source_rewards,
        comparability_rule,
        component_disposition,
        contributes_to_total,
        disposition_for_observed_types,
        reward_signature,
        value_type,
    )
    from .reward_policy import (
        ANNOTATION_FIELD,
        ARITHMETIC_METHODS,
        CANONICAL_SCOPE,
        CANONICAL_UNIT,
        CANONICAL_UNIT_USD,
        COMPARABILITY_CLASSES,
        COMPARABILITY_RULES,
        CONVERSION_POLICY,
        DECLARED_TOTAL_KEY,
        MAGNITUDE_AGGREGATION,
        MIGRATION_FACTOR_FIELD,
        MIGRATION_SCOPE_FIELD,
        PREFERENCE_POINTERS,
        REASON_CODES,
        RECORD_ID_RE,
        REWARD_KEYS,
        SOURCE_VOCABULARY,
        UNWEIGHTED_EXCLUDE,
        USD_UNIT_RE,
        WEIGHT_ALIASES,
        WEIGHTED_CONTAINERS,
        WEIGHTS_FIELD,
        load_conversion_policy,
        validate_conversion_policy,
    )
    from .reward_units import (
        _extract_unit_usd as _extract_unit_usd,
        _normalize_calibration as _normalize_calibration,
        assess_arithmetic,
        normalize_calibration,
    )
else:
    _PIPELINES = Path(__file__).resolve().parent
    if str(_PIPELINES) not in sys.path:
        sys.path.insert(0, str(_PIPELINES))
    from exact_json import dumps_exact_json, parse_finite_json_float
    from reward_calibration import _entry_calibrations
    from reward_document import (
        canonical_magnitudes,
        comparability_of,
        curate_record,
        magnitude_training_cohort,
        restore_source_record,
        reward_census,
        validate_ontology_document,
    )
    from reward_mapping import (
        ARITHMETIC_STATUSES,
        COMPONENT_DISPOSITIONS,
        DISPOSITION_AMBIGUOUS,
        DISPOSITION_DECLARED_TOTAL,
        DISPOSITION_MAGNITUDE_TERM,
        EXCLUDE,
        MAGNITUDE_COMPARABLE,
        MAPPING_PATH,
        ONTOLOGY_VERSION,
        REWARD_TRANSFORM_VERSION,
        REQUIRED_ARITHMETIC_METHODS,
        RUN_CALIBRATION_FILENAME,
        RUN_MANIFEST_FILENAME,
        RUN_SIDECAR_FILENAME,
        SIGN_ORDER_ONLY,
        MagnitudeNotComparable,
        RewardOntologyError,
        _UNSET as _UNSET,
        _canonical_bytes as _canonical_bytes,
        _canonical_record_id as _canonical_record_id,
        _decimal as _decimal,
        _json_number as _json_number,
        _reject_nonfinite_numbers as _reject_nonfinite_numbers,
        _sha256 as _sha256,
        canonical_bytes,
        canonical_source_record_id,
    )
    from reward_ontology import (
        _classify as _classify,
        _require_declared_rule as _require_declared_rule,
        _walk_rewards as _walk_rewards,
        classify_source_rewards,
        comparability_rule,
        component_disposition,
        contributes_to_total,
        disposition_for_observed_types,
        reward_signature,
        value_type,
    )
    from reward_policy import (
        ANNOTATION_FIELD,
        ARITHMETIC_METHODS,
        CANONICAL_SCOPE,
        CANONICAL_UNIT,
        CANONICAL_UNIT_USD,
        COMPARABILITY_CLASSES,
        COMPARABILITY_RULES,
        CONVERSION_POLICY,
        DECLARED_TOTAL_KEY,
        MAGNITUDE_AGGREGATION,
        MIGRATION_FACTOR_FIELD,
        MIGRATION_SCOPE_FIELD,
        PREFERENCE_POINTERS,
        REASON_CODES,
        RECORD_ID_RE,
        REWARD_KEYS,
        SOURCE_VOCABULARY,
        UNWEIGHTED_EXCLUDE,
        USD_UNIT_RE,
        WEIGHT_ALIASES,
        WEIGHTED_CONTAINERS,
        WEIGHTS_FIELD,
        load_conversion_policy,
        validate_conversion_policy,
    )
    from reward_units import (
        _extract_unit_usd as _extract_unit_usd,
        _normalize_calibration as _normalize_calibration,
        assess_arithmetic,
        normalize_calibration,
    )

# These private names are deliberate compatibility exports for direct callers
# of the pre-split ``curate_rewards`` module. Keeping one explicit reference
# set distinguishes that supported surface from accidentally unused imports.
_PRIVATE_COMPATIBILITY_EXPORTS = (
    _UNSET,
    _decimal,
    _json_number,
    _sha256,
    _extract_unit_usd,
    _normalize_calibration,
    _classify,
    _require_declared_rule,
    _walk_rewards,
)

__all__ = [
    "ANNOTATION_FIELD",
    "ARITHMETIC_METHODS",
    "ARITHMETIC_STATUSES",
    "Counter",
    "CANONICAL_SCOPE",
    "CANONICAL_UNIT",
    "CANONICAL_UNIT_USD",
    "COMPARABILITY_CLASSES",
    "COMPARABILITY_RULES",
    "COMPONENT_DISPOSITIONS",
    "CONVERSION_POLICY",
    "DECLARED_TOTAL_KEY",
    "DISPOSITION_AMBIGUOUS",
    "DISPOSITION_DECLARED_TOTAL",
    "DISPOSITION_MAGNITUDE_TERM",
    "EXCLUDE",
    "MAGNITUDE_AGGREGATION",
    "MAGNITUDE_COMPARABLE",
    "MAPPING_PATH",
    "MIGRATION_FACTOR_FIELD",
    "MIGRATION_SCOPE_FIELD",
    "MagnitudeNotComparable",
    "ONTOLOGY_VERSION",
    "PREFERENCE_POINTERS",
    "Path",
    "REASON_CODES",
    "RECORD_ID_RE",
    "REQUIRED_ARITHMETIC_METHODS",
    "REWARD_KEYS",
    "REWARD_TRANSFORM_VERSION",
    "RUN_CALIBRATION_FILENAME",
    "RUN_MANIFEST_FILENAME",
    "RUN_SIDECAR_FILENAME",
    "RewardOntologyError",
    "SIGN_ORDER_ONLY",
    "SOURCE_VOCABULARY",
    "UNWEIGHTED_EXCLUDE",
    "USD_UNIT_RE",
    "WEIGHT_ALIASES",
    "WEIGHTED_CONTAINERS",
    "WEIGHTS_FIELD",
    "annotations",
    "argparse",
    "assess_arithmetic",
    "catalog_record_key",
    "canonical_bytes",
    "canonical_magnitudes",
    "canonical_source_record_id",
    "census_jsonl",
    "classify_jsonl",
    "classify_source_rewards",
    "comparability_of",
    "comparability_rule",
    "component_disposition",
    "contributes_to_total",
    "convert_jsonl",
    "convert_run",
    "curate_record",
    "disposition_for_observed_types",
    "hashlib",
    "json",
    "load_conversion_policy",
    "load_units_migration",
    "load_units_migration_bytes",
    "main",
    "magnitude_training_cohort",
    "normalize_calibration",
    "os",
    "parse_args",
    "restore_source_record",
    "reward_census",
    "reward_signature",
    "shutil",
    "sys",
    "units_migration_catalog",
    "validate_conversion_policy",
    "validate_ontology_document",
    "value_type",
]

def _admit_calibration(catalog, record_id, calibration, *, path):
    """Insert one calibration, refusing any conflicting duplicate claim."""

    key = catalog_record_key(record_id)
    previous = catalog.get(key)
    if previous is not None and previous != calibration:
        raise RewardOntologyError(
            f"{path}: conflicting calibrations for {record_id}"
        )
    catalog[key] = calibration


def units_migration_catalog(document, evidence_path):
    """Build explicit per-record conversions from authenticated JSON evidence."""

    path = Path(evidence_path)
    records = document.get("records") if isinstance(document, dict) else None
    if not isinstance(records, list):
        raise RewardOntologyError(f"{path}: calibration records must be a list")

    catalog = {}
    for index, entry in enumerate(records):
        for record_id, calibration in _entry_calibrations(entry, path=path, index=index):
            _admit_calibration(catalog, record_id, calibration, path=path)
    return catalog


def load_units_migration(path):
    """Load only explicit, positive per-record conversions from an FFPC sidecar.

    Null factors and the documented coarse affine guess are deliberately
    ignored. Broad filename scopes without explicit record IDs are also
    ignored because the record itself already carries structured units there.
    """
    path = Path(path)
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise RewardOntologyError(f"{path}: invalid calibration JSON: {exc}") from exc
    return units_migration_catalog(document, path)


def load_units_migration_bytes(payload, *, label="<memory>"):
    """Parse exact migration bytes into the same catalog ``load_units_migration`` builds."""
    if not isinstance(payload, bytes):
        raise RewardOntologyError("calibration payload must be bytes")
    try:
        document = json.loads(payload.decode("utf-8"), parse_constant=_reject_json_constant)
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        raise RewardOntologyError(f"{label}: invalid calibration JSON: {exc}") from exc
    return units_migration_catalog(document, label)


def _record_calibration(record, catalog):
    if not catalog or not isinstance(record, dict):
        return None
    record_id = record.get("id")
    if not isinstance(record_id, str):
        meta = record.get("meta")
        record_id = meta.get("id") if isinstance(meta, dict) else None
    if not isinstance(record_id, str):
        return None
    return catalog.get(catalog_record_key(record_id))


def _load_jsonl(path):
    for line_number, _raw_line, record in _load_jsonl_with_source_bytes(path):
        yield line_number, record


def _reject_json_constant(value):
    raise ValueError(f"non-standard JSON numeric constant {value}")



def _load_jsonl_with_source_bytes(path):
    path = Path(path)
    try:
        payload = path.read_bytes()
    except OSError as exc:
        raise RewardOntologyError(f"cannot read {path}: {exc}") from exc
    for line_number, terminated in enumerate(payload.split(b"\n"), 1):
        raw_line = terminated[:-1] if terminated.endswith(b"\r") else terminated
        if not raw_line.strip():
            continue
        try:
            line = raw_line.decode("utf-8")
            record = json.loads(
                line,
                parse_constant=_reject_json_constant,
                parse_float=parse_finite_json_float,
            )
            canonical_bytes(record)
        except (ValueError, RecursionError) as exc:
            raise RewardOntologyError(
                f"{path}:{line_number}: invalid JSON: {exc}"
            ) from exc
        _reject_nonfinite_numbers(record, where=f"{path}:{line_number}")
        yield line_number, raw_line, record


def catalog_record_key(record_id):
    """Catalog insertion and lookup use str.lower, not casefold."""
    return record_id.lower()


def _converted_jsonl_rows(
    input_path,
    *,
    source_path,
    calibration_catalog=None,
):
    """Yield deterministic output, sidecar, and manifest rows for one JSONL."""
    stable_source_path = str(source_path).replace("\\", "/")
    for line_number, raw_line, record in _load_jsonl_with_source_bytes(input_path):
        curated, sidecar = curate_record(
            record,
            source_path=stable_source_path,
            source_line=line_number,
            calibration=_record_calibration(record, calibration_catalog),
        )
        annotation = curated[ANNOTATION_FIELD]
        manifest_entry = {
            "source_path": stable_source_path,
            "source_line": line_number,
            "source_hash": hashlib.sha256(raw_line).hexdigest(),
            "transform_name": "reward_ontology",
            "transform_version": REWARD_TRANSFORM_VERSION,
            "action": "retained",
            "reason_codes": list(annotation["reason_codes"]),
            "classification": annotation["comparability"],
            "output_id": _canonical_record_id(curated),
            "output_hash": hashlib.sha256(_canonical_bytes(curated)).hexdigest(),
        }
        yield (
            dumps_exact_json(curated, ensure_ascii=False, sort_keys=True),
            dumps_exact_json(sidecar, ensure_ascii=False, sort_keys=True),
            manifest_entry,
            annotation["comparability"],
        )


def classify_jsonl(input_path, *, source_path=None, calibration_catalog=None):
    source_path = source_path or str(input_path)
    counts = Counter()
    reasons = Counter()
    records = 0
    for line_number, record in _load_jsonl(input_path):
        curated, _sidecar = curate_record(
            record,
            source_path=source_path,
            source_line=line_number,
            calibration=_record_calibration(record, calibration_catalog),
        )
        annotation = curated[ANNOTATION_FIELD]
        counts[annotation["comparability"]] += 1
        reasons.update(annotation["reason_codes"])
        records += 1
    return {
        "input": str(input_path),
        "records": records,
        "comparability": dict(sorted(counts.items())),
        "reason_codes": dict(sorted(reasons.items())),
    }


def census_jsonl(input_paths, *, scope_keys=None):
    """Recompute the source-vocabulary census over one or more JSONL inputs."""
    paths = [str(path) for path in input_paths]

    def _records():
        for input_path in paths:
            for _line_number, record in _load_jsonl(input_path):
                yield record

    census = reward_census(_records(), scope_keys=scope_keys)
    return {"inputs": paths, **census}


def _write_new_bytes(path, payload):
    """Create one new file exclusively; never replace an existing path."""
    try:
        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    except FileExistsError as exc:
        raise RewardOntologyError(
            f"refusing to overwrite existing path: {path}"
        ) from exc
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(payload)
    except BaseException:
        path.unlink(missing_ok=True)
        raise


def _write_new_text(path, text):
    """Create one new file exclusively; never replace an existing path."""
    _write_new_bytes(path, text.encode("utf-8"))


def convert_jsonl(
    input_path,
    output_path,
    sidecar_path,
    *,
    source_path=None,
    calibration_catalog=None,
    manifest_path=None,
):
    """Convert JSONL and optionally emit a gate-compatible record manifest."""
    input_path = Path(input_path)
    output_path = Path(output_path)
    sidecar_path = Path(sidecar_path)
    manifest_path = Path(manifest_path) if manifest_path is not None else None
    destinations = [output_path, sidecar_path]
    if manifest_path is not None:
        destinations.append(manifest_path)
    resolved_destinations = {destination.resolve() for destination in destinations}
    if input_path.resolve() in resolved_destinations:
        raise RewardOntologyError("input and output paths must be distinct")
    if len(resolved_destinations) != len(destinations):
        raise RewardOntologyError("record, sidecar, and manifest outputs must be distinct")
    for destination in destinations:
        if destination.exists():
            raise RewardOntologyError(f"refusing to overwrite existing path: {destination}")

    stable_source_path = source_path or str(input_path)
    output_lines = []
    sidecar_lines = []
    manifest_entries = []
    counts = Counter()
    for output_line, sidecar_line, manifest_entry, comparability in _converted_jsonl_rows(
        input_path,
        source_path=stable_source_path,
        calibration_catalog=calibration_catalog,
    ):
        output_lines.append(output_line)
        sidecar_lines.append(sidecar_line)
        manifest_entries.append(manifest_entry)
        counts[comparability] += 1

    for destination in destinations:
        destination.parent.mkdir(parents=True, exist_ok=True)
    written = []
    try:
        _write_new_text(
            output_path,
            "\n".join(output_lines) + ("\n" if output_lines else ""),
        )
        written.append(output_path)
        _write_new_text(
            sidecar_path,
            "\n".join(sidecar_lines) + ("\n" if sidecar_lines else ""),
        )
        written.append(sidecar_path)
        if manifest_path is not None:
            _write_new_text(
                manifest_path,
                json.dumps(manifest_entries, ensure_ascii=False, indent=2, sort_keys=True)
                + "\n",
            )
            written.append(manifest_path)
    except BaseException:
        # Every requested output or none, so a retry is never blocked by a
        # partial record/sidecar/manifest transaction.
        for destination in reversed(written):
            destination.unlink(missing_ok=True)
        raise
    summary = {
        "input": str(input_path),
        "output": str(output_path),
        "sidecars": str(sidecar_path),
        "records": len(output_lines),
        "comparability": dict(sorted(counts.items())),
    }
    if manifest_path is not None:
        summary["manifest"] = str(manifest_path)
    return summary


def _absolute_path(path):
    return Path(os.path.abspath(os.fspath(path)))


def _reject_symlink_components(path, label):
    """Reject an existing symlink anywhere in an absolute path."""
    absolute = _absolute_path(path)
    parts = absolute.parts
    walked = Path(parts[0])
    for part in parts[1:]:
        walked /= part
        if walked.is_symlink():
            raise RewardOntologyError(
                f"{label} contains a symlinked path component: {walked}"
            )
        if walked != absolute and os.path.lexists(walked) and not walked.is_dir():
            raise RewardOntologyError(
                f"{label} has a non-directory path component: {walked}"
            )
    return absolute


def _is_under_raw(path):
    parts = Path(path).resolve(strict=False).parts
    return any(
        parts[index : index + 2] == ("outputs", "raw")
        for index in range(len(parts) - 1)
    )


def _run_source_paths(source_root):
    source_root = _reject_symlink_components(source_root, "source run")
    if not source_root.is_dir():
        raise RewardOntologyError(f"source run is not a directory: {source_root}")

    discovered = []
    for path in source_root.rglob("*"):
        if path.is_symlink():
            raise RewardOntologyError(f"source run contains a symlinked path: {path}")
        if path.is_file() and path.suffix == ".jsonl":
            discovered.append(path)
    paths = sorted(
        discovered,
        key=lambda jsonl_path: jsonl_path.relative_to(source_root).as_posix(),
    )
    if not paths:
        raise RewardOntologyError(f"source run holds no JSONL files: {source_root}")
    reserved = source_root / RUN_SIDECAR_FILENAME
    if reserved in paths:
        raise RewardOntologyError(
            f"source JSONL path conflicts with aggregate sidecar name: {RUN_SIDECAR_FILENAME}"
        )
    return source_root, paths


def _new_run_destination(destination, source_root):
    destination = _reject_symlink_components(destination, "run destination")
    if _is_under_raw(destination):
        raise RewardOntologyError(
            f"refusing to write run destination beneath immutable outputs/raw: {destination}"
        )
    if os.path.lexists(destination):
        raise RewardOntologyError(
            f"refusing to overwrite existing run destination: {destination}"
        )
    if destination == source_root or source_root in destination.parents:
        raise RewardOntologyError(
            f"run destination must be outside the source run: {destination}"
        )
    return destination


def convert_run(
    input_dir,
    output_dir,
    *,
    calibration_catalog=None,
    units_migration=None,
):
    """Convert a source run into one new, gate-ready reward lane tree.

    Source JSONLs are processed in stable relative-path order. Their relative
    output paths are preserved, while sidecars and manifest entries are
    aggregated at the lane root. Any failure removes the entire new tree.
    """
    source_root, source_paths = _run_source_paths(input_dir)
    output_root = _new_run_destination(output_dir, source_root)
    try:
        output_root.mkdir(parents=True, exist_ok=False)
    except FileExistsError as exc:
        raise RewardOntologyError(
            f"refusing to overwrite existing run destination: {output_root}"
        ) from exc

    sidecar_lines = []
    manifest_entries = []
    counts = Counter()
    records = 0
    try:
        for input_path in source_paths:
            relative = input_path.relative_to(source_root)
            relative_source = relative.as_posix()
            output_lines = []
            for (
                output_line,
                sidecar_line,
                manifest_entry,
                comparability,
            ) in _converted_jsonl_rows(
                input_path,
                source_path=relative_source,
                calibration_catalog=calibration_catalog,
            ):
                output_lines.append(output_line)
                sidecar_lines.append(sidecar_line)
                manifest_entries.append(manifest_entry)
                counts[comparability] += 1
                records += 1
            output_path = output_root / relative
            output_path.parent.mkdir(parents=True, exist_ok=True)
            _write_new_text(
                output_path,
                "\n".join(output_lines) + ("\n" if output_lines else ""),
            )

        if not records:
            raise RewardOntologyError(f"source run holds no JSONL records: {source_root}")
        sidecar_path = output_root / RUN_SIDECAR_FILENAME
        manifest_path = output_root / RUN_MANIFEST_FILENAME
        _write_new_text(sidecar_path, "\n".join(sidecar_lines) + "\n")
        _write_new_text(
            manifest_path,
            json.dumps(manifest_entries, ensure_ascii=False, indent=2, sort_keys=True)
            + "\n",
        )
        if units_migration is not None:
            migration_path = Path(units_migration)
            try:
                migration_payload = migration_path.read_bytes()
            except OSError as exc:
                raise RewardOntologyError(
                    f"cannot read calibration {migration_path}: {exc}"
                ) from exc
            _write_new_bytes(output_root / RUN_CALIBRATION_FILENAME, migration_payload)
    except BaseException:
        shutil.rmtree(output_root, ignore_errors=True)
        raise

    return {
        "input": str(source_root),
        "output": str(output_root),
        "sidecars": str(output_root / RUN_SIDECAR_FILENAME),
        "manifest": str(output_root / RUN_MANIFEST_FILENAME),
        "files": len(source_paths),
        "records": records,
        "comparability": dict(sorted(counts.items())),
    }


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    classify = subparsers.add_parser("classify", help="read-only JSONL classification")
    classify.add_argument("input")
    classify.add_argument("--source-path")
    classify.add_argument("--units-migration")

    convert = subparsers.add_parser("convert", help="write annotated JSONL and sidecars")
    convert.add_argument("input")
    convert.add_argument("output")
    convert.add_argument("sidecars")
    convert.add_argument("--manifest")
    convert.add_argument("--source-path")
    convert.add_argument("--units-migration")

    census = subparsers.add_parser(
        "census", help="read-only reward vocabulary census over JSONL inputs"
    )
    census.add_argument("inputs", nargs="+")
    census.add_argument(
        "--scope-key",
        action="append",
        dest="scope_keys",
        help="reward key to census (repeatable); defaults to the mapped scope",
    )
    census.add_argument(
        "--tables",
        action="store_true",
        help="include the full per-key and per-shape tables in the output",
    )
    run = subparsers.add_parser(
        "run",
        aliases=["convert-run"],
        help="write a new gate-ready reward lane from a source run directory",
    )
    run.add_argument("input")
    run.add_argument("output")
    run.add_argument("--units-migration")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    try:
        migration = getattr(args, "units_migration", None)
        calibration_catalog = load_units_migration(migration) if migration else None
        if args.command == "census":
            summary = census_jsonl(args.inputs, scope_keys=args.scope_keys)
            if not args.tables:
                summary.pop("component_keys", None)
                summary.pop("shapes", None)
        elif args.command == "classify":
            summary = classify_jsonl(
                args.input,
                source_path=args.source_path,
                calibration_catalog=calibration_catalog,
            )
        elif args.command == "convert":
            summary = convert_jsonl(
                args.input,
                args.output,
                args.sidecars,
                source_path=args.source_path,
                calibration_catalog=calibration_catalog,
                manifest_path=args.manifest,
            )
        else:
            summary = convert_run(
                args.input,
                args.output,
                calibration_catalog=calibration_catalog,
                units_migration=args.units_migration,
            )
    except (OSError, RewardOntologyError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
