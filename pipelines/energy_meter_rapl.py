#!/usr/bin/env python3
"""Linux RAPL powercap meter for ``snn-energy-routing-preferences``.

Split out of ``energy_meters.py`` verbatim: :class:`RaplEnergyMeter`, the
meter that reads ``/sys/class/powercap`` domains, skips subzones already
counted by their package parent, and unwraps the 32-bit counter per repeat.
Re-exported through ``energy_meters`` so call sites resolve unchanged.
"""

from __future__ import annotations

import re
import sys
import time
from pathlib import Path
from typing import Any, Callable, NamedTuple

_PIPELINES = Path(__file__).resolve().parent
if str(_PIPELINES) not in sys.path:
    sys.path.insert(0, str(_PIPELINES))

from oracle_grounded import distill_contract as oc  # noqa: E402

if __package__:
    from .energy_meter_types import EnergyOracle, MeterReading
else:
    from energy_meter_types import EnergyOracle, MeterReading


RAPL_ROOT = Path("/sys/class/powercap")

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
        self, sample: _DomainSample, ranges: dict[str, int]
    ) -> int:
        delta = sample.end - sample.start
        if delta < 0:
            # The counter wrapped. Unwrapping needs the domain's range; if
            # that is missing or unreadable, clamping to zero would report
            # a real workload as free and could reverse the preference. An
            # unmeasurable interval is unmeasured, not zero.
            wrap_range = ranges.get(sample.name, 0)
            if wrap_range <= 0:
                raise oc.OracleUnavailable(
                    self.name,
                    f"{sample.name} energy_uj wrapped and max_energy_range_uj is "
                    "missing or unreadable, so the interval cannot be measured",
                )
            delta += wrap_range
            if delta < 0:
                raise oc.OracleUnavailable(
                    self.name,
                    f"{sample.name} energy_uj is still negative after unwrapping "
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
            self._check_stable_domains(before, after)
            total_uj += sum(
                self._unwrapped_delta(
                    _DomainSample(name, start, after[name]), ranges
                )
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

    def _check_stable_domains(
        self, before: dict[str, int], after: dict[str, int]
    ) -> None:
        if set(after) == set(before):
            return
        # A vanished domain used to read as a zero delta and silently
        # underreport the interval; an appeared one would be silently
        # dropped. Either way the interval cannot be attributed to a
        # stable meter.
        raise oc.OracleUnavailable(
            self.name,
            "the RAPL domain set changed mid-measurement "
            f"({sorted(before)} -> {sorted(after)})",
        )


class _DomainSample(NamedTuple):
    """One counter domain's readings bracketing a single workload run."""

    name: str
    start: int
    end: int

