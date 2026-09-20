#!/usr/bin/env python3
"""Shared check context for ``snn-energy-routing-preferences``.

Split out of ``energy_check.py`` verbatim: the small data carriers the
candidate checks pass between each other — a single usable meter reading
and the per-scenario context of weights, caps, and measurement index.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

_PIPELINES = Path(__file__).resolve().parent
if str(_PIPELINES) not in sys.path:
    sys.path.insert(0, str(_PIPELINES))



@dataclass(frozen=True)
class _Reading:
    """One usable oracle reading: value, instrument, and whether it measured."""

    value: float
    meter: str
    measured: Any


@dataclass(frozen=True)
class _CandidateContext:
    """Record-level facts every candidate is checked against."""

    measured_costs: dict[tuple[str, str], _Reading]
    corpus_quantity: Any
    can_derive_safety: bool
    caps: Any
    demand: Any
    weights: list[float] | None
    optimum: float | None
    solver: tuple[int, int] | None = None
