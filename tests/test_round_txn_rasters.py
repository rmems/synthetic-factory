#!/usr/bin/env python3
"""Raster and spike-implemented-gate publication contracts."""

import json
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO / "pipelines") not in sys.path:
    sys.path.insert(0, str(REPO / "pipelines"))
if str(REPO / "tests") not in sys.path:
    sys.path.insert(0, str(REPO / "tests"))

import round_txn  # noqa: E402
from record_kind import classify_kind  # noqa: E402
from round_txn_test_helpers import (  # noqa: E402
    bridge,
    raw_factory,
    stage_round,
    thalamic,
)

BRIDGE_SLUG = "neuromorphic-event-language-bridge"
THALAMIC_SLUG = "thalamic-trajectory-factory"
OUROBOROS_SLUG = "multi-agent-ouroboros-swarm"


class RasterPublishAssertions(unittest.TestCase):
    """Shared publication setup without adding discoverable test methods."""

    def publish_records(self, slug, records, override):
        with tempfile.TemporaryDirectory() as td:
            factory = raw_factory(td, slug)
            reservation = stage_round(round_txn, factory, records)
            return round_txn.publish(
                factory,
                1,
                reservation["token"],
                execution_override=override,
            )

    def assert_publish_rejected(self, slug, records, pattern):
        with tempfile.TemporaryDirectory() as td:
            factory = raw_factory(td, slug)
            reservation = stage_round(round_txn, factory, records)
            with self.assertRaisesRegex(round_txn.TransactionError, pattern):
                round_txn.publish(factory, 1, reservation["token"])
            self.assertFalse((factory / "batch-r01.jsonl").exists())

    def validate_payload(self, payload, slug=BRIDGE_SLUG):
        with tempfile.TemporaryDirectory() as td:
            factory = raw_factory(td, slug)
            batch = factory / "batch-r01.jsonl"
            batch.write_bytes(payload)
            return round_txn.validate_bridge_envelope(batch, factory)


