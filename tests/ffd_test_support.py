#!/usr/bin/env python3
"""Shared surface for the ``test_ffd_*`` modules."""

from __future__ import annotations

import subprocess
import sys
import types
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "pipelines"))

from distill_contract_test_support import REPO
from ffd import catalog, cli, generate
from ffd._contract import FfdRefusal, FINDING_CODE_SET

LEGACY = catalog.LEGACY_COMMIT

__all__ = (
    "FINDING_CODE_SET",
    "FfdRefusal",
    "LEGACY",
    "REPO",
    "catalog",
    "cli",
    "generate",
    "legacy_module",
    "legacy_source",
)


def legacy_source(source_id: str) -> str:
    path = catalog.SOURCE_PATHS[source_id]
    return subprocess.check_output(["git", "show", f"{LEGACY}:{path}"], text=True)


def legacy_module(source_id: str):
    module = types.ModuleType(f"legacy_ffd_{source_id}")
    module.__file__ = f"/tmp/legacy_ffd_{source_id}.py"
    exec(compile(legacy_source(source_id), f"legacy-ffd-{source_id}.py", "exec"), module.__dict__)
    return module
