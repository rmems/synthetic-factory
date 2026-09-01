#!/usr/bin/env python3
"""Training-audit coverage for raster/gate-SNN distillation readiness."""

import tempfile
import unittest
from pathlib import Path

from training_audit_test_helpers import (
    gate_snn_bridge,
    thalamic,
    write,
)

import training_audit

BRIDGE_FACTORY = "neuromorphic-event-language-bridge"
THALAMIC_FACTORY = "thalamic-trajectory-factory"
OUROBOROS_FACTORY = "multi-agent-ouroboros-swarm"


class DistillationRasterAudit(unittest.TestCase):
    """Raster coverage is distinct from Bridge-only event fidelity."""

    @staticmethod
    def _audit(factory, records, batch="batch-r01.jsonl"):
        temporary = tempfile.TemporaryDirectory()
        root = Path(temporary.name)
        write(root / factory / batch, records)
        return temporary, training_audit.audit_run(root)

    def _assert_mutation_blocks(
        self,
        *,
        record_id,
        mutate,
        metric_expectation,
        blocker_text,
    ):
        record = gate_snn_bridge(record_id)
        mutate(record)
        temporary, report = self._audit(BRIDGE_FACTORY, [record])
        temporary.cleanup()
        self.assertFalse(report["training_ready"])
        metric, expected = metric_expectation
        self.assertEqual(report["bridge"][metric], expected)
        self.assertTrue(
            any(blocker_text in item for item in report["blockers"]),
            report["blockers"],
        )

    def test_raster_backed_bridge_round_is_training_ready(self):
        temporary, report = self._audit(BRIDGE_FACTORY, [gate_snn_bridge()])
        with temporary:
            markdown = training_audit.render_markdown(report)

        self.assertTrue(report["training_ready"], report["blockers"])
        bridge = report["bridge"]
        self.assertEqual(bridge["pairs"], 1)
        self.assertEqual(bridge["distillation_records"], 1)
        self.assertEqual(bridge["raster_valid_pairs"], 1)
        self.assertEqual(bridge["raster_coverage_pct"], 100.0)
        self.assertEqual(bridge["raster_spikes"], 123)
        self.assertEqual(bridge["third_factor_pairs"], 1)
        self.assertEqual(bridge["gate_snn_records"], 1)
        self.assertEqual(bridge["gate_snn_valid_records"], 1)
        self.assertEqual(bridge["gate_snn_covered_batches"], 1)
        self.assertEqual(bridge["gate_snn_missing_batches"], 0)
        self.assertIn("Distillation rasters", markdown)

    def test_bridge_pair_without_raster_blocks_training(self):
        inner = thalamic("no-raster-inner")
        inner.pop("raster")
        inner.pop("gate_snn")
        bare = {
            "id": "no-raster-1",
            "spike_events": [
                {"channel": "a", "t_rel_ms": 1.0, "amplitude": 0.4},
                {"channel": "a", "t_rel_ms": 2.0, "amplitude": 0.5},
            ],
            "language_view": {"trajectory": inner},
        }
        temporary, report = self._audit(BRIDGE_FACTORY, [bare])
        temporary.cleanup()

        self.assertFalse(report["training_ready"])
        self.assertEqual(report["bridge"]["raster_missing_pairs"], 1)
        self.assertEqual(report["bridge"]["raster_coverage_pct"], 0)
        self.assertEqual(
            report["bridge"]["raster_missing_examples"],
            [f"{BRIDGE_FACTORY}/batch-r01.jsonl:1"],
        )
        blockers = " ".join(report["blockers"])
        self.assertIn("lack a 20-50 ms raster excerpt sidecar", blockers)
        self.assertIn("spike-implemented gate", blockers)

    def test_broken_spike_product_is_a_named_blocker(self):
        record = gate_snn_bridge("bad-budget-1")
        record["raster"]["spikes"] = 999
        temporary, report = self._audit(BRIDGE_FACTORY, [record])
        temporary.cleanup()

        self.assertFalse(report["training_ready"])
        self.assertEqual(report["bridge"]["raster_defect_pairs"], 1)
        self.assertEqual(
            report["bridge"]["raster_defect_codes"],
            {"BRIDGE_ENERGY_MISMATCH": 1, "BRIDGE_SPIKE_BUDGET_MISMATCH": 1},
        )
        self.assertTrue(
            any("spike-budget defects" in item for item in report["blockers"]),
            report["blockers"],
        )

    def test_raster_without_routing_table_blocks_training(self):
        self._assert_mutation_blocks(
            record_id="no-table-1",
            mutate=lambda record: record["raster"]["routing"].pop("table"),
            metric_expectation=("raster_routing_table_missing_pairs", 1),
            blocker_text="lack a routing table",
        )

    def test_window_needs_a_spike_implemented_gate(self):
        self._assert_mutation_blocks(
            record_id="no-gate-1",
            mutate=lambda record: record.pop("gate_snn"),
            metric_expectation=("gate_snn_records", 0),
            blocker_text="carry a spike-implemented gate",
        )

    def test_one_gate_snn_record_covers_the_whole_window(self):
        plain = gate_snn_bridge("plain-1")
        del plain["gate_snn"]
        temporary, report = self._audit(
            BRIDGE_FACTORY,
            [plain, gate_snn_bridge("gate-1")],
        )
        temporary.cleanup()

        self.assertTrue(report["training_ready"], report["blockers"])
        self.assertEqual(report["bridge"]["pairs"], 2)
        self.assertEqual(report["bridge"]["distillation_records"], 2)
        self.assertEqual(report["bridge"]["gate_snn_records"], 1)

    def test_gate_snn_coverage_is_required_in_every_batch(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            write(
                root / BRIDGE_FACTORY / "batch-r01.jsonl",
                [gate_snn_bridge("gate-1")],
            )
            plain = gate_snn_bridge("plain-2")
            del plain["gate_snn"]
            write(root / BRIDGE_FACTORY / "batch-r02.jsonl", [plain])
            report = training_audit.audit_run(root)

        bridge = report["bridge"]
        self.assertFalse(report["training_ready"])
        self.assertEqual(bridge["gate_snn_batches"], 2)
        self.assertEqual(bridge["gate_snn_covered_batches"], 1)
        self.assertEqual(bridge["gate_snn_missing_batches"], 1)
        self.assertEqual(
            bridge["gate_snn_missing_batch_examples"],
            [f"{BRIDGE_FACTORY}/batch-r02.jsonl"],
        )
        self.assertTrue(
            any("1/2 distillation batches" in item for item in report["blockers"]),
            report["blockers"],
        )

    def test_invalid_gate_snn_spec_is_a_blocker(self):
        record = gate_snn_bridge("bad-gate-1")
        record["gate_snn"]["populations"] = [{"name": "gate", "neurons": 0}]
        temporary, report = self._audit(BRIDGE_FACTORY, [record])
        temporary.cleanup()

        self.assertFalse(report["training_ready"])
        self.assertEqual(report["bridge"]["gate_snn_records"], 1)
        self.assertEqual(report["bridge"]["gate_snn_valid_records"], 0)
        self.assertEqual(report["bridge"]["raster_valid_pairs"], 1)
        self.assertEqual(report["bridge"]["raster_defect_pairs"], 0)
        self.assertEqual(report["bridge"]["raster_spikes"], 123)
        self.assertEqual(report["bridge"]["raster_defect_codes"], {})
        self.assertEqual(report["bridge"]["raster_coverage_pct"], 100.0)
        self.assertTrue(
            any("gate specs are invalid" in item for item in report["blockers"]),
            report["blockers"],
        )

    def test_gate_spike_mismatch_does_not_reduce_raster_coverage(self):
        record = gate_snn_bridge("bad-gate-spikes")
        record["gate_snn"]["populations"][0]["spikes"] += 10
        temporary, report = self._audit(BRIDGE_FACTORY, [record])
        temporary.cleanup()

        bridge = report["bridge"]
        self.assertFalse(report["training_ready"])
        self.assertEqual(bridge["gate_snn_valid_records"], 0)
        self.assertEqual(bridge["raster_valid_pairs"], 1)
        self.assertEqual(bridge["raster_coverage_pct"], 100.0)
        self.assertEqual(bridge["raster_defect_codes"], {})

    def test_raster_and_gate_defects_remain_separately_accounted(self):
        record = gate_snn_bridge("bad-raster-and-gate")
        record["raster"]["spikes"] = 999
        record["gate_snn"]["populations"] = [{"name": "gate", "neurons": 0}]
        temporary, report = self._audit(BRIDGE_FACTORY, [record])
        temporary.cleanup()

        bridge = report["bridge"]
        self.assertFalse(report["training_ready"])
        self.assertEqual(bridge["gate_snn_valid_records"], 0)
        self.assertEqual(bridge["raster_valid_pairs"], 0)
        self.assertEqual(bridge["raster_coverage_pct"], 0)
        self.assertEqual(
            bridge["raster_defect_codes"],
            {"BRIDGE_ENERGY_MISMATCH": 1, "BRIDGE_SPIKE_BUDGET_MISMATCH": 1},
        )

    def test_other_factory_thalamic_record_is_not_distillation_data(self):
        temporary, report = self._audit("other-factory", [thalamic("t-1")])
        temporary.cleanup()

        self.assertTrue(report["training_ready"], report["blockers"])
        self.assertEqual(report["bridge"]["pairs"], 0)
        self.assertEqual(report["bridge"]["distillation_records"], 0)
        self.assertEqual(report["bridge"]["raster_coverage_pct"], 0)

    def test_ouroboros_thalamic_record_is_distillation_data(self):
        record = thalamic("ouroboros-no-raster")
        record.pop("raster")
        record.pop("gate_snn")
        temporary, report = self._audit(OUROBOROS_FACTORY, [record])
        temporary.cleanup()

        self.assertFalse(report["training_ready"])
        self.assertEqual(report["bridge"]["distillation_records"], 1)
        self.assertEqual(report["bridge"]["raster_missing_pairs"], 1)
        self.assertTrue(
            any("lack a 20-50 ms raster" in item for item in report["blockers"]),
            report["blockers"],
        )
        self.assertTrue(
            any("raster-gated distillation records" in item for item in report["blockers"]),
            report["blockers"],
        )
        self.assertEqual(report["bridge"]["wrong_kind_records"], 0)

    def test_bridge_record_in_thalamic_lane_is_wrong_kind(self):
        pair = gate_snn_bridge("bridge-in-thalamic")
        temporary, report = self._audit(THALAMIC_FACTORY, [pair])
        temporary.cleanup()

        self.assertFalse(report["training_ready"])
        self.assertEqual(report["bridge"]["pairs"], 1)
        self.assertEqual(report["bridge"]["distillation_records"], 0)
        self.assertEqual(report["bridge"]["wrong_kind_records"], 1)
        blockers = " ".join(report["blockers"])
        self.assertIn("wrong-kind distillation records", blockers)
        self.assertIn(f"non-Thalamic records in {THALAMIC_FACTORY}", blockers)

    def test_bridge_record_in_ouroboros_lane_names_the_supported_lane(self):
        pair = gate_snn_bridge("bridge-in-ouroboros")
        temporary, report = self._audit(OUROBOROS_FACTORY, [pair])
        temporary.cleanup()

        blockers = " ".join(report["blockers"])
        self.assertFalse(report["training_ready"])
        self.assertIn(OUROBOROS_FACTORY, blockers)
        self.assertIn("non-Thalamic records", blockers)

    def test_thalamic_record_in_bridge_lane_is_wrong_kind(self):
        temporary, report = self._audit(
            BRIDGE_FACTORY,
            [thalamic("thalamic-in-bridge")],
        )
        temporary.cleanup()

        self.assertFalse(report["training_ready"])
        self.assertEqual(report["bridge"]["pairs"], 0)
        self.assertEqual(report["bridge"]["distillation_records"], 0)
        self.assertEqual(report["bridge"]["wrong_kind_records"], 1)
        self.assertTrue(
            any("non-Bridge records" in item for item in report["blockers"]),
            report["blockers"],
        )

    def test_bridge_fidelity_and_distillation_use_distinct_denominators(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            write(
                root / BRIDGE_FACTORY / "batch-r01.jsonl",
                [gate_snn_bridge("bridge-1")],
            )
            write(
                root / THALAMIC_FACTORY / "batch-r02.jsonl",
                [thalamic(f"ttf-{index}") for index in range(3)],
            )
            report = training_audit.audit_run(root)
            markdown = training_audit.render_markdown(report)

        bridge = report["bridge"]
        self.assertTrue(report["training_ready"], report["blockers"])
        self.assertEqual(bridge["pairs"], 1)
        self.assertEqual(bridge["sorted_pairs"], 1)
        self.assertEqual(bridge["distillation_records"], 4)
        self.assertEqual(bridge["raster_valid_pairs"], 4)
        self.assertEqual(bridge["raster_coverage_pct"], 100.0)
        self.assertIn("Bridge fidelity: 1/1", markdown)
        self.assertIn("Distillation rasters: 4/4", markdown)

    def test_foreign_mill_cannot_inflate_distillation_denominator(self):
        eligible = thalamic("ttf-clean")
        foreign = thalamic("sir-r56-meili-swap-leftover3c-rebuild")
        foreign["meta"]["factory"] = "search-index-rebuild-factory"
        temporary, report = self._audit(THALAMIC_FACTORY, [eligible, foreign])
        temporary.cleanup()

        self.assertEqual(report["totals"]["records"], 2)
        self.assertEqual(report["totals"]["eligible_records"], 1)
        self.assertEqual(report["mill_mix"]["records"], 1)
        self.assertEqual(report["bridge"]["distillation_records"], 1)
        self.assertEqual(report["bridge"]["raster_valid_pairs"], 1)


if __name__ == "__main__":
    unittest.main()
