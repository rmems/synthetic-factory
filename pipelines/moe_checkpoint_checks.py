#!/usr/bin/env python3
"""Sealed-checkpoint and router-logits checks for ``moe-router-distillation-trajectories``.

Split out of ``moe_check.py`` verbatim: pin the recorded teacher's checkpoint
and Hub card against the sealed revisions, classify transformer/grounded
claims, and verify the recorded teacher logits.
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
    from .moe_featurizer import (
        COMMIT_SHA_RE,
        SEALED_HUB_MOE_CARDS,
        SEALED_HUB_MOE_REVISIONS,
        TRANSFORMERS_MOE_IMPLEMENTATION,
    )
    from .moe_oracles import TransformersMoERouter
else:
    from moe_featurizer import (
        COMMIT_SHA_RE,
        SEALED_HUB_MOE_CARDS,
        SEALED_HUB_MOE_REVISIONS,
        TRANSFORMERS_MOE_IMPLEMENTATION,
    )
    from moe_oracles import TransformersMoERouter


def _sealed_hub_card(fingerprint: Any) -> dict[str, int] | None:
    """The sealed Hub MoE card for ``fingerprint.model``, when one exists."""

    if not isinstance(fingerprint, dict):
        return None
    model = fingerprint.get("model")
    if isinstance(model, str):
        return SEALED_HUB_MOE_CARDS.get(model.strip())
    return None

def _is_authoritative_teacher_grounded(oracle: Any, result: Any) -> bool:
    """True when the record claims an authoritative LLM teacher trajectory."""

    if not isinstance(oracle, dict) or not isinstance(result, dict):
        return False
    if oracle.get("authority") != oc.AUTHORITY_AUTHORITATIVE:
        return False
    return (
        result.get("is_llm_teacher") is True
        and result.get("teacher_grounded") is True
    )

def _claims_transformers(oracle: Any) -> bool:
    """Either known producer field keeps the Transformers contract active."""

    return isinstance(oracle, dict) and (
        oracle.get("name") == TransformersMoERouter.name
        or oracle.get("implementation") == TRANSFORMERS_MOE_IMPLEMENTATION
    )

def _claims_transformers_or_sealed_moe(oracle: Any, fingerprint: Any) -> bool:
    """A Transformers producer identity or a sealed Hub MoE card model."""

    return _claims_transformers(oracle) or _sealed_hub_card(fingerprint) is not None

def _check_authoritative_checkpoint(
    oracle: Any, fingerprint: Any, where: str
) -> list[str]:
    """An authoritative router record must pin an immutable checkpoint.

    ``resolve_checkpoint`` protects the live Transformers adapter, but a
    replayed recording could otherwise carry ``revision_or_checkpoint:
    "main"`` — a mutable name under which different weight revisions share
    one teacher identity while the configuration digest stays the same.

    For models on :data:`SEALED_HUB_MOE_CARDS`, a format-valid 40-hex string is
    still insufficient: the ``(model, revision)`` pair must appear in
    :data:`SEALED_HUB_MOE_REVISIONS` with a matching ``configuration_sha256``.
    No Hub network calls — unbound digests fail closed.
    """

    if not isinstance(oracle, dict):
        return []
    if not isinstance(fingerprint, dict):
        return []
    if oracle.get("authority") != oc.AUTHORITY_AUTHORITATIVE:
        return []
    revision = fingerprint.get("revision_or_checkpoint")
    if not isinstance(revision, str) or not COMMIT_SHA_RE.match(revision.strip()):
        return [
            f"{where}.oracle.fingerprint.revision_or_checkpoint must be a "
            f"resolved 40-hex commit for an authoritative router record, got "
            f"{revision!r} — a mutable name can serve different weights under "
            "one recorded identity"
        ]
    return _check_sealed_checkpoint(fingerprint, revision.strip(), where)

def _check_sealed_checkpoint(
    fingerprint: dict[str, Any], revision: str, where: str
) -> list[str]:
    """Bind a format-valid checkpoint to the sealed (model, revision) digest."""

    model = fingerprint.get("model")
    if not isinstance(model, str) or model.strip() not in SEALED_HUB_MOE_CARDS:
        return []
    model = model.strip()
    sealed_digest = SEALED_HUB_MOE_REVISIONS.get((model, revision))
    config_digest = fingerprint.get("configuration_sha256")
    if sealed_digest is None:
        return [
            f"{where}.oracle.fingerprint: UNBOUND_HUB_REVISION — "
            f"revision_or_checkpoint {revision!r} is not a sealed "
            f"(model, revision) for {model!r}; format-valid 40-hex alone "
            "does not bind an authoritative teacher checkpoint"
        ]
    if not isinstance(config_digest, str) or config_digest != sealed_digest:
        return [
            f"{where}.oracle.fingerprint: UNBOUND_HUB_REVISION — "
            f"configuration_sha256 must match the sealed digest for "
            f"({model!r}, {revision!r})"
        ]
    return []

def _check_sealed_hub_cardinality(
    fingerprint: Any, oracle: Any, result: Any, where: str
) -> list[str]:
    """Bind declared depth/experts to the sealed Hub card for the model.

    Authoritative teacher-grounded records whose ``fingerprint.model`` matches
    a sealed card may not self-attest a different ``num_layers`` /
    ``num_local_experts`` / ``num_experts_per_tok``.
    """

    if not _is_authoritative_teacher_grounded(oracle, result):
        return []
    card = _sealed_hub_card(fingerprint)
    if card is None or not isinstance(fingerprint, dict):
        return []
    checks = (
        ("num_layers", card["num_hidden_layers"], "num_hidden_layers"),
        ("num_local_experts", card["num_local_experts"], "num_local_experts"),
        ("num_experts_per_tok", card["num_experts_per_tok"], "num_experts_per_tok"),
    )
    model = str(fingerprint.get("model")).strip()
    return [
        f"{where}.oracle.fingerprint: SEALED_HUB_MOE_CARDINALITY — "
        f"{field} is {fingerprint.get(field)!r} but sealed Hub card for "
        f"{model!r} has {card_field}={expected}"
        for field, expected, card_field in checks
        if fingerprint.get(field) != expected
    ]

def _check_teacher_router_logits(
    layers: list[Any], record: dict[str, Any], where: str
) -> list[str]:
    """Authoritative Transformers / sealed-card teachers must expose logits.

    Fabricated top-k without a teacher run omits ``router_logits``; requiring
    them (with the existing ordering check) closes that launder. Recorded
    teachers that are not TransformersMoERouter and not on a sealed card may
    still omit logits.
    """

    oracle = record.get("oracle")
    result = record.get("result")
    if not _is_authoritative_teacher_grounded(oracle, result):
        return []
    fingerprint = oracle.get("fingerprint")
    if not _claims_transformers_or_sealed_moe(oracle, fingerprint):
        return []
    return [
        f"{where}.result.routing.layers[{index}]: "
        "TEACHER_ROUTER_LOGITS_REQUIRED — authoritative "
        "TransformersMoERouter / sealed Hub MoE teacher records must "
        "expose router_logits so top_k can be rebound to a real gate"
        for index, layer in enumerate(layers)
        if _layer_missing_logits(layer)
    ]


def _layer_missing_logits(layer: Any) -> bool:
    return isinstance(layer, dict) and layer.get("router_logits") is None
