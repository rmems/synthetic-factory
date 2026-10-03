#!/usr/bin/env python3
"""Source-kind, hidden-reasoning, and strict-input tests (#154)."""

from __future__ import annotations

import copy
import sys
import tempfile
import unittest
from pathlib import Path

_TESTS = Path(__file__).resolve().parent
if str(_TESTS) not in sys.path:
    sys.path.insert(0, str(_TESTS))

from vset_testutil import ACCEPT, codes as _codes, load_record as _load, vset  # noqa: E402


class SourceKindStrictnessTests(unittest.TestCase):
    def setUp(self) -> None:
        self.record = _load(ACCEPT / "issue-patch-validated.json")

    def test_hyphenated_prometheus_in_training_view_is_a_masquerade(self) -> None:
        record = copy.deepcopy(self.record)
        record["training_view"]["notes"] = "operation-prometheus lineage"
        self.assertIn("vset.source_kind_masquerade", _codes(vset.validate_record(record)))

    def test_lookalike_hidden_reasoning_key_is_rejected(self) -> None:
        record = copy.deepcopy(self.record)
        record["training_view"]["th\u043eught"] = "private"  # Cyrillic о
        self.assertIn(
            "vset.hidden_reasoning_in_training_view",
            _codes(vset.validate_record(record)),
        )

    def test_nan_is_rejected(self) -> None:
        record = copy.deepcopy(self.record)
        record["curation"]["score"] = float("nan")
        self.assertIn("vset.payload_invalid", _codes(vset.validate_record(record)))

    def test_duplicate_reason_codes_are_rejected(self) -> None:
        record = copy.deepcopy(self.record)
        record["curation"]["reason_codes"] = ["kept", "kept"]
        self.assertIn("vset.actor_fields_invalid", _codes(vset.validate_record(record)))

    def test_cli_fails_on_an_empty_directory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            code = vset.main([tmp])
        self.assertEqual(code, 1)

    def test_cli_rejects_manifest_combined_with_oracle(self) -> None:
        code = vset.main(["--manifest", str(ACCEPT), "--oracle"])
        self.assertEqual(code, 2)


if __name__ == "__main__":
    unittest.main()
