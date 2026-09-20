#!/usr/bin/env python3
"""Teacher-identity checks for ``moe-router-distillation-trajectories``.

Split out of ``moe_check.py`` verbatim: pin the recorded teacher oracle's
identity — fingerprint, laundered-name rules, oracle type, grounding — so a
renamed or foreign teacher cannot carry an authoritative verdict.
Checkpoint/Hub-card binding lives in ``moe_checkpoint_checks``.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

_PIPELINES = Path(__file__).resolve().parent
if str(_PIPELINES) not in sys.path:
    sys.path.insert(0, str(_PIPELINES))

from oracle_grounded import distill_contract as oc  # noqa: E402
if __package__:
    from .moe_checkpoint_checks import _claims_transformers
    from .moe_featurizer import (
        NON_TEACHER_IMPLEMENTATIONS,
        NON_TEACHER_ORACLE_NAMES,
        NON_TEACHER_ORACLE_TYPES,
        TEACHER_ORACLE_TYPES,
        TRANSFORMERS_MOE_IMPLEMENTATION,
    )
    from .moe_oracles import TransformersMoERouter
else:
    from moe_checkpoint_checks import _claims_transformers
    from moe_featurizer import (
        NON_TEACHER_IMPLEMENTATIONS,
        NON_TEACHER_ORACLE_NAMES,
        NON_TEACHER_ORACLE_TYPES,
        TEACHER_ORACLE_TYPES,
        TRANSFORMERS_MOE_IMPLEMENTATION,
    )
    from moe_oracles import TransformersMoERouter


def _recorded(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _check_configuration_digest(fingerprint: dict[str, Any], where: str) -> list[str]:
    # "not-a-digest" satisfied the non-empty check, so the promised
    # configuration digest could be absent in everything but name and the
    # teacher configuration could never be audited.
    digest = fingerprint.get("configuration_sha256")
    if not _recorded(digest) or oc.SHA256_RE.match(digest):
        return []
    return [
        f"{where}.oracle.fingerprint.configuration_sha256 must be a "
        f"64-character sha256 hex digest, got {digest!r}"
    ]


def _check_fingerprint_identity(fingerprint: dict[str, Any], where: str) -> list[str]:
    """Model, checkpoint, configuration digest, and the teacher flag."""

    errors = [
        f"{where}.oracle.fingerprint.{field} must be recorded"
        for field in ("model", "revision_or_checkpoint", "configuration_sha256")
        if not _recorded(fingerprint.get(field))
    ]
    errors.extend(_check_configuration_digest(fingerprint, where))
    if not isinstance(fingerprint.get("is_llm_teacher"), bool):
        errors.append(
            f"{where}.oracle.fingerprint.is_llm_teacher must be a boolean"
        )
    return errors

def _non_teacher_identity(oracle: dict[str, Any], fingerprint: dict[str, Any]) -> str | None:
    """The stand-in identity an oracle block carries, if it carries one.

    The fingerprint's ``model`` is caller-controlled prose; the oracle's own
    name, type and implementation are what the producing code wrote. All four
    are checked so renaming one field cannot launder a stand-in.
    """

    if oc.is_enum_value(fingerprint.get("model"), NON_TEACHER_ORACLE_NAMES):
        return f"fingerprint.model {fingerprint.get('model')!r}"
    if oc.is_enum_value(oracle.get("name"), NON_TEACHER_ORACLE_NAMES):
        return f"oracle.name {oracle.get('name')!r}"
    if oc.is_enum_value(oracle.get("type"), NON_TEACHER_ORACLE_TYPES):
        return f"oracle.type {oracle.get('type')!r}"
    if oc.is_enum_value(oracle.get("implementation"), NON_TEACHER_IMPLEMENTATIONS):
        return f"oracle.implementation {oracle.get('implementation')!r}"
    return None

def _check_laundered_oracle(
    oracle: Any, fingerprint: dict[str, Any], where: str
) -> list[str]:
    """A non-teacher stand-in may not be recorded as an authoritative teacher."""

    if not isinstance(oracle, dict) or oracle.get("authority") != oc.AUTHORITY_AUTHORITATIVE:
        return []
    identity = _non_teacher_identity(oracle, fingerprint)
    if identity is not None:
        return [
            f"{where}.oracle: LAUNDERED_REFERENCE_ORACLE — {identity} names a "
            "non-teacher stand-in and may not be recorded as an authoritative "
            "teacher"
        ]
    return []

def _check_transformers_identity(oracle: Any, where: str) -> list[str]:
    """Known producer claims must retain their implementation and oracle type."""

    if not _claims_transformers(oracle):
        return []
    return [
        f"{where}.oracle.{field}: TRANSFORMERS_IDENTITY_MISMATCH — expected {expected!r}"
        for field, expected in (
            ("implementation", TRANSFORMERS_MOE_IMPLEMENTATION),
            ("type", TransformersMoERouter.oracle_type),
        )
        if oracle.get(field) != expected
    ]

def _check_teacher_fingerprint(oracle: Any, fingerprint: Any, where: str) -> list[str]:
    """The recorded teacher identity: model, checkpoint, configuration digest."""

    if not isinstance(fingerprint, dict):
        return [
            f"{where}.oracle.fingerprint must record the teacher model, checkpoint "
            "and configuration"
        ]
    return (
        _check_fingerprint_identity(fingerprint, where)
        + _check_laundered_oracle(oracle, fingerprint, where)
        + _check_transformers_identity(oracle, where)
        + _check_teacher_oracle_type(oracle, where)
    )

def _check_teacher_oracle_type(oracle: Any, where: str) -> list[str]:
    """An authoritative router record must name a teacher-capable oracle type."""

    if not (
        isinstance(oracle, dict)
        and oracle.get("authority") == oc.AUTHORITY_AUTHORITATIVE
    ):
        return []
    oracle_type = oracle.get("type")
    if oc.is_enum_value(oracle_type, TEACHER_ORACLE_TYPES):
        return []
    return [
        f"{where}.oracle.type: {oracle_type!r} is not a teacher-capable oracle "
        f"type {sorted(TEACHER_ORACLE_TYPES)} — an authoritative routing label "
        "must come from a model router or a recording of one"
    ]

def _check_is_llm_teacher(
    result: dict[str, Any], fingerprint: Any, where: str
) -> list[str]:
    """The result's teacher flag must be a boolean and match the fingerprint."""

    if not isinstance(result.get("is_llm_teacher"), bool):
        return [f"{where}.result.is_llm_teacher must be a boolean"]
    if not isinstance(fingerprint, dict):
        return []
    if not isinstance(fingerprint.get("is_llm_teacher"), bool):
        return []
    if result["is_llm_teacher"] != fingerprint["is_llm_teacher"]:
        return [
            f"{where}.result.is_llm_teacher disagrees with the oracle fingerprint"
        ]
    return []

