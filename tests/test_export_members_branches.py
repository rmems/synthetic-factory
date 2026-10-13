"""Fail-closed branches of exact export member reads and tree enumeration."""

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

import export_members
import export_members_read as members_read
from compose_destination_branch_support import TempTreeCase
from export_contract import ExportError

LABEL = "curated payload a.jsonl"


class ExportReadCase(TempTreeCase):
    def setUp(self) -> None:
        super().setUp()
        self.member = self.root / "a.jsonl"
        self.member.write_bytes(b"{}\n")

    def assert_refused(self, message: str, call, *args) -> None:
        with self.assertRaises(ExportError) as caught:
            call(*args)

        self.assertEqual(str(caught.exception), message)


class PinnedDescriptorTests(ExportReadCase):
    def test_symlink_member_cannot_be_opened(self):
        link = self.root / "link.jsonl"
        link.symlink_to(self.member)

        with self.assertRaises(ExportError) as caught:
            members_read.read_pinned_descriptor(link, link.lstat(), "link.jsonl", LABEL)

        self.assertRegex(
            str(caught.exception),
            "^" + re.escape(f"{LABEL}: cannot open exact regular file 'link.jsonl': "),
        )

    def test_hard_linked_member_is_not_unique(self):
        os.link(self.member, self.root / "b.jsonl")

        self.assert_refused(
            f"{LABEL}: opened identity is not a unique regular file",
            members_read.read_pinned_descriptor,
            self.member,
            self.member.lstat(),
            "a.jsonl",
            LABEL,
        )

    def test_member_swapped_before_opening_is_refused(self):
        other = self.root / "b.jsonl"
        other.write_bytes(b"[]\n")

        self.assert_refused(
            f"{LABEL}: path identity changed while opening",
            members_read.read_pinned_descriptor,
            self.member,
            other.lstat(),
            "a.jsonl",
            LABEL,
        )

    def test_member_growing_during_the_read_is_refused(self):
        original = members_read._read_descriptor_bytes

        def read_then_append(descriptor: int) -> bytes:
            payload = original(descriptor)
            with self.member.open("ab") as handle:
                handle.write(b"{}\n")
            return payload

        # Seam: _read_descriptor_bytes is the read the identity must survive.
        with (
            mock.patch.object(members_read, "_read_descriptor_bytes", read_then_append),
            self.assertRaises(ExportError) as caught,
        ):
            members_read.read_pinned_descriptor(self.member, self.member.lstat(), "a.jsonl", LABEL)

        self.assertEqual(str(caught.exception), f"{LABEL}: source identity changed while reading")


class ExactRegularReadTests(ExportReadCase):
    def read_with_race(self, relative: str, race) -> None:
        original = members_read.read_pinned_descriptor

        def read_then_race(path, before, raw_path, label):
            result = original(path, before, raw_path, label)
            race()
            return result

        # Seam: read_pinned_descriptor returns right before the path is re-authenticated.
        with mock.patch.object(members_read, "read_pinned_descriptor", read_then_race):
            members_read.read_exact_regular_file(self.root, relative, LABEL)

    def test_exact_member_bytes_are_returned(self):
        self.assertEqual(
            members_read.read_exact_regular_file(self.root, "a.jsonl", LABEL),
            (self.member, b"{}\n"),
        )

    def test_member_replaced_after_reading_is_refused(self):
        def replace_member() -> None:
            replacement = self.root / "replacement"
            replacement.write_bytes(b"{}\n")
            os.replace(replacement, self.member)

        with self.assertRaises(ExportError) as caught:
            self.read_with_race("a.jsonl", replace_member)

        self.assertEqual(str(caught.exception), f"{LABEL}: path identity changed while reading")

    def test_parent_swapped_for_a_symlink_after_reading_is_refused(self):
        (self.make_directory("sub") / "a.jsonl").write_bytes(b"{}\n")

        def alias_parent() -> None:
            (self.root / "sub").rename(self.root / "real")
            (self.root / "sub").symlink_to(self.root / "real", target_is_directory=True)

        with self.assertRaises(ExportError) as caught:
            self.read_with_race("sub/a.jsonl", alias_parent)

        self.assertEqual(
            str(caught.exception), f"{LABEL}: path became a symlink alias while reading"
        )

    def test_unresolvable_member_after_reading_is_refused(self):
        self.assert_refused(
            f"{LABEL}: cannot resolve file after reading",
            members_read._resolved_after_read,
            self.root,
            self.root / "absent.jsonl",
            "absent.jsonl",
            LABEL,
        )

    def test_member_that_cannot_be_inspected_is_refused(self):
        with self.assertRaises(ExportError) as caught:
            members_read._member_lstat(self.root / "absent.jsonl", "absent.jsonl", LABEL)

        self.assertRegex(
            str(caught.exception),
            "^" + re.escape(f"{LABEL}: cannot inspect declared file 'absent.jsonl': "),
        )


class AliasFreeEnumerationTests(TempTreeCase):
    def enumeration_error(self, root: Path) -> str:
        with self.assertRaises(ExportError) as caught:
            export_members.iter_alias_free_jsonl(root, "curated records")

        return str(caught.exception)

    def test_missing_root_cannot_be_enumerated(self):
        missing = self.root / "absent"

        self.assertRegex(
            self.enumeration_error(missing),
            "^" + re.escape(f"curated records: cannot enumerate {missing}: "),
        )

    def test_symlink_entry_is_an_alias(self):
        link = self.root / "link"
        link.symlink_to(self.root)

        self.assertEqual(
            self.enumeration_error(self.root),
            f"curated records: tree contains a symlink alias: {link}",
        )

    def test_directory_named_like_jsonl_is_refused(self):
        trap = self.make_directory("trap.jsonl")

        self.assertEqual(
            self.enumeration_error(self.root),
            f"curated records: JSONL entry is not an exact regular file: {trap}",
        )

    def test_vanished_entry_cannot_be_inspected(self):
        (self.root / "gone.jsonl").write_bytes(b"")
        with os.scandir(self.root) as scan:
            entries = list(scan)
        (self.root / "gone.jsonl").unlink()

        with self.assertRaises(ExportError) as caught:
            export_members._entry_metadata(entries[0], "curated records")

        self.assertRegex(str(caught.exception), r"^curated records: cannot inspect ")

    def test_members_are_sorted_and_other_files_ignored(self):
        nested = self.make_directory("factory")
        (nested / "b.jsonl").write_bytes(b"")
        (self.root / "a.jsonl").write_bytes(b"")
        (self.root / "notes.txt").write_bytes(b"")

        self.assertEqual(
            export_members.iter_alias_free_jsonl(self.root, "curated records"),
            [self.root / "a.jsonl", nested / "b.jsonl"],
        )


if __name__ == "__main__":
    unittest.main()
