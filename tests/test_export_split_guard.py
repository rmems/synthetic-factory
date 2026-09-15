#!/usr/bin/env python3
"""The two-sided split guard in ``export_split`` is reachable, not defensive.

``_partition_by_eval_keys`` carried a comment claiming request validation made
its refusal unreachable. It does not: the split is keyed on the
``(source_file, source_line)`` identity, while ``_rebalance_one_sided_split``
compares a set of those identities against a count of rows, so a corpus
carrying the same identity twice defeats the rebalance and lands every row on
one side. ``export_hf`` builds one row per physical line per distinct curated
file, so its own corpora cannot reach this; ``split_rows`` is public API and
callers can.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

_PIPELINES = Path(__file__).resolve().parents[1] / "pipelines"
if str(_PIPELINES) not in sys.path:
    sys.path.insert(0, str(_PIPELINES))

import export_split  # noqa: E402
from export_contract import ExportError, ViewerRow  # noqa: E402

_FRACTIONS = (0.1, 0.25, 0.5, 0.75, 0.9)


class TwoSidedSplitGuard(unittest.TestCase):
    def test_duplicate_row_identities_are_refused_at_every_fraction(self):
        rows = [ViewerRow("a/b.jsonl", 1, "{}"), ViewerRow("a/b.jsonl", 1, "{}")]
        for fraction in _FRACTIONS:
            with (
                self.subTest(eval_fraction=fraction),
                self.assertRaisesRegex(ExportError, "both split sides"),
            ):
                export_split.split_rows(rows, eval_fraction=fraction, salt="s")

    def test_distinct_row_identities_still_split_two_sided(self):
        rows = [ViewerRow("a/b.jsonl", 1, "{}"), ViewerRow("a/b.jsonl", 2, "{}")]
        for fraction in _FRACTIONS:
            with self.subTest(eval_fraction=fraction):
                train, evaluate = export_split.split_rows(
                    rows, eval_fraction=fraction, salt="s"
                )
                self.assertEqual(len(train), 1)
                self.assertEqual(len(evaluate), 1)


if __name__ == "__main__":
    unittest.main()
