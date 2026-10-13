#!/usr/bin/env python3
"""Hub card claims a code-repair release can make, derived from its evidence (#420).

A card's verification sentence is a claim about ``REPLAY.json`` and its contents
line is a claim about ``RUN.json``, so both are rendered from those files and
checked against them rather than written as prose. ``REPLAY.json``'s top-level
``status`` is computed over the replayed positives only: ``passed`` with 35 of 132
records not replayed is a partial replay, never "the full batch passed".
``MUTATION_NO_SITES`` in ``RUN.json`` ``skips`` counts catalog programs left out
of the draw pool before drawing starts; those programs use no draws, so they
never explain a shortfall between requested and produced candidates.

Inconsistent evidence (counts that do not add up, a not-replayed list that
disagrees with its count, a run and a replay of different sizes) raises
:class:`CardClaimError`: no claim is rendered from evidence that contradicts itself.
"""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass
from typing import Any, TypeGuard

from . import vocabulary as cv
from ._contract import bind_import_twin, load_strict_json

REPLAY_EVIDENCE = "evidence/REPLAY.json"
RUN_EVIDENCE = "evidence/RUN.json"
VERIFICATION_MARKER = "> **Verification:**"
DRAW_POOL_PHRASE = "excluded from the draw pool"
# Wording that sells failures or a partial replay as a clean full one; #420 found "full batch".
PASS_OVERCLAIMS = (
    "full batch passed", "entire batch passed", "whole batch passed", "every candidate passed",
    "all candidates passed",
)
COVERAGE_OVERCLAIMS = ("full batch", "entire batch", "whole batch")
# Plain-English names a card may give a draw-skip reason instead of its code.
SKIP_REASON_WORDS = {cv.SKIP_DUPLICATE_MUTANT_IN_RUN: ("duplicate mutant",)}

__all__ = [
    "CardClaimError", "ReplayCoverage", "card_claim_errors", "contents_statement",
    "load_evidence", "replay_coverage", "split_statement", "verification_statement",
]

Tally = tuple[tuple[str, int], ...]


class CardClaimError(ValueError):
    """The evidence cannot support any card claim because it contradicts itself."""


@dataclass(frozen=True)
class ReplayCoverage:
    """What ``REPLAY.json`` proves: how many records replayed, passed, failed or were skipped."""

    status: str
    records: int
    passed: int
    failed: int
    not_replayed: int
    not_replayed_outcomes: Tally
    not_replayed_statuses: Tally

    @property
    def complete(self) -> bool:
        """Every record was replayed and passed."""
        return self.passed == self.records

    @property
    def fully_replayed(self) -> bool:
        """Every record was replayed, whether or not it passed."""
        return self.not_replayed == 0


def load_evidence(text: str | bytes, path: str) -> dict[str, Any]:
    """Parse one evidence file strictly (no duplicate keys, no NaN) into a JSON object."""

    try:
        payload = load_strict_json(text)
    except ValueError as error:
        raise CardClaimError(f"{path} is invalid JSON: {error}") from error
    if not isinstance(payload, dict):
        raise CardClaimError(f"{path} must contain a JSON object")
    return payload


def _is_count(value: Any) -> TypeGuard[int]:
    if isinstance(value, bool):  # JSON true is not a count
        return False
    return isinstance(value, int) and value >= 0


def _count(mapping: Any, key: str, where: str) -> int:
    value = mapping.get(key) if isinstance(mapping, dict) else None
    if _is_count(value):
        return value
    raise CardClaimError(f"{where} needs a non-negative integer {key!r}")


def _counted(values: list[Any]) -> Tally:
    return tuple(sorted(Counter(str(v) for v in values).items()))


def _entry_kind(entry: Any) -> str:
    """Classify one REPLAY.json entry: passed, failed, not_replayed or malformed."""
    status = entry.get("status") if isinstance(entry, dict) else None
    if status == "not_replayed":
        return "not_replayed"
    if status != "replayed":
        return "malformed"
    return "passed" if entry.get("code") == cv.REPLAY_PASSED else "failed"


