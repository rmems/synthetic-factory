#!/usr/bin/env python3
"""Focused atomic-materialization tests for Bridge curation."""

from __future__ import annotations

import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

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
import curate_bridge_materialize  # noqa: E402
import check_records  # noqa: E402
import training_audit  # noqa: E402
from census import visible_jsonl_paths  # noqa: E402


def raster_sidecars():
    """Return raster and gate sidecars in their producer representation."""

    record = gate_snn_fixture()
    return {"raster": record["raster"], "gate_snn": record["gate_snn"]}


class BridgeMaterialization(unittest.TestCase):
    @staticmethod
    def _write_source(root, relative, records):
        source = root / relative
        source.parent.mkdir(parents=True, exist_ok=True)
        source.write_text(
            "".join(json.dumps(record, ensure_ascii=False) + "\n" for record in records),
            encoding="utf-8",
        )
        return source

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
            entries = json.loads(manifest_path.read_text(encoding="utf-8"))
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
                "manifest_format": "json",
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
            with self.assertRaisesRegex(curate_bridge.BridgeCurationError, "end in .json"):
                curate_bridge.materialize_paths(
                    sources,
                    source_root=source_root,
                    output_dir=temporary / "out-manifest",
                    manifest_name="manifest.jsonl",
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

    def test_staged_manifest_is_one_strict_json_document(self):
        context = SimpleNamespace(reject_json_constant=curate_bridge._reject_json_constant)
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "manifest.json"
            path.write_bytes('[{"text":"left\u2028middle\u2029right"}]\r\n'.encode("utf-8"))
            self.assertEqual(
                curate_bridge_materialize._read_manifest(path, context),
                [{"text": "left\u2028middle\u2029right"}],
            )

            path.write_bytes(b'[{"first":1}\r{"second":2}]\n')
            with self.assertRaisesRegex(curate_bridge.BridgeCurationError, "invalid staged"):
                curate_bridge_materialize._read_manifest(path, context)

            path.write_bytes(b'[{"value":NaN}]\n')
            with self.assertRaisesRegex(curate_bridge.BridgeCurationError, "non-standard"):
                curate_bridge_materialize._read_manifest(path, context)

            path.write_bytes(b'{"value":1}\n')
            with self.assertRaisesRegex(curate_bridge.BridgeCurationError, "expected a JSON array"):
                curate_bridge_materialize._read_manifest(path, context)

    def test_materialization_quarantines_nonfinite_and_nonscalar_json(self):
        overflow = gate_snn_fixture()
        overflow["extra"] = 0
        overflow_line = json.dumps(overflow).replace('"extra": 0', '"extra": 1e999')
        surrogate = gate_snn_fixture()
        surrogate["id"] = "surrogate-\ud800"

        with tempfile.TemporaryDirectory() as td:
            temporary = Path(td)
            source_root = temporary / "source"
            source = source_root / "bridge" / "batch-r01.jsonl"
            source.parent.mkdir(parents=True)
            source.write_text(
                overflow_line + "\n" + json.dumps(surrogate) + "\n",
                encoding="utf-8",
            )
            output = temporary / "lane-bridge"

            decisions = curate_bridge.materialize_paths(
                [source],
                source_root=source_root,
                output_dir=output,
            )

            manifest = json.loads(
                (output / curate_bridge.MANIFEST_NAME).read_text(encoding="utf-8")
            )

        self.assertEqual([decision.action for decision in decisions], ["quarantine"] * 2)
        self.assertTrue(all(decision.output_record is None for decision in decisions))
        self.assertEqual(len(manifest), 2)

    def test_materialized_manifest_is_not_consumed_as_training_data(self):
        with tempfile.TemporaryDirectory() as td:
            temporary = Path(td)
            source_root = temporary / "source"
            source = self._write_source(
                source_root,
                "bridge/batch-r01.jsonl",
                [gate_snn_fixture()],
            )
            output = temporary / "lane-bridge"

            decisions = curate_bridge.materialize_paths(
                [source],
                source_root=source_root,
                output_dir=output,
            )
            manifest_path = output / curate_bridge.MANIFEST_NAME
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            visible = [path.relative_to(output).as_posix() for path in visible_jsonl_paths(output)]
            structural = check_records.check_run(output, strict=True)
            readiness = training_audit.audit_run(output)

        self.assertEqual([decision.action for decision in decisions], ["retain"])
        self.assertEqual(len(manifest), 1)
        self.assertEqual(visible, ["bridge/batch-r01.jsonl"])
        self.assertEqual(structural["totals"]["files"], 1)
        self.assertEqual(structural["totals"]["records"], 1)
        self.assertEqual(structural["exit_code"], 0)
        self.assertEqual(readiness["totals"]["files"], 1)
        self.assertEqual(readiness["totals"]["records"], 1)
        self.assertFalse(
            any(
                curate_bridge.MANIFEST_NAME in example
                for example in readiness["record_invariants"]["error_examples"]
            )
        )

    def test_atomic_publication_fails_explicitly_off_linux_and_windows(self):
        source = Path("unused-source")
        destination = Path("unused-destination")
        with (
            mock.patch.object(curate_bridge_materialize.os, "name", "posix"),
            mock.patch.object(curate_bridge_materialize.sys, "platform", "darwin"),
            self.assertRaisesRegex(
                curate_bridge.BridgeCurationError,
                "unsupported on platform 'darwin'",
            ),
        ):
            curate_bridge_materialize._rename_noreplace(source, destination)

    def test_linux_publication_fails_explicitly_without_renameat2(self):
        with (
            mock.patch.object(
                curate_bridge_materialize.ctypes,
                "CDLL",
                return_value=object(),
            ),
            self.assertRaisesRegex(
                curate_bridge.BridgeCurationError,
                "requires Linux renameat2",
            ),
        ):
            curate_bridge_materialize._rename_linux(
                Path("unused-source"),
                Path("unused-destination"),
            )

    def test_routing_validation_is_independent_of_raster_requirement(self):
        record = gate_snn_fixture()
        record["raster"]["routing"]["table"] = []
        with tempfile.TemporaryDirectory() as td:
            temporary = Path(td)
            root = temporary / "source"
            source = self._write_source(root, "bridge/batch-r01.jsonl", [record])
            decisions = curate_bridge.materialize_paths(
                [source],
                source_root=root,
                output_dir=temporary / "tree",
                require_raster=False,
            )

        self.assertEqual([decision.action for decision in decisions], ["quarantine"])
        self.assertIn(
            curate_bridge.REASON_RASTER_ROUTING,
            decisions[0].manifest["reason_codes"],
        )

    def test_each_materialized_source_batch_requires_a_valid_gate_head(self):
        gated = gate_snn_fixture()
        ungated = gate_snn_fixture()
        ungated.pop("gate_snn")
        with tempfile.TemporaryDirectory() as td:
            temporary = Path(td)
            root = temporary / "source"
            first = self._write_source(root, "factory-a/batch-r01.jsonl", [gated])
            second = self._write_source(root, "factory-b/batch-r02.jsonl", [ungated])
            destination = temporary / "tree"

            with self.assertRaisesRegex(
                curate_bridge.BridgeCurationError,
                "valid spike-implemented gate.*factory-b/batch-r02.jsonl",
            ):
                curate_bridge.materialize_paths(
                    [first, second],
                    source_root=root,
                    output_dir=destination,
                )

            self.assertFalse(destination.exists())

    def test_one_valid_gate_covers_its_materialized_source_batch(self):
        gated = gate_snn_fixture()
        gated["id"] = "gated"
        ungated = gate_snn_fixture()
        ungated["id"] = "ungated"
        ungated.pop("gate_snn")
        with tempfile.TemporaryDirectory() as td:
            temporary = Path(td)
            root = temporary / "source"
            source = self._write_source(
                root,
                "bridge/batch-r01.jsonl",
                [ungated, gated],
            )
            destination = temporary / "tree"
            decisions = curate_bridge.materialize_paths(
                [source],
                source_root=root,
                output_dir=destination,
            )

            self.assertEqual([decision.action for decision in decisions], ["retain", "retain"])
            self.assertTrue(destination.is_dir())


if __name__ == "__main__":
    unittest.main()
