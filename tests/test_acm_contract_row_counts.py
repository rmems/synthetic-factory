"""ACM row counts: the deferred count is the remainder of the full extract."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from pipelines.acm import _contract

PACKAGE = Path(__file__).resolve().parents[1] / "pipelines" / "acm"


class AcmRowCountContractTests(unittest.TestCase):
    def test_representative_plus_deferred_is_the_full_extract(self):
        self.assertEqual(
            _contract.REPRESENTATIVE_ROW_COUNT + _contract.DEFERRED_ROW_COUNT,
            _contract.FULL_ROW_COUNT,
        )

    def test_counts_match_the_committed_catalog_and_rows(self):
        header = json.loads((PACKAGE / "CATALOG.json").read_text(encoding="utf-8"))
        extract = header["extract"]
        self.assertEqual(header["row_count"], _contract.REPRESENTATIVE_ROW_COUNT)
        self.assertEqual(len(header["rows"]), _contract.REPRESENTATIVE_ROW_COUNT)
        self.assertEqual(extract["deferred_row_count"], _contract.DEFERRED_ROW_COUNT)
        self.assertEqual(extract["full_row_count"], _contract.FULL_ROW_COUNT)
        rows = (PACKAGE / _contract.ROWS_FILENAME).read_text(encoding="utf-8").splitlines()
        self.assertEqual(len(rows), _contract.DEFERRED_ROW_COUNT)


if __name__ == "__main__":
    unittest.main()
