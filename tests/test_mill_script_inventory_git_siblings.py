"""Contracts for the git-evidence siblings behind ``mill_script_inventory_git``.

The facade's public names reach every sibling the way the inventory does:
``gitignore_matches`` exercises gitdir (core.ignorecase), gitglob and
gitignore; ``tracked_paths`` exercises gitindex. Each repository is synthesized
in a temporary directory, so nothing reads or mutates this checkout's ``.git``.
"""

from __future__ import annotations

import importlib
import sys
import tempfile
import unittest
from pathlib import Path

from tests.pipeline_import_test_support import (
    PIPELINES,
    direct_pipeline_path,
    isolated_pipeline_modules,
)
from tests.test_mill_script_inventory_refusals import _ewah_bitmap, _git_index, _index_entry

if str(PIPELINES) not in sys.path:
    sys.path.insert(0, str(PIPELINES))
facade = importlib.import_module("mill_script_inventory_git")

# Literal-bound (package-mode, direct-mode) loaders for each sibling.
SIBLING_LOADERS = {
    "mill_script_inventory_gitdir": (
        lambda: importlib.import_module("pipelines.mill_script_inventory_gitdir"),
        lambda: importlib.import_module("mill_script_inventory_gitdir"),
    ),
    "mill_script_inventory_gitglob": (
        lambda: importlib.import_module("pipelines.mill_script_inventory_gitglob"),
        lambda: importlib.import_module("mill_script_inventory_gitglob"),
    ),
    "mill_script_inventory_gitignore": (
        lambda: importlib.import_module("pipelines.mill_script_inventory_gitignore"),
        lambda: importlib.import_module("mill_script_inventory_gitignore"),
    ),
    "mill_script_inventory_gitindex": (
        lambda: importlib.import_module("pipelines.mill_script_inventory_gitindex"),
        lambda: importlib.import_module("mill_script_inventory_gitindex"),
    ),
}
SHARED_OID = bytes(range(20))
IGNORECASE_CONFIG = "[core]\n\tignorecase = yes # folded\n"
REFUSED = facade.MillScriptInventoryError
ONE_LITERAL = 1 << 33  # an EWAH run word followed by one literal word


class SyntheticRepo:
    """One temporary work tree with a ``.git`` directory."""

    def __init__(self, test: unittest.TestCase) -> None:
        handle = tempfile.TemporaryDirectory()
        test.addCleanup(handle.cleanup)
        self.root = Path(handle.name)
        self.gitdir = self.root / ".git"
        self.gitdir.mkdir()

    def put(self, relative: str, text: str) -> Path:
        target = self.root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")
        return target

    def index(self, payload: bytes, shared: bytes | None = None) -> None:
        (self.gitdir / "index").write_bytes(payload)
        if shared is not None:
            (self.gitdir / f"sharedindex.{SHARED_OID.hex()}").write_bytes(shared)


def _split_link(deleted: bytes | None = None, replaced: bytes | None = None) -> bytes:
    empty = _ewah_bitmap(0, ())
    return SHARED_OID + (deleted or empty) + (replaced or empty)


def _named_entry(name: bytes, length_field: int) -> bytes:
    """An index entry whose 12-bit name length is written as given."""

    return bytes(60) + length_field.to_bytes(2, "big") + name


def _padded(entry: bytes) -> bytes:
    return entry + bytes((8 - len(entry) % 8) % 8)


def _header(count: int, version: int = 2) -> bytes:
    return b"DIRC" + version.to_bytes(4, "big") + count.to_bytes(4, "big")


class SiblingImportIdentity(unittest.TestCase):
    def test_each_sibling_is_one_module_under_both_import_names(self):
        for first in ("package", "direct"):
            with (
                self.subTest(first=first),
                isolated_pipeline_modules(tuple(SIBLING_LOADERS)),
                direct_pipeline_path(),
            ):
                for name, loaders in SIBLING_LOADERS.items():
                    order = loaders if first == "package" else tuple(reversed(loaders))
                    loaded = [load() for load in order]
                    self.assertIs(loaded[0], loaded[1], name)


class IgnoreCaseEvidence(unittest.TestCase):
    def test_relative_and_absolute_commondir_configs_fold_case(self):
        for pointer in ("../shared", "absolute"):
            with self.subTest(pointer=pointer):
                repo = SyntheticRepo(self)
                config = repo.put("shared/config", IGNORECASE_CONFIG)
                target = str(config.parent) if pointer == "absolute" else pointer
                repo.put(".git/commondir", f"{target}\n")
                repo.put(".gitignore", "Makefile\n")
                hit = facade.gitignore_matches(repo.root, ("makefile",))
                self.assertEqual(hit, {"makefile": (".gitignore", "1", "Makefile")})

    def test_nested_scope_rules_fold_case_relative_to_their_directory(self):
        repo = SyntheticRepo(self)
        repo.put(".git/config", IGNORECASE_CONFIG)
        repo.put("Docs/.gitignore", "*.TXT\n")
        hits = facade.gitignore_matches(repo.root, ("Docs/a.txt", "Other/a.txt"))
        self.assertEqual(hits, {"Docs/a.txt": ("Docs/.gitignore", "1", "*.TXT")})

    def test_work_tree_without_git_matches_case_sensitively_and_has_no_index(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / ".gitignore").write_text("Makefile\n", encoding="utf-8")
            self.assertEqual(facade.gitignore_matches(root, ("makefile",)), {})
            with self.assertRaisesRegex(REFUSED, "git is required"):
                facade.tracked_paths(root)


