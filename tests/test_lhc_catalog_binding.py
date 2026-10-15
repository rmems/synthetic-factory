"""Pin how ``lhc.catalog.load_catalog`` binds the committed extract to its pins.

Each case copies ``CATALOG.json`` and ``pairs.jsonl`` into a temporary
directory, perturbs one thing, and checks the refusal that fires first.
"""

from __future__ import annotations

import ast
import copy
import dataclasses
import json
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "pipelines"))

from lhc import catalog as lhc_catalog
from lhc import catalog_extract_plants as plants_extract
from lhc.catalog import load_catalog
from lhc.catalog_extract_jsonl import load_pair_rows
from lhc.sources import catalog_sources
from lhc.vocabulary import EXCLUDED_DEFERRED_MILL_ID, SLICE_MILL_ID

_PACKAGE = REPO / "pipelines" / "lhc"
_CATALOG = json.loads((_PACKAGE / "CATALOG.json").read_text(encoding="utf-8"))
_PAIRS_TEXT = (_PACKAGE / "pairs.jsonl").read_text(encoding="utf-8")
_PAIRS = [json.loads(line) for line in _PAIRS_TEXT.splitlines()]
def _first_deferred_mill() -> str:
    for mill_id, mill in _CATALOG["mills"].items():
        if mill_id not in (SLICE_MILL_ID, EXCLUDED_DEFERRED_MILL_ID) and mill.get("n_rows"):
            return mill_id
    raise AssertionError("the committed LHC catalog has no deferred mill with pair rows")


_DEFERRED = _first_deferred_mill()


def _dump(rows) -> str:
    return "".join(
        json.dumps(row, ensure_ascii=True, sort_keys=True, separators=(",", ":")) + "\n" for row in rows
    )


def _catalog_with(mutate):
    document = copy.deepcopy(_CATALOG)
    mutate(document)
    return document


def _load_copy(root: Path, document=None, pairs_text=_PAIRS_TEXT):
    """Write a (perturbed) catalog copy into ``root`` and load it."""
    (root / "CATALOG.json").write_text(json.dumps(document or _CATALOG), encoding="utf-8")
    if pairs_text is not None:
        (root / "pairs.jsonl").write_bytes(pairs_text.encode("utf-8"))
    return load_catalog(root / "CATALOG.json")


def _refusal(document=None, pairs_text=_PAIRS_TEXT) -> str:
    """The ValueError text ``load_catalog`` raises for a perturbed copy."""
    with tempfile.TemporaryDirectory(prefix="lhc-binding-") as td:
        try:
            _load_copy(Path(td), document, pairs_text)
        except ValueError as exc:
            return str(exc)
    raise AssertionError("load_catalog accepted the perturbed copy")


def _rows_refusal(text: str | None) -> tuple[str, Path]:
    """The ValueError text ``load_pair_rows`` raises, and the path it read."""
    with tempfile.TemporaryDirectory(prefix="lhc-pairs-") as td:
        path = Path(td) / "pairs.jsonl"
        if text is not None:
            path.write_bytes(text.encode("utf-8"))
        try:
            load_pair_rows(path)
        except ValueError as exc:
            return str(exc), path
    raise AssertionError("load_pair_rows accepted the perturbed rows")


class CatalogHeaderBindingTests(unittest.TestCase):
    def test_committed_copy_loads(self):
        with tempfile.TemporaryDirectory(prefix="lhc-binding-") as td:
            self.assertEqual(set(_load_copy(Path(td)).mills), set(_CATALOG["mills"]))

    def test_identity_and_mill_set_drift_are_refused(self):
        self.assertTrue(_refusal(document=_catalog_with(lambda d: d.update(slice="x"))).endswith(
            "slice drifted from vocabulary"
        ))
        missing = _refusal(document=_catalog_with(lambda d: d["mills"].pop(_DEFERRED)))
        self.assertEqual(missing, f"catalog mills drifted from sources: extra=[] missing=['{_DEFERRED}']")

    def test_slice_rows_pins_and_inline_pairs_are_refused(self):
        cases = (
            (lambda d: d["mills"][SLICE_MILL_ID].update(n_rows=1), "w4x-r4358 slice n_rows does not match"),
            (lambda d: d["mills"][_DEFERRED].update(pairs=[{}]), f"{_DEFERRED} is not the first slice"),
        )
        for mutate, prefix in cases:
            with self.subTest(prefix=prefix):
                self.assertTrue(_refusal(document=_catalog_with(mutate)).startswith(prefix))

    def test_pair_identity_drift_is_refused(self):
        cases = (
            (lambda d: d["mills"][_DEFERRED].update(first_slug="zz"), f"{_DEFERRED} first_slug drifted"),
            (lambda d: d["mills"][_DEFERRED].update(last_slug="zz"), f"{_DEFERRED} last_slug drifted"),
            (
                lambda d: d["mills"][_DEFERRED].update(n_rows=d["mills"][_DEFERRED]["n_rows"] + 1),
                "deferred pair width drifted from vocabulary",
            ),
        )
        for mutate, prefix in cases:
            with self.subTest(prefix=prefix):
                self.assertTrue(_refusal(document=_catalog_with(mutate)).startswith(prefix))
        dropped = _refusal(pairs_text=_dump(_PAIRS[:-1]))
        self.assertTrue(dropped.endswith("n_rows does not match committed pair identities"), dropped)


