#!/usr/bin/env python3
"""Re-derive the published #74 audit from its append-only raw corpus.

Split out of test_payload_kind_audit.py: this is the one test in the #74
suite that touches the gitignored raw tree, so it is skipped wherever that
tree is absent (any checkout other than one that ran the factory harvest).
"""

import hashlib
import json
import sys
import unittest
from pathlib import Path

_TESTS = Path(__file__).resolve().parent
if str(_TESTS) not in sys.path:
    sys.path.insert(0, str(_TESTS))

from payload_kind_audit_fixtures import (  # noqa: E402
    AUDIT_JSON,
    DERIVED_KEYS,
    RAW_AGENTIC_CODING,
    REPO,
)

PIPELINES = REPO / "pipelines"
if str(PIPELINES) not in sys.path:
    sys.path.insert(0, str(PIPELINES))

import payload_kind_audit  # noqa: E402


@unittest.skipUnless(
    RAW_AGENTIC_CODING.is_dir(),
    "raw agentic-coding corpus not present in this checkout (gitignored); "
    "the published audit is re-derived only where the immutable raw tree exists",
)
class AgenticCodingRawCorpusFidelity(unittest.TestCase):
    """Re-derive the published snapshot from its append-only source, read-only."""

    def test_the_published_audit_is_a_fresh_scan_of_the_raw_corpus(self):
        before = {
            path.name: hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sorted(RAW_AGENTIC_CODING.glob("*.jsonl"))
        }
        published = json.loads(AUDIT_JSON.read_text(encoding="utf-8"))
        discovered_names = sorted(
            path.name for path in RAW_AGENTIC_CODING.glob("*.jsonl")
        )
        published_names = [entry["path"] for entry in published["files"]]
        self.assertEqual(
            discovered_names,
            published_names,
            "published files must name every raw JSONL in this checkout",
        )
        derived = payload_kind_audit.build_audit(RAW_AGENTIC_CODING)
        after = {
            path.name: hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sorted(RAW_AGENTIC_CODING.glob("*.jsonl"))
        }
        self.assertEqual(before, after, "the audit must never write to the raw corpus")

        self.assertEqual(
            {key: derived[key] for key in DERIVED_KEYS},
            {key: published[key] for key in DERIVED_KEYS},
        )
        self.assertEqual(set(derived), set(DERIVED_KEYS))


if __name__ == "__main__":
    unittest.main()
