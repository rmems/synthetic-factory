"""Deterministic membership selection, independent of record validation."""
import unittest

from pipelines.code_repair import selection


def candidate(identity, text, digest, lineage):
    return {"id": identity, "scenario": {"broken_program": {"files": {"program.py": text}}},
            "result": {"broken_sha256": digest},
            "provenance": {"split_lineage": {"lineage_id": lineage}}}


class SelectionTests(unittest.TestCase):
    def test_membership_uses_stable_id_order_before_dedup_and_cap(self):
        records = [candidate("b", "def f():\n return 1\n", "one", "lineage"),
                   candidate("a", "def f():\n return 2\n", "two", "lineage"),
                   candidate("c", "def f():\n return 3\n", "three", "lineage")]
        selected = selection.selected_records(records, lineage_cap=2)
        self.assertEqual([r["id"] for r in selected], ["a", "b"])
        self.assertEqual([r["id"] for r in records], ["b", "a", "c"])

    def test_structural_duplicates_do_not_consume_lineage_cap(self):
        records = [candidate("a", "def f():\n return 1\n", "one", "lineage"),
                   candidate("b", "def f():\n  return 1\n", "one-spaced", "lineage"),
                   candidate("c", "def f():\n return 2\n", "two", "lineage")]
        self.assertEqual([r["id"] for r in selection.selected_records(records, lineage_cap=2)],
                         ["a", "c"])

    def test_boolean_zero_and_negative_caps_are_refused(self):
        for cap in (True, 0, -1):
            with self.subTest(cap=cap), self.assertRaises(ValueError):
                selection.selected_records([], lineage_cap=cap)
