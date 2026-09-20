#!/usr/bin/env python3
"""Cost meters for ``snn-energy-routing-preferences``.

Split out of ``energy_preferences.py`` verbatim: the ``EnergyOracle`` boundary
and the three meters that implement it — ``ProcessResourceMeter``,
``RaplEnergyMeter``, ``RecordedEnergyMeter`` — plus ``select_meter`` and the
``meters`` report. Every name here is re-exported from ``energy_preferences``
so existing call sites resolve unchanged.
"""

from __future__ import annotations

import json
import platform
import re
import statistics
import sys
import time
from dataclasses import dataclass
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
else:
    from energy_contract import FAMILY



RAPL_ROOT = Path("/sys/class/powercap")


# --------------------------------------------------------------------------
# Meters
# --------------------------------------------------------------------------


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


class RaplEnergyMeter(EnergyOracle):
    """Reads Intel RAPL powercap counters around an executed workload.

    Produces genuine joules. Unavailable whenever the ``energy_uj`` files are
    not readable by the current user, which is the common non-root case.
    """

    name = "intel_rapl_powercap"
    version = "1.0.0"
    cost_quantity = "energy_j"
    measures_energy = True
    implementation = "pipelines/energy_preferences.py:RaplEnergyMeter"

    # A root RAPL zone: `intel-rapl:0`, never a subzone like `intel-rapl:0:0`.
    _ROOT_ZONE_RE = re.compile(r"^intel-rapl:\d+$")

    def __init__(self, root: Path | None = None) -> None:
        self.root = Path(root) if root is not None else RAPL_ROOT

    @staticmethod
    def _zone_label(domain: Path) -> str:
        try:
            return (domain / "name").read_text(encoding="utf-8").strip()
        except OSError:
            return ""

    def _domains(self) -> list[Path]:
        """The non-overlapping RAPL zones whose counters may be summed.

        ``/sys/class/powercap`` lists every zone flat: ``intel-rapl:0`` (the
        package) sits beside its own subzones ``intel-rapl:0:0`` (core) and
        ``intel-rapl:0:1`` (uncore), and a parent's counter already includes
        its children. Summing everything double-counts whichever components a
        workload exercises, and workloads with different component mixes can
        then receive a different preference ordering — so only root zones are
        read. ``psys``, when it appears beside package zones, is itself a
        superset of them and is dropped for the same reason; when it is the
        only root zone, it is the measurement.
        """

        roots = self._root_zones()
        psys = [domain for domain in roots if self._zone_label(domain) == "psys"]
        if psys and len(psys) < len(roots):
            roots = [domain for domain in roots if self._zone_label(domain) != "psys"]
        return roots

    def _root_zones(self) -> list[Path]:
        if not self.root.is_dir():
            return []
        return sorted(
            child
            for child in self.root.iterdir()
            if self._ROOT_ZONE_RE.match(child.name)
            and (child / "energy_uj").exists()
        )

    def available(self) -> tuple[bool, str]:
        domains = self._domains()
        if not domains:
            return False, f"no intel-rapl domains under {self.root}"
        for domain in domains:
            try:
                (domain / "energy_uj").read_text()
            except OSError as exc:
                return False, f"{domain / 'energy_uj'} not readable: {exc.strerror}"
        return True, f"{len(domains)} readable rapl domain(s)"

    def _read_uj(self) -> dict[str, int]:
        return {
            domain.name: int((domain / "energy_uj").read_text().strip())
            for domain in self._domains()
        }

    def _range_uj(self) -> dict[str, int]:
        ranges: dict[str, int] = {}
        for domain in self._domains():
            path = domain / "max_energy_range_uj"
            try:
                ranges[domain.name] = int(path.read_text().strip())
            except OSError:
                continue
        return ranges

    def _unwrapped_delta(
        self, name: str, start: int, end: int, ranges: dict[str, int]
    ) -> int:
        delta = end - start
        if delta < 0:
            # The counter wrapped. Unwrapping needs the domain's range; if
            # that is missing or unreadable, clamping to zero would report
            # a real workload as free and could reverse the preference. An
            # unmeasurable interval is unmeasured, not zero.
            wrap_range = ranges.get(name, 0)
            if wrap_range <= 0:
                raise oc.OracleUnavailable(
                    self.name,
                    f"{name} energy_uj wrapped and max_energy_range_uj is "
                    "missing or unreadable, so the interval cannot be measured",
                )
            delta += wrap_range
            if delta < 0:
                raise oc.OracleUnavailable(
                    self.name,
                    f"{name} energy_uj is still negative after unwrapping "
                    f"by {wrap_range}",
                )
        return delta

    def measure(
        self, workload: Callable[[], Any], *, repeats: int, warmup: int
    ) -> MeterReading:
        if repeats < 1:
            raise oc.ContractError("repeats must be >= 1")
        ok, detail = self.available()
        if not ok:
            raise oc.OracleUnavailable(self.name, detail)
        for _ in range(max(0, warmup)):
            workload()
        ranges = self._range_uj()
        # One counter sample per executed repeat, never one around the whole
        # batch: a long batch (the CLI allows up to 1000 repeats) can wrap a
        # domain counter more than once, and unwrapping can only ever add a
        # single range — endpoint sampling would silently report energy
        # modulo the counter range, and an even number of wraps would add
        # nothing at all. Per-repeat intervals observe every wrap the meter
        # can observe; a single workload execution outrunning the entire
        # counter range is outside what endpoint arithmetic can ever
        # disambiguate and outside this meter's measurable domain.
        total_uj = 0
        before = self._read_uj()
        wall_start = time.perf_counter_ns()
        for _ in range(repeats):
            workload()
            after = self._read_uj()
            if set(after) != set(before):
                # A vanished domain used to read as a zero delta and
                # silently underreport the interval; an appeared one would
                # be silently dropped. Either way the interval cannot be
                # attributed to a stable meter.
                raise oc.OracleUnavailable(
                    self.name,
                    "the RAPL domain set changed mid-measurement "
                    f"({sorted(before)} -> {sorted(after)})",
                )
            total_uj += sum(
                self._unwrapped_delta(name, start, after[name], ranges)
                for name, start in before.items()
            )
            before = after
        wall_s = (time.perf_counter_ns() - wall_start) / 1e9
        joules = total_uj / 1e6 / repeats
        return MeterReading(
            meter=self.name,
            cost_quantity=self.cost_quantity,
            cost_value=joules,
            extra=(
                oc.new_measurement("wall_time_s", wall_s / repeats, self.name),
                oc.new_measurement("repeats", repeats, self.name),
            ),
            detail={"domains": sorted(before), "aggregation": "mean_over_repeats"},
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
        return cls(json.loads(Path(path).read_text(encoding="utf-8")))

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
