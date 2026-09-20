#!/usr/bin/env python3
"""Reference-recompute checks for ``moe-router-distillation-trajectories``.

Split out of ``moe_check.py`` verbatim: recompute the reference router's
layers from the recorded fingerprint and bind the recorded configuration to
the fingerprint pairs.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

_PIPELINES = Path(__file__).resolve().parent
if str(_PIPELINES) not in sys.path:
    sys.path.insert(0, str(_PIPELINES))

from oracle_grounded import distill_contract as oc  # noqa: E402
if __package__:
    from .moe_featurizer import (
        FEATURE_DIM,
        MAX_RECOMPUTE_DIM,
        _DEFAULT_REFERENCE_SEED,
    )
    from .moe_layers import (
        _declared_expert_count,
        _declared_layer_count,
        _declared_top_k,
        _recomputed_layer_mismatches,
    )
    from .moe_oracles import GateShape, ReferenceMoERouter
else:
    from moe_featurizer import (
        FEATURE_DIM,
        MAX_RECOMPUTE_DIM,
        _DEFAULT_REFERENCE_SEED,
    )
    from moe_layers import (
        _declared_expert_count,
        _declared_layer_count,
        _declared_top_k,
        _recomputed_layer_mismatches,
    )
    from moe_oracles import GateShape, ReferenceMoERouter


_CONFIGURATION_FINGERPRINT_PAIRS = (
    ("num_experts", "num_local_experts"),
    ("num_layers", "num_layers"),
    ("top_k", "num_experts_per_tok"),
)

def _check_configuration_binding(
    record: dict[str, Any], oracle: Any, fingerprint: Any, where: str
) -> list[str]:
    """The declared gate configuration must agree with its fingerprint."""

    if not isinstance(oracle, dict):
        return []
    configuration = oracle.get("configuration")
    if not isinstance(configuration, dict) or not isinstance(fingerprint, dict):
        return []
    errors: list[str] = []
    for configuration_key, fingerprint_key in _CONFIGURATION_FINGERPRINT_PAIRS:
        declared = configuration.get(configuration_key)
        fingerprinted = fingerprint.get(fingerprint_key)
        if declared is not None and fingerprinted is not None and declared != fingerprinted:
            errors.append(
                f"{where}.oracle.configuration.{configuration_key} is "
                f"{declared!r} but oracle.fingerprint.{fingerprint_key} is "
                f"{fingerprinted!r}"
            )
    feature_dim = configuration.get("feature_dim")
    scenario = record.get("scenario")
    compact = scenario.get("compact_input") if isinstance(scenario, dict) else None
    declared_dim = compact.get("feature_dim") if isinstance(compact, dict) else None
    if (
        isinstance(feature_dim, int)
        and not isinstance(feature_dim, bool)
        and declared_dim is not None
        and declared_dim != feature_dim
    ):
        errors.append(
            f"{where}.scenario.compact_input.feature_dim is {declared_dim!r} "
            f"but oracle.configuration.feature_dim is {feature_dim!r} — the "
            "compact input must be a view of the features the router gated on"
        )
    return errors

def _reference_seed(fingerprint: dict[str, Any]) -> int | None:
    revision = fingerprint.get("revision_or_checkpoint")
    if not (isinstance(revision, str) and revision.startswith("seed:")):
        return None
    try:
        return int(revision[5:])
    except ValueError:
        return None

def _check_reference_recompute(
    record: dict[str, Any], oracle: Any, fingerprint: Any, layers: list[Any], where: str
) -> list[str]:
    """Re-run the declared deterministic reference router and compare layers.

    Internal consistency checks cannot catch a record whose whole ``result``
    was copied from another row: only re-running the oracle over the recorded
    context pins the routing to this scenario. That is only possible for the
    known deterministic implementation — a teacher recording is intentionally
    not recomputable — so the check is scoped to it and fails closed when the
    declared dimensions or seed are missing.
    """

    if not isinstance(oracle, dict) or not isinstance(fingerprint, dict):
        return []
    if oracle.get("implementation") != ReferenceMoERouter.implementation:
        return []
    scenario = record.get("scenario")
    context = scenario.get("context") if isinstance(scenario, dict) else None
    if not isinstance(context, str):
        return []  # reported by the scenario context check; nothing to recompute
    engine, problems = _reference_engine(
        oracle.get("configuration"), fingerprint, where
    )
    if problems:
        return problems
    return _recomputed_routing_errors(engine, context, layers, where)

def _declared_int(configuration: dict[str, Any], key: str, default: int) -> int:
    """An integer the oracle configuration declares, or the reference default."""

    value = configuration.get(key)
    return value if isinstance(value, int) and not isinstance(value, bool) else default

def _reference_engine(
    configuration: Any, fingerprint: Any, where: str
) -> tuple[ReferenceMoERouter | None, list[str]]:
    """The declared reference gate re-instantiated, or why it cannot run.

    Dimensions the record does not declare fall back to the reference
    defaults — not as a trust decision but because recompute is itself the
    check: a record whose gate really ran at other dimensions mismatches
    layer-for-layer, and one that ran at the defaults reproduces cleanly.
    """

    declared = configuration if isinstance(configuration, dict) else {}
    dim = _declared_int(declared, "feature_dim", FEATURE_DIM)
    seed = _reference_seed(fingerprint)
    if seed is None:
        seed = _DEFAULT_REFERENCE_SEED
    num_experts = _declared_expert_count(fingerprint) or _declared_int(
        declared, "num_experts", 8
    )
    num_layers = _declared_layer_count(fingerprint) or _declared_int(
        declared, "num_layers", 4
    )
    top_k = _declared_top_k(fingerprint) or _declared_int(declared, "top_k", 2)
    in_bounds = all(
        0 < dimension <= MAX_RECOMPUTE_DIM
        for dimension in (dim, num_experts, num_layers)
    )
    if not in_bounds or top_k <= 0:
        # Recompute would allocate gates at whatever dimensions a forged
        # record declares; outside a bounded domain the routing cannot be
        # reproduced here — refused, not skipped.
        return None, [
            f"{where}.oracle: declared reference dimensions (feature_dim "
            f"{dim!r}, num_experts {num_experts!r}, num_layers "
            f"{num_layers!r}, top_k {top_k!r}) are outside the recomputable "
            f"domain [1, {MAX_RECOMPUTE_DIM}]; the routing cannot be verified"
        ]
    try:
        engine = ReferenceMoERouter(
            seed=seed,
            shape=GateShape(
                num_experts=num_experts,
                num_layers=num_layers,
                top_k=top_k,
                dim=dim,
            ),
        )
    except oc.ContractError as exc:
        return None, [
            f"{where}.oracle: declared reference configuration cannot run "
            f"({exc}); the recorded routing cannot be reproduced"
        ]
    return engine, []

def _recomputed_routing_errors(
    engine: ReferenceMoERouter, context: str, layers: list[Any], where: str
) -> list[str]:
    """Layer-for-layer mismatches between the record and the recomputed run."""

    observed = engine.route(context)
    if len(layers) != len(observed.layers):
        return [
            f"{where}.result.routing.layers has {len(layers)} layers but the "
            f"reference router computes {len(observed.layers)} for this context"
        ]
    errors: list[str] = []
    for index, (layer, actual) in enumerate(zip(layers, observed.layers)):
        spot = f"{where}.result.routing.layers[{index}]"
        if isinstance(layer, dict):
            errors += _recomputed_layer_mismatches(layer, actual, spot)
    if errors:
        errors.append(
            f"{where}.result: REFERENCE_RECOMPUTE_MISMATCH — the recorded "
            "routing does not match a recomputed run of the declared "
            "reference router"
        )
    return errors
