"""Fail-closed branches of exclusive compose destination creation."""

from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path
from unittest import mock

TESTS = Path(__file__).resolve().parent
for _path in (TESTS, TESTS.parent / "pipelines"):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

import compose_destination_creation as creation
import compose_destination_directory as directory
from compose_contract import ComposeError
from compose_destination_branch_support import TempTreeCase

TAKEN = ".synthetic-factory-taken"


class CreationCase(TempTreeCase):
    def setUp(self) -> None:
        super().setUp()
        self.source = self.make_directory("source")

    def create(self, destination: Path, refuse_existing=creation._refuse_existing_destination):
        pinned = creation.create_pinned_destination(self.source, destination, refuse_existing)
        self.addCleanup(pinned.cleanup)
        return pinned

    def assert_creation_refused(self, destination: Path, message: str, **options) -> None:
        with self.assertRaises(ComposeError) as caught:
            self.create(destination, **options)

        self.assertEqual(str(caught.exception), message)

    def visible_entries(self) -> list[str]:
        return sorted(os.listdir(self.root))


class DisjointTreeTests(unittest.TestCase):
    def assert_disjoint_refused(self, source: str, destination: str, message: str) -> None:
        source_path, destination_path = Path(source), Path(destination)

        with self.assertRaises(ComposeError) as caught:
            creation._assert_destination_disjoint(source_path, destination_path)

        self.assertEqual(str(caught.exception), message)

    def test_destination_cannot_replace_the_source(self):
        self.assert_disjoint_refused(
            "/runs/source", "/runs/source", "destination cannot replace the source run"
        )

    def test_destination_cannot_sit_inside_the_source(self):
        self.assert_disjoint_refused(
            "/runs/source",
            "/runs/source/curated",
            "destination cannot be written inside the source run",
        )

    def test_destination_cannot_contain_the_source(self):
        self.assert_disjoint_refused(
            "/runs/source", "/runs", "destination cannot contain the source run"
        )


class NewDestinationTests(CreationCase):
    def test_existing_destination_is_never_overwritten(self):
        existing = self.make_directory("curated")

        self.assert_creation_refused(
            existing, f"refusing to overwrite an existing destination: {existing}"
        )

    def test_dangling_symlink_destination_is_never_overwritten(self):
        dangling = self.root / "curated"
        dangling.symlink_to(self.root / "absent")

        self.assert_creation_refused(
            dangling, f"refusing to overwrite an existing destination: {dangling}"
        )

    def test_destination_inside_a_raw_tree_is_refused(self):
        destination = self.make_directory("outputs", "raw") / "curated"

        self.assert_creation_refused(
            destination, f"refusing to write inside immutable raw evidence: {destination}"
        )
        self.assertEqual(os.listdir(destination.parent), [])

    def test_destination_inside_the_source_is_refused(self):
        self.assert_creation_refused(
            self.source / "curated", "destination cannot be written inside the source run"
        )

    def test_missing_destination_parent_is_refused(self):
        parent = self.root / "absent"

        self.assert_creation_refused(parent / "curated", f"destination parent is missing: {parent}")

    def test_symlinked_destination_parent_is_refused(self):
        parent = self.root / "alias"
        parent.symlink_to(self.make_directory("real"), target_is_directory=True)

        self.assert_creation_refused(
            parent / "curated",
            f"destination parent must be an exact non-symlink directory: {parent}",
        )


class PinnedParentTests(CreationCase):
    def test_existing_name_under_the_pinned_parent_is_refused(self):
        existing = self.make_directory("curated")
        parent = self.open_directory(self.root)

        with self.assertRaises(ComposeError) as caught:
            creation._refuse_existing_destination(parent, existing)

        self.assertEqual(
            str(caught.exception), f"refusing to overwrite an existing destination: {existing}"
        )

    def test_regular_file_descriptor_is_not_path_addressable(self):
        regular = self.root / "file"
        regular.write_bytes(b"")
        descriptor = self.open_file(regular)

        with self.assertRaises(ComposeError) as caught:
            creation._pinned_root_path(descriptor)

        self.assertEqual(
            str(caught.exception), "pinned destination descriptor is not path-addressable"
        )

    def test_created_regular_file_is_not_a_destination(self):
        destination = self.root / "curated"
        destination.write_bytes(b"")
        parent = self.open_directory(self.root)

        with self.assertRaises(ComposeError) as caught:
            creation._created_destination_identity(parent, destination)

        self.assertEqual(
            str(caught.exception), f"new destination is not a directory: {destination}"
        )

    def test_identity_drift_while_opening_is_refused(self):
        destination = self.make_directory("curated")
        parent = self.open_directory(self.root)
        flags = creation._directory_open_flags()

        with self.assertRaises(ComposeError) as caught:
            creation._open_created_destination(parent, destination, flags, (0, 0, 0))

        self.assertEqual(str(caught.exception), "destination identity changed while opening")


class PrivateDestinationTests(CreationCase):
    def test_every_private_name_colliding_is_refused(self):
        self.make_directory(TAKEN)
        parent = self.open_directory(self.root)

        # Seam: _private_entry_name is pinned to one already-existing sibling.
        with (
            mock.patch.object(creation, "_private_entry_name", return_value=TAKEN),
            self.assertRaises(ComposeError) as caught,
        ):
            creation._create_private_destination(parent, self.root / "curated")

        self.assertEqual(str(caught.exception), "cannot allocate a private destination name")

    def test_private_destination_under_a_deleted_parent_is_refused(self):
        doomed = self.make_directory("doomed")
        parent = self.open_directory(doomed)
        doomed.rmdir()

        with self.assertRaises(ComposeError) as caught:
            creation._create_private_destination(parent, doomed / "curated")

        self.assertRegex(str(caught.exception), r"^cannot create private destination: \[Errno 2\]")


class CreationRollbackTests(CreationCase):
    def test_refused_existing_check_leaves_nothing_behind(self):
        def refuse(_parent_descriptor: int, destination: Path) -> None:
            raise ComposeError(f"raced: {destination.name}")

        self.assert_creation_refused(
            self.root / "curated", "raced: curated", refuse_existing=refuse
        )
        self.assertEqual(self.visible_entries(), ["source"])

    def test_failure_after_creation_detaches_the_private_root(self):
        foreign = mock.Mock(return_value=os.geteuid() + 1)

        # Seam: geteuid stands in for a private root owned by another user.
        with mock.patch.object(directory.os, "geteuid", foreign):
            self.assert_creation_refused(
                self.root / "curated",
                "destination: new directory has unexpected ownership metadata",
            )

        entries = self.visible_entries()
        self.assertNotIn("curated", entries)
        self.assertEqual(len(entries), 2)
        self.assertTrue(entries[0].startswith(".synthetic-factory-rollback-"))

    def test_successful_creation_is_staged_privately(self):
        pinned = self.create(self.root / "curated")

        self.assertTrue(pinned.staged_name.startswith(".synthetic-factory-destination-"))
        self.assertNotIn("curated", self.visible_entries())
        self.assertEqual(pinned.root, Path(f"/proc/self/fd/{pinned.destination_descriptor}"))


if __name__ == "__main__":
    unittest.main()
