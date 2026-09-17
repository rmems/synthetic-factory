"""Synthetic ACTF fixture. Not a recovered mill. AST-scan only."""

from __future__ import annotations

import subprocess
from pathlib import Path

FACTORY = "agentic-coding-trajectory-factory"


def ep1() -> dict[str, str]:
    return {"factory": FACTORY, "id": "actf-fixture-001"}


def build_batch(out_dir: Path) -> Path:
    target = out_dir / "batch-r10.jsonl"
    target.write_text('{"id":"actf-fixture-001"}\n', encoding="utf-8")
    return target


def main() -> None:
    build_batch(Path("/tmp/actf-fixture"))
    subprocess.run(["true"], check=False)
