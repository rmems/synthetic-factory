#!/usr/bin/env python3
"""Reserve → mill → publish proto-breaking-change-factory until catalog dies.

Hop an unreserved named factory if this seat is already reserved.
Never steal a reservation. Never rewrite raw. Not eval-harness. Not sandbox-refusal.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MILL = ROOT / "experiments" / "pbc-mill-r751.py"
TXN = ROOT / "pipelines" / "round_txn.py"
FACTORY = ROOT / "outputs" / "raw" / "2026-08-19-agentic" / "proto-breaking-change-factory"
AGENTIC = FACTORY.parent
HOP_ORDER = [
    AGENTIC / "notebook-to-pipeline-factory",
    AGENTIC / "prompt-cache-invalidation-factory",
    AGENTIC / "distributed-lock-factory",
    AGENTIC / "cache-stampede-factory",
    AGENTIC / "git-ops-recovery-factory",
    AGENTIC / "docker-build-cache-factory",
    AGENTIC / "k8s-crashloop-factory",
]

import importlib.util

_spec = importlib.util.spec_from_file_location("pbc_mill_r701", MILL)
_mill = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(_mill)
CATALOG_FIRST = _mill.CATALOG_FIRST
CATALOG_LEN = len(getattr(_mill, "unused_pairs", lambda: _mill.PAIRS)())


def run(args: list[str], check: bool = True) -> subprocess.CompletedProcess:
    print("+", " ".join(str(a) for a in args), flush=True)
    return subprocess.run(
        [str(a) for a in args],
        cwd=ROOT,
        check=check,
        text=True,
        capture_output=True,
    )


def frontier(factory: Path) -> int:
    proc = run([sys.executable, str(TXN), "frontier", str(factory)])
    print(proc.stdout, flush=True)
    return json.loads(proc.stdout)["next_round"]


def reserved(factory: Path, n: int) -> bool:
    return (factory / f"ROUND-r{n:02d}.reserved.json").exists()


def publish_one(factory: Path, n: int, mill: Path) -> None:
    proc = run(
        [
            sys.executable,
            str(TXN),
            "reserve",
            str(factory),
            "--round",
            str(n),
            "--expected",
            "2",
        ]
    )
    payload = json.loads(proc.stdout)
    print(proc.stdout, flush=True)
    token = payload["token"]
    staging = payload["staging_dir"]
    print(f"reserved r{n} token={token} staging={staging}", flush=True)
    mill_proc = run(
        [sys.executable, str(mill), "--round", str(n), "--staging", staging]
    )
    sys.stderr.write(mill_proc.stderr or "")
    print(mill_proc.stdout, flush=True)
    pub = run(
        [
            sys.executable,
            str(TXN),
            "publish",
            str(factory),
            "--round",
            str(n),
            "--token",
            token,
        ]
    )
    print(pub.stdout, flush=True)


def main() -> int:
    max_rounds = int(sys.argv[1]) if len(sys.argv) > 1 else CATALOG_LEN
    done = 0
    hops = 0
    published: list[int] = []
    while done < max_rounds:
        n = frontier(FACTORY)
        unused_n = len(getattr(_mill, "unused_pairs", lambda: _mill.PAIRS)())
        if unused_n <= 0:
            print(f"catalog exhausted at frontier {n}", flush=True)
            break
        if reserved(FACTORY, n):
            print(f"proto-breaking-change r{n} already reserved; hop", flush=True)
            hopped = False
            for hop in HOP_ORDER:
                if hop.name in {
                    "eval-harness-trajectory-factory",
                    "sandbox-refusal-factory",
                }:
                    continue
                if not hop.is_dir():
                    continue
                hn = frontier(hop)
                if reserved(hop, hn):
                    print(f"{hop.name} r{hn} reserved; skip", flush=True)
                    continue
                print(
                    f"hop candidate {hop.name} next={hn} unreserved; "
                    "no mill in this proto-breaking-change mechanic loop",
                    flush=True,
                )
                hops += 1
                hopped = True
                break
            if not hopped:
                print("no unreserved hop factory; stop", flush=True)
                return 3
            return 3
        try:
            publish_one(FACTORY, n, MILL)
        except subprocess.CalledProcessError as exc:
            print(exc.stdout, exc.stderr, flush=True)
            if reserved(FACTORY, n):
                print(
                    "lost race on reserve or mill/publish failed with seat held",
                    flush=True,
                )
                return 4
            print("reserve/mill/publish failed", flush=True)
            return 5
        done += 1
        published.append(n)
        print(f"published r{n} ({done}/{max_rounds})", flush=True)
    print(
        json.dumps(
            {
                "published": done,
                "rounds": published,
                "hops": hops,
                "frontier": frontier(FACTORY),
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