def _listed_entries(replay: dict[str, Any], counts: dict[str, int]) -> list[dict[str, Any]]:
    """The per-record list, refused unless it reconciles with every summary count."""

    entries = replay.get("records")
    if not isinstance(entries, list):
        raise CardClaimError(f"{REPLAY_EVIDENCE} needs a 'records' list")
    listed = Counter(_entry_kind(entry) for entry in entries)
    for kind, expected in {**counts, "malformed": 0}.items():
        if listed[kind] != expected:
            raise CardClaimError(
                f"{REPLAY_EVIDENCE} lists {listed[kind]} {kind} records but counts {expected}"
            )
    return entries


def _summary_counts(replay: Any) -> tuple[int, int, int, int]:
    """``records, passed, failed, not_replayed`` from ``counts``, refused unless they add up."""

    counts = replay.get("counts") if isinstance(replay, dict) else None
    records, passed, failed, not_replayed = (
        _count(counts, key, f"{REPLAY_EVIDENCE} counts")
        for key in ("records", "passed", "failed", "not_replayed")
    )
    if passed + failed + not_replayed != records:
        raise CardClaimError(
            f"{REPLAY_EVIDENCE} counts do not add up: {passed} passed + {failed} failed + "
            f"{not_replayed} not replayed != {records} records"
        )
    return records, passed, failed, not_replayed


def replay_coverage(replay: dict[str, Any]) -> ReplayCoverage:
    """Read the replay coverage ``REPLAY.json`` supports, refusing evidence that disagrees."""

    records, passed, failed, not_replayed = _summary_counts(replay)
    status = replay.get("status")
    if not isinstance(status, str):
        raise CardClaimError(f"{REPLAY_EVIDENCE} needs a string 'status'")
    entries = _listed_entries(
        replay, {"passed": passed, "failed": failed, "not_replayed": not_replayed}
    )
    skipped = [entry for entry in entries if _entry_kind(entry) == "not_replayed"]
    return ReplayCoverage(
        status, records, passed, failed, not_replayed,
        _counted([e.get("outcome") for e in skipped]),
        _counted([e.get("oracle_status") for e in skipped]),
    )


def _tally(mapping: Any, where: str) -> Tally:
    if not isinstance(mapping, dict):
        raise CardClaimError(f"{where} must be an object of counts")
    return tuple((str(key), _count(mapping, key, where)) for key in sorted(mapping))


def _joined(tally: Tally) -> str:
    parts = [f"{n} {name}" for name, n in tally]
    if len(parts) < 2:
        return "".join(parts)
    return ", ".join(parts[:-1]) + " and " + parts[-1]


def verification_statement(coverage: ReplayCoverage) -> str:
    """The card's replay sentence, stating exactly the coverage ``REPLAY.json`` reports."""

    source = f"independent replay (`{REPLAY_EVIDENCE}`)"
    if coverage.complete:
        return (
            f"{source} re-executed all {coverage.records} candidates and every one passed "
            f"(`status: {coverage.status}`)."
        )
    if coverage.fully_replayed:
        return (
            f"{source} re-executed all {coverage.records} candidates: {coverage.passed} of "
            f"{coverage.records} passed and {coverage.failed} failed (`status: {coverage.status}`)."
        )
    return (
        f"{source} covered only part of the batch: {coverage.passed} of {coverage.records} "
        f"candidates replayed and passed, {coverage.failed} failed, and {coverage.not_replayed} "
        f"not replayed ({_joined(coverage.not_replayed_outcomes)}; oracle statuses "
        f"{_joined(coverage.not_replayed_statuses)}); its overall `status: {coverage.status}` "
        "applies to the replayed subset only."
    )


def split_statement(run: dict[str, Any]) -> str:
    """The outcome and oracle-status mix ``RUN.json`` records for the candidates."""

    records = _count(run, "records", RUN_EVIDENCE)
    outcomes = _joined(_tally(run.get("outcomes"), f"{RUN_EVIDENCE} outcomes"))
    statuses = _joined(_tally(run.get("oracle_statuses"), f"{RUN_EVIDENCE} oracle_statuses"))
    return (
        f"The {records} rows mix {outcomes} outcomes, with {statuses} oracle statuses "
        f"(`{RUN_EVIDENCE}`)."
    )


