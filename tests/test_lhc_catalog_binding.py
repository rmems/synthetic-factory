"""Pin how ``lhc.catalog.load_catalog`` binds the committed extract to its pins.

Each case copies ``CATALOG.json`` and ``pairs.jsonl`` into a temporary
directory, perturbs one thing, and checks the refusal that fires first.
"""

from __future__ import annotations

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
from lhc.catalog import load_catalog
from lhc.catalog_extract_jsonl import load_pair_rows
from lhc.sources import catalog_sources
from lhc.vocabulary import EXCLUDED_DEFERRED_MILL_ID, SLICE_MILL_ID

_PACKAGE = REPO / "pipelines" / "lhc"
_CATALOG = json.loads((_PACKAGE / "CATALOG.json").read_text(encoding="utf-8"))
_PAIRS_TEXT = (_PACKAGE / "pairs.jsonl").read_text(encoding="utf-8")
_PAIRS = [json.loads(line) for line in _PAIRS_TEXT.splitlines()]
_DEFERRED = next(
    mill_id
    for mill_id, mill in _CATALOG["mills"].items()
    if mill_id not in (SLICE_MILL_ID, EXCLUDED_DEFERRED_MILL_ID) and mill.get("n_rows")
)


def _dump(rows) -> str:
    return "".join(
        json.dumps(row, ensure_ascii=True, sort_keys=True, separators=(",", ":")) + "\n" for row in rows
    )


def _catalog_with(mutate):
    document = copy.deepcopy(_CATALOG)
    mutate(document)
    return document


class _Workspace(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory(prefix="lhc-binding-")
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)

    def _load(self, document=None, pairs_text=_PAIRS_TEXT):
        (self.root / "CATALOG.json").write_text(json.dumps(document or _CATALOG), encoding="utf-8")
        if pairs_text is not None:
            (self.root / "pairs.jsonl").write_bytes(pairs_text.encode("utf-8"))
        return load_catalog(self.root / "CATALOG.json")

    def _refusal(self, **kwargs) -> str:
        with self.assertRaises(ValueError) as caught:
            self._load(**kwargs)
        return str(caught.exception)


class CatalogHeaderBindingTests(_Workspace):
    def test_committed_copy_loads(self):
        self.assertEqual(set(self._load().mills), set(_CATALOG["mills"]))

    def test_identity_and_mill_set_drift_are_refused(self):
        self.assertTrue(self._refusal(document=_catalog_with(lambda d: d.update(slice="x"))).endswith(
            "slice drifted from vocabulary"
        ))
        missing = self._refusal(document=_catalog_with(lambda d: d["mills"].pop(_DEFERRED)))
        self.assertEqual(missing, f"catalog mills drifted from sources: extra=[] missing=['{_DEFERRED}']")

    def test_slice_rows_pins_and_inline_pairs_are_refused(self):
        cases = (
            (lambda d: d["mills"][SLICE_MILL_ID].update(n_rows=1), "w4x-r4358 slice n_rows does not match"),
            (lambda d: d["mills"][_DEFERRED].update(pairs=[{}]), f"{_DEFERRED} is not the first slice"),
        )
        for mutate, prefix in cases:
            with self.subTest(prefix=prefix):
                self.assertTrue(self._refusal(document=_catalog_with(mutate)).startswith(prefix))

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
                self.assertTrue(self._refusal(document=_catalog_with(mutate)).startswith(prefix))
        dropped = self._refusal(pairs_text=_dump(_PAIRS[:-1]))
        self.assertTrue(dropped.endswith("n_rows does not match committed pair identities"), dropped)


class SourcePinTests(unittest.TestCase):
    def test_a_mill_whose_pin_disagrees_with_sources_is_refused(self):
        mills = dict(load_catalog().mills)
        expected = {source.mill_id: source for source in catalog_sources()}
        mills[_DEFERRED] = dataclasses.replace(mills[_DEFERRED], pairs=(), blob_sha="0" * 40)
        with self.assertRaises(ValueError) as caught:
            lhc_catalog._bind_header(mills, expected)
        self.assertEqual(str(caught.exception), f"{_DEFERRED} pin disagrees with sources.py")


class DeferredPairOverlayTests(_Workspace):
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
                self.assertEqual(self._refusal(pairs_text=_dump(rows)), message)


class PairRowsFramingTests(_Workspace):
    def _rows_refusal(self, text: str | None) -> str:
        path = self.root / "pairs.jsonl"
        if text is not None:
            path.write_bytes(text.encode("utf-8"))
        with self.assertRaises(ValueError) as caught:
            load_pair_rows(path)
        return str(caught.exception)

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
                self.assertTrue(self._rows_refusal(text).startswith(prefix))

    def test_unreadable_file_is_refused_with_its_path(self):
        message = self._rows_refusal(None)
        self.assertTrue(message.startswith(f"cannot load LHC pairs {self.root / 'pairs.jsonl'}: "), message)

    def test_committed_rows_load_in_order(self):
        self.assertEqual(load_pair_rows(_PACKAGE / "pairs.jsonl"), _PAIRS)


if __name__ == "__main__":
    unittest.main()
