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
from typing import Any

from . import vocabulary as cv
from ._contract import bind_import_twin, load_strict_json

REPLAY_EVIDENCE = "evidence/REPLAY.json"
RUN_EVIDENCE = "evidence/RUN.json"
VERIFICATION_MARKER = "> **Verification:**"
DRAW_POOL_PHRASE = "excluded from the draw pool"
# Wording that sells a partial replay as a complete one; issue #420 found the first.
OVERCLAIM_PHRASES = ("full batch", "entire batch", "whole batch", "every candidate passed")

__all__ = [
    "CardClaimError", "ReplayCoverage", "card_claim_errors", "contents_statement",
    "load_evidence", "replay_coverage", "split_statement", "verification_statement",
]


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
    not_replayed_by_kind: tuple[tuple[str, int], ...]

    @property
    def complete(self) -> bool:
        return self.passed == self.records


def load_evidence(text: str | bytes, path: str) -> dict[str, Any]:
    """Parse one evidence file strictly (no duplicate keys, no NaN) into a JSON object."""

    try:
        payload = load_strict_json(text)
    except ValueError as error:
        raise CardClaimError(f"{path} is invalid JSON: {error}") from error
    if not isinstance(payload, dict):
        raise CardClaimError(f"{path} must contain a JSON object")
    return payload


def _is_count(value: Any) -> bool:
    if isinstance(value, bool):  # JSON true is not a count
        return False
    return isinstance(value, int) and value >= 0


def _count(mapping: Any, key: str, where: str) -> int:
    value = mapping.get(key) if isinstance(mapping, dict) else None
    if not _is_count(value):
        raise CardClaimError(f"{where} needs a non-negative integer {key!r}")
    return value


def _not_replayed_kind(entry: dict[str, Any]) -> str:
    return f"{entry.get('outcome')} with oracle status {entry.get('oracle_status')}"


def _not_replayed_kinds(replay: dict[str, Any], expected: int) -> tuple[tuple[str, int], ...]:
    entries = replay.get("records")
    if not isinstance(entries, list):
        raise CardClaimError(f"{REPLAY_EVIDENCE} needs a 'records' list")
    skipped = [e for e in entries if isinstance(e, dict) and e.get("status") == "not_replayed"]
    if len(skipped) != expected:
        raise CardClaimError(
            f"{REPLAY_EVIDENCE} lists {len(skipped)} not-replayed records but counts {expected}"
        )
    return tuple(sorted(Counter(_not_replayed_kind(e) for e in skipped).items()))


def replay_coverage(replay: dict[str, Any]) -> ReplayCoverage:
    """Read the replay coverage ``REPLAY.json`` supports, refusing counts that do not add up."""

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
    status = replay.get("status")
    if not isinstance(status, str):
        raise CardClaimError(f"{REPLAY_EVIDENCE} needs a string 'status'")
    kinds = _not_replayed_kinds(replay, not_replayed)
    return ReplayCoverage(status, records, passed, failed, not_replayed, kinds)


def _tally(mapping: Any, where: str) -> tuple[tuple[str, int], ...]:
    if not isinstance(mapping, dict):
        raise CardClaimError(f"{where} must be an object of counts")
    return tuple((str(key), _count(mapping, key, where)) for key in sorted(mapping))


def _joined(tally: tuple[tuple[str, int], ...]) -> str:
    parts = [f"{n} {name}" for name, n in tally]
    return parts[0] if len(parts) == 1 else ", ".join(parts[:-1]) + " and " + parts[-1]


