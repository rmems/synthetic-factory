#!/usr/bin/env python3
"""Registry of slice-A burst mills (plants modules extracted from legacy-mill-lane)."""

from __future__ import annotations

from types import ModuleType

from . import (
    plants_r701,
    plants_r731,
    plants_r751,
    plants_r787,
    plants_r803,
    plants_r966,
    plants_r988,
    plants_r2535,
)

BURST_MILLS: dict[str, ModuleType] = {
    plants_r701.MILL_ID: plants_r701,
    plants_r731.MILL_ID: plants_r731,
    plants_r751.MILL_ID: plants_r751,
    plants_r787.MILL_ID: plants_r787,
    plants_r803.MILL_ID: plants_r803,
    plants_r966.MILL_ID: plants_r966,
    plants_r988.MILL_ID: plants_r988,
    plants_r2535.MILL_ID: plants_r2535,
}


def plants_module(mill_id: str) -> ModuleType:
    try:
        return BURST_MILLS[mill_id]
    except KeyError as exc:
        raise KeyError(f"unknown pbc burst mill {mill_id!r}") from exc
