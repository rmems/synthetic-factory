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

_PIPELINES = Path(__file__).resolve().parent
if str(_PIPELINES) not in sys.path:
    sys.path.insert(0, str(_PIPELINES))

try:
    from pipelines.raw_tree_guard import is_under_raw as _guard_is_under_raw
except ImportError:  # python3 pipelines/curate_preferences.py
    from raw_tree_guard import is_under_raw as _guard_is_under_raw

__all__ = [
    "ACTION_EXCLUDED",
    "ACTION_QUARANTINED",
    "ACTION_REPAIRED",
    "ACTION_RETAINED",
    "CurationDecision",
    "CurationRun",
    "PreferenceCurationError",
    "RAW_OUTPUT_ROOT",
    "REPOSITORY_ROOT",
    "TRANSFORM_NAME",
    "TRANSFORM_VERSION",
    "canonical_json",
    "is_canonicalizable",
    "is_under_raw",
    "sha256_hex",
]

TRANSFORM_NAME = "same-context-preference-curation"
TRANSFORM_VERSION = "1.2.0"
REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
RAW_OUTPUT_ROOT = REPOSITORY_ROOT / "outputs" / "raw"

ACTION_RETAINED = "retained"
ACTION_REPAIRED = "repaired"
ACTION_EXCLUDED = "excluded"
# Quarantine is not a preference decision: a leftover-mill record never was a
# pair, so it is recorded separately and never counted in a pair denominator.
ACTION_QUARANTINED = "quarantined"


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
    except (UnicodeEncodeError, ValueError, TypeError):
        return False
    return True