def _check_teacher_grounded(
    result: dict[str, Any], oracle: dict[str, Any], where: str
) -> list[str]:
    """teacher_grounded follows from the teacher flag and the oracle authority."""

    errors: list[str] = []
    expected = bool(
        result.get("is_llm_teacher")
        and oracle.get("authority") == oc.AUTHORITY_AUTHORITATIVE
    )
    if result.get("teacher_grounded") is not expected:
        errors.append(
            f"{where}.result.teacher_grounded must be {expected} for an "
            f"{oracle.get('authority')!r} oracle with is_llm_teacher="
            f"{result.get('is_llm_teacher')!r}"
        )
    # An authoritative router oracle must be a teacher. Otherwise a
    # stand-in's routing reaches curation with teacher_grounded false and
    # nothing downstream objecting.
    if (
        oracle.get("authority") == oc.AUTHORITY_AUTHORITATIVE
        and result.get("teacher_grounded") is not True
    ):
        errors.append(
            f"{where}.oracle: an authoritative router oracle must be "
            "teacher-grounded; mark a non-teacher oracle reference_only"
        )
    return errors

def _check_teacher_grounding(
    result: dict[str, Any], oracle: Any, fingerprint: Any, where: str
) -> list[str]:
    """`is_llm_teacher` and `teacher_grounded` against the oracle's authority."""

    errors = _check_is_llm_teacher(result, fingerprint, where)
    if isinstance(oracle, dict):
        errors += _check_teacher_grounded(result, oracle, where)
    return errors
