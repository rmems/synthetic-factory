#!/usr/bin/env python3
"""Shared contract for the composed-curated export pipeline.

Split out of ``export_hf.py`` (CodeScene: Lines of Code in a Single File) by
responsibility; every public name is re-exported from ``export_hf`` so
existing ``export_hf.X`` call sites resolve unchanged. This module holds the
error type, the row/file dataclasses, the destination layout constants, and
the strict-JSON primitives that two or more of the siblings need.
"""

from __future__ import annotations

import json
import math
import sys
from dataclasses import dataclass
from typing import Any, TypeGuard

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("export_contract")
    from .tag_jsonutil import reject_duplicate_object_keys
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "export_contract"
    )
    from tag_jsonutil import reject_duplicate_object_keys

EXPORT_NAME = "export_hf"
EXPORT_VERSION = "export-hf-v3"
CREATED_BY = f"synthetic-factory {EXPORT_NAME} ({EXPORT_VERSION})"

CURATED_DIRNAME = "data/curated"
VIEWER_PATH = "data/viewer/records.parquet"
TRAIN_PATH = "data/splits/train.jsonl"
EVAL_PATH = "data/splits/eval.jsonl"
PROVENANCE_PATH = "provenance.json"
PROTOCOL_PATH = "EVAL_PROTOCOL.md"

VIEWER_COLUMNS = ("source_file", "source_line", "record_json")
DEFAULT_EVAL_FRACTION = 0.1
DEFAULT_SPLIT_SALT = "spikenaut.synthetic-factory.split-v1"
SPLIT_POLICY = (
    "deterministic snapshot split: sha256(salt|source_file|source_line) maps each "
    "row to [0,1); rows below eval_fraction are eval, every factory with at least "
    "two rows contributes to both sides, and a global hash-order fallback keeps "
    "every corpus of at least two records two-sided"
)


@dataclass(frozen=True)
class SplitOptions:
    """Deterministic train/eval split parameters for one export."""

    eval_fraction: float = DEFAULT_EVAL_FRACTION
    salt: str = DEFAULT_SPLIT_SALT


DEFAULT_SPLIT = SplitOptions()


class ExportError(RuntimeError):
    """Raised when the export input, gate, or destination is unsafe."""


@dataclass(frozen=True)
class ViewerRow:
    """One lossless viewer row: the exact curated line and its coordinate."""

    source_file: str
    source_line: int
    record_json: str


@dataclass(frozen=True)
class CuratedFile:
    """One curated JSONL file, its exact bytes, and its viewer rows."""

    source_file: str
    payload: bytes
    rows: tuple[ViewerRow, ...]


def _reject_json_constant(value: str) -> None:
    raise ValueError(f"non-finite JSON constant {value!r}")


def _reject_nonfinite_json_float(value: str) -> float:
    parsed = float(value)
    if not math.isfinite(parsed):
        raise ValueError(f"non-finite JSON number {value!r}")
    return parsed


def _is_json_integer(value: Any) -> TypeGuard[int]:
    """Accept JSON integers without Python's boolean-as-integer coercion."""

    return isinstance(value, int) and not isinstance(value, bool)


def _require_equal(actual: Any, expected: Any, message: str) -> None:
    """Reject an authenticated declaration that differs from its evidence."""

    if actual != expected:
        raise ExportError(message)


def _loads_json(payload: str, label: str) -> Any:
    try:
        return json.loads(
            payload,
            object_pairs_hook=reject_duplicate_object_keys,
            parse_constant=_reject_json_constant,
            parse_float=_reject_nonfinite_json_float,
        )
    except (ValueError, RecursionError) as exc:
        raise ExportError(f"{label}: invalid JSON: {exc}") from exc


if __package__:
    _expose_package_sibling(__name__)
