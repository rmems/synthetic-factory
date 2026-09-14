#!/usr/bin/env python3
"""frontier → reserve --expected 2 → unique leftover leftover leftover leftover mill → publish.

Never steal reserved seats. Never rewrite outputs/raw.
If NTP is reserved, hop-wait (do not steal) and retry the unreserved frontier.
Never hop into sandbox-refusal when it is reserved or writing.
"""
from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path("/home/raulmc/rmems/synthetic-factory")
AGENTIC = ROOT / "outputs/raw/2026-08-19-agentic"
DIR = AGENTIC / "notebook-to-pipeline-factory"
TXN = ["python3", str(ROOT / "pipelines/round_txn.py")]
GEN = ["python3", str(ROOT / "experiments/ntp-mill-unique-llll.py")]
MAX_SECONDS = 6 * 60 * 60
TARGET_ROUNDS = 32
NEVER_HOP = {"sandbox-refusal-factory"}


def run(args: list[str], timeout: int = 300) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=str(ROOT), capture_output=True, text=True, timeout=timeout)


def reserved_here(path: Path) -> list[Path]:
    return sorted(path.glob("ROUND-r*.reserved.json"))


def writing_here(path: Path) -> bool:
    return bool(list(path.glob(".txn*")) or list(path.glob("ROUND-r*.reserved.json")))


def main() -> int:
    t0 = time.time()
    published: list[int] = []
    ids: list[str] = []
    consecutive_fail = 0
    while time.time() - t0 < MAX_SECONDS and len(published) < TARGET_ROUNDS and consecutive_fail < 12:
        leftover = reserved_here(DIR)
        if leftover:
            print(f"HOP reserved {leftover[0].name} — never steal NTP", flush=True)
            hops = [
                p
                for p in sorted(AGENTIC.iterdir())
                if p.is_dir()
                and p.name not in NEVER_HOP
                and p.name != DIR.name
                and not writing_here(p)
            ]
            if hops:
                print(f"HOP candidate {hops[0].name} (NTP reserved; staying on NTP mill)", flush=True)
            time.sleep(0.08)
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
    return 0 if published else 1


if __name__ == "__main__":
    raise SystemExit(main())
