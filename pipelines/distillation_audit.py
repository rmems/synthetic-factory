#!/usr/bin/env python3
"""Distillation-raster metrics for the corpus training audit.

Bridge event fidelity and SNN distillation readiness intentionally have
different denominators.  ``pairs`` contains only Bridge records and owns the
event-order metrics.  ``distillation_records`` contains eligible records from
the NELB and TTF lanes (plus legacy Bridge records outside those named lanes)
and owns raster, routing, and gate-head coverage.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any

from curate_bridge import raster_status
from training_audit_bridge import event_stream_status

BRIDGE_FACTORY_SLUG = "neuromorphic-event-language-bridge"
THALAMIC_FACTORY_SLUG = "thalamic-trajectory-factory"

_EXPECTED_KIND = {
    BRIDGE_FACTORY_SLUG: "bridge_pair",
    THALAMIC_FACTORY_SLUG: "thalamic",
}


class DistillationAudit:
    """Accumulate fidelity and distillation metrics after quarantine."""

    def __init__(self) -> None:
        self.metrics = Counter(
            pairs=0,
            distillation_records=0,
            raster_valid_pairs=0,
            raster_missing_pairs=0,
            raster_defect_pairs=0,
            raster_routing_table_missing_pairs=0,
            raster_spikes=0,
            third_factor_pairs=0,
            gate_snn_records=0,
            gate_snn_valid_records=0,
            wrong_kind_records=0,
        )
        self.batches: defaultdict[str, Counter] = defaultdict(Counter)
        self.raster_missing_examples: list[str] = []
        self.raster_defect_examples: list[str] = []
        self.raster_defect_codes: Counter = Counter()
        self.wrong_kind_examples: list[str] = []

    def observe(
        self,
        *,
        factory: str,
        where: str,
        kind: str,
        record: Any,
    ) -> None:
        """Account for one eligible record.

        Callers must invoke this only after foreign-mill quarantine.  That
        ordering keeps quarantined records out of both fidelity and raster
        coverage denominators.
        """

        if kind == "bridge_pair":
            self._observe_bridge_fidelity(record)

        batch_path = where.rpartition(":")[0]
        expected_kind = _EXPECTED_KIND.get(factory)
        if expected_kind is not None and kind != expected_kind:
            self.metrics["wrong_kind_records"] += 1
            self.batches[batch_path]["wrong_kind_records"] += 1
            if len(self.wrong_kind_examples) < 5:
                self.wrong_kind_examples.append(f"{where}:{kind}")
            return
        if expected_kind is None and kind != "bridge_pair":
            return

        self.metrics["distillation_records"] += 1
        batch = self.batches[batch_path]
        batch["distillation_records"] += 1
        self._observe_raster(record, where, batch)

    def _observe_bridge_fidelity(self, record: Any) -> None:
        self.metrics["pairs"] += 1
        events = record.get("spike_events") if isinstance(record, dict) else None
        if isinstance(events, list):
            self.metrics["events"] += len(events)
            self.metrics["pairs_48_plus"] += int(len(events) >= 48)
        status = event_stream_status(events, record)
        self.metrics[f"{status}_pairs"] += 1

    def _observe_raster(self, record: Any, where: str, batch: Counter) -> None:
        status = raster_status(record)
        self._raster_quality_observer(status)(status, where)
        self._observe_routing(status)
        self._observe_gate(status, batch)

    def _raster_quality_observer(self, status):
        return (
            self._observe_missing_raster
            if not status["raster_present"]
            else self._observe_defective_raster
            if status["reason_codes"]
            else self._observe_valid_raster
        )

    def _observe_missing_raster(self, _status, where):
        self.metrics["raster_missing_pairs"] += 1
        if len(self.raster_missing_examples) < 5:
            self.raster_missing_examples.append(where)

    def _observe_defective_raster(self, status, where):
        self.metrics["raster_defect_pairs"] += 1
        self.raster_defect_codes.update(status["reason_codes"])
        if len(self.raster_defect_examples) < 5:
            joined = ",".join(status["reason_codes"])
            self.raster_defect_examples.append(f"{where}: {joined}")

    def _observe_valid_raster(self, status, _where):
        self.metrics["raster_valid_pairs"] += 1
        if isinstance(status["spikes"], int):
            self.metrics["raster_spikes"] += status["spikes"]

    def _observe_routing(self, status):
        if status["raster_present"] and status["routing_table_entries"] < 1:
            self.metrics["raster_routing_table_missing_pairs"] += 1
        self.metrics["third_factor_pairs"] += int(status["third_factor_present"])

    def _observe_gate(self, status, batch):
        if status["gate_snn_present"]:
            self.metrics["gate_snn_records"] += 1
            self.metrics["gate_snn_valid_records"] += int(status["gate_snn_valid"])
            batch["gate_snn_records"] += 1
            batch["gate_snn_valid_records"] += int(status["gate_snn_valid"])

    def report(self) -> dict[str, Any]:
        """Return the stable public ``bridge`` report mapping."""

        missing_batches = sorted(
            path for path, counts in self.batches.items() if not counts.get("gate_snn_records", 0)
        )
        batch_count = len(self.batches)
        denominator = self.metrics["distillation_records"]
        return {
            **dict(self.metrics),
            "gate_snn_batches": batch_count,
            "gate_snn_covered_batches": batch_count - len(missing_batches),
            "gate_snn_missing_batches": len(missing_batches),
            "gate_snn_missing_batch_examples": missing_batches[:10],
            "raster_coverage_pct": (
                round(100 * self.metrics["raster_valid_pairs"] / denominator, 1)
                if denominator
                else 0
            ),
            "raster_missing_examples": self.raster_missing_examples,
            "raster_defect_examples": self.raster_defect_examples,
            "raster_defect_codes": dict(sorted(self.raster_defect_codes.items())),
            "wrong_kind_examples": self.wrong_kind_examples,
        }
