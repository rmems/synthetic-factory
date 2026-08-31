#!/usr/bin/env python3
"""``snn-energy-routing-preferences`` generator + measured-execution oracle.

Issue #78. A generator may propose *equivalent* control policies; it may not
invent their cost. Every cost in a record here comes from actually executing
the candidate policy and reading a meter.

The preference is **not** "cheapest wins". It is::

    minimise measured cost subject to task-quality and safety constraints

so a wrong-but-cheap policy and a fast-but-unsafe policy are both rejected
even when they are the cheapest thing measured.

Meters:

``RaplEnergyMeter``
    Reads ``/sys/class/powercap/intel-rapl:*/energy_uj`` around the executed
    workload and reports real joules. Requires read access to the powercap
    counters (root on most distributions).
``ProcessResourceMeter``
    Always available. Measures CPU time, wall time and RSS of the executed
    workload. These are real measurements, but they are **not** energy: a
    record metered this way is denominated in ``cpu_time_s`` and says so.
``RecordedEnergyMeter``
    Replays a measurement recorded by a real metered run elsewhere. Fails
    closed on an unknown key; it never interpolates or synthesises. API-only;
    excluded from automatic selection by ``select_meter``.

There is deliberately no "estimate joules from CPU seconds" path. Turning a
measured second into a joule requires a power model, and a modelled joule is
exactly what issue #78 forbids.

CLI::

    python3 pipelines/energy_preferences.py measure --count 4 --seed 20260823 \
        --output <new.jsonl>
    python3 pipelines/energy_preferences.py meters --json
"""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import random
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

import oracle_contract as oc  # noqa: E402

FAMILY = "snn-energy-routing-preferences"
GENERATOR_NAME = "equivalent-policy-generator"
GENERATOR_VERSION = "1.0.0"

RAPL_ROOT = Path("/sys/class/powercap")

DECISION_RULE = "min_measured_cost_subject_to_quality_and_safety"

# The policy implementations a workload key names. Bump this whenever a
# policy's algorithm changes: a recorded cost is only valid for the workload
# it was taken over, and a silently different implementation under the same
# key would attach an old reading to a new workload.
POLICY_SUITE_VERSION = "1.0.0"

DEFAULT_FINE_STEPS = 48
DEFAULT_COARSE_STEPS = 8

ABSTAIN_NO_FEASIBLE = "NO_CANDIDATE_SATISFIES_QUALITY_AND_SAFETY_CONSTRAINTS"
ABSTAIN_NO_MEASUREMENT = "NO_MEASURED_COST_AVAILABLE"

# The one safety envelope this family's oracle enforces. Validated verbatim:
# a scenario describing a different rule to the student than the one the
# labels were derived under would pair one decision rule's description with
# another's outcomes.
SAFETY_ENVELOPE = "0 <= x_i <= cap_i and sum(x_i) == demand"

