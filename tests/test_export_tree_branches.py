"""Fail-closed branches of curated-tree reads and export destination validation."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

TESTS = Path(__file__).resolve().parent
for _path in (TESTS, TESTS.parent / "pipelines"):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

import export_curated
import export_destination
from compose_destination_branch_support import TempTreeCase
from export_contract import CuratedFile, ExportError

EXISTING = "refusing to overwrite an existing destination: {}"


class ExportTreeCase(TempTreeCase):
    def assert_refused(self, message: str, call, *args) -> None:
        with self.assertRaises(ExportError) as caught:
            call(*args)

        self.assertEqual(str(caught.exception), message)


class CuratedFileTests(ExportTreeCase):
    def test_curated_file_is_read_from_disk_when_no_payload_is_supplied(self):
        member = self.root / "a.jsonl"
        member.write_bytes(b'{"a": 1}\n{"b": 2}\n')

        curated = export_curated._read_curated_file(member, "f/a.jsonl")

        self.assertEqual(curated.source_file, "data/curated/f/a.jsonl")
        self.assertEqual([row.source_line for row in curated.rows], [1, 2])

    def test_rows_follow_path_then_line_order(self):
        factory = self.make_directory("records", "f")
        (factory / "b.jsonl").write_bytes(b'{"b": 1}\n')
        (factory / "a.jsonl").write_bytes(b'{"a": 1}\n{"a": 2}\n')

        rows = export_curated.collect_rows(self.root / "records")

        self.assertEqual(
            [(row.source_file, row.source_line) for row in rows],
            [
                ("data/curated/f/a.jsonl", 1),
                ("data/curated/f/a.jsonl", 2),
                ("data/curated/f/b.jsonl", 1),
            ],
        )

    def test_foreign_source_path_cannot_be_snapshotted(self):
        foreign = CuratedFile(source_file="data/other/a.jsonl", payload=b"", rows=())

        self.assert_refused(
            "invalid curated source path: data/other/a.jsonl",
            export_curated._snapshot_payloads,
            [foreign],
        )

    def test_duplicate_snapshot_path_is_refused(self):
        curated = CuratedFile(source_file="data/curated/a.jsonl", payload=b"", rows=())

        self.assert_refused(
            "duplicate curated snapshot path: a.jsonl",
            export_curated._snapshot_payloads,
            [curated, curated],
        )


class CuratedTreeValidationTests(ExportTreeCase):
    def test_curated_root_without_records_is_refused(self):
        curated = self.make_directory("curated")

        self.assert_refused(
            f"curated root has no exact records/ payload: {curated}",
            export_destination._validated_curated_tree,
            curated,
        )

    def test_destination_inside_the_curated_root_is_refused(self):
        curated = self.make_directory("curated")
        self.make_directory("curated", "records")

        self.assert_refused(
            "destination cannot be written inside the curated root",
            export_destination._validated_export_paths,
            curated,
            curated / "export",
        )

    def test_curated_root_itself_is_not_a_destination(self):
        curated = self.make_directory("curated")

        self.assert_refused(
            "destination cannot be written inside the curated root",
            export_destination._require_destination_outside_curated,
            curated,
            curated,
        )


class NewExportDestinationTests(ExportTreeCase):
    def test_existing_destination_is_never_overwritten(self):
        existing = self.make_directory("export")

        self.assert_refused(
            EXISTING.format(existing), export_destination._require_new_export_destination, existing
        )

    def test_destination_inside_a_raw_tree_is_refused(self):
        destination = self.make_directory("outputs", "raw") / "export"

        self.assert_refused(
            f"refusing to write inside immutable raw evidence: {destination}",
            export_destination._require_new_export_destination,
            destination,
        )

    def test_missing_destination_parent_is_refused(self):
        parent = self.root / "absent"

        self.assert_refused(
            f"destination parent does not exist: {parent}",
            export_destination._require_new_export_destination,
            parent / "export",
        )

    def test_symlinked_destination_parent_is_refused(self):
        alias = self.root / "alias"
        alias.symlink_to(self.make_directory("real"), target_is_directory=True)

        self.assert_refused(
            "destination parent: directory path must be an exact non-symlink identity",
            export_destination._require_new_export_destination,
            alias / "export",
        )

    def test_destination_inside_the_compose_source_is_refused(self):
        source = self.make_directory("source")
        metadata = {"source": {"path": str(source)}}

        self.assert_refused(
            "destination cannot be written inside the authenticated compose source",
            export_destination._refuse_authenticated_source_destination,
            metadata,
            source / "export",
        )

    def test_compose_source_itself_is_not_a_destination(self):
        source = self.make_directory("source")

        self.assert_refused(
            "destination cannot be written inside the authenticated compose source",
            export_destination._refuse_authenticated_source_destination,
            {"source": {"path": str(source)}},
            source,
        )


class PinnedExportWriteTests(ExportTreeCase):
    def setUp(self) -> None:
        super().setUp()
        self.curated = self.make_directory("curated")
        self.destination = self.root / "export"

    def test_existing_pinned_destination_is_reported_as_an_export_error(self):
        self.destination.mkdir()

        self.assert_refused(
            EXISTING.format(self.destination),
            export_destination._create_pinned_destination,
            self.curated,
            self.destination,
        )

    def test_unsafe_relative_write_is_reported_as_an_export_error(self):
        pinned = export_destination._create_pinned_destination(self.curated, self.destination)
        self.addCleanup(pinned.cleanup)

        self.assert_refused(
            "export ../escape: unsafe destination path '../escape'",
            export_destination._write_new_bytes,
            pinned,
            "../escape",
            b"",
        )

    def test_failed_finish_is_reported_as_an_export_error(self):
        pinned = export_destination._create_pinned_destination(self.curated, self.destination)
        self.addCleanup(pinned.cleanup)
        (pinned.root / "stray").mkdir()

        self.assert_refused(
            "destination tree directory set changed before commit",
            export_destination._finish_pinned_destination,
            pinned,
        )
        self.assertFalse(self.destination.exists())

    def test_written_bytes_are_published_on_finish(self):
        pinned = export_destination._create_pinned_destination(self.curated, self.destination)
        self.addCleanup(pinned.cleanup)
        export_destination._write_new_bytes(pinned, "data/a.jsonl", b"{}\n")

        export_destination._finish_pinned_destination(pinned)

        self.assertEqual((self.destination / "data" / "a.jsonl").read_bytes(), b"{}\n")


if __name__ == "__main__":
    unittest.main()
