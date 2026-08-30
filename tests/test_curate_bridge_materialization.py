#!/usr/bin/env python3
"""Focused atomic-materialization tests for Bridge curation."""

from __future__ import annotations

import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

try:
    from tests.test_curate_bridge import bridge, curate_bridge, event, gate_snn_fixture
except ModuleNotFoundError:
    from test_curate_bridge import (  # type: ignore[no-redef]
        bridge,
        curate_bridge,
        event,
        gate_snn_fixture,
    )

import curate_gate  # noqa: E402


def raster_sidecars():
    """Return raster and gate sidecars in their producer representation."""

    record = gate_snn_fixture()
    return {"raster": record["raster"], "gate_snn": record["gate_snn"]}


class BridgeMaterialization(unittest.TestCase):
    def _source_tree(self, root):
        first = root / "factory-a" / "batch-r01.jsonl"
        second = root / "factory-b" / "batch-r02.jsonl"
        first.parent.mkdir(parents=True)
        second.parent.mkdir(parents=True)
        retained = {**bridge([event(1, "already")], "retain"), **raster_sidecars()}
        repaired = {
            **bridge([event(2, "late"), event(1, "early")], "repair"),
            **raster_sidecars(),
        }
        first.write_text(
            "\n".join((json.dumps(retained), json.dumps(repaired), "")),
            encoding="utf-8",
        )
        second.write_text(
            json.dumps({"id": "quarantine", "not_bridge": True}) + "\n",
            encoding="utf-8",
        )
        return first, second

    def test_cli_materializes_a_gate_compatible_multi_file_lane_tree(self):
        with tempfile.TemporaryDirectory() as td:
            temporary = Path(td)
            source_root = temporary / "source"
            output = temporary / "lane-bridge"
            sources = self._source_tree(source_root)
            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                exit_code = curate_bridge.main(
                    [
                        "--source-root",
                        str(source_root),
                        "--out-dir",
                        str(output),
                        *(str(path) for path in sources),
                    ]
                )

            self.assertEqual(exit_code, 0)
            self.assertEqual(json.loads(stdout.getvalue())["records"], 3)
            manifest_path = output / curate_bridge.MANIFEST_NAME
            entries = [
                json.loads(line) for line in manifest_path.read_text(encoding="utf-8").splitlines()
            ]
            self.assertEqual(
                [entry["action"] for entry in entries],
                ["retain", "repair", "quarantine"],
            )
            self.assertTrue((output / "factory-a" / "batch-r01.jsonl").is_file())
            self.assertFalse((output / "factory-b" / "batch-r02.jsonl").exists())

            lane = {
                "order": 1,
                "bead": "sf-c5l.1",
                "transform": curate_bridge.TRANSFORM_NAME,
                "version": curate_bridge.TRANSFORM_VERSION,
                "outputs_dir": output,
                "manifest_path": manifest_path,
                "manifest_format": "jsonl",
                "artifacts": [],
            }
            prepared = curate_gate._prepare_lane(
                lane,
                curate_gate._load_source_records(source_root),
            )

        self.assertEqual(len(prepared["entries"]), 3)
        self.assertEqual(len(prepared["records"]), 2)
        self.assertEqual(
            {record["output_id"] for record in prepared["records"]},
            {"retain", "repair"},
        )

    def test_materialization_refuses_clobber_and_preserves_existing_tree(self):
        with tempfile.TemporaryDirectory() as td:
            temporary = Path(td)
            source_root = temporary / "source"
            sources = self._source_tree(source_root)
            output = temporary / "lane-bridge"
            output.mkdir()
            marker = output / "owned-by-someone-else"
            marker.write_text("preserve", encoding="utf-8")

            with self.assertRaisesRegex(curate_bridge.BridgeCurationError, "already exists"):
                curate_bridge.materialize_paths(
                    sources,
                    source_root=source_root,
                    output_dir=output,
                )

            self.assertEqual(marker.read_text(encoding="utf-8"), "preserve")
            self.assertEqual(sorted(path.name for path in output.iterdir()), [marker.name])

    def test_materialization_refuses_raw_destination_and_symlink_source(self):
        with tempfile.TemporaryDirectory() as td:
            temporary = Path(td)
            source_root = temporary / "source"
            sources = self._source_tree(source_root)
            raw_parent = temporary / "outputs" / "raw" / "run"
            raw_parent.mkdir(parents=True)
            with self.assertRaisesRegex(
                curate_bridge.BridgeCurationError, "immutable raw evidence"
            ):
                curate_bridge.materialize_paths(
                    sources,
                    source_root=source_root,
                    output_dir=raw_parent / "lane-bridge",
                )

            linked = source_root / "linked.jsonl"
            linked.symlink_to(sources[0])
            with self.assertRaisesRegex(curate_bridge.BridgeCurationError, "real JSONL file"):
                curate_bridge.materialize_paths(
                    [linked],
                    source_root=source_root,
                    output_dir=temporary / "linked-output",
                )

    def test_materialize_paths_in_process_and_rejects_unsafe_layout(self):
        with tempfile.TemporaryDirectory() as td:
            temporary = Path(td)
            source_root = temporary / "source"
            sources = self._source_tree(source_root)
            output = temporary / "lane-bridge"
            decisions = curate_bridge.materialize_paths(
                sources,
                source_root=source_root,
                output_dir=output,
            )
            self.assertEqual(len(decisions), 3)
            self.assertTrue((output / curate_bridge.MANIFEST_NAME).is_file())

            with self.assertRaisesRegex(curate_bridge.BridgeCurationError, "real directory"):
                curate_bridge.materialize_paths(
                    sources,
                    source_root=sources[0],
                    output_dir=temporary / "out-file-root",
                )
            with self.assertRaisesRegex(curate_bridge.BridgeCurationError, "at least one"):
                curate_bridge.materialize_paths(
                    [],
                    source_root=source_root,
                    output_dir=temporary / "out-empty",
                )
            with self.assertRaisesRegex(curate_bridge.BridgeCurationError, "inside source_root"):
                curate_bridge.materialize_paths(
                    sources,
                    source_root=source_root,
                    output_dir=source_root / "nested-out",
                )
            with self.assertRaisesRegex(curate_bridge.BridgeCurationError, "end in .jsonl"):
                curate_bridge.materialize_paths(
                    sources,
                    source_root=source_root,
                    output_dir=temporary / "out-manifest",
                    manifest_name="manifest.json",
                )
            outside = temporary / "outside.jsonl"
            outside.write_text("{}\n", encoding="utf-8")
            with self.assertRaisesRegex(curate_bridge.BridgeCurationError, "outside source_root"):
                curate_bridge.materialize_paths(
                    [outside],
                    source_root=source_root,
                    output_dir=temporary / "out-outside",
                )
            with self.assertRaisesRegex(curate_bridge.BridgeCurationError, "safe relative path"):
                curate_bridge._safe_relative_path("../escape.jsonl", label="manifest_name")


if __name__ == "__main__":
    unittest.main()
