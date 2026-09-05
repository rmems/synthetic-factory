#!/usr/bin/env python3
"""Shared fixtures and helpers for the curated-export test modules.

Split out of ``test_export_hf`` so each test module can state one
responsibility. Not named ``test_*`` so it is not itself collected.
"""

import importlib.util
import json
import sys
from pathlib import Path

TESTS = Path(__file__).resolve().parent
REPO = TESTS.parents[0]
sys.path.insert(0, str(TESTS))
sys.path.insert(0, str(REPO / "pipelines"))

import compose_curated  # noqa: E402

from compose_curated_test_support import build_source_run  # noqa: E402

HAS_PYARROW = importlib.util.find_spec("pyarrow") is not None



def compose_fixture(root):
    """Compose the shared four-factory fixture and return the curated root."""

    source = build_source_run(Path(root) / "run")
    curated = Path(root) / "curated"
    compose_curated.compose_run(source, curated)
    return curated


def calibration_document(*records):
    """A reward-calibration sidecar in the shape the export authenticates."""

    return json.dumps({"records": list(records)}, ensure_ascii=False) + "\n"


ONE_CALIBRATION = calibration_document(
    {"usd_conversion_factor": 0.5, "scope": "applies to ffpc-r5-002"}
)
