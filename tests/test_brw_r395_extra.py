#!/usr/bin/env python3
"""Fourth-slice leftover catalogs for ``brw-mill-r395-extra*``.

Pairs are compact JSONL under ``config/brw/``. Mills are read only as
``git show`` + ``ast.literal_eval`` on ``ROWS`` / ``KEYS`` and are never
executed or vendored.
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

from brw import catalog  # noqa: E402

LEGACY_REF = "origin/legacy-mill-lane"
SOURCE_REF = "813f93f"
EXTRA_FIRST = "usneacot-padding-inline"
EXTRA_LAST = "aglaophytonclough-scrollbar-color-flip"
VENDOR_BITS = ("mill", "loop")

EXTRA_PATHS = tuple(
    f"experiments/brw-mill-r395-extra{'' if i == 1 else i}.py" for i in range(1, 18)
)


def _legacy_extra_pairs(path: str) -> list[dict]:
    src = subprocess.check_output(
        ["git", "show", f"{LEGACY_REF}:{path}"],
        text=True,
        cwd=REPO,
        stderr=subprocess.DEVNULL,
    )
    tree = ast.parse(src)
    rows: list[tuple] | None = None
    keys: tuple[str, ...] | None = None
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        for target in node.targets:
            if not isinstance(target, ast.Name):
                continue
            if target.id == "ROWS":
                rows = ast.literal_eval(node.value)
            elif target.id == "KEYS":
                keys = ast.literal_eval(node.value)
    if rows is None or keys is None:
        raise AssertionError(f"ROWS/KEYS missing from {path}")
    out: list[dict] = []
    for row in rows:
        spec = dict(zip(keys, row, strict=True))
        spec["not"] = row[-3]
        out.append(spec)
    return out


class BrwR395ExtraLayout(unittest.TestCase):
    def test_no_vendored_mill_or_loop(self):
        owned = [
            *(REPO / "config" / "brw").iterdir(),
            *(REPO / "pipelines" / "brw").iterdir(),
            REPO / "tests" / "test_brw.py",
            REPO / "tests" / "test_brw_r212.py",
            REPO / "tests" / "test_brw_r383.py",
            REPO / "tests" / "test_brw_r395_extra.py",
        ]
        for path in owned:
            name = path.name.lower()
            self.assertFalse(any(bit in name for bit in VENDOR_BITS), path.name)
        for rel in (*EXTRA_PATHS, "experiments/brw-loop-r395-extra6.py"):
            self.assertFalse((REPO / rel).exists(), rel)

    def test_package_line_cap_still_holds(self):
        total = (REPO / "tests" / "test_brw.py").read_text().count("\n")
        for path in (REPO / "pipelines" / "brw").glob("*.py"):
            total += path.read_text().count("\n")
        self.assertLessEqual(total, 2500)


class BrwR395ExtraHeader(unittest.TestCase):
    def test_header_pins_all_seventeen_extra_mills(self):
        header = catalog.LEFTOVER_HEADER
        self.assertEqual(header["source_commit"], SOURCE_REF)
        self.assertEqual(header["n_pair_rows_committed"], 1916)
        mills = header["mills"]
        self.assertEqual(len(mills), 20)
        extra_mills = mills[3:]
        self.assertEqual([mill["mill_id"] for mill in extra_mills], [Path(p).stem for p in EXTRA_PATHS])
        self.assertEqual(extra_mills[0]["catalog_first"], 455)
        self.assertEqual(extra_mills[-1]["catalog_last"], 2127)
        self.assertEqual(
            header["deferred"],
            ["brw-loop-r395-extra6 (filename-historical; loads brw-mill-r395 later)"],
        )


class BrwR395ExtraCatalog(unittest.TestCase):
    def test_sixteen_hundred_seventy_three_unique_extra_pairs(self):
        self.assertEqual(catalog.R395_EXTRA_PAIR_COUNT, 1673)
        self.assertEqual(len(catalog.R395_EXTRA_PAIRS), 1673)
        slugs = tuple(
            f"{pair['ok_place']}-{pair['widget']}" for pair in catalog.R395_EXTRA_PAIRS
        )
        self.assertEqual(slugs[0], EXTRA_FIRST)
        self.assertEqual(slugs[-1], EXTRA_LAST)
        self.assertEqual(len(set(slugs)), 1673)


class BrwR395ExtraAstExtract(unittest.TestCase):
    def test_jsonl_matches_legacy_rows_without_exec(self):
        try:
            extracted: list[dict] = []
            for path in EXTRA_PATHS:
                extracted.extend(_legacy_extra_pairs(path))
        except (subprocess.CalledProcessError, FileNotFoundError):
            self.skipTest("origin/legacy-mill-lane is not fetched")
        self.assertEqual(len(extracted), 1673)
        for extracted_row, committed in zip(extracted, catalog.R395_EXTRA_PAIRS, strict=True):
            self.assertEqual(extracted_row, dict(committed))
        raw = (REPO / "config" / "brw" / "pairs.jsonl").read_bytes()
        self.assertEqual(
            hashlib.sha256(raw).hexdigest(),
            catalog.LEFTOVER_HEADER["pairs_sha256"],
        )
        lines = raw.decode("utf-8").splitlines()
        self.assertEqual(len(lines), 1916)
        for line in lines[243:]:
            self.assertFalse(line.startswith((" ", "\t")))
            row = json.loads(line)
            self.assertIsInstance(row, dict)


if __name__ == "__main__":
    unittest.main()
