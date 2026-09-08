#!/usr/bin/env python3
"""The one-time vendoring script, offline: file admission, tree filtering, and a build from
the fixture's upstream files served through the fetch seam (real subprocess evidence)."""

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import vendor_python_repair_catalog as vendor  # noqa: E402
from code_repair_test_support import FIXTURE_CATALOG, catalog, executor, oc  # noqa: E402

COMMIT = "2067ce6dfb3b0426a88c7a40531e355a5c703cff"
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


def _fixture_fetch(url: str, _cache: Path) -> bytes:
    """Serve the fixture's upstream files as the pinned repository."""

    sources = {r["path"]: r["text"] for _n, r in oc.read_jsonl(FIXTURE_CATALOG / "upstream.jsonl")}
    if url.startswith("https://api.github.com/"):
        tree = [{"path": p, "type": "blob", "size": len(t)} for p, t in sources.items()]
        return json.dumps({"tree": tree, "truncated": False}).encode("utf-8")
    path = url.split(f"{COMMIT}/", 1)[1]
    if path == "LICENSE.md":
        return (FIXTURE_CATALOG / catalog.LICENSE_FILENAME).read_bytes()
    return sources[path].encode("utf-8")


class OfflineBuild(unittest.TestCase):
    def test_the_script_builds_a_catalog_that_passes_catalog_check(self):
        root = Path(tempfile.mkdtemp(prefix="code-repair-vendor-"))
        self.addCleanup(shutil.rmtree, root, True)
        argv = [
            "--commit", COMMIT, "--out", str(root / "catalog"), "--cache-dir", str(root / "cache"),
            "--references", str(FIXTURE_CATALOG / "references.json"), "--catalog-id", "vendor-test",
        ]
        with mock.patch.object(vendor, "_fetch", _fixture_fetch), mock.patch("builtins.print"):
            self.assertEqual(vendor.main(argv), 0)
        built = catalog.load_catalog(root / "catalog")
        fixture = catalog.load_catalog(FIXTURE_CATALOG)
        self.assertEqual(built.catalog_id, "vendor-test")
        self.assertLessEqual(
            {p.program_id for p in fixture.programs}, {p.program_id for p in built.programs}
        )
        self.assertEqual(catalog.catalog_check(built, executor.Executor(timeout_s=5.0)), [])
        self.assertEqual(built.meta["build"]["notes"], [])


if __name__ == "__main__":
    unittest.main()
