#!/usr/bin/env python3
"""Assembled 88-plant catalog for the db mill (r845-r888, 44 pairs)."""

from __future__ import annotations

from .import_twins import bind_import_twin
from .plant import Plant
from .plants_01 import PLANTS_01
from .plants_02 import PLANTS_02
from .plants_03 import PLANTS_03

__all__ = ["N_PAIRS", "PLANTS"]

PLANTS: list[Plant] = [*PLANTS_01, *PLANTS_02, *PLANTS_03]
N_PAIRS = len(PLANTS) // 2

bind_import_twin(__name__)
