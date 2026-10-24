"""Shared paths and helpers for VSET validator tests."""

from __future__ import annotations

import json
import subprocess  # nosec B404
import sys
import tempfile
from collections.abc import Iterable
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

__all__ = [
    "ACCEPT",
    "FIXTURES",
    "MANIFEST",
    "PACK",
    "REJECT",
    "child_timeout",
    "cli",
    "codes",
    "load_record",
    "reference_report",
    "vset",
]


def reference_report(
    filename: str, files: dict[str, str], *, tests: Iterable[str] | None = None
):
    with tempfile.TemporaryDirectory() as tmp:
        pack = Path(tmp)
        (pack / "src").mkdir()
        (pack / "tests").mkdir()
        for name, text in files.items():
            target = pack / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(text, encoding="utf-8")
        chosen = [f"tests/{filename}"] if tests is None else list(tests)
        return vset.run_oracle(pack, reference_tests=chosen)


def load_record(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def codes(errors: Iterable[vset.VSetValidationError]) -> list[str]:
    return [item.code for item in errors]


def child_timeout(timeout: float) -> BaseException:
    # The fake child wait raises the same type the oracle catches. Nothing runs.
    return subprocess.TimeoutExpired(cmd="oracle", timeout=timeout)  # nosec B603  # nosemgrep: python.lang.security.audit.dangerous-subprocess-use-audit.dangerous-subprocess-use-audit


def cli(*args: str) -> subprocess.CompletedProcess[str]:
    # argv is this interpreter and the repo's own validator path; `args` are
    # the literal flags the calling test wrote, and no shell is enabled.
    return subprocess.run(  # nosemgrep: python.lang.security.audit.dangerous-subprocess-use-audit.dangerous-subprocess-use-audit  # nosec B603
        [sys.executable, str(VALIDATE), *args],
        cwd=str(REPO),
        capture_output=True,
        text=True,
        check=False,
    )