def _skips(run: dict[str, Any]) -> tuple[Tally, int]:
    tally = _tally(run.get("skips", {}), f"{RUN_EVIDENCE} skips")
    draws = tuple((code, n) for code, n in tally if code != cv.SKIP_MUTATION_NO_SITES)
    return draws, dict(tally).get(cv.SKIP_MUTATION_NO_SITES, 0)


def _program_count(run: dict[str, Any]) -> int:
    return _count(run.get("catalog"), "program_count", f"{RUN_EVIDENCE} catalog")


def contents_statement(run: dict[str, Any]) -> str:
    """Produced versus requested candidates, with draw skips kept apart from pool exclusions."""

    records, requested = _count(run, "records", RUN_EVIDENCE), _count(run, "count", RUN_EVIDENCE)
    draws, siteless = _skips(run)
    skipped = "; ".join(f"{n} draws skipped as `{code}`" for code, n in draws) or "no draws skipped"
    statement = f"{records} candidates from {requested} requested draws ({skipped})"
    if not siteless:
        return statement + "."
    return (
        f"{statement}; separately, {siteless} of the {_program_count(run)} catalog programs "
        f"have no mutation sites and were {DRAW_POOL_PHRASE}, so they used no draws."
    )


def _flat(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _mentions(text: str, phrase: str) -> bool:
    """Whole-phrase match, so '10 failed' never stands in for '0 failed'."""
    pattern = rf"(?<!\w){re.escape(phrase)}(?!\w)"  # escaped: a literal, so linear time
    return re.search(pattern, text, re.IGNORECASE) is not None


def _verification_text(card: str) -> str | None:
    """Every ``> **Verification:**`` blockquote on the card, flattened into one text."""

    blocks: list[list[str]] = []
    current: list[str] | None = None
    for line in card.splitlines():
        if line.startswith(VERIFICATION_MARKER):
            current = []
            blocks.append(current)
        if current is not None and line.startswith(">"):
            current.append(line[1:])
        else:
            current = None
    return _flat(" ".join(" ".join(block) for block in blocks)) if blocks else None


def _claim_rules(coverage: ReplayCoverage) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """The phrases a Verification statement must carry, and those it must not."""

    status = f"status: {coverage.status}"
    if coverage.complete:
        return (f"all {coverage.records}", status), ()
    required = (f"{coverage.passed} of {coverage.records}", f"{coverage.failed} failed", status)
    if coverage.fully_replayed:
        return required, PASS_OVERCLAIMS
    breakdown = tuple(f"{n} {outcome}" for outcome, n in coverage.not_replayed_outcomes)
    return (
        (*required, f"{coverage.not_replayed} not replayed", *breakdown),
        (*PASS_OVERCLAIMS, *COVERAGE_OVERCLAIMS, f"all {coverage.records}"),
    )


def _overclaim_scope(phrase: str, card: str, verification: str) -> str:
    """Pass overclaims are false anywhere on the card; coverage wording only where coverage
    is stated, since body text such as "all 132 rows carry evidence" can be true."""
    return _flat(card) if phrase in PASS_OVERCLAIMS else verification


def _replay_errors(card: str, coverage: ReplayCoverage) -> list[str]:
    text = _verification_text(card)
    if text is None:
        return [f"card has no {VERIFICATION_MARKER!r} statement"]
    required, forbidden = _claim_rules(coverage)
    facts = (
        f"{coverage.passed} of {coverage.records} passed, {coverage.failed} failed, "
        f"{coverage.not_replayed} not replayed"
    )
    errors = [
        f"Card overclaims replay ({phrase!r}): {facts}"
        for phrase in forbidden if _mentions(_overclaim_scope(phrase, card, text), phrase)
    ]
    errors.extend(
        f"Verification must state {phrase!r} from {REPLAY_EVIDENCE}"
        for phrase in required if not _mentions(text, phrase)
    )
    return errors


Requirement = tuple[str, tuple[str, ...]]  # a phrase and the reasons it must sit beside


def _skip_reasons(code: str) -> tuple[str, ...]:
    return (code.lower(), *SKIP_REASON_WORDS.get(code, ()))


def _contents_requirements(run: dict[str, Any]) -> tuple[Requirement, ...]:
    """Contents phrases; each skip count must share a clause with its own reason."""

    draws, siteless = _skips(run)
    requirements: tuple[Requirement, ...] = (
        (f"{_count(run, 'records', RUN_EVIDENCE)} candidates", ()),
        (f"{_count(run, 'count', RUN_EVIDENCE)} requested", ()),
        *((f"{n} draws", _skip_reasons(code)) for code, n in draws),
    )
    if not siteless:
        return requirements
    pool = f"{siteless} of the {_program_count(run)} catalog programs"
    return (*requirements, (pool, (DRAW_POOL_PHRASE,)))


def _body_text(card: str) -> str:
    """The card outside its blockquotes, where the contents statement lives, so a
    Verification phrase such as "97 of 132 candidates" never stands in for it."""
    return _flat(" ".join(line for line in card.splitlines() if not line.lstrip().startswith(">")))


def _clauses(card: str) -> list[str]:
    """Clauses of the card body. Parentheses stay inside a clause, so
    "18 draws (skipped as duplicate mutants)" keeps the count with its reason."""
    return re.split(r"[.;:]", _body_text(card))


def _states(clauses: list[str], requirement: Requirement) -> bool:
    phrase, reasons = requirement
    return any(
        _mentions(clause, phrase) and _gives_reason(clause.lower(), reasons) for clause in clauses
    )


def _gives_reason(clause: str, reasons: tuple[str, ...]) -> bool:
    return not reasons or any(reason in clause for reason in reasons)


def _requirement_error(requirement: Requirement) -> str:
    phrase, reasons = requirement
    if not reasons:
        return f"card must state {phrase!r} from {RUN_EVIDENCE}"
    named = " or ".join(repr(reason) for reason in reasons)
    return f"card must state {phrase!r} beside its reason ({named}) from {RUN_EVIDENCE}"


def _run_errors(card: str, run: dict[str, Any]) -> list[str]:
    tallies = (
        *_tally(run.get("outcomes"), f"{RUN_EVIDENCE} outcomes"),
        *_tally(run.get("oracle_statuses"), f"{RUN_EVIDENCE} oracle_statuses"),
    )
    flat, clauses = _flat(card), _clauses(card)
    errors = [
        f"card must state {f'{n} {name}'!r} from {RUN_EVIDENCE}"
        for name, n in tallies if not _mentions(flat, f"{n} {name}")
    ]
    return errors + [
        _requirement_error(requirement)
        for requirement in _contents_requirements(run) if not _states(clauses, requirement)
    ]


def _check_run_totals(run: dict[str, Any], records: int) -> None:
    """Each RUN.json tally must count every record exactly once."""

    for key in ("outcomes", "oracle_statuses"):
        total = sum(n for _, n in _tally(run.get(key), f"{RUN_EVIDENCE} {key}"))
        if total != records:
            raise CardClaimError(f"{RUN_EVIDENCE} {key} sum to {total}, not {records} records")


def card_claim_errors(card: str, replay: dict[str, Any], run: dict[str, Any]) -> list[str]:
    """Every card claim the replay and run evidence does not support; empty when honest."""

    coverage = replay_coverage(replay)
    records = _count(run, "records", RUN_EVIDENCE)
    if records != coverage.records:
        raise CardClaimError(
            f"{RUN_EVIDENCE} has {records} records but {REPLAY_EVIDENCE} covers {coverage.records}"
        )
    _check_run_totals(run, records)
    return [*_replay_errors(card, coverage), *_run_errors(card, run)]


bind_import_twin(__name__)