class BridgeRasterEnvelope(RasterPublishAssertions):
    """New Bridge rounds must be directly loadable by a distillation probe."""

    def test_raster_backed_round_with_a_gate_head_publishes(self):
        records = [bridge("bridge-1", gate_snn=False), bridge("bridge-2")]
        manifest = self.publish_records(
            BRIDGE_SLUG,
            records,
            "bridge envelope fixture has no live executor",
        )

        self.assertEqual(manifest["records"], 2)

    def test_record_without_a_raster_cannot_be_published(self):
        record = bridge("bridge-1")
        del record["raster"]
        self.assert_publish_rejected(BRIDGE_SLUG, [record], "20-50 ms raster excerpt sidecar")

    def test_broken_spike_product_cannot_be_published(self):
        record = bridge("bridge-1")
        record["raster"]["spikes"] = 999
        self.assert_publish_rejected(BRIDGE_SLUG, [record], "BRIDGE_SPIKE_BUDGET_MISMATCH")

    def test_malformed_declared_raster_fields_cannot_be_published(self):
        record = bridge("bridge-1")
        record["raster"]["window_s"] = "bogus"
        self.assert_publish_rejected(BRIDGE_SLUG, [record], "BRIDGE_RASTER_WINDOW_INVALID")

    def test_raster_without_a_routing_table_cannot_be_published(self):
        record = bridge("bridge-1")
        record["raster"]["routing"]["table"] = []
        self.assert_publish_rejected(BRIDGE_SLUG, [record], "routing.table must carry at least one")

    def test_round_without_a_spike_implemented_gate_cannot_be_published(self):
        records = [
            bridge("bridge-1", gate_snn=False),
            bridge("bridge-2", gate_snn=False),
        ]
        self.assert_publish_rejected(BRIDGE_SLUG, records, "at least one spike-implemented gate")

    def test_non_bridge_record_cannot_be_published_by_the_bridge_factory(self):
        self.assert_publish_rejected(
            BRIDGE_SLUG,
            [thalamic("not-bridge")],
            "requires only paired Bridge records",
        )

    def test_canonically_thalamic_hybrid_cannot_publish_in_bridge_lane(self):
        record = bridge("hybrid")
        record.update(thalamic("hybrid-top"))

        self.assertEqual(classify_kind(record), "thalamic")
        self.assert_publish_rejected(
            BRIDGE_SLUG,
            [record],
            "requires only paired Bridge records",
        )

    def test_other_factories_skip_the_raster_envelope_without_opening_batch(self):
        slug = "failure-as-fuel-preference-cascade"
        self.assertNotIn(slug, round_txn.RASTER_FACTORY_SLUGS)
        with tempfile.TemporaryDirectory() as td:
            factory = raw_factory(td, slug)
            errors = round_txn.validate_bridge_envelope(factory / "batch-r01.jsonl", factory)
        self.assertEqual(errors, [])

    def test_thalamic_factory_cannot_publish_prose_only_spike_counts(self):
        record = thalamic("prose-only")
        del record["raster"]
        del record["gate_snn"]
        self.assert_publish_rejected(THALAMIC_SLUG, [record], "20-50 ms raster excerpt sidecar")

    def test_bare_cr_between_objects_is_not_a_record_boundary(self):
        payload = (json.dumps(bridge("bridge-1")) + "\r" + json.dumps(bridge("bridge-2"))).encode(
            "utf-8"
        )
        errors = self.validate_payload(payload)
        self.assertTrue(any("JSON parse error" in error for error in errors), errors)

    def test_crlf_separates_bridge_records(self):
        lines = [
            json.dumps(bridge("bridge-1", gate_snn=False)),
            json.dumps(bridge("bridge-2")),
        ]
        errors = self.validate_payload(("\r\n".join(lines) + "\r\n").encode())
        self.assertEqual(errors, [])

    def test_unicode_line_separators_remain_inside_one_json_record(self):
        record = bridge("bridge-unicode")
        record["bridge_notes"]["mapping"] = "left\u2028middle\u2029right"
        payload = (json.dumps(record, ensure_ascii=False) + "\n").encode("utf-8")
        self.assertEqual(self.validate_payload(payload), [])

    def test_exponent_overflow_in_a_forwarded_gate_field_cannot_publish(self):
        with tempfile.TemporaryDirectory() as td:
            factory = raw_factory(td, BRIDGE_SLUG)
            reservation = stage_round(round_txn, factory, [bridge("bridge-overflow")])
            batch = Path(reservation["staging_dir"]) / reservation["batch_file"]
            payload = batch.read_text(encoding="utf-8").replace(
                '"gate_snn": {',
                '"gate_snn": {"forward_compatible_extra": 1e999, ',
                1,
            )
            batch.write_text(payload, encoding="utf-8")

            with self.assertRaisesRegex(round_txn.TransactionError, "non-finite JSON number 1e999"):
                round_txn.publish(factory, 1, reservation["token"])
            self.assertFalse((factory / reservation["batch_file"]).exists())


class OuroborosLaneRasterEnvelope(RasterPublishAssertions):
    """The swarm lane emits Thalamic trajectories and shares the raster gate."""

    @staticmethod
    def record(record_id):
        record = thalamic(record_id)
        record["meta"]["factory"] = OUROBOROS_SLUG
        return record

    def test_a_swarm_round_without_a_raster_cannot_publish(self):
        record = self.record("swarm-prose-only")
        del record["raster"]
        del record["gate_snn"]
        self.assert_publish_rejected(OUROBOROS_SLUG, [record], "20-50 ms raster excerpt sidecar")

    def test_a_raster_backed_swarm_round_still_publishes(self):
        manifest = self.publish_records(
            OUROBOROS_SLUG,
            [self.record("swarm-raster-1")],
            "swarm envelope fixture has no live executor",
        )

        self.assertEqual(manifest["records"], 1)


class UnboundedSpikeBudgetsAtPublish(RasterPublishAssertions):
    def test_an_unrepresentable_spike_count_is_refused_not_raised(self):
        record = thalamic("oversized-budget")
        record["raster"]["spikes"] = 10**400
        record["raster"]["energy_uJ"] = 1.0
        self.assert_publish_rejected(THALAMIC_SLUG, [record], "spike-budget contract violated")


if __name__ == "__main__":
    unittest.main()
