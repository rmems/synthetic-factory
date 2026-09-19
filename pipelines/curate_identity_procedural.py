#!/usr/bin/env python3
"""Procedural preserved-record routes and retained-rights attachment.

Split out of ``curate_identity.py`` (CodeScene: Lines of Code in a Single
File) by responsibility; every name is re-exported from ``curate_identity``
so existing ``curate_identity.X`` call sites and test seams resolve
unchanged.

Code-repair and oracle records keep their exact source bytes: the generated
envelope is the measurement's attribution, so curation preserves the family
ID and output bytes instead of deriving a canonical identity ID.  Retained
records of every kind then carry the row's reviewed rights fields.
"""

from __future__ import annotations

import copy
import sys
from typing import Any

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("curate_identity_procedural")
    from . import curate_identity_json as _identity_json
    from . import curate_identity_materialize as _materialize
    from . import curate_identity_provenance as _provenance
    from . import curate_identity_sources as _sources
    from . import rights_record as _rights_record
    from .rights_mapping import RightsPolicyError
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "curate_identity_procedural"
    )
    import curate_identity_json as _identity_json
    import curate_identity_materialize as _materialize
    import curate_identity_provenance as _provenance
    import curate_identity_sources as _sources
    import rights_record as _rights_record
    from rights_mapping import RightsPolicyError

IdentityCurationError = _identity_json.IdentityCurationError
CurationResult = _sources.CurationResult


def _preserved_result(
    mapping: dict[str, Any], original: Any, row: Any, eligibility
) -> CurationResult:
    eligible, reasons = eligibility
    curated = copy.deepcopy(original)
    output_id = curated["id"]
    mapping.update(
        action="retained",
        reason_codes=["identity.preserved", "provenance.preserved"],
        output_id=output_id,
        output_sha256=_identity_json.sha256_json(curated),
        id_mappings=[{"owner_path": "/", "output_id": output_id}],
        provenance_mappings=[],
        procedural_authority={
            "policy_sha256": row.procedural_policy_sha256,
            "generator_ownership": row.generator_ownership,
            "generation_method": row.generation_method,
            "source_license_evidence": dict(row.source_license_evidence),
            "eligible_training_candidate": eligible,
            "ineligibility_reasons": list(reasons),
        },
    )
    return CurationResult("retained", curated, mapping)


def _require_training_policy(original: Any, row: Any, mapping: dict[str, Any]):
    ready_claims = _provenance.training_ready_true_paths(original)
    if ready_claims:
        return _materialize.exclude(
            mapping,
            "identity.training_ready_policy_violation",
            details=[{"paths": ready_claims, "policy": row.training_ready_policy}],
        )
    return None


def curate_code_repair(original: Any, row: Any, mapping: dict[str, Any]):
    if __package__:
        from .code_repair.admission import natural_eligibility
        from .code_repair.source_policy import SourcePolicyError
    else:
        from code_repair.admission import natural_eligibility
        from code_repair.source_policy import SourcePolicyError
    try:
        eligible, reasons = natural_eligibility(original, row)
    except SourcePolicyError as exc:
        return _materialize.exclude(
            mapping, "identity.code_repair_invalid", details=[str(exc)]
        )
    rejection = _require_training_policy(original, row, mapping)
    if rejection is not None:
        return rejection
    return _preserved_result(mapping, original, row, (eligible, reasons))


def curate_oracle(original: Any, row: Any, mapping: dict[str, Any]):
    """Preserve oracle-grounded records byte-for-byte like the code-repair route.

    The oracle envelope (generator/oracle split, hashes, provenance) is the
    measurement's training attribution; rewriting it into canonical curated
    provenance would drop the verifiable claims, so retained records keep
    the source bytes. Eligibility is recomputed by the shared oracle validator
    through ``oracle_grounded.admission``, never read from the record's own
    validation block: a record whose measured result was edited while keeping
    its stored verdict is refused, not admitted. An honestly-rejected record
    (a family-invariant failure the record itself reports) is retained as
    evidence but ineligible.
    """
    if __package__:
        from .oracle_grounded.admission import OracleAdmissionError, natural_eligibility
    else:
        from oracle_grounded.admission import OracleAdmissionError, natural_eligibility
    rejection = _require_training_policy(original, row, mapping)
    if rejection is not None:
        return rejection
    try:
        eligible, reasons = natural_eligibility(original, row)
    except OracleAdmissionError as exc:
        return _materialize.exclude(
            mapping, "identity.oracle_invalid", details=[str(exc)]
        )
    return _preserved_result(mapping, original, row, (eligible, reasons))


def curate_fault_recovery(original: Any, row: Any, mapping: dict[str, Any]):
    if __package__:
        from .curate_identity_simulator import require_replayed_record
    else:
        from curate_identity_simulator import require_replayed_record
    try:
        require_replayed_record(original, row)
    except IdentityCurationError as exc:
        return _materialize.exclude(
            mapping, "identity.simulator_replay_invalid", details=[str(exc)]
        )
    curated = copy.deepcopy(original)
    output_id = curated["id"]
    mapping.update(
        action="retained",
        reason_codes=["identity.preserved", "provenance.preserved"],
        output_id=output_id,
        output_sha256=_identity_json.sha256_json(curated),
        id_mappings=[{"owner_path": "/", "output_id": output_id}],
        provenance_mappings=[],
        simulator_authority={"basis": "reviewed_producer_replay"},
    )
    return CurationResult("retained", curated, mapping)


def curate_known_kind(kind: str, original: Any, row: Any, mapping: dict[str, Any]):
    if kind == "code_repair":
        return curate_code_repair(original, row, mapping)
    if kind == "fault_recovery":
        return curate_fault_recovery(original, row, mapping)
    if kind == "oracle":
        return curate_oracle(original, row, mapping)
    return None


def attach_retained_rights(result, row, source_sha256, registry_sha256):
    if result.action == "retained":
        if row is None:
            raise IdentityCurationError(
                "retained record has no reviewed registry row"
            )
        try:
            _rights_record.attach_identity_rights(
                result.mapping,
                row,
                source_sha256=source_sha256,
                factory_registry_sha256=registry_sha256,
            )
        except RightsPolicyError as exc:
            raise IdentityCurationError(str(exc)) from exc
    return result


if __package__:
    _expose_package_sibling(__name__)
