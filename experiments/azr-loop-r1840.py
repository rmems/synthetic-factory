#!/usr/bin/env python3
"""Reserve → mill → publish authz-regression-factory unique IDOR/BFLA from r1840.

Do not steal reserved seats. Hop if the frontier seat is already reserved.
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
MILL = ROOT / "experiments" / "azr-mill-r1840.py"
TXN = ROOT / "pipelines" / "round_txn.py"
FACTORY = ROOT / "outputs" / "raw" / "2026-08-19-agentic" / "authz-regression-factory"
AGENTIC = FACTORY.parent
HOP_ORDER = [
    AGENTIC / "prompt-cache-invalidation-factory",
    AGENTIC / "k8s-crashloop-factory",
    AGENTIC / "payment-idempotency-factory",
    AGENTIC / "distributed-lock-factory",
    AGENTIC / "cache-stampede-factory",
    AGENTIC / "git-ops-recovery-factory",
    AGENTIC / "secret-scan-remediation-factory",
    AGENTIC / "observability-debug-factory",
    AGENTIC / "browser-tool-use-factory",
]

import importlib.util

_spec = importlib.util.spec_from_file_location("azr_mill_r1840", MILL)
_mill = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(_mill)
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


def publish_one(n: int, pair_idx: int) -> None:
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
    print(f"reserved r{n} token={token} staging={staging} pair={pair_idx}", flush=True)
    try:
        _mill.write_round(n, Path(staging), pair_idx)
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
    except Exception:
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


def hop_report(n: int) -> None:
    print(f"authz r{n} already reserved; hop scan (never steal)", flush=True)
    for hop in HOP_ORDER:
        if hop.name in {"eval-harness-trajectory-factory", "sandbox-refusal-factory"}:
            continue
        if not hop.is_dir():
            continue
        try:
            hn = frontier(hop)
        except Exception as exc:
            print(f"{hop.name} frontier failed: {exc}", flush=True)
            continue
        if reserved(hop, hn):
            print(f"{hop.name} r{hn} reserved; skip", flush=True)
            continue
        print(
            f"hop candidate {hop.name} next={hn} unreserved; "
            "this mill stays on authz-regression-factory unique leftover IDOR",
            flush=True,
        )
        return
    print("no unreserved hop factory this spin", flush=True)


def main() -> int:
    max_rounds = int(sys.argv[1]) if len(sys.argv) > 1 else CATALOG_LEN
    wait_s = 0.12
    reserved_spins = 0
    done = 0
    published: list[int] = []
    pair_idx = 0
    while done < max_rounds and pair_idx < CATALOG_LEN:
        n = frontier(FACTORY)
        if reserved(FACTORY, n):
            reserved_spins += 1
            if reserved_spins == 1 or reserved_spins % 40 == 0:
                hop_report(n)
            time.sleep(wait_s)
            continue
        reserved_spins = 0
        try:
            publish_one(n, pair_idx)
        except subprocess.CalledProcessError:
            if reserved(FACTORY, n):
                print(f"lost race r{n}; retry (never steal)", flush=True)
                time.sleep(0.2)
                continue
            print(f"mill/publish failed for r{n}", flush=True)
            return 6
        except Exception as exc:
            print(f"error r{n}: {exc}", flush=True)
            time.sleep(0.2)
            continue
        done += 1
        published.append(n)
        print(f"published r{n} pair={pair_idx} ({done}/{max_rounds})", flush=True)
        pair_idx += 1
    print(
        json.dumps(
            {
                "published": done,
                "rounds": published,
                "frontier": frontier(FACTORY),
                "catalog_len": CATALOG_LEN,
                "pair_idx": pair_idx,
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
