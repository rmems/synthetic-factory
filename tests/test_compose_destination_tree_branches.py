"""Fail-closed branches of exact destination-tree capture."""

from __future__ import annotations

import hashlib
import os
import sys
import unittest
from pathlib import Path
from unittest import mock

TESTS = Path(__file__).resolve().parent
for _path in (TESTS, TESTS.parent / "pipelines"):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

import compose_destination_tree as tree
from compose_contract import ComposeError
from compose_destination_branch_support import TempTreeCase


def _allow(_descriptor: int, _label: str) -> None:
    """A raw-relocation guard that accepts every descriptor."""


class TreeCaptureCase(TempTreeCase):
    def capture(self, guard=_allow):
        descriptor = self.open_directory(self.root)
        return tree.DestinationTreeSnapshot(guard).capture(descriptor)

    def assert_capture_refused(self, message: str, guard=_allow) -> None:
        descriptor = self.open_directory(self.root)
        snapshot = tree.DestinationTreeSnapshot(guard)

        with self.assertRaises(ComposeError) as caught:
            snapshot.capture(descriptor)

        self.assertEqual(str(caught.exception), message)


class TreeCaptureTests(TreeCaptureCase):
    def test_exact_tree_reports_directories_and_digests(self):
        self.make_directory("records", "nested")
        (self.root / "records" / "nested" / "a.jsonl").write_bytes(b"{}\n")

        directories, digests = self.capture()

        self.assertEqual(directories, frozenset({"records", "records/nested"}))
        self.assertEqual(digests, {"records/nested/a.jsonl": hashlib.sha256(b"{}\n").hexdigest()})

    def test_hard_linked_file_is_unsafe(self):
        (self.root / "a.jsonl").write_bytes(b"{}\n")
        os.link(self.root / "a.jsonl", self.root / "b.jsonl")

        self.assert_capture_refused("destination tree contains unsafe file: a.jsonl")

    def test_symlink_entry_is_unsafe(self):
        (self.root / "link").symlink_to("elsewhere")

        self.assert_capture_refused("destination tree contains unsafe entry: link")

    def test_file_guard_os_error_is_reported_as_unreadable(self):
        (self.root / "a.jsonl").write_bytes(b"{}\n")

        def refuse_files(_descriptor: int, label: str) -> None:
            if label.startswith("destination tree file"):
                raise OSError("descriptor vanished")

        self.assert_capture_refused(
            "destination tree file cannot be read: a.jsonl", guard=refuse_files
        )

    def test_file_rewritten_under_the_guard_has_changed(self):
        member = self.root / "a.jsonl"
        member.write_bytes(b"{}\n")

        def rewrite(_descriptor: int, _label: str) -> None:
            member.write_bytes(b'{"changed": true}\n')

        self.assert_capture_refused("destination tree file changed: a.jsonl", guard=rewrite)

    def test_directory_swapped_after_scan_has_changed(self):
        self.make_directory("sub")

        def swap(_descriptor: int, label: str) -> None:
            if label == "destination tree directory sub":
                (self.root / "sub").rename(self.root / "sub-old")
                (self.root / "sub").mkdir()

        self.assert_capture_refused("destination tree directory changed: sub", guard=swap)

    def test_directory_swapped_before_open_has_changed(self):
        self.make_directory("sub")
        descriptor = self.open_directory(self.root)
        snapshot = tree.DestinationTreeSnapshot(_allow)
        original_open = tree.DestinationTreeSnapshot._open

        def swap_then_open(path, *, directory):
            (self.root / "sub").rename(self.root / "sub-old")
            (self.root / "sub").mkdir()
            return original_open(path, directory=directory)

        # Seam: _open is the only step between the entry stat and the pinned open.
        with (
            mock.patch.object(tree.DestinationTreeSnapshot, "_open", staticmethod(swap_then_open)),
            self.assertRaises(ComposeError) as caught,
        ):
            snapshot.capture(descriptor)

        self.assertEqual(str(caught.exception), "destination tree directory changed: sub")


class TreeStaticHelperTests(TempTreeCase):
    def test_missing_directory_cannot_be_opened(self):
        parent = self.open_directory(self.root)
        path = tree.TreePath(parent, "absent", ("records", "absent"))

        with self.assertRaises(ComposeError) as caught:
            tree.DestinationTreeSnapshot._open(path, directory=True)

        self.assertEqual(
            str(caught.exception), "destination tree directory cannot be opened: records/absent"
        )

    def test_missing_file_cannot_be_opened(self):
        parent = self.open_directory(self.root)
        path = tree.TreePath(parent, "absent", ("absent",))

        with self.assertRaises(ComposeError) as caught:
            tree.DestinationTreeSnapshot._open(path, directory=False)

        self.assertEqual(str(caught.exception), "destination tree file cannot be opened: absent")

    def test_missing_entry_cannot_be_inspected(self):
        parent = self.open_directory(self.root)
        path = tree.TreePath(parent, "absent", ("absent",))

        with self.assertRaises(ComposeError) as caught:
            tree.DestinationTreeSnapshot._metadata(path)

        self.assertEqual(
            str(caught.exception), "destination tree entry cannot be inspected: absent"
        )

    def test_tree_entry_relative_path_joins_its_parts(self):
        parent = self.open_directory(self.root)
        path = tree.TreePath(parent, "a.jsonl", ("records", "a.jsonl"))
        entry = tree.TreeEntry(path, os.stat(self.root))

        self.assertEqual(entry.relative, "records/a.jsonl")


if __name__ == "__main__":
    unittest.main()
