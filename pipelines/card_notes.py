#!/usr/bin/env python3
"""What a Hub card may say about the NOTES files published beside its raw rounds.

Issue #405: ``observability-debug-trajectories`` reached Hub main with raw
batches for 1435 rounds but NOTES files for only 974 (``r38`` through ``r498``
missing), while its card said only that notes live under
``data/metadata/NOTES-*.md``. A card must state the coverage of the files it
actually publishes: every round, or exactly which rounds have none. It never
invents notes to close a hole.

This module is pure: callers pass the round numbers parsed from the published
payload and note names, and get back the card sentence.
"""

from __future__ import annotations

import dataclasses
import re
import sys
from collections.abc import Iterable

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("card_notes")
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "card_notes"
    )

# The sentence every card carried before coverage was reported. It is still
# rendered when a caller supplies no coverage, so legacy callers keep
# byte-identical cards.
LEGACY_NOTES_SENTENCE = "Supporting notes are under\n`data/metadata/NOTES-*.md`."


@dataclasses.dataclass(frozen=True)
class NotesCoverage:
    """How many published rounds carry a published NOTES file, and which do not."""

    rounds: int
    noted: int
    missing: tuple[tuple[int, int], ...]


def notes_coverage(published: Iterable[int], noted: Iterable[int]) -> NotesCoverage:
    """Compare published round numbers with the rounds that have notes.

    A note for a round that is not published cannot be claimed by the card, so
    only notes on published rounds count toward coverage.
    """
    rounds = set(published)
    covered = rounds & set(noted)
    return NotesCoverage(
        rounds=len(rounds),
        noted=len(covered),
        missing=missing_spans(rounds - covered),
    )


def round_numbers(pattern: re.Pattern[str], names: Iterable[str]) -> set[int]:
    """Return the round number (first group) of every name the pattern matches."""
    return {
        int(match.group(1))
        for name in names
        if (match := pattern.fullmatch(name)) is not None
    }


def pop_notes_keyword(keywords: dict[str, object]) -> NotesCoverage | None:
    """Pop a card renderer's notes= coverage, refusing anything but NotesCoverage."""
    notes = keywords.pop("notes", None)
    if notes is None or isinstance(notes, NotesCoverage):
        return notes
    raise TypeError("render_card() notes= takes a card_notes.NotesCoverage")


def missing_spans(rounds: Iterable[int]) -> tuple[tuple[int, int], ...]:
    """Collapse round numbers into sorted, inclusive, contiguous spans."""
    spans: list[tuple[int, int]] = []
    for number in sorted(set(rounds)):
        if spans and spans[-1][1] + 1 == number:
            spans[-1] = (spans[-1][0], number)
        else:
            spans.append((number, number))
    return tuple(spans)


def render_notes_sentence(coverage: NotesCoverage | None) -> str:
    """Return the card's NOTES sentence for the published coverage."""
    if coverage is None or coverage.rounds == 0:
        return LEGACY_NOTES_SENTENCE
    if not coverage.missing:
        return (
            "Supporting notes are under\n`data/metadata/NOTES-*.md`; every one of "
            f"the {coverage.rounds} published rounds has one."
        )
    if coverage.noted == 0:
        return (
            "No supporting `data/metadata/NOTES-*.md` file is published for any of "
            f"the {coverage.rounds} published rounds."
        )
    return _partial_coverage_sentence(coverage)


def _partial_coverage_sentence(coverage: NotesCoverage) -> str:
    absent = coverage.rounds - coverage.noted
    return (
        "Supporting notes are under\n`data/metadata/NOTES-*.md` for "
        f"{coverage.noted} of the {coverage.rounds} published rounds. The other "
        f"{absent} have no published NOTES file: {_describe_spans(coverage.missing)}. "
        "Their raw batches are published unchanged, and no NOTES file is written "
        "after the fact to fill the gap."
    )


def _describe_spans(spans: tuple[tuple[int, int], ...]) -> str:
    """Name every missing span: a disclosure that elides rounds is not one."""
    return ", ".join(_describe_span(first, last) for first, last in spans)


def _describe_span(first: int, last: int) -> str:
    if first == last:
        return f"`r{first:02d}`"
    return f"`r{first:02d}`–`r{last:02d}` ({last - first + 1} rounds)"


if __package__:
    # One module object for both import forms, so NotesCoverage keeps one class
    # identity and pop_notes_keyword accepts it whichever form loaded first.
    _expose_package_sibling(__name__)