# The costs this family's decision rule may minimise: measured joules, or the
# documented CPU-time fallback. Any other registered quantity (a latency, a
# temperature) is a different optimisation wearing this family's name.
SUPPORTED_COST_QUANTITIES = frozenset({"energy_j", "cpu_time_s"})


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

    def available(self) -> tuple[bool, str]:
        return True, "process clocks are always readable"

    def _delta_extras(
        self,
        rss: tuple[float | None, float | None],
        switches: tuple[float | None, float | None],
    ) -> list[dict[str, Any]]:
        extra: list[dict[str, Any]] = []
        rss_before, rss_after = rss
        if rss_after is not None and rss_before is not None:
            extra.append(
                oc.new_measurement("max_rss_kb", float(rss_after - rss_before), self.name)
            )
        switches_before, switches_after = switches
        if switches_after is not None and switches_before is not None:
            extra.append(
                oc.new_measurement(
                    "context_switches",
                    float(switches_after - switches_before),
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
        rss_before = _max_rss_kb()
        switches_before = _context_switches()
        for _ in range(repeats):
            cpu_start = time.process_time_ns()
            wall_start = time.perf_counter_ns()
            workload()
            wall_samples.append((time.perf_counter_ns() - wall_start) / 1e9)
            cpu_samples.append((time.process_time_ns() - cpu_start) / 1e9)
        rss_after = _max_rss_kb()
        switches_after = _context_switches()

        cpu_median = statistics.median(cpu_samples)
        wall_median = statistics.median(wall_samples)
        extra = [
            oc.new_measurement("wall_time_s", wall_median, self.name),
            oc.new_measurement("latency_ms", wall_median * 1000.0, self.name),
            oc.new_measurement("repeats", float(repeats), self.name),
        ] + self._delta_extras(
            (rss_before, rss_after), (switches_before, switches_after)
        )
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
            total_uj += sum(
                self._unwrapped_delta(name, start, after.get(name, start), ranges)
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
                oc.new_measurement("repeats", float(repeats), self.name),
            ),
            detail={"domains": sorted(before), "aggregation": "mean_over_repeats"},
        )


class RecordedEnergyMeter(EnergyOracle):
    """Replays a measurement taken by a real metered run recorded elsewhere.

    The recording carries the meter that produced it. ``lookup`` takes the
    caller's key — a candidate id, or a candidate id joined to a workload
    fingerprint — and fails closed: an unknown key raises
    :class:`oracle_contract.OracleUnavailable` rather than guessing or
    interpolating.
    """

    name = "recorded_power_run"
    version = "1.0.0"
    cost_quantity = "energy_j"
    measures_energy = True

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


def _max_rss_kb() -> float | None:
    if resource is None:
        return None
    usage = resource.getrusage(resource.RUSAGE_SELF)
    # Linux reports kilobytes; macOS reports bytes.
    if sys.platform == "darwin":
        return usage.ru_maxrss / 1024.0
    return float(usage.ru_maxrss)


def _context_switches() -> float | None:
    if resource is None:
        return None
    usage = resource.getrusage(resource.RUSAGE_SELF)
    return float(usage.ru_nvcsw + usage.ru_nivcsw)


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


# --------------------------------------------------------------------------
# Task: constrained actuator allocation
# --------------------------------------------------------------------------


def objective(weights: list[float], allocation: list[float]) -> float:
    """Quadratic effort of an allocation. Lower is better."""

    return sum(w * x * x for w, x in zip(weights, allocation))


def analytic_allocation(
    demand: float, weights: list[float], caps: list[float]
) -> list[float]:
    """Exact KKT solution of the capped quadratic allocation problem.

    Each round spreads the remaining demand proportionally to ``1/w``, pins any
    actuator that would exceed its cap, and repeats. Every pinned actuator was
    over its trial share, and the trial shares sum to the remaining demand, so
    the remainder stays strictly positive until the loop settles — the free set
    empties only when the caps cannot meet the demand at all.
    """

    n = len(weights)
    fixed: dict[int, float] = {}
    free = set(range(n))
    remaining = demand
    while free:
        inverse_sum = sum(1.0 / weights[i] for i in free)
        trial = {i: remaining / (weights[i] * inverse_sum) for i in free}
        violating = [i for i in free if trial[i] > caps[i] + 1e-12]
        if not violating:
            fixed.update(trial)
            break
        for index in violating:
            fixed[index] = caps[index]
            remaining -= caps[index]
            free.discard(index)
    return [fixed.get(i, 0.0) for i in range(n)]


def unclipped_allocation(demand: float, weights: list[float]) -> list[float]:
    """Proportional-to-1/w allocation that ignores the actuator caps.

    Achieves the lowest possible objective precisely because it is allowed to
    break the caps. Fast, high quality, and unsafe.
    """

    inverse_sum = sum(1.0 / w for w in weights)
    return [demand / (w * inverse_sum) for w in weights]


def _grid_allocations(demand: float, n: int, steps: int):
    """Yield every allocation of ``demand`` over ``n`` actuators on a grid."""

    step = demand / steps

    def walk(index: int, left: int, prefix: list[float]):
        if index == n - 1:
            yield prefix + [left * step]
            return
        for take in range(left + 1):
            yield from walk(index + 1, left - take, prefix + [take * step])

    yield from walk(0, steps, [])


def grid_allocation(
    demand: float, weights: list[float], caps: list[float], steps: int
) -> list[float] | None:
    """Exhaustive grid search. Correct up to grid resolution, and slow.

    Returns ``None`` when no point on the grid satisfies the caps. It must not
    return an all-zero allocation in that case: zeros have an objective of
    ``0.0``, *lower* than the true optimum, so any caller comparing objectives
    would rank a policy that solved nothing above one that solved the problem.
    ``None`` says "this policy found nothing", which is the actual outcome.
    """

    best: list[float] | None = None
    best_cost = float("inf")
    for candidate in _grid_allocations(demand, len(weights), steps):
        if any(x > cap + 1e-12 for x, cap in zip(candidate, caps)):
            continue
        cost = objective(weights, candidate)
        if cost < best_cost:
            best_cost = cost
            best = candidate
    return best


@dataclass(frozen=True)
class PolicyEvaluation:
    """Quality and safety of one policy's allocation, both measured."""

    allocation: tuple[float, ...]
    task_quality: float
    safety_ok: bool
    violations: tuple[str, ...]
    success: bool


def evaluate_allocation(
    allocation: list[float] | None,
    *,
    demand: float,
    weights: list[float],
    caps: list[float],
    optimum: float,
    quality_floor: float,
) -> PolicyEvaluation:
    """Score an allocation against the task objective and safety envelope.

    ``allocation is None`` means the policy produced no answer at all, which is
    reported as its own failure rather than folded into a safety violation.
    """

    if allocation is None:
        return PolicyEvaluation(
            allocation=(),
            task_quality=0.0,
            safety_ok=False,
            violations=("NO_FEASIBLE_ALLOCATION_FOUND",),
            success=False,
        )

    violations: list[str] = []
    for index, (value, cap) in enumerate(zip(allocation, caps)):
        if value > cap + 1e-9:
            violations.append(f"ACTUATOR_{index}_OVER_CAP")
        if value < -1e-9:
            violations.append(f"ACTUATOR_{index}_NEGATIVE")
    total = sum(allocation)
    if abs(total - demand) > 1e-6:
        violations.append("DEMAND_NOT_MET")
    achieved = objective(weights, allocation)
    quality = 0.0 if achieved <= 0 else min(1.0, optimum / achieved)
    safety_ok = not violations
    return PolicyEvaluation(
        allocation=tuple(round(value, 9) for value in allocation),
        task_quality=round(quality, 6),
        safety_ok=safety_ok,
        violations=tuple(violations),
        success=bool(safety_ok and quality >= quality_floor),
    )


# --------------------------------------------------------------------------
# Generator + measurement
# --------------------------------------------------------------------------

POLICY_DESCRIPTIONS = {
    "exhaustive_grid": "search every capped allocation on a fine grid",
    "analytic_kkt": "closed-form KKT solution with cap redistribution",
    "coarse_grid": "search a deliberately coarse grid",
    "unclipped_proportional": "ignore the actuator caps and split by 1/weight",
}


def _allocation_state(rng: random.Random) -> dict[str, Any]:
    """One randomly drawn capped-allocation problem."""

    n = 4
    weights = [round(rng.uniform(0.6, 2.4), 3) for _ in range(n)]
    demand = round(rng.uniform(0.8, 1.6), 3)
    headroom = rng.uniform(1.25, 1.8)
    caps = [round(demand / n * headroom, 3) for _ in range(n)]
    # Bind the cap of the cheapest actuator just under the share an
    # uncapped policy would give it, so the fast unclipped policy always
    # has a real safety violation to be rejected for.
    binding = min(range(n), key=lambda i: weights[i])
    caps[binding] = round(unclipped_allocation(demand, weights)[binding] * 0.9, 3)
    if sum(caps) <= demand:
        caps = [round(cap + demand / n, 3) for cap in caps]
    return {
        "demand": demand,
        "actuator_weights": weights,
        "actuator_caps": caps,
    }


def propose_scenarios(seed: int, count: int) -> list[dict[str, Any]]:
    """Generator side: equivalent policy alternatives, with no cost attached."""

    if count < 1:
        raise oc.ContractError("count must be >= 1")
    rng = random.Random(seed)
    proposals: list[dict[str, Any]] = []
    for index in range(count):
        proposals.append(
            {
                "index": index,
                "scenario": {
                    "task": "capped quadratic actuator allocation",
                    "state": _allocation_state(rng),
                    "constraints": {
                        "quality_floor": 0.98,
                        "safety_envelope": SAFETY_ENVELOPE,
                    },
                    "candidate_actions": [
                        {"id": policy, "description": description}
                        for policy, description in sorted(POLICY_DESCRIPTIONS.items())
                    ],
                    "objective": "minimise measured cost subject to quality and safety",
                },
            }
        )
    return proposals


def _policy_workloads(
    demand: float, weights: list[float], caps: list[float], *, fine_steps: int,
    coarse_steps: int,
) -> dict[str, Callable[[], list[float]]]:
    return {
        "exhaustive_grid": lambda: grid_allocation(demand, weights, caps, fine_steps),
        "analytic_kkt": lambda: analytic_allocation(demand, weights, caps),
        "coarse_grid": lambda: grid_allocation(demand, weights, caps, coarse_steps),
        "unclipped_proportional": lambda: unclipped_allocation(demand, weights),
    }


def choose_preference(
    candidates: list[dict[str, Any]], quality_floor: float
) -> tuple[dict[str, Any] | None, str | None]:
    """Minimise measured cost subject to quality and safety.

    Returns ``(preference, abstention_reason)``. Exactly one is ``None``.

    Fields of the returned preference:

    ``preferred``
        The cheapest measured candidate that is safe and clears the quality
        floor. Equal measured costs are broken by candidate id, so the label is
        a function of the measurements rather than of iteration order.
    ``over``
        Every other candidate in the record, preferred-over — not only the
        feasible ones and not only the cheaper ones.
    ``feasible``
        The subset that satisfied both constraints and so could have won.
    ``cheaper_but_constraint_violating``
        Candidates measured cheaper than the winner that the constraints ruled
        out. This is what makes the constraint visibly load-bearing.
    """

    feasible = _feasible_candidates(candidates, quality_floor)
    if not feasible:
        return None, ABSTAIN_NO_FEASIBLE
    preferred = min(feasible, key=lambda item: (item["cost_value"], item["id"]))
    cheaper_but_rejected = sorted(
        candidate["id"]
        for candidate in candidates
        if candidate["id"] != preferred["id"]
        and oc.is_number(candidate.get("cost_value"))
        and candidate["cost_value"] < preferred["cost_value"]
    )
    return (
        {
            "preferred": preferred["id"],
            "over": sorted(
                candidate["id"]
                for candidate in candidates
                if candidate["id"] != preferred["id"]
            ),
            "decision_rule": DECISION_RULE,
            "cost_quantity": preferred["cost_quantity"],
            "cost_value": preferred["cost_value"],
            "quality_floor": quality_floor,
            "feasible": sorted(candidate["id"] for candidate in feasible),
            "cheaper_but_constraint_violating": cheaper_but_rejected,
        },
        None,
    )


def _feasible_candidates(
    candidates: list[dict[str, Any]], quality_floor: float
) -> list[dict[str, Any]]:
    """The candidates that are safe, clear the floor, and carry a cost."""

    return [
        candidate
        for candidate in candidates
        if candidate.get("safety_ok") is True
        and oc.is_number(candidate.get("task_quality"))
        and candidate["task_quality"] >= quality_floor
        and oc.is_number(candidate.get("cost_value"))
    ]


def workload_key(
    policy_id: str,
    scenario: dict[str, Any],
    *,
    fine_steps: int = DEFAULT_FINE_STEPS,
    coarse_steps: int = DEFAULT_COARSE_STEPS,
) -> str:
    """Stable key identifying one policy running one workload configuration.

    A recorded measurement is only valid for the workload it was taken over,
    so the key binds the policy to the scenario state *and* to the solver
    parameters that shape the executed search. Without the solver binding, a
    recording taken at one grid resolution replays cleanly against another:
    the grid policy runs a different allocation search while the old energy
    reading is attached to it, which can silently change the preference.
    """

    state = scenario.get("state") if isinstance(scenario, dict) else None
    payload = {
        "state": state,
        "policy_suite": POLICY_SUITE_VERSION,
        "solver": {
            "fine_steps": int(fine_steps),
            "coarse_steps": int(coarse_steps),
        },
    }
    digest = hashlib.sha256(oc.canonical_json(payload).encode("utf-8")).hexdigest()
    return f"{policy_id}@{digest[:16]}"


def _read_cost(
    meter: EnergyOracle,
    workload: Callable[[], Any],
    *,
    policy_id: str,
    scenario: dict[str, Any],
    repeats: int,
    warmup: int,
    fine_steps: int,
    coarse_steps: int,
) -> MeterReading:
    """Take a live measurement, or replay one a real metered run recorded.

    A replay meter supplies the *cost* only. Task quality and safety are still
    evaluated by executing the policy here, which is sound because the task is
    deterministic: the same policy on the same state produces the same
    allocation on any host. Only the cost needs a meter that was actually
    attached to the hardware.
    """

    lookup = getattr(meter, "lookup", None)
    if callable(lookup):
        return lookup(
            workload_key(
                policy_id,
                scenario,
                fine_steps=fine_steps,
                coarse_steps=coarse_steps,
            )
        )
    return meter.measure(workload, repeats=repeats, warmup=warmup)


@dataclass(frozen=True)
class _MeterRun:
    """The meter and knobs one measured batch runs with."""

    meter: EnergyOracle
    probe: dict[str, Any]
    repeats: int
    warmup: int
    fine_steps: int
    coarse_steps: int


def _resolve_meter(
    meter: EnergyOracle | None, meter_probe: dict[str, Any] | None
) -> tuple[EnergyOracle, dict[str, Any]]:
    """The meter to measure with, and the probe documenting that choice."""

    if meter is None:
        return select_meter(prefer_energy=True)
    ok, detail = meter.available()
    probe = meter_probe
    if probe is None:
        probe = {
            "probed": [
                {
                    "meter": meter.name,
                    "measures_energy": meter.measures_energy,
                    "available": ok,
                    "detail": detail,
                }
            ],
            "selected": meter.name,
            "cost_quantity": meter.cost_quantity,
            "cost_is_energy": meter.measures_energy,
        }
    if not ok:
        raise oc.OracleUnavailable(meter.name, detail)
    return meter, probe


def _oracle_block(run: _MeterRun) -> dict[str, Any]:
    meter = run.meter
    # A replay meter (it exposes `lookup`, the same discriminator
    # `_measure_policy` routes on) hands back a cost recorded by a metered run
    # elsewhere; only task quality and safety were executed locally. Labelling
    # that `measured_execution` would claim the cost truth came from a live
    # metered execution on this run, so provenance consumers could not tell a
    # replayed corpus from one metered in place.
    replayed = callable(getattr(meter, "lookup", None))
    return oc.new_oracle(
        meter.name,
        oracle_type="recorded_measurement" if replayed else "measured_execution",
        implementation=f"pipelines/energy_preferences.py:{type(meter).__name__}",
        version=meter.version,
        authority=oc.AUTHORITY_AUTHORITATIVE,
        configuration={
            "repeats": run.repeats,
            "warmup": run.warmup,
            "fine_steps": run.fine_steps,
            "coarse_steps": run.coarse_steps,
            "meter_probe": run.probe,
        },
        seed=None,
        commit=None,
        fingerprint=meter.fingerprint(),
    )


def _reading_measurements(
    reading: MeterReading, policy_id: str, evaluation: PolicyEvaluation
) -> list[dict[str, Any]]:
    """The oracle measurements one policy's reading and evaluation yield."""

    measurements = [
        oc.new_measurement(
            reading.cost_quantity,
            reading.cost_value,
            reading.meter,
            detail={"candidate": policy_id, **(reading.detail or {})},
        )
    ]
    for extra in reading.extra:
        enriched = dict(extra)
        detail = dict(enriched.get("detail") or {})
        detail["candidate"] = policy_id
        enriched["detail"] = detail
        measurements.append(enriched)
    measurements.append(
        oc.new_measurement(
            "task_quality",
            evaluation.task_quality,
            "task_reference_solver",
            detail={"candidate": policy_id},
        )
    )
    return measurements


def _measure_candidate(
    run: _MeterRun,
    policy_id: str,
    workload: Callable[[], Any],
    scenario: dict[str, Any],
    evaluation: PolicyEvaluation,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """One executed policy's measurements and its candidate summary."""

    reading = _read_cost(
        run.meter,
        workload,
        policy_id=policy_id,
        scenario=scenario,
        repeats=run.repeats,
        warmup=run.warmup,
        fine_steps=run.fine_steps,
        coarse_steps=run.coarse_steps,
    )
    measurements = _reading_measurements(reading, policy_id, evaluation)
    candidate = {
        "id": policy_id,
        "description": POLICY_DESCRIPTIONS[policy_id],
        "allocation": list(evaluation.allocation),
        "task_quality": evaluation.task_quality,
        "safety_ok": evaluation.safety_ok,
        "safety_violations": list(evaluation.violations),
        "success": evaluation.success,
        "cost_quantity": reading.cost_quantity,
        "cost_value": reading.cost_value,
        "cost_meter": reading.meter,
    }
    return measurements, candidate


def _scenario_result(run: _MeterRun, scenario: dict[str, Any]) -> dict[str, Any]:
    """Execute and meter every candidate policy for one scenario."""

    state = scenario["state"]
    demand = float(state["demand"])
    weights = [float(value) for value in state["actuator_weights"]]
    caps = [float(value) for value in state["actuator_caps"]]
    quality_floor = float(scenario["constraints"]["quality_floor"])
    optimum = objective(weights, analytic_allocation(demand, weights, caps))

    workloads = _policy_workloads(
        demand,
        weights,
        caps,
        fine_steps=run.fine_steps,
        coarse_steps=run.coarse_steps,
    )
    measurements: list[dict[str, Any]] = []
    candidates: list[dict[str, Any]] = []
    for policy_id in sorted(workloads):
        workload = workloads[policy_id]
        allocation = workload()
        evaluation = evaluate_allocation(
            None if allocation is None else list(allocation),
            demand=demand,
            weights=weights,
            caps=caps,
            optimum=optimum,
            quality_floor=quality_floor,
        )
        policy_measurements, candidate = _measure_candidate(
            run, policy_id, workload, scenario, evaluation
        )
        measurements += policy_measurements
        candidates.append(candidate)

    preference, abstention = choose_preference(candidates, quality_floor)
    result_fields: dict[str, Any] = {
        "candidates": candidates,
        "cost_quantity": run.meter.cost_quantity,
        "cost_is_energy": run.meter.measures_energy,
        "reference_objective": round(optimum, 12),
        "meter_probe": run.probe,
    }
    if preference is None:
        return oc.new_result(
            status=oc.RESULT_ABSTAINED,
            measurements=measurements,
            abstention_reason=abstention,
            **result_fields,
        )
    return oc.new_result(
        measurements=measurements, preference=preference, **result_fields
    )


def build_records(
    seed: int,
    count: int,
    *,
    meter: EnergyOracle | None = None,
    meter_probe: dict[str, Any] | None = None,
    repeats: int = 5,
    warmup: int = 1,
    fine_steps: int = DEFAULT_FINE_STEPS,
    coarse_steps: int = DEFAULT_COARSE_STEPS,
    id_prefix: str = "ep",
) -> list[dict[str, Any]]:
    """Execute every candidate policy, meter it, and build measured records."""

    meter, probe = _resolve_meter(meter, meter_probe)
    run = _MeterRun(
        meter=meter,
        probe=probe,
        repeats=repeats,
        warmup=warmup,
        fine_steps=fine_steps,
        coarse_steps=coarse_steps,
    )
    generator = oc.new_generator(
        GENERATOR_NAME, version=GENERATOR_VERSION, kind="programmatic", seed=seed
    )
    oracle = _oracle_block(run)
    records: list[dict[str, Any]] = []
    for proposal in propose_scenarios(seed, count):
        scenario = proposal["scenario"]
        records.append(
            oc.build_record(
                record_id=f"{id_prefix}-{seed}-{proposal['index']:04d}",
                family=FAMILY,
                generator=generator,
                scenario=scenario,
                oracle=oracle,
                result=_scenario_result(run, scenario),
                provenance=oc.new_provenance(
                    "pipelines/energy_preferences.py",
                    host={
                        "platform": platform.platform(),
                        "machine": platform.machine(),
                        "python": platform.python_version(),
                    },
                ),
            )
        )
    return records


def _allocation_rejection(allocation: Any, caps: list[float]) -> str | None:
    """The reason an allocation cannot be evaluated at all, if there is one."""

    if allocation is None or (isinstance(allocation, list) and not allocation):
        return "NO_FEASIBLE_ALLOCATION_FOUND"
    if not isinstance(allocation, list) or not all(
        oc.is_number(value) for value in allocation
    ):
        return "ALLOCATION_NOT_NUMERIC"
    if len(allocation) != len(caps):
        return "ALLOCATION_WIDTH_MISMATCH"
    return None


def _allocation_shape_error(
    allocation: Any, caps: list[Any], spot: str
) -> list[str]:
    """A malformed allocation is record corruption, not a derived failure.

    The builder's only no-solution representation is ``None`` (stored as an
    empty vector). Anything else that is not a finite numeric vector of the
    actuator width never came from ``evaluate_allocation`` — converting it
    into ``ALLOCATION_NOT_NUMERIC`` let a tampered candidate restate the
    derived failure values and ship a fabricated policy failure to pairwise
    consumers.
    """

    if allocation is None or (isinstance(allocation, list) and not allocation):
        return []
    if (
        not isinstance(allocation, list)
        or not all(oc.is_number(value) for value in allocation)
        or len(allocation) != len(caps)
    ):
        return [
            f"{spot}.allocation must be null, empty, or a finite numeric "
            "vector with one entry per actuator cap"
        ]
    return []


def _cap_violations(allocation: list[Any], caps: list[float]) -> list[str]:
    """Per-actuator cap and sign violations, in actuator order."""

    violations: list[str] = []
    for index, (value, cap) in enumerate(zip(allocation, caps)):
        if float(value) > float(cap) + 1e-9:
            violations.append(f"ACTUATOR_{index}_OVER_CAP")
        if float(value) < -1e-9:
            violations.append(f"ACTUATOR_{index}_NEGATIVE")
    return violations


def _derive_safety(
    allocation: Any, demand: float, caps: list[float]
) -> tuple[bool, list[str]]:
    """Re-derive a candidate's safety from its allocation and the scenario.

    Mirrors :func:`evaluate_allocation`, so a record whose ``safety_ok`` was
    edited away from what its own allocation implies becomes a finding rather
    than a preferred candidate.
    """

    rejection = _allocation_rejection(allocation, caps)
    if rejection is not None:
        return False, [rejection]
    violations = _cap_violations(allocation, caps)
    if abs(sum(float(value) for value in allocation) - demand) > 1e-6:
        violations.append("DEMAND_NOT_MET")
    return (not violations), violations


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


def _check_scenario_constraints(
    scenario: Any, where: str
) -> tuple[list[str], float | None]:
    """Constraint checks, and the quality floor the preference is held to."""

    errors: list[str] = []
    if not isinstance(scenario, dict):
        return errors, None
    constraints = scenario.get("constraints")
    if not isinstance(constraints, dict):
        errors.append(f"{where}.scenario.constraints must be an object")
        return errors, None
    quality_floor: float | None = None
    floor = constraints.get("quality_floor")
    if not oc.is_number(floor):
        errors.append(
            f"{where}.scenario.constraints.quality_floor must be a number"
        )
    elif not 0.0 <= float(floor) <= 1.0:
        # task_quality is a ratio in [0, 1]; a floor of -1 admits every safe
        # candidate regardless of quality, and a floor above 1 admits none.
        errors.append(
            f"{where}.scenario.constraints.quality_floor must lie in [0, 1], "
            f"got {floor!r}"
        )
    else:
        quality_floor = float(floor)
    if constraints.get("safety_envelope") != SAFETY_ENVELOPE:
        errors.append(
            f"{where}.scenario.constraints.safety_envelope must state the "
            f"enforced envelope {SAFETY_ENVELOPE!r}, got "
            f"{constraints.get('safety_envelope')!r} — the description the "
            "student sees has to be the rule the labels were derived under"
        )
    return errors, quality_floor


def _check_scenario_state(scenario: Any, where: str) -> list[str]:
    """The allocation state every label is grounded in must be re-derivable.

    Silently skipping derivation when the state is malformed would let a
    record drop ``scenario.state`` (or its demand, caps or weights) and
    disable the safety, quality and reference-objective checks in one move
    while its unchanged candidates stayed curation-eligible.
    """

    if not isinstance(scenario, dict):
        return []
    state = scenario.get("state")
    if not isinstance(state, dict):
        return [
            f"{where}.scenario.state must be an object carrying the "
            "allocation problem the candidates were measured on"
        ]
    errors: list[str] = []
    if not oc.is_number(state.get("demand")):
        errors.append(f"{where}.scenario.state.demand must be a number")
    caps = state.get("actuator_caps")
    if not (
        isinstance(caps, list)
        and caps
        and all(oc.is_number(cap) for cap in caps)
    ):
        errors.append(
            f"{where}.scenario.state.actuator_caps must be a non-empty array "
            "of numbers"
        )
    weights = state.get("actuator_weights")
    if not (
        isinstance(weights, list)
        and isinstance(caps, list)
        and weights
        and len(weights) == len(caps)
        and all(oc.is_number(w) and float(w) > 0.0 for w in weights)
    ):
        errors.append(
            f"{where}.scenario.state.actuator_weights must be positive "
            "numbers, one per actuator cap"
        )
    return errors


def _proposed_actions(scenario: Any) -> dict[str, Any] | None:
    """id -> description of the proposed candidate actions, or None if unusable."""

    actions = scenario.get("candidate_actions") if isinstance(scenario, dict) else None
    if not isinstance(actions, list) or not actions:
        return None
    proposed: dict[str, Any] = {}
    for action in actions:
        if not isinstance(action, dict) or not isinstance(action.get("id"), str):
            return None
        proposed[action["id"]] = action.get("description")
    if len(proposed) != len(actions):
        return None
    return proposed


def _check_candidate_binding(
    scenario: Any, candidates: list[Any], where: str
) -> list[str]:
    """The measured candidates must be the proposed decision problem's.

    The student is shown ``scenario.candidate_actions`` as the choices on
    offer; the oracle measured ``result.candidates``. Nothing reconciled the
    two, so a record could present one action set while its preference was
    grounded in another — pairing the visible decision problem with a winner
    the student was never offered.
    """

    proposed = _proposed_actions(scenario)
    if proposed is None:
        return [
            f"{where}.scenario.candidate_actions must list each proposed "
            "policy exactly once as an object with a string id"
        ]
    measured = {
        candidate["id"]: candidate.get("description")
        for candidate in candidates
        if isinstance(candidate, dict) and isinstance(candidate.get("id"), str)
    }
    if set(proposed) != set(measured):
        return [
            f"{where}: CANDIDATE_SET_MISMATCH — scenario.candidate_actions "
            f"proposes {sorted(proposed)} but result.candidates measured "
            f"{sorted(measured)}"
        ]
    return [
        f"{where}: candidate {candidate_id!r} is described as "
        f"{measured[candidate_id]!r} but was proposed as "
        f"{proposed[candidate_id]!r}"
        for candidate_id in sorted(proposed)
        if measured[candidate_id] != proposed[candidate_id]
    ]


def _check_cost_denomination(result: dict[str, Any], where: str) -> list[str]:
    """The corpus quantity, and the energy flag that must follow from it.

    The flag that tells a joule corpus from a second corpus. Readers,
    MANIFEST.json and the "no theoretical energy" rule all lean on it, so it
    has to follow from the quantity rather than be asserted alongside it.
    """

    errors: list[str] = []
    corpus_quantity = result.get("cost_quantity")
    cost_is_energy = result.get("cost_is_energy")
    if not oc.is_enum_value(corpus_quantity, SUPPORTED_COST_QUANTITIES):
        # Any registered quantity used to pass, so a record could quietly
        # minimise temperature or latency under this family's name.
        errors.append(
            f"{where}.result.cost_quantity must be one of "
            f"{sorted(SUPPORTED_COST_QUANTITIES)}, got {corpus_quantity!r}"
        )
    if not isinstance(cost_is_energy, bool):
        errors.append(f"{where}.result.cost_is_energy must be a boolean")
    elif cost_is_energy != oc.is_enum_value(corpus_quantity, oc.ENERGY_QUANTITIES):
        errors.append(
            f"{where}.result.cost_is_energy is {cost_is_energy} but cost_quantity "
            f"is {corpus_quantity!r} — the flag must follow the quantity"
        )
    return errors


def _usable_measurement(item: Any) -> tuple[tuple[str, str], _Reading] | None:
    """The ``(key, reading)`` of a measurement, or None if it is not usable."""

    if not isinstance(item, dict):
        return None
    detail = item.get("detail")
    candidate_id = detail.get("candidate") if isinstance(detail, dict) else None
    quantity = item.get("quantity")
    meter = item.get("meter")
    if (
        isinstance(candidate_id, str)
        and isinstance(quantity, str)
        and oc.is_number(item.get("value"))
        and isinstance(meter, str)
    ):
        reading = _Reading(
            value=item["value"], meter=meter, measured=item.get("measured")
        )
        return (candidate_id, quantity), reading
    return None


def _collect_measured_costs(
    result: dict[str, Any], where: str
) -> tuple[list[str], dict[tuple[str, str], _Reading]]:
    """Index the oracle measurements, reporting readings that contradict.

    Keyed by a tuple, not a joined string, so a candidate id containing the
    separator cannot be made to collide with another candidate's reading.
    """

    errors: list[str] = []
    measured_costs: dict[tuple[str, str], _Reading] = {}
    measurements = result.get("measurements")
    measurements = measurements if isinstance(measurements, list) else []
    for item in measurements:
        usable = _usable_measurement(item)
        if usable is None:
            continue
        key, reading = usable
        previous = measured_costs.get(key)
        if previous is None:
            measured_costs[key] = reading
            continue
        # Silently keeping the first reading made the preference depend
        # on JSON array order while the record still carried the
        # contradicting one. Two readings that disagree are a finding.
        if (
            abs(float(previous.value) - float(reading.value)) > 1e-12
            or previous.meter != reading.meter
            or (previous.measured is True) != (reading.measured is True)
        ):
            candidate_id, quantity = key
            errors.append(
                f"{where}.result.measurements: CONFLICTING_MEASUREMENT — "
                f"{quantity} for candidate {candidate_id!r} is recorded "
                f"both as {previous.value!r} ({previous.meter}) and "
                f"{reading.value!r} ({reading.meter})"
            )
    return errors, measured_costs


def _safety_derivation_inputs(scenario: Any) -> tuple[bool, Any, Any]:
    """The scenario state needed to re-derive a candidate's safety verdict."""

    state = scenario.get("state") if isinstance(scenario, dict) else None
    caps = state.get("actuator_caps") if isinstance(state, dict) else None
    demand = state.get("demand") if isinstance(state, dict) else None
    can_derive_safety = (
        isinstance(caps, list)
        and bool(caps)
        and all(oc.is_number(cap) for cap in caps)
        and oc.is_number(demand)
    )
    return can_derive_safety, caps, demand


# Slack for re-deriving task_quality from a recorded allocation. Allocations
# are stored rounded to 9 places and qualities to 6, so an exact comparison
# would reject honest records; a real tamper has to move the quality by
# orders of magnitude more than this to matter against a 0.98 floor.
QUALITY_TOLERANCE = 2e-6


def _usable_weights(scenario: Any, caps: Any) -> list[float] | None:
    """The actuator weights, when they can parameterise the objective."""

    state = scenario.get("state") if isinstance(scenario, dict) else None
    weights = state.get("actuator_weights") if isinstance(state, dict) else None
    if (
        isinstance(weights, list)
        and len(weights) == len(caps)
        and all(oc.is_number(w) and float(w) > 0.0 for w in weights)
    ):
        return [float(w) for w in weights]
    return None


def _quality_derivation_inputs(
    scenario: Any, *, can_derive_safety: bool, caps: Any, demand: Any
) -> tuple[list[float] | None, float | None]:
    """The weights and re-derived optimum quality is measured against."""

    if not can_derive_safety:
        return None, None
    weights = _usable_weights(scenario, caps)
    if weights is None:
        return None, None
    optimum = objective(
        weights,
        analytic_allocation(float(demand), weights, [float(cap) for cap in caps]),
    )
    return weights, optimum


def _derived_quality(allocation: Any, context: _CandidateContext) -> float | None:
    """The task quality this allocation earns, or None when unevaluable.

    Non-numeric or wrong-width allocations are already reported by the safety
    derivation; a policy that produced no answer has quality 0.0 by definition.
    """

    caps = [float(cap) for cap in context.caps]
    if _allocation_rejection(allocation, caps) is None:
        return evaluate_allocation(
            [float(value) for value in allocation],
            demand=float(context.demand),
            weights=context.weights,
            caps=caps,
            optimum=context.optimum,
            quality_floor=0.0,
        ).task_quality
    if allocation is None or (isinstance(allocation, list) and not allocation):
        return 0.0
    return None


def _check_quality_derivation(
    candidate: dict[str, Any], spot: str, context: _CandidateContext
) -> list[str]:
    """task_quality is a function of the allocation and the scenario state.

    Binding the candidate's quality to its oracle measurement is not enough:
    editing both together keeps them agreeing while lowering the cheapest safe
    candidate below the floor, so a correctly rehashed record could steer the
    preference to a more expensive candidate and stay validation-clean.
    Re-deriving the quality from the recorded allocation pins both stored
    values to the arithmetic the scenario defines.
    """

    if context.optimum is None or context.weights is None:
        return []
    derived = _derived_quality(candidate.get("allocation"), context)
    if derived is None:
        return []
    recorded = candidate.get("task_quality")
    if oc.is_number(recorded) and abs(float(recorded) - derived) > QUALITY_TOLERANCE:
        return [
            f"{spot}: QUALITY_NOT_REPRODUCIBLE — task_quality is {recorded} "
            f"but re-evaluating the recorded allocation against the scenario "
            f"state yields {derived}"
        ]
    return []


def _check_reference_objective(
    result: dict[str, Any], context: _CandidateContext, where: str
) -> list[str]:
    """The restated reference objective must match the scenario's own optimum."""

    if context.optimum is None:
        return []
    recorded = result.get("reference_objective")
    if not oc.is_number(recorded):
        # The scenario supplies everything needed to derive the optimum, so
        # a deleted or non-numeric restatement is a finding — skipping the
        # comparison silently lost the reference target that grounds
        # candidate quality.
        return [
            f"{where}.result.reference_objective must restate the scenario "
            f"optimum as a finite number — the state derives "
            f"{round(context.optimum, 12)}"
        ]
    if abs(float(recorded) - context.optimum) > 1e-9:
        return [
            f"{where}.result.reference_objective is {recorded} but the "
            f"scenario state yields {round(context.optimum, 12)}"
        ]
    return []


def _check_candidate_safety(
    candidate: dict[str, Any], spot: str, context: _CandidateContext
) -> list[str]:
    """safety_ok and safety_violations, re-derived from the scenario state."""

    errors: list[str] = []
    if not isinstance(candidate.get("safety_ok"), bool):
        errors.append(f"{spot}.safety_ok must be a boolean")
    elif context.can_derive_safety:
        shape_errors = _allocation_shape_error(
            candidate.get("allocation"), list(context.caps), spot
        )
        if shape_errors:
            # Deriving from a corrupt allocation would only restate the
            # fabricated failure the tamper wrote; report the corruption.
            return errors + shape_errors
        # safety_ok summarises the allocation; it is not an independent
        # fact. Trusting it lets an obviously over-cap allocation be
        # preferred as the feasible minimum.
        derived_ok, derived_violations = _derive_safety(
            candidate.get("allocation"),
            float(context.demand),
            [float(c) for c in context.caps],
        )
        if candidate["safety_ok"] is not derived_ok:
            errors.append(
                f"{spot}: SAFETY_NOT_REPRODUCIBLE — safety_ok is "
                f"{candidate['safety_ok']} but the recorded allocation "
                f"against the scenario state yields {derived_ok} "
                f"({sorted(derived_violations)})"
            )
        recorded_violations = candidate.get("safety_violations")
        if isinstance(recorded_violations, list) and sorted(
            str(item) for item in recorded_violations
        ) != sorted(derived_violations):
            errors.append(
                f"{spot}: SAFETY_NOT_REPRODUCIBLE — safety_violations are "
                f"{sorted(str(v) for v in recorded_violations)} but the "
                f"allocation yields {sorted(derived_violations)}"
            )
    return errors


def _check_quality_binding(
    candidate: dict[str, Any],
    candidate_id: str,
    spot: str,
    context: _CandidateContext,
) -> list[str]:
    """Quality gates the preference as hard as cost, so bind it to its measurement.

    Otherwise a candidate can claim 0.99 while its oracle measurement says
    0.0 and still clear the floor.
    """

    quality_key = (candidate_id, "task_quality")
    reading = context.measured_costs.get(quality_key)
    if reading is None:
        return [
            f"{spot}: UNMEASURED_TASK_QUALITY — no oracle measurement of "
            f"task_quality for candidate {candidate_id!r}"
        ]
    errors: list[str] = []
    if reading.measured is not True:
        # A reading marked `measured: false` is a model wearing a
        # measurement's clothes. Quality gates the preference, so the reading
        # that backs it has to be one the oracle actually took.
        errors.append(
            f"{spot}: UNMEASURED_TASK_QUALITY — the task_quality reading for "
            f"candidate {candidate_id!r} is marked measured: "
            f"{reading.measured!r}, so nothing measured backs the quality gate"
        )
    if oc.is_number(candidate.get("task_quality")) and (
        abs(reading.value - float(candidate["task_quality"])) > 1e-9
    ):
        errors.append(
            f"{spot}.task_quality disagrees with the oracle measurement "
            f"({candidate['task_quality']} vs {reading.value})"
        )
    return errors


def _check_cost_binding(
    candidate: dict[str, Any],
    candidate_id: str,
    spot: str,
    context: _CandidateContext,
) -> list[str]:
    """Bind the recorded cost and its instrument to the oracle measurement."""

    quantity = candidate.get("cost_quantity")
    candidate_meter = candidate.get("cost_meter")
    reading = context.measured_costs.get((candidate_id, quantity))
    if reading is None:
        return [
            f"{spot}: UNMEASURED_COST — no oracle measurement of {quantity} "
            f"for candidate {candidate_id!r}"
        ]
    errors: list[str] = []
    if reading.measured is not True:
        # The preference minimises this number. A cost whose backing reading
        # says `measured: false` is a modelled cost, which is exactly what
        # this family exists to refuse.
        errors.append(
            f"{spot}: UNMEASURED_COST — the {quantity} reading backing "
            f"candidate {candidate_id!r} is marked measured: "
            f"{reading.measured!r}, so no measured cost stands behind it"
        )
    if abs(reading.value - float(candidate["cost_value"])) > 1e-12:
        errors.append(
            f"{spot}.cost_value disagrees with the oracle measurement "
            f"({candidate['cost_value']} vs {reading.value})"
        )
    if reading.meter != candidate_meter:
        errors.append(
            f"{spot}.cost_meter is {candidate_meter!r} but the measurement "
            f"meter is {reading.meter!r}"
        )
    return errors


def _check_candidate_measurements(
    candidate: dict[str, Any],
    candidate_id: str,
    spot: str,
    context: _CandidateContext,
) -> list[str]:
    """Bind a candidate's quality, cost and meter to the oracle measurements."""

    errors: list[str] = []
    quantity = candidate.get("cost_quantity")
    if not oc.is_enum_value(quantity, SUPPORTED_COST_QUANTITIES):
        errors.append(
            f"{spot}.cost_quantity must be one of "
            f"{sorted(SUPPORTED_COST_QUANTITIES)}, got {quantity!r}"
        )
        return errors
    if (
        oc.is_enum_value(context.corpus_quantity, oc.QUANTITY_UNITS)
        and quantity != context.corpus_quantity
    ):
        errors.append(
            f"{spot}.cost_quantity is {quantity!r} but the record is "
            f"denominated in {context.corpus_quantity!r} — costs must be comparable"
        )
    if not oc.is_number(candidate.get("cost_value")):
        errors.append(f"{spot}.cost_value must be a number")
        return errors
    if float(candidate["cost_value"]) < 0.0:
        # Cheapest wins, so a negative cost takes the preference outright.
        # No meter in this pipeline can produce one.
        errors.append(
            f"{spot}: NEGATIVE_COST — {candidate['cost_value']} "
            f"{quantity} is not a physically possible measurement"
        )
    candidate_meter = candidate.get("cost_meter")
    if not isinstance(candidate_meter, str) or not candidate_meter:
        errors.append(f"{spot}.cost_meter must be a non-empty string")
        return errors
    # cost_meter names the *instrument*, not the oracle. On the replay path
    # the oracle is `recorded_power_run` while the instrument that actually
    # took the reading stays `external_power_meter`, so pinning cost_meter to
    # oracle.name or meter_probe.selected would reject every recorded run.
    # The binding that matters — cost_meter against the meter of the
    # measurement it cites — is enforced against measured_meter.
    errors += _check_quality_binding(candidate, candidate_id, spot, context)
    errors += _check_cost_binding(candidate, candidate_id, spot, context)
    return errors


def _check_candidate_success(
    candidate: Any, spot: str, quality_floor: float | None
) -> list[str]:
    """``success`` is a summary of safety and the floor, not a free bit.

    ``build_records`` writes ``success = safety_ok and task_quality >=
    quality_floor``; nothing re-derived it, so flipping the unsafe
    candidate's ``false`` to ``true`` and rehashing left a curation-eligible
    record with contradictory candidate labels.
    """

    if not isinstance(candidate, dict):
        return []
    success = candidate.get("success")
    if not isinstance(success, bool):
        return [f"{spot}.success must be a boolean"]
    if quality_floor is None or not oc.is_number(candidate.get("task_quality")):
        # The floor and the quality carry their own findings when malformed;
        # without them the summary cannot be re-derived.
        return []
    expected = (
        candidate.get("safety_ok") is True
        and float(candidate["task_quality"]) >= quality_floor
    )
    if success is not expected:
        return [
            f"{spot}.success is {success} but safety_ok "
            f"{candidate.get('safety_ok')!r} and task_quality "
            f"{candidate['task_quality']} against quality_floor "
            f"{quality_floor} give {expected}"
        ]
    return []


def _check_candidate(
    candidate: Any,
    spot: str,
    seen_candidate_ids: set[str],
    context: _CandidateContext,
) -> list[str]:
    """One measured candidate, in the order the findings were emitted."""

    if not isinstance(candidate, dict):
        return [f"{spot} must be an object"]
    candidate_id = candidate.get("id")
    if not isinstance(candidate_id, str) or not candidate_id:
        return [f"{spot}.id must be a non-empty string"]
    if candidate_id in seen_candidate_ids:
        # The preference names a candidate by id. Two candidates sharing one
        # makes the winning allocation ambiguous, and the cost measurements
        # can no longer be attributed to either.
        return [
            f"{spot}: DUPLICATE_CANDIDATE_ID — {candidate_id!r} is already "
            "used by an earlier candidate"
        ]
    seen_candidate_ids.add(candidate_id)
    errors = _check_candidate_safety(candidate, spot, context)
    if not oc.is_number(candidate.get("task_quality")):
        errors.append(f"{spot}.task_quality must be a number")
    errors += _check_quality_derivation(candidate, spot, context)
    errors += _check_candidate_measurements(candidate, candidate_id, spot, context)
    return errors


def _feasible_rivals(
    candidates: list[Any], preferred_id: Any, quality_floor: float
) -> list[dict[str, Any]]:
    """Every other candidate that is safe, clears the floor, and has a cost."""

    return [
        candidate
        for candidate in candidates
        if isinstance(candidate, dict)
        and candidate.get("id") != preferred_id
        and candidate.get("safety_ok") is True
        and oc.is_number(candidate.get("task_quality"))
        and float(candidate["task_quality"]) >= quality_floor
        and oc.is_number(candidate.get("cost_value"))
    ]


def _check_preferred_cost_minimality(
    preferred: dict[str, Any],
    candidates: list[Any],
    quality_floor: float,
    where: str,
) -> list[str]:
    """The preferred candidate must be the cheapest feasible one, tie-break included.

    ``preferred`` came out of a ``{candidate["id"]: candidate}`` index, so its
    ``id`` is the very object the preference named.
    """

    errors: list[str] = []
    preferred_id = preferred["id"]
    preferred_cost = float(preferred["cost_value"])
    feasible_rivals = _feasible_rivals(candidates, preferred_id, quality_floor)
    cheaper_feasible = [
        candidate["id"]
        for candidate in feasible_rivals
        if float(candidate["cost_value"]) < preferred_cost - 1e-12
    ]
    if cheaper_feasible:
        errors.append(
            f"{where}.result.preference: NOT_MINIMAL_FEASIBLE_COST — "
            f"{sorted(cheaper_feasible)} are feasible and cheaper than "
            f"{preferred_id!r}"
        )
    # `choose_preference` breaks a cost tie by candidate id, which coarse
    # counters make a real case rather than a theoretical one. Without this
    # either side of a tie validates, so the label is not a function of the
    # measurements.
    tied_lower_id = [
        candidate["id"]
        for candidate in feasible_rivals
        if abs(float(candidate["cost_value"]) - preferred_cost) <= 1e-12
        and isinstance(candidate.get("id"), str)
        and isinstance(preferred_id, str)
        and candidate["id"] < preferred_id
    ]
    if tied_lower_id:
        errors.append(
            f"{where}.result.preference: TIE_NOT_BROKEN_BY_ID — "
            f"{sorted(tied_lower_id)} tie {preferred_id!r} on measured cost "
            "and sort before it, so the documented tie-break selects the "
            "first of those instead"
        )
    return errors


def _derived_membership(
    candidates: list[Any], quality_floor: float, preferred: dict[str, Any]
) -> dict[str, list[str]]:
    """The membership lists ``choose_preference`` would derive."""

    rows = [
        candidate
        for candidate in candidates
        if isinstance(candidate, dict) and isinstance(candidate.get("id"), str)
    ]
    preferred_id = preferred["id"]
    preferred_cost = float(preferred["cost_value"])
    return {
        "over": sorted(row["id"] for row in rows if row["id"] != preferred_id),
        "feasible": sorted(
            row["id"] for row in _feasible_candidates(rows, quality_floor)
        ),
        "cheaper_but_constraint_violating": sorted(
            row["id"]
            for row in rows
            if row["id"] != preferred_id
            and oc.is_number(row.get("cost_value"))
            and float(row["cost_value"]) < preferred_cost
        ),
    }


def _membership_field_error(
    preference: dict[str, Any], field: str, expected: list[str], where: str
) -> list[str]:
    recorded = preference.get(field)
    recorded_ids = (
        sorted(str(item) for item in recorded) if isinstance(recorded, list) else None
    )
    if recorded_ids == expected:
        return []
    return [
        f"{where}.result.preference.{field}: "
        f"PREFERENCE_MEMBERSHIP_NOT_REPRODUCIBLE — recorded "
        f"{recorded!r} but the measured candidates yield {expected}"
    ]


def _check_preference_membership(
    preference: dict[str, Any],
    candidates: list[Any],
    quality_floor: float,
    preferred: dict[str, Any],
    where: str,
) -> list[str]:
    """``over``, ``feasible`` and the cheaper-but-rejected list are derived.

    ``choose_preference`` computes all three from the measured candidates.
    Left unchecked, a record could ship arbitrary lists — no opponents, a
    fabricated feasible set, or a false account of which constraints rejected
    each policy — while everything else validated clean, and pairwise
    consumers would train on that account.
    """

    errors: list[str] = []
    derived = _derived_membership(candidates, quality_floor, preferred)
    for field, expected in derived.items():
        errors += _membership_field_error(preference, field, expected, where)
    restated_floor = preference.get("quality_floor")
    if not oc.is_number(restated_floor) or (
        abs(float(restated_floor) - quality_floor) > 1e-12
    ):
        errors.append(
            f"{where}.result.preference.quality_floor is {restated_floor!r} "
            f"but the scenario constraint is {quality_floor}"
        )
    return errors


def _check_preference_restatement(
    preference: dict[str, Any], preferred: dict[str, Any], where: str
) -> list[str]:
    """The preference restates the winner's cost; it must not drift.

    If that restatement is free to drift, a record can advertise a cheap
    energy figure while the candidate it points at was measured in seconds.
    """

    errors: list[str] = []
    preferred_id = preferred["id"]
    if preference.get("cost_quantity") != preferred.get("cost_quantity"):
        errors.append(
            f"{where}.result.preference.cost_quantity is "
            f"{preference.get('cost_quantity')!r} but {preferred_id!r} was measured "
            f"in {preferred.get('cost_quantity')!r}"
        )
    if not oc.is_number(preference.get("cost_value")) or (
        oc.is_number(preferred.get("cost_value"))
        and abs(float(preference["cost_value"]) - float(preferred["cost_value"])) > 1e-12
    ):
        errors.append(
            f"{where}.result.preference.cost_value is "
            f"{preference.get('cost_value')!r} but {preferred_id!r} measured "
            f"{preferred.get('cost_value')!r}"
        )
    return errors


def _check_preferred_feasibility(
    preferred: dict[str, Any], quality_floor: float | None, where: str
) -> list[str]:
    """The winner must itself be safe and clear the quality floor."""

    errors: list[str] = []
    preferred_id = preferred["id"]
    if preferred.get("safety_ok") is not True:
        errors.append(
            f"{where}.result.preference: PREFERRED_CANDIDATE_UNSAFE — "
            f"{preferred_id!r} violates {preferred.get('safety_violations')}"
        )
    if quality_floor is not None and oc.is_number(preferred.get("task_quality")):
        if float(preferred["task_quality"]) < quality_floor:
            errors.append(
                f"{where}.result.preference: PREFERRED_CANDIDATE_BELOW_QUALITY_FLOOR "
                f"({preferred['task_quality']} < {quality_floor})"
            )
    return errors


def _preferred_candidate(
    preference: dict[str, Any], candidates: list[Any]
) -> dict[str, Any] | None:
    """The candidate the preference names, if it names a measured one."""

    preferred = preference.get("preferred")
    if not isinstance(preferred, str) or not preferred:
        # A JSON object or array here is unhashable: looking it up raised
        # TypeError straight out of the family checker, and validate_path does
        # not catch that — one malformed record aborted validation of the
        # whole run instead of being reported as one bad line.
        return None
    by_id = {
        candidate["id"]: candidate
        for candidate in candidates
        if isinstance(candidate, dict) and isinstance(candidate.get("id"), str)
    }
    return by_id.get(preferred)


def _check_abstention_feasibility(
    result: dict[str, Any],
    candidates: list[Any],
    quality_floor: float | None,
    where: str,
) -> list[str]:
    """An abstention must be earned by the measured candidates.

    The family's only abstention path is ``choose_preference`` finding no
    feasible candidate, so a record relabelled ``abstained`` while its own
    measurements still contain safe, quality-clearing, costed candidates is
    a silently discarded label, not an oracle abstention.
    """

    if quality_floor is None:
        # The malformed floor carries its own finding; without it the
        # feasible set cannot be re-derived.
        return []
    errors: list[str] = []
    reason = result.get("abstention_reason")
    if reason != ABSTAIN_NO_FEASIBLE:
        errors.append(
            f"{where}.result.abstention_reason must be the canonical "
            f"{ABSTAIN_NO_FEASIBLE!r} — it is this family's only abstention"
        )
    feasible = _feasible_candidates(
        [c for c in candidates if isinstance(c, dict)], quality_floor
    )
    if feasible:
        errors.append(
            f"{where}.result: FALSE_ABSTENTION — "
            f"{sorted(c['id'] for c in feasible if isinstance(c.get('id'), str))} "
            "satisfy the quality and safety constraints, so the oracle had a "
            "preference to record"
        )
    return errors


def _check_preference(
    result: dict[str, Any],
    candidates: list[Any],
    quality_floor: float | None,
    where: str,
) -> list[str]:
    """The preference, and the restatements of the winner it must agree with."""

    errors: list[str] = []
    status = result.get("status")
    preference = result.get("preference")
    if status == oc.RESULT_ABSTAINED:
        if preference is not None:
            errors.append(
                f"{where}.result: an abstained result must not carry a preference"
            )
        return errors + _check_abstention_feasibility(
            result, candidates, quality_floor, where
        )
    if not isinstance(preference, dict):
        return errors + [
            f"{where}.result.preference must be an object (or the result must abstain)"
        ]
    if preference.get("decision_rule") != DECISION_RULE:
        errors.append(f"{where}.result.preference.decision_rule must be {DECISION_RULE!r}")
    preferred = _preferred_candidate(preference, candidates)
    if preferred is None:
        return errors + [
            f"{where}.result.preference.preferred must name a measured candidate"
        ]
    errors += _check_preference_restatement(preference, preferred, where)
    errors += _check_preferred_feasibility(preferred, quality_floor, where)
    # A non-numeric preferred cost is a finding, not an exception. `float()` on
    # it used to raise straight out of the family checker, and validate_path
    # does not catch that — one malformed record would abort validation of the
    # entire run instead of being reported as one bad line.
    if quality_floor is not None and oc.is_number(preferred.get("cost_value")):
        errors += _check_preferred_cost_minimality(
            preferred, candidates, quality_floor, where
        )
        errors += _check_preference_membership(
            preference, candidates, quality_floor, preferred, where
        )
    return errors


def _check_oracle_audit(record: dict[str, Any], where: str) -> list[str]:
    """The audit metadata behind an authoritative measured preference.

    Nothing validated ``oracle.configuration`` or ``oracle.fingerprint``, so
    deleting both left a record curation-eligible while no longer
    identifying the meter host, probe result, repeat/warmup settings, or
    solver configuration behind its measured costs — the documented audit
    trail for oracle-grounded energy.
    """

    oracle = record.get("oracle")
    if not isinstance(oracle, dict):
        # The envelope reports a missing or malformed oracle block.
        return []
    errors: list[str] = []
    fingerprint = oracle.get("fingerprint")
    if not isinstance(fingerprint, dict) or not fingerprint:
        errors.append(
            f"{where}.oracle.fingerprint must identify the meter host that "
            "measured this record"
        )
    configuration = oracle.get("configuration")
    if not isinstance(configuration, dict):
        return errors + [
            f"{where}.oracle.configuration must record the meter probe and "
            "solver settings behind the measured costs"
        ]
    for key in ("repeats", "warmup", "fine_steps", "coarse_steps"):
        if not oc.is_number(configuration.get(key)):
            errors.append(f"{where}.oracle.configuration.{key} must be a number")
    probe = configuration.get("meter_probe")
    if not isinstance(probe, dict):
        return errors + [
            f"{where}.oracle.configuration.meter_probe must document the "
            "probed meters and the selection"
        ]
    selected = probe.get("selected")
    if not isinstance(selected, str) or not selected.strip():
        errors.append(
            f"{where}.oracle.configuration.meter_probe.selected must name "
            "the selected meter"
        )
    result = record.get("result")
    corpus_quantity = result.get("cost_quantity") if isinstance(result, dict) else None
    cost_is_energy = result.get("cost_is_energy") if isinstance(result, dict) else None
    if probe.get("cost_quantity") != corpus_quantity:
        errors.append(
            f"{where}.oracle.configuration.meter_probe.cost_quantity is "
            f"{probe.get('cost_quantity')!r} but the corpus is denominated "
            f"in {corpus_quantity!r}"
        )
    if probe.get("cost_is_energy") != cost_is_energy:
        errors.append(
            f"{where}.oracle.configuration.meter_probe.cost_is_energy is "
            f"{probe.get('cost_is_energy')!r} but result.cost_is_energy is "
            f"{cost_is_energy!r}"
        )
    return errors


def check_family(record: dict[str, Any], where: str) -> list[str]:
    """Family checks: measured cost, and a preference that respects limits."""

    scenario = record.get("scenario")
    errors, quality_floor = _check_scenario_constraints(scenario, where)
    errors += _check_scenario_state(scenario, where)
    errors += _check_oracle_audit(record, where)

    result = record.get("result")
    if not isinstance(result, dict):
        return errors + [f"{where}.result must be an object"]

    candidates = result.get("candidates")
    if not isinstance(candidates, list) or len(candidates) < 2:
        return errors + [
            f"{where}.result.candidates must list at least two measured candidates"
        ]

    errors += _check_candidate_binding(scenario, candidates, where)
    errors += _check_cost_denomination(result, where)
    measurement_errors, measured_costs = _collect_measured_costs(result, where)
    errors += measurement_errors

    can_derive_safety, caps, demand = _safety_derivation_inputs(scenario)
    weights, optimum = _quality_derivation_inputs(
        scenario, can_derive_safety=can_derive_safety, caps=caps, demand=demand
    )
    context = _CandidateContext(
        measured_costs=measured_costs,
        corpus_quantity=result.get("cost_quantity"),
        can_derive_safety=can_derive_safety,
        caps=caps,
        demand=demand,
        weights=weights,
        optimum=optimum,
    )
    errors += _check_reference_objective(result, context, where)

    seen_candidate_ids: set[str] = set()
    for index, candidate in enumerate(candidates):
        spot = f"{where}.result.candidates[{index}]"
        errors += _check_candidate(candidate, spot, seen_candidate_ids, context)
        errors += _check_candidate_success(candidate, spot, quality_floor)

    return errors + _check_preference(result, candidates, quality_floor, where)


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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)

    measure = sub.add_parser("measure", help="execute and meter candidate policies")
    measure.add_argument("--seed", type=int, default=20260823)
    measure.add_argument("--count", type=int, default=4)
    measure.add_argument("--repeats", type=int, default=5, choices=range(1, 1001), metavar="1-1000")
    measure.add_argument("--output", help="destination JSONL (must not exist)")

    meters = sub.add_parser("meters", help="probe meter availability")
    meters.add_argument("--json", action="store_true")

    args = parser.parse_args(argv)
    if args.command == "meters":
        print(json.dumps(meters_report(), indent=2, sort_keys=True))
        return 0

    records = build_records(args.seed, args.count, repeats=args.repeats)
    if args.output:
        written = oc.write_jsonl(args.output, records)
        print(json.dumps({"written": written, "output": args.output}, indent=2))
    else:
        for record in records:
            print(oc.canonical_json(record))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
