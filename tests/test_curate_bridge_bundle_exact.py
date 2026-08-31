#!/usr/bin/env python3
"""Regression coverage for exact decimals emitted by the Bridge bundle CLI."""

from __future__ import annotations

import contextlib
import hashlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
if str(REPO / "pipelines") not in sys.path:
    sys.path.insert(0, str(REPO / "pipelines"))

import curate_bridge  # noqa: E402
from exact_json import parse_finite_json_float  # noqa: E402


class BridgeBundleExactJSONTests(unittest.TestCase):
    def test_bundle_output_record_rehashes_with_its_exact_decimal(self):
        """Changing bundle output to ordinary JSON encoding rounds its output hash."""

        decimal = "1.0000000000000001"
        source_line = (
            '{"id":"bundle-exact","spike_events":[{"channel":"only",'
            f'"t_rel_ms":{decimal},"amplitude":0.5}}],'
            '"language_view":{"trajectory":{"state":{"episode_id":"bundle-exact"}}}}'
            "\n"
        )

        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            source = root / "bridge.jsonl"
            source.write_text(source_line, encoding="utf-8")
            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                self.assertEqual(
                    curate_bridge.main(
                        ["--source-root", str(root), "--emit", "bundle", str(source)]
                    ),
                    0,
                )

        bundle = json.loads(stdout.getvalue(), parse_float=parse_finite_json_float)
        decision = bundle["decisions"][0]
        output_record = decision["output_record"]

        self.assertEqual(output_record["spike_events"][0]["t_rel_ms"].json_token, decimal)
        self.assertEqual(
            hashlib.sha256(curate_bridge.canonical_json_bytes(output_record)).hexdigest(),
            decision["manifest"]["output_hash"],
        )


if __name__ == "__main__":
    unittest.main()
