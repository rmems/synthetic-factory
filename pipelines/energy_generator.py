#!/usr/bin/env python3
"""Generator side of ``snn-energy-routing-preferences``.

Split out of ``energy_preferences.py`` verbatim: :func:`propose_scenarios`
builds the generator-owned scenario, :func:`choose_preference` applies the
decision rule to measured candidates, and :func:`build_records` measures every
candidate policy and assembles the record. Every name here is re-exported from
``energy_preferences`` so existing call sites resolve unchanged.
"""

from __future__ import annotations

import hashlib
import platform
import random
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

_PIPELINES = Path(__file__).resolve().parent
if str(_PIPELINES) not in sys.path:
    sys.path.insert(0, str(_PIPELINES))

from oracle_grounded import distill_contract as oc  # noqa: E402

if __package__:
    from .energy_contract import (
        ABSTAIN_NO_FEASIBLE,
        DECISION_RULE,
        DEFAULT_COARSE_STEPS,
        DEFAULT_FINE_STEPS,
        FAMILY,
        GENERATOR_NAME,
        GENERATOR_VERSION,
        MAX_ACTUATORS,
        MAX_REPLAY_STEPS,
        POLICY_SUITE_VERSION,
        PREFERENCE_OBJECTIVE,
        SAFETY_ENVELOPE,
        _genuine_int_at_least,
    )
    from .energy_meters import EnergyOracle, MeterReading, select_meter
    from .energy_task import (
        PolicyEvaluation,
        ProblemSpec,
        analytic_allocation,
        evaluate_allocation,
        grid_allocation,
        objective,
        unclipped_allocation,
    )
else:
    from energy_contract import (
        ABSTAIN_NO_FEASIBLE,
        DECISION_RULE,
        DEFAULT_COARSE_STEPS,
        DEFAULT_FINE_STEPS,
        FAMILY,
        GENERATOR_NAME,
        GENERATOR_VERSION,
        MAX_ACTUATORS,
        MAX_REPLAY_STEPS,
        POLICY_SUITE_VERSION,
        PREFERENCE_OBJECTIVE,
        SAFETY_ENVELOPE,
        _genuine_int_at_least,
    )
    from energy_meters import EnergyOracle, MeterReading, select_meter
    from energy_task import (
        PolicyEvaluation,
        ProblemSpec,
        analytic_allocation,
        evaluate_allocation,
        grid_allocation,
        objective,
        unclipped_allocation,
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

    n = MAX_ACTUATORS
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
    rng = random.Random(seed)  # nosec B311 - reproducible dataset generation
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
                    "objective": PREFERENCE_OBJECTIVE,
                },
            }
        )
    return proposals


def _policy_workloads(
    problem: ProblemSpec, protocol: MeterProtocol
) -> dict[str, Callable[[], list[float]]]:
    demand, weights, caps = problem.demand, problem.weights, problem.caps
    return {
        "exhaustive_grid": lambda: grid_allocation(
            demand, weights, caps, protocol.fine_steps
        ),
        "analytic_kkt": lambda: analytic_allocation(demand, weights, caps),
        "coarse_grid": lambda: grid_allocation(
            demand, weights, caps, protocol.coarse_steps
        ),
        "unclipped_proportional": lambda: unclipped_allocation(demand, weights),
    }


def _cheaper_rejected(
    candidate: dict[str, Any], preferred: dict[str, Any]
) -> bool:
    """Measured cheaper than the winner but ruled out by the constraints."""

    if candidate["id"] == preferred["id"]:
        return False
    if not oc.is_number(candidate.get("cost_value")):
        return False
    return candidate["cost_value"] < preferred["cost_value"]


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
        if _cheaper_rejected(candidate, preferred)
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


@dataclass(frozen=True)
class MeterProtocol:
    """The repeat/warmup protocol and solver grids a measurement binds to."""

    repeats: int = 5
    warmup: int = 1
    fine_steps: int = DEFAULT_FINE_STEPS
    coarse_steps: int = DEFAULT_COARSE_STEPS


@dataclass(frozen=True)
class MeterSpec(MeterProtocol):
    """The meter choice, probe, protocol and record id prefix of a batch."""

    meter: EnergyOracle | None = None
    meter_probe: dict[str, Any] | None = None
    id_prefix: str = "ep"


def workload_key(
    policy_id: str,
    scenario: dict[str, Any],
    protocol: MeterProtocol = MeterProtocol(),
) -> str:
    """Stable key identifying one policy running one workload configuration.

    A recorded measurement is only valid for the workload it was taken over,
    so the key binds the policy to the scenario state *and* to the solver
    parameters that shape the executed search and the repeat/warmup protocol. Without the solver binding, a
    recording taken at one grid resolution replays cleanly against another:
    the grid policy runs a different allocation search while the old energy
    reading is attached to it, which can silently change the preference.
    """

    _check_run_knobs(protocol)
    state = scenario.get("state") if isinstance(scenario, dict) else None
    payload = {
        "state": state,
        "policy_suite": POLICY_SUITE_VERSION,
        "measurement_protocol": {
            "repeats": protocol.repeats,
            "warmup": protocol.warmup,
        },
        "solver": {
            "fine_steps": int(protocol.fine_steps),
            "coarse_steps": int(protocol.coarse_steps),
        },
    }
    digest = hashlib.sha256(oc.canonical_json(payload).encode("utf-8")).hexdigest()
    return f"{policy_id}@{digest[:16]}"