class GlobTranslation(unittest.TestCase):
    # (rule, ignored path, path the rule must not ignore), pinned to main.
    CASES = (
        ("x[0-9]", "x7", "xa"),
        ("[^q]y", "ay", "qy"),
        ("[!/]z", "az", "a/z"),
        ("[\\]]w", "]w", "aw"),
        ("[\\-x]v", "-v", "av"),
        ("[a-]u", "-u", "bu"),
        ("[]t", "[]t", "t"),
        ("[k", "[k", "k"),
        ("g?s", "gas", "g/s"),
        ("**/deep", "a/b/deep", "a/deepx"),
        ("logs/**", "logs/a/b", "logsx/a"),
    )

    def test_classes_ranges_escapes_and_wildcards_match_like_main(self):
        for rule, ignored, kept in self.CASES:
            with self.subTest(rule=rule):
                repo = SyntheticRepo(self)
                repo.put(".gitignore", f"# rule\n{rule}\n")
                hits = facade.gitignore_matches(repo.root, (ignored, kept))
                self.assertEqual(hits, {ignored: (".gitignore", "2", rule)})


class IndexEvidence(unittest.TestCase):
    def tracked(self, payload: bytes, shared: bytes | None = None) -> tuple[str, ...]:
        repo = SyntheticRepo(self)
        repo.index(payload, shared)
        return facade.tracked_paths(repo.root)

    def test_entry_layouts_are_read_like_main(self):
        long_name = b"n/" + b"q" * 0x1001
        extended = _index_entry("ext.py", flags=0x4000)
        cases = (
            ("extended-flags", _git_index((extended,), version=3), ("ext.py",)),
            ("long-name", _git_index((_padded(_named_entry(long_name + b"\0", 0xFFF)),)),
             (long_name.decode(),)),
            # The name fills its length field exactly and the trailer starts non-zero.
            ("unterminated-name", _header(1) + _named_entry(b"ab", 2) + b"\x01" * 20, ("ab",)),
        )
        for label, payload, expected in cases:
            with self.subTest(case=label):
                self.assertEqual(self.tracked(payload), expected)

    def test_malformed_indexes_raise_the_coded_refusal(self):
        cases = (
            ("bad-signature", b"CRID" + bytes(28), "not parseable"),
            ("missing-entry", _header(3) + bytes(20), "truncated"),
            ("version-4", _git_index((), version=4), "unsupported"),
        )
        for label, payload, message in cases:
            with self.subTest(case=label), self.assertRaisesRegex(REFUSED, message):
                self.tracked(payload)


class SplitIndexEvidence(unittest.TestCase):
    SHARED = _git_index(tuple(_index_entry(name) for name in ("keep", "", "old", "gone")))

    def tracked(self, link: bytes, split=(), shared: bytes | None = SHARED) -> tuple[str, ...]:
        repo = SyntheticRepo(self)
        repo.index(_git_index(tuple(split), {b"link": link}), shared)
        return facade.tracked_paths(repo.root)

    def test_deletions_replacements_and_additions_merge_like_main(self):
        deleted = _ewah_bitmap(4, (ONE_LITERAL, 0b1000))
        replaced = _ewah_bitmap(4, (ONE_LITERAL, 0b0100))
        merged = self.tracked(
            _split_link(deleted, replaced),
            (_index_entry(""), _index_entry("added")),
        )
        self.assertEqual(merged, ("keep", "old", "added"))

    def test_run_of_deleted_bits_drops_every_shared_entry(self):
        deleted = _ewah_bitmap(4, ((1 << 1) | 1,))
        self.assertEqual(self.tracked(_split_link(deleted), (_index_entry("only"),)), ("only",))

    def test_inconsistent_split_indexes_raise_the_coded_refusal(self):
        nested = _git_index((), {b"link": _split_link()})
        cases = (
            ("missing-shared", _split_link(), None, "not parseable"),
            ("nested-link", _split_link(), nested, "unsupported"),
            ("trailing-link-bytes", _split_link() + b"\0", self.SHARED, "not parseable"),
            ("literal-past-end", _split_link(_ewah_bitmap(2, (ONE_LITERAL,))), self.SHARED,
             "truncated"),
            ("replacement-past-end", _split_link(replaced=_ewah_bitmap(4, (ONE_LITERAL, 0b0100))),
             self.SHARED, "truncated"),
        )
        for label, link, shared, message in cases:
            with self.subTest(case=label), self.assertRaisesRegex(REFUSED, message):
                self.tracked(link, shared=shared)


if __name__ == "__main__":
    unittest.main()
