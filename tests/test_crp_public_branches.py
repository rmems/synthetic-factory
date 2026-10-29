"""CRP fail-closed branches reached through the public surface only.

``plants_from_source`` / ``catalog_check`` on small in-memory inputs, and a
wave's ``load_catalog`` (``crp.r432``) on mutated temp copies of ``config/crp``.
"""

from __future__ import annotations

import dataclasses
import importlib
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
support = importlib.import_module("mill_public_branch_support")
catalog = importlib.import_module("crp.catalog")
r432 = importlib.import_module("crp.r432")
CrpRefusal = importlib.import_module("crp._contract").CrpRefusal

COMMITTED = support.REPO / "config" / "crp"
NOT_A_PLANT = "CATALOG_AST_NOT_A_PLANT"
INVALID = "CATALOG_FIELD_INVALID"
NO_NOUN_LOOP = "_RAW expand loop has no indexed {{prefix}}{{base + i}} noun"
DUPLICATE_KEY = "is not strict JSON: duplicate JSON object key 'a'"
FAMILY = "family"


def raw_loop(noun: str) -> str:
    """A literal ``_RAW`` block whose expand loop passes ``noun`` as the third ``_p`` argument."""

    return (
        "_RAW = [('fam',)]\n"
        "for i, row in enumerate(_RAW):\n"
        f"    PLANTS.append(_p(a, b, {noun}))\n"
        "    log(i)\n"
    )


def source_refusal(text: str) -> tuple[str, str] | None:
    return support.refusal(CrpRefusal, catalog.plants_from_source, text)


def repeats(slug: str, family: str) -> tuple[str, str]:
    return "CATALOG_DUPLICATE_SLUG", f"slug {slug!r} repeats ({family} and {family})"


def family_repeats(family: str) -> tuple[str, str]:
    return "CATALOG_DUPLICATE_FAMILY", f"family {family!r} repeats"


class CrpSourceShapes(unittest.TestCase):
    def test_raw_loops_without_an_indexed_noun_are_refused(self):
        for noun in ("'keel'", "f'{x}{800 + i}'", "f'lake{800 + i}'"):
            with self.subTest(noun=noun):
                self.assertEqual(source_refusal(raw_loop(noun)), (NOT_A_PLANT, NO_NOUN_LOOP))

    def test_malformed_calls_and_empty_sources_are_coded_refusals(self):
        sixteen = ", ".join(["'x'"] * 16)
        empty = ("CATALOG_EMPTY", "mill source has no literal P() rows or _RAW expand block")
        for label, text, expected in (
            ("extra positional", f"P({sixteen})\n",
             (NOT_A_PLANT, "P() has extra positional arguments")),
            ("no rows", "x = 1\n", empty),
        ):
            with self.subTest(label):
                self.assertEqual(source_refusal(text), expected)

    def test_prefix_only_refusals_carry_python_detail(self):
        for label, text, prefix in (
            ("keyword name", "P(family=fam)\n", "P() argument is not a literal: "),
            ("syntax", "P(\n", "mill source is not parseable: "),
        ):
            with self.subTest(label):
                code, message = source_refusal(text)
                self.assertEqual(code, NOT_A_PLANT)
                self.assertTrue(message.startswith(prefix), message)


class CrpCatalogIdentity(unittest.TestCase):
    def test_plant_lookup_by_slug(self):
        loaded = catalog.load_catalog()
        first = loaded.plants[0]
        missing = support.refusal(CrpRefusal, loaded.plant, "nope")
        found = (loaded.plant(first.slug), missing)
        self.assertEqual(found, (first, (INVALID, "no plant 'nope' in the catalog")))

    def test_catalog_check_refuses_a_repeated_slug_or_family(self):
        first, second, third = catalog.load_catalog().plants[:3]
        twin = dataclasses.replace(second, family=first.family)
        for label, plants, expected in (
            ("slug", (first, first, third), repeats(first.slug, first.family)),
            ("repeated family", (first, twin, third), family_repeats(first.family)),
        ):
            with self.subTest(label):
                found = support.refusal(CrpRefusal, catalog.catalog_check, plants)
                self.assertEqual(found, expected)


class CrpWaveCatalogCopies(unittest.TestCase):
    def copy(self) -> support.CatalogCopy:
        names = (support.CATALOG_JSON, support.PLANTS_JSONL)
        return support.CatalogCopy(self, COMMITTED, names)

    def load_rows(self, payload: bytes) -> tuple[str, str] | None:
        """``r432.load_catalog`` over a copy whose plants file is ``payload``, re-pinned."""

        copy = self.copy()
        meta = copy.read_json()
        meta["plants_sha256"] = copy.write_bytes(payload)
        copy.write_json(meta)
        return support.refusal(CrpRefusal, r432.load_catalog, copy.directory)

    def test_a_pinned_copy_outside_config_loads_without_source_pins(self):
        copy = self.copy()
        copy.write_json({**copy.read_json(), "source_commit": "0" * 40})
        loaded = r432.load_catalog(copy.directory)
        self.assertEqual((loaded.catalog_id, len(loaded.plants)), ("crp-r432-v1", 366))

    def test_catalog_json_must_be_strict(self):
        copy = self.copy()
        copy.path(support.CATALOG_JSON).write_text('{"a": 1, "a": 2}', encoding="utf-8")
        found = support.refusal(CrpRefusal, r432.load_catalog, copy.directory)
        self.assertEqual(found, (INVALID, f"CATALOG.json {DUPLICATE_KEY}"))

    def test_plants_bytes_must_be_strict_utf8_json(self):
        not_utf8 = (
            "plants.jsonl is not utf-8: "
            "'utf-8' codec can't decode byte 0xff in position 0: invalid start byte"
        )
        for label, payload, message in (
            ("not utf-8", b"\xff\n", not_utf8),
            ("duplicate key", b'{"a":1,"a":2}\n', f"plants.jsonl:1 {DUPLICATE_KEY}"),
        ):
            with self.subTest(label):
                self.assertEqual(self.load_rows(payload), (INVALID, message))

    def test_a_repeated_slug_or_family_is_refused(self):
        lines = (COMMITTED / support.PLANTS_JSONL).read_bytes().splitlines(keepends=True)
        first, second = json.loads(lines[0]), json.loads(lines[1])
        twin = support.compact_jsonl([second | {FAMILY: first[FAMILY]}])
        for label, line, expected in (
            ("slug", lines[0], repeats(first["slug"], first[FAMILY])),
            ("repeated family", twin, family_repeats(first[FAMILY])),
        ):
            with self.subTest(label):
                payload = b"".join([lines[0], line, *lines[2:]])
                self.assertEqual(self.load_rows(payload), expected)


if __name__ == "__main__":
    unittest.main()
