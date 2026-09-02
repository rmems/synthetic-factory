#!/usr/bin/env python3
"""Calibration lookup keyed by a record's pre-identity source identifiers."""

from __future__ import annotations

import sys
from typing import Any, Mapping

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("compose_curated_calibration_lookup")
    from . import curate_identity, curate_rewards
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "compose_curated_calibration_lookup"
    )
    import curate_identity
    import curate_rewards


def _container_calibration_id_candidates(container: Mapping[str, Any]):
    """Yield usable legacy IDs from one identity container."""

    values = map(container.get, curate_identity.LEGACY_ID_KEYS)
    yield from filter(None, map(_usable_calibration_id, values))


def _usable_calibration_id(value: Any) -> str | None:
    """Normalize one legacy identifier without nesting generator branches."""

    if isinstance(value, str) and value.strip():
        return value.strip()
    return None


def _owner_calibration_id_candidates(owner: Mapping[str, Any]):
    """Yield legacy IDs from one identity owner and its nested containers."""

    for container in (owner, owner.get("meta"), owner.get("state")):
        if isinstance(container, Mapping):
            yield from _container_calibration_id_candidates(container)


def _calibration_id_candidates(record: Mapping[str, Any]):
    """Yield source identifiers using the identity lane's vocabulary/order."""

    yield from _owner_calibration_id_candidates(record)
    for side in ("chosen", "rejected"):
        owner = record.get(side)
        if isinstance(owner, Mapping):
            yield from _owner_calibration_id_candidates(owner)


def calibration_for(record: Mapping[str, Any], catalog: Mapping[str, Any] | None) -> Any:
    """Look up calibration by pre-identity source identifiers."""

    if not catalog or not isinstance(record, Mapping):
        return None
    for candidate in _calibration_id_candidates(record):
        calibration = catalog.get(curate_rewards.catalog_record_key(candidate))
        if calibration is not None:
            return calibration
    return None


if __package__:
    _expose_package_sibling(__name__)
