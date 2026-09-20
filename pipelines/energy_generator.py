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
import json
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
        ABSTAIN_NO_MEASUREMENT,
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
        SUPPORTED_COST_QUANTITIES,
        _genuine_int_at_least,
    )
    from .energy_meters import EnergyOracle, MeterReading, select_meter
    from .energy_task import (
        PolicyEvaluation,
        analytic_allocation,
        evaluate_allocation,
        grid_allocation,
        objective,
        unclipped_allocation,
    )
else:
    from energy_contract import (
        ABSTAIN_NO_FEASIBLE,
        ABSTAIN_NO_MEASUREMENT,
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
        SUPPORTED_COST_QUANTITIES,
        _genuine_int_at_least,
    )
    from energy_meters import EnergyOracle, MeterReading, select_meter
    from energy_task import (
        PolicyEvaluation,
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
    repeats: int = 5,
    warmup: int = 1,
    fine_steps: int = DEFAULT_FINE_STEPS,
    coarse_steps: int = DEFAULT_COARSE_STEPS,
) -> str:
    """Stable key identifying one policy running one workload configuration.

    A recorded measurement is only valid for the workload it was taken over,
    so the key binds the policy to the scenario state *and* to the solver
    parameters that shape the executed search and the repeat/warmup protocol. Without the solver binding, a
    recording taken at one grid resolution replays cleanly against another:
    the grid policy runs a different allocation search while the old energy
    reading is attached to it, which can silently change the preference.
    """

    _check_run_knobs({
        "repeats": repeats, "warmup": warmup,
        "fine_steps": fine_steps, "coarse_steps": coarse_steps,
    })
    state = scenario.get("state") if isinstance(scenario, dict) else None
    payload = {
        "state": state,
        "policy_suite": POLICY_SUITE_VERSION,
        "measurement_protocol": {"repeats": repeats, "warmup": warmup},
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
                repeats=repeats,
                warmup=warmup,
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


def _check_run_knobs(knobs: dict[str, Any]) -> None:
    """Refuse measurement-run knobs the recorded audit could not describe."""

    for name, floor in _RUN_KNOB_FLOORS:
        if not _genuine_int_at_least(knobs[name], floor):
            raise oc.ContractError(
                f"{name} must be an integer >= {floor}, got {knobs[name]!r}; "
                "the recorded oracle configuration must describe the "
                "execution that actually happened"
            )
    for name in ("fine_steps", "coarse_steps"):
        if knobs[name] > MAX_REPLAY_STEPS:
            # The family's own validator declines to replay grids above this
            # ceiling, so a run built beyond it would measure successfully and
            # still be rejected on validation — refuse it before executing.
            raise oc.ContractError(
                f"{name} must be an integer <= {MAX_REPLAY_STEPS}, got "
                f"{knobs[name]!r}; the validator cannot replay a grid larger "
                "than that"
            )


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
                "repeats": run.repeats,
                "warmup": run.warmup,
                "fine_steps": run.fine_steps,
                "coarse_steps": run.coarse_steps,
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

    _check_run_knobs(
        {
            "repeats": repeats,
            "warmup": warmup,
            "fine_steps": fine_steps,
            "coarse_steps": coarse_steps,
        }
    )
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
                    f"{id_prefix}-{seed}-{proposal['index']:04d}", FAMILY
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
