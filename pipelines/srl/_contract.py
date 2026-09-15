#!/usr/bin/env python3
"""Pinned identity for the sparse-reward long-task family (prefix ``srl``).

Constants are AST-extracted from ``srl_r6110`` on ``origin/legacy-mill-lane``
(``experiments/srl_r6110_leftover3_mill.py``). This module is the only place
the family names the factory, generator, horizon, and banned keys.
"""

from __future__ import annotations

if __name__.startswith("pipelines."):
    from ..exact_json import dumps_exact_json
else:
    from exact_json import dumps_exact_json

FAMILY_PREFIX = "srl"
FACTORY = "sparse-reward-long-task-factory"
GENERATOR = "grok-4.6"
GEN = GENERATOR
N_STEPS = 32
SOURCE_MILL_ID = "srl_r6110"
SOURCE_ROUND = 6110
SOURCE_REF = "origin/legacy-mill-lane"
SOURCE_PATH = "experiments/srl_r6110_leftover3_mill.py"
NOVEL_COVERAGE = "42%"
BANNED = (
    "thought",
    "chain_of_thought",
    "scratch",
    "inner_monologue",
    "spike_events",
)
HOP = (
    "incident-response-oncall-factory",
    "eval-harness-trajectory-factory",
    "rag-retrieval-debug-factory",
    "git-ops-recovery-factory",
    "observability-debug-factory",
)
THEME_TOOLS = (
    "systemd-networkd",
    "chrony",
    "nft",
    "podman",
    "buildah",
    "skopeo",
    "cosign",
    "syft",
    "grype",
    "opa",
    "cilium",
    "linkerd",
    "vault",
    "age",
    "restic",
    "kopia",
)

__all__ = [
    "BANNED",
    "FACTORY",
    "FAMILY_PREFIX",
    "GEN",
    "GENERATOR",
    "HOP",
    "NOVEL_COVERAGE",
    "N_STEPS",
    "SOURCE_MILL_ID",
    "SOURCE_PATH",
    "SOURCE_REF",
    "SOURCE_ROUND",
    "SrlError",
    "THEME_TOOLS",
    "dumps_exact_json",
    "require_round",
]


class SrlError(ValueError):
    """Fail-closed refusal from the sparse-reward long-task family."""


def require_round(rnd: int) -> int:
    """Accept a positive integer round token. Booleans are not rounds."""

    if type(rnd) is not int or rnd < 1:
        raise SrlError(f"invalid_round: {rnd!r}")
    return rnd
