#!/usr/bin/env python3
"""Refusals that protect the destination, the source members, and the CLI."""

import io
import json
import os
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock

from export_test_support import (  # noqa: E402
    compose_fixture,
)
from test_compose_curated import (  # noqa: E402
    multi_agent,
    write_jsonl,
)
import compose_curated  # noqa: E402
import export_hf  # noqa: E402


class ExportDestinationSafety(unittest.TestCase):
    def test_refuses_empty_missing_and_existing_destinations(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            curated = compose_fixture(root)

            with self.assertRaises(export_hf.ExportError):
                export_hf.export_run(root / "no-such-root", root / "export-a")

            empty = root / "empty-curated"
            (empty / compose_curated.RECORDS_DIRNAME).mkdir(parents=True)
            with self.assertRaises(export_hf.ExportError):
                export_hf.export_run(empty, root / "export-b")

            export_hf.export_run(curated, root / "export")
            with self.assertRaises(export_hf.ExportError):
                export_hf.export_run(curated, root / "export")
            with self.assertRaises(export_hf.ExportError):
                export_hf.export_run(curated, curated / "nested-export")
            with self.assertRaises(export_hf.ExportError):
                export_hf.export_run(curated, root / "missing-parent" / "export")

    def test_refuses_export_destinations_lexically_or_resolved_under_raw(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            curated = compose_fixture(root)
            raw = root / "outputs" / "raw"
            raw.mkdir(parents=True)
            safe = root / "safe"
            safe.mkdir()

            lexical = raw / ".." / ".." / "safe" / "lexical-export"
            with self.assertRaisesRegex(export_hf.ExportError, "immutable raw"):
                export_hf.export_run(curated, lexical)
            self.assertFalse((safe / "lexical-export").exists())

            raw_link = root / "raw-link"
            raw_link.symlink_to(raw, target_is_directory=True)
            with self.assertRaisesRegex(export_hf.ExportError, "immutable raw"):
                export_hf.export_run(curated, raw_link / "resolved-export")
            self.assertFalse((raw / "resolved-export").exists())

            real_parent = root / "real-destination-parent"
            real_parent.mkdir()
            symlink_parent = root / "destination-parent-alias"
            symlink_parent.symlink_to(real_parent, target_is_directory=True)
            with self.assertRaisesRegex(
                export_hf.ExportError, "exact non-symlink"
            ):
                export_hf.export_run(curated, symlink_parent / "export")
            self.assertFalse((real_parent / "export").exists())

    def test_destination_parent_swap_cannot_redirect_creation_or_cleanup(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            curated = compose_fixture(root)
            parent = root / "destination-parent"
            parent.mkdir()
            moved_parent = root / "original-parent-moved"
            destination = parent / "export"
            raw = root / "outputs" / "raw"
            real_mkdir = os.mkdir
            swapped = False

            def swap_parent_before_create(path, mode=0o777, *, dir_fd=None):
                nonlocal swapped
                if path == destination.name and dir_fd is not None and not swapped:
                    swapped = True
                    parent.rename(moved_parent)
                    raw.mkdir(parents=True)
                    parent.symlink_to(raw, target_is_directory=True)
                return real_mkdir(path, mode, dir_fd=dir_fd)

            with mock.patch.object(
                compose_curated.os,
                "mkdir",
                side_effect=swap_parent_before_create,
            ):
                with self.assertRaisesRegex(
                    export_hf.ExportError,
                    "destination parent changed while it was pinned",
                ):
                    export_hf.export_run(curated, destination)

            self.assertTrue(swapped)
            self.assertFalse((moved_parent / destination.name).exists())
            self.assertFalse((raw / destination.name).exists())
            self.assertFalse(destination.exists())


class ExportCompositionMemberSafety(unittest.TestCase):
    def test_rejects_symlink_and_hardlink_aliases_for_every_compose_member(self):
        mutations = (
            "summary_symlink",
            "manifest_symlink",
            "output_lexical_alias",
            "output_symlink",
            "output_hardlink",
            "source_symlink",
            "source_hardlink",
            "source_directory_symlink",
        )
        for mutation in mutations:
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as td:
                root = Path(td)
                curated = compose_fixture(root)
                summary_path = curated / compose_curated.SUMMARY_FILENAME
                summary = json.loads(summary_path.read_text(encoding="utf-8"))
                if mutation == "summary_symlink":
                    target = root / "outside-COMPOSE.json"
                    summary_path.replace(target)
                    summary_path.symlink_to(target)
                elif mutation == "manifest_symlink":
                    path = curated / summary["manifest"]["path"]
                    target = root / "outside-manifest.jsonl"
                    path.replace(target)
                    path.symlink_to(target)
                elif mutation == "source_symlink":
                    source_root = Path(summary["source_run"])
                    path = next(source_root.rglob("*.jsonl"))
                    target = root / "outside-source.jsonl"
                    path.replace(target)
                    path.symlink_to(target)
                elif mutation == "source_hardlink":
                    source_root = Path(summary["source_run"])
                    path = next(source_root.rglob("*.jsonl"))
                    target = root / "outside-source.jsonl"
                    path.replace(target)
                    os.link(target, path)
                elif mutation == "source_directory_symlink":
                    source_root = Path(summary["source_run"])
                    path = next(source_root.rglob("*.jsonl")).parent
                    target = root / "outside-source-directory"
                    path.replace(target)
                    path.symlink_to(target, target_is_directory=True)
                elif mutation == "output_lexical_alias":
                    summary["outputs"][0]["path"] = summary["outputs"][0][
                        "path"
                    ].replace("/", "//", 1)
                    summary_path.write_text(
                        json.dumps(summary, indent=2, sort_keys=True) + "\n",
                        encoding="utf-8",
                    )
                else:
                    path = curated / summary["outputs"][0]["path"]
                    target = curated / "aliased-output.bin"
                    path.replace(target)
                    if mutation == "output_symlink":
                        path.symlink_to(target)
                    else:
                        os.link(target, path)

                with self.assertRaises(export_hf.ExportError):
                    export_hf.export_run(curated, root / "export")
                self.assertFalse((root / "export").exists())


class ExportAuditByteCapture(unittest.TestCase):
    def test_audit_uses_captured_bytes_when_output_changes_before_the_gate(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root / "run" / "multi-agent-coordination-factory"
            first = multi_agent("a")
            second = multi_agent("b")
            second["goal"] = "cover the TTL race before merge"
            second["transcript"][0]["content"] = "The race is real; stop the patch."
            second["joint_outcome"] = "reverted until the TTL test lands"
            records = [first, second]
            write_jsonl(source / "batch-r01.jsonl", records)
            curated = root / "curated"
            compose_curated.compose_run(root / "run", curated)
            output = (
                curated
                / compose_curated.RECORDS_DIRNAME
                / "multi-agent-coordination-factory"
                / "batch-r01.jsonl"
            )
            safe_payload = output.read_bytes()
            unsafe_documents = [
                json.loads(line)
                for line in safe_payload.decode("utf-8").split("\n")
                if line
            ]
            unsafe_documents[0]["thought"] = "hidden payload captured before the audit"
            unsafe_payload = "".join(
                compose_curated.canonical_json(record) + "\n"
                for record in unsafe_documents
            ).encode("utf-8")
            output.write_bytes(unsafe_payload)
            real_collect = export_hf.collect_files

            def capture_then_replace(records_dir):
                captured = real_collect(records_dir)
                output.write_bytes(safe_payload)
                return captured

            with mock.patch.object(
                export_hf, "collect_files", side_effect=capture_then_replace
            ):
                with self.assertRaisesRegex(export_hf.ExportError, "hidden-thought"):
                    export_hf.export_run(curated, root / "export")
            self.assertFalse((root / "export").exists())


class ExportCli(unittest.TestCase):
    def test_cli_prints_provenance_and_reports_refusals(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            curated = compose_fixture(root)

            stdout = io.StringIO()
            with redirect_stdout(stdout):
                status = export_hf.main([str(curated), str(root / "export")])
            self.assertEqual(status, 0)
            self.assertTrue(json.loads(stdout.getvalue())["training_ready"])

            stderr = io.StringIO()
            with redirect_stdout(io.StringIO()), redirect_stderr(stderr):
                status = export_hf.main([str(curated), str(root / "export")])
            self.assertEqual(status, 2)
            self.assertIn("refusing to overwrite", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
