"""Pin how compose source snapshots refuse unsafe or aliased member paths.

A snapshot member must be a plain in-tree POSIX relative path that names
exactly one regular file: no separators other than ``/``, no traversal, no NUL,
no symlink or hard-link alias. Trees are built in temporary directories.
"""

from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path

TESTS = Path(__file__).resolve().parent
for entry in (TESTS, TESTS.parent / "pipelines"):
    if str(entry) not in sys.path:
        sys.path.insert(0, str(entry))

import compose_source_snapshot_members as members
from compose_contract import ComposeError
from refusal_case_support import RefusalCaseAssertions

_TEXT = "member: path must be a nonempty POSIX string"


def _unsafe(raw: str) -> str:
    return f"member: unsafe relative path {raw!r}"


def _validated_member(raw):
    return members.validated_member_relative(raw, "member")


_PATH_REFUSALS = (
    ("not text", 5, _TEXT),
    ("empty", "", _TEXT),
    ("backslash separator", "a\\b.jsonl", _TEXT),
    ("NUL byte", "a\0b.jsonl", _unsafe("a\0b.jsonl")),
    ("doubled separator", "a//b.jsonl", _unsafe("a//b.jsonl")),
    ("leading dot segment", "./a.jsonl", _unsafe("./a.jsonl")),
    ("absolute", "/a.jsonl", _unsafe("/a.jsonl")),
    ("parent segment", "..", _unsafe("..")),
    ("trailing parent segment", "a/..", _unsafe("a/..")),
)


class MemberPathText(RefusalCaseAssertions, unittest.TestCase):
    def test_unsafe_member_paths_are_refused(self):
        self.assert_each_refuses(ComposeError, _validated_member, _PATH_REFUSALS)

    def test_plain_relative_path_is_accepted(self):
        relative = members.validated_member_relative("factory/batch-r01.jsonl", "member")
        self.assertEqual(relative.parts, ("factory", "batch-r01.jsonl"))


class SourceMemberResolution(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name) / "source"
        (self.root / "factory").mkdir(parents=True)
        self.batch = self.root / "factory" / "batch-r01.jsonl"
        self.batch.write_text("{}\n")
        self.outside = Path(temp.name) / "outside.jsonl"
        self.outside.write_text("{}\n")

    def _refusal(self, raw: str) -> str:
        with self.assertRaises(ComposeError) as caught:
            members.source_member_path(self.root, raw, "member")
        return str(caught.exception)

    def test_regular_member_resolves_inside_the_root(self):
        resolved = members.source_member_path(self.root, "factory/batch-r01.jsonl", "member")
        self.assertEqual(resolved, self.root.resolve() / "factory" / "batch-r01.jsonl")

    def test_missing_member_is_refused(self):
        self.assertEqual(
            self._refusal("factory/batch-r02.jsonl"),
            "member: source member is missing: factory/batch-r02.jsonl",
        )

    def test_symlink_aliases_are_refused(self):
        (self.root / "factory" / "inside-link.jsonl").symlink_to(self.batch)
        (self.root / "factory" / "outside-link.jsonl").symlink_to(self.outside)
        for name in ("inside-link.jsonl", "outside-link.jsonl"):
            with self.subTest(name):
                self.assertEqual(
                    self._refusal(f"factory/{name}"),
                    f"member: source member is a symlink alias: factory/{name}",
                )

    def test_directory_member_is_refused(self):
        self.assertEqual(
            self._refusal("factory"), "member: source member is not a regular file: factory"
        )

    def test_hard_link_alias_is_refused(self):
        os.link(self.batch, self.root / "factory" / "hard-link.jsonl")
        self.assertEqual(
            self._refusal("factory/hard-link.jsonl"),
            "member: hard-link aliases are not accepted: factory/hard-link.jsonl",
        )


if __name__ == "__main__":
    unittest.main()
