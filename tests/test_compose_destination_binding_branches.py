"""Fail-closed branches of the pinned compose destination lifecycle."""

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

import compose_destination_binding as binding
import compose_destination_creation as creation
from compose_contract import ComposeError
from compose_destination_branch_support import TempTreeCase

RAW_RELOCATION = "destination: destination was relocated into immutable raw evidence"
UNVERIFIABLE = "destination: cannot verify descriptor outside immutable raw evidence"


class PinnedDestinationCase(TempTreeCase):
    """A real staged destination created next to a separate source run."""

    def setUp(self) -> None:
        super().setUp()
        self.destination = self.root / "curated"
        self.pinned = creation.create_pinned_destination(
            self.make_directory("source"),
            self.destination,
            creation._refuse_existing_destination,
        )
        self.addCleanup(self.pinned.cleanup)

    def entries(self) -> list[str]:
        return sorted(name for name in os.listdir(self.root) if name != "source")

    def assert_refused(self, call, message: str) -> None:
        with self.assertRaises(ComposeError) as caught:
            call()

        self.assertEqual(str(caught.exception), message)


class RawResidencyTests(TempTreeCase):
    def test_lexical_raw_path_is_under_raw(self):
        self.assertIs(binding._is_under_raw(self.root / "outputs" / "raw" / "run"), True)

    def test_unresolvable_raw_check_is_refused(self):
        path = self.root / "curated"
        failing = mock.Mock(side_effect=RuntimeError("symlink loop"))

        # Seam: _path_aliases_raw is the resolving half of the raw residency check.
        with (
            mock.patch.object(binding, "_path_aliases_raw", failing),
            self.assertRaises(ComposeError) as caught,
        ):
            binding._is_under_raw(path)

        self.assertEqual(str(caught.exception), f"cannot resolve destination path safely: {path}")

    def test_unreadable_descriptor_path_is_unverifiable(self):
        with self.assertRaises(ComposeError) as caught:
            binding._descriptor_path(-1, "destination")

        self.assertEqual(str(caught.exception), UNVERIFIABLE)

    def test_vanished_descriptor_path_is_unverifiable(self):
        with self.assertRaises(ComposeError) as caught:
            binding._descriptor_aliases_raw(self.root / "absent", "destination")

        self.assertEqual(str(caught.exception), UNVERIFIABLE)

    def test_descriptor_inside_a_raw_tree_is_relocated(self):
        descriptor = self.open_directory(self.make_directory("outputs", "raw", "run"))

        with self.assertRaises(ComposeError) as caught:
            binding._assert_descriptor_outside_raw(descriptor, "destination")

        self.assertEqual(str(caught.exception), RAW_RELOCATION)

    def test_descriptor_aliasing_raw_is_relocated(self):
        descriptor = self.open_directory(self.make_directory("curated"))

        # Seam: _path_aliases_raw stands in for a bind mount or inode alias of raw.
        with (
            mock.patch.object(binding, "_path_aliases_raw", return_value=True),
            self.assertRaises(ComposeError) as caught,
        ):
            binding._assert_descriptor_outside_raw(descriptor, "destination")

        self.assertEqual(str(caught.exception), RAW_RELOCATION)


class ContainmentTests(TempTreeCase):
    def test_root_and_child_descriptors_are_contained(self):
        root = self.open_directory(self.root)
        child = self.open_directory(self.make_directory("records"))

        self.assertIsNone(binding._assert_descriptor_contained(root, root, "component"))
        self.assertIsNone(binding._assert_descriptor_contained(root, child, "component"))

    def test_escaped_component_is_refused(self):
        root = self.open_directory(self.make_directory("curated"))
        sibling = self.open_directory(self.make_directory("elsewhere"))

        with self.assertRaises(ComposeError) as caught:
            binding._assert_descriptor_contained(root, sibling, "component")

        self.assertEqual(
            str(caught.exception), "component: component escaped its pinned destination root"
        )


class TargetDispatchTests(PinnedDestinationCase):
    def test_raw_descriptor_targets_pass_through(self):
        descriptor = self.open_directory(self.root)

        self.assertEqual(binding._destination_descriptor(descriptor), descriptor)
        self.assertIsNone(binding._verify_destination_target(descriptor))

    def test_pinned_targets_resolve_and_verify_their_root(self):
        self.assertEqual(
            binding._destination_descriptor(self.pinned), self.pinned.destination_descriptor
        )
        self.assertIsNone(binding._verify_destination_target(self.pinned))


