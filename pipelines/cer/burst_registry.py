#!/usr/bin/env python3
"""Registry of slice-A burst mills (plants modules extracted from legacy-mill-lane)."""

from __future__ import annotations

from types import ModuleType

from . import plants_r1901, plants_r1958

BURST_MILLS: dict[str, ModuleType] = {
    plants_r1901.MILL_ID: plants_r1901,
    plants_r1958.MILL_ID: plants_r1958,
}


def plants_module(mill_id: str) -> ModuleType:
    try:
        return BURST_MILLS[mill_id]
    except KeyError as exc:
        raise KeyError(f"unknown cer burst mill {mill_id!r}") from exc
