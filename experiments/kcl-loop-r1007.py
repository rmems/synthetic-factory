#!/usr/bin/env python3
"""Reserve → mill → publish k8s-crashloop-factory until catalog or quota dies.

Hop an unreserved named factory if this seat is already reserved.
Never steal a reservation. Never rewrite raw. Not eval-harness. Not sandbox-refusal.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MILL = ROOT / "experiments" / "kcl-mill-r1007.py"
TXN = ROOT / "pipelines" / "round_txn.py"
FACTORY = ROOT / "outputs" / "raw" / "2026-08-19-agentic" / "k8s-crashloop-factory"
AGENTIC = FACTORY.parent
HOP_ORDER = [
    AGENTIC / "git-ops-recovery-factory",
    AGENTIC / "observability-debug-factory",
    AGENTIC / "payment-idempotency-factory",
    AGENTIC / "infra-as-code-factory",
    AGENTIC / "data-pipeline-repair-factory",
    AGENTIC / "package-release-factory",
    AGENTIC / "authz-regression-factory",
    AGENTIC / "mcp-tool-schema-drift-factory",
]

import importlib.util

_spec = importlib.util.spec_from_file_location("kcl_mill_r1007", MILL)
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
    print(
        f"kcl loop start catalog={CATALOG_LEN} first={CATALOG_FIRST} max={max_rounds}",
        flush=True,
    )
    while done < max_rounds:
        n = frontier(FACTORY)
        last = CATALOG_FIRST + CATALOG_LEN - 1
        if n > last:
            print(f"catalog exhausted at frontier {n} (last={last})", flush=True)
            break
        if reserved(FACTORY, n):
            print(f"k8s-crashloop r{n} already reserved; hop", flush=True)
            hopped = False
            for hop in HOP_ORDER:
                if hop.name in {
                    "eval-harness-trajectory-factory",
                    "sandbox-refusal-factory",
                }:
                    continue
                hn = frontier(hop)
                if reserved(hop, hn):
                    print(f"{hop.name} r{hn} reserved; skip", flush=True)
                    continue
                print(
                    f"hop candidate {hop.name} next={hn} unreserved; "
                    f"no mill in this loop — skip (do not steal kcl)",
                    flush=True,
                )
                hops += 1
                hopped = True
                if hops >= 8:
                    print("HOP thrice+; stopping without steal.", flush=True)
                    return 2
            if not hopped:
                print("no hop candidate; stopping without steal.", flush=True)
                return 2
            continue
        try:
            publish_one(FACTORY, n, MILL)
        except subprocess.CalledProcessError as exc:
            print(exc.stdout or "", flush=True)
            print(exc.stderr or "", flush=True)
            msg = (exc.stderr or exc.stdout or str(exc)).lower()
            if "reserv" in msg or "already" in msg or "not the frontier" in msg:
                print(f"reserve/publish failed for r{n}; hop", flush=True)
                hops += 1
                if hops >= 8:
                    print("quota/reserve died; stopping.", flush=True)
                    return 0 if published else 2
                continue
            raise
        published.append(n)
        done += 1
        print(f"LOOP published r{n} done={done}/{max_rounds}", flush=True)
    print(f"DONE published={published} hops={hops}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
