#!/usr/bin/env python3
"""Cost meters for ``snn-energy-routing-preferences``.

Split out of ``energy_preferences.py`` verbatim: the meters
``ProcessResourceMeter`` and ``RecordedEnergyMeter`` (the contract types and
the RAPL meter live in ``energy_meter_types`` / ``energy_meter_rapl``) plus
``select_meter`` and the ``meters`` report. Every name here is re-exported
from ``energy_preferences`` so existing call sites resolve unchanged.
"""

from __future__ import annotations

import json
import statistics
import sys
import time
from pathlib import Path
from typing import Any, Callable

try:  # pragma: no cover - Windows has no resource module
    import resource
except ImportError:  # pragma: no cover
    resource = None  # type: ignore[assignment]

_PIPELINES = Path(__file__).resolve().parent
if str(_PIPELINES) not in sys.path:
    sys.path.insert(0, str(_PIPELINES))

from oracle_grounded import distill_contract as oc  # noqa: E402

if __package__:
    from .energy_contract import FAMILY
    from .energy_meter_rapl import RaplEnergyMeter
    from .energy_meter_types import EnergyOracle, MeterReading
else:
    from energy_contract import FAMILY
    from energy_meter_rapl import RaplEnergyMeter
    from energy_meter_types import EnergyOracle, MeterReading


# --------------------------------------------------------------------------
# Meters
# --------------------------------------------------------------------------



class ProcessResourceMeter(EnergyOracle):
    """Measures CPU time, wall time and RSS of an actually executed workload.

    Real measurements of a real execution — but of *time*, not energy. Records
    metered this way are denominated in ``cpu_time_s``.
    """

    name = "process_resource_meter"
    version = "1.0.0"
    cost_quantity = "cpu_time_s"
    measures_energy = False
    implementation = "pipelines/energy_preferences.py:ProcessResourceMeter"

    def available(self) -> tuple[bool, str]:
        return True, "process clocks are always readable"

    def _delta_extras(
        self,
        peak_rss_kb: float | None,
        switches: tuple[int | None, int | None],
    ) -> list[dict[str, Any]]:
        extra: list[dict[str, Any]] = []
        if peak_rss_kb is not None:
            extra.append(
                oc.new_measurement(
                    "max_rss_kb",
                    peak_rss_kb,
                    self.name,
                    detail={"scope": "process_peak_during_workload"},
                )
            )
        switches_before, switches_after = switches
        if switches_after is not None and switches_before is not None:
            extra.append(
                oc.new_measurement(
                    "context_switches",
                    switches_after - switches_before,
                    self.name,
                )
            )
        return extra

    def measure(
        self, workload: Callable[[], Any], *, repeats: int, warmup: int
    ) -> MeterReading:
        if repeats < 1:
            raise oc.ContractError("repeats must be >= 1")
        for _ in range(max(0, warmup)):
            workload()
        cpu_samples: list[float] = []
        wall_samples: list[float] = []
        # `ru_maxrss` is the process-lifetime high-water mark; subtracting two
        # snapshots of it does not measure this workload — warmup runs before
        # the first snapshot and candidates share one process, so an equal or
        # smaller footprint read as a false `max_rss_kb: 0`. The kernel's peak
        # counter is reset instead, so the post-run high-water mark is this
        # workload's own peak residency; where no resettable counter exists
        # the quantity is unmeasured, not zero.
        rss_tracked = _facade_seam("_reset_peak_rss")()
        switches_before = _facade_seam("_context_switches")()
        for _ in range(repeats):
            cpu_start = time.process_time_ns()
            wall_start = time.perf_counter_ns()
            workload()
            wall_samples.append((time.perf_counter_ns() - wall_start) / 1e9)
            cpu_samples.append((time.process_time_ns() - cpu_start) / 1e9)
        peak_rss_kb = _peak_rss_kb() if rss_tracked else None
        switches_after = _facade_seam("_context_switches")()

        cpu_median = statistics.median(cpu_samples)
        wall_median = statistics.median(wall_samples)
        extra = [
            oc.new_measurement("wall_time_s", wall_median, self.name),
            oc.new_measurement("latency_ms", wall_median * 1000.0, self.name),
            oc.new_measurement("repeats", repeats, self.name),
        ] + self._delta_extras(peak_rss_kb, (switches_before, switches_after))
        return MeterReading(
            meter=self.name,
            cost_quantity=self.cost_quantity,
            cost_value=cpu_median,
            extra=tuple(extra),
            detail={
                "cpu_samples_s": [round(value, 9) for value in cpu_samples],
                "aggregation": "median",
            },
        )





