#!/usr/bin/env python3
"""Second-round raster-contract regressions for Bridge curation."""

from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

try:
    from tests.test_curate_bridge import curate_bridge, gate_snn_fixture
except ModuleNotFoundError:
    from test_curate_bridge import curate_bridge, gate_snn_fixture  # type: ignore[no-redef]

from exact_json import MAX_DECIMAL_DIGITS  # noqa: E402


class RasterContractSecondReviewRound(unittest.TestCase):
    """PR #94 follow-up review: crashes and gaps the first round left open."""

    def test_an_oversized_declared_number_is_a_defect_not_an_overflow(self):
        """An integer beyond the exact-JSON digit contract is invalid.

        Every numeric raster/gate guard runs through ``_is_finite_number``, so
        a staged record declaring an unbounded JSON integer crashed the
        publish gate, the training audit and strict probing instead of
        reporting an invalid contract.
        """
        oversized = 10**MAX_DECIMAL_DIGITS
        self.assertFalse(curate_bridge._is_finite_number(oversized))
        self.assertFalse(curate_bridge._is_finite_number(-oversized))

        for field, reason in (
            ("window_ms", curate_bridge.REASON_RASTER_WINDOW),
            ("window_s", curate_bridge.REASON_RASTER_WINDOW),
            ("energy_pJ", curate_bridge.REASON_RASTER_ENERGY),
            ("energy_uJ", curate_bridge.REASON_RASTER_ENERGY),
            ("mean_rate_hz", curate_bridge.REASON_RASTER_SPIKE_BUDGET),
        ):
            with self.subTest(field=field):
                record = gate_snn_fixture()
                record["raster"][field] = oversized

                status = curate_bridge.raster_status(record)

                self.assertFalse(status["raster_valid"])
                self.assertIn(reason, status["reason_codes"])
                json.dumps(status["evidence"], allow_nan=False)

    def test_a_routing_entry_without_a_weight_is_invalid(self):
        """prompts/03-neuromorphic-event-language-bridge.md specifies
        ``{from, to, weight}``: without a synaptic weight a distillation
        consumer cannot reconstruct the declared connection, so a missing
        weight is as invalid as a non-numeric one."""
        for entry in (
            {"from": "pop_a", "to": "pop_b"},
            {"from": "pop_a", "to": "pop_b", "weight": None},
            {"from": "pop_a", "to": "pop_b", "weight": "0.5"},
        ):
            with self.subTest(entry=entry):
                record = gate_snn_fixture()
                record["raster"]["routing"]["table"] = [entry]

                status = curate_bridge.raster_status(record)

                self.assertFalse(status["raster_valid"])
                self.assertIn(curate_bridge.REASON_RASTER_ROUTING, status["reason_codes"])
                self.assertEqual(status["routing_table_entries"], 0)

        record = gate_snn_fixture()
        self.assertTrue(curate_bridge.raster_status(record)["raster_valid"])

    def test_materialized_trees_require_a_loadable_routing_table(self):
        """``materialize_paths`` advertises a gate-compatible tree, but a
        raster with no routing entry is exactly what the strict probe rejects
        as BRIDGE_RASTER_ROUTING_MISSING, so publishing one produced a corpus
        distillation cannot load."""
        for table in ([], None):
            with self.subTest(table=table):
                record = gate_snn_fixture()
                if table is None:
                    record["raster"]["routing"].pop("table", None)
                else:
                    record["raster"]["routing"]["table"] = table
                raw = json.dumps(record, ensure_ascii=False).encode("utf-8")
                digest = hashlib.sha256(raw).hexdigest()

                published = curate_bridge.curate_record(
                    record,
                    source_path="bridge/batch-r02.jsonl",
                    source_line=1,
                    source_hash=digest,
                    require_raster=True,
                    require_routing_table=True,
                )
                self.assertEqual(published.action, "quarantine")
                self.assertIn(
                    curate_bridge.REASON_RASTER_ROUTING,
                    published.manifest["reason_codes"],
                )

                # The pure decision API is unchanged: the table stays optional
                # there, and the publish gate keeps its own routing message.
                lenient = curate_bridge.curate_record(
                    record,
                    source_path="bridge/batch-r02.jsonl",
                    source_line=1,
                    source_hash=digest,
                    require_raster=True,
                )
                self.assertEqual(lenient.action, "retain")

    def test_materialize_paths_refuses_a_tableless_raster(self):
        record = gate_snn_fixture()
        record["raster"]["routing"]["table"] = []
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "src"
            (root / "bridge").mkdir(parents=True)
            source = root / "bridge" / "batch-r02.jsonl"
            source.write_text(json.dumps(record, ensure_ascii=False) + "\n", encoding="utf-8")

            decisions = curate_bridge.materialize_paths(
                [source],
                source_root=root,
                output_dir=Path(td) / "tree",
            )

        self.assertEqual([d.action for d in decisions], ["quarantine"])
        self.assertIn(curate_bridge.REASON_RASTER_ROUTING, decisions[0].manifest["reason_codes"])


if __name__ == "__main__":
    unittest.main()
