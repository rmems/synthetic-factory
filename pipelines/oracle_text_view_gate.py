"""Which records may become rows: the positive-example gate and the seal check.

A record is a positive example only when it belongs to one of the five
families, declares ``validation.status == "accepted"`` and
``validation.publishable is True``, carries ``provenance.kind == "simulated"``,
attributes its result to the oracle it declares (``result.produced_by ==
oracle.id``), still matches the ``proposal_hash`` and ``result_hash`` it was
sealed with, and projects into a public view, a label and a choice answer that
is one of its options. Everything else -- a rejected record first among them --
is refused with a coded refusal rather than rendered. The gate reads stored
declarations; the CLI additionally refuses any run the shared oracle validator
does not authenticate, which is where those declarations are recomputed.
"""

from __future__ import annotations

import sys
from typing import Any

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("oracle_text_view_gate")
    from . import oracle_text_view_public as public
    from . import oracle_text_view_render as render
    from . import oracle_text_view_vocabulary as tv
    from .oracle_grounded import canon, envelope
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "oracle_text_view_gate"
    )
    import oracle_text_view_public as public
    import oracle_text_view_render as render
    import oracle_text_view_vocabulary as tv
    from oracle_grounded import canon, envelope

__all__ = ["is_positive", "positive_problems", "refusal_of", "require_positive", "seal_findings"]


def _section(record: dict[str, Any], name: str) -> dict[str, Any]:
    value = record.get(name)
    return value if isinstance(value, dict) else {}


def positive_problems(record: dict[str, Any]) -> list[str]:
    """Each stored declaration that keeps ``record`` from being a positive example."""

    validation = _section(record, "validation")
    oracle_id = _section(record, "oracle").get("id")
    produced_by = _section(record, "result").get("produced_by")
    checks = (
        (validation.get("status") == tv.STATUS_ACCEPTED,
         f"validation.status is {tv.shown(validation.get('status'))}, not accepted"),
        (validation.get("publishable") is True, "validation.publishable is not true"),
        (_section(record, "provenance").get("kind") == tv.PROVENANCE_SIMULATED,
         "provenance.kind is not simulated"),
        (isinstance(oracle_id, str) and bool(oracle_id) and produced_by == oracle_id,
         f"result.produced_by {tv.shown(produced_by)} is not oracle.id {tv.shown(oracle_id)}"),
    )
    return [problem for holds, problem in checks if not holds]


def _digest_or_none(value: Any) -> str | None:
    try:
        return canon.digest(value)
    except (TypeError, ValueError):
        return None


def seal_findings(record: dict[str, Any]) -> list[str]:
    """Leak codes for a scenario or measurement that no longer matches its stored hash."""

    findings = []
    proposal = _digest_or_none(envelope.proposal_of(record))
    if proposal is None or record.get("proposal_hash") != proposal:
        findings.append(tv.LEAK_PROPOSAL_DIGEST_MISMATCH)
    measurement = _digest_or_none(record.get("result"))
    if measurement is None or record.get("result_hash") != measurement:
        findings.append(tv.LEAK_MEASUREMENT_DIGEST_MISMATCH)
    return findings


def refusal_of(record: Any) -> tuple[str, str] | None:
    """``(code, message)`` refusing ``record`` as a positive example, or None."""

    try:
        public.family_of(record)
    except tv.TextViewRefusal as exc:
        return exc.code, exc.message
    problems = positive_problems(record)
    if problems:
        return tv.FINDING_RECORD_NOT_A_POSITIVE_EXAMPLE, "; ".join(problems)
    unsealed = seal_findings(record)
    if unsealed:
        return tv.FINDING_RECORD_NOT_SEALED, "stored hashes do not cover: " + ", ".join(unsealed)
    try:
        render.render_row(record, tv.KIND_CHOICE)
    except tv.TextViewRefusal as exc:
        return exc.code, exc.message
    return None


def is_positive(record: Any) -> bool:
    """Accepted, publishable, simulated, self-attributed, sealed and projectable."""

    return refusal_of(record) is None


def require_positive(record: Any) -> None:
    """Raise the coded refusal ``refusal_of`` names; return quietly for a positive record."""

    refusal = refusal_of(record)
    if refusal is not None:
        tv.refuse(*refusal)


if __package__:
    _expose_package_sibling(__name__)
