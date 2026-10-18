"""A materialized Bridge lane must gate on raster sidecars."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

try:
    from tests.curate_bridge_raster_test_support import (
        bridge,
        curate_bridge,
        event,
        gate_snn_fixture,
    )
except ModuleNotFoundError:
    from curate_bridge_raster_test_support import (  # type: ignore[no-redef]
        bridge,
        curate_bridge,
        event,
        gate_snn_fixture,
    )


def source_tree(root, records):
    """Write ``records`` as one Bridge batch under ``<root>/raw``; return (raw root, batch)."""
    source_root = Path(root) / "raw"
    batch = source_root / "neuromorphic-event-language-bridge" / "batch-r02.jsonl"
    batch.parent.mkdir(parents=True)
    batch.write_text(
        "".join(json.dumps(record, ensure_ascii=False) + "\n" for record in records),
        encoding="utf-8",
    )
    return source_root, batch


class MaterializedLaneRequiresRasters(unittest.TestCase):
    """``--out-dir`` publishes a *gate-compatible* tree, so it must gate.

    The publication, audit and probe contracts all reject a Bridge record with
    no raster sidecar; materializing one into the tree this module advertises
    as gate-compatible would hand a downstream distillation run a record every
    other layer refuses.
    """

    def test_materialized_tree_quarantines_a_raster_less_record(self):
        with tempfile.TemporaryDirectory() as td:
            records = [bridge([event(1.0, "a"), event(2.0, "b")], "no-raster")]
            source_root, batch = source_tree(td, records)
            out_dir = Path(td) / "lane"

            decisions = curate_bridge.materialize_paths(
                [batch], source_root=source_root, output_dir=out_dir
            )

            self.assertEqual([d.action for d in decisions], ["quarantine"])
            self.assertIn(
                curate_bridge.REASON_RASTER_MISSING, decisions[0].manifest["reason_codes"]
            )
            self.assertFalse(
                (out_dir / "neuromorphic-event-language-bridge" / "batch-r02.jsonl").exists()
            )

    def test_materialized_tree_keeps_a_raster_backed_record(self):
        with tempfile.TemporaryDirectory() as td:
            source_root, batch = source_tree(td, [gate_snn_fixture()])
            out_dir = Path(td) / "lane"

            decisions = curate_bridge.materialize_paths(
                [batch], source_root=source_root, output_dir=out_dir
            )

            self.assertEqual([d.action for d in decisions], ["retain"])
            self.assertTrue(
                (out_dir / "neuromorphic-event-language-bridge" / "batch-r02.jsonl").exists()
            )

    def test_the_pure_decision_api_still_defaults_to_lenient(self):
        with tempfile.TemporaryDirectory() as td:
            records = [bridge([event(1.0, "a"), event(2.0, "b")], "no-raster")]
            _source_root, batch = source_tree(td, records)

            self.assertEqual([d.action for d in curate_bridge.curate_jsonl(batch)], ["retain"])
            self.assertEqual(
                [d.action for d in curate_bridge.curate_jsonl(batch, require_raster=True)],
                ["quarantine"],
            )


if __name__ == "__main__":
    unittest.main()
