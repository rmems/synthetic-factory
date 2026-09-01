#!/usr/bin/env python3
"""Declaration payload validation for card-schema declarations.

Validates a raw JSON declaration payload (as loaded by ``card_schema.load``)
against the documented format in ``card_schema.py``'s module docstring, and
returns it normalized. Every rejection raises ``CardSchemaError`` by way of
``_require`` -- a declaration that fails to validate is never silently
dropped or defaulted.
"""

from __future__ import annotations

import re
from typing import cast

from card_schema_core import DATASET_NAME_RE, DEFAULT_CONFIG_NAME, _require

DEFAULT_SPLIT = "train"
DEFAULT_DATA_FILES = ("data/raw/batch-*.jsonl",)

# Value dtypes this repository declares. ``json`` is the ``datasets`` Json()
# feature and is the only correct choice for a key-bag column.
SCALAR_DTYPES = frozenset(
    {"string", "bool", "int32", "int64", "float32", "float64", "json"}
)

FIELD_NAME_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_-]*$")
DATA_FILE_RE = re.compile(r"^data/raw/[A-Za-z0-9_*?./-]+$")

TOP_LEVEL_KEYS = frozenset(
    {
        "version",
        "dataset",
        "issues",
        "note",
        "config_name",
        "split",
        "data_files",
        "features",
        "disclosures",
    }
)
FEATURE_KEYS = frozenset({"name", "dtype", "struct", "list", "optional", "note"})
DISCLOSURE_KEYS = frozenset({"summary", "ids", "issues"})

__all__ = ("validate",)


def validate(payload: object, dataset: str) -> dict:
    """Validate one declaration payload and return it normalized."""
    _require(isinstance(payload, dict), "declaration must be a JSON object")
    payload = cast(dict, payload)  # narrowed by _require
    note = _validate_identity(payload, dataset)
    config_name, split = _validate_config_and_split(payload)
    data_files = _validate_data_files(payload.get("data_files", list(DEFAULT_DATA_FILES)))

    raw_features = payload.get("features", [])
    _require(isinstance(raw_features, list), "features must be a list")
    features = [_validate_feature(node, ()) for node in raw_features]
    _reject_duplicate_names(features, ())

    raw_disclosures = payload.get("disclosures", [])
    _require(isinstance(raw_disclosures, list), "disclosures must be a list")
    disclosures = [_validate_disclosure(item) for item in raw_disclosures]

    issues = _validate_issues(payload.get("issues", []), "issues")

    return {
        "version": 1,
        "dataset": dataset,
        "issues": issues,
        "note": note,
        "config_name": config_name,
        "split": split,
        "data_files": data_files,
        "features": features,
        "disclosures": disclosures,
    }


def _validate_identity(payload: dict, dataset: str) -> str:
    unknown = sorted(set(payload) - TOP_LEVEL_KEYS)
    _require(not unknown, f"unknown declaration key(s): {', '.join(unknown)}")
    _require(payload.get("version") == 1, "declaration version must be 1")
    _require(
        payload.get("dataset") == dataset,
        f"declaration dataset {payload.get('dataset')!r} does not match {dataset!r}",
    )
    note = payload.get("note")
    _require(
        isinstance(note, str) and note.strip() != "",
        "declaration needs a non-empty 'note' explaining the hand-declared schema",
    )
    note = cast(str, note)
    return note.strip()


def _validate_config_and_split(payload: dict) -> tuple[str, str]:
    config_name = payload.get("config_name", DEFAULT_CONFIG_NAME)
    _require(
        isinstance(config_name, str) and DATASET_NAME_RE.fullmatch(config_name),
        f"invalid config_name: {config_name!r}",
    )
    split = payload.get("split", DEFAULT_SPLIT)
    _require(
        isinstance(split, str) and DATASET_NAME_RE.fullmatch(split),
        f"invalid split: {split!r}",
    )
    return config_name, split


def _validate_data_files(raw_data_files: object) -> list[str]:
    if isinstance(raw_data_files, str):
        raw_data_files = [raw_data_files]
    _require(
        isinstance(raw_data_files, list) and raw_data_files,
        "data_files must be a non-empty string or list of strings",
    )
    raw_data_files = cast(list, raw_data_files)
    data_files: list[str] = []
    for pattern in raw_data_files:
        _require(
            isinstance(pattern, str) and DATA_FILE_RE.fullmatch(pattern) is not None,
            f"data_files pattern must be a repo-relative data/raw/ path: {pattern!r}",
        )
        _require(".." not in pattern, f"data_files pattern escapes the repo: {pattern!r}")
        _require(
            all("**" not in segment or segment == "**" for segment in pattern.split("/")),
            f"recursive wildcard '**' must occupy an entire path segment: {pattern!r}",
        )
        _require(pattern not in data_files, f"duplicate data_files pattern: {pattern!r}")
        data_files.append(pattern)
    return data_files


