#!/usr/bin/env python3
"""Reserve → mill → publish authz-regression-factory unique leftover IDOR from r1464.

Do not steal r1205–r1463. Hop if the frontier seat is already reserved.
Never rewrite raw. Not leftover mill. Not JWT catalog. Not sandbox-refusal.
Do not exit after one batch: loop until catalog exhausts, reserve conflict, or quota dies.
"""
from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MILL = ROOT / "experiments" / "azr-mill-r1464.py"
TXN = ROOT / "pipelines" / "round_txn.py"
FACTORY = ROOT / "outputs" / "raw" / "2026-08-19-agentic" / "authz-regression-factory"
AGENTIC = FACTORY.parent
HOP_ORDER = [
    AGENTIC / "prompt-cache-invalidation-factory",
    AGENTIC / "docker-build-cache-factory",
    AGENTIC / "k8s-crashloop-factory",
    AGENTIC / "payment-idempotency-factory",
    AGENTIC / "distributed-lock-factory",
    AGENTIC / "cache-stampede-factory",
    AGENTIC / "git-ops-recovery-factory",
]

import importlib.util

_spec = importlib.util.spec_from_file_location("azr_mill_r1464", MILL)
_mill = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(_mill)
CATALOG_FIRST = _mill.CATALOG_FIRST
CATALOG_LEN = len(_mill.PAIRS)


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
    return json.loads(proc.stdout)["next_round"]


def reserved(factory: Path, n: int) -> bool:
    return (factory / f"ROUND-r{n:02d}.reserved.json").exists()


def publish_one(n: int) -> None:
    proc = run(
        [
            sys.executable,
            str(TXN),
            "reserve",
            str(FACTORY),
            "--round",
            str(n),
            "--expected",
            "2",
        ]
    )
    print(proc.stdout, flush=True)
    payload = json.loads(proc.stdout)
    token = payload["token"]
    staging = payload["staging_dir"]
    print(f"reserved r{n} token={token} staging={staging}", flush=True)
    try:
        # Mill in-process: spawning azr-mill-r1464.py re-imports mill r1205 (~13s)
        # per round and was the one-batch stall mode.
        _mill.write_round(n, Path(staging))
        pub = run(
            [
                sys.executable,
                str(TXN),
                "publish",
                str(FACTORY),
                "--round",
                str(n),
                "--token",
                token,
            ]
        )
        print(pub.stdout, flush=True)
    except subprocess.CalledProcessError as exc:
        print(exc.stdout, exc.stderr, flush=True)
        run(
            [
                sys.executable,
                str(TXN),
                "abort",
                str(FACTORY),
                "--round",
                str(n),
                "--token",
                token,
            ],
            check=False,
        )
        raise


def hop_report(n: int) -> int:
    print(f"authz r{n} already reserved; hop (never steal)", flush=True)
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
            "this mill stays on authz-regression-factory unique leftover IDOR",
            flush=True,
        )
        return 3
    print("no unreserved hop factory; stop", flush=True)
    return 3


def main() -> int:
    # Default is the full remaining catalog — do not stop after one batch.
    last = CATALOG_FIRST + CATALOG_LEN - 1
    max_rounds = int(sys.argv[1]) if len(sys.argv) > 1 else CATALOG_LEN
    wait_s = 4.0
    waited = 0.0
    wait_cap = 600.0
    done = 0
    published: list[int] = []
    while done < max_rounds:
        n = frontier(FACTORY)
        if n < CATALOG_FIRST:
            if waited >= wait_cap:
                print(
                    f"still waiting for frontier {CATALOG_FIRST} (now {n}); hop",
                    flush=True,
                )
                return hop_report(n)
            print(
                f"frontier {n} before catalog {CATALOG_FIRST}; wait (never steal)",
                flush=True,
            )
            time.sleep(wait_s)
            waited += wait_s
            continue
        if n > last:
            print(f"catalog exhausted at frontier {n} (last={last})", flush=True)
            break
        if reserved(FACTORY, n):
            return hop_report(n)
        try:
            publish_one(n)
        except subprocess.CalledProcessError:
            if reserved(FACTORY, n):
                return hop_report(n)
            print(f"mill/publish failed for r{n}", flush=True)
            return 6
        done += 1
        published.append(n)
        print(f"published r{n} ({done}/{max_rounds})", flush=True)
    print(
        json.dumps(
            {
                "published": done,
                "rounds": published,
                "frontier": frontier(FACTORY),
                "catalog_last": last,
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
