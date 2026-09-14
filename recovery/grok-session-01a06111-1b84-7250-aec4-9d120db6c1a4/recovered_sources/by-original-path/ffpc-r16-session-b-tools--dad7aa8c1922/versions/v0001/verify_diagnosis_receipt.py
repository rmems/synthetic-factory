#!/usr/bin/env python3
"""Verify diagnosis files against the handoff receipt. Never open rejected JSON."""
from __future__ import annotations
import hashlib, json, sys
from pathlib import Path

STAGE = Path(sys.argv[1] if len(sys.argv) > 1 else "/tmp/ffpc-r16")
ROUND = 16
RECEIPT = STAGE / f"diagnosis-handoff-receipt-r{ROUND:02d}.json"
if not RECEIPT.is_file():
    raise SystemExit(f"missing receipt {RECEIPT}")
doc = json.loads(RECEIPT.read_text(encoding="utf-8"))
print(f"receipt_keys={sorted(doc)}")
print(f"receipt_round={doc.get('round')} kind={doc.get('kind')} version={doc.get('version')}")

# Collect diagnosis entries only.
entries = []
if isinstance(doc.get("diagnosis_files"), list):
    entries = list(doc["diagnosis_files"])
elif isinstance(doc.get("files"), list):
    entries = [e for e in doc["files"] if str(e.get("name","")).startswith("diagnosis-")]
else:
    raise SystemExit("receipt has no diagnosis_files/files")

expected = [f"diagnosis-{i:02d}-r{ROUND:02d}.md" for i in range(1,4)]
names = [e.get("name") for e in entries]
print("receipt_diagnosis_names", names)
if names != expected and set(names) != set(expected):
    print("WARNING name set mismatch vs expected", expected)

ok = True
for e in entries:
    name = e.get("name")
    if not isinstance(name, str) or not name.startswith("diagnosis-") or name.endswith(".json"):
        print(f"SKIP non-diagnosis entry {name!r}")
        continue
    path = STAGE / name
    if not path.is_file() or path.is_symlink():
        print(f"FAIL missing {name}")
        ok = False
        continue
    data = path.read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    want_b = e.get("bytes")
    want_h = e.get("sha256")
    match_b = (want_b == len(data))
    match_h = (want_h == digest)
    print(f"{name} bytes={len(data)} sha256={digest} bytes_ok={match_b} sha_ok={match_h}")
    if not match_b or not match_h:
        ok = False
        print(f"  expected bytes={want_b} sha256={want_h}")
if not ok:
    raise SystemExit("RECEIPT_MISMATCH")
print("RECEIPT_OK diagnosis files only")
