"""In-process git index and gitignore evidence must match Git or fail closed.

Every repository here is synthesized inside a temporary directory; nothing
reads or mutates this checkout's own ``.git``.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tests.test_mill_script_inventory_refusals import _ewah_bitmap, _git_index, _index_entry

import mill_script_inventory_git as git

OID = b"\x02" * 20
EMPTY_BITMAP = _ewah_bitmap(0, ())


def _raw_entry(path: bytes, path_len: int) -> bytes:
    """An index entry whose name length field is set verbatim (no NUL, no padding)."""

    return bytes(60) + path_len.to_bytes(2, "big") + path


def _link(deleted: bytes = EMPTY_BITMAP, replaced: bytes = EMPTY_BITMAP) -> bytes:
    return OID + deleted + replaced


class TempRepoCaseMixin:
    def setUp(self):
        self._temp = tempfile.TemporaryDirectory()
        self.addCleanup(self._temp.cleanup)
        self.root = Path(self._temp.name)

    def write(self, relative: str, text: str) -> Path:
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    def write_index(self, payload: bytes, shared: bytes | None = None) -> None:
        gitdir = self.root / ".git"
        gitdir.mkdir(exist_ok=True)
        (gitdir / "index").write_bytes(payload)
        if shared is not None:
            (gitdir / f"sharedindex.{OID.hex()}").write_bytes(shared)

    def ignored(self, *paths: str) -> dict[str, tuple[str, str, str]]:
        return git.gitignore_matches(self.root, paths)


class WildcardTranslation(TempRepoCaseMixin, unittest.TestCase):
    CASES = (
        ("[a-c].py", "b.py", "d.py"),
        ("[!x]y.txt", "ay.txt", "xy.txt"),
        ("[\\]]z", "]z", "az"),
        ("[abc", "[abc", "a"),
        ("?.log", "a.log", "ab.log"),
    )

    def test_glob_classes_and_wildcards_match_like_git(self):
        for rule, hit, miss in self.CASES:
            with self.subTest(rule=rule):
                self.write(".gitignore", rule + "\n")
                matches = self.ignored(hit, miss)
                self.assertEqual(matches.get(hit), (".gitignore", "1", rule))
                self.assertNotIn(miss, matches)


class CoreIgnoreCase(TempRepoCaseMixin, unittest.TestCase):
    IGNORECASE = "[core]\n\tignorecase = true ; comment\n"

    def test_ignorecase_folds_nested_scope_rules(self):
        self.write(".git/config", self.IGNORECASE)
        self.write("Sub/.gitignore", "*.PY\n")
        self.assertEqual(self.ignored("Sub/a.py")["Sub/a.py"], ("Sub/.gitignore", "1", "*.PY"))

    def test_commondir_config_is_honoured_for_relative_and_absolute_pointers(self):
        config = self.write("common/config", self.IGNORECASE)
        self.write(".gitignore", "README\n")
        for pointer in ("../common", str(config.parent)):
            with self.subTest(pointer=pointer):
                self.write(".git/commondir", pointer + "\n")
                self.assertIn("readme", self.ignored("readme"))

    def test_missing_config_or_gitdir_keeps_matching_case_sensitive(self):
        self.write(".gitignore", "README\n")
        self.assertEqual(self.ignored("readme"), {})
        (self.root / ".git").mkdir()
        self.assertEqual(self.ignored("readme"), {})


class IndexParsingRefusals(TempRepoCaseMixin, unittest.TestCase):
    def test_malformed_indexes_fail_closed(self):
        cases = (
            ("bad-magic", b"XXXX" + bytes(28), "not parseable"),
            ("missing-entry", b"DIRC" + (2).to_bytes(4, "big") + (1).to_bytes(4, "big"),
             "truncated"),
            ("trailing-link-bytes", _git_index((), {b"link": _link() + b"\0"}), "not parseable"),
        )
        for name, payload, message in cases:
            with self.subTest(case=name):
                self.write_index(payload)
                with self.assertRaisesRegex(git.MillScriptInventoryError, message):
                    git.tracked_paths(self.root)

    def test_long_name_entry_is_read_to_its_terminator(self):
        name = b"d/" + b"x" * 0x1000
        entry = _raw_entry(name + b"\0", 0xFFF)
        self.write_index(_git_index((entry + bytes((8 - len(entry) % 8) % 8),)))
        self.assertEqual(git.tracked_paths(self.root), (name.decode(),))


class SplitIndexMerging(TempRepoCaseMixin, unittest.TestCase):
    SHARED = _git_index((_index_entry(""), _index_entry("README"), _index_entry("x")))

    def tracked_with(self, link: bytes, split: tuple[bytes, ...] = (), shared=SHARED):
        self.write_index(_git_index(split, {b"link": link}), shared)
        return git.tracked_paths(self.root)

    def test_unreplaced_empty_shared_names_are_dropped(self):
        self.assertEqual(self.tracked_with(_link()), ("README", "x"))

    def test_run_length_deletions_remove_every_covered_shared_entry(self):
        deleted = _ewah_bitmap(3, (3,))
        self.assertEqual(self.tracked_with(_link(deleted), (_index_entry("new"),)), ("new",))

    def test_inconsistent_split_indexes_fail_closed(self):
        cases = (
            ("literal-past-end", _link(_ewah_bitmap(1, (1 << 33,))), self.SHARED, "truncated"),
            ("replacement-past-end", _link(replaced=_ewah_bitmap(2, (1 << 33, 0b10))),
             self.SHARED, "truncated"),
            ("nested-link", _link(), _git_index((), {b"link": _link()}), "unsupported"),
        )
        for name, link, shared, message in cases:
            with self.subTest(case=name), self.assertRaisesRegex(
                git.MillScriptInventoryError, message
            ):
                self.tracked_with(link, shared=shared)


class GitOutputEmulation(TempRepoCaseMixin, unittest.TestCase):
    CHECK_IGNORE = ("check-ignore", "--no-index", "-z", "-v", "--stdin")

    def test_ls_files_lists_index_paths_nul_terminated(self):
        self.write_index(_git_index((_index_entry("README"), _index_entry("a/b.py"))))
        self.assertEqual(git._git_output(self.root, ("ls-files", "-z")), b"README\0a/b.py\0")

    def test_check_ignore_reports_source_line_rule_and_path(self):
        self.write(".gitignore", "# logs\n*.log\n")
        output = git._git_output(self.root, self.CHECK_IGNORE, b"a.log\0keep.txt\0")
        self.assertEqual(output, b".gitignore\x002\x00*.log\x00a.log\x00")

    def test_check_ignore_without_hits_is_empty(self):
        for payload in (None, b"", b"keep.txt\0"):
            with self.subTest(payload=payload):
                self.assertEqual(git._git_output(self.root, self.CHECK_IGNORE, payload), b"")


if __name__ == "__main__":
    unittest.main()
