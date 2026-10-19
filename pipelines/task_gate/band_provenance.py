#!/usr/bin/env python3
"""Provenance a self-generated row must carry: ``attempts``, ``successes`` and ``pass_rate``.

``check_row`` is the check the band writer applies to every row it emits and the one a
composing step can apply to any row of a train set. Only ``generator == "self"`` rows are
held to it; it is exact (``pass_rate`` must equal ``successes / attempts``), so a row cannot
claim a difficulty its counts do not support.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from . import band_vocabulary as bv
from . import vocabulary as cv
from ._contract import bind_import_twin
from .checks import is_int

__all__ = ["check_row", "problem_with"]


def _counts_problem(row: Mapping[str, Any]) -> str | None:
    attempts, successes = row.get("attempts"), row.get("successes")
    if not is_int(attempts) or attempts < 1:
        return "attempts must be a positive integer"
    if not is_int(successes) or not 0 <= successes <= attempts:
        return "successes must be an integer in [0, attempts]"
    return None


def _rate_problem(row: Mapping[str, Any]) -> str | None:
    rate = row.get("pass_rate")
    if isinstance(rate, bool) or not isinstance(rate, (int, float)):
        return "pass_rate must be a number"
    return None if rate == row["successes"] / row["attempts"] else "pass_rate != successes / attempts"


def problem_with(row: Mapping[str, Any]) -> str | None:
    """Why a ``generator=self`` row's difficulty provenance is unusable, or None."""

    if row.get("generator") != bv.GENERATOR_SELF:
        return None
    return _counts_problem(row) or _rate_problem(row)


def check_row(row: Mapping[str, Any]) -> None:
    """Refuse a ``generator=self`` row without sound ``attempts``/``successes``/``pass_rate``."""

    problem = problem_with(row)
    cv.refuse_when(
        problem is not None, bv.REFUSE_ROW_PROVENANCE, f"{row.get('proposal_id')}: {problem}",
    )


bind_import_twin(__name__)
