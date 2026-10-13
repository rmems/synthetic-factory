"""Fail-closed branches of exact directory observation for pinned compose I/O."""

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

import compose_destination_directory as directory
from compose_contract import ComposeError
from compose_destination_branch_support import TempTreeCase


class RequiredObservationTests(TempTreeCase):
    def test_missing_directory_is_reported_as_missing(self):
        missing = self.root / "absent"

        with self.assertRaises(ComposeError) as caught:
            directory.required_directory_observations(missing, "source run")

        self.assertEqual(str(caught.exception), f"source run is missing: {missing}")

    def test_symlink_loop_cannot_be_resolved_safely(self):
        loop = self.root / "loop"
        loop.symlink_to(loop)

        with self.assertRaises(ComposeError) as caught:
            directory.required_directory_observations(loop, "source run")

        self.assertEqual(str(caught.exception), f"source run cannot be resolved safely: {loop}")


class RequireExactDirectoryTests(TempTreeCase):
    def test_regular_file_is_not_an_exact_directory(self):
        regular = self.root / "file.jsonl"
        regular.write_bytes(b"{}\n")

        with self.assertRaises(ComposeError) as caught:
            directory.require_exact_directory(regular, "destination parent")

        self.assertEqual(
            str(caught.exception),
            f"destination parent must be an exact non-symlink directory: {regular}",
        )

    def test_symlinked_directory_alias_is_refused(self):
        target = self.make_directory("target")
        alias = self.root / "alias"
        alias.symlink_to(target, target_is_directory=True)

        with self.assertRaises(ComposeError) as caught:
            directory.require_exact_directory(alias, "destination parent")

        self.assertEqual(
            str(caught.exception),
            f"destination parent must be an exact non-symlink directory: {alias}",
        )

    def test_directory_below_a_symlinked_parent_is_refused(self):
        self.make_directory("real", "child")
        (self.root / "alias").symlink_to(self.root / "real", target_is_directory=True)
        aliased = self.root / "alias" / "child"

        with self.assertRaises(ComposeError) as caught:
            directory.require_exact_directory(aliased, "destination parent")

        self.assertEqual(
            str(caught.exception),
            f"destination parent must be an exact non-symlink directory: {aliased}",
        )

    def test_exact_directory_returns_its_resolved_path(self):
        target = self.make_directory("target")

        self.assertEqual(directory.require_exact_directory(target, "label"), target)


class FreshDirectoryNameTests(TempTreeCase):
    def test_non_directory_descriptor_cannot_be_enumerated(self):
        regular = self.root / "file"
        regular.write_bytes(b"x")
        descriptor = self.open_file(regular)

        with self.assertRaises(ComposeError) as caught:
            directory.fresh_directory_names(descriptor, "destination tree")

        self.assertEqual(
            str(caught.exception), "destination tree: cannot open directory for enumeration"
        )

    def test_identity_drift_before_enumeration_is_refused(self):
        descriptor = self.open_directory(self.root)
        drifting = mock.Mock(side_effect=[(1, 1, 1), (2, 2, 2)])

        # Seam: directory_identity is the only observation the drift check compares.
        with (
            mock.patch.object(directory, "directory_identity", drifting),
            self.assertRaises(ComposeError) as caught,
        ):
            directory.fresh_directory_names(descriptor, "destination tree")

        self.assertEqual(
            str(caught.exception),
            "destination tree: directory identity changed before enumeration",
        )

    def test_listing_failure_is_normalized(self):
        descriptor = self.open_directory(self.root)
        failing = mock.Mock(side_effect=OSError("listing failed"))

        # Seam: os.listdir is the only call that can fail after the identity check.
        with (
            mock.patch.object(directory.os, "listdir", failing),
            self.assertRaises(ComposeError) as caught,
        ):
            directory.fresh_directory_names(descriptor, "destination tree")

        self.assertEqual(str(caught.exception), "destination tree: cannot enumerate directory")

    def test_names_are_sorted(self):
        for name in ("b", "a", "c"):
            (self.root / name).write_bytes(b"")
        descriptor = self.open_directory(self.root)

        self.assertEqual(directory.fresh_directory_names(descriptor, "tree"), ["a", "b", "c"])


class NewDirectoryTests(TempTreeCase):
    def test_nonempty_new_directory_is_refused(self):
        (self.root / "adopted").write_bytes(b"x")
        descriptor = self.open_directory(self.root)

        with self.assertRaises(ComposeError) as caught:
            directory.require_empty_directory(descriptor, "destination")

        self.assertEqual(
            str(caught.exception), "destination: new directory was not empty when pinned"
        )

    def test_unreadable_descriptor_cannot_be_authenticated(self):
        parent = self.open_directory(self.root)

        with self.assertRaises(ComposeError) as caught:
            directory.require_safe_new_directory(-1, parent, "destination")

        self.assertEqual(str(caught.exception), "destination: cannot authenticate new directory")

    def test_regular_file_is_not_a_new_directory(self):
        regular = self.root / "file"
        regular.write_bytes(b"")
        descriptor = self.open_file(regular)
        parent = self.open_directory(self.root)

        with self.assertRaises(ComposeError) as caught:
            directory.require_safe_new_directory(descriptor, parent, "destination")

        self.assertEqual(str(caught.exception), "destination: new entry is not an exact directory")

    def test_foreign_owner_is_refused(self):
        child = self.open_directory(self.make_directory("child"))
        parent = self.open_directory(self.root)
        foreign = mock.Mock(return_value=os.geteuid() + 1)

        # Seam: geteuid stands in for a directory created by another user.
        with (
            mock.patch.object(directory.os, "geteuid", foreign),
            self.assertRaises(ComposeError) as caught,
        ):
            directory.require_safe_new_directory(child, parent, "destination")

        self.assertEqual(
            str(caught.exception), "destination: new directory has unexpected ownership metadata"
        )


class DirectoryBindingTests(TempTreeCase):
    def assert_binding_refused(self, pinned: Path, descriptor: int, **options) -> None:
        with self.assertRaises(ComposeError) as caught:
            directory.verify_directory_binding(pinned, descriptor, "destination", **options)

        self.assertEqual(
            str(caught.exception), f"destination changed while it was pinned: {pinned}"
        )

    def test_vanished_path_changed_while_pinned(self):
        pinned = self.make_directory("pinned")
        descriptor = self.open_directory(pinned)
        pinned.rmdir()

        self.assert_binding_refused(pinned, descriptor)

    def test_swapped_directory_changed_while_pinned(self):
        pinned = self.make_directory("pinned")
        descriptor = self.open_directory(pinned)
        pinned.rename(self.root / "moved")
        pinned.mkdir()

        self.assert_binding_refused(pinned, descriptor)

    def test_unexpected_identity_changed_while_pinned(self):
        pinned = self.make_directory("pinned")
        descriptor = self.open_directory(pinned)

        self.assert_binding_refused(pinned, descriptor, expected_identity=(0, 0, 0))

    def test_binding_match_helper_reports_a_held_binding(self):
        pinned = self.make_directory("pinned")
        descriptor = self.open_directory(pinned)
        metadata = pinned.lstat()
        binding = directory.DirectoryBinding(
            metadata=metadata,
            opened=os.fstat(descriptor),
            resolved=pinned,
            absolute=Path(os.path.abspath(pinned)),
            expected_identity=directory.directory_identity(metadata),
        )

        self.assertIs(directory.directory_binding_matches(binding), True)


if __name__ == "__main__":
    unittest.main()