def _validate_issues(value: object, label: str) -> list[int]:
    _require(isinstance(value, list), f"{label} must be a list of issue numbers")
    value = cast(list, value)
    issues = []
    for number in value:
        _require(
            isinstance(number, int) and not isinstance(number, bool) and number > 0,
            f"{label} entries must be positive integers: {number!r}",
        )
        issues.append(number)
    return issues


def _validate_feature(node: object, path: tuple[str, ...]) -> dict:
    where = ".".join(path) or "<top level>"
    _require(isinstance(node, dict), f"feature under {where} must be an object")
    node = cast(dict, node)
    unknown = sorted(set(node) - FEATURE_KEYS)
    _require(not unknown, f"unknown feature key(s) under {where}: {', '.join(unknown)}")
    name = node.get("name")
    _require(
        isinstance(name, str) and FIELD_NAME_RE.fullmatch(name) is not None,
        f"invalid feature name under {where}: {name!r}",
    )
    name = cast(str, name)
    here = (*path, name)

    kind = _single_feature_kind(node, here)
    out = _feature_value(node, kind, here)
    _apply_feature_annotations(node, out, here)
    return out


def _single_feature_kind(node: dict, here: tuple[str, ...]) -> str:
    kinds = [key for key in ("dtype", "struct", "list") if key in node]
    _require(
        len(kinds) == 1,
        f"feature {'.'.join(here)} needs exactly one of dtype/struct/list, got "
        f"{kinds or ['none']}",
    )
    return kinds[0]


def _feature_value(node: dict, kind: str, here: tuple[str, ...]) -> dict:
    out: dict = {"name": here[-1]}
    if kind == "dtype":
        out["dtype"] = _feature_dtype(node["dtype"], here)
    elif kind == "struct":
        out["struct"] = _feature_struct(node["struct"], here)
    else:
        out["list"] = _feature_list(node["list"], here)
    return out


def _feature_dtype(dtype: object, here: tuple[str, ...]) -> str:
    _require(
        isinstance(dtype, str) and dtype in SCALAR_DTYPES,
        f"unsupported dtype on {'.'.join(here)}: {dtype!r} "
        f"(allowed: {', '.join(sorted(SCALAR_DTYPES))})",
    )
    dtype = cast(str, dtype)
    return dtype


def _feature_struct(children: object, here: tuple[str, ...]) -> list[dict]:
    _require(
        isinstance(children, list) and children,
        f"struct on {'.'.join(here)} must be a non-empty list of features",
    )
    children = cast(list, children)
    struct = [_validate_feature(child, here) for child in children]
    _reject_duplicate_names(struct, here)
    return struct


def _feature_list(children: object, here: tuple[str, ...]) -> object:
    if isinstance(children, str):
        _require(
            children in SCALAR_DTYPES,
            f"unsupported list dtype on {'.'.join(here)}: {children!r}",
        )
        return children
    _require(
        isinstance(children, list) and children,
        f"list on {'.'.join(here)} must be a dtype string or a non-empty "
        "list of features",
    )
    children = cast(list, children)
    items = [_validate_feature(child, (*here, "[]")) for child in children]
    _reject_duplicate_names(items, (*here, "[]"))
    return items


def _apply_feature_annotations(node: dict, out: dict, here: tuple[str, ...]) -> None:
    if "optional" in node:
        _require(
            isinstance(node["optional"], bool),
            f"optional on {'.'.join(here)} must be a boolean",
        )
        out["optional"] = node["optional"]
    if "note" in node:
        _require(
            isinstance(node["note"], str) and node["note"].strip() != "",
            f"note on {'.'.join(here)} must be a non-empty string",
        )
        out["note"] = node["note"].strip()


def _reject_duplicate_names(features: list[dict], path: tuple[str, ...]) -> None:
    seen: set[str] = set()
    for feature in features:
        name = feature["name"]
        _require(
            name not in seen,
            f"duplicate feature name {name!r} under {'.'.join(path) or '<top level>'}",
        )
        seen.add(name)


def _validate_disclosure(item: object) -> dict:
    if isinstance(item, str):
        _require(item.strip() != "", "disclosure sentence must not be empty")
        return {"summary": item.strip(), "ids": [], "issues": []}
    _require(isinstance(item, dict), "disclosure must be a string or an object")
    item = cast(dict, item)
    unknown = sorted(set(item) - DISCLOSURE_KEYS)
    _require(not unknown, f"unknown disclosure key(s): {', '.join(unknown)}")
    summary = item.get("summary")
    _require(
        isinstance(summary, str) and summary.strip() != "",
        "disclosure needs a non-empty 'summary'",
    )
    summary = cast(str, summary)
    raw_ids = item.get("ids", [])
    _require(isinstance(raw_ids, list), "disclosure ids must be a list")
    ids = []
    for record_id in raw_ids:
        _require(
            isinstance(record_id, str) and record_id.strip() != "",
            f"disclosure id must be a non-empty string: {record_id!r}",
        )
        ids.append(record_id.strip())
    return {
        "summary": summary.strip(),
        "ids": ids,
        "issues": _validate_issues(item.get("issues", []), "disclosure issues"),
    }
