#!/usr/bin/env python3
"""ACTF vocabulary is declared, unique, and fail-closed on vendor paths."""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from actf_test_support import FAMILY_MODULES, cv


class VocabularyTests(unittest.TestCase):
    def test_family_and_corpus_pins(self):
        self.assertEqual(cv.FAMILY, "actf")
        self.assertEqual(cv.CORPUS, "burst-corpus-b")
        self.assertEqual(cv.FACTORY, "agentic-coding-trajectory-factory")
        self.assertEqual(cv.RECORD_ID_PREFIX, "actf")
        self.assertEqual(cv.LINEAGE_PREFIX, "actf-")
        self.assertEqual(cv.RECOVERY_SESSION, "01a06111-1b84-7250-aec4-9d120db6c1a4")

    def test_finding_codes_are_unique_and_bound_to_the_refusal(self):
        self.assertEqual(len(cv.FINDING_CODES), len(cv.FINDING_CODE_SET))
        self.assertEqual(cv.ActfRefusal.CODES, cv.FINDING_CODE_SET)

    def test_reason_codes_are_unique_and_namespaced(self):
        self.assertEqual(len(cv.REASON_CODES), len(cv.REASON_CODE_SET))
        self.assertTrue(all(code.startswith("actf.") for code in cv.REASON_CODES))

    def test_classifications_match_the_recover_grok_report(self):
        self.assertEqual(
            cv.CLASSIFICATIONS,
            ("exact", "high-confidence", "partial", "unrecoverable"),
        )

    def test_an_undeclared_finding_code_is_a_programming_error(self):
        with self.assertRaises(LookupError):
            cv.ActfRefusal("NOT_A_CODE", "no")

    def test_refuse_renders_code_then_prose(self):
        with self.assertRaises(cv.ActfRefusal) as caught:
            cv.refuse(cv.FINDING_VENDOR_PATH, "no mills")
        self.assertEqual(caught.exception.code, cv.FINDING_VENDOR_PATH)
        self.assertEqual(str(caught.exception), f"{cv.FINDING_VENDOR_PATH}: no mills")

    def test_vendor_destination_refuses_actf_mill_scripts(self):
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "actf-mill-r10.py"
            with self.assertRaises(cv.ActfRefusal) as caught:
                cv.refuse_vendor_destination(path)
            self.assertEqual(caught.exception.code, cv.FINDING_VENDOR_PATH)

    def test_vendor_destination_allows_the_package_tree(self):
        cv.refuse_vendor_destination(Path("pipelines/actf/records.py"))

    def test_family_modules_are_the_declared_skeleton(self):
        self.assertEqual(
            FAMILY_MODULES,
            ("_contract", "vocabulary", "lineage", "ast_scan", "records", "catalog", "cli"),
        )


if __name__ == "__main__":
    unittest.main()
