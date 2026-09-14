#!/usr/bin/env python3
"""Reserve → mill decoder plants → publish until catalog or max_rounds.

Hop log-redaction-factory if the secret-scan seat is already reserved and
log-redaction is unreserved. Never steal a reservation. Never rewrite raw.
"""
from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MILL = ROOT / "experiments" / "ssr-mill-decoder.py"
TXN = ROOT / "pipelines" / "round_txn.py"
FACTORY = ROOT / "outputs" / "raw" / "2026-08-19-agentic" / "secret-scan-remediation-factory"
HOP = ROOT / "outputs" / "raw" / "2026-08-19-agentic" / "log-redaction-factory"

import importlib.util

_spec = importlib.util.spec_from_file_location("ssr_mill_decoder", MILL)
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
    print(proc.stdout, flush=True)
    return json.loads(proc.stdout)["next_round"]


def reserved(factory: Path, n: int) -> bool:
    return (factory / f"ROUND-r{n:02d}.reserved.json").exists()


def next_idx() -> int:
    used = _mill.published_slugs()
    for i, (suc, fail) in enumerate(_mill.PAIRS):
        if suc["slug"] not in used and fail["slug"] not in used:
            return i
    return -1


def publish_one(n: int, idx: int) -> None:
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
    payload = json.loads(proc.stdout)
    print(proc.stdout, flush=True)
    token = payload["token"]
    staging = payload["staging_dir"]
    print(f"reserved r{n} idx={idx} token={token} staging={staging}", flush=True)
    mill_proc = run(
        [
            sys.executable,
            str(MILL),
            "--round",
            str(n),
            "--staging",
            staging,
            "--idx",
            str(idx),
        ]
    )
    sys.stderr.write(mill_proc.stderr or "")
    print(mill_proc.stdout, flush=True)
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


def main() -> int:
    max_rounds = int(sys.argv[1]) if len(sys.argv) > 1 else 12
    done = 0
    hops = 0
    published: list[int] = []
    spins = 0
    while done < max_rounds:
        idx = next_idx()
        if idx < 0:
            print("catalog exhausted (all slugs published)", flush=True)
            break
        n = frontier(FACTORY)
        if reserved(FACTORY, n):
            print(f"secret-scan r{n} already reserved; check hop", flush=True)
            hn = frontier(HOP)
            if not reserved(HOP, hn):
                print(
                    f"log-redaction r{hn} unreserved; no decoder mill for that factory; wait",
                    flush=True,
                )
                hops += 1
            else:
                print(f"log-redaction r{hn} reserved; do not steal", flush=True)
            spins += 1
            if spins > 80:
                print("too many reserved spins; stop", flush=True)
                break
            time.sleep(2)
            continue
        try:
            publish_one(n, idx)
        except subprocess.CalledProcessError as exc:
            print(exc.stdout, exc.stderr, flush=True)
            if reserved(FACTORY, n):
                print("lost race on reserve; do not steal", flush=True)
                spins += 1
                time.sleep(1)
                continue
            print("reserve/mill/publish failed", flush=True)
            return 5
        done += 1
        published.append(n)
        spins = 0
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
