#!/usr/bin/env python3
"""Prefer DPR leftover mill; hop LRD leftover3b when reserved. Never steal."""
from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

REPO = Path("/home/raulmc/rmems/synthetic-factory")
TXN = REPO / "pipelines/round_txn.py"
DPR_MILL = REPO / "experiments/dpr-mill-leftover3-r2475.py"
LRD_MILL = REPO / "experiments/lrd-mill-leftover3b-r75.py"
DPR = REPO / "outputs/raw/2026-08-19-agentic/data-pipeline-repair-factory"
LRD = REPO / "outputs/raw/2026-08-19-agentic/log-redaction-factory"
TARGET = 8


def run(args, check=True):
    proc = subprocess.run(args, cwd=REPO, capture_output=True, text=True)
    if check and proc.returncode != 0:
        raise RuntimeError(
            f"cmd failed {args}\nstdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"
        )
    return proc


def frontier(factory: Path) -> dict:
    return json.loads(run([sys.executable, str(TXN), "frontier", str(factory)]).stdout)


def reserved_here(factory: Path, rnd: int) -> bool:
    return (factory / f"ROUND-r{rnd:02d}.reserved.json").exists()


def complete_here(factory: Path, rnd: int) -> bool:
    return (factory / f"ROUND-r{rnd:02d}.complete.json").exists()


def reserve(factory: Path, rnd: int) -> dict:
    proc = run(
        [
            sys.executable,
            str(TXN),
            "reserve",
            str(factory),
            "--round",
            str(rnd),
            "--expected",
            "2",
        ],
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr or proc.stdout)
    return json.loads(proc.stdout)


def publish(factory: Path, rnd: int, token: str) -> dict:
    return json.loads(
        run(
            [
                sys.executable,
                str(TXN),
                "publish",
                str(factory),
                "--round",
                str(rnd),
                "--token",
                token,
            ]
        ).stdout
    )


def mill_and_publish(factory: Path, mill: Path, rnd: int) -> dict:
    try:
        res = reserve(factory, rnd)
    except RuntimeError as exc:
        msg = str(exc)
        if "already exists" in msg or "not the frontier" in msg:
            return {"skip": rnd, "reason": msg.splitlines()[-1][:200]}
        raise
    token = res["token"]
    staging = Path(res["staging_dir"])
    try:
        mill_out = run(
            [sys.executable, str(mill), "--round", str(rnd), "--staging", str(staging)]
        )
        mill_info = json.loads(mill_out.stdout)
        pub = publish(factory, rnd, token)
    except Exception as exc:
        run(
            [
                sys.executable,
                str(TXN),
                "abort",
                str(factory),
                "--round",
                str(rnd),
                "--token",
                token,
            ],
            check=False,
        )
        err = str(exc)
        if "no unused leftover" in err:
            return {"exhausted": factory.name, "round": rnd, "error": err[-200:]}
        raise RuntimeError(err[:600]) from exc
    return {
        "factory": factory.name,
        "round": rnd,
        "ids": mill_info["ids"],
        "records": pub.get("records"),
    }


def main():
    published = []
    hops = []
    started = time.time()
    while len(published) < TARGET and (time.time() - started) < 20 * 60:
        dpr = frontier(DPR)
        rnd = dpr["next_round"]
        if not reserved_here(DPR, rnd) and not complete_here(DPR, rnd):
            got = mill_and_publish(DPR, DPR_MILL, rnd)
            if "exhausted" in got:
                print(json.dumps(got), flush=True)
                time.sleep(2)
                continue
            if "skip" in got:
                print(json.dumps(got), flush=True)
                time.sleep(0.4)
                continue
            published.append(got)
            print(json.dumps({"published": got}), flush=True)
            continue
        lr = frontier(LRD)
        lrnd = lr["next_round"]
        if not reserved_here(LRD, lrnd) and not complete_here(LRD, lrnd):
            hops.append({"dpr_reserved": rnd, "lrd_next": lrnd})
            print(json.dumps({"hop": "log-redaction", **hops[-1]}), flush=True)
            got = mill_and_publish(LRD, LRD_MILL, lrnd)
            if "exhausted" in got:
                print(json.dumps(got), flush=True)
                time.sleep(3)
                continue
            if "skip" in got:
                print(json.dumps(got), flush=True)
                time.sleep(0.4)
                continue
            published.append(got)
            print(json.dumps({"published": got}), flush=True)
            continue
        print(json.dumps({"blocked": {"dpr": rnd, "lrd": lrnd}}), flush=True)
        time.sleep(2)
    print(
        json.dumps(
            {
                "done": True,
                "published": published,
                "hops": hops,
                "elapsed_s": int(time.time() - started),
            }
        )
    )


if __name__ == "__main__":
    sys.exit(main() or 0)
