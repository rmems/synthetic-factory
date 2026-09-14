#!/usr/bin/env python3
"""Mill authz-regression-factory r1285+ unique leftover object-id IDOR / BFLA.

Catalog lives in azr-plants-r1285.py and is also appended on azr-mill-r1205.
This mill indexes that slice at CATALOG_FIRST=1285.

Not leftover mill cartesian. Not JWT-claim catalog. Not r200–r1284 vesselNNNN-sys.
Not clones of r1181–r1284 (no snomed-concept-idor / emmett-pipeline-skip-delete).
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

FACTORY = "authz-regression-factory"
GEN = "grok-4.6"
CATALOG_FIRST = 1285
EXPERIMENTS = Path(__file__).resolve().parent

_spec = importlib.util.spec_from_file_location(
    "azr_mill_r1205_for_r1285", EXPERIMENTS / "azr-mill-r1205.py"
)
_r1205 = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(_r1205)

# mill r1205 CATALOG_FIRST=1205; plants r1285 occupy index 80..159 (r1285..r1364)
_OFFSET = CATALOG_FIRST - _r1205.CATALOG_FIRST
PAIRS = _r1205.PAIRS[_OFFSET:]
if not PAIRS:
    raise SystemExit("r1285 catalog slice empty")
if PAIRS[0][0]["slug"] != "icd10-dx-idor":
    raise SystemExit(f"unexpected r1285 tip slug {PAIRS[0][0]['slug']}")
if PAIRS[0][1]["slug"] != "litestar-skip-guard-delete":
    raise SystemExit(f"unexpected r1285 bfla slug {PAIRS[0][1]['slug']}")

build_success = _r1205.build_success
build_handoff = _r1205.build_handoff
notes_for = _r1205.notes_for


def generate_round(round_n: int) -> tuple[list[dict], str]:
    idx = round_n - CATALOG_FIRST
    if idx < 0 or idx >= len(PAIRS):
        raise SystemExit(
            f"no catalog pair for round {round_n} (have {CATALOG_FIRST}..{CATALOG_FIRST + len(PAIRS) - 1})"
        )
    sa, sb = PAIRS[idx]
    a = build_success(round_n, sa)
    b = build_handoff(round_n, sb)
    return [a, b], notes_for(round_n, a, b, sa, sb)


def write_round(round_n: int, staging: Path) -> None:
    eps, notes = generate_round(round_n)
    batch = staging / f"batch-r{round_n:02d}.jsonl"
    nfile = staging / f"NOTES-r{round_n:02d}.md"
    with batch.open("w") as fh:
        for ep in eps:
            fh.write(json.dumps(ep, ensure_ascii=True) + "\n")
    nfile.write_text(notes)
    print(
        json.dumps(
            {
                "round": round_n,
                "ids": [e["id"] for e in eps],
                "steps": [len(e["steps"]) for e in eps],
                "success": [e["reward"]["success"] for e in eps],
                "batch": str(batch),
                "notes": str(nfile),
            }
        )
    )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--round", type=int, required=True)
    ap.add_argument("--staging", required=True)
    args = ap.parse_args()
    write_round(args.round, Path(args.staging))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
