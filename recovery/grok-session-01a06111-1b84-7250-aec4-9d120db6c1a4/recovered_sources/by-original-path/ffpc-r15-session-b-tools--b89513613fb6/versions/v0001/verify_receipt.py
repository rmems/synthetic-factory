#!/usr/bin/env python3
"""Verify diagnosis-handoff-receipt hashes/bytes without loading rejected JSON.

Prints MATCH/MISMATCH for each named file. Never dumps file contents.
Rejected artifacts are hashed as raw bytes only.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

STAGE = Path("/tmp/ffpc-r15")
RECEIPT_NAME = "diagnosis-handoff-receipt-r15.json"
DIAGNOSIS_NAMES = (
    "diagnosis-01-r15.md",
    "diagnosis-02-r15.md",
    "diagnosis-03-r15.md",
)


def digest(path: Path) -> tuple[int, str]:
    data = path.read_bytes()
    return len(data), hashlib.sha256(data).hexdigest()


def entries_from_receipt(receipt: dict) -> list[dict]:
    if isinstance(receipt.get("diagnosis_files"), list) and receipt["diagnosis_files"]:
        rows = list(receipt["diagnosis_files"])
        extra = receipt.get("rejected_files") or []
        if isinstance(extra, list):
            rows.extend(extra)
        elif isinstance(receipt.get("files"), list):
            names = {row.get("name") for row in rows if isinstance(row, dict)}
            for row in receipt["files"]:
                if isinstance(row, dict) and row.get("name") not in names:
                    rows.append(row)
        return rows
    if isinstance(receipt.get("files"), list):
        return list(receipt["files"])
    raise SystemExit("receipt has no diagnosis_files or files list")


def main() -> int:
    receipt_path = STAGE / RECEIPT_NAME
    if not receipt_path.is_file():
        print(f"MISSING {RECEIPT_NAME}")
        return 1
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    round_n = receipt.get("round")
    if round_n not in (15, "15"):
        print(f"FAIL receipt.round={round_n!r} expected 15")
        return 1
    print(
        f"RECEIPT name={RECEIPT_NAME} bytes={receipt_path.stat().st_size} "
        f"sha256={hashlib.sha256(receipt_path.read_bytes()).hexdigest()} "
        f"round={round_n} isolation={receipt.get('isolation')}"
    )
    mismatches = 0
    seen_diag = set()
    for row in entries_from_receipt(receipt):
        name = row.get("name")
        if not isinstance(name, str) or "/" in name or name in {".", ".."}:
            print(f"FAIL bad name {name!r}")
            return 1
        path = STAGE / name
        want_bytes = row.get("bytes")
        want_sha = row.get("sha256")
        role = "diagnosis" if name.startswith("diagnosis-") else (
            "rejected" if name.startswith("rejected-") else "other"
        )
        if not path.is_file():
            print(f"MISSING {role} {name}")
            mismatches += 1
            continue
        got_bytes, got_sha = digest(path)
        byte_ok = got_bytes == want_bytes
        sha_ok = got_sha == want_sha
        verdict = "MATCH" if byte_ok and sha_ok else "MISMATCH"
        if verdict != "MATCH":
            mismatches += 1
        print(
            f"{verdict} {role} {name} "
            f"receipt_bytes={want_bytes} disk_bytes={got_bytes} "
            f"receipt_sha256={want_sha} disk_sha256={got_sha}"
        )
        if role == "diagnosis":
            seen_diag.add(name)
    missing_diag = [name for name in DIAGNOSIS_NAMES if name not in seen_diag]
    if missing_diag:
        print("FAIL receipt omitted " + " ".join(missing_diag))
        mismatches += 1
    if mismatches:
        print(f"RECEIPT_VERIFY_FAIL mismatches={mismatches}")
        return 1
    print("RECEIPT_VERIFY_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
