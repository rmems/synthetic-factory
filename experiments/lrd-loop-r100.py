#!/usr/bin/env python3
"""LRD leftover3d mill r100+: frontier → reserve → mill → publish until 16 rounds."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO = Path("/home/raulmc/rmems/synthetic-factory")
TXN = REPO / "pipelines/round_txn.py"
MILL = REPO / "experiments/lrd-mill-leftover3d-r100.py"
LRD = REPO / "outputs/raw/2026-08-19-agentic/log-redaction-factory"
AGENTIC = REPO / "outputs/raw/2026-08-19-agentic"
TARGET = 16
BANNED_HOP = {"sandbox-refusal-factory"}


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
    return (factory / f"ROUND-r{rnd:02d}.reserved.json").exists() or (
        factory / f"ROUND-r{rnd}.reserved.json"
    ).exists()


def pick_factory() -> Path:
    fr = frontier(LRD)
    nxt = int(fr["next_round"])
    if not reserved_here(LRD, nxt):
        return LRD
    for child in sorted(AGENTIC.iterdir()):
        if not child.is_dir() or child.name in BANNED_HOP:
            continue
        if child.name == LRD.name:
            continue
        try:
            other = frontier(child)
        except Exception:
            continue
        on = int(other["next_round"])
        if reserved_here(child, on):
            continue
        raise SystemExit(f"LRD reserved; hop candidate {child.name} next={on} (not implemented mill)")
    raise SystemExit("LRD reserved and no hop mill")


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


def mill_and_publish(factory: Path, rnd: int) -> dict:
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
            [sys.executable, str(MILL), "--round", str(rnd), "--staging", str(staging)]
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
        raise RuntimeError(err[:800]) from exc
    return {
        "factory": factory.name,
        "round": rnd,
        "ids": mill_info["ids"],
        "records": pub.get("records"),
    }


def main():
    published = []
    for _ in range(TARGET):
        factory = pick_factory()
        if factory != LRD:
            break
        fr = frontier(LRD)
        rnd = int(fr["next_round"])
        out = mill_and_publish(LRD, rnd)
        if out.get("exhausted"):
            published.append(out)
            break
        if out.get("skip"):
            published.append(out)
            continue
        published.append(out)
        print(json.dumps(out), flush=True)
    print(json.dumps({"published": published, "n": len([p for p in published if p.get("ids")])}))


if __name__ == "__main__":
    sys.exit(main() or 0)
