#!/usr/bin/env python3
"""Replay native simulator identity mappings without granting training consent."""

from __future__ import annotations

import sys

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("curate_gate_simulator_identity")
    from . import curate_identity
    from .curate_gate_contract import GateError
    from .curate_gate_digest import record_sha256
    from .exact_json_compare import same_exact_json
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "curate_gate_simulator_identity"
    )
    import curate_identity
    from curate_gate_contract import GateError
    from curate_gate_digest import record_sha256
    from exact_json_compare import same_exact_json


def is_native(entry, record):
    return entry.get("record_kind") == "fault_recovery" or record.get("family") == "neuromorphic-fault-recovery"


def _replayed_detail(entry, record):
    detail = entry.get("identity_detail")
    if not isinstance(detail, dict) or not isinstance(detail.get("source"), dict):
        raise GateError("native simulator identity needs its complete source mapping")
    return _check_detail_replay(detail, record)


def _check_detail_replay(detail, record):
    source = curate_identity._hash_verified_manifest_source(detail["source"], 0)
    replayed = curate_identity.curate_record(source)
    if replayed.action != "retained" or not same_exact_json(replayed.mapping, detail):
        raise GateError("native simulator identity mapping differs from complete replay")
    if curate_identity.canonical_json(replayed.record) != curate_identity.canonical_json(record):
        raise GateError("native simulator source or retained envelope differs from replay")
    return detail


def _check_outer(entry, detail):
    source = detail["source"]
    expected = {
        "source_path": source["path"], "source_line": source["line"],
        "source_hash": source["sha256"], "output_hash": detail["output_sha256"],
        "manifest_entry_sha256": record_sha256(detail),
    }
    for field in ("action", "reason_codes", "record_kind", "classification", "output_id",
                  "id_mappings", "provenance_mappings"):
        expected[field] = detail.get(field)
    actual = {field: entry.get(field) for field in expected}
    if not same_exact_json(actual, expected):
        raise GateError("native simulator outer identity fields differ from replay")


def authenticate(entry, record, label):
    try:
        detail = _replayed_detail(entry, record)
        _check_outer(entry, detail)
    except ValueError as exc:
        raise GateError(f"{label}: {exc}") from exc
    return record_sha256(detail)


if __package__:
    _expose_package_sibling(__name__)
