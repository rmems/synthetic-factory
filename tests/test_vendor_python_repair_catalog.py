#!/usr/bin/env python3
"""The one-time vendoring script, offline: file admission, tree filtering, and a build from
fixture modules served as fake upstream files (real subprocess evidence)."""

import contextlib
import hashlib
import io
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from scripts import vendor_python_repair_catalog as vendor
from tests.code_repair_test_support import FIXTURE_CATALOG, catalog, executor, oc
from code_repair import catalog_check  # noqa: E402


def blob_sha(data):
    framed = b"blob " + str(len(data)).encode() + b"\0" + data
    # nosemgrep: python.lang.security.insecure-hash-algorithms.insecure-hash-algorithm-sha1 -- mirrors Git blob object identity in the fixture.
    return hashlib.sha1(framed, usedforsecurity=False).hexdigest()


COMMIT = "2067ce6dfb3b0426a88c7a40531e355a5c703cff"
TREE_SHA = "a" * 40  # the fixture commit's tree, as the commit endpoint reports it
DOCTESTED = "def f(x):\n    '''\n    >>> f(1)\n    1\n    >>> f(2)\n    2\n    '''\n    return x\n"


class FileAdmission(unittest.TestCase):
    def test_stdlib_only_modules_are_admitted(self):
        self.assertTrue(vendor._file_admissible("import math\n\n\n" + DOCTESTED))
        self.assertTrue(vendor._file_admissible("from __future__ import annotations\n" + DOCTESTED))

    def test_io_randomness_third_party_and_unparseable_files_are_not(self):
        for text in ("import os\n", "from random import randint\n", "import numpy as np\n",
                     "def f(:\n", DOCTESTED + "x = '''```'''\n"):
            with self.subTest(text=text.split("\n")[0]):
                self.assertFalse(vendor._file_admissible(text))

    def test_candidate_paths_keep_small_top_level_family_files_only(self):
        tree = [
            {"path": "maths/abs.py", "type": "blob", "size": 100},
            {"path": "maths/__init__.py", "type": "blob", "size": 0},
            {"path": "maths/series/p.py", "type": "blob", "size": 100},
            {"path": "graphs/a.py", "type": "blob", "size": 100},
            {"path": "sorts/big.py", "type": "blob", "size": vendor.MAX_FILE_BYTES},
            {"path": "sorts/ok.py", "type": "blob", "size": vendor.MAX_FILE_BYTES - 1},
            {"path": "sorts/README.md", "type": "blob", "size": 10},
        ]
        self.assertEqual(vendor._candidate_paths(tree), ["maths/abs.py", "sorts/ok.py"])

    def test_all_import_scopes_use_the_explicit_allowlist(self):
        for text in ("import ctypes\n", "def f():\n    import os\n",
                     "if True:\n    from random import randint\n",
                     "class X:\n    import numpy\n", "from .math import sqrt\n"):
            with self.subTest(text=text):
                self.assertFalse(vendor._file_admissible(text))
        self.assertTrue(vendor._file_admissible("def f():\n    import math\n"))

    def test_pinned_catalog_imports_remain_admissible(self):
        path = Path(__file__).resolve().parents[1] / "catalogs/python-repair-v1/programs.jsonl"
        for _n, row in oc.read_jsonl(path):
            with self.subTest(program=row["program_id"]):
                self.assertTrue(vendor._file_admissible(row["module"]["text"]))

    def test_commit_must_be_exactly_forty_hex_characters(self):
        argv = ["--out", "out", "--cache-dir", "cache", "--references", "refs"]
        for value in ("main", "a" * 39, "a" * 41, "z" * 40, "a" * 40 + "\n"):
            with (self.subTest(value=value), contextlib.redirect_stderr(io.StringIO()),
                  self.assertRaises(SystemExit)):
                vendor._parse_args(argv + ["--commit", value])
        self.assertEqual(vendor._parse_args(argv + ["--commit", COMMIT]).commit, COMMIT)


def _fixture_source(program):
    text = program.text
    if program.reference.kind == "sibling_same_file":
        text += program.reference.source
    return text


def _fixture_fetch(url: str, _cache: Path) -> bytes:
    """Serve the fixture modules as fake upstream files, without executable CLI guards."""

    sources = {p.upstream["path"]: _fixture_source(p)
               for p in catalog.load_catalog(FIXTURE_CATALOG).programs}
    sources["LICENSE.md"] = (FIXTURE_CATALOG / catalog.LICENSE_FILENAME).read_text()
    if "/commits/" in url:
        return json.dumps({"commit": {"tree": {"sha": TREE_SHA}}}).encode()
    if url.startswith("https://api.github.com/"):
        if url != vendor.API.format(repository=vendor.REPOSITORY, commit=TREE_SHA):
            raise ValueError(f"the tree must be fetched by its own sha, not {url}")
        tree = [{"path": p, "type": "blob", "size": len(t.encode()),
                 "sha": blob_sha(t.encode())} for p, t in sources.items()]
        return json.dumps({"tree": tree, "sha": TREE_SHA, "truncated": False}).encode()
    path = url.split(f"{COMMIT}/", 1)[1]
    return sources[path].encode("utf-8")


