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
    ``reference_only``, are excluded by ``oracle_contract.curation_eligible``,
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
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

_PIPELINES = Path(__file__).resolve().parent
if str(_PIPELINES) not in sys.path:
    sys.path.insert(0, str(_PIPELINES))

import oracle_contract as oc  # noqa: E402

FAMILY = "moe-router-distillation-trajectories"
GENERATOR_NAME = "context-corpus-generator"
GENERATOR_VERSION = "1.0.0"

FEATURE_DIM = 48
COMPACT_DIM = 16
# compact_view appends tail mean/energy/max/min to the leading components.
COMPACT_SUMMARY_STATS = 4

# Oracles that compute real routing but are not language-model teachers. A
# recording may never name one of these as the teacher it replays.
NON_TEACHER_ORACLE_NAMES = frozenset({"reference_moe_router"})

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
            self.name,
            oracle_type=self.oracle_type,
            implementation=self.implementation,
            version=self.version,
            authority=self.authority,
            configuration=self.configuration(),
            seed=getattr(self, "seed", None),
            commit=None,
            fingerprint=self.fingerprint(),
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

    def __init__(
        self,
        *,
        seed: int = 7,
        num_experts: int = 8,
        num_layers: int = 4,
        top_k: int = 2,
        dim: int = FEATURE_DIM,
    ) -> None:
        if top_k < 2:
            raise oc.ContractError("top_k must be >= 2 to define a top1/top2 margin")
        if num_experts <= top_k:
            raise oc.ContractError("num_experts must exceed top_k")
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

    def available(self) -> tuple[bool, str]:
        missing = [
            field
            for field in ("model", "revision_or_checkpoint", "configuration_sha256")
            if not self.teacher.get(field)
        ]
        if missing:
            return False, f"recording is missing teacher fields: {sorted(missing)}"
        if not self.is_llm_teacher:
            return False, (
                "recording does not declare is_llm_teacher: true — a recorded "
                "replay may only ground labels for a real teacher run"
            )
        model = self.teacher.get("model")
        if isinstance(model, str) and model in NON_TEACHER_ORACLE_NAMES:
            return False, (
                f"recording names {model!r} as its teacher, which is a "
                "non-teacher stand-in; its routing may not be curated as "
                "teacher truth"
            )
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
        return {"is_llm_teacher": self.is_llm_teacher, **self.teacher}

    def route(self, text: str) -> RouterObservation:
        entry = self.observations.get(self.key_for(text))
        if not isinstance(entry, dict) or not isinstance(entry.get("layers"), list):
            raise oc.OracleUnavailable(
                self.name,
                f"no recorded routing for context sha256 {self.key_for(text)}",
            )
        layers = [
            LayerRouting(
                layer=int(layer["layer"]),
                top_k_experts=tuple(int(value) for value in layer["top_k_experts"]),
                router_logits=(
                    tuple(float(value) for value in layer["router_logits"])
                    if layer.get("router_logits") is not None
                    else None
                ),
                top1_top2_margin=float(layer["top1_top2_margin"]),
                routing_entropy=float(layer["routing_entropy"]),
            )
            for layer in entry["layers"]
        ]
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
            "revision_or_checkpoint": self.revision or "main",
            "configuration_sha256": hashlib.sha256(
                config.to_json_string().encode("utf-8")
            ).hexdigest(),
            "num_local_experts": getattr(config, "num_local_experts", None)
            or getattr(config, "num_experts", None),
            "num_experts_per_tok": getattr(config, "num_experts_per_tok", None),
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
                        "featurizer": "blake2b-char-trigram-hashing/1.0.0",
                        "feature_dim": FEATURE_DIM,
                        "compact_dim": COMPACT_DIM,
                        "view": "leading components + tail mean/energy/max/min",
                        "features": compact_view(features),
                    },
                },
            }
        )
    return proposals


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
        GENERATOR_NAME, version=GENERATOR_VERSION, kind="programmatic", seed=seed
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
        routing = observation.as_dict()
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
        result = oc.new_result(
            measurements=measurements,
            routing=routing,
            top1_expert=observation.top1_expert,
            is_llm_teacher=bool(engine.is_llm_teacher),
            teacher_grounded=bool(
                engine.is_llm_teacher
                and oracle_block["authority"] == oc.AUTHORITY_AUTHORITATIVE
            ),
        )
        records.append(
            oc.build_record(
                record_id=f"{id_prefix}-{seed}-{proposal['index']:04d}",
                family=FAMILY,
                generator=generator,
                scenario=scenario,
                oracle=oracle_block,
                result=result,
                provenance=oc.new_provenance("pipelines/moe_router.py"),
            )
        )
    return records


