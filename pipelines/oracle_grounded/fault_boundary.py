#!/usr/bin/env python3
"""The oracle boundary of the fault-recovery family (F1): the interface every
engine implements and the frozen verdict it returns. Kept apart from the
simulator so it can subclass the boundary and ``fault_oracle`` can default to
it without an import cycle."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from . import distill_vocabulary as vocab
from . import fault_vocabulary as fv
from .import_twins import bind_import_twin


@dataclass(frozen=True)
class FaultResult:
    """One executed disturbance: the outcome plus the state it was read from.

    Both latencies are relative to the disturbance onset, so identical faults
    at different onsets carry identical labels; ``detection_latency_ms`` is
    ``None`` only for a ``continue`` outcome.
    """

    outcome: str
    reason_codes: tuple[str, ...]
    detection_latency_ms: float | None
    recovery_latency_ms: float
    worst_healthy_channels: int
    dropped_events: int
    corrupt_events: int
    total_events: int
    peak_temperature_c: float
    max_staleness_ms: float
    max_jitter_ms: float
    saturated_ticks: int
    integrity_violation: bool
    result_delay_ms: float
    trace: tuple[dict[str, Any], ...] = field(default=())

    @property
    def realised_corrupt_ratio(self) -> float:
        """The corrupted share the tick grid actually applied (0.0 for no events)."""
        if self.total_events <= 0:
            return 0.0
        return self.corrupt_events / self.total_events

    @property
    def residual_error(self) -> float:
        """Corrupt plus dropped events over the total (0.0 for no events)."""
        if self.total_events <= 0:
            return 0.0
        return (self.corrupt_events + self.dropped_events) / self.total_events

    @property
    def ticks(self) -> int:
        return len(self.trace)


class FaultOracle:
    """Boundary a fault-recovery oracle must implement.

    The meters name the instruments behind the readings ``fault_oracle``
    derives; they default to unset so a hardware replay cannot inherit the
    simulator's provenance (``fault_oracle`` refuses undeclared meters).
    """

    name = "abstract"
    version = "0"
    oracle_type = fv.ORACLE_TYPE
    authority = vocab.AUTHORITY_AUTHORITATIVE
    implementation = fv.BOUNDARY_IMPLEMENTATION
    meter_clock: str | None = None
    meter_state: str | None = None
    meter_thermal: str | None = None

    def run(self, scenario: dict[str, Any], disturbance: dict[str, Any]) -> FaultResult:
        raise NotImplementedError

    def oracle_block(self, scenario: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError


bind_import_twin(__name__)
