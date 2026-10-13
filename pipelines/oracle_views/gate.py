"""Which records may become rows: the positive-example gate and the seal check.

A record is a positive example only when it belongs to one of the five
families, declares ``validation.status == "accepted"`` and
``validation.publishable is True``, carries ``provenance.kind == "simulated"``,
attributes its result to the oracle it declares (``result.produced_by ==
oracle.id``), still matches the ``proposal_hash`` and ``result_hash`` it was
sealed with, projects into a public view, a label and a choice answer that is
one of its options, and replays to that same ``result_hash`` on the reference
oracle. Stored ``validation`` fields and a recomputed seal are not the verdict:
a resealed edit of ``result.measured`` is refused. Everything else -- a rejected
record first among them -- is refused with a coded refusal rather than rendered.
"""

from __future__ import annotations

from typing import Any

from . import public, render
from . import vocabulary as tv
from ._contract import bind_import_twin, canon, envelope, record as oracle_record

__all__ = ["is_positive", "positive_problems", "refusal_of", "require_positive", "seal_findings"]


def _section(record: dict[str, Any], name: str) -> dict[str, Any]:
    value = record.get(name)
    return value if isinstance(value, dict) else {}


def _self_attributed(record: dict[str, Any]) -> bool:
    oracle_id = _section(record, "oracle").get("id")
    produced_by = _section(record, "result").get("produced_by")
    return isinstance(oracle_id, str) and produced_by == oracle_id != ""


def positive_problems(record: dict[str, Any]) -> list[str]:
    """Each stored declaration that keeps ``record`` from being a positive example.

    These checks are necessary and not sufficient. :func:`refusal_of` also
    replays the measurement; a matching declaration with a resealed edit is
    still refused.
    """

    validation = _section(record, "validation")
    checks = (
        (validation.get("status") == tv.STATUS_ACCEPTED,
         f"validation.status is {tv.shown(validation.get('status'))}, not accepted"),
        (validation.get("publishable") is True, "validation.publishable is not true"),
        (_section(record, "provenance").get("kind") == tv.PROVENANCE_SIMULATED,
         "provenance.kind is not simulated"),
        (_self_attributed(record), "result.produced_by is not oracle.id"),
    )
    return [problem for holds, problem in checks if not holds]


def _digest_or_none(value: Any) -> str | None:
    try:
        return canon.digest(value)
    except (TypeError, ValueError):
        return None


def _seal_holds(stored: Any, value: Any) -> bool:
    digest = _digest_or_none(value)
    return digest is not None and stored == digest


def seal_findings(record: dict[str, Any]) -> list[str]:
    """Leak codes for a scenario or measurement that no longer matches its stored hash."""

    seals = (
        (record.get("proposal_hash"), envelope.proposal_of(record),
         tv.LEAK_PROPOSAL_DIGEST_MISMATCH),
        (record.get("result_hash"), record.get("result"), tv.LEAK_MEASUREMENT_DIGEST_MISMATCH),
    )
    return [code for stored, value, code in seals if not _seal_holds(stored, value)]


def _replay_detail(record: dict[str, Any]) -> str | None:
    try:
        status, detail = oracle_record.reproduce(record, environ={})
    except Exception as exc:  # one untrusted record must not escape the gate
        return f"reference replay could not run: {type(exc).__name__}"
    if status == "reproduced":
        return None
    return f"reference replay {status}: {detail}"


def _replay_problem(record: dict[str, Any]) -> str | None:
    """Why the reference oracle does not stand behind ``result_hash``, or None."""

    if _section(record, "oracle").get("implementation") != "reference":
        return "oracle.implementation is not the reference simulator"
    return _replay_detail(record)


def _projection_refusal(record: Any) -> tuple[str, str] | None:
    try:
        render.render_row(record, tv.KIND_CHOICE)
    except tv.TextViewRefusal as exc:
        return exc.code, exc.message
    return None


def _family_refusal(record: Any) -> tuple[str, str] | None:
    try:
        public.family_of(record)
    except tv.TextViewRefusal as exc:
        return exc.code, exc.message
    return None


def _declared_refusal(record: Any) -> tuple[str, str] | None:
    problems = positive_problems(record)
    if problems:
        return tv.FINDING_RECORD_NOT_A_POSITIVE_EXAMPLE, "; ".join(problems)
    unsealed = seal_findings(record)
    if not unsealed:
        return None
    return tv.FINDING_RECORD_NOT_SEALED, "stored hashes do not cover: " + ", ".join(unsealed)


def _replay_refusal(record: Any) -> tuple[str, str] | None:
    problem = _replay_problem(record)
    if problem is None:
        return None
    return tv.FINDING_RECORD_NOT_A_POSITIVE_EXAMPLE, problem


def refusal_of(record: Any) -> tuple[str, str] | None:
    """``(code, message)`` refusing ``record`` as a positive example, or None."""

    for check in (_family_refusal, _declared_refusal, _projection_refusal, _replay_refusal):
        refusal = check(record)
        if refusal is not None:
            return refusal
    return None


def is_positive(record: Any) -> bool:
    """Accepted, publishable, simulated, self-attributed, sealed, projectable, replayed."""

    return refusal_of(record) is None


def require_positive(record: Any) -> None:
    """Raise the coded refusal ``refusal_of`` names; return quietly for a positive record."""

    refusal = refusal_of(record)
    if refusal is not None:
        tv.refuse(*refusal)


bind_import_twin(__name__)
