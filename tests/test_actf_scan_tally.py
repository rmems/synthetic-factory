"""Pin ``actf.ast_scan.scan_source`` feature counts and raw-tree write findings."""

from __future__ import annotations

import unittest

from actf_test_support import ast_scan, cv

_SOURCE = f"""
import os
from pathlib import Path

class Mill:
    pass

async def ep7():
    return '{cv.FACTORY}'

def ep():
    open('outputs/raw/run/batch.jsonl', 'w').write('x')
    Path('notes.md').write_text('outputs/raw/elsewhere')
    open('outputs/raw/run/batch.jsonl')
"""


class ScanTallyTests(unittest.TestCase):
    def test_features_count_every_definition_import_call_and_literal(self):
        result = ast_scan.scan_source(_SOURCE)
        self.assertEqual(result.syntax_status, cv.SYNTAX_OK)
        features = result.features
        self.assertEqual((features.functions, features.classes, features.imports, features.calls), (2, 1, 2, 5))
        self.assertEqual(features.episode_functions, ("ep7",))
        self.assertEqual(features.factory_literals, (cv.FACTORY,))

    def test_writes_that_name_the_raw_tree_are_raw_dataset_mutations(self):
        findings = [(item.category, item.line) for item in ast_scan.scan_source(_SOURCE).operations]
        self.assertIn((cv.FINDING_FILE_WRITE, 12), findings)
        self.assertIn((cv.FINDING_RAW_DATASET_MUTATION, 12), findings)
        self.assertIn((cv.FINDING_RAW_DATASET_MUTATION, 13), findings)
        self.assertNotIn((cv.FINDING_FILE_WRITE, 14), findings)
        self.assertIn((cv.FINDING_SENSITIVE_IMPORT, 2), findings)


if __name__ == "__main__":
    unittest.main()
