#!/usr/bin/env python3
"""frontier → reserve --expected 2 → mill → publish. Never steal. Loop until catalog/quota dies."""
from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

from importlib.machinery import SourceFileLoader

REPO = Path(__file__).resolve().parents[1]
FACTORY = REPO / "outputs/raw/2026-08-19-agentic/agent-memory-compaction-factory"
AGENTIC = FACTORY.parent
MILL_PATH = REPO / "experiments/amc-mill-r424.py"
MILL = SourceFileLoader("amcmill424", str(MILL_PATH)).load_module()
TXN = [sys.executable, str(REPO / "pipelines/round_txn.py")]
SKIP_HOP = {"sandbox-refusal-factory", "eval-harness-trajectory-factory"}


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


def hop_scan() -> list[dict]:
    found: list[dict] = []
    for hop in sorted(AGENTIC.iterdir()):
        if not hop.is_dir() or hop.name in SKIP_HOP or hop == FACTORY:
            continue
        if reserved(hop, 1) and (hop / "ROUND-r01.reserved.json").exists():
            pass
        try:
            hop_st = txn("frontier", str(hop))
        except RuntimeError as exc:
            print(f"hop frontier {hop.name} failed: {exc}", flush=True)
            continue
        hn = int(hop_st["next_round"])
        if reserved(hop, hn):
            print(f"{hop.name} r{hn} reserved; skip", flush=True)
            continue
        writing = list(hop.glob("ROUND-r*.reserved.json")) or list(hop.glob("ROUND-r*.publishing.json"))
        if writing:
            print(f"{hop.name} writing { [p.name for p in writing] }; skip", flush=True)
            continue
        row = {"hop": hop.name, "next_round": hn, "unreserved": True}
        found.append(row)
        print(json.dumps(row), flush=True)
        if len(found) >= 3:
            break
    return found


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
    # Keep going until quota/catalog dies; do not stop after one batch.
    deadline = time.monotonic() + 8 * 60 * 60
    consecutive_reserve_fail = 0
    while len(published) < want and time.monotonic() < deadline:
        status = txn("frontier", str(FACTORY))
        nxt = int(status["next_round"])
        if reserved(FACTORY, nxt):
            print(f"RESERVED r{nxt}; never steal; hop scan", flush=True)
            hops = hop_scan()
            print(json.dumps({"amc_reserved": nxt, "hops": hops}), flush=True)
            time.sleep(2)
            consecutive_reserve_fail += 1
            if consecutive_reserve_fail > 30:
                print("AMC reserved too long; stop so operator can hop-mill", flush=True)
                break
            continue
        if nxt > last:
            print(f"catalog exhausted at frontier {nxt} (last={last})", flush=True)
            break
        try:
            payload = txn(
                "reserve",
                str(FACTORY),
                "--round",
                str(nxt),
                "--expected",
                "2",
            )
        except RuntimeError as exc:
            print(f"reserve race r{nxt}: {exc}", flush=True)
            consecutive_reserve_fail += 1
            if consecutive_reserve_fail > 8:
                print("repeated reserve failure (quota or race); stop", flush=True)
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
                "ids": [p["ids"] for p in published],
                "frontier": txn("frontier", str(FACTORY))["next_round"],
                "catalog_last": last,
            },
            indent=2,
        )
    )
    return 0 if published else 1


if __name__ == "__main__":
    raise SystemExit(main())
