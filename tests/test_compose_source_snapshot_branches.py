"""Fail-closed branches of descriptor-authenticated compose source reads."""

from __future__ import annotations

import os
import re
import sys
import unittest
from pathlib import Path
from unittest import mock

TESTS = Path(__file__).resolve().parent
for _path in (TESTS, TESTS.parent / "pipelines"):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

import compose_source_snapshot as snapshot
from compose_contract import ComposeError
from compose_destination_branch_support import TempTreeCase

LABEL = "compose source a.jsonl"
CHANGED_WHILE_READING = f"{LABEL}: source identity changed while reading"
PATH_CHANGED_WHILE_READING = f"{LABEL}: source path identity changed while reading"


def _resolve_under_root(root: Path, raw_path, _label: str) -> Path:
    return root / raw_path


def _assert_path_unchanged(*observations) -> None:
    """The facade's path re-authentication hook over one ``SourcePathRead``."""

    snapshot.assert_source_path_unchanged(snapshot.SourcePathRead(*observations))


def _descriptor_hooks(drain=snapshot._drain_descriptor) -> snapshot.DescriptorReadHooks:
    return snapshot.DescriptorReadHooks(snapshot._assert_opened_source_identity, drain)


def _read_pinned(*observations) -> bytes:
    """The facade's pinned-child reader over one ``PinnedChildRead``."""

    return snapshot.read_pinned_child_bytes(
        snapshot.PinnedChildRead(*observations), _descriptor_hooks()
    )


def _exact_hooks(drain=snapshot._drain_descriptor) -> snapshot.ExactReadHooks:
    return snapshot.ExactReadHooks(
        _resolve_under_root, _descriptor_hooks(drain), _assert_path_unchanged
    )


class SourceCase(TempTreeCase):
    def setUp(self) -> None:
        super().setUp()
        self.member = self.root / "a.jsonl"
        self.member.write_bytes(b"{}\n")

    def assert_refused(self, message: str, call, *args) -> None:
        with self.assertRaises(ComposeError) as caught:
            call(*args)

        self.assertEqual(str(caught.exception), message)


class OpenedIdentityTests(SourceCase):
    def test_directory_is_not_a_regular_source_file(self):
        directory = self.root.stat()

        self.assert_refused(
            f"{LABEL}: opened identity is not a regular file",
            snapshot._assert_opened_source_identity,
            directory,
            directory,
            LABEL,
        )

    def test_hard_link_alias_is_refused(self):
        os.link(self.member, self.root / "b.jsonl")
        linked = self.member.stat()

        self.assert_refused(
            f"{LABEL}: hard-link aliases are not accepted",
            snapshot._assert_opened_source_identity,
            linked,
            linked,
            LABEL,
        )

    def test_identity_change_while_opening_is_refused(self):
        before = self.member.stat()
        (self.root / "b.jsonl").write_bytes(b"[]\n")

        self.assert_refused(
            f"{LABEL}: source identity changed while opening",
            snapshot._assert_opened_source_identity,
            before,
            (self.root / "b.jsonl").stat(),
            LABEL,
        )


class PathReauthenticationTests(SourceCase):
    def read(self, path: Path, opened_after, raw_path="a.jsonl") -> snapshot.SourcePathRead:
        return snapshot.SourcePathRead(path, self.root, raw_path, opened_after, LABEL)

    def test_vanished_member_disappeared_while_reading(self):
        opened = self.member.stat()
        self.member.unlink()

        self.assert_refused(
            f"{LABEL}: source member disappeared while reading",
            snapshot.assert_source_path_unchanged,
            self.read(self.member, opened),
        )

    def test_incomplete_read_changed_while_reading(self):
        self.assert_refused(
            PATH_CHANGED_WHILE_READING,
            snapshot.assert_source_path_unchanged,
            self.read(self.member, None),
        )

    def test_replaced_member_changed_while_reading(self):
        opened = self.member.stat()
        replacement = self.root / "replacement"
        replacement.write_bytes(b"{}\n")
        os.replace(replacement, self.member)

        self.assert_refused(
            PATH_CHANGED_WHILE_READING,
            snapshot.assert_source_path_unchanged,
            self.read(self.member, opened),
        )

    def test_symlinked_parent_alias_is_refused(self):
        real = self.make_directory("real")
        (real / "a.jsonl").write_bytes(b"{}\n")
        (self.root / "alias").symlink_to(real, target_is_directory=True)
        aliased = self.root / "alias" / "a.jsonl"

        self.assert_refused(
            f"{LABEL}: source path became a symlink alias while reading",
            snapshot.assert_source_path_unchanged,
            self.read(aliased, aliased.stat(), raw_path="alias/a.jsonl"),
        )


