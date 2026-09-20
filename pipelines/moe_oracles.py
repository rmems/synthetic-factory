#!/usr/bin/env python3
"""Teacher oracles for ``moe-router-distillation-trajectories``.

Split out of ``moe_router.py`` verbatim: the ``RouterOracle`` boundary and its
three implementations — ``ReferenceMoERouter``, ``RecordedTeacherRouter``,
``TransformersMoERouter`` — plus the ``oracles`` report. Every name here is
re-exported from ``moe_router`` so existing call sites resolve unchanged.
"""

from __future__ import annotations

import hashlib
import json
import random
import sys
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

_PIPELINES = Path(__file__).resolve().parent
if str(_PIPELINES) not in sys.path:
    sys.path.insert(0, str(_PIPELINES))

from oracle_grounded import distill_contract as oc  # noqa: E402


if __package__:
    from .moe_featurizer import (
        COMMIT_SHA_RE,
        FAMILY,
        FEATURE_DIM,
        NON_TEACHER_ORACLE_NAMES,
        entropy_nats,
        featurize,
        resolve_checkpoint,
        softmax,
    )
    from .moe_layers import (
        LayerRouting,
        RouterObservation,
        _check_layer_count,
        _check_routing_layers,
        _declared_expert_count,
        _declared_positive_int,
        _declared_top_k,
    )
else:
    from moe_featurizer import (
        COMMIT_SHA_RE,
        FAMILY,
        FEATURE_DIM,
        NON_TEACHER_ORACLE_NAMES,
        entropy_nats,
        featurize,
        resolve_checkpoint,
        softmax,
    )
    from moe_layers import (
        LayerRouting,
        RouterObservation,
        _check_layer_count,
        _check_routing_layers,
        _declared_expert_count,
        _declared_positive_int,
        _declared_top_k,
    )



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
        rng = random.Random(seed)  # nosec B311 - reproducible reference weights
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
        # The operator names the recording; reading it is the method's purpose.
        return cls(json.loads(Path(path).read_text(encoding="utf-8")))  # NOSONAR

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

    def _require_recorded_dimensions(self, layers: list[Any]) -> None:
        problem = self._teacher_identity_problem()
        if problem is not None:
            raise oc.OracleUnavailable(self.name, problem)
        errors = _check_layer_count(layers, self.teacher, "recording")
        errors += _check_routing_layers(
            layers, _declared_expert_count(self.teacher),
            _declared_top_k(self.teacher), "recording",
        )
        if errors:
            raise oc.OracleUnavailable(self.name, "; ".join(errors))

    def route(self, text: str) -> RouterObservation:
        entry = self.observations.get(self.key_for(text))
        if not isinstance(entry, dict) or not isinstance(entry.get("layers"), list):
            raise oc.OracleUnavailable(
                self.name,
                f"no recorded routing for context sha256 {self.key_for(text)}",
            )
        layers = [self._recorded_layer(layer) for layer in entry["layers"]]
        self._require_recorded_dimensions(entry["layers"])
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
        # Resolve before even probing the optional runtime. A mutable branch
        # can resolve to a commit after download, but that is too late to pin
        # the bytes fetched.
        pinned_revision = resolve_checkpoint(self.revision, None)
        ok, detail = self.available()
        if not ok:
            raise oc.OracleUnavailable(self.name, detail)
        import torch
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

    def _effective_top_k(self) -> int:
        """An override may restate, but cannot contradict, checkpoint routing."""

        declared = _declared_top_k(self._fingerprint)
        experts = _declared_expert_count(self._fingerprint)
        if declared is None or experts is None or declared > experts:
            raise oc.OracleUnavailable(self.name, "checkpoint has invalid routing width")
        if self.top_k is not None and (
            not isinstance(self.top_k, int) or isinstance(self.top_k, bool)
            or self.top_k != declared
        ):
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