class RecordedEnergyMeter(EnergyOracle):
    """Replays a measurement taken by a real metered run recorded elsewhere.

    The recording carries the meter that produced it. ``lookup`` takes the
    caller's key — a candidate id, or a candidate id joined to a workload
    fingerprint — and fails closed: an unknown key raises
    :class:`oracle_grounded.envelope.OracleUnavailable` rather than guessing or
    interpolating.
    """

    name = "recorded_power_run"
    version = "1.0.0"
    cost_quantity = "energy_j"
    measures_energy = True
    implementation = "pipelines/energy_preferences.py:RecordedEnergyMeter"

    def __init__(self, recording: dict[str, Any]) -> None:
        self.recording = recording
        # No default. `recorded_power_run` is this replay wrapper, not an
        # instrument; defaulting to it would let a file of bare observations
        # emit `energy_j` records that never name the meter that took the
        # readings. The wrapper is the oracle; the meter is whatever was
        # physically attached, and the recording has to say which.
        source_meter = recording.get("meter")
        self.source_meter = source_meter if isinstance(source_meter, str) else ""
        self.cost_quantity = recording.get("cost_quantity", self.cost_quantity)
        self.measures_energy = oc.is_enum_value(self.cost_quantity, oc.ENERGY_QUANTITIES)
        observations = recording.get("observations")
        self.observations = observations if isinstance(observations, dict) else {}

    @classmethod
    def from_path(cls, path) -> "RecordedEnergyMeter":
        return cls(json.loads(Path(path).read_text(encoding="utf-8")))  # NOSONAR

    def available(self) -> tuple[bool, str]:
        if not self.source_meter.strip():
            return False, (
                "recording does not name the physical meter that produced it; "
                "set 'meter' to the instrument, not to the replay wrapper"
            )
        if not self.observations:
            return False, "recording contains no observations"
        return True, f"{len(self.observations)} recorded observation(s)"

    def lookup(self, key: str) -> MeterReading:
        entry = self.observations.get(key)
        if not isinstance(entry, dict) or not oc.is_number(entry.get("cost_value")):
            raise oc.OracleUnavailable(
                self.name, f"no recorded measurement for key {key!r}"
            )
        if float(entry["cost_value"]) < 0.0:
            # Neither joules nor seconds can be negative, and the cheapest
            # candidate wins: a negative replayed cost would take the
            # preference every time.
            raise oc.OracleUnavailable(
                self.name,
                f"recorded cost for key {key!r} is negative "
                f"({entry['cost_value']}); a measured cost cannot be below zero",
            )
        if not self.source_meter.strip():
            raise oc.OracleUnavailable(
                self.name, "recording does not name the physical meter"
            )
        return MeterReading(
            meter=self.source_meter,
            cost_quantity=self.cost_quantity,
            cost_value=float(entry["cost_value"]),
            detail={"recorded_key": key, "recorded_run": self.recording.get("run_id")},
        )

    def measure(
        self, workload: Callable[[], Any], *, repeats: int, warmup: int
    ) -> MeterReading:
        raise oc.OracleUnavailable(
            self.name,
            "a recorded meter replays measurements; call lookup(key) instead",
        )

    def fingerprint(self) -> dict[str, Any]:
        return {
            "meter": self.source_meter,
            "version": self.version,
            "run_id": self.recording.get("run_id"),
            "recorded_at": self.recording.get("recorded_at"),
            "host": self.recording.get("host"),
        }


