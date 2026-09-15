#!/usr/bin/env python3
"""Second-slice leftover catalog for ``brw-mill-r212``.

Pairs are compact JSONL under ``config/brw/``. The leftover mill is read only
as ``git show`` + ``ast.literal_eval`` and is never executed or vendored.
"""

from __future__ import annotations

import ast
import hashlib
import json
import subprocess
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "pipelines"))

from brw._contract import BANNED_HOSTS, BrwError, FACTORY  # noqa: E402
from brw import catalog  # noqa: E402

R212_HEADER = REPO / "config" / "brw" / "CATALOG.json"
R212_PAIRS = REPO / "config" / "brw" / "pairs.jsonl"
SOURCE_PATH = "experiments/brw-mill-r212.py"
SOURCE_REF = "origin/legacy-mill-lane"
FIRST_SLUG = "feverfewcot-composition-add"
LAST_SLUG = "goosefootfen-text-size-adjust"
VENDOR_BITS = ("mill", "loop")


def _legacy_pairs():
    src = subprocess.check_output(
        ["git", "show", f"{SOURCE_REF}:{SOURCE_PATH}"],
        text=True,
        cwd=REPO,
        stderr=subprocess.DEVNULL,
    )
    tree = ast.parse(src)
    for node in tree.body:
        if (
            isinstance(node, ast.AnnAssign)
            and isinstance(node.target, ast.Name)
            and node.target.id == "PAIRS"
        ):
            return ast.literal_eval(node.value)
    raise AssertionError("PAIRS assignment missing from leftover mill")


def _legacy_function_names():
    src = subprocess.check_output(
        ["git", "show", f"{SOURCE_REF}:{SOURCE_PATH}"],
        text=True,
        cwd=REPO,
        stderr=subprocess.DEVNULL,
    )
    tree = ast.parse(src)
    return tuple(node.name for node in tree.body if isinstance(node, ast.FunctionDef))


class BrwR212Layout(unittest.TestCase):
    def test_no_vendored_mill_or_loop(self):
        owned = [
            *(REPO / "config" / "brw").iterdir(),
            *(REPO / "pipelines" / "brw").iterdir(),
            REPO / "tests" / "test_brw.py",
            REPO / "tests" / "test_brw_r212.py",
        ]
        for path in owned:
            name = path.name.lower()
            self.assertFalse(any(bit in name for bit in VENDOR_BITS), path.name)
        tracked = subprocess.check_output(
            ["git", "ls-files", "config/brw", "pipelines/brw"],
            cwd=REPO,
            text=True,
        ).splitlines()
        for path in tracked:
            self.assertFalse(any(bit in Path(path).name.lower() for bit in VENDOR_BITS), path)
        self.assertFalse((REPO / "experiments" / "brw-mill-r212.py").exists())

    def test_package_line_cap_still_holds(self):
        total = (REPO / "tests" / "test_brw.py").read_text().count("\n")
        for path in (REPO / "pipelines" / "brw").glob("*.py"):
            total += path.read_text().count("\n")
        self.assertLessEqual(total, 2500)


class BrwR212CompactJsonl(unittest.TestCase):
    def test_pairs_are_one_object_per_line(self):
        raw = R212_PAIRS.read_bytes()
        text = raw.decode("utf-8")
        self.assertTrue(text.endswith("\n"))
        self.assertNotIn("\r", text)
        lines = text.splitlines()
        self.assertEqual(len(lines), 171)
        self.assertEqual(len(lines), catalog.R212_PAIR_COUNT)
        for line in lines:
            self.assertFalse(line.startswith((" ", "\t")))
            row = json.loads(line)
            self.assertIsInstance(row, dict)
        digest = hashlib.sha256(raw).hexdigest()
        header = json.loads(R212_HEADER.read_text(encoding="utf-8"))
        self.assertEqual(header["pairs_sha256"], digest)
        self.assertEqual(digest, catalog.R212_HEADER["pairs_sha256"])


