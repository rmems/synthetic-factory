#!/usr/bin/env python3
"""Reserve → mill → publish browser-tool-use-factory until catalog or quota dies."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path("/home/raulmc/rmems/synthetic-factory")
DIR = ROOT / "outputs/raw/2026-08-19-agentic/browser-tool-use-factory"
TXN = [sys.executable, str(ROOT / "pipelines/round_txn.py")]
MILL_PATH = ROOT / "experiments/brw-mill-r212.py"
MILL = [sys.executable, str(MILL_PATH)]


def run(cmd: list[str]) -> tuple[int, str]:
    p = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    return p.returncode, (p.stdout or "") + (p.stderr or "")


def frontier() -> int:
    rc, out = run(TXN + ["frontier", str(DIR)])
    if rc != 0:
        raise SystemExit(f"frontier failed:\n{out}")
    return json.loads(out[out.find("{") :])["next_round"]


def catalog_last() -> int:
    ns: dict = {}
    exec(MILL_PATH.read_text(), ns)
    return ns["CATALOG_FIRST"] + len(ns["PAIRS"]) - 1


def main() -> int:
    published: list[int] = []
    while True:
        nxt = frontier()
        last = catalog_last()
        if nxt > last:
            print(json.dumps({"stop": "catalog_exhausted", "next_round": nxt, "published": published}))
            return 0
        rc, out = run(TXN + ["reserve", str(DIR), "--round", str(nxt), "--expected", "2"])
        if rc != 0:
            print(json.dumps({"stop": "reserve_failed", "round": nxt, "out": out[-2000:], "published": published}))
            return 2
        payload = json.loads(out[out.find("{") :])
        token = payload["token"]
        stage = payload["staging_dir"]
        print(f"RESERVED r{nxt} {token[:8]} {stage}", flush=True)
        rc, mout = run(MILL + ["--round", str(nxt), "--out", stage])
        if rc != 0:
            run(TXN + ["abort", str(DIR), "--round", str(nxt), "--token", token])
            print(json.dumps({"stop": "mill_failed", "round": nxt, "out": mout[-2000:], "published": published}))
            return 3
        print(mout.strip(), flush=True)
        rc, pout = run(TXN + ["publish", str(DIR), "--round", str(nxt), "--token", token])
        if rc != 0:
            print(json.dumps({"stop": "publish_failed", "round": nxt, "out": pout[-4000:], "published": published}))
            return 4
        published.append(nxt)
        print(f"PUBLISHED r{nxt}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
