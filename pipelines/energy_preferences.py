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
import json
import platform
import random
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

ABSTAIN_NO_FEASIBLE = "NO_CANDIDATE_SATISFIES_QUALITY_AND_SAFETY_CONSTRAINTS"
ABSTAIN_NO_MEASUREMENT = "NO_MEASURED_COST_AVAILABLE"


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
        ]
        if rss_after is not None and rss_before is not None:
            extra.append(
                oc.new_measurement("max_rss_kb", float(rss_after - rss_before), self.name)
            )
        if switches_after is not None and switches_before is not None:
            extra.append(
                oc.new_measurement(
                    "context_switches",
                    float(switches_after - switches_before),
                    self.name,
                )
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

    def __init__(self, root: Path | None = None) -> None:
        self.root = Path(root) if root is not None else RAPL_ROOT

    def _domains(self) -> list[Path]:
        if not self.root.is_dir():
            return []
        return sorted(
            child
            for child in self.root.iterdir()
            if child.name.startswith("intel-rapl:") and (child / "energy_uj").exists()
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
        before = self._read_uj()
        wall_start = time.perf_counter_ns()
        for _ in range(repeats):
            workload()
        wall_s = (time.perf_counter_ns() - wall_start) / 1e9
        after = self._read_uj()
        total_uj = 0
        for name, start in before.items():
            end = after.get(name, start)
            delta = end - start
            if delta < 0:  # counter wraparound
                delta += ranges.get(name, 0)
            total_uj += max(delta, 0)
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
        self.source_meter = recording.get("meter", self.name)
        self.cost_quantity = recording.get("cost_quantity", self.cost_quantity)
        self.measures_energy = self.cost_quantity in oc.ENERGY_QUANTITIES
        observations = recording.get("observations")
        self.observations = observations if isinstance(observations, dict) else {}

    @classmethod
    def from_path(cls, path) -> "RecordedEnergyMeter":
        return cls(json.loads(Path(path).read_text(encoding="utf-8")))

    def available(self) -> tuple[bool, str]:
        if not self.observations:
            return False, "recording contains no observations"
        return True, f"{len(self.observations)} recorded observation(s)"

    def lookup(self, key: str) -> MeterReading:
        entry = self.observations.get(key)
        if not isinstance(entry, dict) or not oc.is_number(entry.get("cost_value")):
            raise oc.OracleUnavailable(
                self.name, f"no recorded measurement for key {key!r}"
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


def propose_scenarios(seed: int, count: int) -> list[dict[str, Any]]:
    """Generator side: equivalent policy alternatives, with no cost attached."""

    if count < 1:
        raise oc.ContractError("count must be >= 1")
    rng = random.Random(seed)
    proposals: list[dict[str, Any]] = []
    for index in range(count):
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
        proposals.append(
            {
                "index": index,
                "scenario": {
                    "task": "capped quadratic actuator allocation",
                    "state": {
                        "demand": demand,
                        "actuator_weights": weights,
                        "actuator_caps": caps,
                    },
                    "constraints": {
                        "quality_floor": 0.98,
                        "safety_envelope": "0 <= x_i <= cap_i and sum(x_i) == demand",
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
    """

    feasible = [
        candidate
        for candidate in candidates
        if candidate.get("safety_ok") is True
        and oc.is_number(candidate.get("task_quality"))
        and candidate["task_quality"] >= quality_floor
        and oc.is_number(candidate.get("cost_value"))
    ]
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


def build_records(
    seed: int,
    count: int,
    *,
    meter: EnergyOracle | None = None,
    meter_probe: dict[str, Any] | None = None,
    repeats: int = 5,
    warmup: int = 1,
    fine_steps: int = 48,
    coarse_steps: int = 8,
    id_prefix: str = "ep",
) -> list[dict[str, Any]]:
    """Execute every candidate policy, meter it, and build measured records."""

    if meter is None:
        meter, probe = select_meter(prefer_energy=True)
    else:
        if meter_probe is not None:
            probe = meter_probe
        else:
            ok, detail = meter.available()
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
        ok, detail = meter.available()
        if not ok:
            raise oc.OracleUnavailable(meter.name, detail)

    generator = oc.new_generator(
        GENERATOR_NAME, version=GENERATOR_VERSION, kind="programmatic", seed=seed
    )
    oracle = oc.new_oracle(
        meter.name,
        oracle_type="measured_execution",
        implementation=f"pipelines/energy_preferences.py:{type(meter).__name__}",
        version=meter.version,
        authority=oc.AUTHORITY_AUTHORITATIVE,
        configuration={
            "repeats": repeats,
            "warmup": warmup,
            "fine_steps": fine_steps,
            "coarse_steps": coarse_steps,
            "meter_probe": probe,
        },
        seed=None,
        commit=None,
        fingerprint=meter.fingerprint(),
    )

    records: list[dict[str, Any]] = []
    for proposal in propose_scenarios(seed, count):
        scenario = proposal["scenario"]
        state = scenario["state"]
        demand = float(state["demand"])
        weights = [float(value) for value in state["actuator_weights"]]
        caps = [float(value) for value in state["actuator_caps"]]
        quality_floor = float(scenario["constraints"]["quality_floor"])
        optimum = objective(weights, analytic_allocation(demand, weights, caps))

        workloads = _policy_workloads(
            demand, weights, caps, fine_steps=fine_steps, coarse_steps=coarse_steps
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
            reading = meter.measure(workload, repeats=repeats, warmup=warmup)
            cost_measurement = oc.new_measurement(
                reading.cost_quantity,
                reading.cost_value,
                reading.meter,
                detail={"candidate": policy_id, **(reading.detail or {})},
            )
            measurements.append(cost_measurement)
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
            candidates.append(
                {
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
            )

        preference, abstention = choose_preference(candidates, quality_floor)
        result_fields: dict[str, Any] = {
            "candidates": candidates,
            "cost_quantity": meter.cost_quantity,
            "cost_is_energy": meter.measures_energy,
            "reference_objective": round(optimum, 12),
            "meter_probe": probe,
        }
        if preference is None:
            result = oc.new_result(
                status=oc.RESULT_ABSTAINED,
                measurements=measurements,
                abstention_reason=abstention,
                **result_fields,
            )
        else:
            result = oc.new_result(
                measurements=measurements, preference=preference, **result_fields
            )
        records.append(
            oc.build_record(
                record_id=f"{id_prefix}-{seed}-{proposal['index']:04d}",
                family=FAMILY,
                generator=generator,
                scenario=scenario,
                oracle=oracle,
                result=result,
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


def check_family(record: dict[str, Any], where: str) -> list[str]:
    """Family checks: measured cost, and a preference that respects limits."""

    errors: list[str] = []
    scenario = record.get("scenario")
    quality_floor: float | None = None
    if isinstance(scenario, dict):
        constraints = scenario.get("constraints")
        if not isinstance(constraints, dict):
            errors.append(f"{where}.scenario.constraints must be an object")
        else:
            floor = constraints.get("quality_floor")
            if not oc.is_number(floor):
                errors.append(
                    f"{where}.scenario.constraints.quality_floor must be a number"
                )
            else:
                quality_floor = float(floor)
            if not str(constraints.get("safety_envelope") or "").strip():
                errors.append(
                    f"{where}.scenario.constraints.safety_envelope must be stated"
                )

    result = record.get("result")
    if not isinstance(result, dict):
        return errors + [f"{where}.result must be an object"]

    candidates = result.get("candidates")
    if not isinstance(candidates, list) or len(candidates) < 2:
        return errors + [
            f"{where}.result.candidates must list at least two measured candidates"
        ]

    # The flag that tells a joule corpus from a second corpus. Readers,
    # MANIFEST.json and the "no theoretical energy" rule all lean on it, so it
    # has to follow from the quantity rather than be asserted alongside it.
    corpus_quantity = result.get("cost_quantity")
    cost_is_energy = result.get("cost_is_energy")
    if corpus_quantity not in oc.QUANTITY_UNITS:
        errors.append(f"{where}.result.cost_quantity must be a registered quantity")
    if not isinstance(cost_is_energy, bool):
        errors.append(f"{where}.result.cost_is_energy must be a boolean")
    elif cost_is_energy != (corpus_quantity in oc.ENERGY_QUANTITIES):
        errors.append(
            f"{where}.result.cost_is_energy is {cost_is_energy} but cost_quantity "
            f"is {corpus_quantity!r} — the flag must follow the quantity"
        )

    # Keyed by a tuple, not a joined string, so a candidate id containing the
    # separator cannot be made to collide with another candidate's reading.
    measured_costs: dict[tuple[str, str], tuple[float, str]] = {}
    measurements = result.get("measurements")
    measurements = measurements if isinstance(measurements, list) else []
    for item in measurements:
        if not isinstance(item, dict):
            continue
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
            measured_costs.setdefault((candidate_id, quantity), (item["value"], meter))

    for index, candidate in enumerate(candidates):
        spot = f"{where}.result.candidates[{index}]"
        if not isinstance(candidate, dict):
            errors.append(f"{spot} must be an object")
            continue
        candidate_id = candidate.get("id")
        if not isinstance(candidate_id, str) or not candidate_id:
            errors.append(f"{spot}.id must be a non-empty string")
            continue
        if not isinstance(candidate.get("safety_ok"), bool):
            errors.append(f"{spot}.safety_ok must be a boolean")
        if not oc.is_number(candidate.get("task_quality")):
            errors.append(f"{spot}.task_quality must be a number")
        quantity = candidate.get("cost_quantity")
        if quantity not in oc.QUANTITY_UNITS:
            errors.append(f"{spot}.cost_quantity must be a registered quantity")
            continue
        if corpus_quantity in oc.QUANTITY_UNITS and quantity != corpus_quantity:
            errors.append(
                f"{spot}.cost_quantity is {quantity!r} but the record is "
                f"denominated in {corpus_quantity!r} — costs must be comparable"
            )
        if not oc.is_number(candidate.get("cost_value")):
            errors.append(f"{spot}.cost_value must be a number")
            continue
        candidate_meter = candidate.get("cost_meter")
        if not isinstance(candidate_meter, str) or not candidate_meter:
            errors.append(f"{spot}.cost_meter must be a non-empty string")
            continue
        oracle_name = record.get("oracle", {}).get("name") if isinstance(record.get("oracle"), dict) else None
        selected_meter = result.get("meter_probe", {}).get("selected") if isinstance(result.get("meter_probe"), dict) else None
        if candidate_meter != oracle_name:
            errors.append(
                f"{spot}.cost_meter is {candidate_meter!r} but oracle.name is {oracle_name!r}"
            )
        if candidate_meter != selected_meter:
            errors.append(
                f"{spot}.cost_meter is {candidate_meter!r} but meter_probe.selected is {selected_meter!r}"
            )
        key = (candidate_id, quantity)
        if key not in measured_costs:
            errors.append(
                f"{spot}: UNMEASURED_COST — no oracle measurement of {quantity} "
                f"for candidate {candidate_id!r}"
            )
        else:
            measured_value, measured_meter = measured_costs[key]
            if abs(measured_value - float(candidate["cost_value"])) > 1e-12:
                errors.append(
                    f"{spot}.cost_value disagrees with the oracle measurement "
                    f"({candidate['cost_value']} vs {measured_value})"
                )
            if measured_meter != candidate_meter:
                errors.append(
                    f"{spot}.cost_meter is {candidate_meter!r} but the measurement meter is {measured_meter!r}"
                )

    status = result.get("status")
    preference = result.get("preference")
    if status == oc.RESULT_ABSTAINED:
        if preference is not None:
            errors.append(
                f"{where}.result: an abstained result must not carry a preference"
            )
        return errors
    if not isinstance(preference, dict):
        return errors + [
            f"{where}.result.preference must be an object (or the result must abstain)"
        ]
    if preference.get("decision_rule") != DECISION_RULE:
        errors.append(f"{where}.result.preference.decision_rule must be {DECISION_RULE!r}")
    by_id = {
        candidate["id"]: candidate
        for candidate in candidates
        if isinstance(candidate, dict) and isinstance(candidate.get("id"), str)
    }
    preferred_id = preference.get("preferred")
    preferred = by_id.get(preferred_id)
    if preferred is None:
        return errors + [
            f"{where}.result.preference.preferred must name a measured candidate"
        ]
    # The preference restates the winning candidate's cost. If that restatement
    # is free to drift, a record can advertise a cheap energy figure while the
    # candidate it points at was measured in seconds.
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
    if quality_floor is not None:
        cheaper_feasible = [
            candidate["id"]
            for candidate in candidates
            if isinstance(candidate, dict)
            and candidate.get("id") != preferred_id
            and candidate.get("safety_ok") is True
            and oc.is_number(candidate.get("task_quality"))
            and float(candidate["task_quality"]) >= quality_floor
            and oc.is_number(candidate.get("cost_value"))
            and float(candidate["cost_value"]) < float(preferred["cost_value"])
        ]
        if cheaper_feasible:
            errors.append(
                f"{where}.result.preference: NOT_MINIMAL_FEASIBLE_COST — "
                f"{sorted(cheaper_feasible)} are feasible and cheaper than "
                f"{preferred_id!r}"
            )
    return errors


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
