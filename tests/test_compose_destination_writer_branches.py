"""Fail-closed branches of descriptor-pinned compose destination writes."""

from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path, PurePosixPath
from unittest import mock

TESTS = Path(__file__).resolve().parent
for _path in (TESTS, TESTS.parent / "pipelines"):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

import compose_destination_writer as writer
from compose_contract import ComposeError
from compose_destination_branch_support import TempTreeCase

TAKEN = ".synthetic-factory-taken"
NOT_A_POSIX_STRING = "export: destination path must be a nonempty POSIX string"


class WriterCase(TempTreeCase):
    def setUp(self) -> None:
        super().setUp()
        self.parent = self.open_directory(self.root)

    def assert_refused(self, message: str, call, *args) -> None:
        with self.assertRaises(ComposeError) as caught:
            call(*args)

        self.assertEqual(str(caught.exception), message)

    def entries(self) -> list[str]:
        return sorted(os.listdir(self.root))


class DestinationPartsTests(unittest.TestCase):
    def assert_parts_refused(self, relative, message: str) -> None:
        with self.assertRaises(ComposeError) as caught:
            writer._destination_write_parts(relative, "export")

        self.assertEqual(str(caught.exception), message)

    def test_non_string_path_is_refused(self):
        self.assert_parts_refused(7, NOT_A_POSIX_STRING)

    def test_empty_path_is_refused(self):
        self.assert_parts_refused("", NOT_A_POSIX_STRING)

    def test_windows_separator_is_refused(self):
        self.assert_parts_refused("data\\train.jsonl", NOT_A_POSIX_STRING)

    def test_nul_byte_is_unsafe(self):
        self.assert_parts_refused("a\0b", "export: unsafe destination path 'a\\x00b'")

    def test_non_canonical_spelling_is_unsafe(self):
        self.assert_parts_refused(
            "data//train.jsonl", "export: unsafe destination path 'data//train.jsonl'"
        )

    def test_absolute_path_is_unsafe(self):
        self.assert_parts_refused("/etc/passwd", "export: unsafe destination path '/etc/passwd'")

    def test_traversal_component_is_unsafe(self):
        self.assert_parts_refused("data/../raw", "export: unsafe destination path 'data/../raw'")

    def test_pure_posix_path_is_accepted_as_text(self):
        parts = writer._destination_write_parts(PurePosixPath("data/train.jsonl"), "export")

        self.assertEqual(parts, ("data", "train.jsonl"))


class ChildDirectoryTests(WriterCase):
    def test_existing_component_is_not_reported_as_created(self):
        self.make_directory("records")

        self.assertIs(writer._create_child_directory(self.parent, "records", "export"), False)

    def test_component_under_a_file_cannot_be_created(self):
        (self.root / "file").write_bytes(b"")
        descriptor = self.open_file(self.root / "file")

        with self.assertRaises(ComposeError) as caught:
            writer._create_child_directory(descriptor, "records", "export")

        self.assertRegex(
            str(caught.exception), r"^export: cannot create directory component 'records': "
        )

    def test_new_component_is_reported_as_created(self):
        self.assertIs(writer._create_child_directory(self.parent, "records", "export"), True)
        self.assertTrue((self.root / "records").is_dir())

    def test_symlinked_component_is_not_an_exact_directory(self):
        (self.root / "records").symlink_to(self.make_directory("elsewhere"))

        self.assert_refused(
            "export: directory component 'records' is not an exact directory",
            writer._open_child_directory_entry,
            self.parent,
            "records",
            "export",
        )


class VerifyPinnedChildTests(WriterCase):
    MESSAGE = "export: directory component 'records' changed while it was pinned"

    def test_entry_replaced_by_a_file_changed_while_pinned(self):
        (self.root / "records").write_bytes(b"")
        descriptor = self.open_directory(self.make_directory("other"))

        self.assert_refused(
            self.MESSAGE, writer._verify_pinned_child, descriptor, self.parent, "records", "export"
        )

    def test_file_descriptor_changed_while_pinned(self):
        self.make_directory("records")
        (self.root / "file").write_bytes(b"")
        descriptor = self.open_file(self.root / "file")

        self.assert_refused(
            self.MESSAGE, writer._verify_pinned_child, descriptor, self.parent, "records", "export"
        )

    def test_different_directory_changed_while_pinned(self):
        self.make_directory("records")
        descriptor = self.open_directory(self.make_directory("other"))

        self.assert_refused(
            self.MESSAGE, writer._verify_pinned_child, descriptor, self.parent, "records", "export"
        )


class OpenPinnedChildTests(WriterCase):
    def test_component_under_a_file_cannot_be_inspected(self):
        (self.root / "file").write_bytes(b"")
        descriptor = self.open_file(self.root / "file")

        with self.assertRaises(ComposeError) as caught:
            writer._open_pinned_child_directory(descriptor, "records", "export")

        self.assertRegex(
            str(caught.exception), r"^export: cannot inspect directory component 'records': "
        )

    def test_existing_component_is_reused_without_creation(self):
        self.make_directory("records")

        descriptor, created = writer._open_pinned_child_directory(self.parent, "records", "export")
        self.addCleanup(os.close, descriptor)

        self.assertIs(created, False)

    def test_missing_component_is_created_and_published(self):
        descriptor, created = writer._open_pinned_child_directory(self.parent, "records", "export")
        self.addCleanup(os.close, descriptor)

        self.assertIs(created, True)
        self.assertEqual(self.entries(), ["records"])

    def test_existing_component_failing_verification_is_released(self):
        self.make_directory("records")
        failing = mock.Mock(side_effect=ComposeError("pinned check failed"))

        # Seam: _verify_pinned_child is the check between the open and the return.
        with (
            mock.patch.object(writer, "_verify_pinned_child", failing),
            self.assertRaises(ComposeError) as caught,
        ):
            writer._open_pinned_child_directory(self.parent, "records", "export")

        self.assertEqual(str(caught.exception), "pinned check failed")
        self.assertEqual(self.entries(), ["records"])


