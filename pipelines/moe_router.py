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
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
import re
import sys
from collections import Counter
from dataclasses import dataclass
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

# Oracles that compute real routing but are not language-model teachers. A
# recording may never name one of these as the teacher it replays. The name,
# type and implementation are all checked: a laundered record can rename the
# fingerprint's model while leaving the oracle's own identity intact.
NON_TEACHER_ORACLE_NAMES = frozenset({"reference_moe_router"})
NON_TEACHER_ORACLE_TYPES = frozenset({"reference_model_router"})
NON_TEACHER_IMPLEMENTATIONS = frozenset(
    {"pipelines/moe_router.py:ReferenceMoERouter"}
)

# Slack allowed when the validator recomputes a summary from the recorded
# logits. The logits are themselves stored rounded to 6 places, so an exact
# comparison would reject honest records; anything wider than this would start
# admitting fabricated ones.
RECOMPUTE_TOLERANCE = 1e-4

# A 40-character hex string: a resolved git commit on the Hub. A branch or tag
# is not a checkpoint — the same name serves different weights tomorrow.
COMMIT_SHA_RE = re.compile(r"^[0-9a-f]{40}$")


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
    if norm == 0.0:
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


# --------------------------------------------------------------------------
# Oracle boundary
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class LayerRouting:
    """One layer's routing decision as the router actually computed it."""

    layer: int
    top_k_experts: tuple[int, ...]
    router_logits: tuple[float, ...] | None
    top1_top2_margin: float
    routing_entropy: float


@dataclass(frozen=True)
class RouterObservation:
    """Compact distillation targets for one context."""

    layers: tuple[LayerRouting, ...]
    top1_expert: int
    expert_agreement: float

    def as_dict(self) -> dict[str, Any]:
        return {
            "layers": [
                {
                    "layer": layer.layer,
                    "top_k_experts": list(layer.top_k_experts),
                    "router_logits": (
                        list(layer.router_logits)
                        if layer.router_logits is not None
                        else None
                    ),
                    "top1_top2_margin": layer.top1_top2_margin,
                    "routing_entropy": layer.routing_entropy,
                }
                for layer in self.layers
            ],
            "top1_expert": self.top1_expert,
            "expert_agreement": self.expert_agreement,
        }


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


class ReferenceMoERouter(RouterOracle):
    """Deterministic seeded top-k gate. Real computation, not an LLM teacher."""

    name = "reference_moe_router"
    version = "1.0.0"
    oracle_type = "reference_model_router"
    authority = oc.AUTHORITY_REFERENCE_ONLY
    implementation = "pipelines/moe_router.py:ReferenceMoERouter"
    is_llm_teacher = False

    @staticmethod
    def _check_gate_shape(top_k: int, num_experts: int, num_layers: int) -> None:
        if top_k < 2:
            raise oc.ContractError("top_k must be >= 2 to define a top1/top2 margin")
        if num_experts <= top_k:
            raise oc.ContractError("num_experts must exceed top_k")
        if num_layers < 1:
            # A layerless router builds an empty routing list and `_summarise`
            # then fails indexing `Counter(...).most_common(1)[0]`. Fail here
            # with a bounded contract error instead of crashing generation.
            raise oc.ContractError("num_layers must be >= 1")

    def __init__(
        self,
        *,
        seed: int = 7,
        num_experts: int = 8,
        num_layers: int = 4,
        top_k: int = 2,
        dim: int = FEATURE_DIM,
    ) -> None:
        self._check_gate_shape(top_k, num_experts, num_layers)
        self.seed = seed
        self.num_experts = num_experts
        self.num_layers = num_layers
        self.top_k = top_k
        self.dim = dim
        rng = random.Random(seed)
        self.gates: list[list[list[float]]] = [
            [
                [rng.gauss(0.0, 1.0) for _ in range(dim)]
                for _ in range(num_experts)
            ]
            for _ in range(num_layers)
        ]
        self.biases: list[list[float]] = [
            [rng.gauss(0.0, 0.35) for _ in range(num_experts)]
            for _ in range(num_layers)
        ]

    def available(self) -> tuple[bool, str]:
        return True, "pure-python reference gate"

    def configuration(self) -> dict[str, Any]:
        return {
            "num_experts": self.num_experts,
            "num_layers": self.num_layers,
            "top_k": self.top_k,
            "feature_dim": self.dim,
            "gate": "linear + softmax, gaussian weights from random.Random(seed)",
        }

    def fingerprint(self) -> dict[str, Any]:
        gate_bytes = oc.canonical_json(
            {"gates": self.gates, "biases": self.biases}
        ).encode("utf-8")
        return {
            "is_llm_teacher": False,
            "model": "reference_moe_router",
            "revision_or_checkpoint": f"seed:{self.seed}",
            "configuration_sha256": hashlib.sha256(gate_bytes).hexdigest(),
            "num_local_experts": self.num_experts,
            "num_experts_per_tok": self.top_k,
            "num_layers": self.num_layers,
            "note": "deterministic stand-in; not a language model teacher",
        }

    def route(self, text: str) -> RouterObservation:
        features = featurize(text, self.dim)
        layers: list[LayerRouting] = []
        for index in range(self.num_layers):
            logits = [
                sum(w * x for w, x in zip(row, features)) + bias
                for row, bias in zip(self.gates[index], self.biases[index])
            ]
            order = sorted(range(self.num_experts), key=lambda e: (-logits[e], e))
            top = tuple(order[: self.top_k])
            probabilities = softmax(logits)
            layers.append(
                LayerRouting(
                    layer=index,
                    top_k_experts=top,
                    router_logits=tuple(round(value, 6) for value in logits),
                    top1_top2_margin=round(logits[order[0]] - logits[order[1]], 6),
                    routing_entropy=round(entropy_nats(probabilities), 6),
                )
            )
        return _summarise(layers)


