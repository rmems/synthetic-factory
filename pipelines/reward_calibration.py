#!/usr/bin/env python3
"""Shared parsing for explicit reward-calibration evidence entries."""

from __future__ import annotations

from reward_mapping import _decimal, _json_number
from reward_policy import (
    CANONICAL_UNIT_USD,
    MIGRATION_FACTOR_FIELD,
    MIGRATION_SCOPE_FIELD,
    RECORD_ID_RE,
)


def _entry_calibrations(entry, *, path, index):
    """Yield (record_id, calibration) pairs from one explicit, positive entry."""

    if not isinstance(entry, dict):
        return
    factor = _decimal(entry.get(MIGRATION_FACTOR_FIELD))
    if factor is None or factor <= 0:
        return
    scope = entry.get(MIGRATION_SCOPE_FIELD)
    if not isinstance(scope, str):
        return
    for record_id in sorted(set(RECORD_ID_RE.findall(scope))):
        yield record_id, {
            "source_unit_usd": _json_number(factor * CANONICAL_UNIT_USD),
            "canonical_factor": _json_number(factor),
            "evidence_ref": f"{path.as_posix()}#/records/{index}",
        }