class ClosedPinTests(PinnedDestinationCase):
    def setUp(self) -> None:
        super().setUp()
        self.pinned.cleanup()

    def test_cleanup_is_idempotent(self):
        self.pinned.cleanup()

        self.assertIs(self.pinned.closed, True)

    def test_closed_pin_cannot_be_verified(self):
        self.assert_refused(self.pinned.verify_binding, binding.DESTINATION_PIN_CLOSED)

    def test_closed_pin_cannot_begin_commit(self):
        self.assert_refused(self.pinned.begin_commit, binding.DESTINATION_PIN_CLOSED)

    def test_closed_pin_cannot_finish(self):
        self.assert_refused(self.pinned.finish, binding.DESTINATION_PIN_CLOSED)


class StagedEntryTests(PinnedDestinationCase):
    def swap_staged_entry(self) -> tuple[int, int, int]:
        staged = self.root / self.pinned.staged_name
        staged.rename(self.root / "detached")
        staged.mkdir()
        return binding._directory_identity(staged.lstat())

    def test_swapped_staged_entry_changed_while_pinned(self):
        self.swap_staged_entry()

        self.assert_refused(self.pinned.verify_binding, "destination changed while it was pinned")

    def test_descriptor_identity_drift_changed_while_pinned(self):
        self.pinned.destination_identity = self.swap_staged_entry()

        self.assert_refused(self.pinned.verify_binding, "destination changed while it was pinned")

    def test_unexpected_directory_blocks_commit(self):
        (self.pinned.root / "stray").mkdir()

        self.assert_refused(
            self.pinned.finish, "destination tree directory set changed before commit"
        )
        self.assertIs(self.pinned.closed, True)
        self.assertNotIn("curated", self.entries())

    def test_unexpected_file_blocks_commit(self):
        (self.pinned.root / "stray.jsonl").write_bytes(b"{}\n")

        self.assert_refused(
            self.pinned.finish, "destination tree bytes or member set changed before commit"
        )
        self.assertNotIn("curated", self.entries())

    def test_racing_public_name_is_never_replaced(self):
        self.destination.mkdir()
        (self.destination / "keep.txt").write_bytes(b"owner")

        with self.assertRaises(ComposeError) as caught:
            self.pinned.finish()

        self.assertRegex(str(caught.exception), r"^destination publication failed: \[Errno 17\]")
        self.assertEqual((self.destination / "keep.txt").read_bytes(), b"owner")


class PublicationIdentityTests(PinnedDestinationCase):
    def test_swapped_publication_is_refused_and_left_in_place(self):
        original = binding._rename_noreplace

        def publish_then_swap(parent_descriptor, source_name, destination_name):
            original(parent_descriptor, source_name, destination_name)
            self.destination.rename(self.root / "published-original")
            self.destination.mkdir()

        # Seam: _rename_noreplace is the publication step; the swap races right after it.
        with (
            mock.patch.object(binding, "_rename_noreplace", publish_then_swap),
            self.assertRaises(ComposeError) as caught,
        ):
            self.pinned.finish()

        self.assertEqual(str(caught.exception), "published destination identity changed")
        self.assertTrue(self.destination.is_dir())
        self.assertIn("published-original", self.entries())


class UnstagedPinTests(PinnedDestinationCase):
    def setUp(self) -> None:
        super().setUp()
        self.pinned._publish_staged()

    def test_unstaged_pin_cannot_verify_a_staged_entry(self):
        self.assert_refused(
            self.pinned._verify_staged_entry, "destination is not staged for commit"
        )

    def test_unstaged_pin_cannot_publish(self):
        self.assert_refused(self.pinned._publish_staged, "destination is not staged for commit")

    def test_relocated_public_name_changed_while_pinned(self):
        self.destination.rename(self.root / "moved")

        self.assert_refused(
            self.pinned.verify_binding,
            f"destination changed while it was pinned: {self.destination}",
        )

    def test_begin_commit_restages_a_published_pin(self):
        self.pinned.begin_commit()

        self.assertTrue(self.pinned.staged_name.startswith(".synthetic-factory-commit-"))
        self.assertNotIn("curated", self.entries())

    def test_finish_republishes_after_restaging(self):
        self.pinned.finish()

        self.assertIs(self.pinned.closed, True)
        self.assertEqual(self.entries(), ["curated"])

    def test_cleanup_detaches_the_public_name_without_deleting_it(self):
        self.pinned.cleanup()

        remaining = self.entries()
        self.assertEqual(len(remaining), 1)
        self.assertTrue(remaining[0].startswith(".synthetic-factory-rollback-"))


if __name__ == "__main__":
    unittest.main()
