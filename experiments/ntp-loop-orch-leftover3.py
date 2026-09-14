#!/usr/bin/env python3
"""frontier → reserve --expected 2 → orch leftover leftover leftover mill → publish.

Hop never steal. Never rewrite outputs/raw.
"""
from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path("/home/raulmc/rmems/synthetic-factory")
DIR = ROOT / "outputs/raw/2026-08-19-agentic/notebook-to-pipeline-factory"
TXN = ["python3", str(ROOT / "pipelines/round_txn.py")]
GEN = ["python3", str(ROOT / "experiments/ntp-mill-orch-leftover3.py")]
MAX_SECONDS = 40 * 60
TARGET_ROUNDS = 16


def run(args: list[str], timeout: int = 300) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=str(ROOT), capture_output=True, text=True, timeout=timeout)


def reserved_here() -> list[Path]:
    return sorted(DIR.glob("ROUND-r*.reserved.json"))


def main() -> int:
    t0 = time.time()
    published: list[int] = []
    ids: list[str] = []
    consecutive_fail = 0
    while time.time() - t0 < MAX_SECONDS and len(published) < TARGET_ROUNDS and consecutive_fail < 12:
        leftover = reserved_here()
        if leftover:
            print(f"HOP reserved {leftover[0].name} — never steal", flush=True)
            time.sleep(0.4)
            continue
        fr = run(TXN + ["frontier", str(DIR)], timeout=60)
        if fr.returncode != 0:
            consecutive_fail += 1
            print(f"FRONTIER_FAIL {(fr.stderr or fr.stdout)[-300:]}", flush=True)
            time.sleep(0.3)
            continue
        try:
            n = int(json.loads(fr.stdout)["next_round"])
        except (json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
            consecutive_fail += 1
            print(f"FRONTIER_PARSE {exc}", flush=True)
            time.sleep(0.3)
            continue
        rsv = run(TXN + ["reserve", str(DIR), "--round", str(n), "--expected", "2"], timeout=60)
        if rsv.returncode != 0:
            msg = (rsv.stderr or rsv.stdout)[-600:]
            consecutive_fail += 1
            print(f"RESERVE_FAIL r{n}\n{msg}", flush=True)
            if any(tok in msg.lower() for tok in ("already", "reserved", "not the frontier", "exists")):
                print("HOP — never steal", flush=True)
            time.sleep(0.25)
            continue
        try:
            payload = json.loads(rsv.stdout)
        except json.JSONDecodeError:
            consecutive_fail += 1
            print("RESERVE_JSON_FAIL", flush=True)
            time.sleep(0.3)
            continue
        token = payload["token"]
        staging = payload["staging_dir"]
        mill = run(GEN + [str(n), staging], timeout=60)
        if mill.returncode != 0:
            consecutive_fail += 1
            print(f"MILL_FAIL r{n}\n{(mill.stderr or mill.stdout)[-800:]}", flush=True)
            abort = run(TXN + ["abort", str(DIR), "--round", str(n), "--token", token], timeout=60)
            print(f"ABORT r{n} rc={abort.returncode}", flush=True)
            time.sleep(0.3)
            continue
        print(mill.stdout.strip(), flush=True)
        ids.append(mill.stdout.strip())
        pub = run(TXN + ["publish", str(DIR), "--round", str(n), "--token", token], timeout=300)
        if pub.returncode != 0:
            consecutive_fail += 1
            print(f"PUBLISH_FAIL r{n}\n{(pub.stderr or pub.stdout)[-800:]}", flush=True)
            time.sleep(0.3)
            continue
        published.append(n)
        consecutive_fail = 0
        print(f"PUBLISHED r{n} count={len(published)} {(pub.stdout or '')[-200:]}", flush=True)
    print(json.dumps({"published": published, "ids": ids, "elapsed": round(time.time() - t0)}, indent=2))
    return 0 if len(published) >= TARGET_ROUNDS else 1


if __name__ == "__main__":
    raise SystemExit(main())