def verification_statement(coverage: ReplayCoverage) -> str:
    """The card's replay sentence, stating exactly the coverage ``REPLAY.json`` reports."""

    if coverage.complete:
        return (
            f"independent replay (`{REPLAY_EVIDENCE}`) re-executed all {coverage.records} "
            f"candidates and every one passed (`status: {coverage.status}`)."
        )
    breakdown = _joined(coverage.not_replayed_by_kind) or "none listed"
    return (
        f"independent replay (`{REPLAY_EVIDENCE}`) covered only part of the batch: "
        f"{coverage.passed} of {coverage.records} candidates replayed and passed, "
        f"{coverage.failed} failed, and {coverage.not_replayed} not replayed ({breakdown}); "
        f"its overall `status: {coverage.status}` applies to the replayed subset only."
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


def _skips(run: dict[str, Any]) -> tuple[tuple[tuple[str, int], ...], int]:
    tally = _tally(run.get("skips", {}), f"{RUN_EVIDENCE} skips")
    draws = tuple((code, n) for code, n in tally if code != cv.SKIP_MUTATION_NO_SITES)
    return draws, dict(tally).get(cv.SKIP_MUTATION_NO_SITES, 0)


def contents_statement(run: dict[str, Any]) -> str:
    """Produced versus requested candidates, with draw skips kept apart from pool exclusions."""

    records, requested = _count(run, "records", RUN_EVIDENCE), _count(run, "count", RUN_EVIDENCE)
    draws, siteless = _skips(run)
    skipped = "; ".join(f"{n} draws skipped as `{code}`" for code, n in draws) or "no draws skipped"
    statement = f"{records} candidates from {requested} requested draws ({skipped})"
    if not siteless:
        return statement + "."
    programs = _count(run.get("catalog"), "program_count", f"{RUN_EVIDENCE} catalog")
    return (
        f"{statement}; separately, {siteless} of the {programs} catalog programs have no "
        f"mutation sites and were {DRAW_POOL_PHRASE}, so they used no draws."
    )


def _flat(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _verification_block(card: str) -> str | None:
    lines = card.splitlines()
    starts = [i for i, line in enumerate(lines) if line.startswith(VERIFICATION_MARKER)]
    if not starts:
        return None
    block = []
    for line in lines[starts[0]:]:
        if not line.startswith(">"):
            break
        block.append(line[1:])
    return _flat(" ".join(block))


def _partial_replay_errors(block: str, coverage: ReplayCoverage) -> list[str]:
    errors = [
        f"Verification claims a complete replay ({phrase!r}) but {coverage.not_replayed} of "
        f"{coverage.records} records were not replayed"
        for phrase in (*OVERCLAIM_PHRASES, f"all {coverage.records}")
        if phrase in block.lower()
    ]
    required = (
        f"{coverage.passed} of {coverage.records}", f"{coverage.failed} failed",
        f"{coverage.not_replayed} not replayed",
    )
    errors.extend(
        f"Verification must state {phrase!r} from {REPLAY_EVIDENCE}"
        for phrase in required if phrase not in block
    )
    return errors


def _replay_errors(card: str, coverage: ReplayCoverage) -> list[str]:
    block = _verification_block(card)
    if block is None:
        return [f"card has no {VERIFICATION_MARKER!r} statement"]
    return [] if coverage.complete else _partial_replay_errors(block, coverage)


def _run_errors(card: str, run: dict[str, Any]) -> list[str]:
    flat = _flat(card)
    tallies = (
        *_tally(run.get("outcomes"), f"{RUN_EVIDENCE} outcomes"),
        *_tally(run.get("oracle_statuses"), f"{RUN_EVIDENCE} oracle_statuses"),
    )
    errors = [
        f"card must disclose '{n} {name}' from {RUN_EVIDENCE}"
        for name, n in tallies if f"{n} {name}" not in flat
    ]
    if _skips(run)[1] and DRAW_POOL_PHRASE not in flat:
        errors.append(
            f"card must say the {cv.SKIP_MUTATION_NO_SITES} programs were {DRAW_POOL_PHRASE}, "
            "not count them as skipped draws"
        )
    return errors


def card_claim_errors(card: str, replay: dict[str, Any], run: dict[str, Any]) -> list[str]:
    """Every card claim the replay and run evidence does not support; empty when honest."""

    coverage = replay_coverage(replay)
    records = _count(run, "records", RUN_EVIDENCE)
    if records != coverage.records:
        raise CardClaimError(
            f"{RUN_EVIDENCE} has {records} records but {REPLAY_EVIDENCE} covers {coverage.records}"
        )
    return [*_replay_errors(card, coverage), *_run_errors(card, run)]


bind_import_twin(__name__)
