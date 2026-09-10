"""Sealed catalog byte verification and isolated snapshot loading for admission."""

from __future__ import annotations

import hashlib
from collections.abc import Mapping
from dataclasses import replace
from functools import cache
from typing import Any

from . import _admission_evidence as evidence
from . import catalog as cat
from . import source_policy as sp
from ._contract import bind_import_twin


def _thaw(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {key: _thaw(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_thaw(item) for item in value]
    return value


def _pins_match(loaded: cat.Catalog) -> bool:
    actual = (
        loaded.programs_sha256,
        loaded.catalog_id,
        loaded.license_sha256,
        loaded.meta["upstream"],
    )
    expected = (
        sp.POLICY["programs_sha256"],
        sp.POLICY["catalog_id"],
        sp.POLICY["source_license_evidence"]["license_sha256"],
        dict(sp.POLICY["source_license_evidence"]),
    )
    return actual == expected


def _immutable_catalog(loaded: cat.Catalog) -> cat.Catalog:
    return replace(
        loaded, meta=sp.freeze_json(loaded.meta),
        programs=tuple(replace(program, upstream=sp.freeze_json(program.upstream))
                       for program in loaded.programs),
    )


@cache
def catalog_snapshot() -> cat.Catalog:
    """Parse and structurally validate the independently pinned catalog once."""
    from .catalog_check import catalog_structure_findings

    try:
        loaded = cat.load_catalog(sp.ROOT / sp.POLICY["catalog_relative_path"])
    except ValueError as exc:
        raise sp.SourcePolicyError(f"PROCEDURAL_CATALOG_INVALID: {exc}") from exc
    if not _pins_match(loaded):
        raise sp.SourcePolicyError("PROCEDURAL_CATALOG_PIN_MISMATCH: loaded source drifted")
    findings = catalog_structure_findings(loaded)
    if findings:
        raise sp.SourcePolicyError(f"PROCEDURAL_CATALOG_INVALID: {findings}")
    return _immutable_catalog(loaded)


def verify_catalog_bytes() -> None:
    """Recheck every sealed file on every admission request."""

    root = sp.ROOT / sp.POLICY["catalog_relative_path"]
    pins = {
        cat.CATALOG_FILENAME: sp.POLICY["catalog_sha256"],
        cat.PROGRAMS_FILENAME: sp.POLICY["programs_sha256"],
        cat.LICENSE_FILENAME: sp.POLICY["source_license_evidence"]["license_sha256"],
    }
    try:
        for filename, digest in pins.items():
            if hashlib.sha256((root / filename).read_bytes()).hexdigest() != digest:
                raise sp.SourcePolicyError(f"PROCEDURAL_CATALOG_PIN_MISMATCH: {filename}")
    except OSError as exc:
        raise sp.SourcePolicyError(f"PROCEDURAL_CATALOG_UNREADABLE: {exc}") from exc


def copy_catalog(snapshot: cat.Catalog) -> cat.Catalog:
    """Isolate mutable metadata while retaining immutable program examples."""

    return replace(
        snapshot,
        meta=_thaw(snapshot.meta),
        programs=tuple(
            replace(program, upstream=_thaw(program.upstream))
            for program in snapshot.programs
        ),
    )


def load_trusted_catalog(row: Any = None) -> cat.Catalog:
    """Load reviewed bytes and return an independent catalog copy."""

    if row is not None and (findings := evidence.row_findings(row)):
        raise sp.SourcePolicyError("; ".join(findings))
    verify_catalog_bytes()
    return copy_catalog(catalog_snapshot())


def bound_catalog(row: Any, supplied: cat.Catalog | None) -> cat.Catalog:
    """Bind an optional caller copy back to the sealed catalog authority."""

    if findings := evidence.row_findings(row):
        raise sp.SourcePolicyError("; ".join(findings))
    trusted = load_trusted_catalog()
    if supplied is not None and supplied != trusted:
        raise sp.SourcePolicyError(
            "PROCEDURAL_CATALOG_SUBSTITUTED: supplied catalog is not trusted"
        )
    return trusted


def sealed_record_findings(record: Any, where: str) -> list[str]:
    """Bind operational record checks to reviewed source bytes without execution."""
    from .validation import validate_record

    try:
        trusted = load_trusted_catalog()
    except sp.SourcePolicyError as exc:
        return [str(exc)]
    return validate_record(record, where, catalog=trusted)


bind_import_twin(__name__)
