"""Branch coverage for ``dbc.catalog_extract``: shapes, refusals, and serializers."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from typing import ClassVar
from unittest import mock

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "pipelines"))

from dbc import catalog_extract as ce
from dbc.sources import MillSource
from dbc.vocabulary import (
    FACTORY,
    GENERATOR,
    PAIR_JSONL_KEYS,
    R647_COMPANION_ID,
    R647_INHERIT_FROM,
    R647_MILL_ID,
    SLICE_MILL_ID,
)

PATH = "scripts/dbc-mill-r100.py"
CTOR_PAIR = "(lang('a'), left('b'))"
LL_TAIL = "PAIRS = list(zip(LANGS, LEFTOVERS))\n"


def extract(source: str, path: str = PATH) -> dict:
    return ce.extract_mill_catalog(source, path=path, blob_sha="blob")


def pair(slug: str) -> dict:
    return {
        "success_slug": slug,
        "fail_slug": f"{slug}-f",
        "success_plant": None,
        "fail_plant": None,
        "fail_handoff": True,
    }


ZIP_LISTCOMP = (
    "_LANGS = [('a', 1)]\n_LEFTS = [{'slug': 'b'}]\n"
    "PAIRS = [(x, y) for x, y in zip(_LANGS, _LEFTS)]\n"
)
ZIP_LOOP = (
    "_CRYPTO = [('c',)]\n_GPIO = [('g',)]\nPAIRS = []\nX = 1\n"
    "for x in Y:\n    pass\nfor x in range(3):\n    pass\nfor x in enumerate():\n    pass\n"
    "for x in enumerate(Y):\n    pass\nfor x in zip(A, B):\n    pass\n"
    "for i, (a, b) in enumerate(zip(_CRYPTO, _GPIO)):\n    PAIRS.append(a)\n"
)
PLANT_BUILD = (
    "def other():\n    pass\n"
    "def build(lang, left):\n    L, R, Q = lang, left, other\n    y = 1\n    y += 1\n"
    "    return [(L('a'), R('b'))]\n"
)


class ShapeExtractTests(unittest.TestCase):
    CASES = (
        ("new-extend", f"NEW_PAIRS = [{CTOR_PAIR}]\nPAIRS = build_pairs()\n",
         ce.SHAPE_NEW_EXTEND, "a"),
        ("zip-listcomp", ZIP_LISTCOMP, ce.SHAPE_ZIP_TABLES, "a"),
        ("zip-fill-loop", ZIP_LOOP, ce.SHAPE_ZIP_TABLES, "c"),
        ("skip-extra-empty", "SKIP = {'s'}\nEXTRA = []\nPAIRS = [p for p in B] + EXTRA\n",
         ce.SHAPE_SKIP_EXTRA, None),
        ("mixed-tuples", "PAIRS = [({'slug': 'a', 'plant': 'p'}, lang('b', 'harbor-x'))]\n",
         ce.SHAPE_CTOR, "a"),
        ("plant-build-aliases", PLANT_BUILD, ce.SHAPE_PLANT_BUILD, "a"),
    )

    def test_shapes(self) -> None:
        for label, source, shape, first in self.CASES:
            with self.subTest(label=label):
                record = extract(source)
                self.assertEqual((record["shape"], record["first_slug"]), (shape, first))

    def test_zip_table_dict_slug_and_mixed_plants(self) -> None:
        self.assertEqual(extract(ZIP_LISTCOMP)["pairs"][0]["fail_slug"], "b")
        row = extract(self.CASES[4][1])["pairs"][0]
        self.assertEqual((row["success_plant"], row["fail_plant"]), ("p", "harbor-x"))

    def test_new_extend_counts(self) -> None:
        record = extract(self.CASES[0][1])
        self.assertEqual((record["n_new"], record["n_inherited"]), (1, 0))


class ConstantsTests(unittest.TestCase):
    BODY = f"PAIRS = [{CTOR_PAIR}]\n"

    def test_non_string_generator_falls_back(self) -> None:
        record = extract("GEN = 1\nOUT = ROOT / 'x'\n" + self.BODY)
        self.assertEqual(record["generator"], GENERATOR)

    def test_suffixed_and_foreign_factory_both_bind_factory(self) -> None:
        for value in (f"'legacy-{FACTORY}'", "3"):
            with self.subTest(value=value):
                record = extract(f"FACTORY = {value}\n" + self.BODY)
                self.assertEqual(record["factory"], FACTORY)

    def test_catalog_first_from_constant_or_name(self) -> None:
        self.assertEqual(extract("CATALOG_FIRST = 9\n" + self.BODY)["catalog_first"], 9)
        self.assertIsNone(extract(self.BODY, path="weird.py")["catalog_first"])


class RefusalTests(unittest.TestCase):
    LL_OK = "LANGS = [{'slug': 'a'}]\nLEFTOVERS = [{'slug': 'b'}]\n"
    CASES = (
        ("no-catalog", "X = 1\n"),
        ("empty-langs", "LANGS = []\nLEFTOVERS = [{'slug': 'b'}]\n" + LL_TAIL),
        ("bad-leftovers", "LANGS = [{'slug': 'a'}]\nLEFTOVERS = 1\n" + LL_TAIL),
        ("list-two-args", LL_OK + "PAIRS = list(a, b)\n"),
        ("list-map", LL_OK + "PAIRS = list(map(f, x))\n"),
        ("non-dict-lang", "LANGS = [1]\nLEFTOVERS = [{'slug': 'b'}]\n" + LL_TAIL),
        ("slugless-lang", "LANGS = [{'lang': 'x'}]\nLEFTOVERS = [{'slug': 'b'}]\n" + LL_TAIL),
        ("empty-table", "_LANGS = []\n"),
        ("slugless-tables", "_LANGS = [1]\n_LEFTS = [2]\nPAIRS = [x for x in zip(_LANGS, _LEFTS)]\n"),
        ("two-generators", "PAIRS = [x for a in A for b in B]\n"),
        ("empty-pairs-no-fill-loop", "PAIRS = []\nfor x in zip(A, B):\n    pass\n"),
        ("listcomp-not-zip", "PAIRS = [x for x in A]\n"),
        ("listcomp-zip-call-arg", "PAIRS = [x for x in zip(_LANGS, f(y))]\n"),
        ("non-string-skip", "SKIP = {1}\n"),
        ("non-tuple-extra", "SKIP = {'a'}\nEXTRA = [1]\n"),
        ("unarmed-extra", "SKIP = {'a'}\nEXTRA = [(1, 2)]\n"),
        ("bad-new-pairs", "NEW_PAIRS = [1]\n"),
        ("new-pairs-unbuilt", f"NEW_PAIRS = [{CTOR_PAIR}]\n"),
        ("unresolved-dict-tuple", "PAIRS = [({'slug': X}, {'slug': 'b'})]\n"),
        ("unresolved-mixed-arm", "PAIRS = [({'slug': X}, lang('b'))]\n"),
        ("two-returns", "def build():\n    return []\n    return []\n"),
        ("non-tuple-build", "def build():\n    return [1]\n"),
        ("slugless-build", "def build():\n    return [(lang(), left('b'))]\n"),
    )

    def test_unextractable_sources_refuse_with_path(self) -> None:
        message = f"^{PATH} has no extractable DBC catalog assignment$"
        for label, source in self.CASES:
            with self.subTest(label=label), self.assertRaisesRegex(ValueError, message):
                extract(source)


class ComposeAndCompanionTests(unittest.TestCase):
    def test_r647_inherits_companion_tail_without_r248(self) -> None:
        companion = [pair(f"c{i}") for i in range(R647_INHERIT_FROM + 2)]
        records = {R647_COMPANION_ID: {"pairs": companion}, R647_MILL_ID: {"pairs": [pair("n")]}}
        current = ce.compose_family_records(records)[R647_MILL_ID]
        self.assertEqual(current["shape"], ce.SHAPE_NEW_EXTEND)
        self.assertEqual((current["n_rows"], current["n_new"], current["n_inherited"]), (3, 1, 2))
        self.assertEqual((current["first_slug"], current["last_slug"]), (companion[-2]["success_slug"], "n"))

    def test_companion_path_falls_back_to_loops(self) -> None:
        source = "LOOPS = [ROOT / 'scripts' / 'dbc-mill-r1.py']\n"
        self.assertEqual(ce.extract_companion_path(source), "scripts/dbc-mill-r1.py")
        self.assertIsNone(ce.extract_companion_path("X = 1\n"))


class SummaryAndSerializerTests(unittest.TestCase):
    BASE: ClassVar[dict] = {
        "mill_id": "m", "path": "p", "blob_sha": "b", "sha256": "s", "kind": "pairs",
        "catalog_first": 1, "n_rows": 1, "first_slug": "a", "last_slug": "a",
        "generator": GENERATOR, "factory": FACTORY, "pairs": [pair("a")],
    }

    def summary(self, include_pairs: bool, **extra) -> dict:
        return ce.mill_summary({**self.BASE, **extra}, include_pairs=include_pairs)

    def test_skip_extra_summary_carries_skip_fields(self) -> None:
        out = self.summary(True, shape=ce.SHAPE_SKIP_EXTRA, n_skip=1, n_extra=1, skip_slugs=("z",))
        self.assertEqual((out["skip_slugs"], out["pairs"]), (["z"], [pair("a")]))

    def test_new_extend_summary_without_pairs(self) -> None:
        out = self.summary(False, shape=ce.SHAPE_NEW_EXTEND, n_new=1, n_inherited=0)
        self.assertEqual((out["n_new"], out["n_inherited"]), (1, 0))
        self.assertNotIn("pairs", out)

    def test_catalog_document_round_trips_through_write(self) -> None:
        mill = self.summary(False, shape=ce.SHAPE_CTOR)
        document = ce.catalog_document([mill, {**mill, "mill_id": "m2"}])
        self.assertEqual((document["n_mills"], document["n_pair_rows"]), (2, 2))
        with tempfile.TemporaryDirectory() as tmp:
            written = ce.write_catalog_document(document, Path(tmp) / "CATALOG.json")
            self.assertEqual(json.loads(written.read_text(encoding="utf-8")), document)


class DeferredPairTests(unittest.TestCase):
    def test_deferred_rows_skip_slice_mill(self) -> None:
        sources = [MillSource(SLICE_MILL_ID, "a.py", "", "pairs"), MillSource("m", "m.py", "", "pairs")]
        composed = {SLICE_MILL_ID: {"pairs": [pair("x")]}, "m": {"pairs": [pair("y")]}}
        rows = ce.deferred_pair_rows(composed, sources)
        self.assertEqual([(r["mill_id"], r["success_slug"]) for r in rows], [("m", "y")])
        self.assertEqual(set(rows[0]), set(PAIR_JSONL_KEYS))

    def test_dumps_pairs_jsonl_is_compact_lines(self) -> None:
        text = ce.dumps_pairs_jsonl([{"b": 1, "a": 2}, {"c": 3}])
        self.assertEqual(text, '{"a":2,"b":1}\n{"c":3}\n')

    def test_key_drift_refuses(self) -> None:
        row = pair("a")
        with (
            mock.patch.object(ce, "PAIR_JSONL_KEYS", ("only",)),
            self.assertRaisesRegex(ValueError, "^deferred pair keys drifted: "),
        ):
            ce.compact_deferred_pair(row, mill_id="m", source_path="m.py")


if __name__ == "__main__":
    unittest.main()