_CLEAR_REFS = Path("/proc/self/clear_refs")
_PROC_STATUS = Path("/proc/self/status")


def _facade_seam(name: str) -> Callable[..., Any]:
    """Resolve ``name`` through the ``energy_preferences`` facade namespace.

    Tests patch these counters on the facade (``ep._context_switches``), and
    the repo convention for compat facades is that seams read the live module
    namespace rather than the sibling's private copy.
    """

    module = sys.modules.get(
        f"{__package__}.energy_preferences" if __package__ else "energy_preferences"
    )
    fallback = globals()[name]
    if module is None or module is sys.modules[__name__]:
        return fallback
    return getattr(module, name, fallback)


def _reset_peak_rss() -> bool:
    """Reset the kernel's peak-RSS high-water mark for this process.

    Writing ``5`` to ``/proc/self/clear_refs`` resets ``VmHWM``, so the next
    read reports the peak residency *since this call* — a per-workload peak
    rather than a process-lifetime one. False where the interface does not
    exist (non-Linux) or cannot be written.
    """

    try:
        _CLEAR_REFS.write_text("5", encoding="ascii")
    except OSError:
        return False
    return True


def _peak_rss_kb() -> float | None:
    """The peak resident set size since the last reset, in kilobytes."""

    try:
        status = _PROC_STATUS.read_text(encoding="ascii")
    except OSError:
        return None
    for line in status.splitlines():
        if line.startswith("VmHWM:"):
            fields = line.split()
            if len(fields) >= 2 and fields[1].isdigit():
                return float(fields[1])
    return None


def _context_switches() -> int | None:
    if resource is None:
        return None
    usage = resource.getrusage(resource.RUSAGE_SELF)
    return usage.ru_nvcsw + usage.ru_nivcsw


def select_meter(prefer_energy: bool = True) -> tuple[EnergyOracle, dict[str, Any]]:
    """Pick the best available meter and report what was probed.

    Returns ``(meter, probe)`` where ``probe`` records every meter that was
    tried and why it was or was not used. The probe goes into the record so a
    reader can tell a cpu-time-denominated corpus from a joule-denominated one
    without guessing.
    """

    probe: dict[str, Any] = {"probed": [], "selected": None}
    candidates: list[EnergyOracle] = []
    if prefer_energy:
        candidates.append(RaplEnergyMeter())
    candidates.append(ProcessResourceMeter())
    chosen: EnergyOracle | None = None
    for meter in candidates:
        ok, detail = meter.available()
        probe["probed"].append(
            {
                "meter": meter.name,
                "measures_energy": meter.measures_energy,
                "available": ok,
                "detail": detail,
            }
        )
        if ok and chosen is None:
            chosen = meter
    if chosen is None:  # pragma: no cover - ProcessResourceMeter is always available
        raise oc.OracleUnavailable("energy_meter", "no meter is available")
    probe["selected"] = chosen.name
    probe["cost_quantity"] = chosen.cost_quantity
    probe["cost_is_energy"] = chosen.measures_energy
    return chosen, probe


def meters_report() -> dict[str, Any]:
    """Probe every meter and report availability without measuring anything."""

    report: dict[str, Any] = {"family": FAMILY, "meters": []}
    for meter in (RaplEnergyMeter(), ProcessResourceMeter()):
        ok, detail = meter.available()
        report["meters"].append(
            {
                "meter": meter.name,
                "cost_quantity": meter.cost_quantity,
                "measures_energy": meter.measures_energy,
                "available": ok,
                "detail": detail,
            }
        )
    report["note"] = (
        "There is no path from a measured second to a joule in this pipeline. "
        "When no energy meter is available the corpus is denominated in "
        "cpu_time_s and result.cost_is_energy is false."
    )
    return report
