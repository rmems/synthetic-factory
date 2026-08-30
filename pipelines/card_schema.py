#!/usr/bin/env python3
"""Per-dataset Hugging Face card schema declarations.

Published raw JSONL has heterogeneous ``meta`` / ``reward`` / ``tool_call.args``
shapes plus optional per-dataset extras. The datasets-server infers a schema from
the first shard, then fails to cast a later shard, so it cannot build a parquet
index: ``/is-valid`` reports ``preview`` true but ``viewer`` / ``search`` /
``filter`` / ``statistics`` false. The fix is always card-side -- declare the
union schema on the card. Historical raw JSONL is never rewritten.

One dataset owns exactly one declaration file::

    config/card-schemas/<hub-dataset-name>.json

Keying on the published Hub dataset name (not the factory slug) means a dataset
is added as an independent file with zero merge conflicts against its siblings.

Declaration format (``version: 1``)::

    {
      "version": 1,
      "dataset": "long-horizon-coding-trajectories",   # must equal the filename stem
      "issues": [36],                                  # tracking issues, optional
      "note": "One sentence saying why the schema is declared by hand.",
      "config_name": "default",                        # optional, default "default"
      "split": "train",                                # optional, default "train"
      "data_files": ["data/raw/batch-*.jsonl"],        # optional, default that glob
      "features": [ <feature>, ... ],                  # omit for a disclosure-only card
      "disclosures": [ <disclosure>, ... ]             # optional
    }

A ``<feature>`` mirrors the Hugging Face YAML feature encoding one-to-one, plus
two card-only annotations that are stripped before the YAML is emitted::

    {"name": "goal", "dtype": "string"}
    {"name": "plan", "dtype": "json", "optional": true, "note": "4262 of 9970"}
    {"name": "tags", "list": "string"}
    {"name": "tool_call", "struct": [ <feature>, ... ]}
    {"name": "steps", "list": [ <feature>, ... ]}

``dtype: json`` maps to the ``datasets`` ``Json()`` feature, which is what a
key-bag column (``meta``, ``reward``, ``tool_call.args``) needs: keys may differ
per record without an Arrow cast error. Every declared field is nullable --
``datasets`` sets all struct fields nullable -- so declaring an optional field
makes it read back as ``null`` where the raw record omits it. ``optional`` is
therefore documentation: it drives the card's field table, not the Arrow schema.

A ``<disclosure>`` is either a plain sentence, or::

    {"summary": "...", "ids": ["..."], "issues": [43, 44]}

Disclosures carry the known leftover-mill / dest-stamped rows that a dataset must
own on its card.

Omitting ``features`` produces a disclosure-only declaration: no ``configs`` and
no ``dataset_info`` are emitted. That is the right shape for a dataset whose
working viewer projection must not be replaced by a default raw config.

The declaration mechanism is split by responsibility across sibling modules --
``card_schema_core`` (shared errors/constants), ``card_schema_validate``
(payload validation), ``card_schema_render`` (YAML + Markdown rendering), and
``card_schema_coverage`` (declared-vs-published glob matching) -- and re-exported
here so ``import card_schema`` remains the one entry point callers use.
"""

from __future__ import annotations

import json
from pathlib import Path

from card_schema_core import CardSchemaError, DATASET_NAME_RE, _require
from card_schema_coverage import payload_coverage_errors
from card_schema_render import (
    _yaml_scalar,
    body_section,
    field_notes,
    json_columns,
    metadata_yaml,
    undeclared_body_section,
    yaml_features,
)
from card_schema_validate import validate

REPO_ROOT = Path(__file__).resolve().parents[1]
SCHEMA_ROOT = REPO_ROOT / "config" / "card-schemas"

__all__ = (
    "CardSchemaError",
    "body_section",
    "declaration_path",
    "declared_datasets",
    "field_notes",
    "json_columns",
    "load",
    "metadata_yaml",
    "payload_coverage_errors",
    "schema_root",
    "undeclared_body_section",
    "validate",
    "yaml_features",
    "_yaml_scalar",
)


def schema_root() -> Path:
    """Directory holding one declaration file per dataset, resolved at call time."""
    return SCHEMA_ROOT


def declaration_path(dataset: str, root: Path | None = None) -> Path:
    """Return the declaration path for one Hub dataset name."""
    _require(
        isinstance(dataset, str) and DATASET_NAME_RE.fullmatch(dataset) is not None,
        f"invalid Hub dataset name: {dataset!r}",
    )
    return (root if root is not None else schema_root()) / f"{dataset}.json"


def _declaration_root(root: Path | None = None) -> Path:
    """Return a safe declaration root, whether or not it exists yet."""
    directory = root if root is not None else schema_root()
    _require(
        not directory.is_symlink(),
        f"unsafe card schema root: {directory}",
    )
    if directory.exists():
        _require(
            directory.is_dir(),
            f"unsafe card schema root: {directory}",
        )
    return directory


def declared_datasets(root: Path | None = None) -> list[str]:
    """Return every dataset name that owns a declaration file."""
    directory = _declaration_root(root)
    if not directory.exists():
        return []
    names = []
    for path in sorted(directory.iterdir()):
        if path.name.startswith("."):
            continue
        _require(
            path.is_file() and not path.is_symlink(),
            f"unsafe card schema entry: {path}",
        )
        _require(
            path.suffix == ".json",
            f"unexpected card schema entry (expected <dataset>.json): {path}",
        )
        _require(
            DATASET_NAME_RE.fullmatch(path.stem) is not None,
            f"invalid card schema filename: {path}",
        )
        names.append(path.stem)
    return names


def load(dataset: str, root: Path | None = None) -> dict | None:
    """Return a validated declaration for ``dataset``, or ``None`` if undeclared.

    A file that exists but does not validate raises ``CardSchemaError``. A
    declaration is never silently ignored.
    """
    directory = _declaration_root(root)
    if not directory.exists():
        return None
    path = declaration_path(dataset, directory)
    if not path.exists() and not path.is_symlink():
        return None
    _require(
        path.is_file() and not path.is_symlink(),
        f"unsafe card schema entry: {path}",
    )
    payload = _read_declaration_payload(path)
    return _validated_declaration(payload, dataset, path)


def _read_declaration_payload(path: Path) -> object:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise CardSchemaError(f"cannot read card schema {path}: {exc}") from exc


def _validated_declaration(payload: object, dataset: str, path: Path) -> dict:
    try:
        return validate(payload, dataset)
    except CardSchemaError as exc:
        raise CardSchemaError(f"invalid card schema {path}: {exc}") from exc
