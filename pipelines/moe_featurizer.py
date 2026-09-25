#!/usr/bin/env python3
"""Context featurisation and identity constants for ``moe-router-distillation-trajectories``.

Split out of ``moe_router.py`` verbatim: the blake2b char-trigram featurizer,
the compact summary view, softmax/entropy, the sealed Hub MoE identity tables,
and the checkpoint-resolution rule. Every name here is re-exported from
``moe_router`` so existing call sites resolve unchanged.
"""

from __future__ import annotations

import hashlib
import math
import re
import sys
from pathlib import Path
from typing import Any

_PIPELINES = Path(__file__).resolve().parent
if str(_PIPELINES) not in sys.path:
    sys.path.insert(0, str(_PIPELINES))

from oracle_grounded import distill_contract as oc  # noqa: E402


FAMILY = "moe-router-distillation-trajectories"
GENERATOR_NAME = "context-corpus-generator"
GENERATOR_VERSION = "1.0.0"

FEATURE_DIM = 48
COMPACT_DIM = 16
# compact_view appends tail mean/energy/max/min to the leading components.
COMPACT_SUMMARY_STATS = 4

# The one featurizer this family's compact inputs come from. Pinned so the
# validator can recompute the student input from the recorded context rather
# than trust the vector it was handed.
FEATURIZER_ID = "blake2b-char-trigram-hashing/1.0.0"

# The largest dimensions the validator will recompute. Without a ceiling a
# malformed record declaring feature_dim of a few billion would make the
# recomputation allocate that many buckets before anything could object.
MAX_RECOMPUTE_DIM = 4096

# The generator builds its reference router with no arguments, so a record that
# omits a dimension still recomputes against the same gate when the declared
# values do not override it.
_DEFAULT_REFERENCE_SEED = 7

# Oracles that compute real routing but are not language-model teachers. A
# recording may never name one of these as the teacher it replays. The name,
# type and implementation are all checked: a laundered record can rename the
# fingerprint's model while leaving the oracle's own identity intact.
NON_TEACHER_ORACLE_NAMES = frozenset({"reference_moe_router"})
NON_TEACHER_ORACLE_TYPES = frozenset({"reference_model_router"})
NON_TEACHER_IMPLEMENTATIONS = frozenset(
    {"pipelines/moe_router.py:ReferenceMoERouter"}
)

# The oracle types that can ground an authoritative routing label: a real
# model router or a recording of one. An authoritative record claiming any
# other type has no router behind it at all and fails closed.
TEACHER_ORACLE_TYPES = frozenset({"real_model_router", "recorded_measurement"})

# Slack allowed when the validator recomputes a summary from the recorded
# logits. The logits are themselves stored rounded to 6 places, so an exact
# comparison would reject honest records; anything wider than this would start
# admitting fabricated ones.
RECOMPUTE_TOLERANCE = 1e-4

# A 40-character hex string: a resolved git commit on the Hub. A branch or tag
# is not a checkpoint — the same name serves different weights tomorrow.
COMMIT_SHA_RE = re.compile(r"^[0-9a-f]{40}$")

# Sealed known-Hub MoE cardinality cards. Published config facts for models
# whose fingerprints appear as authoritative teachers. Validate binds declared
# depth / experts / top-k to these cards — no Hub network calls in CI.
SEALED_HUB_MOE_CARDS: dict[str, dict[str, int]] = {
    "mistralai/Mixtral-8x7B-Instruct-v0.1": {
        "num_hidden_layers": 32,
        "num_local_experts": 8,
        "num_experts_per_tok": 2,
    },
}

# Sealed (model, revision) -> configuration_sha256. Format-valid 40-hex alone
# is not a binding; an authoritative record naming a sealed-card model must
# carry a revision whose digest is listed here. Tip fixtures use
# ReferenceMoERouter (not Hub Mixtral), so this table stays empty until a real
# teacher run is sealed — unbound 40-hex must fail closed.
SEALED_HUB_MOE_REVISIONS: dict[tuple[str, str], str] = {}

TRANSFORMERS_MOE_IMPLEMENTATION = (
    "pipelines/moe_router.py:TransformersMoERouter"
)

# Oracle-label policy (D2): the routing keys only this family's oracle may
# write. Any of them inside a generator-owned section is a label leak.
ORACLE_LABEL_POLICY = oc.declare_oracle_labels(
    FAMILY,
    {
        "routing",
        "top1_expert",
        "teacher_grounded",
        "is_llm_teacher",
        "top_k_experts",
        "router_logits",
        "top1_top2_margin",
        "routing_entropy",
        "expert_agreement",
    },
)


