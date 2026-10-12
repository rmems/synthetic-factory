"""search.catalog pin binding: each drift check, its message, and the order they run in."""

from __future__ import annotations

import copy
import sys
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "pipelines"))

from search import catalog as sc
from search.catalog_extract import (
    home_jsonl_path,
    home_mill_pins,
    load_home_header,
    load_home_rows,
)
from search.sources import R31_SOURCE, catalog_sources
from search.vocabulary import R31_MILL_ID

LEFTOVER_ID = "search_index_rebuild_leftover3_mill"


def _leftover_pair():
    sources = {source.mill_id: source for source in catalog_sources()}
    return sc.CATALOG.mills[LEFTOVER_ID], sources[LEFTOVER_ID]


class LeftoverMillBindingTests(unittest.TestCase):
    def test_committed_catalog_binds_to_sources(self):
        self.assertIsNone(sc._bind_sources(sc.CATALOG))
        mill, source = _leftover_pair()
        self.assertIsNone(sc._bind_mill_to_source(LEFTOVER_ID, mill, source))
        self.assertIsNone(sc._check_pair_rows(LEFTOVER_ID, mill))

    def test_each_source_drift_names_its_field(self):
        mill, source = _leftover_pair()
        cases = (
            (replace(mill, path="experiments/other.py"), "pin"),
            (replace(mill, blob_sha="0" * 40), "pin"),
            (replace(mill, catalog_first=mill.catalog_first + 1), "catalog_first"),
            (replace(mill, n_hops=mill.n_hops + 1), "hop count"),
            (replace(mill, hops=mill.hops[:-1]), "hop count"),
        )
        for drifted, field in cases:
            with self.subTest(field=field), self.assertRaises(ValueError) as caught:
                sc._bind_mill_to_source(LEFTOVER_ID, drifted, source)
            self.assertEqual(
                str(caught.exception), f"{LEFTOVER_ID} {field} disagrees with sources.py"
            )

    def test_pair_row_drift(self):
        mill, _ = _leftover_pair()
        for drifted in (
            replace(mill, n_rounds=mill.n_rounds + 1),
            replace(mill, pairs=mill.pairs[:-1]),
        ):
            with self.assertRaisesRegex(ValueError, f"^{LEFTOVER_ID} pair rows do not match n_rows$"):
                sc._check_pair_rows(LEFTOVER_ID, drifted)

    def test_source_pin_is_checked_before_pair_rows(self):
        mill, _ = _leftover_pair()
        drifted = replace(mill, blob_sha="0" * 40, n_rounds=mill.n_rounds + 1)
        mills = dict(sc.CATALOG.mills)
        mills[LEFTOVER_ID] = drifted
        with self.assertRaisesRegex(ValueError, "pin disagrees with sources.py"):
            sc._bind_sources(replace(sc.CATALOG, mills=mills))


class HomeMillHeaderTests(unittest.TestCase):
    def setUp(self):
        self.pins = home_mill_pins(R31_MILL_ID)
        self.header = load_home_header(R31_MILL_ID)

    def test_committed_header_matches_pins(self):
        self.assertIsNone(sc._check_home_header(R31_MILL_ID, self.header, self.pins))

    def test_each_header_drift_names_its_field(self):
        cases = (
            (("mill", "mill_id"), "header mill pin drifted from vocabulary"),
            (("mill", "path"), "header mill pin drifted from vocabulary"),
            (("mill", "blob_sha"), "header source hashes drifted from vocabulary"),
            (("mill", "sha256"), "header source hashes drifted from vocabulary"),
            (("pairs_sha256",), "header pairs_sha256 drifted from vocabulary"),
        )
        for keys, message in cases:
            header = copy.deepcopy(self.header)
            target = header
            for key in keys[:-1]:
                target = target[key]
            target[keys[-1]] = "drifted"
            with self.subTest(keys=keys), self.assertRaises(ValueError) as caught:
                sc._check_home_header(R31_MILL_ID, header, self.pins)
            self.assertEqual(str(caught.exception), f"{R31_MILL_ID} {message}")


class HomeMillRowsTests(unittest.TestCase):
    def setUp(self):
        self.pins = home_mill_pins(R31_MILL_ID)
        self.rows = load_home_rows(R31_MILL_ID)
        self.path = Path("r31.jsonl")

    def test_committed_rows_give_the_pinned_slug_window(self):
        window = sc._home_slug_window(self.path, self.rows, self.pins)
        self.assertEqual(window, (self.pins.first_slug, self.pins.last_slug))

    def test_row_count_drift(self):
        rows = self.rows[:-1]
        expected = f"r31.jsonl expected {self.pins.n_rows} rows, found {len(rows)}"
        with self.assertRaises(ValueError) as caught:
            sc._home_slug_window(self.path, rows, self.pins)
        self.assertEqual(str(caught.exception), expected)

    def test_slug_window_drift(self):
        rows = copy.deepcopy(self.rows)
        rows[-1]["success_slug"] = "drifted"
        with self.assertRaises(ValueError) as caught:
            sc._home_slug_window(self.path, rows, self.pins)
        self.assertEqual(
            str(caught.exception),
            f"r31.jsonl first/last slugs drifted: {self.pins.first_slug} / drifted",
        )

    def test_round_drift(self):
        rows = copy.deepcopy(self.rows)
        rows[1]["round"] = -1
        expected_round = self.pins.catalog_first + 1
        with self.assertRaises(ValueError) as caught:
            sc._home_slug_window(self.path, rows, self.pins)
        self.assertEqual(
            str(caught.exception), f"r31.jsonl row 1 round drifted from {expected_round}"
        )

    def test_load_home_mill_refuses_a_truncated_jsonl(self):
        lines = home_jsonl_path(R31_MILL_ID).read_text(encoding="utf-8").splitlines(True)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "r31.jsonl"
            path.write_text("".join(lines[:-1]), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, f"expected {self.pins.n_rows} rows, found"):
                sc.load_home_mill(R31_MILL_ID, path)


class HomeMillSourceTests(unittest.TestCase):
    def setUp(self):
        self.pins = home_mill_pins(R31_MILL_ID)
        self.source = R31_SOURCE

    def test_committed_source_matches_pins(self):
        self.assertIsNone(sc._check_home_source(R31_MILL_ID, self.source, self.pins))

    def test_each_source_drift_names_its_field(self):
        cases = (
            (replace(self.source, path="experiments/other.py"), "source pin drifted"),
            (replace(self.source, blob_sha="0" * 40), "source pin drifted"),
            (replace(self.source, catalog_first=0), "source window drifted"),
            (replace(self.source, n_hops=1), "source window drifted"),
        )
        for drifted, message in cases:
            with self.subTest(message=message), self.assertRaises(ValueError) as caught:
                sc._check_home_source(R31_MILL_ID, drifted, self.pins)
            self.assertEqual(str(caught.exception), f"{R31_MILL_ID} {message} from vocabulary")
        with self.assertRaises(ValueError) as caught:
            sc._check_home_source(R31_MILL_ID, replace(self.source, kind="other"), self.pins)
        self.assertEqual(str(caught.exception), f"{R31_MILL_ID} source kind is not home-pairs")


if __name__ == "__main__":
    unittest.main()
