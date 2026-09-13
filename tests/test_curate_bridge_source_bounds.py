#!/usr/bin/env python3
"""Bounded-source regressions shared by curation and materialization."""

import json
import tempfile
import unittest
from pathlib import Path

try:
    from tests.test_curate_bridge import curate_bridge, gate_snn_fixture
except ModuleNotFoundError:
    from test_curate_bridge import curate_bridge, gate_snn_fixture  # type: ignore[no-redef]

from exact_json import MAX_JSON_NESTING_DEPTH  # noqa: E402


class BridgeSourceBounds(unittest.TestCase):
    def test_materialization_quarantines_excessive_json_nesting(self):
        nested = "[" * (MAX_JSON_NESTING_DEPTH + 1) + "0" + "]" * (
            MAX_JSON_NESTING_DEPTH + 1
        )
        with tempfile.TemporaryDirectory() as td:
            temporary = Path(td)
            source_root = temporary / "source"
            source = source_root / "bridge" / "batch-r01.jsonl"
            source.parent.mkdir(parents=True)
            source.write_text(
                '{"id":"too-deep","extra":' + nested + "}\n"
                + json.dumps(gate_snn_fixture())
                + "\n",
                encoding="utf-8",
            )

            decisions = curate_bridge.materialize_paths(
                [source],
                source_root=source_root,
                output_dir=temporary / "lane-bridge",
            )

        self.assertEqual([item.action for item in decisions], ["quarantine", "retain"])
        self.assertEqual(
            decisions[0].manifest["reason_codes"],
            [curate_bridge.REASON_INVALID_JSON],
        )
        self.assertIn("JSON nesting", decisions[0].manifest["evidence"]["parse_error"])


if __name__ == "__main__":
    unittest.main()
