#!/usr/bin/env python3
"""``neuromorphic-fault-recovery`` generator + deterministic relay oracle.

Issue #78. A generator proposes a disturbance against a bounded relay/reflex
system and may attach a *prediction*. The label comes from actually stepping
the disturbance through a deterministic simulator, never from the prediction.

The simulator is the oracle. Parent epic #76 explicitly admits a deterministic
simulator as ground truth, so records from ``RelayReflexSimulator`` carry
``oracle.authority = "authoritative"``. Hardware replay would slot in behind
the same :class:`FaultOracle` boundary; it is not available here.

Disturbance vocabulary and outcome vocabulary are the ones written in #78.

Relationship to ``oracle_grounded.fault_*`` (F1 of #191, landed in #193): main
re-implemented the *generator and oracle* half of this module across
``fault_vocabulary`` / ``fault_config`` / ``fault_scenario`` / ``fault_simulator``
/ ``fault_oracle``, on the shared ``rng.DrawStream`` and with the owner's D7
rulings applied. That library is not a drop-in replacement for this module and
does not supersede it yet: it carries no ``check_family`` and no CLI, and its
records differ from this one's for the same seed (a different draw stream, a
different ``oracle.implementation``, and the corrected ``events_dropped``
degradation sign). Re-pointing this family at it is a record-level migration --
new fixture bytes and a rewritten identity pin in
``_check_oracle_implementation_identity`` -- and is tracked separately, not done
as part of a merge.

CLI::

    python3 pipelines/fault_recovery.py generate --count 12 --seed 20260823 \
        --output <new.jsonl>
    python3 pipelines/fault_recovery.py describe --json


This module is the stable entry point and compatibility facade. The
implementation is split into responsibility-named siblings:

* ``fault_simulator.py`` -- disturbance vocabulary, the ``FaultOracle``
  boundary, and ``RelayReflexSimulator``.
* ``fault_records.py`` -- scenario proposals and record assembly.
* ``fault_check.py`` -- the ``check_family`` record validator.

Every public name any of them defines is re-exported here, so existing
``import fault_recovery`` call sites resolve unchanged.
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
from oracle_grounded import envelope  # noqa: E402,F401
from oracle_grounded import fault_vocabulary  # noqa: E402,F401

if __package__:
    from . import fault_check as _fault_check
    from . import fault_records as _fault_records
    from . import fault_simulator as _fault_simulator
    from . import fault_types as _fault_types
    from .fault_records import build_records
    from .fault_types import describe
else:
    import fault_check as _fault_check
    import fault_records as _fault_records
    import fault_simulator as _fault_simulator
    import fault_types as _fault_types
    from fault_records import build_records
    from fault_types import describe


def _reexport(module: Any, names: str) -> None:
    globals().update({name: getattr(module, name) for name in names.split()})


_reexport(
    _fault_types,
    """
    DEFAULT_SYSTEM DISTURBANCES FAMILY GENERATOR_NAME GENERATOR_VERSION
    MALFORMED_INTEGRITY_KINDS MALFORMED_KINDS ORACLE_IMPLEMENTATION ORACLE_NAME
    ORACLE_VERSION OUTCOME_LABELS OUTCOME_PRECEDENCE OUTCOMES PARAMETER_SPEC
    FaultOracle FaultResult describe
    """,
)
_reexport(_fault_simulator, "RelayReflexSimulator")
_reexport(_fault_records, "build_records propose_scenarios")
_reexport(_fault_check, "check_family")

del _reexport, _fault_check, _fault_records, _fault_simulator, _fault_types


def main(argv: list[str] | None = None) -> int:  # NOSONAR - successful commands return 0
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)

    generate = sub.add_parser("generate", help="propose disturbances and run the oracle")
    generate.add_argument("--seed", type=int, default=20260823)
    generate.add_argument("--count", type=int, default=9)
    generate.add_argument("--output", help="destination JSONL (must not exist)")

    sub.add_parser("describe", help="print the family contract")

    args = parser.parse_args(argv)
    if args.command == "describe":
        print(json.dumps(describe(), indent=2, sort_keys=True))
        return 0

    records = build_records(args.seed, args.count)
    if args.output:
        written = oc.write_jsonl(args.output, records)
        print(json.dumps({"written": written, "output": args.output}, indent=2))
    else:
        for record in records:
            print(oc.canonical_json(record))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
