#!/usr/bin/env python3
"""Strict schema validation for the reviewed mill-script inventory."""

from __future__ import annotations

import json
import re
import sys
from pathlib import PurePosixPath

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("mill_script_inventory_schema")
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "mill_script_inventory_schema"
    )

SCHEMA_VERSION = "mill-script-inventory-v1"
CLASSIFICATIONS = frozenset(
    {
        "production",
        "retained_historical_generator",
        "removable_duplicate",
    }
)
QUALITY_SCOPES = frozenset({"production", "archived"})
MAX_INVENTORY_BYTES = 256_000


class MillScriptInventoryError(Exception):
    """Fail-closed inventory or guard refusal."""


def _reject_duplicate_keys(pairs: list[tuple[object, object]]) -> dict:
    seen: dict[object, object] = {}
    for key, value in pairs:
        if key in seen:
            raise MillScriptInventoryError(f"duplicate key {key!r}")
        seen[key] = value
    return seen


def _require_mapping(value: object, where: str) -> dict:
    if not isinstance(value, dict):
        raise MillScriptInventoryError(f"{where} must be an object")
    return value


def _require_str(value: object, where: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise MillScriptInventoryError(f"{where} must be a nonempty string")
    return value


def _require_str_list(value: object, where: str) -> tuple[str, ...]:
    if not isinstance(value, list) or not value:
        raise MillScriptInventoryError(f"{where} must be a nonempty array of strings")
    return tuple(_require_str(item, f"{where}[{index}]") for index, item in enumerate(value))


def _require_path(value: object, where: str) -> str:
    path = _require_str(value, where).replace("\\", "/")
    if PurePosixPath(path).is_absolute() or ".." in PurePosixPath(path).parts:
        raise MillScriptInventoryError(f"{where} must be a repo-relative path")
    return path


def _validate_scope(classification: str, scope: str, where: str) -> None:
    expected = "production" if classification == "production" else "archived"
    if scope != expected:
        raise MillScriptInventoryError(f"{where}: classification requires quality_scope {expected}")


def _optional_replacement(row: dict, where: str) -> str | None:
    value = row.get("canonical_replacement")
    if value is not None:
        _require_str(value, f"{where}.canonical_replacement")
    return value


def _validate_script(entry: object, index: int) -> dict:
    row = _require_mapping(entry, f"scripts[{index}]")
    classification = _require_str(row.get("classification"), f"scripts[{index}].classification")
    if classification not in CLASSIFICATIONS:
        raise MillScriptInventoryError(
            f"scripts[{index}].classification must be one of {sorted(CLASSIFICATIONS)}"
        )
    scope = _require_str(row.get("quality_scope"), f"scripts[{index}].quality_scope")
    if scope not in QUALITY_SCOPES:
        raise MillScriptInventoryError(
            f"scripts[{index}].quality_scope must be one of {sorted(QUALITY_SCOPES)}"
        )
    _validate_scope(classification, scope, f"scripts[{index}]")
    replacement = _optional_replacement(row, f"scripts[{index}]")
    return {
        "path": _require_path(row.get("path"), f"scripts[{index}].path"),
        "classification": classification,
        "owner": _require_str(row.get("owner"), f"scripts[{index}].owner"),
        "status": _require_str(row.get("status"), f"scripts[{index}].status"),
        "canonical_replacement": replacement,
        "quality_scope": scope,
        "provenance": _require_str(row.get("provenance"), f"scripts[{index}].provenance"),
    }


def _validate_family(entry: object, index: int) -> dict:
    row = _require_mapping(entry, f"mill_families[{index}]")
    classification = _require_str(
        row.get("classification"), f"mill_families[{index}].classification"
    )
    if classification not in CLASSIFICATIONS:
        raise MillScriptInventoryError(
            f"mill_families[{index}].classification must be one of {sorted(CLASSIFICATIONS)}"
        )
    return {
        "family": _require_str(row.get("family"), f"mill_families[{index}].family"),
        "owner": _require_str(row.get("owner"), f"mill_families[{index}].owner"),
        "classification": classification,
        "provenance": _require_str(row.get("provenance"), f"mill_families[{index}].provenance"),
    }


def _archive_commit(value: object) -> str:
    commit = _require_str(value, "historical_generator_policy.provenance_commit")
    if not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise MillScriptInventoryError("historical provenance_commit must be a full commit SHA")
    return commit


def _archive_paths(value: object) -> tuple[str, ...]:
    paths = _require_str_list(value, "historical_generator_policy.archived_paths")
    return tuple(_require_path(path, "archived_paths") for path in paths)


def _validate_historical_policy(value: object) -> dict:
    row = _require_mapping(value, "historical_generator_policy")
    classification = _require_str(
        row.get("classification"), "historical_generator_policy.classification"
    )
    if classification != "retained_historical_generator":
        raise MillScriptInventoryError(
            "historical_generator_policy.classification must be retained_historical_generator"
        )
    scope = _require_str(row.get("quality_scope"), "historical_generator_policy.quality_scope")
    if scope != "archived":
        raise MillScriptInventoryError("historical_generator_policy.quality_scope must be archived")
    return {
        "classification": classification,
        "status": _require_str(row.get("status"), "historical_generator_policy.status"),
        "quality_scope": scope,
        "canonical_owner": _require_str(
            row.get("canonical_owner"), "historical_generator_policy.canonical_owner"
        ),
        "canonical_replacement": _require_str(
            row.get("canonical_replacement"),
            "historical_generator_policy.canonical_replacement",
        ),
        "provenance_ref": _require_str(
            row.get("provenance_ref"), "historical_generator_policy.provenance_ref"
        ),
        "location": _require_str(row.get("location"), "historical_generator_policy.location"),
        "archived_paths": _archive_paths(row.get("archived_paths")),
        "provenance_commit": _archive_commit(row.get("provenance_commit")),
        "example_paths": _require_str_list(
            row.get("example_paths"), "historical_generator_policy.example_paths"
        ),
        "notes": _require_str(row.get("notes"), "historical_generator_policy.notes"),
    }


def _validate_quality_policy(value: object) -> dict:
    row = _require_mapping(value, "quality_policy")
    return {
        "historical_ref": _require_str(row.get("historical_ref"), "quality_policy.historical_ref"),
        "gitignore_patterns": _require_str_list(
            row.get("gitignore_patterns"), "quality_policy.gitignore_patterns"
        ),
        "archived_exclude_patterns": _require_str_list(
            row.get("archived_exclude_patterns"),
            "quality_policy.archived_exclude_patterns",
        ),
        "forbidden_blanket_patterns": _require_str_list(
            row.get("forbidden_blanket_patterns"),
            "quality_policy.forbidden_blanket_patterns",
        ),
    }


def _inventory_document(payload: bytes, where: str) -> dict:
    if not isinstance(payload, bytes):
        raise MillScriptInventoryError(f"{where} must be bytes")
    if len(payload) > MAX_INVENTORY_BYTES:
        raise MillScriptInventoryError(f"{where} exceeds {MAX_INVENTORY_BYTES} bytes")
    try:
        document = json.loads(payload.decode("utf-8"), object_pairs_hook=_reject_duplicate_keys)
    except (UnicodeDecodeError, json.JSONDecodeError, RecursionError) as exc:
        raise MillScriptInventoryError(f"{where}: invalid JSON: {exc}") from exc
    return _require_mapping(document, where)


def _required_rows(mapping: dict, key: str) -> list:
    rows = mapping.get(key)
    if not isinstance(rows, list):
        raise MillScriptInventoryError(f"{key} must be a nonempty array")
    if not rows:
        raise MillScriptInventoryError(f"{key} must be a nonempty array")
    return rows


def _validated_scripts(rows: list) -> tuple[dict, ...]:
    scripts = tuple(_validate_script(entry, index) for index, entry in enumerate(rows))
    paths = [row["path"] for row in scripts]
    if len(paths) != len(set(paths)):
        raise MillScriptInventoryError("scripts paths must be unique")
    return scripts


def load_inventory_bytes(payload: bytes, *, where: str = "mill-script inventory") -> dict:
    """Strictly decode and validate mill-script inventory bytes."""

    mapping = _inventory_document(payload, where)
    version = _require_str(mapping.get("schema_version"), "schema_version")
    if version != SCHEMA_VERSION:
        raise MillScriptInventoryError(f"schema_version must be {SCHEMA_VERSION}")
    scripts = _validated_scripts(_required_rows(mapping, "scripts"))
    families = _required_rows(mapping, "mill_families")
    return {
        "schema_version": version,
        "notes": _require_str(mapping.get("notes"), "notes"),
        "match_patterns": _require_str_list(mapping.get("match_patterns"), "match_patterns"),
        "scripts": scripts,
        "historical_generator_policy": _validate_historical_policy(
            mapping.get("historical_generator_policy")
        ),
        "mill_families": tuple(
            _validate_family(entry, index) for index, entry in enumerate(families)
        ),
        "quality_policy": _validate_quality_policy(mapping.get("quality_policy")),
    }


if __package__:
    _expose_package_sibling(__name__)
