#!/usr/bin/env python3
"""sandbox-refusal leftover leftover leftover mill from frontier (r1268+).

16 rounds × Q=3. Catalog plants in experiments/sbox-mill-r359.py leftover16+.
BAN leftover leftover leftover search leftover leftover leftover plants, r01–r190 sock mill.
IDs sbox-rNNNN-<slug>. Staging only. Never rewrite raw. Never steal.
"""
from __future__ import annotations

import json
import subprocess
import sys
import time
from importlib.machinery import SourceFileLoader
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FACTORY = ROOT / "outputs/raw/2026-08-19-agentic/sandbox-refusal-factory"
MILL = SourceFileLoader(
    "sboxmill", str(ROOT / "experiments/sbox-mill-r359.py")
).load_module()
N_ROUNDS = 16
TXN = [sys.executable, str(ROOT / "pipelines/round_txn.py")]


def txn(*args: str) -> dict:
    proc = subprocess.run(
        TXN + list(args), cwd=ROOT, text=True, capture_output=True, check=False
    )
    if proc.returncode != 0:
        raise RuntimeError(
            f"round_txn {' '.join(args)} failed ({proc.returncode}): {proc.stderr.strip()}"
        )
    return json.loads(proc.stdout)


def publish_one(rnd: int, write_notes: bool) -> dict:
    rsv = txn("reserve", str(FACTORY), "--round", str(rnd), "--expected", "3")
    staging = Path(rsv["staging_dir"])
    token = rsv["token"]
    recs, notes = MILL.build_round(rnd)
    (staging / f"batch-r{rnd}.jsonl").write_text(
        "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in recs)
    )
    if write_notes:
        (staging / f"NOTES-r{rnd}.md").write_text(notes)
    pub = txn("publish", str(FACTORY), "--round", str(rnd), "--token", token)
    return {
        "round": rnd,
        "family": MILL.plant_for_round(rnd)["family"],
        "ids": [r["id"] for r in recs],
        "publish": pub,
    }


def main() -> int:
    published: list[dict] = []
    tries = 0
    while len(published) < N_ROUNDS:
        tries += 1
        if tries > 80:
            raise SystemExit(f"gave up published={len(published)}")
        fr = txn("frontier", str(FACTORY))
        rnd = int(fr["next_round"])
        reserved = sorted(FACTORY.glob("ROUND-r*.reserved.json"))
        if reserved:
            print(f"RESERVED {reserved[0].name}; wait unreserved", file=sys.stderr)
            time.sleep(0.35)
            continue
        last = MILL.FIRST + len(MILL.PLANTS) - 1
        if rnd > last:
            print(f"catalog exhausted r{rnd} last={last}", file=sys.stderr)
            return 1
        fam = MILL.plant_for_round(rnd)["family"]
        if "search" in fam.lower():
            print(f"BAN search plant {fam} r{rnd}", file=sys.stderr)
            return 1
        try:
            row = publish_one(rnd, True)
        except RuntimeError as exc:
            print("reserve fail", rnd, exc, file=sys.stderr)
            time.sleep(0.25)
            continue
        published.append(row)
        print(json.dumps(row, indent=2), flush=True)
    print(json.dumps({"published": published, "n": len(published)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