def resolve_checkpoint(revision: Any, config_commit: Any) -> str:
    """Return the immutable commit these teacher weights came from.

    ``configuration_sha256`` only covers the configuration, so two runs of
    different weights under one mutable branch name produce different routing
    labels under an identical recorded identity. Prefer the commit the loader
    resolved (``config._commit_hash``); accept an explicitly pinned commit;
    refuse anything else rather than recording ``main`` as a checkpoint.
    """

    if isinstance(config_commit, str) and COMMIT_SHA_RE.match(config_commit.strip()):
        return config_commit.strip()
    if isinstance(revision, str) and COMMIT_SHA_RE.match(revision.strip()):
        return revision.strip()
    raise oc.OracleUnavailable(
        "transformers_moe_router",
        f"cannot record an immutable checkpoint: revision {revision!r} is not a "
        "resolved commit and the loaded configuration exposes none; pass "
        "--revision <40-hex commit> so the teacher identity is reproducible",
    )


# Context seeds spanning prose, code, math, structured data, dialogue and
# configuration. The generator composes them; it never labels them.
CONTEXT_TEMPLATES: tuple[tuple[str, str], ...] = (
    ("prose", "The relay held its gate closed while the {noun} settled, and the "
              "operator logged a {adj} disposition before the next window."),
    ("prose", "Reviewers disagreed about whether the {noun} counted as evidence; "
              "the {adj} reading eventually won the argument."),
    ("code_python", "def {noun}_gate(events, threshold):\n"
                    "    kept = [e for e in events if e.amplitude > threshold]\n"
                    "    return sorted(kept, key=lambda e: e.t_rel_ms)"),
    ("code_rust", "fn {noun}_step(state: &mut Relay, dt: f32) -> Result<(), Fault> "
                  "{{\n    state.decay(dt);\n    state.commit()\n}}"),
    ("code_sql", "SELECT channel, avg(amplitude) AS mean_{noun}\n"
                 "FROM spike_events WHERE t_rel_ms < 50 GROUP BY channel;"),
    ("math", "Let x_i denote the {noun} allocation. Minimise sum_i w_i x_i^2 "
             "subject to sum_i x_i = D and 0 <= x_i <= c_i."),
    ("structured", '{{"channel": "c{digit}", "state": "{adj}", '
                   '"t_rel_ms": {digit}.0, "kind": "{noun}"}}'),
    ("dialogue", "A: the {noun} looks {adj} to me.\nB: it is within tolerance; "
                 "keep the loop closed and re-check next tick."),
    ("config", "[relay.{noun}]\nmode = \"{adj}\"\nstale_threshold_ms = {digit}\n"
               "fallback = true"),
    ("task", "Given a {adj} {noun} trace, decide whether to continue, degrade, "
             "fall back, or fail closed, and justify the choice."),
)

TEMPLATE_NOUNS = (
    "spike", "relay", "thermal", "router", "expert", "gate", "burst",
    "actuator", "channel", "window",
)
TEMPLATE_ADJECTIVES = (
    "stale", "saturated", "nominal", "jittered", "corrupt", "degraded",
    "quarantined", "bounded",
)


# --------------------------------------------------------------------------
# Featurisation
# --------------------------------------------------------------------------


def featurize(text: str, dim: int = FEATURE_DIM) -> list[float]:
    """Deterministic hashed character-trigram features, L2-normalised.

    Stdlib only and stable across machines: bucket assignment comes from
    BLAKE2b, not from Python's randomised ``hash``.
    """

    if dim < 4:
        raise oc.ContractError("feature dim must be >= 4")
    buckets = [0.0] * dim
    padded = f"  {text}  "
    for index in range(len(padded) - 2):
        trigram = padded[index : index + 3]
        digest = hashlib.blake2b(trigram.encode("utf-8"), digest_size=8).digest()
        bucket = int.from_bytes(digest[:4], "big") % dim
        sign = 1.0 if digest[4] % 2 == 0 else -1.0
        buckets[bucket] += sign
    norm = math.sqrt(sum(value * value for value in buckets))
    if not norm:
        return buckets
    return [round(value / norm, 9) for value in buckets]


def compact_view(features: list[float], compact_dim: int = COMPACT_DIM) -> list[float]:
    """A deliberately lossy student-side view of the full gate input.

    The reference gate consumes the full feature vector. The student sees the
    leading ``compact_dim`` components plus four summary statistics, so the
    distillation target is not trivially a copy of the gate's own input.
    """

    head = list(features[:compact_dim])
    tail = features[compact_dim:] or [0.0]
    mean = sum(tail) / len(tail)
    energy = math.sqrt(sum(value * value for value in tail))
    return head + [
        round(mean, 9),
        round(energy, 9),
        round(max(tail), 9),
        round(min(tail), 9),
    ]


def softmax(values: list[float]) -> list[float]:
    peak = max(values)
    exponentials = [math.exp(value - peak) for value in values]
    total = sum(exponentials)
    return [value / total for value in exponentials]


def entropy_nats(probabilities: list[float]) -> float:
    return -sum(p * math.log(p) for p in probabilities if p > 0.0)
