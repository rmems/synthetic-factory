"""Authenticate native parity observations without conferring training rights."""
from __future__ import annotations

import sys
import copy
from collections.abc import Mapping

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling
    _assert_direct_sibling("curate_parity")
    from . import curate_parity_policy as policy
    from . import curate_identity_json as _json
    from . import curate_identity
    from .curate_gate_contract import GateError
    from .curate_gate_digest import record_sha256
    from .exact_json_compare import same_exact_json
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)("curate_parity")
    import curate_parity_policy as policy
    import curate_identity_json as _json
    import curate_identity
    from curate_gate_contract import GateError
    from curate_gate_digest import record_sha256
    from exact_json_compare import same_exact_json


def _current_stamps(kind):
    if __package__:
        from . import hardware_parity_provenance, nir_equivalence_provenance
    else:
        import hardware_parity_provenance
        import nir_equivalence_provenance
    module = {"hardware_parity": hardware_parity_provenance,
              "nir_equivalence": nir_equivalence_provenance}[kind]
    return module._catalog_provenance_stamps()


def _record_kind(record):
    if not isinstance(record, Mapping):
        raise policy.ParityPolicyError("native parity record must be an object")
    kind = record.get("record_kind")
    if not isinstance(kind, str) or kind not in policy.KINDS:
        raise policy.ParityPolicyError("native parity kind is missing or invalid")
    return kind


def _require_payload_factory(record, row):
    metadata = record.get("meta")
    if not isinstance(metadata, Mapping) or metadata.get("factory") != row.payload_factory:
        raise policy.ParityPolicyError("native parity payload factory differs from source directory")


def _require_current_producer(kind, row):
    stamps = _current_stamps(kind)
    if (stamps["generator_version"], stamps["catalog_digest"]) != (row.generator_version, row.catalog_sha256):
        raise policy.ParityPolicyError("current parity producer differs from reviewed source authority")


def _require_record_validation(record):
    if __package__:
        from .check_records import check_record
    else:
        from check_records import check_record
    errors = check_record(record, "native parity")[0]
    if errors:
        raise policy.ParityPolicyError("; ".join(errors))


def admit(record, row):
    kind = _record_kind(record)
    policy.require_row(row, kind)
    _require_payload_factory(record, row)
    _json._reject_training_ready_true(record)
    _require_current_producer(kind, row)
    _require_record_validation(record)
    return {"policy_sha256": policy.POLICY_SHA256, "catalog_id": row.catalog_id,
            "catalog_sha256": row.catalog_sha256, "generator_version": row.generator_version,
            "source_type": "frontier_session", "intended_use": "research_only",
            "project_training_policy": "blocked", "training_ready_policy": "never"}


def curate(original, row, mapping):
    try:
        authority = admit(original, row)
    except ValueError as exc:
        return curate_identity._exclude(mapping, "identity.parity_invalid", details=[str(exc)])
    curated = copy.deepcopy(original)
    output_id = curated["id"]
    mapping.update(action="retained", reason_codes=["identity.preserved", "provenance.preserved"],
                   output_id=output_id, output_sha256=curate_identity.sha256_json(curated),
                   id_mappings=[{"owner_path": "/", "output_id": output_id}], provenance_mappings=[],
                   parity_authority=authority)
    return curate_identity.CurationResult("retained", curated, mapping)


def _claims_research_record(record, factory):
    if factory in policy.FACTORIES:
        return True
    if not isinstance(record, Mapping):
        return False
    kind = record.get("record_kind")
    return isinstance(kind, str) and kind in policy.KINDS


def observe_research(audit, obj, where, factory):
    """Account validated native evidence without adding any eligible records."""
    if not _claims_research_record(obj, factory):
        return False
    audit.totals["parity_research_records"] += 1
    try:
        admit(obj, curate_identity.default_registry().by_path_id.get(factory))
    except ValueError as exc:
        audit.record_errors.append(f"{where}: {exc}")
        audit.totals["invalid_parity_records"] += 1
        return True
    audit.totals["observed_parity_records"] += 1
    kind = audit._observe_record(obj, where, factory)
    audit.kinds[kind] += 1
    audit.factories[factory]["by_kind"][kind] += 1
    return True


def is_native(entry, record):
    kinds = (entry.get("record_kind"), record.get("record_kind"))
    return any(isinstance(kind, str) and kind in policy.KINDS for kind in kinds)


def _replayed_detail(entry, record):
    detail = entry.get("identity_detail")
    if not isinstance(detail, dict) or not isinstance(detail.get("source"), dict):
        raise GateError("native parity identity needs its complete source mapping")
    return _check_detail_replay(detail, record)


def _check_detail_replay(detail, record):
    source = curate_identity._hash_verified_manifest_source(detail["source"], 0)
    replayed = curate_identity.curate_record(source)
    if replayed.action != "retained" or not same_exact_json(replayed.mapping, detail):
        raise GateError("native parity identity mapping differs from complete replay")
    if curate_identity.canonical_json(replayed.record) != curate_identity.canonical_json(record):
        raise GateError("native parity source or retained envelope differs from replay")
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
        raise GateError("native parity outer identity fields differ from replay")


def authenticate(entry, record, label):
    try:
        detail = _replayed_detail(entry, record)
        _check_outer(entry, detail)
    except ValueError as exc:
        raise GateError(f"{label}: {exc}") from exc
    return record_sha256(detail)


if __package__:
    _expose_package_sibling(__name__)