class SourcePinTests(unittest.TestCase):
    def test_a_mill_whose_pin_disagrees_with_sources_is_refused(self):
        mills = dict(load_catalog().mills)
        expected = {source.mill_id: source for source in catalog_sources()}
        mills[_DEFERRED] = dataclasses.replace(mills[_DEFERRED], pairs=(), blob_sha="0" * 40)
        with self.assertRaises(ValueError) as caught:
            lhc_catalog._bind_header(mills, expected)
        self.assertEqual(str(caught.exception), f"{_DEFERRED} pin disagrees with sources.py")


class DeferredPairOverlayTests(unittest.TestCase):
    def test_pair_rows_for_excluded_unknown_or_drifted_mills_are_refused(self):
        first = _PAIRS[0]
        cases = (
            (_PAIRS + [dict(first, mill_id=SLICE_MILL_ID)], "pairs.jsonl must omit the w4x first-slice mill"),
            (_PAIRS + [dict(first, mill_id=EXCLUDED_DEFERRED_MILL_ID)], f"pairs.jsonl must omit {EXCLUDED_DEFERRED_MILL_ID}"),
            (_PAIRS + [dict(first, mill_id="lhc-mill-zz")], "pairs.jsonl names unknown mill lhc-mill-zz"),
            ([dict(first, i=5)] + _PAIRS[1:], f"{first['mill_id']} pair index drifted"),
            ([dict(first, path="x.py")] + _PAIRS[1:], f"{first['mill_id']} path drifted from catalog"),
        )
        for rows, message in cases:
            with self.subTest(message=message):
                self.assertEqual(_refusal(pairs_text=_dump(rows)), message)


class PairRowsFramingTests(unittest.TestCase):
    def test_framing_and_row_shape_refusals_name_the_line(self):
        first = json.dumps(_PAIRS[0], separators=(",", ":"))
        cases = (
            (_PAIRS_TEXT[:-1],"pairs.jsonl must be LF-framed jsonl"),
            ("", "pairs.jsonl must be LF-framed jsonl"),
            (first + "\n\n", "pairs.jsonl:2 is empty"),
            (" " + first + "\n", "pairs.jsonl:1 is not compact"),
            ("{\n", "pairs.jsonl:1 is not JSON: "),
            ("[1]\n", "pairs.jsonl:1 keys differ"),
            (json.dumps(dict(_PAIRS[0], extra=1)) + "\n", "pairs.jsonl:1 keys differ"),
        )
        for text, prefix in cases:
            with self.subTest(prefix=prefix):
                self.assertTrue(_rows_refusal(text)[0].startswith(prefix))

    def test_unreadable_file_is_refused_with_its_path(self):
        message, path = _rows_refusal(None)
        self.assertTrue(message.startswith(f"cannot load LHC pairs {path}: "), message)

    def test_committed_rows_load_in_order(self):
        self.assertEqual(load_pair_rows(_PACKAGE / "pairs.jsonl"), _PAIRS)


class PlantIdentityTests(unittest.TestCase):
    def test_p_constructor_identity_needs_literal_slug_and_plant(self):
        cases = {
            "P(slug='s')": None,
            "P(**spec)": None,
            "P(slug=name, plant='p')": None,
            "P('ok', slug='s', plant='p')": {"slug": "s", "plant": "p", "ok": "ok", "key": None},
            "P(slug='s', plant='p', ok=1)": {"slug": "s", "plant": "p", "ok": 1, "key": None},
        }
        for source, expected in cases.items():
            with self.subTest(source=source):
                node = ast.parse(source, mode="eval").body
                self.assertEqual(plants_extract._p_identity(node), expected)

    def test_a_plants_table_with_a_spread_entry_is_not_read(self):
        spread = plants_extract.plants_context(ast.parse("PLANTS = {**base, 'a': P(slug='s', plant='p')}"))
        plain = plants_extract.plants_context(ast.parse("PLANTS = {'a': P(slug='s', plant='p')}"))
        self.assertEqual(spread[:2], ({}, None))
        self.assertEqual(plain[:2], ({"a": {"slug": "s", "plant": "p", "ok": None, "key": None}}, "P"))


if __name__ == "__main__":
    unittest.main()
