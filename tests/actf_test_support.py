#!/usr/bin/env python3
"""Shared ACTF test imports. Puts ``pipelines/`` on ``sys.path``."""

from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PIPELINES = REPO / "pipelines"
FIXTURE_TREE = REPO / "tests" / "fixtures" / "actf" / "recovery-tree"
FAMILY_MODULES = ("_contract", "vocabulary", "lineage", "ast_scan", "records", "cli")

if str(PIPELINES) not in sys.path:
    sys.path.insert(0, str(PIPELINES))

from actf import ast_scan, cli, lineage, records  # noqa: E402
from actf import vocabulary as cv  # noqa: E402
from actf._contract import dumps_exact_json, load_strict_json  # noqa: E402
