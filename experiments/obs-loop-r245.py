#!/usr/bin/env python3
"""Hop loop: observability-debug-factory until catalog/quota. Never steal kcl."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MILL = ROOT / "experiments" / "obs-mill-r245.py"
TXN = ROOT / "pipelines" / "round_txn.py"
FACTORY = ROOT / "outputs" / "raw" / "2026-08-19-agentic" / "observability-debug-factory"

import importlib.util

_spec = importlib.util.spec_from_file_location("obs_mill_r245", MILL)
_mill = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(_mill)
CATALOG_FIRST = _mill.CATALOG_FIRST
CATALOG_LEN = len(_mill.PAIRS)


def run(args, check=True):
    print("+", " ".join(str(a) for a in args), flush=True)
    return subprocess.run([str(a) for a in args], cwd=ROOT, check=check, text=True, capture_output=True)


def frontier(factory: Path) -> int:
    proc = run([sys.executable, str(TXN), "frontier", str(factory)])
    print(proc.stdout, flush=True)
    return json.loads(proc.stdout)["next_round"]


def reserved(factory: Path, n: int) -> bool:
    return (factory / f"ROUND-r{n:02d}.reserved.json").exists()


def publish_one(n: int) -> None:
    proc = run([sys.executable, str(TXN), "reserve", str(FACTORY), "--round", str(n), "--expected", "2"])
    payload = json.loads(proc.stdout)
    print(proc.stdout, flush=True)
    token = payload["token"]
    staging = payload["staging_dir"]
    run([sys.executable, str(MILL), "--round", str(n), "--staging", staging])
    pub = run([sys.executable, str(TXN), "publish", str(FACTORY), "--round", str(n), "--token", token])
    print(pub.stdout, flush=True)


def main() -> int:
    published = []
    hops = 0
    print(f"obs hop loop catalog={CATALOG_LEN} first={CATALOG_FIRST}", flush=True)
    while True:
        n = frontier(FACTORY)
        last = CATALOG_FIRST + CATALOG_LEN - 1
        if n > last:
            print(f"catalog exhausted at frontier {n} (last={last})", flush=True)
            break
        if reserved(FACTORY, n):
            print(f"obs r{n} reserved; hop/stop without steal", flush=True)
            hops += 1
            if hops >= 3:
                return 2
            continue
        try:
            publish_one(n)
        except subprocess.CalledProcessError as exc:
            print(exc.stdout or "", exc.stderr or "", flush=True)
            print("reserve/publish failed; stop without steal", flush=True)
            return 0 if published else 2
        published.append(n)
        print(f"LOOP published r{n}", flush=True)
    print(f"DONE published={published} hops={hops}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