class PrivateChildTests(WriterCase):
    def test_every_private_name_colliding_is_refused(self):
        self.make_directory(TAKEN)

        # Seam: _private_entry_name is pinned to one already-existing sibling.
        with (
            mock.patch.object(writer, "_private_entry_name", return_value=TAKEN),
            self.assertRaises(ComposeError) as caught,
        ):
            writer._create_private_child(self.parent, "export")

        self.assertEqual(str(caught.exception), "export: cannot allocate a private directory name")

    def test_private_child_under_a_deleted_parent_is_refused(self):
        doomed = self.make_directory("doomed")
        descriptor = self.open_directory(doomed)
        doomed.rmdir()

        with self.assertRaises(ComposeError) as caught:
            writer._create_private_child(descriptor, "export")

        self.assertRegex(str(caught.exception), r"^export: cannot create private directory: ")


class PublishChildTests(WriterCase):
    def test_racing_public_component_is_never_replaced(self):
        raced = self.make_directory("records")
        (raced / "keep.txt").write_bytes(b"owner")

        with self.assertRaises(ComposeError) as caught:
            writer._create_and_publish_child_directory(self.parent, "records", "export")

        self.assertRegex(
            str(caught.exception), r"^export: cannot publish directory component 'records': "
        )
        self.assertEqual((raced / "keep.txt").read_bytes(), b"owner")
        rollback = [name for name in self.entries() if name != "records"]
        self.assertEqual(len(rollback), 1)
        self.assertTrue(rollback[0].startswith(".synthetic-factory-rollback-"))

    def publish_with_failing(self, seam: str, failure: mock.Mock) -> list[str]:
        """Publish ``records`` while one named writer seam fails; return the entries left."""

        with (
            mock.patch.object(writer, seam, failure),
            self.assertRaises(ComposeError) as caught,
        ):
            writer._create_and_publish_child_directory(self.parent, "records", "export")

        self.assertEqual(str(caught.exception), "seam failed")
        return self.entries()

    def test_published_component_failing_verification_is_detached(self):
        # Seam: the second _verify_pinned_child call checks the published name.
        checks = mock.Mock(side_effect=[None, ComposeError("seam failed")])

        entries = self.publish_with_failing("_verify_pinned_child", checks)

        self.assertNotIn("records", entries)
        self.assertTrue(entries[0].startswith(".synthetic-factory-rollback-"))

    def test_private_component_that_cannot_be_opened_is_detached(self):
        # Seam: _open_child_directory_entry fails after the private identity is known.
        failing = mock.Mock(side_effect=ComposeError("seam failed"))

        entries = self.publish_with_failing("_open_child_directory_entry", failing)

        self.assertEqual(len(entries), 1)
        self.assertTrue(entries[0].startswith(".synthetic-factory-rollback-"))

    def test_unidentified_private_component_is_never_removed(self):
        # Seam: _directory_identity fails before ownership of the private entry is proven.
        failing = mock.Mock(side_effect=ComposeError("seam failed"))

        entries = self.publish_with_failing("_directory_identity", failing)

        self.assertEqual(len(entries), 1)
        self.assertTrue(entries[0].startswith(".synthetic-factory-directory-"))

    def test_missing_entry_has_no_identity(self):
        self.assertIs(writer._entry_has_identity(self.parent, "absent", (0, 0, 0)), False)


class LeafWriteTests(WriterCase):
    def test_existing_leaf_is_never_overwritten(self):
        (self.root / "train.jsonl").write_bytes(b"owner")

        with self.assertRaises(ComposeError) as caught:
            writer._open_new_leaf(self.parent, "train.jsonl", "export")

        self.assertRegex(str(caught.exception), r"^export: cannot create new file 'train.jsonl': ")
        self.assertEqual((self.root / "train.jsonl").read_bytes(), b"owner")

    def test_new_leaf_receives_every_byte(self):
        descriptor = writer._open_new_leaf(self.parent, "train.jsonl", "export")
        try:
            writer._write_all(descriptor, b"{}\n" * 3)
            writer._write_all(descriptor, b"")
        finally:
            os.close(descriptor)

        self.assertEqual((self.root / "train.jsonl").read_bytes(), b"{}\n" * 3)

    def test_file_rollback_detaches_only_the_owned_identity(self):
        leaf = self.root / "train.jsonl"
        leaf.write_bytes(b"")
        identity = writer._directory_identity(leaf.lstat())

        writer._remove_created_file_if_identity(self.parent, "train.jsonl", identity)

        entries = self.entries()
        self.assertEqual(len(entries), 1)
        self.assertTrue(entries[0].startswith(".synthetic-factory-rollback-"))


if __name__ == "__main__":
    unittest.main()
