#!/usr/bin/env python3
"""Replayed evidence preserves JSON types and exact numeric values."""

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from export_test_support import ResearchExportAllowed, compose_fixture
from exact_json import dumps_exact_json, parse_finite_json_float
import export_hf


def _replace_value(document, path, replacement):
    for key in path[:-1]:
        document = document[key]
    document[path[-1]] = replacement


def _reseal_evidence(curated, mutation):
    """Change one evidence claim and authenticate the changed member bytes."""

    member, path, replacement = mutation
    summary_path = curated / "COMPOSE.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    if member == "summary":
        _replace_value(summary, path, replacement)
    else:
        descriptor = summary[member]
        evidence_path = curated / descriptor["path"]
        documents = [
            json.loads(line, parse_float=parse_finite_json_float)
            for line in evidence_path.read_text(encoding="utf-8").splitlines()
        ]
        _replace_value(documents, path, replacement)
        payload = "".join(dumps_exact_json(row) + "\n" for row in documents).encode("utf-8")
        evidence_path.write_bytes(payload)
        descriptor["sha256"] = hashlib.sha256(payload).hexdigest()
    summary_path.write_text(dumps_exact_json(summary) + "\n", encoding="utf-8")


class ExportReplayEvidenceValues(ResearchExportAllowed, unittest.TestCase):
    def _assert_forgery_refused(self, mutation):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            curated = compose_fixture(root)
            _reseal_evidence(curated, mutation)
            destination = root / "export"

            with self.assertRaises(export_hf.ExportError):
                export_hf.export_run(export_hf.ExportRequest(curated, destination))

            self.assertFalse(destination.exists())

    def test_resealed_boolean_number_substitutions_are_refused(self):
        mutations = (
            ("manifest", (0, "source_line"), True),
            ("manifest", (0, "stages", 0, "detail", "identity_authoritative"), 1),
            ("manifest", (0, "stages", 3, "detail", "step_counts", "source"), True),
            ("summary", ("counts", "blank_lines"), False),
            ("summary", ("lane_actions", "bridge", "retained"), True),
            ("summary", ("exclusions", "PROPOSED_ACTION_CONTEXT_DIVERGES"), True),
            ("summary", ("rights", "training_exportable"), 0),
        )
        for mutation in mutations:
            with self.subTest(mutation=mutation):
                self._assert_forgery_refused(mutation)

    def test_resealed_distinct_decimals_with_equal_float_values_are_refused(self):
        mutations = (
            (
                "manifest",
                (4, "stages", 1, "detail", "evidence", "time_min"),
                parse_finite_json_float("1.0000000000000001"),
            ),
            (
                "reward_sidecars",
                (2, "source_rewards", 0, "value", "safety"),
                parse_finite_json_float("0.50000000000000001"),
            ),
        )
        for mutation in mutations:
            with self.subTest(mutation=mutation):
                self._assert_forgery_refused(mutation)

    def test_equivalent_decimal_spellings_still_export_identical_payloads(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            curated = compose_fixture(root)
            _reseal_evidence(
                curated,
                (
                    "reward_sidecars",
                    (2, "source_rewards", 0, "value", "safety"),
                    parse_finite_json_float("5e-1"),
                ),
            )
            destination = root / "export"

            provenance = export_hf.export_run(export_hf.ExportRequest(curated, destination))

            self.assertEqual(provenance["records"], 7)
            for source in (curated / "records").rglob("*.jsonl"):
                exported = destination / "data" / "curated" / source.relative_to(curated / "records")
                self.assertEqual(source.read_bytes(), exported.read_bytes())


if __name__ == "__main__":
    unittest.main()
