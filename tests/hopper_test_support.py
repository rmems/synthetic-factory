#!/usr/bin/env python3
"""Shared import path and refusal helper for hopper tests."""

from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PIPELINES = REPO / "pipelines"
if str(PIPELINES) not in sys.path:
    sys.path.insert(0, str(PIPELINES))
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from coded_refusal_test_support import CodedFamily, coded_refusal  # noqa: E402
from hopper import _contract as hc  # noqa: E402

FAMILY = CodedFamily(hc.HopperRefusal, hc.FINDING_CODE_SET, frozenset())
FIXTURE = REPO / "tests" / "fixtures" / "hopper"
CATALOG = REPO / "config" / "hopper"
G46C_SLUG = "zombodb-refresh-vs-truncate"


def refusal(case, code, *fragments):
    return coded_refusal(case, FAMILY, code, *fragments)
