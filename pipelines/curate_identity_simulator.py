#!/usr/bin/env python3
"""Authenticate native fault-recovery records by replaying the reviewed producer."""

from __future__ import annotations

import re
import sys

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("curate_identity_simulator")
    from .curate_identity_json import IdentityCurationError, canonical_json
    from .curate_identity_simulator_process import replay_coordinate
    from .rights_mapping import SIMULATOR_PROFILE_ID
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "curate_identity_simulator"
    )
    from curate_identity_json import IdentityCurationError, canonical_json
    from curate_identity_simulator_process import replay_coordinate
    from rights_mapping import SIMULATOR_PROFILE_ID

FACTORY = "fault-recovery-simulator-factory"
CONTRACT = "replay_fault_recovery"
# Reviewed fault_vocabulary at 6ca641: MAX_SEED=2**64-1, MAX_COUNT=100000.
MAX_SEED = 2**64 - 1
MAX_INDEX = 99_999
_ID = re.compile(r"fr-(\d{1,20})-(\d{4,5})", re.ASCII)


def _coordinates(record):
    match = _ID.fullmatch(str(record.get("id", "")))
    if match is None:
        raise IdentityCurationError("fault-recovery record ID is not a producer coordinate")
    seed, index = map(int, match.groups())
    if seed > MAX_SEED or index > MAX_INDEX:
        raise IdentityCurationError("fault-recovery coordinate exceeds the reviewed producer domain")
    if record["id"] != f"fr-{seed}-{index:04d}":
        raise IdentityCurationError("fault-recovery record ID is not canonical")
    provenance = record.get("provenance")
    if not isinstance(provenance, dict):
        raise IdentityCurationError("fault-recovery provenance must be an object")
    stamp = provenance.get("produced_at")
    if not isinstance(stamp, str):
        raise IdentityCurationError("fault-recovery produced_at must be explicit")
    return seed, index, stamp


def require_replayed_record(record, row) -> None:
    """Refuse any native envelope not exactly reproduced by the sealed simulator."""
    if (row.path_id, row.rights_profile_id) != (FACTORY, SIMULATOR_PROFILE_ID):
        raise IdentityCurationError("fault-recovery source has no reviewed simulator assignment")
    coordinates = _coordinates(record)
    expected = replay_coordinate(coordinates)
    if canonical_json(record) != canonical_json(expected):
        raise IdentityCurationError("fault-recovery envelope differs from reviewed producer replay")


def record_findings(record, where):
    """Shape validation authenticates the native producer, without training consent."""
    if __package__:
        from .curate_identity_registry import default_registry
    else:
        from curate_identity_registry import default_registry
    try:
        require_replayed_record(record, default_registry().by_path_id[FACTORY])
    except IdentityCurationError as exc:
        return [f"{where}: {exc}"]
    return []


if __package__:
    _expose_package_sibling(__name__)
