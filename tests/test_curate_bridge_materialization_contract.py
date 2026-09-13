#!/usr/bin/env python3
"""Focused publication-boundary contracts for Bridge materialization."""

import json
import tempfile
import unittest
from pathlib import Path

try:
    from tests.test_curate_bridge import curate_bridge, gate_snn_fixture
except ModuleNotFoundError:
    from test_curate_bridge import curate_bridge, gate_snn_fixture  # type: ignore[no-redef]


def _write_source(root: Path) -> Path:
    source = root / "bridge" / "batch-r01.jsonl"
    source.parent.mkdir(parents=True)
    source.write_text(json.dumps(gate_snn_fixture()) + "\n", encoding="utf-8")
    return source


class BridgeMaterializationContract(unittest.TestCase):
    def test_materialization_refuses_a_symlinked_destination_ancestor(self):
        with tempfile.TemporaryDirectory() as td:
            temporary = Path(td)
            source_root = temporary / "source"
            source = _write_source(source_root)
            real_parent = temporary / "real-parent"
            (real_parent / "nested").mkdir(parents=True)
            alias = temporary / "alias"
            alias.symlink_to(real_parent, target_is_directory=True)
            destination = alias / "nested" / "lane-bridge"

            with self.assertRaisesRegex(curate_bridge.BridgeCurationError, "symlink"):
                curate_bridge.materialize_paths(
                    [source],
                    source_root=source_root,
                    output_dir=destination,
                )

            self.assertFalse((real_parent / "nested" / "lane-bridge").exists())

    def test_materialization_cannot_disable_the_raster_contract(self):
        with tempfile.TemporaryDirectory() as td:
            temporary = Path(td)
            root = temporary / "source"
            source = _write_source(root)
            destination = temporary / "tree"

            with self.assertRaisesRegex(curate_bridge.BridgeCurationError, "require_raster"):
                curate_bridge.materialize_paths(
                    [source],
                    source_root=root,
                    output_dir=destination,
                    require_raster=False,
                )

            self.assertFalse(destination.exists())


if __name__ == "__main__":
    unittest.main()
