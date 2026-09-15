#!/usr/bin/env python3
"""Pay lane: Archive B catalog (mill_plants) and slice A disjointness."""

from __future__ import annotations

import ast
import json
import subprocess
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PIPELINES = REPO / "pipelines"
PACKAGE = PIPELINES / "pay"
SOURCE_PATH = "scripts/payment_idempotency_mill/mill_plants.py"
DEFERRED_B = "scripts/payment_idempotency_mill/mill_plants_b.py"
DEFERRED_G = "scripts/payment_idempotency_mill/mill_plants_g.py"
SESSION_COMMIT = "e5206e72fa829931162944648e1e180949baaf0b"
BYTES_REF = "origin/legacy-mill-lane"
COMMITTED_ARCHIVE_B_PAIRS = 21
DEFERRED_SOURCE_COUNT = 11

sys.path.insert(0, str(PIPELINES))

from pay import archive_b_catalog as cat  # noqa: E402
from pay import archive_b_deferred as deferred  # noqa: E402
from pay import archive_b_extract as extract  # noqa: E402
from pay import pairs as slice_a  # noqa: E402
from pay._contract import (  # noqa: E402
    CATALOG_ID,
    FACTORY,
    FINDING_CATALOG_SHA256_MISMATCH,
    FINDING_SLICE_A_OVERLAP,
    GENERATOR,
    PayRefusal,
    is_vendor_filename,
    refuse_vendor_paths,
)
from mill_reviewed_vocabulary import REVIEWED_MILL_PREFIX_HOMES  # noqa: E402

TINY_SOURCE = '''
PAIRS = []

def _ok(**kwargs):
    return kwargs

def _fail(**kwargs):
    return kwargs

PAIRS.append(
    (
        _ok(slug="tiny-ok"),
        _fail(slug="tiny-fail"),
    )
)
'''


def _git_show(spec: str) -> str | None:
    try:
        proc = subprocess.run(
            ["git", "show", spec],
            cwd=REPO,
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError:
        return None
    if proc.returncode != 0:
        return None
    return proc.stdout


def _archive_b_source_text() -> str | None:
    for spec in (
        f"{SESSION_COMMIT}:{SOURCE_PATH}",
        f"{BYTES_REF}:{SOURCE_PATH}",
    ):
        text = _git_show(spec)
        if text is not None:
            return text
    return None


class ArchiveBCatalogTests(unittest.TestCase):
    def test_committed_catalog_loads_archive_b_pairs(self):
        loaded = cat.load_archive_b_catalog(PACKAGE)
        self.assertEqual(loaded.catalog_id, CATALOG_ID)
        self.assertEqual(loaded.meta["factory"], FACTORY)
        self.assertEqual(loaded.meta["generator"], GENERATOR)
        self.assertEqual(len(loaded.pairs), COMMITTED_ARCHIVE_B_PAIRS)
        self.assertEqual(loaded.pairs[0].ok_slug, "worldpay-ntf-vs-inquiry")
        self.assertEqual(loaded.pairs[0].fail_slug, "nuvei-dmn-vs-getstatus")
        self.assertEqual(loaded.pairs[1].ok_slug, "rapyd-completed-vs-retrieve")
        self.assertEqual(loaded.pairs[1].fail_slug, "gocardless-mandate-vs-payment")
        self.assertEqual(loaded.pairs[2].ok_slug, "plaid-transfer-vs-webhook")
        self.assertEqual(loaded.pairs[-1].ok_slug, "forter-preauth-vs-capture")
        extract_meta = loaded.meta["extract"]
        self.assertEqual(extract_meta["committed_pairs"], COMMITTED_ARCHIVE_B_PAIRS)
        self.assertEqual(len(deferred.deferred_sources()), DEFERRED_SOURCE_COUNT)

    def test_archive_b_slugs_do_not_overlap_slice_a(self):
        loaded = cat.load_archive_b_catalog(PACKAGE)
        slice_slugs = {row["slug"] for row in slice_a.PAIRS}
        slice_slugs.update(row["fail"] for row in slice_a.PAIRS)
        self.assertFalse(loaded.slugs() & slice_slugs)

    def test_pairs_sha256_pin_mismatch_refuses(self):
        pairs_path = PACKAGE / "archive_b.jsonl"
        original = pairs_path.read_bytes()
        self.addCleanup(pairs_path.write_bytes, original)
        pairs_path.write_bytes(original + b"\n")
        with self.assertRaises(PayRefusal) as caught:
            cat.load_archive_b_catalog(PACKAGE)
        self.assertEqual(caught.exception.code, FINDING_CATALOG_SHA256_MISMATCH)


class AstExtractTests(unittest.TestCase):
    def test_pairs_from_source_reads_append_tuple(self):
        rows = extract.pairs_from_source(TINY_SOURCE, source="tiny.py")
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["ok"]["slug"], "tiny-ok")
        self.assertEqual(rows[0]["fail"]["slug"], "tiny-fail")

    def test_live_git_show_extract_matches_committed_jsonl(self):
        text = _archive_b_source_text()
        if text is None:
            self.skipTest("mill_plants.py not available via git show in this checkout")
        extracted = extract.pairs_from_source(text)
        loaded = cat.load_archive_b_catalog(PACKAGE)
        self.assertEqual(len(extracted), 2)
        for index, pair in enumerate(loaded.pairs[:2]):
            self.assertEqual(extracted[index]["ok"]["slug"], pair.ok_slug)
            self.assertEqual(extracted[index]["fail"]["slug"], pair.fail_slug)

    def test_deferred_git_show_extract_matches_committed_tail(self):
        try:
            b_text = deferred.git_show_deferred_source(DEFERRED_B)
            g_text = deferred.git_show_deferred_source(DEFERRED_G)
        except Exception:
            self.skipTest("deferred mill_plants sources not available via git show")
        b_rows = extract.pairs_from_chained_source(b_text, source=DEFERRED_B, expected_rows=5)
        g_rows = extract.pairs_from_chained_source(g_text, source=DEFERRED_G, expected_rows=1)
        loaded = cat.load_archive_b_catalog(PACKAGE)
        self.assertEqual(b_rows[0]["ok"]["slug"], loaded.pairs[2].ok_slug)
        self.assertEqual(g_rows[0]["ok"]["slug"], loaded.pairs[-1].ok_slug)
        self.assertEqual(len(deferred.deferred_sources()), DEFERRED_SOURCE_COUNT)

    def test_extract_modules_do_not_call_exec(self):
        for name in (
            "archive_b_extract.py",
            "archive_b_catalog.py",
            "archive_b_deferred.py",
            "_contract.py",
        ):
            path = PACKAGE / name
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for node in ast.walk(tree):
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                    self.assertNotIn(node.func.id, {"exec", "eval", "compile"}, msg=f"{name}:{node.lineno}")


class PackageHygiene(unittest.TestCase):
    def test_no_vendored_mill_plants_modules(self):
        names = {path.name for path in PACKAGE.iterdir()}
        self.assertNotIn("mill_plants.py", names)
        self.assertNotIn("mill_plants_b.py", names)
        refuse_vendor_paths(PACKAGE)

    def test_vendor_filename_guard(self):
        self.assertTrue(is_vendor_filename("mill_plants_b.py"))
        self.assertFalse(is_vendor_filename("archive_b.jsonl"))

    def test_reviewed_vocabulary_still_maps_pay(self):
        self.assertEqual(REVIEWED_MILL_PREFIX_HOMES.get("pay"), FACTORY)


if __name__ == "__main__":
    unittest.main()