class ExactRegularReadTests(SourceCase):
    def test_exact_member_bytes_are_returned(self):
        path, payload = snapshot.read_exact_regular_file(
            self.root, "a.jsonl", LABEL, _exact_hooks()
        )

        self.assertEqual((path, payload), (self.member, b"{}\n"))

    def test_symlink_member_cannot_be_opened(self):
        (self.root / "link.jsonl").symlink_to(self.member)
        hooks = _exact_hooks()

        with self.assertRaises(ComposeError) as caught:
            snapshot.read_exact_regular_file(self.root, "link.jsonl", LABEL, hooks)

        self.assertRegex(
            str(caught.exception), "^" + re.escape(f"{LABEL}: cannot open exact source file: ")
        )

    def test_member_growing_during_the_read_is_refused(self):
        def drain_then_append(descriptor: int) -> bytes:
            payload = snapshot._drain_descriptor(descriptor)
            with self.member.open("ab") as handle:
                handle.write(b"{}\n")
            return payload

        hooks = _exact_hooks(drain_then_append)

        self.assert_refused(
            CHANGED_WHILE_READING,
            snapshot.read_exact_regular_file,
            self.root,
            "a.jsonl",
            LABEL,
            hooks,
        )


class PinnedChildReadTests(SourceCase):
    def pinned_read(self, drain) -> bytes:
        parent = self.open_directory(self.root)
        before, descriptor = snapshot._open_pinned_child("a.jsonl", parent, LABEL)
        self.addCleanup(os.close, descriptor)
        read = snapshot.PinnedChildRead("a.jsonl", parent, descriptor, before, LABEL)
        return snapshot.read_pinned_child_bytes(read, _descriptor_hooks(drain))

    def test_missing_child_cannot_be_opened(self):
        parent = self.open_directory(self.root)

        with self.assertRaises(ComposeError) as caught:
            snapshot._open_pinned_child("absent.jsonl", parent, LABEL)

        self.assertRegex(
            str(caught.exception), "^" + re.escape(f"{LABEL}: cannot open exact source file: ")
        )

    def test_child_growing_during_the_read_is_refused(self):
        def drain_then_append(descriptor: int) -> bytes:
            payload = snapshot._drain_descriptor(descriptor)
            with self.member.open("ab") as handle:
                handle.write(b"{}\n")
            return payload

        with self.assertRaises(ComposeError) as caught:
            self.pinned_read(drain_then_append)

        self.assertEqual(str(caught.exception), CHANGED_WHILE_READING)

    def test_child_name_naming_another_file_is_refused(self):
        other = self.make_directory("other")
        (other / "a.jsonl").write_bytes(b"{}\n")
        descriptor = self.open_file(self.member)
        other_parent = self.open_directory(other)
        before = self.member.stat()

        with self.assertRaises(ComposeError) as caught:
            _read_pinned("a.jsonl", other_parent, descriptor, before, LABEL)

        self.assertEqual(str(caught.exception), CHANGED_WHILE_READING)

    def test_stable_child_bytes_are_returned(self):
        self.assertEqual(self.pinned_read(snapshot._drain_descriptor), b"{}\n")


class ExactChildFileTests(SourceCase):
    def test_exact_child_bytes_are_returned(self):
        path, payload = snapshot.read_exact_child_file(self.root, "a.jsonl", LABEL, _read_pinned)

        self.assertEqual((path, payload), (self.member, b"{}\n"))

    def test_parent_that_cannot_be_pinned_is_refused(self):
        failing = mock.Mock(side_effect=OSError("parent vanished"))

        # Seam: os.open is the parent pin; failing it models a parent swapped after validation.
        with (
            mock.patch.object(snapshot.os, "open", failing),
            self.assertRaises(ComposeError) as caught,
        ):
            snapshot.read_exact_child_file(self.root, "a.jsonl", LABEL, _read_pinned)

        self.assertEqual(
            str(caught.exception), f"{LABEL} parent changed while it was pinned: {self.root}"
        )

    def test_missing_child_is_refused_and_the_parent_released(self):
        with self.assertRaises(ComposeError) as caught:
            snapshot.read_exact_child_file(self.root, "absent.jsonl", LABEL, _read_pinned)

        self.assertRegex(
            str(caught.exception), "^" + re.escape(f"{LABEL}: cannot open exact source file: ")
        )


class SourceEnumerationTests(SourceCase):
    def test_missing_source_directory_cannot_be_enumerated(self):
        missing = self.root / "absent"

        with self.assertRaises(ComposeError) as caught:
            snapshot._scan_source_directory(missing)

        self.assertRegex(
            str(caught.exception), "^" + re.escape(f"cannot enumerate source directory {missing}: ")
        )

    def test_vanished_source_entry_cannot_be_inspected(self):
        with os.scandir(self.root) as scan:
            entries = list(scan)
        self.member.unlink()

        with self.assertRaises(ComposeError) as caught:
            snapshot._source_entry_metadata(entries[0], self.member)

        self.assertRegex(
            str(caught.exception), "^" + re.escape(f"cannot inspect source member {self.member}: ")
        )


if __name__ == "__main__":
    unittest.main()
