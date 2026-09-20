#!/usr/bin/env python3
"""Recorded-teacher router oracle for ``sparse-moe-router-routing``.

Split out of ``moe_oracles.py`` verbatim: :class:`RecordedTeacherRouter`, the
oracle that replays routing recorded from a real teacher run — the only one
whose records can earn an ``authoritative`` label, so every teacher-identity
guard lives here. Re-exported through ``moe_oracles`` / ``moe_router`` so call
sites resolve unchanged.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any

_PIPELINES = Path(__file__).resolve().parent
if str(_PIPELINES) not in sys.path:
    sys.path.insert(0, str(_PIPELINES))

from oracle_grounded import distill_contract as oc  # noqa: E402

if __package__:
    from .moe_featurizer import COMMIT_SHA_RE, NON_TEACHER_ORACLE_NAMES
    from .moe_layers import (
        LayerRouting,
        RouterObservation,
        _check_layer_count,
        _check_routing_layers,
        _declared_expert_count,
        _declared_positive_int,
        _declared_top_k,
    )
    from .moe_oracle_types import RouterOracle, _summarise
else:
    from moe_featurizer import COMMIT_SHA_RE, NON_TEACHER_ORACLE_NAMES
    from moe_layers import (
        LayerRouting,
        RouterObservation,
        _check_layer_count,
        _check_routing_layers,
        _declared_expert_count,
        _declared_positive_int,
        _declared_top_k,
    )
    from moe_oracle_types import RouterOracle, _summarise


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

    def _missing_teacher_fields_problem(self) -> str | None:
        missing = [
            field
            for field in ("model", "revision_or_checkpoint", "configuration_sha256")
            if not self.teacher.get(field)
        ]
        if missing:
            return f"recording is missing teacher fields: {sorted(missing)}"
        return None

    def _mutable_revision_problem(self) -> str | None:
        revision = self.teacher.get("revision_or_checkpoint")
        if isinstance(revision, str) and COMMIT_SHA_RE.match(revision.strip()):
            return None
        # A branch or tag is not a checkpoint: the same name can serve
        # different weights tomorrow while the configuration digest stays
        # the same, so replayed labels would share one teacher identity
        # across revisions.
        return (
            f"recording names a mutable revision {revision!r}; a replayed "
            "teacher must pin a resolved 40-hex commit"
        )

    def _teacher_claim_problem(self) -> str | None:
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
        return None

    def _teacher_field_problem(self, field: str, consequence: str) -> str | None:
        if _declared_positive_int(self.teacher, field) is None:
            return (
                f"recording does not declare a positive {field}, so "
                f"{consequence}"
            )
        return None

    def _teacher_shape_problem(self) -> str | None:
        # Without these declarations nothing bounds the replayed routing: a
        # recording with no logits could serve ids like [-1, 999], widen its
        # top-k, or drop a layer suffix, all as authoritative labels.
        for field, consequence in (
            ("num_local_experts", "replayed expert ids cannot be range-checked"),
            ("num_experts_per_tok", "the replayed top-k width cannot be checked"),
            ("num_layers", "a dropped layer suffix cannot be detected"),
        ):
            problem = self._teacher_field_problem(field, consequence)
            if problem is not None:
                return problem
        return None

    def _teacher_identity_problem(self) -> str | None:
        """Why the recorded teacher identity cannot ground labels, if any."""

        for check in (
            self._missing_teacher_fields_problem,
            self._mutable_revision_problem,
            self._teacher_claim_problem,
            self._teacher_shape_problem,
        ):
            problem = check()
            if problem is not None:
                return problem
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

    def _require_recorded_layer_fields(self, layer: Any) -> int:
        """The layer index of a well-formed recorded layer."""
        if not isinstance(layer, dict):
            raise oc.OracleUnavailable(self.name, "layer must be an object")
        for field in ("top1_top2_margin", "routing_entropy"):
            if not oc.is_number(layer.get(field)):
                raise oc.OracleUnavailable(
                    self.name, f"layer missing {field}"
                )
        layer_index = layer.get("layer")
        if not oc.is_genuine_int(layer_index):
            # int() silently rewrote 0.9 to 0 and True to 1, normalising
            # malformed recording metadata into a validation-clean trajectory
            # instead of failing closed at the replay boundary.
            raise oc.OracleUnavailable(
                self.name,
                f"layer index must be a genuine integer, got {layer_index!r}",
            )
        return layer_index

    def _recorded_layer(self, layer: Any) -> LayerRouting:
        return self._routing_from_recorded(
            layer, self._require_recorded_layer_fields(layer)
        )

    def _routing_from_recorded(
        self, layer: dict[str, Any], layer_index: int
    ) -> LayerRouting:
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