class RecordedTeacherRouter(RouterOracle):
    """Replays routing recorded from a real teacher run. Fails closed.

    This is the only oracle here that turns a file on disk into an
    ``authoritative`` label, so it is also the obvious laundering route: point
    it at a recording of a stand-in's output, label the recording as a teacher,
    and the stand-in's routing becomes curatable teacher truth.

    Two guards make that a deliberate lie rather than an accident. The
    recording must declare ``is_llm_teacher: true`` explicitly — the default is
    no longer "assume teacher" — and it may not name a known non-teacher oracle
    as its model. Neither guard can stop someone who sets out to forge a
    recording; what they stop is a stand-in's output drifting into the
    authoritative path by omission.
    """

    name = "recorded_teacher_router"
    version = "1.0.0"
    oracle_type = "recorded_measurement"
    authority = oc.AUTHORITY_AUTHORITATIVE
    implementation = "pipelines/moe_router.py:RecordedTeacherRouter"

    def __init__(self, recording: dict[str, Any]) -> None:
        self.recording = recording
        teacher = recording.get("teacher")
        self.teacher = teacher if isinstance(teacher, dict) else {}
        observations = recording.get("observations")
        self.observations = observations if isinstance(observations, dict) else {}
        # Defaults to False: a recording that forgets to say what produced it
        # is not assumed to be a teacher.
        self.is_llm_teacher = self.teacher.get("is_llm_teacher") is True

    @classmethod
    def from_path(cls, path) -> "RecordedTeacherRouter":
        return cls(json.loads(Path(path).read_text(encoding="utf-8")))

    @staticmethod
    def key_for(text: str) -> str:
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    def _teacher_identity_problem(self) -> str | None:
        """Why the recorded teacher identity cannot ground labels, if any."""

        missing = [
            field
            for field in ("model", "revision_or_checkpoint", "configuration_sha256")
            if not self.teacher.get(field)
        ]
        if missing:
            return f"recording is missing teacher fields: {sorted(missing)}"
        revision = self.teacher.get("revision_or_checkpoint")
        if not (isinstance(revision, str) and COMMIT_SHA_RE.match(revision.strip())):
            # A branch or tag is not a checkpoint: the same name can serve
            # different weights tomorrow while the configuration digest stays
            # the same, so replayed labels would share one teacher identity
            # across revisions.
            return (
                f"recording names a mutable revision {revision!r}; a replayed "
                "teacher must pin a resolved 40-hex commit"
            )
        if not self.is_llm_teacher:
            return (
                "recording does not declare is_llm_teacher: true — a recorded "
                "replay may only ground labels for a real teacher run"
            )
        model = self.teacher.get("model")
        if isinstance(model, str) and model in NON_TEACHER_ORACLE_NAMES:
            return (
                f"recording names {model!r} as its teacher, which is a "
                "non-teacher stand-in; its routing may not be curated as "
                "teacher truth"
            )
        # Without these declarations nothing bounds the replayed routing: a
        # recording with no logits could serve ids like [-1, 999], widen its
        # top-k, or drop a layer suffix, all as authoritative labels.
        for field, consequence in (
            ("num_local_experts", "replayed expert ids cannot be range-checked"),
            ("num_experts_per_tok", "the replayed top-k width cannot be checked"),
            ("num_layers", "a dropped layer suffix cannot be detected"),
        ):
            if _declared_positive_int(self.teacher, field) is None:
                return (
                    f"recording does not declare a positive {field}, so "
                    f"{consequence}"
                )
        return None

    def available(self) -> tuple[bool, str]:
        problem = self._teacher_identity_problem()
        if problem is not None:
            return False, problem
        if not self.observations:
            return False, "recording contains no routing observations"
        return True, f"{len(self.observations)} recorded context(s)"

    def configuration(self) -> dict[str, Any]:
        return {
            "recording_id": self.recording.get("run_id"),
            "recorded_at": self.recording.get("recorded_at"),
            "observations": len(self.observations),
        }

    def fingerprint(self) -> dict[str, Any]:
        return {**self.teacher, "is_llm_teacher": self.is_llm_teacher}

    def _recorded_experts(self, layer: dict[str, Any]) -> tuple[int, ...]:
        """The layer's expert ids, validated rather than coerced.

        ``int()`` coercion silently turned ``true`` into ``1`` and ``3.7``
        into ``3``, and an empty list slipped through to ``_summarise`` where
        indexing the first expert raised ``IndexError`` instead of failing
        closed. Only a list of at least two genuine integers can define a
        top-k with a top-1/top-2 margin.
        """

        experts = layer.get("top_k_experts")
        if not isinstance(experts, list) or len(experts) < 2:
            raise oc.OracleUnavailable(
                self.name, "layer top_k_experts must list at least the top two"
            )
        for value in experts:
            if not isinstance(value, int) or isinstance(value, bool):
                raise oc.OracleUnavailable(
                    self.name,
                    f"layer top_k_experts must be integers, got {value!r}",
                )
        return tuple(experts)

    def _recorded_logits(self, layer: dict[str, Any]) -> tuple[float, ...] | None:
        logits = layer.get("router_logits")
        if logits is None:
            return None
        if not isinstance(logits, list) or not all(
            oc.is_number(value) for value in logits
        ):
            raise oc.OracleUnavailable(
                self.name, "layer router_logits must be an array of finite numbers"
            )
        return tuple(float(value) for value in logits)

    def _recorded_layer(self, layer: Any) -> LayerRouting:
        if not isinstance(layer, dict):
            raise oc.OracleUnavailable(self.name, "layer must be an object")
        if not oc.is_number(layer.get("top1_top2_margin")):
            raise oc.OracleUnavailable(self.name, "layer missing top1_top2_margin")
        if not oc.is_number(layer.get("routing_entropy")):
            raise oc.OracleUnavailable(self.name, "layer missing routing_entropy")
        layer_index = layer.get("layer")
        if not isinstance(layer_index, int) or isinstance(layer_index, bool):
            # int() silently rewrote 0.9 to 0 and True to 1, normalising
            # malformed recording metadata into a validation-clean trajectory
            # instead of failing closed at the replay boundary.
            raise oc.OracleUnavailable(
                self.name,
                f"layer index must be a genuine integer, got {layer_index!r}",
            )
        try:
            return LayerRouting(
                layer=layer_index,
                top_k_experts=self._recorded_experts(layer),
                router_logits=self._recorded_logits(layer),
                top1_top2_margin=float(layer["top1_top2_margin"]),
                routing_entropy=float(layer["routing_entropy"]),
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise oc.OracleUnavailable(self.name, f"malformed layer data: {exc}")

    def route(self, text: str) -> RouterObservation:
        entry = self.observations.get(self.key_for(text))
        if not isinstance(entry, dict) or not isinstance(entry.get("layers"), list):
            raise oc.OracleUnavailable(
                self.name,
                f"no recorded routing for context sha256 {self.key_for(text)}",
            )
        layers = [self._recorded_layer(layer) for layer in entry["layers"]]
        if not layers:
            raise oc.OracleUnavailable(self.name, "recorded routing has no layers")
        return _summarise(layers)


class TransformersMoERouter(RouterOracle):
    """Real Hugging Face MoE teacher. Unavailable in this environment.

    ``route`` runs the checkpoint with ``output_router_logits=True`` and reads
    the per-layer gate logits for the final position. That request path is the
    documented transformers API for MoE causal LMs (Mixtral, Qwen2-MoE, OLMoE,
    GraniteMoE and friends); it is **not exercised here** because the local
    ``transformers`` install cannot import (missing ``regex``) and no MoE
    checkpoint is available offline. Nothing downstream fakes its output: with
    the dependency missing, ``available()`` is false and ``route`` raises.
    """

    name = "transformers_moe_router"
    version = "1.0.0"
    oracle_type = "real_model_router"
    authority = oc.AUTHORITY_AUTHORITATIVE
    implementation = "pipelines/moe_router.py:TransformersMoERouter"
    is_llm_teacher = True

    def __init__(
        self,
        model_id: str,
        *,
        revision: str | None = None,
        device: str = "cpu",
        top_k: int | None = None,
    ) -> None:
        self.model_id = model_id
        self.revision = revision
        self.device = device
        self.top_k = top_k
        self._model = None
        self._tokenizer = None
        self._fingerprint: dict[str, Any] | None = None

    def available(self) -> tuple[bool, str]:
        try:
            import torch  # noqa: F401
            import transformers  # noqa: F401
        except Exception as exc:  # pragma: no cover - depends on the host
            return False, f"{type(exc).__name__}: {exc}"
        return True, "torch and transformers import"

    def _load(self):  # pragma: no cover - requires a real checkpoint
        if self._model is not None:
            return self._model, self._tokenizer
        ok, detail = self.available()
        if not ok:
            raise oc.OracleUnavailable(self.name, detail)
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer

        kwargs: dict[str, Any] = {}
        if self.revision:
            kwargs["revision"] = self.revision
        tokenizer = AutoTokenizer.from_pretrained(self.model_id, **kwargs)
        model = AutoModelForCausalLM.from_pretrained(self.model_id, **kwargs)
        model.eval()
        model.to(self.device)
        config = model.config
        if not getattr(config, "num_local_experts", None) and not getattr(
            config, "num_experts", None
        ):
            raise oc.OracleUnavailable(
                self.name, f"{self.model_id} is not a mixture-of-experts checkpoint"
            )
        self._fingerprint = {
            "is_llm_teacher": True,
            "model": self.model_id,
            # Never "main": a branch name is not a checkpoint, and the
            # configuration digest does not cover the weights.
            "revision_or_checkpoint": resolve_checkpoint(
                self.revision, getattr(config, "_commit_hash", None)
            ),
            "configuration_sha256": hashlib.sha256(
                config.to_json_string().encode("utf-8")
            ).hexdigest(),
            "num_local_experts": getattr(config, "num_local_experts", None)
            or getattr(config, "num_experts", None),
            "num_experts_per_tok": getattr(config, "num_experts_per_tok", None),
            # Initial claim from the config; `route` overwrites it with the
            # routed trajectory length, because interleaved-MoE checkpoints
            # emit router_logits only for their MoE layers.
            "num_layers": getattr(config, "num_hidden_layers", None),
            "torch_dtype": str(getattr(model, "dtype", "unknown")),
            "transformers_version": __import__("transformers").__version__,
            "torch_version": torch.__version__,
            "device": self.device,
        }
        self._model, self._tokenizer = model, tokenizer
        return model, tokenizer

    def configuration(self) -> dict[str, Any]:
        return {
            "model_id": self.model_id,
            "revision": self.revision,
            "device": self.device,
            "request": "output_router_logits=True",
        }

    def fingerprint(self) -> dict[str, Any]:
        if self._fingerprint is None:
            raise oc.OracleUnavailable(
                self.name, "fingerprint is only available after the model loads"
            )
        return dict(self._fingerprint)

    def route(self, text: str) -> RouterObservation:  # pragma: no cover - no checkpoint
        model, tokenizer = self._load()
        import torch

        inputs = tokenizer(text, return_tensors="pt").to(self.device)
        with torch.no_grad():
            outputs = model(**inputs, output_router_logits=True)
        router_logits = getattr(outputs, "router_logits", None)
        if not router_logits:
            raise oc.OracleUnavailable(
                self.name, f"{self.model_id} returned no router_logits"
            )
        top_k = self.top_k or self._fingerprint.get("num_experts_per_tok") or 2
        layers: list[LayerRouting] = []
        for index, layer_logits in enumerate(router_logits):
            # transformers returns (tokens, experts) per layer; read the last
            # position so one context yields one routing decision per layer.
            values = [float(value) for value in layer_logits[-1].tolist()]
            order = sorted(range(len(values)), key=lambda e: (-values[e], e))
            layers.append(
                LayerRouting(
                    layer=index,
                    top_k_experts=tuple(order[:top_k]),
                    router_logits=tuple(round(value, 6) for value in values),
                    top1_top2_margin=round(values[order[0]] - values[order[1]], 6),
                    routing_entropy=round(entropy_nats(softmax(values)), 6),
                )
            )
        # The fingerprint's layer-count claim must be the ROUTED trajectory
        # length, not config.num_hidden_layers: interleaved-MoE checkpoints
        # (Qwen2-MoE style) emit router_logits only for their MoE layers, so
        # the config count can exceed the routed count and every honest
        # record would then fail `_check_layer_count`. `build_records`
        # captures the oracle block after the first route, so this
        # correction lands in the emitted fingerprint.
        self._fingerprint["num_layers"] = len(layers)
        return _summarise(layers)


def oracles_report() -> dict[str, Any]:
    """Probe each router oracle without producing any routing labels."""

    teacher = TransformersMoERouter("<unset>")
    teacher_ok, teacher_detail = teacher.available()
    reference = ReferenceMoERouter()
    return {
        "family": FAMILY,
        "oracles": [
            {
                "name": teacher.name,
                "type": teacher.oracle_type,
                "authority": teacher.authority,
                "is_llm_teacher": True,
                "available": teacher_ok,
                "detail": teacher_detail,
                "note": "still needs an MoE checkpoint even when the import works",
            },
            {
                "name": RecordedTeacherRouter.name,
                "type": RecordedTeacherRouter.oracle_type,
                "authority": RecordedTeacherRouter.authority,
                "is_llm_teacher": True,
                "available": False,
                "detail": "supply a recording from a real teacher run",
            },
            {
                "name": reference.name,
                "type": reference.oracle_type,
                "authority": reference.authority,
                "is_llm_teacher": False,
                "available": True,
                "detail": "deterministic stand-in; records are reference_only",
            },
        ],
    }


# --------------------------------------------------------------------------
# Generator
# --------------------------------------------------------------------------


def propose_contexts(seed: int, count: int) -> list[dict[str, Any]]:
    """Generator side: diverse contexts and their compact student inputs."""

    if count < 1:
        raise oc.ContractError("count must be >= 1")
    rng = random.Random(seed)
    proposals: list[dict[str, Any]] = []
    for index in range(count):
        domain, template = CONTEXT_TEMPLATES[index % len(CONTEXT_TEMPLATES)]
        text = template.format(
            noun=rng.choice(TEMPLATE_NOUNS),
            adj=rng.choice(TEMPLATE_ADJECTIVES),
            digit=rng.randrange(10),
        )
        features = featurize(text)
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
                        "feature_dim": FEATURE_DIM,
                        "compact_dim": COMPACT_DIM,
                        "view": "leading components + tail mean/energy/max/min",
                        "features": compact_view(features),
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
    records: list[dict[str, Any]] = []
    for proposal in propose_contexts(seed, count):
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


class _LayerOrder:
    """Running layer-index state carried across the recorded layers."""

    def __init__(self) -> None:
        self.seen: set[int] = set()
        self.previous: int | None = None


def _check_context_digest(scenario: dict[str, Any], where: str) -> list[str]:
    """The student-visible context and the digest that pins it."""

    context = scenario.get("context")
    if not isinstance(context, str) or not context.strip():
        return [f"{where}.scenario.context must be a non-empty string"]
    if scenario.get("context_sha256") != hashlib.sha256(
        context.encode("utf-8")
    ).hexdigest():
        return [f"{where}.scenario.context_sha256 does not match the context"]
    return []


def _check_compact_input(scenario: dict[str, Any], where: str) -> list[str]:
    """The compact student input the baseline is evaluated on."""

    compact = scenario.get("compact_input")
    if not isinstance(compact, dict):
        return [f"{where}.scenario.compact_input must be an object"]
    features = compact.get("features")
    if not isinstance(features, list) or not features:
        return [
            f"{where}.scenario.compact_input.features must carry the "
            "student input the baseline is evaluated on"
        ]
    if not all(oc.is_number(value) for value in features):
        # router_baseline silently skips a record whose features are not
        # finite numbers, so without this a curated corpus could contain
        # no usable student input at all.
        return [
            f"{where}.scenario.compact_input.features must be finite "
            "numbers — the baseline extractor drops anything else"
        ]
    declared = compact.get("compact_dim")
    if isinstance(declared, int) and not isinstance(declared, bool):
        expected = declared + COMPACT_SUMMARY_STATS
        if len(features) != expected:
            return [
                f"{where}.scenario.compact_input.features has "
                f"{len(features)} values but compact_dim {declared} "
                f"declares {expected}"
            ]
    return _check_compact_recompute(scenario, compact, features, where)


def _positive_dim(value: Any, floor: int) -> int | None:
    if (
        isinstance(value, int)
        and not isinstance(value, bool)
        and floor <= value <= MAX_RECOMPUTE_DIM
    ):
        return value
    return None


def _check_compact_recompute(
    scenario: dict[str, Any],
    compact: dict[str, Any],
    features: list[Any],
    where: str,
) -> list[str]:
    """The features must recompute from the context they claim to describe.

    Width and finiteness alone let a correctly rehashed record replace the
    student input with arbitrary finite values of the same length while
    ``router_baseline`` consumes them as the input paired with the teacher's
    label — a corrupted input-label pairing that could change the baseline
    and the escalation verdict. The featurizer is deterministic, so the
    validator recomputes ``compact_view(featurize(context))`` instead of
    trusting the vector.
    """

    if compact.get("featurizer") != FEATURIZER_ID:
        return [
            f"{where}.scenario.compact_input.featurizer must be "
            f"{FEATURIZER_ID!r} so the student input can be recomputed, got "
            f"{compact.get('featurizer')!r}"
        ]
    feature_dim = _positive_dim(compact.get("feature_dim"), 4)
    compact_dim = _positive_dim(compact.get("compact_dim"), 1)
    if feature_dim is None or compact_dim is None:
        return [
            f"{where}.scenario.compact_input must declare integer "
            f"feature_dim (4..{MAX_RECOMPUTE_DIM}) and compact_dim "
            f"(1..{MAX_RECOMPUTE_DIM}) so the student input can be recomputed"
        ]
    context = scenario.get("context")
    if not isinstance(context, str) or not context.strip():
        # Reported by the context-digest check; nothing to recompute from.
        return []
    expected = compact_view(featurize(context, feature_dim), compact_dim)
    if len(features) != len(expected) or any(
        abs(float(value) - target) > 1e-9
        for value, target in zip(features, expected)
    ):
        return [
            f"{where}.scenario.compact_input.features: "
            "COMPACT_INPUT_NOT_REPRODUCIBLE — the recorded features do not "
            "recompute from the context with the declared featurizer"
        ]
    return []


def _check_scenario_context(scenario: Any, where: str) -> list[str]:
    """The student-visible context, its digest, and the compact input."""

    if not isinstance(scenario, dict):
        return []
    return _check_context_digest(scenario, where) + _check_compact_input(
        scenario, where
    )


def _check_fingerprint_identity(fingerprint: dict[str, Any], where: str) -> list[str]:
    """Model, checkpoint, configuration digest, and the teacher flag."""

    errors: list[str] = []
    for field in ("model", "revision_or_checkpoint", "configuration_sha256"):
        value = fingerprint.get(field)
        if not isinstance(value, str) or not value.strip():
            errors.append(f"{where}.oracle.fingerprint.{field} must be recorded")
    # "not-a-digest" satisfied the non-empty check above, so the promised
    # configuration digest could be absent in everything but name and the
    # teacher configuration could never be audited.
    configuration_digest = fingerprint.get("configuration_sha256")
    if isinstance(configuration_digest, str) and configuration_digest.strip():
        if not oc.SHA256_RE.match(configuration_digest):
            errors.append(
                f"{where}.oracle.fingerprint.configuration_sha256 must be a "
                f"64-character sha256 hex digest, got "
                f"{configuration_digest!r}"
            )
    if not isinstance(fingerprint.get("is_llm_teacher"), bool):
        errors.append(
            f"{where}.oracle.fingerprint.is_llm_teacher must be a boolean"
        )
    return errors


def _non_teacher_identity(oracle: dict[str, Any], fingerprint: dict[str, Any]) -> str | None:
    """The stand-in identity an oracle block carries, if it carries one.

    The fingerprint's ``model`` is caller-controlled prose; the oracle's own
    name, type and implementation are what the producing code wrote. All four
    are checked so renaming one field cannot launder a stand-in.
    """

    if oc.is_enum_value(fingerprint.get("model"), NON_TEACHER_ORACLE_NAMES):
        return f"fingerprint.model {fingerprint.get('model')!r}"
    if oc.is_enum_value(oracle.get("name"), NON_TEACHER_ORACLE_NAMES):
        return f"oracle.name {oracle.get('name')!r}"
    if oc.is_enum_value(oracle.get("type"), NON_TEACHER_ORACLE_TYPES):
        return f"oracle.type {oracle.get('type')!r}"
    if oc.is_enum_value(oracle.get("implementation"), NON_TEACHER_IMPLEMENTATIONS):
        return f"oracle.implementation {oracle.get('implementation')!r}"
    return None


def _check_laundered_oracle(
    oracle: Any, fingerprint: dict[str, Any], where: str
) -> list[str]:
    """A non-teacher stand-in may not be recorded as an authoritative teacher."""

    if not isinstance(oracle, dict) or oracle.get("authority") != oc.AUTHORITY_AUTHORITATIVE:
        return []
    identity = _non_teacher_identity(oracle, fingerprint)
    if identity is not None:
        return [
            f"{where}.oracle: LAUNDERED_REFERENCE_ORACLE — {identity} names a "
            "non-teacher stand-in and may not be recorded as an authoritative "
            "teacher"
        ]
    return []


def _check_authoritative_checkpoint(
    oracle: Any, fingerprint: Any, where: str
) -> list[str]:
    """An authoritative router record must pin an immutable checkpoint.

    ``resolve_checkpoint`` protects the live Transformers adapter, but a
    replayed recording could otherwise carry ``revision_or_checkpoint:
    "main"`` — a mutable name under which different weight revisions share
    one teacher identity while the configuration digest stays the same.
    """

    if not (
        isinstance(oracle, dict)
        and oracle.get("authority") == oc.AUTHORITY_AUTHORITATIVE
        and isinstance(fingerprint, dict)
    ):
        return []
    revision = fingerprint.get("revision_or_checkpoint")
    if isinstance(revision, str) and COMMIT_SHA_RE.match(revision.strip()):
        return []
    return [
        f"{where}.oracle.fingerprint.revision_or_checkpoint must be a "
        f"resolved 40-hex commit for an authoritative router record, got "
        f"{revision!r} — a mutable name can serve different weights under "
        "one recorded identity"
    ]


def _check_teacher_fingerprint(oracle: Any, fingerprint: Any, where: str) -> list[str]:
    """The recorded teacher identity: model, checkpoint, configuration digest."""

    if not isinstance(fingerprint, dict):
        return [
            f"{where}.oracle.fingerprint must record the teacher model, checkpoint "
            "and configuration"
        ]
    return _check_fingerprint_identity(fingerprint, where) + _check_laundered_oracle(
        oracle, fingerprint, where
    )


def _check_is_llm_teacher(
    result: dict[str, Any], fingerprint: Any, where: str
) -> list[str]:
    """The result's teacher flag must be a boolean and match the fingerprint."""

    if not isinstance(result.get("is_llm_teacher"), bool):
        return [f"{where}.result.is_llm_teacher must be a boolean"]
    if isinstance(fingerprint, dict) and isinstance(
        fingerprint.get("is_llm_teacher"), bool
    ):
        if result["is_llm_teacher"] != fingerprint["is_llm_teacher"]:
            return [
                f"{where}.result.is_llm_teacher disagrees with the oracle fingerprint"
            ]
    return []


def _check_teacher_grounded(
    result: dict[str, Any], oracle: dict[str, Any], where: str
) -> list[str]:
    """teacher_grounded follows from the teacher flag and the oracle authority."""

    errors: list[str] = []
    expected = bool(
        result.get("is_llm_teacher")
        and oracle.get("authority") == oc.AUTHORITY_AUTHORITATIVE
    )
    if result.get("teacher_grounded") is not expected:
        errors.append(
            f"{where}.result.teacher_grounded must be {expected} for an "
            f"{oracle.get('authority')!r} oracle with is_llm_teacher="
            f"{result.get('is_llm_teacher')!r}"
        )
    # An authoritative router oracle must be a teacher. Otherwise a
    # stand-in's routing reaches curation with teacher_grounded false and
    # nothing downstream objecting.
    if (
        oracle.get("authority") == oc.AUTHORITY_AUTHORITATIVE
        and result.get("teacher_grounded") is not True
    ):
        errors.append(
            f"{where}.oracle: an authoritative router oracle must be "
            "teacher-grounded; mark a non-teacher oracle reference_only"
        )
    return errors


def _check_teacher_grounding(
    result: dict[str, Any], oracle: Any, fingerprint: Any, where: str
) -> list[str]:
    """`is_llm_teacher` and `teacher_grounded` against the oracle's authority."""

    errors = _check_is_llm_teacher(result, fingerprint, where)
    if isinstance(oracle, dict):
        errors += _check_teacher_grounded(result, oracle, where)
    return errors


def _declared_positive_int(fingerprint: Any, field: str) -> int | None:
    """A positive-integer fingerprint field, when it is declared as one."""

    if not isinstance(fingerprint, dict):
        return None
    declared = fingerprint.get(field)
    if isinstance(declared, int) and not isinstance(declared, bool) and declared > 0:
        return declared
    return None


def _declared_expert_count(fingerprint: Any) -> int | None:
    """The expert count the oracle fingerprint declares, when it declares one."""

    return _declared_positive_int(fingerprint, "num_local_experts")


def _declared_top_k(fingerprint: Any) -> int | None:
    """The per-token top-k width the fingerprint declares, when it does."""

    return _declared_positive_int(fingerprint, "num_experts_per_tok")


def _declared_layer_count(fingerprint: Any) -> int | None:
    """The routed layer count the fingerprint declares, when it does."""

    return _declared_positive_int(fingerprint, "num_layers")


def _check_layer_index(layer: dict[str, Any], spot: str, order: _LayerOrder) -> list[str]:
    """The layer index: an integer, unseen, and in model order."""

    errors: list[str] = []
    layer_index = layer.get("layer")
    if not isinstance(layer_index, int) or isinstance(layer_index, bool):
        errors.append(f"{spot}.layer must be an integer")
    elif layer_index in order.seen:
        errors.append(f"{spot}.layer {layer_index} is duplicated")
    else:
        # router_baseline._target_label reads the last-layer decision as
        # `layers[-1]`. Unique-but-unordered indices such as [3, 0, 1, 2]
        # would silently make layer 2 the training target while the record
        # advertises layer 3 — and a merely increasing sequence such as
        # [0, 2] would let interior layers vanish while still looking
        # ordered, so the trajectory must be contiguous from zero.
        expected_index = 0 if order.previous is None else order.previous + 1
        if layer_index != expected_index:
            errors.append(
                f"{spot}.layer {layer_index} where {expected_index} was "
                "expected; routing layers must be recorded contiguously "
                "from 0 in model order so the last entry is the last layer"
            )
        order.previous = layer_index
        order.seen.add(layer_index)
    return errors


def _invalid_expert_entries(experts: list[Any]) -> list[Any]:
    return [
        expert
        for expert in experts
        if not isinstance(expert, int) or isinstance(expert, bool)
    ]


def _check_layer_experts(
    layer: dict[str, Any], spot: str, expert_count: int | None,
    top_k: int | None = None,
) -> list[str]:
    """The routed expert ids: the declared width, distinct, and in range."""

    experts = layer.get("top_k_experts")
    if not isinstance(experts, list) or len(experts) < 2:
        return [f"{spot}.top_k_experts must list at least the top two"]
    if top_k is not None and len(experts) != top_k:
        # A wider (or narrower) list than the teacher's declared top-k is a
        # distillation target that contradicts the recorded configuration.
        return [
            f"{spot}.top_k_experts lists {len(experts)} experts but the "
            f"oracle fingerprint declares num_experts_per_tok {top_k}"
        ]
    invalid_experts = _invalid_expert_entries(experts)
    if invalid_experts:
        return [f"{spot}.top_k_experts contains invalid entries: {invalid_experts}"]
    if len(set(experts)) != len(experts):
        return [f"{spot}.top_k_experts must not repeat an expert"]
    if expert_count is not None and not all(
        0 <= value < expert_count for value in experts
    ):
        # Checked independently of router_logits, because a recorded
        # teacher may legitimately omit logits and would otherwise be
        # free to record ids like [-1, 999] as authoritative routing
        # labels.
        return [
            f"{spot}.top_k_experts must lie in [0, {expert_count}) — the "
            "expert count the oracle fingerprint declares"
        ]
    return []


def _experts_index_logits(experts: list[Any], size: int) -> bool:
    """True when every expert id is a genuine int indexing the logit array."""

    return all(
        isinstance(expert, int)
        and not isinstance(expert, bool)
        and 0 <= expert < size
        for expert in experts
    )


def _is_top_of_logits(experts: list[int], logits: list[Any]) -> bool:
    """True when the experts carry, position for position, the top values."""

    recorded_values = [float(logits[expert]) for expert in experts]
    top_values = sorted(
        (float(value) for value in logits), reverse=True
    )[: len(experts)]
    return recorded_values == top_values


def _check_layer_logits(
    layer: dict[str, Any], spot: str, expert_count: int | None = None
) -> list[str]:
    """Router logits, and the expert order they imply.

    The recorded top-k must carry, position for position, the largest logit
    values — but *which* expert wins an exact tie is not checked. The stored
    logits are serialised at six decimal places, so a teacher that ordered by
    full precision can legitimately disagree with an id-ordered tie-break
    over values that round together; demanding one canonical tie-break would
    reject honest records. An expert with a strictly smaller logit still
    cannot appear.
    """

    logits = layer.get("router_logits")
    if logits is None:
        return []
    if not isinstance(logits, list) or not all(
        oc.is_number(value) for value in logits
    ):
        return [f"{spot}.router_logits must be an array of numbers"]
    if expert_count is not None and len(logits) != expert_count:
        # A truncated array that still contains the selected ids passes the
        # ordering check below, but it turns the promised full teacher
        # distribution into a partial one — and both the entropy and the
        # logit distillation targets change with it.
        return [
            f"{spot}.router_logits lists {len(logits)} values but the oracle "
            f"fingerprint declares num_local_experts {expert_count}"
        ]
    experts = layer.get("top_k_experts")
    if not isinstance(experts, list) or not experts:
        return []
    if not _experts_index_logits(experts, len(logits)) or not _is_top_of_logits(
        experts, logits
    ):
        return [f"{spot}.top_k_experts disagrees with router_logits ordering"]
    return []


def _exposed_logits(layer: dict[str, Any]) -> list[float] | None:
    """The logits when they are usable for recomputation, else None.

    Both layer summaries are exact functions of the logits, so when the
    logits are exposed they are recomputed rather than range-checked. A range
    check alone let any non-negative margin and any entropy below
    ln(num_experts) stand in for the real ones — and both are
    distillation targets.
    """

    logits = layer.get("router_logits")
    if (
        isinstance(logits, list)
        and len(logits) >= 2
        and all(oc.is_number(value) for value in logits)
    ):
        return [float(value) for value in logits]
    return None


def _check_layer_margin(
    layer: dict[str, Any], spot: str, exposed_logits: list[float] | None
) -> list[str]:
    """top1_top2_margin, recomputed from the logits when they are recorded."""

    margin = layer.get("top1_top2_margin")
    if not oc.is_number(margin) or float(margin) < 0.0:
        return [f"{spot}.top1_top2_margin must be a non-negative number"]
    if exposed_logits is None:
        return []
    ordered = sorted(exposed_logits, reverse=True)
    recomputed_margin = ordered[0] - ordered[1]
    # The stored logits are themselves rounded to 6 places, so the
    # recomputation carries that rounding; the tolerance covers it and
    # nothing wider.
    if abs(float(margin) - recomputed_margin) > RECOMPUTE_TOLERANCE:
        return [
            f"{spot}.top1_top2_margin is {margin} but the recorded "
            f"router_logits give {round(recomputed_margin, 6)}"
        ]
    return []


def _check_layer_entropy(
    layer: dict[str, Any],
    spot: str,
    exposed_logits: list[float] | None,
    expert_count: int | None,
) -> list[str]:
    """routing_entropy, recomputed from the logits or bounded by ln(support)."""

    routing_entropy = layer.get("routing_entropy")
    if not oc.is_number(routing_entropy) or float(routing_entropy) < 0.0:
        return [f"{spot}.routing_entropy must be a non-negative number"]
    if exposed_logits is not None:
        recomputed_entropy = entropy_nats(softmax(exposed_logits))
        if abs(float(routing_entropy) - recomputed_entropy) > RECOMPUTE_TOLERANCE:
            return [
                f"{spot}.routing_entropy is {routing_entropy} but the "
                f"recorded router_logits give {round(recomputed_entropy, 6)}"
            ]
        return []
    # No logits to recompute from, so fall back to bounding the entropy
    # by ln(num_experts) using the recorded expert count. Kept separate
    # from `expert_count` above so one layer's logit width does not
    # become the id range every later layer is checked against.
    logits = layer.get("router_logits")
    support = len(logits) if isinstance(logits, list) and logits else expert_count
    if support and float(routing_entropy) > math.log(support) + 1e-6:
        return [
            f"{spot}.routing_entropy exceeds ln({support}) — not a "
            "distribution over these experts"
        ]
    return []


def _check_layer_signals(
    layer: dict[str, Any], spot: str, expert_count: int | None,
    top_k: int | None = None,
) -> list[str]:
    """The routed experts, their logits, and the summaries derived from them."""

    exposed_logits = _exposed_logits(layer)
    return (
        _check_layer_experts(layer, spot, expert_count, top_k)
        + _check_layer_logits(layer, spot, expert_count)
        + _check_layer_margin(layer, spot, exposed_logits)
        + _check_layer_entropy(layer, spot, exposed_logits, expert_count)
    )


def _check_expert_agreement_range(routing: dict[str, Any], where: str) -> list[str]:
    """expert_agreement is a fraction, so it lives in [0, 1]."""

    agreement = routing.get("expert_agreement")
    if not oc.is_number(agreement) or not 0.0 <= float(agreement) <= 1.0:
        return [f"{where}.result.routing.expert_agreement must be in [0, 1]"]
    return []


def _layer_top_experts(layers: list[Any]) -> list[int]:
    """The top-1 expert of every layer that recorded a usable one."""

    return [
        layer["top_k_experts"][0]
        for layer in layers
        if isinstance(layer, dict)
        and isinstance(layer.get("top_k_experts"), list)
        and layer["top_k_experts"]
        and isinstance(layer["top_k_experts"][0], int)
        and not isinstance(layer["top_k_experts"][0], bool)
    ]


def _check_modal_agreement(
    result: dict[str, Any], routing: dict[str, Any], tops: list[int], where: str
) -> list[str]:
    """Compare the recorded label and agreement against the modal top-1 expert."""

    errors: list[str] = []
    try:
        modal, count = Counter(tops).most_common(1)[0]
    except (TypeError, ValueError):
        errors.append(f"{where}.result.routing: cannot compute top1_expert from invalid layer data")
        modal, count = None, 0
    if modal is None:
        return errors
    if result.get("top1_expert") != modal:
        errors.append(
            f"{where}.result.top1_expert is {result.get('top1_expert')!r} but the "
            f"recorded layers route to {modal!r}"
        )
    if routing.get("top1_expert") != modal:
        errors.append(
            f"{where}.result.routing.top1_expert disagrees with its own layers"
        )
    agreement = routing.get("expert_agreement")
    expected_agreement = count / len(tops)
    if oc.is_number(agreement) and abs(float(agreement) - expected_agreement) > 1e-6:
        errors.append(
            f"{where}.result.routing.expert_agreement is {agreement} but the "
            f"recorded layers agree {expected_agreement:.6f} of the time"
        )
    return errors


def _check_derived_routing_labels(
    result: dict[str, Any], routing: dict[str, Any], layers: list[Any], where: str
) -> list[str]:
    """Recompute the distillation label and agreement from the recorded layers.

    The distillation label and the summary statistics are derived, not
    independent facts. Recompute them from the layers the oracle recorded, so
    a fabricated top-1 expert cannot be trained on.
    """

    errors = _check_expert_agreement_range(routing, where)
    errors += _check_summary_label_types(result, routing, where)
    tops = _layer_top_experts(layers)
    if len(tops) == len(layers) and tops:
        errors += _check_modal_agreement(result, routing, tops, where)
    return errors


def _check_summary_label_types(
    result: dict[str, Any], routing: dict[str, Any], where: str
) -> list[str]:
    """Both summary labels must be genuine integers, never booleans.

    When the modal expert is 0 or 1, a JSON boolean passes the modal equality
    checks (``False == 0`` and ``True == 1``), yet ``router_baseline``'s
    ``_genuine_int`` rejects it and silently drops the sample — so a record
    that validates cleanly here could still skew the baseline and the SNN
    escalation verdict by vanishing from it.
    """

    return [
        f"{where}.{field} must be a genuine integer expert id, got {value!r}"
        for field, value in (
            ("result.top1_expert", result.get("top1_expert")),
            ("result.routing.top1_expert", routing.get("top1_expert")),
        )
        if not isinstance(value, int) or isinstance(value, bool)
    ]


def _check_measurement_reconciliation(
    result: dict[str, Any], routing: dict[str, Any], layers: list[Any], where: str
) -> list[str]:
    """Reconcile the compact targets with the routing they summarise.

    The compact targets in result.measurements describe the last layer and
    the cross-layer agreement.
    """

    errors: list[str] = []
    last = layers[-1] if isinstance(layers[-1], dict) else {}
    expected_measurements = {
        "top1_top2_margin": last.get("top1_top2_margin"),
        "routing_entropy": last.get("routing_entropy"),
        "expert_agreement": routing.get("expert_agreement"),
    }
    measurements = result.get("measurements")
    reconciled: set[str] = set()
    for item in measurements if isinstance(measurements, list) else []:
        if not isinstance(item, dict):
            continue
        quantity = item.get("quantity")
        if not isinstance(quantity, str):
            # An unhashable quantity raised TypeError out of the dict lookup
            # and aborted validation of the whole run; the shared measurement
            # checker already reports the malformed item as a finding.
            continue
        expected = expected_measurements.get(quantity)
        if expected is None or not oc.is_number(expected):
            continue
        if not oc.is_number(item.get("value")):
            continue
        if oc.is_true(item.get("measured")):
            # A `measured: false` reading is a modelled value wearing a
            # promised router target's name — it does not satisfy the
            # completeness requirement below.
            reconciled.add(quantity)
        if abs(float(item["value"]) - float(expected)) > 1e-6:
            errors.append(
                f"{where}.result: measured {quantity} is {item['value']} but the "
                f"recorded routing says {expected}"
            )
    return errors + _missing_promised_measurements(
        expected_measurements, reconciled, where
    )


def _missing_promised_measurements(
    expected_measurements: dict[str, Any], reconciled: set[str], where: str
) -> list[str]:
    """Every promised compact target must be present, not just the survivors.

    Validating only the readings that happen to be present would let a record
    delete ``routing_entropy`` and ``expert_agreement`` while keeping its
    digest and curation eligibility — measurement-based consumers would
    silently lose two of the three promised router targets.
    """

    return [
        f"{where}.result.measurements must record {quantity} as a measured "
        "numeric reading — the recorded routing promises it"
        for quantity, expected in sorted(expected_measurements.items())
        if oc.is_number(expected) and quantity not in reconciled
    ]


def _check_declared_count_authority(
    expert_count: int | None, oracle: Any, where: str
) -> list[str]:
    if (
        expert_count is None
        and isinstance(oracle, dict)
        and oracle.get("authority") == oc.AUTHORITY_AUTHORITATIVE
    ):
        # Without a declared count the per-layer range check is disabled, so
        # an authoritative recording with no logits could carry expert ids
        # like [-1, 999] straight into curation.
        return [
            f"{where}.oracle.fingerprint.num_local_experts must declare a "
            "positive expert count for an authoritative router record — "
            "without it the routed expert ids cannot be range-checked"
        ]
    return []


def _check_routing_layers(
    layers: list[Any], expert_count: int | None, top_k: int | None, where: str
) -> list[str]:
    errors: list[str] = []
    order = _LayerOrder()
    for index, layer in enumerate(layers):
        spot = f"{where}.result.routing.layers[{index}]"
        if not isinstance(layer, dict):
            errors.append(f"{spot} must be an object")
            continue
        errors += _check_layer_index(layer, spot, order)
        errors += _check_layer_signals(layer, spot, expert_count, top_k)
    return errors


def _check_declared_trajectory_authority(
    fingerprint: Any, oracle: Any, where: str
) -> list[str]:
    """An authoritative router must declare its top-k width and layer count.

    Both equality checks are conditional on the declaration being present, so
    deleting ``num_experts_per_tok`` freed every layer to widen its top-k and
    deleting ``num_layers`` let a contiguous suffix vanish — while the record
    stayed validation-clean and curation-eligible.
    """

    if not (
        isinstance(oracle, dict)
        and oracle.get("authority") == oc.AUTHORITY_AUTHORITATIVE
    ):
        return []
    return [
        f"{where}.oracle.fingerprint.{field} must declare a positive value "
        f"for an authoritative router record — without it {consequence}"
        for field, declared, consequence in (
            (
                "num_experts_per_tok",
                _declared_top_k(fingerprint),
                "the recorded top-k width cannot be checked",
            ),
            (
                "num_layers",
                _declared_layer_count(fingerprint),
                "a dropped layer suffix cannot be detected",
            ),
        )
        if declared is None
    ]


def _check_layer_count(
    layers: list[Any], fingerprint: Any, where: str
) -> list[str]:
    """The recorded trajectory length against the declared layer count.

    Contiguity alone still lets a suffix vanish: a record keeping layers
    [0, 1] of a four-layer teacher looks ordered while ``router_baseline``
    reads a mid-network decision as the last-layer target.
    """

    declared = _declared_layer_count(fingerprint)
    if declared is not None and len(layers) != declared:
        return [
            f"{where}.result.routing.layers has {len(layers)} layers but the "
            f"oracle fingerprint declares num_layers {declared} — a dropped "
            "suffix would change the last-layer target"
        ]
    return []


def check_family(record: dict[str, Any], where: str) -> list[str]:
    """Family checks: real routing, recorded teacher identity, sane targets."""

    errors = _check_scenario_context(record.get("scenario"), where)

    oracle = record.get("oracle")
    fingerprint = oracle.get("fingerprint") if isinstance(oracle, dict) else None
    errors += _check_teacher_fingerprint(oracle, fingerprint, where)

    result = record.get("result")
    if not isinstance(result, dict):
        return errors + [f"{where}.result must be an object"]
    errors += _check_teacher_grounding(result, oracle, fingerprint, where)

    routing = result.get("routing")
    if not isinstance(routing, dict):
        return errors + [f"{where}.result.routing must be an object"]
    layers = routing.get("layers")
    if not isinstance(layers, list) or not layers:
        return errors + [f"{where}.result.routing.layers must be a non-empty array"]

    expert_count = _declared_expert_count(fingerprint)
    errors += _check_declared_count_authority(expert_count, oracle, where)
    errors += _check_declared_trajectory_authority(fingerprint, oracle, where)
    errors += _check_authoritative_checkpoint(oracle, fingerprint, where)
    errors += _check_routing_layers(
        layers, expert_count, _declared_top_k(fingerprint), where
    )
    errors += _check_layer_count(layers, fingerprint, where)
    errors += _check_derived_routing_labels(result, routing, layers, where)
    errors += _check_measurement_reconciliation(result, routing, layers, where)
    return errors


def main(argv: list[str] | None = None) -> int:
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
