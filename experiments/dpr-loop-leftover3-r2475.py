#!/usr/bin/env python3
"""frontier → reserve --expected 2 → mill → publish. Never steal. Never rewrite raw.

LEFTOVER3_G46_SESSION. Mill path is unique so sibling mills cannot overwrite it.
"""
from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

REPO = Path("/home/raulmc/rmems/synthetic-factory")
TXN = REPO / "pipelines/round_txn.py"
MILL = REPO / "experiments/dpr-mill-leftover3-r2475.py"
DPR = REPO / "outputs/raw/2026-08-19-agentic/data-pipeline-repair-factory"
LR = REPO / "outputs/raw/2026-08-19-agentic/log-redaction-factory"
TARGET = 16


def run(args, check=True):
    proc = subprocess.run(args, cwd=REPO, capture_output=True, text=True)
    if check and proc.returncode != 0:
        raise RuntimeError(
            f"cmd failed {args}\nstdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"
        )
    return proc


def frontier(factory: Path) -> dict:
    proc = run([sys.executable, str(TXN), "frontier", str(factory)])
    return json.loads(proc.stdout)


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
    proc = run(
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
    )
    return json.loads(proc.stdout)


def reserved_here(factory: Path, rnd: int) -> bool:
    return (factory / f"ROUND-r{rnd:02d}.reserved.json").exists()


def main():
    published = []
    hops = []
    started = time.time()
    while len(published) < TARGET and (time.time() - started) < 38 * 60:
        st = frontier(DPR)
        rnd = st["next_round"]
        if reserved_here(DPR, rnd):
            lr = frontier(LR) if LR.is_dir() else None
            if lr and not reserved_here(LR, lr["next_round"]):
                hops.append({"dpr_reserved": rnd, "lr_next": lr["next_round"]})
                print(
                    json.dumps(
                        {"hop": "log-redaction reserved seat; skip steal", **hops[-1]}
                    )
                )
                break
            print(json.dumps({"blocked": rnd, "reason": "dpr reserved; lr not hoppable"}))
            time.sleep(5)
            continue
        try:
            res = reserve(DPR, rnd)
        except RuntimeError as exc:
            msg = str(exc)
            if "already exists" in msg or "not the frontier" in msg:
                print(json.dumps({"skip": rnd, "reason": msg.splitlines()[-1][:200]}))
                time.sleep(2)
                continue
            raise
        token = res["token"]
        staging = Path(res["staging_dir"])
        try:
            mill = run(
                [
                    sys.executable,
                    str(MILL),
                    "--round",
                    str(rnd),
                    "--staging",
                    str(staging),
                ]
            )
            mill_info = json.loads(mill.stdout)
            pub = publish(DPR, rnd, token)
        except Exception as exc:
            abort = run(
                [
                    sys.executable,
                    str(TXN),
                    "abort",
                    str(DPR),
                    "--round",
                    str(rnd),
                    "--token",
                    token,
                ],
                check=False,
            )
            print(
                json.dumps(
                    {
                        "failed": rnd,
                        "error": str(exc)[:500],
                        "abort": (abort.stdout or abort.stderr or "")[-200:],
                    }
                )
            )
            raise
        published.append(
            {"round": rnd, "ids": mill_info["ids"], "records": pub.get("records")}
        )
        print(json.dumps({"published": published[-1]}), flush=True)
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
