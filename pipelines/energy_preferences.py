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


This module is the stable entry point and compatibility facade. The
implementation is split into responsibility-named siblings:

* ``energy_contract.py`` -- family constants, decision rule, label policy.
* ``energy_meters.py`` -- the ``EnergyOracle`` boundary and its meters.
* ``energy_task.py`` -- the capped-allocation task and its policies.
* ``energy_generator.py`` -- scenario proposals and record assembly.
* ``energy_check.py`` -- the ``check_family`` record validator.

Every public name any of them defines is re-exported here, so existing
``import energy_preferences`` call sites resolve unchanged.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

_PIPELINES = Path(__file__).resolve().parent
if str(_PIPELINES) not in sys.path:
    sys.path.insert(0, str(_PIPELINES))

from oracle_grounded import distill_contract as oc  # noqa: E402

if __package__:
    from . import energy_check as _energy_check
    from . import energy_contract as _energy_contract
    from . import energy_generator as _energy_generator
    from . import energy_meters as _energy_meters
    from . import energy_task as _energy_task
    from .energy_generator import MeterSpec, build_records
    from .energy_meters import meters_report
else:
    import energy_check as _energy_check
    import energy_contract as _energy_contract
    import energy_generator as _energy_generator
    import energy_meters as _energy_meters
    import energy_task as _energy_task
    from energy_generator import MeterSpec, build_records
    from energy_meters import meters_report


def _reexport(module: Any, names: str) -> None:
    globals().update({name: getattr(module, name) for name in names.split()})


_reexport(
    _energy_contract,
    """
    ABSTAIN_NO_FEASIBLE ABSTAIN_NO_MEASUREMENT DECISION_RULE DEFAULT_COARSE_STEPS
    DEFAULT_FINE_STEPS FAMILY GENERATOR_NAME GENERATOR_VERSION MAX_ACTUATORS
    MAX_REPLAY_STEPS ORACLE_LABEL_POLICY POLICY_SUITE_VERSION PREFERENCE_OBJECTIVE
    QUALITY_TOLERANCE SAFETY_ENVELOPE SUPPORTED_COST_QUANTITIES
    """,
)
_reexport(
    _energy_meters,
    """
    EnergyOracle MeterReading ProcessResourceMeter RaplEnergyMeter
    RecordedEnergyMeter meters_report select_meter resource
    _context_switches _peak_rss_kb _reset_peak_rss
    """,
)
_reexport(
    _energy_task,
    """
    PolicyEvaluation ProblemSpec analytic_allocation evaluate_allocation
    grid_allocation objective unclipped_allocation
    """,
)
_reexport(
    _energy_generator,
    """
    MeterProtocol MeterSpec POLICY_DESCRIPTIONS build_records choose_preference
    propose_scenarios workload_key
    _check_run_knobs _feasible_candidates _policy_workloads
    """,
)
_reexport(_energy_check, "check_family")

del (
    _reexport,
    _energy_check,
    _energy_contract,
    _energy_generator,
    _energy_meters,
    _energy_task,
)


def main(argv: list[str] | None = None) -> int:  # NOSONAR - successful commands return 0
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

    records = build_records(
        args.seed, args.count, MeterSpec(repeats=args.repeats)
    )
    if args.output:
        written = oc.write_jsonl(args.output, records)
        print(json.dumps({"written": written, "output": args.output}, indent=2))
    else:
        for record in records:
            print(oc.canonical_json(record))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
