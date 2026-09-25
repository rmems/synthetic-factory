"""Output races must not overwrite files; manifest hashing stays bounded."""

import contextlib
import hashlib
import importlib.util
import io
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from test_validate_distill import REPO, vd


class OutputBoundaries(unittest.TestCase):
    def test_manifest_hashing_never_reads_an_entire_file_at_once(self):
        payload = b"bounded hashing\n" * 100000

        class BoundedReader(io.BytesIO):
            def read(self, size=-1):
                if not 0 < size <= 1024 * 1024:
                    raise AssertionError("unbounded read")
                return super().read(size)

        expected = {"sha256": hashlib.sha256(payload).hexdigest(), "records": 100000}
        with mock.patch.object(Path, "open", return_value=BoundedReader(payload)):
            self.assertEqual(vd._manifest_entry_errors(expected, Path("data"), "data", 100000), [])

    def test_manifest_symlink_inserted_during_build_is_not_followed(self):
        spec = importlib.util.spec_from_file_location(
            "fixture_output_boundary", REPO / "scripts/build_distillation_fixture.py"
        )
        builder = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(builder)
        with tempfile.TemporaryDirectory() as tmp, contextlib.ExitStack() as stack:
            root = Path(tmp)
            out = root / "run"
            victim = root / "keep"
            victim.write_text("preserved")
            for owner, name, value in (
                (builder.fault_recovery, "build_records", []),
                (builder.energy_preferences, "select_meter", (object(), {})),
                (builder.energy_preferences, "build_records", []),
                (builder.moe_router, "oracles_report", {}),
                (builder.moe_router, "build_records", []),
                (builder, "_write_records", {}),
                (builder, "_baseline_summary", {}),
                (builder, "_validation_summary", {}),
                (builder, "_oracles_block", {}),
            ):
                stack.enter_context(mock.patch.object(owner, name, return_value=value))

            def insert_manifest(*_):
                out.mkdir()
                (out / "MANIFEST.json").symlink_to(victim)
                return "test output race"

            stack.enter_context(
                mock.patch.object(builder, "_training_ready_note", side_effect=insert_manifest)
            )
            with self.assertRaisesRegex(SystemExit, "refusing to overwrite"):
                builder.build(out)
            self.assertEqual(victim.read_text(), "preserved")
