"""The spike probe reads each Bridge raster input once, however it is named."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

try:
    from tests.curate_bridge_raster_test_support import (
        gate_snn_fixture,
    )
except ModuleNotFoundError:
    from curate_bridge_raster_test_support import (  # type: ignore[no-redef]
        gate_snn_fixture,
    )

import spike_probe


class SpikeProbeInputExpansion(unittest.TestCase):
    """One input reached twice must be read once."""

    def test_duplicate_probe_inputs_do_not_double_the_totals(self):
        """Naming a file twice -- or once directly and once through a
        containing directory -- appended it per target, so every raster was
        emitted twice and the spike and energy totals silently doubled,
        changing the weighting of a distillation dataset."""
        record = gate_snn_fixture()
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            batch = root / "batch-r02.jsonl"
            batch.write_text(json.dumps(record, ensure_ascii=False) + "\n", encoding="utf-8")

            once = spike_probe.jsonl_paths([batch])
            twice = spike_probe.jsonl_paths([batch, batch])
            via_dir = spike_probe.jsonl_paths([root, batch])
            relative = spike_probe.jsonl_paths([batch, Path(str(batch))])

            self.assertEqual(len(once), 1)
            self.assertEqual(twice, once)
            self.assertEqual(via_dir, once)
            self.assertEqual(relative, once)

            single, _problems = spike_probe.load_rasters([batch])
            doubled, _again = spike_probe.load_rasters([batch, batch])
            through_dir, _more = spike_probe.load_rasters([root, batch])

        self.assertEqual(len(single), 1)
        self.assertEqual(len(doubled), 1)
        self.assertEqual(len(through_dir), 1)
        self.assertEqual(
            sum(entry["spikes"] for entry in doubled),
            sum(entry["spikes"] for entry in single),
        )
        self.assertEqual(
            sum(entry["energy_pJ"] for entry in through_dir),
            sum(entry["energy_pJ"] for entry in single),
        )


if __name__ == "__main__":
    unittest.main()
