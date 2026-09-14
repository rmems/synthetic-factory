#!/usr/bin/env python3
"""frontier → reserve --expected 2 → mill → publish queue-backpressure r74+."""
from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path
from importlib.machinery import SourceFileLoader

REPO = Path(__file__).resolve().parents[1]
FACTORY = REPO / "outputs/raw/2026-08-19-agentic/queue-backpressure-factory"
AGENTIC = FACTORY.parent
MILL_PATH = REPO / "experiments/qbp-mill-r74.py"
MILL = SourceFileLoader("qbpmill_r74", str(MILL_PATH)).load_module()
TXN = [sys.executable, str(REPO / "pipelines/round_txn.py")]
SKIP_HOP = {"sandbox-refusal-factory"}


def txn(*args: str) -> dict:
    proc = subprocess.run(
        TXN + list(args),
        cwd=REPO,
        text=True,
        capture_output=True,
        check=False,
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


def mill_round(nxt: int, stage: Path) -> None:
    mill_proc = subprocess.run(
        [sys.executable, str(MILL_PATH), "--round", str(nxt), "--staging", str(stage)],
        cwd=REPO,
        text=True,
        capture_output=True,
        check=False,
    )
    sys.stderr.write(mill_proc.stderr or "")
    print(mill_proc.stdout, flush=True)
    if mill_proc.returncode != 0:
        raise RuntimeError(f"mill failed for r{nxt}: {mill_proc.stderr or mill_proc.stdout}")


def main() -> int:
    want = int(sys.argv[1]) if len(sys.argv) > 1 else len(MILL.PAIRS)
    published: list[dict] = []
    last = MILL.CATALOG_FIRST + len(MILL.PAIRS) - 1
    deadline = time.monotonic() + 8 * 60 * 60
    consecutive_reserve_fail = 0
    while len(published) < want and time.monotonic() < deadline:
        status = txn("frontier", str(FACTORY))
        nxt = int(status["next_round"])
        if reserved(FACTORY, nxt):
            print(f"RESERVED r{nxt}; never steal", flush=True)
            consecutive_reserve_fail += 1
            if consecutive_reserve_fail > 40:
                print("qbp reserved too long; stop", flush=True)
                break
            time.sleep(3)
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
            consecutive_reserve_fail += 1
            if consecutive_reserve_fail > 8:
                print("repeated reserve failure; stop", flush=True)
                break
            time.sleep(1)
            continue
        consecutive_reserve_fail = 0
        stage = Path(payload["staging_dir"])
        token = payload["token"]
        print(f"reserved r{nxt} token={token} stage={stage}", flush=True)
        try:
            mill_round(nxt, stage)
        except Exception as exc:
            print(f"mill failed r{nxt}: {exc}; abort reservation", flush=True)
            try:
                txn("abort", str(FACTORY), "--round", str(nxt), "--token", token)
            except RuntimeError as abort_exc:
                print(f"abort r{nxt} failed: {abort_exc}", flush=True)
                return 1
            consecutive_reserve_fail += 1
            if consecutive_reserve_fail > 3:
                raise
            continue
        pub = txn("publish", str(FACTORY), "--round", str(nxt), "--token", token)
        ids = [
            json.loads(line)["id"]
            for line in (FACTORY / f"batch-r{nxt:02d}.jsonl").read_text().splitlines()
            if line.strip()
        ]
        row = {"round": nxt, "ids": ids, "records": pub["records"]}
        published.append(row)
        print(json.dumps(row), flush=True)
    print(
        json.dumps(
            {
                "published": len(published),
                "rounds": [p["round"] for p in published],
                "frontier": txn("frontier", str(FACTORY))["next_round"],
                "catalog_last": last,
            }
        )
    )
    return 0 if published else 1


if __name__ == "__main__":
    raise SystemExit(main())