class OfflineBuild(unittest.TestCase):
    def test_coordinated_cached_metadata_cannot_replace_trusted_tree(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            url = vendor.API.format(repository=vendor.REPOSITORY, commit=TREE_SHA)
            tree = json.loads(_fixture_fetch(url, root))
            forged = {**tree, 'tree': []}
            for address, data in ((url, json.dumps(forged).encode()),
                    (vendor.COMMIT_API.format(repository=vendor.REPOSITORY, commit=COMMIT),
                     _fixture_fetch(vendor.COMMIT_API.format(repository=vendor.REPOSITORY, commit=COMMIT), root))):
                (root / hashlib.sha256(address.encode()).hexdigest()).write_bytes(data)
            with mock.patch.object(vendor, '_https_get', side_effect=lambda u: _fixture_fetch(u, root)):
                with self.assertRaisesRegex(SystemExit, 'cache|sha|digest'):
                    vendor._tree(COMMIT, root)

    def test_the_script_builds_a_catalog_that_passes_catalog_check(self):
        root = Path(tempfile.mkdtemp(prefix="code-repair-vendor-"))
        self.addCleanup(shutil.rmtree, root, True)
        argv = [
            "--commit", COMMIT, "--out", str(root / "catalog"), "--cache-dir", str(root / "cache"),
            "--references", str(FIXTURE_CATALOG / "references.json"), "--catalog-id", "vendor-test",
        ]
        with mock.patch.object(vendor, "_fetch", _fixture_fetch), mock.patch.object(
                vendor, '_https_get', side_effect=lambda u: _fixture_fetch(u, root)), mock.patch("builtins.print"):
            self.assertEqual(vendor.main(argv), 0)
        built = catalog.load_catalog(root / "catalog")
        fixture = catalog.load_catalog(FIXTURE_CATALOG)
        self.assertEqual(built.catalog_id, "vendor-test")
        self.assertLessEqual(
            {p.program_id for p in fixture.programs}, {p.program_id for p in built.programs}
        )
        self.assertEqual(catalog_check.catalog_check(built, executor.Executor(timeout_s=5.0)), [])
        self.assertEqual(built.meta["build"]["notes"], [])

    def test_corrupt_cached_tree_or_raw_file_refuses_before_build(self):
        with tempfile.TemporaryDirectory(prefix="code-repair-cache-") as tmp:
            root = Path(tmp)
            for kind in ("tree", "source", "license"):
                self._corrupt_cache_case(root / kind, kind)

    def _corrupt_cache_case(self, root, kind):
        root.mkdir()
        tree_url = vendor.API.format(repository=vendor.REPOSITORY, commit=TREE_SHA)
        tree = json.loads(_fixture_fetch(tree_url, root))
        urls = [tree_url, f"https://api.github.com/repos/{vendor.REPOSITORY}/commits/{COMMIT}"]
        urls += [vendor.RAW.format(repository=vendor.REPOSITORY, commit=COMMIT, path=e["path"])
                 for e in tree["tree"]]
        tampered = {
            "tree": (tree_url, lambda data: json.dumps({**tree, "sha": "b" * 40}).encode()),
            "source": (urls[2], lambda data: data + b"# tampered\n"),
            "license": (
                next(u for u in urls if u.endswith("/LICENSE.md")),
                lambda data: data + b"tampered\n",
            ),
        }
        target, corrupt = tampered[kind]
        for url in urls:
            data = _fixture_fetch(url, root)
            (root / hashlib.sha256(url.encode()).hexdigest()).write_bytes(
                corrupt(data) if url == target else data
            )
        argv = ["--commit", COMMIT, "--out", str(root / "catalog"),
                "--cache-dir", str(root), "--references", str(FIXTURE_CATALOG / "references.json")]
        with mock.patch.object(vendor, "_https_get", side_effect=lambda u: _fixture_fetch(u, root)):
            with self.subTest(kind=kind), self.assertRaisesRegex(SystemExit, "sha|digest|cached"):
                vendor.main(argv)
        self.assertFalse((root / "catalog").exists())


if __name__ == "__main__":
    unittest.main()
