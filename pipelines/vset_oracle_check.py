"""Structural oracle-status checks (no fixture execution)."""

from __future__ import annotations

from typing import Any, Mapping

from vset_constants import (
    ORACLE_STATUSES,
    SELF_CERTIFY_ORACLE_KINDS,
    VALIDATING_ORACLE_KINDS,
    VSetValidationError,
    _is_nonempty,
    _is_sha256,
)


def oracle_errors(
    record: Mapping[str, Any], oracle: Mapping[str, Any]
) -> list[VSetValidationError]:
    errors: list[VSetValidationError] = []
    status = oracle.get("status")
    kind = oracle.get("kind")
    if status not in ORACLE_STATUSES:
        errors.append(
            VSetValidationError(
                "vset.oracle_status_invalid",
                "oracle.status must be invalid, provisional, or validated",
            )
        )
        return errors
    if not _is_nonempty(kind):
        errors.append(
            VSetValidationError("vset.oracle_status_invalid", "oracle.kind must be a non-empty string")
        )
        return errors
    if status == "validated":
        errors.extend(_validated_oracle_errors(record, oracle, kind))
    return errors


def _self_certify_kind_errors(kind: Any) -> list[VSetValidationError]:
    errors: list[VSetValidationError] = []
    if kind in SELF_CERTIFY_ORACLE_KINDS:
        errors.append(
            VSetValidationError(
                "vset.oracle_self_certified",
                "a solver or task-author claim cannot certify oracle_status=validated",
            )
        )
    if kind not in VALIDATING_ORACLE_KINDS:
        errors.append(
            VSetValidationError(
                "vset.oracle_self_certified",
                f"oracle.kind {kind!r} cannot independently certify validated",
            )
        )
    return errors


def _validated_evidence_errors(oracle: Mapping[str, Any]) -> list[VSetValidationError]:
    if _is_nonempty(oracle.get("command")) and _is_sha256(oracle.get("result_hash")):
        return []
    return [
        VSetValidationError(
            "vset.oracle_validated_without_evidence",
            "validated oracle requires command and result_hash",
        )
    ]


def _solver_upgrade_errors(
    oracle: Mapping[str, Any], solver: Mapping[str, Any], kind: Any
) -> list[VSetValidationError]:
    evidence = oracle.get("signals")
    only_solver_signal = (
        isinstance(evidence, list) and evidence == ["solver_success"]
    ) or oracle.get("upgraded_from_solver_success") is True
    solver_success = solver.get("outcome") == "success"
    if not (only_solver_signal or (solver_success and kind in SELF_CERTIFY_ORACLE_KINDS)):
        return []
    return [
        VSetValidationError(
            "vset.oracle_self_certified",
            "solver success must not upgrade oracle_status to validated",
        )
    ]


def _validated_oracle_errors(
    record: Mapping[str, Any], oracle: Mapping[str, Any], kind: Any
) -> list[VSetValidationError]:
    solver = record.get("solver") if isinstance(record.get("solver"), Mapping) else {}
    author = record.get("task_author") if isinstance(record.get("task_author"), Mapping) else {}
    errors: list[VSetValidationError] = []
    errors.extend(_self_certify_kind_errors(kind))
    errors.extend(_validated_evidence_errors(oracle))
    errors.extend(_certifier_errors(oracle.get("certifier"), solver, author))
    errors.extend(_solver_upgrade_errors(oracle, solver, kind))
    return errors


def _certifier_errors(
    certifier: Any, solver: Mapping[str, Any], author: Mapping[str, Any]
) -> list[VSetValidationError]:
    if not _is_nonempty(certifier):
        return [
            VSetValidationError(
                "vset.oracle_self_certified",
                "validated oracle requires an independent certifier",
            )
        ]
    if certifier in {"solver", "task_author"} or certifier in {
        solver.get("run_id"),
        author.get("run_id"),
        solver.get("model"),
        author.get("model"),
    }:
        return [
            VSetValidationError(
                "vset.oracle_self_certified",
                "oracle.certifier must not be the solver or task_author",
            )
        ]
    return []
