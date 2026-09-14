#!/usr/bin/env python3
"""frontier → reserve --expected 2 → mill → publish CST r1446+ until catalog.

Hop back to db-migration-repair-factory if it becomes unreserved.
Never steal. Never hop to sandbox-refusal if reserved/writing.
"""
from __future__ import annotations

import json
import subprocess
import sys
import time
from importlib.machinery import SourceFileLoader
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
FACTORY = REPO / "outputs/raw/2026-08-19-agentic/cache-stampede-factory"
DBM = REPO / "outputs/raw/2026-08-19-agentic/db-migration-repair-factory"
AGENTIC = FACTORY.parent
MILL_PATH = REPO / "experiments/cst-mill-r2310.py"
MILL = SourceFileLoader("cstmill2310", str(MILL_PATH)).load_module()
TXN = [sys.executable, str(REPO / "pipelines/round_txn.py")]
NEVER = {"sandbox-refusal-factory", "eval-harness-trajectory-factory"}
STOP = REPO / "FACTORY_STOP"


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
    if args[0] not in {"frontier"}:
        print(proc.stdout, flush=True)
    return json.loads(proc.stdout[proc.stdout.find("{") :])


def reserved(factory: Path, n: int) -> bool:
    return (factory / f"ROUND-r{n:02d}.reserved.json").exists()


def writing(factory: Path) -> bool:
    return bool(
        list(factory.glob("ROUND-r*.reserved.json"))
        or list(factory.glob("ROUND-r*.publishing.json"))
    )


def main() -> int:
    published: list[int] = []
    last = MILL.CATALOG_FIRST + len(MILL.PAIRS) - 1
    hops = 0
    while True:
        if STOP.exists():
            print("FACTORY_STOP", flush=True)
            break
        dbm_n = int(txn("frontier", str(DBM))["next_round"])
        if not reserved(DBM, dbm_n) and not writing(DBM):
            print(json.dumps({"stop": "dbm_unreserved", "dbm_next": dbm_n, "published": published}), flush=True)
            return 8
        status = txn("frontier", str(FACTORY))
        nxt = int(status["next_round"])
        if reserved(FACTORY, nxt) or writing(FACTORY):
            hops += 1
            print(f"cst r{nxt} reserved; retry {hops}", flush=True)
            time.sleep(3)
            if hops > 40:
                return 2
            continue
        if nxt > last:
            print(json.dumps({"stop": "catalog_exhausted", "next_round": nxt, "last": last, "published": published}), flush=True)
            return 0
        if nxt < MILL.CATALOG_FIRST:
            print(f"frontier {nxt} before catalog {MILL.CATALOG_FIRST}", flush=True)
            return 7
        try:
            payload = txn("reserve", str(FACTORY), "--round", str(nxt), "--expected", "2")
        except RuntimeError as exc:
            if reserved(FACTORY, nxt):
                hops += 1
                print(f"reserve race r{nxt}; retry {hops}: {exc}", flush=True)
                time.sleep(3)
                continue
            print(json.dumps({"stop": "reserve_failed", "round": nxt, "err": str(exc)[-2000:]}), flush=True)
            return 5
        token = payload["token"]
        stage = Path(payload["staging_dir"])
        print(f"RESERVED r{nxt} {token[:8]} {stage}", flush=True)
        try:
            ids = MILL.write_round(nxt, stage)
            print(json.dumps({"milled": nxt, "ids": ids}), flush=True)
            txn("publish", str(FACTORY), "--round", str(nxt), "--token", token)
        except Exception as exc:
            try:
                txn("abort", str(FACTORY), "--round", str(nxt), "--token", token)
            except RuntimeError as abort_exc:
                print(f"abort r{nxt} failed: {abort_exc}", flush=True)
            print(json.dumps({"stop": "mill_or_publish_failed", "round": nxt, "err": str(exc)[-4000:]}), flush=True)
            return 6
        published.append(nxt)
        print(f"published r{nxt} ({len(published)})", flush=True)
    print(json.dumps({"published": published, "hops": hops}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
