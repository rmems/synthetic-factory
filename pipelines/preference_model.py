#!/usr/bin/env python3
"""Shared vocabulary for the same-context preference curation lane.

The curation scan, the destination writer, the published audit, and the
two-scan reconciler all speak in terms of the same decisions, actions, and
canonical encoding. They live in sibling modules so that no one of them has
to import another just to name a shared type; this module is the single
lower layer they all depend on.

Nothing here reads or writes the filesystem. ``canonical_json`` is the one
definition of record equality the whole lane is measured against, so it must
stay identical for every caller.
"""

from __future__ import annotations

import hashlib
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

if __package__:
    from .raw_tree_guard import is_under_raw as _guard_is_under_raw
else:
    _PIPELINES = Path(__file__).resolve().parent
    if str(_PIPELINES) not in sys.path:
        sys.path.insert(0, str(_PIPELINES))
    from raw_tree_guard import is_under_raw as _guard_is_under_raw

__all__ = [
    "ACTION_EXCLUDED",
    "ACTION_QUARANTINED",
    "ACTION_REPAIRED",
    "ACTION_RETAINED",
    "CurationDecision",
    "CurationRun",
    "PreferenceCurationError",
    "CLASSIFICATION_TRAJECTORY_PAIR",
    "RAW_OUTPUT_ROOT",
    "REASON_TRAJECTORY_PAIR",
    "REPOSITORY_ROOT",
    "TRANSFORM_NAME",
    "TRANSFORM_VERSION",
    "canonical_json",
    "is_canonicalizable",
    "is_under_raw",
    "json_equal",
    "json_key",
    "json_type_name",
    "sha256_hex",
]

TRANSFORM_NAME = "same-context-preference-curation"
TRANSFORM_VERSION = "1.3.0"
REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
RAW_OUTPUT_ROOT = REPOSITORY_ROOT / "outputs" / "raw"

ACTION_RETAINED = "retained"
ACTION_REPAIRED = "repaired"
ACTION_EXCLUDED = "excluded"
# Quarantine is not a preference decision: a leftover-mill record never was a
# pair, so it is recorded separately and never counted in a pair denominator.
ACTION_QUARANTINED = "quarantined"

# A trajectory pair is not a malformed same-state pair: it is a different
# schema that this lane does not own. Naming the exclusion keeps a 0%
# same-state yield readable and stops anyone fabricating state here. The
# lane that does own it is pipelines/curate_trajectory_preferences.py.
REASON_TRAJECTORY_PAIR = "PREFERENCE_PAIR_IS_A_TRAJECTORY_PAIR"
CLASSIFICATION_TRAJECTORY_PAIR = "trajectory_pair_out_of_scope"


class PreferenceCurationError(RuntimeError):
    """Raised when source or destination handling would be unsafe."""


@dataclass(frozen=True)
class CurationDecision:
    """One deterministic record-level curation decision."""

    action: str
    classification: str
    reason_codes: tuple[str, ...]
    record: dict[str, Any] | None
    context_diff_paths: tuple[str, ...]
    changed_context_fields: tuple[str, ...] = ()
    # Source-side agreement per canonical context field, before any repair.
    # ``None`` on both means the pair carries no comparable context at all.
    same_state: bool | None = None
    same_proposed_action: bool | None = None


@dataclass(frozen=True)
class CurationRun:
    """Curated records, manifest entries, and aggregate counts for one source."""

    records: tuple[dict[str, Any], ...]
    manifest: tuple[dict[str, Any], ...]
    summary: dict[str, Any]
    source_files: tuple[dict[str, str], ...] = ()


def canonical_json(value: Any) -> str:
    """Return the canonical JSON representation used for context equality."""

    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )


def sha256_hex(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def is_under_raw(path: Path) -> bool:
    """Whether ``path`` names or aliases the repository's raw output tree."""

    return _guard_is_under_raw(path, RAW_OUTPUT_ROOT)


def is_canonicalizable(value: Any) -> bool:
    """Whether ``value`` survives canonical JSON and UTF-8 encoding.

    ``json.loads`` accepts the non-standard ``NaN``/``Infinity`` literals, so a
    raw JSONL line can carry floats that cannot be re-encoded. Such a pair is
    excluded with a reason code instead of aborting the whole corpus scan.
    Escaped lone surrogates also pass JSON parsing but cannot be written to the
    UTF-8 JSONL destination, so exercise the actual output encoding here too.
    """

    try:
        canonical_json(value).encode("utf-8")
    except (ValueError, TypeError):
        # UnicodeEncodeError is a ValueError, so a lone surrogate is
        # caught here too; naming it as well would be redundant.
        return False
    return True


# ``bool`` is a subclass of ``int``, so it has to be matched first or every
# ``true`` in an audited document would name itself a number.
JSON_TYPE_NAMES = (
    (bool, "boolean"),
    (str, "string"),
    (int, "number"),
    (float, "number"),
    (list, "array"),
    (dict, "object"),
)


def json_type_name(value: Any) -> str:
    """Name a value's JSON type, keeping ``true`` distinct from ``1``."""

    if value is None:
        return "null"
    for python_type, type_name in JSON_TYPE_NAMES:
        if isinstance(value, python_type):
            return type_name
    return type(value).__name__


def json_equal(left: Any, right: Any) -> bool:
    """Whether two audited values agree in JSON type as well as in value.

    Python scores ``False == 0`` and ``True == 1``, so a value-only check
    would accept an expected audit that rewrote ``same_state: false`` as the
    number ``0``. The published document is evidence, and a change of type is
    a change of evidence, so compare the two the way JSON does.
    """

    if json_type_name(left) != json_type_name(right):
        return False
    if isinstance(left, dict):
        return set(left) == set(right) and all(
            json_equal(left[key], right[key]) for key in left
        )
    if isinstance(left, list):
        return len(left) == len(right) and all(
            json_equal(one, other) for one, other in zip(left, right)
        )
    return left == right


def json_key(value: Any) -> tuple[str, str]:
    """Key a JSON value by type and canonical text.

    Keying by the value alone lets ``source_line: true`` index the same slot
    as line ``1`` -- Python hashes them identically -- and raises outright on
    a list or an object, so an audit with a structured location could not be
    compared at all.
    """

    try:
        return json_type_name(value), canonical_json(value)
    except (TypeError, ValueError):
        return json_type_name(value), repr(value)
