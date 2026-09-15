#!/usr/bin/env python3
"""Third-slice leftover catalogs for ``brw-mill-r383`` and ``brw-mill-r395``.

Pairs are compact JSONL under ``config/brw/``. Mills are read only as
``git show`` + ``ast.literal_eval`` and are never executed or vendored.
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

from brw._contract import BANNED_HOSTS, BrwError  # noqa: E402
from brw import catalog  # noqa: E402

SOURCE_REF = "813f93f"
LEGACY_REF = "origin/legacy-mill-lane"
R383_PATH = "experiments/brw-mill-r383.py"
R395_PATH = "experiments/brw-mill-r395.py"
R383_FIRST = "glasswortcot-math-style"
R383_LAST = "alariacot-flex-grow"
R395_FIRST = "cystoseiracot-flex-shrink"
R395_LAST = "pleurocapscot-text-wrap-style"
VENDOR_BITS = ("mill", "loop")


def _legacy_pairs(path: str):
    src = subprocess.check_output(
        ["git", "show", f"{LEGACY_REF}:{path}"],
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
    raise AssertionError(f"PAIRS assignment missing from {path}")


class BrwThirdSliceLayout(unittest.TestCase):
    def test_no_vendored_mill_or_loop(self):
        owned = [
            *(REPO / "config" / "brw").iterdir(),
            *(REPO / "pipelines" / "brw").iterdir(),
            REPO / "tests" / "test_brw.py",
            REPO / "tests" / "test_brw_r212.py",
            REPO / "tests" / "test_brw_r383.py",
        ]
        for path in owned:
            name = path.name.lower()
            self.assertFalse(any(bit in name for bit in VENDOR_BITS), path.name)
        for rel in (R383_PATH, R395_PATH, "experiments/brw-loop-r395-extra6.py"):
            self.assertFalse((REPO / rel).exists(), rel)

    def test_package_line_cap_still_holds(self):
        total = (REPO / "tests" / "test_brw.py").read_text().count("\n")
        for path in (REPO / "pipelines" / "brw").glob("*.py"):
            total += path.read_text().count("\n")
        self.assertLessEqual(total, 2500)


class BrwThirdSliceHeader(unittest.TestCase):
    def test_header_pins_r383_and_r395(self):
        header = catalog.LEFTOVER_HEADER
        self.assertEqual(header["source_commit"], SOURCE_REF)
        self.assertEqual(header["n_pair_rows_committed"], 1916)
        mills = {mill["mill_id"]: mill for mill in header["mills"]}
        r383 = mills["brw-mill-r383"]
        self.assertEqual(r383["source_path"], R383_PATH)
        self.assertEqual(r383["source_blob_sha1"], "2f3cfa87192835a76d4e187aed2befc3d44f5832")
        self.assertEqual(
            r383["source_sha256"],
            "369ec79c054843a653ec11f13d3e03be0541db8d8ba3b745dcdf8fa614f8552e",
        )
        self.assertEqual(r383["catalog_first"], 383)
        self.assertEqual(r383["catalog_last"], 394)
        r395 = mills["brw-mill-r395"]
        self.assertEqual(r395["source_path"], R395_PATH)
        self.assertEqual(r395["source_blob_sha1"], "b5c9ebf082265723ad0b810d0c2d2738fd01abee")
        self.assertEqual(
            r395["source_sha256"],
            "05c05690ecaf076b8cefa4d5b0a190cc0ac80cc386643f72626d67cdbeeeb3f4",
        )
        self.assertEqual(r395["catalog_first"], 395)
        self.assertEqual(r395["catalog_last"], 454)
        self.assertNotIn("brw-mill-r383", header["deferred"])
        self.assertNotIn("brw-mill-r395", header["deferred"])


class BrwR383Catalog(unittest.TestCase):
    def test_twelve_unique_pairs(self):
        self.assertEqual(len(catalog.R383_PAIRS), 12)
        slugs = catalog.r383_slugs()
        self.assertEqual(slugs[0], R383_FIRST)
        self.assertEqual(slugs[-1], R383_LAST)
        self.assertEqual(len(set(slugs)), 12)
        places = {pair["ok_place"] for pair in catalog.R383_PAIRS} | {
            pair["bad_place"] for pair in catalog.R383_PAIRS
        }
        self.assertTrue(places.isdisjoint(BANNED_HOSTS))

    def test_lookup_and_refusals(self):
        self.assertEqual(catalog.r383_pair_for_round(383)["ok_place"], "glasswortcot")
        self.assertEqual(catalog.r383_pair_for_round(394)["widget"], "flex-grow")
        with self.assertRaises(BrwError):
            catalog.r383_pair_for_round(382)
        with self.assertRaises(BrwError):
            catalog.r383_pair_for_round(395)


class BrwR395Catalog(unittest.TestCase):
    def test_sixty_unique_pairs(self):
        self.assertEqual(len(catalog.R395_PAIRS), 60)
        slugs = catalog.r395_slugs()
        self.assertEqual(slugs[0], R395_FIRST)
        self.assertEqual(slugs[-1], R395_LAST)
        self.assertEqual(len(set(slugs)), 60)

    def test_lookup_and_refusals(self):
        self.assertEqual(catalog.r395_pair_for_round(395)["ok_place"], "cystoseiracot")
        self.assertEqual(catalog.r395_pair_for_round(454)["widget"], "text-wrap-style")
        with self.assertRaises(BrwError):
            catalog.r395_pair_for_round(394)
        with self.assertRaises(BrwError):
            catalog.r395_pair_for_round(455)

    def test_r395_extra_slice_starts_at_455(self):
        self.assertEqual(len(catalog.R395_EXTRA_PAIRS), catalog.R395_EXTRA_PAIR_COUNT)
        first = catalog.R395_EXTRA_PAIRS[0]
        self.assertEqual(first["ok_place"], "usneacot")
        self.assertEqual(first["widget"], "padding-inline")


class BrwThirdSliceAstExtract(unittest.TestCase):
    def test_jsonl_matches_legacy_literals_without_exec(self):
        try:
            extracted383 = _legacy_pairs(R383_PATH)
            extracted395 = _legacy_pairs(R395_PATH)
        except (subprocess.CalledProcessError, FileNotFoundError):
            self.skipTest("origin/legacy-mill-lane is not fetched")
        self.assertEqual(len(extracted383), 12)
        self.assertEqual(len(extracted395), 60)
        for extracted_row, committed in zip(extracted383, catalog.R383_PAIRS, strict=True):
            self.assertEqual(extracted_row, dict(committed))
        for extracted_row, committed in zip(extracted395, catalog.R395_PAIRS, strict=True):
            self.assertEqual(extracted_row, dict(committed))
        raw = (REPO / "config" / "brw" / "pairs.jsonl").read_bytes()
        self.assertEqual(
            hashlib.sha256(raw).hexdigest(),
            catalog.LEFTOVER_HEADER["pairs_sha256"],
        )


if __name__ == "__main__":
    unittest.main()
