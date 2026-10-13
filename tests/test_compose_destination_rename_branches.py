"""Fail-closed branches of no-replace renames and owned-entry moves."""

from __future__ import annotations

import errno
import os
import sys
import types
import unittest
from pathlib import Path
from unittest import mock

TESTS = Path(__file__).resolve().parent
for _path in (TESTS, TESTS.parent / "pipelines"):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

import compose_destination_rename as rename
from compose_contract import ComposeError
from compose_destination_branch_support import TempTreeCase

TAKEN = ".synthetic-factory-taken"


class OwnedEntryCase(TempTreeCase):
    """A pinned temp parent holding one owned directory entry."""

    def setUp(self) -> None:
        super().setUp()
        self.owned = self.make_directory("owned")
        self.parent = self.open_directory(self.root)
        self.identity = rename.entry_identity(self.parent, "owned")

    def move(self, *, strict: bool, identity=None) -> rename.OwnedEntryMove:
        return rename.OwnedEntryMove(
            self.parent,
            "owned",
            self.identity if identity is None else identity,
            prefix="rollback",
            label="destination rollback",
            strict=strict,
        )


class RenameNoReplaceTests(TempTreeCase):
    def test_missing_renameat2_is_reported_as_unsupported(self):
        parent = self.open_directory(self.root)
        libc_without_renameat2 = mock.Mock(return_value=types.SimpleNamespace())

        # Seam: ctypes.CDLL stands in for a libc that lacks renameat2.
        with (
            mock.patch.object(rename.ctypes, "CDLL", libc_without_renameat2),
            self.assertRaises(OSError) as caught,
        ):
            rename.rename_noreplace(parent, "a", "b")

        self.assertEqual(caught.exception.errno, errno.ENOSYS)

    def test_existing_destination_is_never_replaced(self):
        self.make_directory("source")
        self.make_directory("target")
        parent = self.open_directory(self.root)

        with self.assertRaises(FileExistsError):
            rename.rename_noreplace(parent, "source", "target")

        self.assertEqual(sorted(os.listdir(self.root)), ["source", "target"])

    def test_missing_entry_has_no_identity(self):
        parent = self.open_directory(self.root)

        self.assertIsNone(rename.entry_identity(parent, "absent"))


class OwnedEntryRenameErrorTests(OwnedEntryCase):
    def test_strict_move_refuses_any_rename_error(self):
        failing = mock.Mock(side_effect=OSError(errno.EACCES, "denied"))

        # Seam: rename_noreplace is the module's only rename primitive.
        with (
            mock.patch.object(rename, "rename_noreplace", failing),
            self.assertRaises(ComposeError) as caught,
        ):
            self.move(strict=True).move()

        self.assertEqual(
            str(caught.exception),
            "destination rollback: atomic private rename failed: [Errno 13] denied",
        )

    def test_lenient_move_refuses_an_unsupported_atomic_rename(self):
        failing = mock.Mock(side_effect=OSError(errno.EXDEV, "cross-device"))

        # Seam: rename_noreplace is the module's only rename primitive.
        with (
            mock.patch.object(rename, "rename_noreplace", failing),
            self.assertRaises(ComposeError) as caught,
        ):
            self.move(strict=False).move()

        self.assertEqual(
            str(caught.exception),
            "destination rollback: atomic private rename failed: [Errno 18] cross-device",
        )

    def test_lenient_move_gives_up_quietly_on_other_errors(self):
        failing = mock.Mock(side_effect=OSError(errno.EACCES, "denied"))

        # Seam: rename_noreplace is the module's only rename primitive.
        with mock.patch.object(rename, "rename_noreplace", failing):
            moved = self.move(strict=False).move()

        self.assertIsNone(moved)
        self.assertTrue(self.owned.is_dir())


class OwnedEntryCollisionTests(OwnedEntryCase):
    def setUp(self) -> None:
        super().setUp()
        self.make_directory(TAKEN)

    def test_strict_move_refuses_when_every_private_name_collides(self):
        # Seam: private_entry_name is pinned to one already-existing sibling.
        with (
            mock.patch.object(rename, "private_entry_name", return_value=TAKEN),
            self.assertRaises(ComposeError) as caught,
        ):
            self.move(strict=True).move()

        self.assertEqual(
            str(caught.exception),
            "destination rollback: cannot allocate a private transaction name",
        )

    def test_lenient_move_returns_none_when_every_private_name_collides(self):
        # Seam: private_entry_name is pinned to one already-existing sibling.
        with mock.patch.object(rename, "private_entry_name", return_value=TAKEN):
            moved = self.move(strict=False).move()

        self.assertIsNone(moved)
        self.assertTrue(self.owned.is_dir())


class OwnedEntryAuthenticationTests(OwnedEntryCase):
    def test_strict_move_restores_and_refuses_a_foreign_identity(self):
        with self.assertRaises(ComposeError) as caught:
            self.move(strict=True, identity=(0, 0, 0)).move()

        self.assertEqual(
            str(caught.exception),
            "destination rollback: entry identity changed before private rename",
        )
        self.assertEqual(os.listdir(self.root), ["owned"])

    def test_lenient_move_restores_a_foreign_identity_and_returns_none(self):
        moved = self.move(strict=False, identity=(0, 0, 0)).move()

        self.assertIsNone(moved)
        self.assertEqual(os.listdir(self.root), ["owned"])

    def test_failed_restore_is_tolerated_before_the_strict_refusal(self):
        # The first call "moves" nothing, so the private name has no identity and
        # the restore attempt fails; the strict refusal must still be raised.
        renames = mock.Mock(side_effect=[None, OSError(errno.ENOENT, "gone")])

        # Seam: rename_noreplace is the module's only rename primitive.
        with (
            mock.patch.object(rename, "rename_noreplace", renames),
            self.assertRaises(ComposeError) as caught,
        ):
            self.move(strict=True).move()

        self.assertEqual(
            str(caught.exception),
            "destination rollback: entry identity changed before private rename",
        )
        self.assertEqual(renames.call_count, 2)


class StageAndQuarantineTests(OwnedEntryCase):
    def test_stage_refuses_an_entry_that_disappeared(self):
        self.owned.rmdir()

        with self.assertRaises(ComposeError) as caught:
            rename.stage_owned_entry(self.parent, "owned", self.identity, "destination commit")

        self.assertEqual(
            str(caught.exception), "destination commit: entry disappeared before private rename"
        )

    def test_stage_moves_the_owned_entry_to_a_private_commit_name(self):
        staged = rename.stage_owned_entry(self.parent, "owned", self.identity, "commit")

        self.assertTrue(staged.startswith(".synthetic-factory-commit-"))
        self.assertEqual(os.listdir(self.root), [staged])

    def test_quarantine_of_a_missing_entry_returns_none(self):
        self.owned.rmdir()

        self.assertIsNone(
            rename.quarantine_owned_entry(self.parent, "owned", self.identity, "rollback")
        )


if __name__ == "__main__":
    unittest.main()
