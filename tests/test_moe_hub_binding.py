#!/usr/bin/env python3
"""Sealed Hub card / teacher-logits / revision binding gap tests.

Split out of ``test_moe_router.py``: the fail-closed binding between the sealed
Hub card fingerprint and the replayed routing trajectory.
"""

import json
import math
import sys
import unittest
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "pipelines"))

from test_moe_router import mr, oc  # noqa: E402


def _distinct_top_k(preferred, num_experts, top_k):
    """Top-``k`` experts: the record's own picks first, then successors."""

    top = [min(e, num_experts - 1) for e in preferred[:top_k]]
    while len(top) < top_k:
        candidate = (top[-1] + 1) % num_experts if top else 0
        top.append(candidate if candidate not in top else (candidate + 1) % num_experts)
    return top


class SealedHubMoEBinding(unittest.TestCase):
    """Fail-closed sealed Hub card / teacher-logits / revision binding."""

    MIXTRAL = "mistralai/Mixtral-8x7B-Instruct-v0.1"
    MIXTRAL_CONFIG_SHA = "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"

    @staticmethod
    def _mixtral_layer(template, index, shape, with_logits):
        layer = json.loads(json.dumps(template))
        layer["layer"] = index
        if not with_logits:
            layer.pop("router_logits", None)
            layer["top_k_experts"] = list(range(shape.top_k))
            return layer

        top = _distinct_top_k(
            layer["top_k_experts"], shape.num_experts, shape.top_k
        )
        logits = [-5.0] * shape.num_experts
        for rank, expert in enumerate(top):
            logits[expert] = 10.0 - 0.01 * rank
        layer["top_k_experts"] = top
        layer["router_logits"] = logits
        ordered = sorted(logits, reverse=True)
        layer["top1_top2_margin"] = round(ordered[0] - ordered[1], 6)
        layer["routing_entropy"] = round(-sum(
            probability * math.log(probability)
            for probability in mr.softmax(logits)
            if probability > 0.0
        ), 6)
        return layer

    def _mixtral_layers(self, record, shape, with_logits):
        # Expand to Mixtral depth when needed by repeating the last honest layer
        # shape with contiguous indices (tests that only care about cardinality
        # / revision / logits presence do not need a real Mixtral run).
        base_layers = record["result"]["routing"]["layers"]
        template = json.loads(json.dumps(base_layers[0]))
        return [
            self._mixtral_layer(template, index, shape, with_logits)
            for index in range(shape.num_layers)
        ]

    def _write_teacher_identity(self, record, shape, revision):
        oracle = record["oracle"]
        oracle["authority"] = oc.AUTHORITY_AUTHORITATIVE
        oracle["name"] = "mixtral-8x7b-instruct"
        oracle["type"] = "real_model_router"
        oracle["implementation"] = mr.TRANSFORMERS_MOE_IMPLEMENTATION
        oracle["fingerprint"] = {
            "model": self.MIXTRAL,
            "revision_or_checkpoint": revision,
            "configuration_sha256": self.MIXTRAL_CONFIG_SHA,
            "is_llm_teacher": True,
            "num_local_experts": shape.num_experts,
            "num_experts_per_tok": shape.top_k,
            "num_layers": shape.num_layers,
        }

    @staticmethod
    def _write_teacher_result(record, layers):
        tops = [layer["top_k_experts"][0] for layer in layers]
        modal, count = Counter(tops).most_common(1)[0]
        result = record["result"]
        result["is_llm_teacher"] = True
        result["teacher_grounded"] = True
        result["routing"]["layers"] = layers
        result["routing"]["top1_expert"] = modal
        result["routing"]["expert_agreement"] = count / len(tops)
        result["top1_expert"] = modal
        # Drop measurements that would disagree with rewritten routing.
        result["measurements"] = []

    def _mixtral_authoritative(self, *, shape=None, revision=("a" * 40),
                               with_logits=True):
        # Build from a reference record then rewrite the oracle identity so the
        # scenario / derived labels stay internally consistent where possible.
        gate = shape or mr.GateShape(num_layers=32)
        record = json.loads(json.dumps(mr.build_records(3, 1)[0]))
        layers = self._mixtral_layers(record, gate, with_logits)
        self._write_teacher_identity(record, gate, revision)
        self._write_teacher_result(record, layers)
        return record

    def test_inflated_expert_cardinality_is_rejected(self):
        record = self._mixtral_authoritative(shape=mr.GateShape(num_layers=32, num_experts=32))
        errors = mr.check_family(record, "x")
        self.assertTrue(
            any("SEALED_HUB_MOE_CARDINALITY" in e and "num_local_experts" in e
                for e in errors),
            errors,
        )

    def test_deflated_layer_cardinality_is_rejected(self):
        record = self._mixtral_authoritative(shape=mr.GateShape(num_layers=2))
        errors = mr.check_family(record, "x")
        self.assertTrue(
            any("SEALED_HUB_MOE_CARDINALITY" in e and "num_layers" in e
                for e in errors),
            errors,
        )

    def test_fabricated_teacher_topk_without_logits_is_rejected(self):
        record = self._mixtral_authoritative(with_logits=False)
        errors = mr.check_family(record, "x")
        self.assertTrue(
            any("TEACHER_ROUTER_LOGITS_REQUIRED" in e for e in errors),
            errors,
        )

    def test_unbound_40hex_revision_is_rejected(self):
        record = self._mixtral_authoritative()
        errors = mr.check_family(record, "x")
        self.assertTrue(
            any("UNBOUND_HUB_REVISION" in e for e in errors),
            errors,
        )

    def test_mutable_main_revision_still_rejected(self):
        record = self._mixtral_authoritative(revision="main")
        errors = mr.check_family(record, "x")
        self.assertTrue(
            any("revision_or_checkpoint" in e and "main" in e for e in errors),
            errors,
        )

    def test_reference_records_still_may_omit_logits(self):
        record = mr.build_records(3, 1)[0]
        for layer in record["result"]["routing"]["layers"]:
            layer["router_logits"] = None
        self.assertEqual(mr.check_family(record, "x"), [])


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
