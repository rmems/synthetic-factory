#!/usr/bin/env python3
"""Exact-number regressions for promotion JSONL I/O."""

import json
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "pipelines"))

import promote  # noqa: E402
from exact_json import MAX_JSON_NESTING_DEPTH  # noqa: E402


class PromoteExactJSON(unittest.TestCase):
    def test_excessive_json_nesting_is_preserved_as_unpromoted_input(self):
        nested = "[" * (MAX_JSON_NESTING_DEPTH + 1) + "0" + "]" * (
            MAX_JSON_NESTING_DEPTH + 1
        )
        payload = '{"state":{"sim_or_real":"designed","extension":' + nested + "}}"
        with tempfile.TemporaryDirectory() as td:
            raw = Path(td) / "raw"
            cleaned = Path(td) / "cleaned"
            source = raw / "f" / "nested.jsonl"
            source.parent.mkdir(parents=True)
            source.write_text(payload + "\n", encoding="utf-8")

            result = promote.promote_run(raw, cleaned)

            promoted = (cleaned / "f" / "nested.jsonl").read_text(encoding="utf-8")

        self.assertEqual(result["records"], 0)
        self.assertEqual(promoted, payload + "\n")

    def test_exact_numbers_survive_promotion_and_drive_event_sorting(self):
        with tempfile.TemporaryDirectory() as td:
            raw = Path(td) / "raw"
            cleaned = Path(td) / "cleaned"
            source = raw / "f" / "exact.jsonl"
            source.parent.mkdir(parents=True)
            record = {
                "state": {"sim_or_real": "designed"},
                "raster": {"mean_rate_hz": "__EXACT_RATE__"},
                "spike_events": [
                    {"channel": "late", "t_rel_ms": "__LATE__"},
                    {"channel": "early", "t_rel_ms": "__EARLY__"},
                ],
            }
            payload = json.dumps(record, separators=(",", ":"))
            payload = payload.replace('"__EXACT_RATE__"', "25.000000000000001")
            payload = payload.replace('"__LATE__"', "1.0000000000000001")
            payload = payload.replace('"__EARLY__"', "1.0")
            source.write_text(payload + "\n", encoding="utf-8")

            result = promote.promote_run(raw, cleaned)

            promoted = (cleaned / "f" / "exact.jsonl").read_text(encoding="utf-8")
            parsed = json.loads(promoted)
            self.assertEqual(result["resorted"], 1)
            self.assertEqual(
                [event["channel"] for event in parsed["spike_events"]],
                ["early", "late"],
            )
            self.assertIn('"mean_rate_hz":25.000000000000001', promoted)
            self.assertLess(
                promoted.index('"t_rel_ms":1.0'),
                promoted.index('"t_rel_ms":1.0000000000000001'),
            )


if __name__ == "__main__":
    unittest.main()
