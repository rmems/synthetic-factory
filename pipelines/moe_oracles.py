#!/usr/bin/env python3
"""Teacher oracles for ``moe-router-distillation-trajectories``.

Split out of ``moe_router.py`` verbatim: ``ReferenceMoERouter`` and
``TransformersMoERouter`` plus the ``oracles`` report — the ``RouterOracle``
boundary lives in ``moe_oracle_types`` and the recorded-teacher oracle in
``moe_teacher_router``. Every name here is re-exported from ``moe_router`` so
existing call sites resolve unchanged.
"""

from __future__ import annotations

import hashlib
import importlib
import random
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

_PIPELINES = Path(__file__).resolve().parent
if str(_PIPELINES) not in sys.path:
    sys.path.insert(0, str(_PIPELINES))

from oracle_grounded import distill_contract as oc  # noqa: E402


if __package__:
    from .moe_featurizer import (
        FAMILY,
        FEATURE_DIM,
        entropy_nats,
        featurize,
        resolve_checkpoint,
        softmax,
    )
    from .moe_layers import (
        LayerRouting,
        RouterObservation,
        _declared_expert_count,
        _declared_top_k,
    )
    from .moe_oracle_types import RouterOracle, _summarise
    from .moe_teacher_router import RecordedTeacherRouter
else:
    from moe_featurizer import (
        FAMILY,
        FEATURE_DIM,
        entropy_nats,
        featurize,
        resolve_checkpoint,
        softmax,
    )
    from moe_layers import (
        LayerRouting,
        RouterObservation,
        _declared_expert_count,
        _declared_top_k,
    )
    from moe_oracle_types import RouterOracle, _summarise
    from moe_teacher_router import RecordedTeacherRouter




@dataclass(frozen=True)
class GateShape:
    """The reference gate's geometry: width, depth, fan-out, feature dim."""

    num_experts: int = 8
    num_layers: int = 4
    top_k: int = 2
    dim: int = FEATURE_DIM

    def __post_init__(self) -> None:
        if self.top_k < 2:
            raise oc.ContractError("top_k must be >= 2 to define a top1/top2 margin")
        if self.num_experts <= self.top_k:
            raise oc.ContractError("num_experts must exceed top_k")
        if self.num_layers < 1:
            # A layerless router builds an empty routing list and `_summarise`
            # then fails indexing `Counter(...).most_common(1)[0]`. Fail here
            # with a bounded contract error instead of crashing generation.
            raise oc.ContractError("num_layers must be >= 1")


class ReferenceMoERouter(RouterOracle):
    """Deterministic seeded top-k gate. Real computation, not an LLM teacher."""

    name = "reference_moe_router"
    version = "1.0.0"
    oracle_type = "reference_model_router"
    authority = oc.AUTHORITY_REFERENCE_ONLY
    implementation = "pipelines/moe_router.py:ReferenceMoERouter"
    is_llm_teacher = False

    def __init__(self, *, seed: int = 7, shape: GateShape = GateShape()) -> None:
        self.seed = seed
        self.shape = shape
        self.num_experts = shape.num_experts
        self.num_layers = shape.num_layers
        self.top_k = shape.top_k
        self.dim = shape.dim
        rng = random.Random(seed)  # nosec B311 - reproducible reference weights
        self.gates: list[list[list[float]]] = [
            [
                [rng.gauss(0.0, 1.0) for _ in range(shape.dim)]
                for _ in range(shape.num_experts)
            ]
            for _ in range(shape.num_layers)
        ]
        self.biases: list[list[float]] = [
            [rng.gauss(0.0, 0.35) for _ in range(shape.num_experts)]
            for _ in range(shape.num_layers)
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
            order = sorted(
                range(self.num_experts),
                key=lambda e, logits=logits: (-logits[e], e),
            )
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



@dataclass(frozen=True)
class TeacherLoadOptions:
    """Optional load-time overrides for the live teacher checkpoint."""

    revision: str | None = None
    device: str = "cpu"
    top_k: int | None = None


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
        self, model_id: str, *, options: TeacherLoadOptions | None = None
    ) -> None:
        options = options or TeacherLoadOptions()
        self.model_id = model_id
        self.revision = options.revision
        self.device = options.device
        self.top_k = options.top_k
        self._model = None
        self._tokenizer = None
        self._fingerprint: dict[str, Any] | None = None

    def available(self) -> tuple[bool, str]:
        try:
            importlib.import_module("torch")
            importlib.import_module("transformers")
        except Exception as exc:  # pragma: no cover - depends on the host
            return False, f"{type(exc).__name__}: {exc}"
        return True, "torch and transformers import"

    def _load(self):  # pragma: no cover - requires a real checkpoint
        if self._model is not None:
            return self._model, self._tokenizer
        # Resolve before even probing the optional runtime. A mutable branch
        # can resolve to a commit after download, but that is too late to pin
        # the bytes fetched.
        pinned_revision = resolve_checkpoint(self.revision, None)
        ok, detail = self.available()
        if not ok:
            raise oc.OracleUnavailable(self.name, detail)
        import torch
        import transformers
        from transformers import AutoModelForCausalLM, AutoTokenizer

        tokenizer = AutoTokenizer.from_pretrained(  # nosec B615 - validated 40-hex pin
            self.model_id, revision=pinned_revision
        )
        model = AutoModelForCausalLM.from_pretrained(  # nosec B615 - validated 40-hex pin
            self.model_id, revision=pinned_revision
        )
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
            "transformers_version": transformers.__version__,
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

    def _effective_top_k(self) -> int:
        """An override may restate, but cannot contradict, checkpoint routing."""

        declared = _declared_top_k(self._fingerprint)
        experts = _declared_expert_count(self._fingerprint)
        if not _valid_routing_width(declared, experts):
            raise oc.OracleUnavailable(self.name, "checkpoint has invalid routing width")
        if not _valid_top_k_override(self.top_k, declared):
            raise oc.OracleUnavailable(self.name, "top_k override differs from checkpoint routing width")
        return declared

    def route(self, text: str) -> RouterObservation:  # pragma: no cover - no checkpoint
        model, tokenizer = self._load()
        top_k = self._effective_top_k()
        import torch

        inputs = tokenizer(text, return_tensors="pt").to(self.device)
        with torch.no_grad():
            outputs = model(**inputs, output_router_logits=True)
        router_logits = getattr(outputs, "router_logits", None)
        if not router_logits:
            raise oc.OracleUnavailable(
                self.name, f"{self.model_id} returned no router_logits"
            )
        layers: list[LayerRouting] = []
        for index, layer_logits in enumerate(router_logits):
            # transformers returns (tokens, experts) per layer; read the last
            # position so one context yields one routing decision per layer.
            values = [float(value) for value in layer_logits[-1].tolist()]
            order = sorted(
                range(len(values)),
                key=lambda e, values=values: (-values[e], e),
            )
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


def _valid_routing_width(declared: Any, experts: Any) -> bool:
    """The checkpoint must declare a top_k inside its expert count."""

    if declared is None or experts is None:
        return False
    return declared <= experts


def _valid_top_k_override(top_k: Any, declared: int) -> bool:
    """None means no override; a genuine int must restate the checkpoint."""

    if top_k is None:
        return True
    if not oc.is_genuine_int(top_k):
        return False
    return top_k == declared


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
