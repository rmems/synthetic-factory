#!/usr/bin/env python3
"""Verify r18 diagnosis handoff hashes without loading rejected JSON.

Reads diagnosis-handoff-receipt-r18.json and hashes diagnosis-*.md plus
rejected-*.json as raw bytes. Never json-loads rejected scratch. Prints
only names, byte counts, SHA-256, and match/mismatch. Exit 0 on match.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROUND_TAG = "r18"
DEFAULT_STAGE = Path("/tmp/ffpc-r18")
RECEIPT_NAME = f"diagnosis-handoff-receipt-{ROUND_TAG}.json"
DIAGNOSIS_NAMES = [
    f"diagnosis-01-{ROUND_TAG}.md",
    f"diagnosis-02-{ROUND_TAG}.md",
    f"diagnosis-03-{ROUND_TAG}.md",
]
REJECTED_NAMES = [
    f"rejected-01-{ROUND_TAG}.json",
    f"rejected-02-{ROUND_TAG}.json",
    f"rejected-03-{ROUND_TAG}.json",
]


def digest(path: Path) -> tuple[int, str]:
    data = path.read_bytes()
    return len(data), hashlib.sha256(data).hexdigest()


def index_receipt_files(receipt: dict) -> dict[str, dict]:
    rows = {}
    for group in ("files", "diagnosis_files", "rejected_files"):
        for row in receipt.get(group) or []:
            name = row.get("name")
            if isinstance(name, str) and name:
                rows.setdefault(name, row)
    return rows


def main() -> int:
    stage = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_STAGE
    receipt_path = stage / RECEIPT_NAME
    if not receipt_path.is_file():
        print(f"MISSING {receipt_path}")
        return 1
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    if receipt.get("round") not in (18, "18"):
        print(f"FAIL receipt.round={receipt.get('round')!r} expected 18")
        return 1
    if receipt.get("isolation") != "two-session":
        print(f"FAIL receipt.isolation={receipt.get('isolation')!r}")
        return 1
    indexed = index_receipt_files(receipt)
    ok = True
    print(f"RECEIPT {receipt_path.name} bytes={receipt_path.stat().st_size}")
    print(f"kind={receipt.get('kind')} session={receipt.get('session')} isolation={receipt.get('isolation')}")
    for name in DIAGNOSIS_NAMES + REJECTED_NAMES:
        path = stage / name
        if not path.is_file() or path.is_symlink():
            print(f"MISSING {name}")
            ok = False
            continue
        nbytes, sha = digest(path)
        expected = indexed.get(name)
        if expected is None:
            print(f"UNDECLARED {name} bytes={nbytes} sha256={sha}")
            ok = False
            continue
        exp_bytes = expected.get("bytes")
        exp_sha = expected.get("sha256")
        match = exp_bytes == nbytes and exp_sha == sha
        if not match:
            ok = False
        print(
            f"{'MATCH' if match else 'MISMATCH'} {name} "
            f"bytes={nbytes} expected_bytes={exp_bytes} "
            f"sha256={sha} expected_sha256={exp_sha}"
        )
    print("VERIFY_OK" if ok else "VERIFY_FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
