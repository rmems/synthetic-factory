#!/usr/bin/env python3
"""``moe-router-distillation-trajectories`` generator + router-oracle boundary.

Issue #78. A generator supplies diverse text / code / task contexts. The
routing label must come from a router that actually ran. Nothing in this module
lets a generator guess what another model's router would have chosen.

Three oracles sit behind one :class:`RouterOracle` boundary:

``TransformersMoERouter``
    The real teacher. Runs a Hugging Face MoE checkpoint with
    ``output_router_logits=True`` and reads the per-layer gate logits.
    **Not exercised in this environment** — see ``available()``; the local
    ``transformers`` install is broken (``ModuleNotFoundError: regex``) and no
    MoE checkpoint is present. Its records are ``authoritative`` and
    ``is_llm_teacher = True``.
``RecordedTeacherRouter``
    Replays a recording produced by a real teacher run, keyed by the SHA-256 of
    the context. Fails closed on an unknown key.
``ReferenceMoERouter``
    A deterministic, seeded, pure-Python top-k gate. It is a *real* router
    computation — softmax over an actual linear gate — but it is not an LLM.
    It exists to prove the pipeline shape end to end. Its records are
    ``reference_only``, are excluded by ``distill_contract.curation_eligible``,
    and must never be presented as teacher-grounded routing data.

Compact targets captured per context: top-k experts, router logits where the
oracle exposes them, top-1/top-2 margin, routing entropy, expert agreement.

CLI::

    python3 pipelines/moe_router.py generate --count 24 --seed 20260823 \
        --output <new.jsonl>
    python3 pipelines/moe_router.py oracles --json


This module is the stable entry point and compatibility facade. The
implementation is split into responsibility-named siblings:

* ``moe_featurizer.py`` -- featurisation, identity constants, checkpoint rules.
* ``moe_layers.py`` -- routing-layer shapes and per-layer consistency checks.
* ``moe_oracles.py`` -- the ``RouterOracle`` boundary and its implementations.
* ``moe_generator.py`` -- context proposals and record assembly.
* ``moe_check.py`` -- the ``check_family`` record validator.

Every public name any of them defines is re-exported here, so existing
``import moe_router`` call sites resolve unchanged.
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
    from . import moe_check as _moe_check
    from . import moe_featurizer as _moe_featurizer
    from . import moe_generator as _moe_generator
    from . import moe_layer_fields as _moe_layer_fields
    from . import moe_layers as _moe_layers
    from . import moe_oracles as _moe_oracles
    from .moe_generator import build_records
    from .moe_oracles import (
        RecordedTeacherRouter,
        ReferenceMoERouter,
        RouterOracle,
        oracles_report,
    )
else:
    import moe_check as _moe_check
    import moe_featurizer as _moe_featurizer
    import moe_generator as _moe_generator
    import moe_layer_fields as _moe_layer_fields
    import moe_layers as _moe_layers
    import moe_oracles as _moe_oracles
    from moe_generator import build_records
    from moe_oracles import (
        RecordedTeacherRouter,
        ReferenceMoERouter,
        RouterOracle,
        oracles_report,
    )


def _reexport(module: Any, names: str) -> None:
    globals().update({name: getattr(module, name) for name in names.split()})


_reexport(
    _moe_featurizer,
    """
    COMMIT_SHA_RE COMPACT_DIM COMPACT_SUMMARY_STATS CONTEXT_TEMPLATES FEATURE_DIM
    FEATURIZER_ID FAMILY GENERATOR_NAME GENERATOR_VERSION MAX_RECOMPUTE_DIM
    NON_TEACHER_IMPLEMENTATIONS NON_TEACHER_ORACLE_NAMES NON_TEACHER_ORACLE_TYPES
    ORACLE_LABEL_POLICY RECOMPUTE_TOLERANCE SEALED_HUB_MOE_CARDS
    SEALED_HUB_MOE_REVISIONS TEACHER_ORACLE_TYPES TEMPLATE_ADJECTIVES
    TEMPLATE_NOUNS TRANSFORMERS_MOE_IMPLEMENTATION compact_view entropy_nats
    featurize resolve_checkpoint softmax
    """,
)
_reexport(_moe_layers, "LayerRouting RouterObservation")
_reexport(_moe_layer_fields, "_check_layer_logits")
_reexport(
    _moe_oracles,
    """
    GateShape RecordedTeacherRouter ReferenceMoERouter RouterOracle
    TransformersMoERouter oracles_report
    """,
)
_reexport(_moe_generator, "build_records propose_contexts")
_reexport(_moe_check, "check_family")

del (
    _reexport,
    _moe_check,
    _moe_featurizer,
    _moe_generator,
    _moe_layer_fields,
    _moe_layers,
    _moe_oracles,
)


def main(argv: list[str] | None = None) -> int:  # NOSONAR - successful commands return 0
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)

    generate = sub.add_parser("generate", help="route generated contexts")
    generate.add_argument("--seed", type=int, default=20260823)
    generate.add_argument("--count", type=int, default=20)
    generate.add_argument("--output", help="destination JSONL (must not exist)")
    generate.add_argument(
        "--recording", help="replay a real teacher recording instead of the reference"
    )

    oracles = sub.add_parser("oracles", help="probe router oracle availability")
    oracles.add_argument("--json", action="store_true")

    args = parser.parse_args(argv)
    if args.command == "oracles":
        print(json.dumps(oracles_report(), indent=2, sort_keys=True))
        return 0

    engine: RouterOracle
    if args.recording:
        engine = RecordedTeacherRouter.from_path(args.recording)
    else:
        engine = ReferenceMoERouter()
    records = build_records(args.seed, args.count, oracle=engine)
    if args.output:
        written = oc.write_jsonl(args.output, records)
        print(json.dumps({"written": written, "output": args.output}, indent=2))
    else:
        for record in records:
            print(oc.canonical_json(record))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
