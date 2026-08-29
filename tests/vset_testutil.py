"""Shared paths and helpers for VSET validator tests."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PIPELINES = REPO / "pipelines"
FIXTURES = Path(__file__).resolve().parent / "fixtures" / "vset"
PACK = FIXTURES / "repo-pack-counter"
ACCEPT = FIXTURES / "records" / "accept"
REJECT = FIXTURES / "records" / "reject"
MANIFEST = FIXTURES / "manifests" / "pilot-v1.json"
VALIDATE = PIPELINES / "validate_vset.py"

sys.path.insert(0, str(PIPELINES))
import validate_vset as vset  # noqa: E402


def load_record(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def codes(errors) -> list[str]:
    return [item.code for item in errors]


def cli(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(VALIDATE), *args],
        cwd=str(REPO),
        capture_output=True,
        text=True,
    )
