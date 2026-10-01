"""Structural oracle-status checks (no fixture execution)."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Iterable, Mapping

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("vset_oracle_check")
    from .vset_oracle_exec import _execution_result_hash
    from .vset_constants import (
        ERR_ORACLE_EXECUTION_MISMATCH,
        ERR_ORACLE_SELF_CERTIFIED,
        ORACLE_STATUSES,
        SELF_CERTIFY_ORACLE_KINDS,
        VALIDATING_ORACLE_KINDS,
        VSetValidationError,
        _is_nonempty,
        _is_sha256,
        _mapping_or_empty,
        _normalized_identity_text,
)
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "vset_oracle_check"
    )
    from vset_oracle_exec import _execution_result_hash
    from vset_constants import (
        ERR_ORACLE_EXECUTION_MISMATCH,
        ERR_ORACLE_SELF_CERTIFIED,
        ORACLE_STATUSES,
        SELF_CERTIFY_ORACLE_KINDS,
        VALIDATING_ORACLE_KINDS,
        VSetValidationError,
        _is_nonempty,
        _is_sha256,
        _mapping_or_empty,
        _normalized_identity_text,
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
                ERR_ORACLE_SELF_CERTIFIED,
                "a solver or task-author claim cannot certify oracle_status=validated",
            )
        )
    if kind not in VALIDATING_ORACLE_KINDS:
        errors.append(
            VSetValidationError(
                ERR_ORACLE_SELF_CERTIFIED,
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


def _solver_only_signal(oracle: Mapping[str, Any]) -> bool:
    evidence = oracle.get("signals")
    if isinstance(evidence, list) and evidence == ["solver_success"]:
        return True
    return oracle.get("upgraded_from_solver_success") is True


def _solver_self_certify_upgrade(solver: Mapping[str, Any], kind: Any) -> bool:
    return solver.get("outcome") == "success" and kind in SELF_CERTIFY_ORACLE_KINDS


def _solver_upgrade_errors(
    oracle: Mapping[str, Any], solver: Mapping[str, Any], kind: Any
) -> list[VSetValidationError]:
    if not _solver_only_signal(oracle) and not _solver_self_certify_upgrade(solver, kind):
        return []
    return [
        VSetValidationError(
            ERR_ORACLE_SELF_CERTIFIED,
            "solver success must not upgrade oracle_status to validated",
        )
    ]


def _validated_oracle_errors(
    record: Mapping[str, Any], oracle: Mapping[str, Any], kind: Any
) -> list[VSetValidationError]:
    solver: Mapping[str, Any] = _mapping_or_empty(record.get("solver"))
    author: Mapping[str, Any] = _mapping_or_empty(record.get("task_author"))
    errors: list[VSetValidationError] = []
    errors.extend(validated_oracle_independence_errors(oracle, solver, author))
    errors.extend(_validated_evidence_errors(oracle))
    errors.extend(_solver_upgrade_errors(oracle, solver, kind))
    return errors


_CERTIFIER_ROLE_ALIASES = frozenset({"solver", "task_author"})
_ACTOR_IDENTITY_FIELDS = ("model", "version", "run_id", "tool_policy", "prompt_hash")


def _actor_identity_strings(actor: Mapping[str, Any]) -> frozenset[str]:
    values: set[str] = set()
    for field in _ACTOR_IDENTITY_FIELDS:
        value = actor.get(field)
        if isinstance(value, str) and value:
            values.add(value)
    return frozenset(values)


def _certifier_is_actor(
    certifier: str, solver: Mapping[str, Any], author: Mapping[str, Any]
) -> bool:
    normalized = _normalized_identity_text(certifier)
    if normalized in _CERTIFIER_ROLE_ALIASES or certifier.casefold() in _CERTIFIER_ROLE_ALIASES:
        return True
    forbidden = {
        _normalized_identity_text(value)
        for value in _actor_identity_strings(solver) | _actor_identity_strings(author)
    }
    return normalized in forbidden


def validated_oracle_independence_errors(
    oracle: Mapping[str, Any], solver: Mapping[str, Any], author: Mapping[str, Any]
) -> list[VSetValidationError]:
    """Certifier + kind independence rules for a ``validated`` oracle claim.

    Shared by the record validator and the release-manifest entry
    validator so both surfaces enforce the same independence contract.
    """

    errors = _self_certify_kind_errors(oracle.get("kind"))
    errors.extend(_certifier_errors(oracle.get("certifier"), solver, author))
    return errors


def _certifier_errors(
    certifier: Any, solver: Mapping[str, Any], author: Mapping[str, Any]
) -> list[VSetValidationError]:
    if not _is_nonempty(certifier):
        return [
            VSetValidationError(
                ERR_ORACLE_SELF_CERTIFIED,
                "validated oracle requires an independent certifier",
            )
        ]
    if not _certifier_is_actor(certifier, solver, author):
        return []
    return [
        VSetValidationError(
            ERR_ORACLE_SELF_CERTIFIED,
            "oracle.certifier must not be the solver or task_author",
        )
    ]


def _illegal_pack_relative(path: str) -> bool:
    candidate = Path(path)
    return not path.strip() or candidate.is_absolute() or ".." in candidate.parts


def _string_path_list_error(value: Any, field: str, *, required: bool) -> VSetValidationError | None:
    if not value and not required:
        return None
    if isinstance(value, list) and all(isinstance(item, str) for item in value):
        return None
    return VSetValidationError(
        ERR_ORACLE_EXECUTION_MISMATCH,
        f"oracle.{field} must be a list of paths",
    )


def _first_illegal_pack_path(paths: Iterable[Any]) -> VSetValidationError | None:
    for item in paths:
        if isinstance(item, str) and _illegal_pack_relative(item):
            return VSetValidationError(
                ERR_ORACLE_EXECUTION_MISMATCH,
                f"oracle test path must stay under the pack: {item!r}",
            )
    return None


def _oracle_path_list_error(oracle: Mapping[str, Any]) -> VSetValidationError | None:
    reference_tests = oracle.get("reference_tests") or ["tests/reference.py"]
    hidden_tests = oracle.get("hidden_tests") or []
    typed = _string_path_list_error(reference_tests, "reference_tests", required=True)
    if typed is not None:
        return typed
    typed = _string_path_list_error(hidden_tests, "hidden_tests", required=False)
    if typed is not None:
        return typed
    return _first_illegal_pack_path(list(reference_tests) + list(hidden_tests or []))


def _execution_match_errors(
    record: Mapping[str, Any],
    oracle: Mapping[str, Any],
    execution: Mapping[str, Any],
    status: Any,
) -> list[VSetValidationError]:
    errors: list[VSetValidationError] = []
    expected = record.get("environment", {})
    if isinstance(expected, Mapping) and expected.get("repo_snapshot_hash") not in {
        None,
        execution["pack_snapshot_hash"],
    }:
        errors.append(
            VSetValidationError(
                ERR_ORACLE_EXECUTION_MISMATCH,
                "environment.repo_snapshot_hash does not match the repo pack",
            )
        )
    errors.extend(_fail_first_errors(execution["fail_first"]))
    if status != "validated":
        return errors
    errors.extend(_validated_execution_errors(oracle, execution))
    return errors


def _fail_first_errors(stages: Iterable[Mapping[str, Any]]) -> list[VSetValidationError]:
    errors: list[VSetValidationError] = []
    for stage in stages:
        if stage["ok"]:
            errors.append(
                VSetValidationError(
                    ERR_ORACLE_EXECUTION_MISMATCH,
                    f"hidden suite passes before the candidate patch at {stage['stage']}; "
                    "the recorded fail-to-pass claim is not demonstrated",
                )
            )
    return errors


def _hidden_suite_errors(hidden: Any) -> list[VSetValidationError]:
    if hidden is None or hidden["ok"]:
        return []
    return [
        VSetValidationError(
            ERR_ORACLE_EXECUTION_MISMATCH,
            "validated oracle requires declared hidden tests to pass",
        )
    ]


def _validated_execution_errors(
    oracle: Mapping[str, Any], execution: Mapping[str, Any]
) -> list[VSetValidationError]:
    errors: list[VSetValidationError] = []
    if not execution["reference"]["ok"]:
        errors.append(
            VSetValidationError(
                ERR_ORACLE_EXECUTION_MISMATCH,
                "validated oracle requires the reference suite to pass",
            )
        )
    errors.extend(_hidden_suite_errors(execution["hidden"]))
    if oracle.get("result_hash") != _execution_result_hash(execution):
        errors.append(
            VSetValidationError(
                ERR_ORACLE_EXECUTION_MISMATCH,
                "oracle.result_hash does not match deterministic fixture execution",
            )
        )
    if oracle.get("kind") in SELF_CERTIFY_ORACLE_KINDS:
        errors.append(
            VSetValidationError(
                ERR_ORACLE_SELF_CERTIFIED,
                "hidden-test pass is meaningless unless the oracle itself is valid",
            )
        )
    return errors


if __package__:
    _expose_package_sibling(__name__)
