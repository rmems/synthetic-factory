#!/usr/bin/env python3
"""frontier → reserve --expected 2 → mill → publish queue-backpressure r94+."""
from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path
from importlib.machinery import SourceFileLoader

REPO = Path(__file__).resolve().parents[1]
FACTORY = REPO / "outputs/raw/2026-08-19-agentic/queue-backpressure-factory"
MILL_PATH = REPO / "experiments/qbp-mill-r94.py"
MILL = SourceFileLoader("qbpmill_r94", str(MILL_PATH)).load_module()
TXN = [sys.executable, str(REPO / "pipelines/round_txn.py")]


def txn(*args: str) -> dict:
    proc = subprocess.run(
        TXN + list(args), cwd=REPO, text=True, capture_output=True, check=False
    )
    if proc.returncode != 0:
        raise RuntimeError(
            f"round_txn {' '.join(args)} failed ({proc.returncode}): "
            f"{(proc.stderr or '').strip()}\n{(proc.stdout or '').strip()}"
        )
    print(proc.stdout, flush=True)
    return json.loads(proc.stdout)


def reserved(factory: Path, n: int) -> bool:
    return (factory / f"ROUND-r{n:02d}.reserved.json").exists()


def main() -> int:
    want = int(sys.argv[1]) if len(sys.argv) > 1 else len(MILL.PAIRS)
    published: list[int] = []
    last = MILL.CATALOG_FIRST + len(MILL.PAIRS) - 1
    fails = 0
    while len(published) < want:
        status = txn("frontier", str(FACTORY))
        nxt = int(status["next_round"])
        if reserved(FACTORY, nxt):
            print(f"RESERVED r{nxt}; never steal", flush=True)
            fails += 1
            if fails > 12:
                break
            time.sleep(2)
            continue
        if nxt < MILL.CATALOG_FIRST:
            print(f"frontier {nxt} before catalog {MILL.CATALOG_FIRST}", flush=True)
            return 7
        if nxt > last:
            print(f"catalog exhausted at frontier {nxt} (last={last})", flush=True)
            break
        try:
            payload = txn("reserve", str(FACTORY), "--round", str(nxt), "--expected", "2")
        except RuntimeError as exc:
            print(f"reserve race r{nxt}: {exc}", flush=True)
            fails += 1
            if fails > 8:
                break
            time.sleep(1)
            continue
        fails = 0
        token = payload["token"]
        stage = Path(payload["staging_dir"])
        print(f"reserved r{nxt} token={token}", flush=True)
        mill = subprocess.run(
            [sys.executable, str(MILL_PATH), "--round", str(nxt), "--staging", str(stage)],
            cwd=REPO, text=True, capture_output=True, check=False,
        )
        print(mill.stdout, flush=True)
        if mill.returncode != 0:
            print(mill.stderr, flush=True)
            txn("abort", str(FACTORY), "--round", str(nxt), "--token", token)
            return 6
        txn("publish", str(FACTORY), "--round", str(nxt), "--token", token)
        published.append(nxt)
        print(f"published r{nxt} ({len(published)}/{want})", flush=True)
    print(json.dumps({"published": len(published), "rounds": published, "frontier": txn("frontier", str(FACTORY))["next_round"]}))
    return 0 if published else 1


if __name__ == "__main__":
    raise SystemExit(main())