def check_family(record: dict[str, Any], where: str) -> list[str]:
    """Family checks: real routing, recorded teacher identity, sane targets."""

    errors: list[str] = []
    scenario = record.get("scenario")
    if isinstance(scenario, dict):
        context = scenario.get("context")
        if not isinstance(context, str) or not context.strip():
            errors.append(f"{where}.scenario.context must be a non-empty string")
        elif scenario.get("context_sha256") != hashlib.sha256(
            context.encode("utf-8")
        ).hexdigest():
            errors.append(f"{where}.scenario.context_sha256 does not match the context")
        compact = scenario.get("compact_input")
        if not isinstance(compact, dict):
            errors.append(f"{where}.scenario.compact_input must be an object")
        else:
            features = compact.get("features")
            if not isinstance(features, list) or not features:
                errors.append(
                    f"{where}.scenario.compact_input.features must carry the "
                    "student input the baseline is evaluated on"
                )
            elif not all(oc.is_number(value) for value in features):
                # router_baseline silently skips a record whose features are not
                # finite numbers, so without this a curated corpus could contain
                # no usable student input at all.
                errors.append(
                    f"{where}.scenario.compact_input.features must be finite "
                    "numbers — the baseline extractor drops anything else"
                )
            else:
                declared = compact.get("compact_dim")
                if isinstance(declared, int) and not isinstance(declared, bool):
                    expected = declared + COMPACT_SUMMARY_STATS
                    if len(features) != expected:
                        errors.append(
                            f"{where}.scenario.compact_input.features has "
                            f"{len(features)} values but compact_dim {declared} "
                            f"declares {expected}"
                        )

    oracle = record.get("oracle")
    fingerprint = oracle.get("fingerprint") if isinstance(oracle, dict) else None
    if not isinstance(fingerprint, dict):
        errors.append(
            f"{where}.oracle.fingerprint must record the teacher model, checkpoint "
            "and configuration"
        )
    else:
        for field in ("model", "revision_or_checkpoint", "configuration_sha256"):
            value = fingerprint.get(field)
            if not isinstance(value, str) or not value.strip():
                errors.append(f"{where}.oracle.fingerprint.{field} must be recorded")
        if not isinstance(fingerprint.get("is_llm_teacher"), bool):
            errors.append(
                f"{where}.oracle.fingerprint.is_llm_teacher must be a boolean"
            )
        if (
            isinstance(oracle, dict)
            and oracle.get("authority") == oc.AUTHORITY_AUTHORITATIVE
            and fingerprint.get("model") in NON_TEACHER_ORACLE_NAMES
        ):
            errors.append(
                f"{where}.oracle: LAUNDERED_REFERENCE_ORACLE — "
                f"{fingerprint.get('model')!r} is a non-teacher stand-in and may "
                "not be recorded as an authoritative teacher"
            )

    result = record.get("result")
    if not isinstance(result, dict):
        return errors + [f"{where}.result must be an object"]
    if not isinstance(result.get("is_llm_teacher"), bool):
        errors.append(f"{where}.result.is_llm_teacher must be a boolean")
    elif isinstance(fingerprint, dict) and isinstance(
        fingerprint.get("is_llm_teacher"), bool
    ):
        if result["is_llm_teacher"] != fingerprint["is_llm_teacher"]:
            errors.append(
                f"{where}.result.is_llm_teacher disagrees with the oracle fingerprint"
            )
    if isinstance(oracle, dict):
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

    routing = result.get("routing")
    if not isinstance(routing, dict):
        return errors + [f"{where}.result.routing must be an object"]
    layers = routing.get("layers")
    if not isinstance(layers, list) or not layers:
        return errors + [f"{where}.result.routing.layers must be a non-empty array"]
    expert_count: int | None = None
    if isinstance(fingerprint, dict):
        declared_experts = fingerprint.get("num_local_experts")
        if (
            isinstance(declared_experts, int)
            and not isinstance(declared_experts, bool)
            and declared_experts > 0
        ):
            expert_count = declared_experts
    seen_layers: set[int] = set()
    for index, layer in enumerate(layers):
        spot = f"{where}.result.routing.layers[{index}]"
        if not isinstance(layer, dict):
            errors.append(f"{spot} must be an object")
            continue
        layer_index = layer.get("layer")
        if not isinstance(layer_index, int) or isinstance(layer_index, bool):
            errors.append(f"{spot}.layer must be an integer")
        elif layer_index in seen_layers:
            errors.append(f"{spot}.layer {layer_index} is duplicated")
        else:
            seen_layers.add(layer_index)
        experts = layer.get("top_k_experts")
        if not isinstance(experts, list) or len(experts) < 2:
            errors.append(f"{spot}.top_k_experts must list at least the top two")
        elif len(set(experts)) != len(experts):
            errors.append(f"{spot}.top_k_experts must not repeat an expert")
        elif not all(
            isinstance(value, int) and not isinstance(value, bool) for value in experts
        ):
            errors.append(f"{spot}.top_k_experts must be integer expert ids")
        elif expert_count is not None and not all(
            0 <= value < expert_count for value in experts
        ):
            # Checked independently of router_logits, because a recorded
            # teacher may legitimately omit logits and would otherwise be free
            # to record ids like [-1, 999] as authoritative routing labels.
            errors.append(
                f"{spot}.top_k_experts must lie in [0, {expert_count}) — the "
                "expert count the oracle fingerprint declares"
            )
        logits = layer.get("router_logits")
        if logits is not None:
            if not isinstance(logits, list) or not all(
                oc.is_number(value) for value in logits
            ):
                errors.append(f"{spot}.router_logits must be an array of numbers")
            elif isinstance(experts, list) and experts:
                order = sorted(range(len(logits)), key=lambda e: (-logits[e], e))
                if list(experts[: len(experts)]) != order[: len(experts)]:
                    errors.append(
                        f"{spot}.top_k_experts disagrees with router_logits ordering"
                    )
        margin = layer.get("top1_top2_margin")
        if not oc.is_number(margin) or float(margin) < 0.0:
            errors.append(f"{spot}.top1_top2_margin must be a non-negative number")
        routing_entropy = layer.get("routing_entropy")
        if not oc.is_number(routing_entropy) or float(routing_entropy) < 0.0:
            errors.append(f"{spot}.routing_entropy must be a non-negative number")
        else:
            # Bound the entropy by ln(num_experts). Prefer this layer's logit
            # width, falling back to the recorded expert count so an oracle
            # that exposes no logits still cannot report an impossible entropy.
            # Kept separate from `expert_count` so one layer's logit width does
            # not become the id range every later layer is checked against.
            support = len(logits) if isinstance(logits, list) and logits else expert_count
            if support and float(routing_entropy) > math.log(support) + 1e-6:
                errors.append(
                    f"{spot}.routing_entropy exceeds ln({support}) — not a "
                    "distribution over these experts"
                )
    agreement = routing.get("expert_agreement")
    if not oc.is_number(agreement) or not 0.0 <= float(agreement) <= 1.0:
        errors.append(f"{where}.result.routing.expert_agreement must be in [0, 1]")

    # The distillation label and the summary statistics are derived, not
    # independent facts. Recompute them from the layers the oracle recorded, so
    # a fabricated top-1 expert cannot be trained on.
    tops = [
        layer["top_k_experts"][0]
        for layer in layers
        if isinstance(layer, dict)
        and isinstance(layer.get("top_k_experts"), list)
        and layer["top_k_experts"]
    ]
    if len(tops) == len(layers) and tops:
        modal, count = Counter(tops).most_common(1)[0]
        if result.get("top1_expert") != modal:
            errors.append(
                f"{where}.result.top1_expert is {result.get('top1_expert')!r} but the "
                f"recorded layers route to {modal!r}"
            )
        if routing.get("top1_expert") != modal:
            errors.append(
                f"{where}.result.routing.top1_expert disagrees with its own layers"
            )
        expected_agreement = count / len(tops)
        if oc.is_number(agreement) and abs(float(agreement) - expected_agreement) > 1e-6:
            errors.append(
                f"{where}.result.routing.expert_agreement is {agreement} but the "
                f"recorded layers agree {expected_agreement:.6f} of the time"
            )

    # The compact targets in result.measurements describe the last layer and
    # the cross-layer agreement. Reconcile them with the routing they summarise.
    last = layers[-1] if isinstance(layers[-1], dict) else {}
    expected_measurements = {
        "top1_top2_margin": last.get("top1_top2_margin"),
        "routing_entropy": last.get("routing_entropy"),
        "expert_agreement": agreement,
    }
    measurements = result.get("measurements")
    for item in measurements if isinstance(measurements, list) else []:
        if not isinstance(item, dict):
            continue
        quantity = item.get("quantity")
        expected = expected_measurements.get(quantity)
        if expected is None or not oc.is_number(expected):
            continue
        if not oc.is_number(item.get("value")):
            continue
        if abs(float(item["value"]) - float(expected)) > 1e-6:
            errors.append(
                f"{where}.result: measured {quantity} is {item['value']} but the "
                f"recorded routing says {expected}"
            )
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
