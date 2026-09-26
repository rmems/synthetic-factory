#!/usr/bin/env python3
"""Router oracle boundary for ``sparse-moe-router-routing``.

Split out of ``moe_oracles.py`` verbatim: :class:`RouterOracle`, the boundary
every routing oracle implements, and :func:`_summarise`, the modal top-1
aggregate that turns per-layer routing into an observation. Re-exported
through ``moe_oracles`` / ``moe_router`` so call sites resolve unchanged.
"""

from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path
from typing import Any

_PIPELINES = Path(__file__).resolve().parent
if str(_PIPELINES) not in sys.path:
    sys.path.insert(0, str(_PIPELINES))

from oracle_grounded import distill_contract as oc  # noqa: E402

if __package__:
    from .moe_layers import LayerRouting, RouterObservation
else:
    from moe_layers import LayerRouting, RouterObservation


class RouterOracle:
    """Boundary every routing oracle implements."""

    name = "abstract"
    version = "0"
    oracle_type = "reference_model_router"
    authority = oc.AUTHORITY_REFERENCE_ONLY
    implementation = "pipelines/moe_router.py:RouterOracle"
    is_llm_teacher = False

    def available(self) -> tuple[bool, str]:
        raise NotImplementedError

    def route(self, text: str) -> RouterObservation:
        raise NotImplementedError

    def fingerprint(self) -> dict[str, Any]:
        raise NotImplementedError

    def oracle_block(self) -> dict[str, Any]:
        return oc.new_oracle(
            oc.OracleIdentity(
                self.name,
                oracle_type=self.oracle_type,
                implementation=self.implementation,
                version=self.version,
                authority=self.authority,
            ),
            oc.OracleRun(
                configuration=self.configuration(),
                seed=getattr(self, "seed", None),
                fingerprint=self.fingerprint(),
            ),
        )

    def configuration(self) -> dict[str, Any]:
        return {}


def _summarise(layers: list[LayerRouting]) -> RouterObservation:
    tops = [layer.top_k_experts[0] for layer in layers]
    modal, count = Counter(tops).most_common(1)[0]
    return RouterObservation(
        layers=tuple(layers),
        top1_expert=modal,
        expert_agreement=round(count / len(tops), 6),
    )

