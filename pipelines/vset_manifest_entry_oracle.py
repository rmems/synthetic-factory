"""Oracle- and curation-level checks for manifest entries.

Fail-closed predicates over a single manifest entry's oracle and curation
claims: status legality, validated-evidence requirements, independence from
the solver/task-author, reason-code validity, and the accept-decision gate.
"""

from __future__ import annotations

import sys
from typing import Any, Mapping

if __package__:  # pragma: no cover - package-child import path
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("vset_manifest_entry_oracle")
    from .vset_constants import (
        CURATION_DECISIONS,
        ERR_ACTOR_FIELDS_INVALID,
        ERR_PAYLOAD_INVALID,
        IDENTITY_UNRESOLVED_PROVENANCE,
        ORACLE_STATUSES,
        VSetValidationError,
        _is_sha256,
        _mapping_or_empty,
        reason_codes_error,
)
    from .vset_oracle_check import (
        _certifier_errors,
        _self_certify_kind_errors,
    )
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "vset_manifest_entry_oracle"
    )
    from vset_constants import (
        CURATION_DECISIONS,
        ERR_ACTOR_FIELDS_INVALID,
        ERR_PAYLOAD_INVALID,
        IDENTITY_UNRESOLVED_PROVENANCE,
        ORACLE_STATUSES,
        VSetValidationError,
        _is_sha256,
        _mapping_or_empty,
        reason_codes_error,
)
    from vset_oracle_check import (
        _certifier_errors,
        _self_certify_kind_errors,
    )


def _entry_oracle_status_errors(
    where: str, oracle: Mapping[str, Any]
) -> list[VSetValidationError]:
    status = oracle.get("status")
    if status is None or status in ORACLE_STATUSES:
        return []
    return [
        VSetValidationError(
            "vset.oracle_status_invalid", f"{where}.oracle.status is not a known status"
        )
    ]


def _entry_validated_oracle_errors(
    where: str, entry: Mapping[str, Any], oracle: Mapping[str, Any]
) -> list[VSetValidationError]:
    errors: list[VSetValidationError] = []
    if not _is_sha256(oracle.get("result_hash")):
        errors.append(
            VSetValidationError(
                "vset.oracle_validated_without_evidence",
                f"{where} validated oracle requires result_hash",
            )
        )
    solver: Mapping[str, Any] = _mapping_or_empty(entry.get("solver"))
    author: Mapping[str, Any] = _mapping_or_empty(entry.get("task_author"))
    reviewer = entry.get("reviewer")
    errors.extend(_self_certify_kind_errors(oracle.get("kind")))
    errors.extend(
        _certifier_errors(
            oracle.get("certifier"),
            solver,
            author,
            reviewer if isinstance(reviewer, Mapping) else None,
        )
    )
    return errors


def _entry_oracle_errors(where: str, entry: Mapping[str, Any]) -> list[VSetValidationError]:
    oracle = entry.get("oracle")
    if oracle is None:
        return []
    if not isinstance(oracle, Mapping):
        return [VSetValidationError(ERR_PAYLOAD_INVALID, f"{where}.oracle must be an object")]
    errors = _entry_oracle_status_errors(where, oracle)
    if oracle.get("status") == "validated":
        errors.extend(_entry_validated_oracle_errors(where, entry, oracle))
    return errors


def is_invalid_or_impossible(entry: Mapping[str, Any]) -> bool:
    if not isinstance(entry, Mapping):
        return False
    oracle = _mapping_or_empty(entry.get("oracle"))
    curation = _mapping_or_empty(entry.get("curation"))
    reasons_value = curation.get("reason_codes")
    reasons: list[Any] = reasons_value if isinstance(reasons_value, list) else []
    return oracle.get("status") == "invalid" or "vset.impossible_task" in reasons


def _entry_reason_errors(
    where: str, curation: Mapping[str, Any]
) -> list[VSetValidationError]:
    if "reason_codes" not in curation:
        return []
    errors = reason_codes_error(curation["reason_codes"], f"{where}.curation")
    reasons_value = curation["reason_codes"]
    reasons: list[Any] = reasons_value if isinstance(reasons_value, list) else []
    if IDENTITY_UNRESOLVED_PROVENANCE in reasons:
        errors.append(
            VSetValidationError(
                "vset.identity_reason_collision",
                f"{where} must not reuse identity.unresolved_provenance for an actor gap",
            )
        )
    return errors


def _entry_curation_errors(where: str, entry: Mapping[str, Any]) -> list[VSetValidationError]:
    curation = entry.get("curation")
    if curation is None:
        return []
    if not isinstance(curation, Mapping):
        return [VSetValidationError(ERR_PAYLOAD_INVALID, f"{where}.curation must be an object")]
    errors: list[VSetValidationError] = []
    decision = curation.get("decision")
    if decision is not None and decision not in CURATION_DECISIONS:
        errors.append(
            VSetValidationError(
                ERR_ACTOR_FIELDS_INVALID, f"{where}.curation.decision is not a known decision"
            )
        )
    errors.extend(_entry_reason_errors(where, curation))
    errors.extend(_entry_outcome_errors(where, entry, decision))
    if decision == "accept":
        errors.extend(_entry_accept_errors(where, entry))
    return errors


def _measured_without_reason(entry: Mapping[str, Any], decision: Any) -> bool:
    reasons = _mapping_or_empty(entry.get("curation")).get("reason_codes")
    if decision != "measure":
        return False
    if not is_invalid_or_impossible(entry):
        return False
    return not isinstance(reasons, list) or not reasons


def _outcome_dropped(entry: Mapping[str, Any], decision: Any) -> bool:
    if _measured_without_reason(entry, decision):
        return True
    if not is_invalid_or_impossible(entry):
        return False
    return decision != "measure"


def _entry_outcome_errors(
    where: str, entry: Mapping[str, Any], decision: Any
) -> list[VSetValidationError]:
    if not _outcome_dropped(entry, decision):
        return []
    return [
        VSetValidationError(
            "vset.invalid_outcome_dropped",
            f"{where} invalid/impossible tasks must remain measure outcomes",
        )
    ]


def _entry_accept_errors(where: str, entry: Mapping[str, Any]) -> list[VSetValidationError]:
    errors: list[VSetValidationError] = []
    if entry.get("source_kind") != "synthetic":
        errors.append(
            VSetValidationError(
                "vset.accept_requires_synthetic",
                f"{where}: accepted records must be first-party synthetic",
            )
        )
    oracle = entry.get("oracle")
    oracle_status = oracle.get("status") if isinstance(oracle, Mapping) else None
    if oracle_status != "validated":
        errors.append(
            VSetValidationError(
                "vset.accept_requires_validated_oracle",
                f"{where}: accepted records require a validated oracle",
            )
        )
    return errors




if __package__:  # pragma: no cover - package-child import path
    _expose_package_sibling(__name__)
