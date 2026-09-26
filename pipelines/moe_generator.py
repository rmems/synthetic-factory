#!/usr/bin/env python3
"""Generator side of ``moe-router-distillation-trajectories``.

Split out of ``moe_router.py`` verbatim: :func:`propose_contexts` builds the
generator-owned context corpus and :func:`build_records` runs the oracle and
assembles the record. Every name here is re-exported from ``moe_router`` so
existing call sites resolve unchanged.
"""

from __future__ import annotations

import hashlib
import random
import sys
from pathlib import Path
from typing import Any

_PIPELINES = Path(__file__).resolve().parent
if str(_PIPELINES) not in sys.path:
    sys.path.insert(0, str(_PIPELINES))

from oracle_grounded import distill_contract as oc  # noqa: E402


if __package__:
    from .moe_featurizer import (
        COMPACT_DIM,
        CONTEXT_TEMPLATES,
        FEATURE_DIM,
        FEATURIZER_ID,
        FAMILY,
        GENERATOR_NAME,
        GENERATOR_VERSION,
        TEMPLATE_ADJECTIVES,
        TEMPLATE_NOUNS,
        compact_view,
        featurize,
    )
    from .moe_layers import RouterObservation
    from .moe_oracles import ReferenceMoERouter, RouterOracle
else:
    from moe_featurizer import (
        COMPACT_DIM,
        CONTEXT_TEMPLATES,
        FEATURE_DIM,
        FEATURIZER_ID,
        FAMILY,
        GENERATOR_NAME,
        GENERATOR_VERSION,
        TEMPLATE_ADJECTIVES,
        TEMPLATE_NOUNS,
        compact_view,
        featurize,
    )
    from moe_layers import RouterObservation
    from moe_oracles import ReferenceMoERouter, RouterOracle



def propose_contexts(
    seed: int, count: int, *, feature_dim: int = FEATURE_DIM
) -> list[dict[str, Any]]:
    """Generator side: diverse contexts and their compact student inputs.

    ``feature_dim`` is the oracle's configured gate width: the compact input
    is a view of the features the router actually gated on, so a non-default
    ``ReferenceMoERouter(shape=GateShape(dim=...))`` must produce a compact input over that
    width rather than the 48-dimensional default.
    """

    if count < 1:
        raise oc.ContractError("count must be >= 1")
    rng = random.Random(seed)  # nosec B311 - reproducible context generation
    proposals: list[dict[str, Any]] = []
    for index in range(count):
        domain, template = CONTEXT_TEMPLATES[index % len(CONTEXT_TEMPLATES)]
        text = template.format(
            noun=rng.choice(TEMPLATE_NOUNS),  # NOSONAR - seeded data generation, not security
            adj=rng.choice(TEMPLATE_ADJECTIVES),  # NOSONAR - seeded data generation
            digit=rng.randrange(10),  # NOSONAR - seeded data generation
        )
        features = featurize(text, feature_dim)
        compact_dim = min(feature_dim, COMPACT_DIM)
        proposals.append(
            {
                "index": index,
                "scenario": {
                    "domain": domain,
                    "context": text,
                    "context_sha256": hashlib.sha256(
                        text.encode("utf-8")
                    ).hexdigest(),
                    "compact_input": {
                        "featurizer": FEATURIZER_ID,
                        "feature_dim": feature_dim,
                        "compact_dim": compact_dim,
                        "view": "leading components + tail mean/energy/max/min",
                        "features": compact_view(features, compact_dim),
                    },
                },
            }
        )
    return proposals


def _routing_result(
    observation: RouterObservation, engine: RouterOracle, oracle_block: dict[str, Any]
) -> dict[str, Any]:
    """The oracle-owned result block for one routed context."""

    last = observation.layers[-1]
    measurements = [
        oc.new_measurement(
            "top1_top2_margin", last.top1_top2_margin, engine.name,
            detail={"layer": last.layer},
        ),
        oc.new_measurement(
            "routing_entropy", last.routing_entropy, engine.name,
            detail={"layer": last.layer},
        ),
        oc.new_measurement(
            "expert_agreement", observation.expert_agreement, engine.name,
            detail={"across_layers": len(observation.layers)},
        ),
    ]
    return oc.new_result(
        measurements=measurements,
        routing=observation.as_dict(),
        top1_expert=observation.top1_expert,
        is_llm_teacher=bool(engine.is_llm_teacher),
        teacher_grounded=bool(
            engine.is_llm_teacher
            and oracle_block["authority"] == oc.AUTHORITY_AUTHORITATIVE
        ),
    )


def build_records(
    seed: int,
    count: int,
    *,
    oracle: RouterOracle | None = None,
    id_prefix: str = "mr",
) -> list[dict[str, Any]]:
    """Route every proposed context through a router oracle that actually ran."""

    engine = oracle or ReferenceMoERouter()
    ok, detail = engine.available()
    if not ok:
        raise oc.OracleUnavailable(engine.name, detail)
    generator = oc.new_generator(
        oc.GeneratorIdentity(GENERATOR_NAME, version=GENERATOR_VERSION, kind="programmatic"),
        seed=seed,
    )
    # The oracle block is built after the first routing call: a real teacher's
    # fingerprint (checkpoint hash, dtype, expert counts) only exists once the
    # model has actually loaded, and an unloaded fingerprint must not be faked.
    oracle_block: dict[str, Any] | None = None
    # The compact student input is a view of the features the router gated
    # on, so it is derived at the oracle's configured width.
    feature_dim = engine.dim if isinstance(engine, ReferenceMoERouter) else FEATURE_DIM
    records: list[dict[str, Any]] = []
    for proposal in propose_contexts(seed, count, feature_dim=feature_dim):
        scenario = proposal["scenario"]
        observation = engine.route(scenario["context"])
        if oracle_block is None:
            oracle_block = engine.oracle_block()
        records.append(
            oc.build_record(
                identity=oc.RecordIdentity(
                    f"{id_prefix}-{seed}-{proposal['index']:04d}", FAMILY
                ),
                proposal=oc.Proposal(generator=generator, scenario=scenario),
                verdict=oc.Verdict(
                    oracle=oracle_block,
                    result=_routing_result(observation, engine, oracle_block),
                ),
                provenance=oc.new_provenance("pipelines/moe_router.py"),
            )
        )
    return records
