#!/usr/bin/env python3
"""Meter contract types for ``snn-energy-routing-preferences``.

Split out of ``energy_meters.py`` verbatim: :class:`MeterReading`, the shape
every cost reading takes, and :class:`EnergyOracle`, the boundary every cost
meter implements. Re-exported through ``energy_meters`` so call sites resolve
unchanged.
"""

from __future__ import annotations

import platform
from dataclasses import dataclass
from typing import Any, Callable

@dataclass(frozen=True)
class MeterReading:
    """One meter's view of one executed workload."""

    meter: str
    cost_quantity: str
    cost_value: float
    extra: tuple[dict[str, Any], ...] = ()
    detail: dict[str, Any] | None = None


class EnergyOracle:
    """Boundary every cost meter implements.

    ``measure`` must actually execute ``workload`` ``repeats`` times and read a
    counter. Returning a modelled number from this method is a contract
    violation, not an implementation shortcut.
    """

    name = "abstract"
    version = "0"
    cost_quantity = "cpu_time_s"
    measures_energy = False
    # The code path the record claims produced it. An injected meter must
    # declare its own implementation: stamping this module's path on a class
    # defined elsewhere would be false provenance the family validator
    # trusts because it honours that prefix (and cannot replay a foreign
    # oracle's policies anyway).
    implementation = "pipelines/energy_preferences.py:EnergyOracle"

    def available(self) -> tuple[bool, str]:
        raise NotImplementedError

    def measure(
        self, workload: Callable[[], Any], *, repeats: int, warmup: int
    ) -> MeterReading:
        raise NotImplementedError

    def fingerprint(self) -> dict[str, Any]:
        return {
            "meter": self.name,
            "version": self.version,
            "platform": platform.platform(),
            "machine": platform.machine(),
            "python": platform.python_version(),
        }