def _read_cost(
    run: _MeterRun,
    workload: Callable[[], Any],
    policy_id: str,
    scenario: dict[str, Any],
) -> MeterReading:
    """Take a live measurement, or replay one a real metered run recorded.

    A replay meter supplies the *cost* only. Task quality and safety are still
    evaluated by executing the policy here, which is sound because the task is
    deterministic: the same policy on the same state produces the same
    allocation on any host. Only the cost needs a meter that was actually
    attached to the hardware.
    """

    lookup = getattr(run.meter, "lookup", None)
    if callable(lookup):
        return lookup(workload_key(policy_id, scenario, run.protocol))
    return run.meter.measure(
        workload, repeats=run.protocol.repeats, warmup=run.protocol.warmup
    )


@dataclass(frozen=True)
class _MeterRun:
    """The meter, probe and protocol one measured batch runs with."""

    meter: EnergyOracle
    probe: dict[str, Any]
    protocol: MeterProtocol




# name -> the lowest integer the knob may take. The oracle configuration is
# an audit of the execution: `warmup=-5` was silently normalised to zero by
# the live meters while the record still said -5, and fractional or zero
# grid settings fail later inside `range()` or the grid division — either
# way the recorded configuration would not describe the run that happened.
_RUN_KNOB_FLOORS = (
    ("repeats", 1),
    ("warmup", 0),
    ("fine_steps", 1),
    ("coarse_steps", 1),
)


_STEP_CEILING_KNOBS = ("fine_steps", "coarse_steps")


def _check_knob_floor(protocol: MeterProtocol, name: str, floor: int) -> None:
    if not _genuine_int_at_least(getattr(protocol, name), floor):
        raise oc.ContractError(
            f"{name} must be an integer >= {floor}, got "
            f"{getattr(protocol, name)!r}; the recorded oracle "
            "configuration must describe the execution that actually "
            "happened"
        )


def _check_step_ceiling(protocol: MeterProtocol, name: str) -> None:
    if getattr(protocol, name) > MAX_REPLAY_STEPS:
        # The family's own validator declines to replay grids above this
        # ceiling, so a run built beyond it would measure successfully and
        # still be rejected on validation — refuse it before executing.
        raise oc.ContractError(
            f"{name} must be an integer <= {MAX_REPLAY_STEPS}, got "
            f"{getattr(protocol, name)!r}; the validator cannot replay a "
            "grid larger than that"
        )


def _check_run_knobs(protocol: MeterProtocol) -> None:
    """Refuse measurement-run knobs the recorded audit could not describe."""

    for name, floor in _RUN_KNOB_FLOORS:
        _check_knob_floor(protocol, name, floor)
    for name in _STEP_CEILING_KNOBS:
        _check_step_ceiling(protocol, name)


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
        oc.OracleIdentity(
            meter.name,
            oracle_type="recorded_measurement" if replayed else "measured_execution",
            implementation=meter.implementation,
            version=meter.version,
            authority=oc.AUTHORITY_AUTHORITATIVE,
        ),
        oc.OracleRun(
            configuration={
                "repeats": run.protocol.repeats,
                "warmup": run.protocol.warmup,
                "fine_steps": run.protocol.fine_steps,
                "coarse_steps": run.protocol.coarse_steps,
                "meter_probe": run.probe,
            },
            fingerprint=meter.fingerprint(),
        ),
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
    scenario: dict[str, Any],
    problem: ProblemSpec,
    task: tuple[str, Callable[[], Any]],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """One executed policy's measurements and its candidate summary."""

    policy_id, workload = task
    allocation = workload()
    evaluation = evaluate_allocation(
        None if allocation is None else list(allocation), problem
    )
    reading = _read_cost(run, workload, policy_id, scenario)
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
    problem = ProblemSpec(
        demand=demand,
        weights=weights,
        caps=caps,
        optimum=optimum,
        quality_floor=quality_floor,
    )

    workloads = _policy_workloads(problem, run.protocol)
    measurements: list[dict[str, Any]] = []
    candidates: list[dict[str, Any]] = []
    for policy_id, workload in sorted(workloads.items()):
        policy_measurements, candidate = _measure_candidate(
            run, scenario, problem, (policy_id, workload)
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
    seed: int, count: int, spec: MeterSpec = MeterSpec()
) -> list[dict[str, Any]]:
    """Execute every candidate policy, meter it, and build measured records."""

    _check_run_knobs(spec)
    meter, probe = _resolve_meter(spec.meter, spec.meter_probe)
    run = _MeterRun(meter=meter, probe=probe, protocol=spec)
    generator = oc.new_generator(
        oc.GeneratorIdentity(GENERATOR_NAME, version=GENERATOR_VERSION, kind="programmatic"),
        seed=seed,
    )
    oracle = _oracle_block(run)
    records: list[dict[str, Any]] = []
    for proposal in propose_scenarios(seed, count):
        scenario = proposal["scenario"]
        records.append(
            oc.build_record(
                identity=oc.RecordIdentity(
                    f"{spec.id_prefix}-{seed}-{proposal['index']:04d}", FAMILY
                ),
                proposal=oc.Proposal(generator=generator, scenario=scenario),
                verdict=oc.Verdict(oracle=oracle, result=_scenario_result(run, scenario)),
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
