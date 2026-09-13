#!/usr/bin/env python3
"""Exact-JSON preservation at the reward conversion boundary."""

import hashlib
import sys
import tempfile
import unittest
from pathlib import Path

PIPELINES = Path(__file__).resolve().parents[1] / "pipelines"
if str(PIPELINES) not in sys.path:
    sys.path.insert(0, str(PIPELINES))

import curate_rewards  # noqa: E402
from exact_json import MAX_JSON_NESTING_DEPTH, parse_finite_json_float  # noqa: E402


class RewardExactJSON(unittest.TestCase):
    def test_conversion_rejects_excessive_nesting_before_output_mutation(self):
        nested = "[" * (MAX_JSON_NESTING_DEPTH + 1) + "0" + "]" * (
            MAX_JSON_NESTING_DEPTH + 1
        )
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root / "source.jsonl"
            output = root / "output.jsonl"
            sidecars = root / "sidecars.jsonl"
            source.write_text(
                '{"id":"too-deep","extension":' + nested + "}\n",
                encoding="utf-8",
            )

            with self.assertRaisesRegex(curate_rewards.RewardOntologyError, "JSON nesting"):
                curate_rewards.convert_jsonl(source, output, sidecars)

            self.assertFalse(output.exists())
            self.assertFalse(sidecars.exists())

    def test_conversion_preserves_precision_sensitive_reward_tokens(self):
        decimal_lexeme = "0.10000000000000001"
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root / "source.jsonl"
            output = root / "output.jsonl"
            sidecars = root / "sidecars.jsonl"
            source.write_text(
                '{"id":"exact","reward_components":'
                f'{{"task_progress":{decimal_lexeme},"total":{decimal_lexeme}}}}}\n',
                encoding="utf-8",
            )

            curate_rewards.convert_jsonl(source, output, sidecars)

            output_text = output.read_text(encoding="utf-8")
            sidecar_text = sidecars.read_text(encoding="utf-8")

        self.assertIn(decimal_lexeme, output_text)
        self.assertIn(decimal_lexeme, sidecar_text)
        value = parse_finite_json_float(decimal_lexeme)
        self.assertEqual(
            curate_rewards._sha256(value),
            "sha256:" + hashlib.sha256(decimal_lexeme.encode("utf-8")).hexdigest(),
        )
        self.assertEqual(
            curate_rewards.canonical_bytes(value), decimal_lexeme.encode("utf-8")
        )


if __name__ == "__main__":
    unittest.main()