class BrwR212Header(unittest.TestCase):
    def test_header_pins_the_r212_mill_only(self):
        header = catalog.R212_HEADER
        self.assertEqual(header["family"], "brw")
        self.assertEqual(header["factory"], FACTORY)
        self.assertEqual(header["slice"], "full")
        self.assertEqual(header["n_pair_rows_extracted"], 171)
        self.assertEqual(header["n_pair_rows_committed"], 171)
        mill = header["mills"][0]
        self.assertEqual(mill["mill_id"], "brw-mill-r212")
        self.assertEqual(mill["source_path"], SOURCE_PATH)
        self.assertEqual(mill["source_blob_sha1"], "4118ae35200e8bb9557a2c1e723294760be9c81a")
        self.assertEqual(
            mill["source_sha256"],
            "ebcb8ac1e8b32f8c24210e24fc0a189db242198cc1efbaea31b463c3184ed9a8",
        )
        self.assertEqual(mill["catalog_first"], 212)
        self.assertEqual(mill["catalog_last"], 382)
        self.assertIn("brw-mill-r383", header["deferred"])
        self.assertTrue(any("r395-extra6" in item for item in header["deferred"]))


class BrwR212Catalog(unittest.TestCase):
    def test_one_hundred_seventy_one_unique_pairs(self):
        self.assertEqual(len(catalog.R212_PAIRS), 171)
        slugs = catalog.r212_slugs()
        self.assertEqual(slugs[0], FIRST_SLUG)
        self.assertEqual(slugs[-1], LAST_SLUG)
        self.assertEqual(len(set(slugs)), 171)
        self.assertEqual(len({pair["ok_place"] for pair in catalog.R212_PAIRS}), 171)
        self.assertEqual(len({pair["bad_place"] for pair in catalog.R212_PAIRS}), 171)
        self.assertEqual(len({pair["widget"] for pair in catalog.R212_PAIRS}), 171)
        places = {pair["ok_place"] for pair in catalog.R212_PAIRS} | {
            pair["bad_place"] for pair in catalog.R212_PAIRS
        }
        self.assertTrue(places.isdisjoint(BANNED_HOSTS))
        for pair in catalog.R212_PAIRS:
            self.assertNotEqual(pair["prefix"], pair["aux"])
            self.assertNotEqual(pair["prefix"], "api")
            self.assertNotEqual(pair["aux"], "api")

    def test_lookup_and_refusals(self):
        first = catalog.r212_pair_at(0)
        self.assertEqual(first["ok_place"], "feverfewcot")
        self.assertEqual(catalog.r212_pair_for_round(212)["widget"], "composition-add")
        self.assertEqual(catalog.r212_pair_for_round(382)["err_slug"], "tsa-415")
        with self.assertRaises(BrwError):
            catalog.r212_pair_at(-1)
        with self.assertRaises(BrwError):
            catalog.r212_pair_at(True)  # type: ignore[arg-type]
        with self.assertRaises(BrwError):
            catalog.r212_pair_for_round(211)
        with self.assertRaises(BrwError):
            catalog.r212_pair_for_round(383)
        with self.assertRaises(BrwError):
            catalog.pair_for_round(212)

    def test_r193_catalog_is_unchanged(self):
        self.assertEqual(len(catalog.PAIRS), 16)
        self.assertEqual(catalog.slugs()[0], "branleat-offset-anchor")
        self.assertEqual(catalog.pair_for_round(193)["ok_slug"], "branleat-offset-anchor")


class BrwR212AstExtract(unittest.TestCase):
    def test_jsonl_matches_legacy_literals_without_exec(self):
        try:
            extracted = _legacy_pairs()
            names = _legacy_function_names()
        except (subprocess.CalledProcessError, FileNotFoundError):
            self.skipTest("origin/legacy-mill-lane is not fetched")
        self.assertEqual(len(extracted), 171)
        self.assertEqual(
            [pair["ok_place"] for pair in extracted],
            [pair["ok_place"] for pair in catalog.R212_PAIRS],
        )
        for extracted_row, committed in zip(extracted, catalog.R212_PAIRS, strict=True):
            self.assertEqual(extracted_row, dict(committed))
        self.assertIn("success_episode", names)
        self.assertIn("write_stage", names)
        self.assertNotIn("write_stage", catalog.__all__)
        self.assertNotIn("success_episode", catalog.__all__)


if __name__ == "__main__":
    unittest.main()
