#!/usr/bin/env python3
"""Loading a catalog: the digest over its pinned packs, drifted pins, and header corruptions.

Each test pins the committed ``counter-workspace`` pack in a private
catalog under a temporary directory; the committed pins are never read or
edited.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import tool_world_test_support as support
from tool_world_pack_support import (
    COMMITTED_TASKS,
    FACTORY,
    PACK,
    refusal,
    rewrite_json,
    sandbox,
    set_key,
)

# The support modules go first: they put pipelines/ on sys.path for the imports below.
# isort: split
from tool_world import catalog as catalog_mod
from tool_world import pack as pack_mod
from tool_world import vocabulary as cv
from tool_world._contract import sha256_canonical

CATALOG_CORRUPTIONS = (
    ("bad format", set_key("format", "catalog/0"), "format must be"),
    ("wrong family", set_key("family", "mill"), "family must be"),
    ("catalog_id blank", set_key("catalog_id", ""), "catalog_id must be"),
    ("packs empty", set_key("packs", []), "packs must be a nonempty list"),
    ("pack row malformed", set_key("packs", [{"pack_id": PACK}]), "packs[0]: must carry"),
)


class LoadCatalog(unittest.TestCase):
    def setUp(self):
        self.root = sandbox(self)
        self.catalog_dir = support.private_catalog(self.root / "catalog", (PACK,))
        self.header = self.catalog_dir / catalog_mod.CATALOG_FILENAME

    def test_a_private_catalog_loads_and_digests_its_pinned_packs(self):
        loaded = catalog_mod.load_catalog(self.catalog_dir)
        self.assertEqual(
            (loaded.catalog_id, loaded.directory), ("tool-world-test", self.catalog_dir)
        )
        self.assertEqual([pack.pack_id for pack in loaded.packs], [PACK])
        self.assertEqual(loaded.catalog_sha256, catalog_mod.catalog_digest(loaded.packs))
        self.assertEqual(
            loaded.catalog_sha256,
            sha256_canonical([[PACK, loaded.packs[0].pack_sha256]]),
        )
        self.assertIs(loaded.pack(PACK), loaded.packs[0])
        pairs = list(loaded.tasks())
        self.assertGreaterEqual({task.task_id for _pack, task in pairs}, set(COMMITTED_TASKS))
        self.assertEqual(list(loaded.tasks(FACTORY)), pairs)
        self.assertEqual(list(loaded.tasks("tool-world-mcp-factory")), [])
        with refusal(self, cv.FINDING_PACK_FILE_MISSING, "'nope' is not in catalog"):
            loaded.pack("nope")

    def test_the_digest_ignores_catalog_prose_and_follows_pack_bytes(self):
        before = catalog_mod.load_catalog(self.catalog_dir).catalog_sha256
        rewrite_json(self.header, set_key("notes", "prose only"))
        self.assertEqual(catalog_mod.load_catalog(self.catalog_dir).catalog_sha256, before)
        (self.catalog_dir / PACK / "files" / "extra.txt").write_text("y", encoding="utf-8")
        repinned = pack_mod.load_pack(self.catalog_dir / PACK).pack_sha256
        rewrite_json(self.header, set_key("packs", [{"pack_id": PACK, "pack_sha256": repinned}]))
        self.assertNotEqual(catalog_mod.load_catalog(self.catalog_dir).catalog_sha256, before)

    def test_missing_catalog_file(self):
        with refusal(self, cv.FINDING_CATALOG_FILE_MISSING, "missing CATALOG.json"):
            catalog_mod.load_catalog(self.root / "empty")

    def test_header_corruptions(self):
        for label, mutate, needle in CATALOG_CORRUPTIONS:
            with self.subTest(label=label):
                support.private_catalog(self.catalog_dir, (PACK,))
                rewrite_json(self.header, mutate)
                with refusal(self, cv.FINDING_CATALOG_FIELD_INVALID, needle):
                    catalog_mod.load_catalog(self.catalog_dir)

    def test_a_header_that_is_not_a_strict_json_object_is_refused(self):
        self.header.write_text("{not json", encoding="utf-8")
        with refusal(self, cv.FINDING_CATALOG_FIELD_INVALID, "not strict JSON"):
            catalog_mod.load_catalog(self.catalog_dir)
        self.header.write_text("[]", encoding="utf-8")
        with refusal(self, cv.FINDING_CATALOG_FIELD_INVALID, "must be an object"):
            catalog_mod.load_catalog(self.catalog_dir)

    def test_a_drifted_pin_is_refused(self):
        readme = self.catalog_dir / PACK / "files" / "README.md"
        readme.write_text(readme.read_text(encoding="utf-8") + "drift\n", encoding="utf-8")
        with refusal(self, cv.FINDING_PACK_SHA_MISMATCH, "is not the pinned"):
            catalog_mod.load_catalog(self.catalog_dir)

    def test_duplicate_pack_ids_are_refused(self):
        rewrite_json(self.header, lambda p: p["packs"].append(dict(p["packs"][0])))
        with refusal(self, cv.FINDING_CATALOG_FIELD_INVALID, "duplicate pack ids"):
            catalog_mod.load_catalog(self.catalog_dir)

    def test_the_default_catalog_is_the_committed_directory(self):
        self.assertEqual(catalog_mod.DEFAULT_CATALOG, support.REPO / "catalogs" / "tool-world-v1")


if __name__ == "__main__":
    unittest.main()
