#!/usr/bin/env python3
"""Bridge clock-domain regressions for identity curation."""

import sys
import unittest
from pathlib import Path

_TESTS = Path(__file__).resolve().parent
if str(_TESTS) not in sys.path:
    sys.path.insert(0, str(_TESTS))

from test_curate_identity import FABLE_BRIDGE, identity, source, thalamic  # noqa: E402


class TestBridgeClockIdentityCuration(unittest.TestCase):
    def test_bridge_owner_clock_conflict_excludes_from_identity_tree(self):
        bridge = {
            "clock_id": "outer",
            "language_view": {"trajectory": thalamic("designed")},
            "spike_events": [
                {
                    "channel": "x",
                    "t_rel_ms": 1,
                    "amplitude": 1,
                    "source_clock": "inner",
                }
            ],
            "meta": {"factory": FABLE_BRIDGE},
        }
        result = identity.curate_record(
            source(bridge, f"{FABLE_BRIDGE}/batch.jsonl", 1)
        )
        self.assertEqual(result.action, "exclude")
        self.assertEqual(
            result.mapping["reason_codes"], ["identity.invalid_payload_shape"]
        )
        self.assertTrue(
            any("one clock domain" in error for error in result.mapping["details"])
        )


if __name__ == "__main__":
    unittest.main()
