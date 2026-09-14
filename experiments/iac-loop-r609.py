#!/usr/bin/env python3
"""Reserve → mill → publish infra-as-code-factory until catalog or max_rounds.

Hop if reserved: observability-debug-factory (never eval-harness).
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MILL = ROOT / "experiments" / "iac-mill-r609.py"
TXN = ROOT / "pipelines" / "round_txn.py"
FACTORY = ROOT / "outputs" / "raw" / "2026-08-19-agentic" / "infra-as-code-factory"
HOP = ROOT / "outputs" / "raw" / "2026-08-19-agentic" / "observability-debug-factory"
SKIP_HOP = ROOT / "outputs" / "raw" / "2026-08-19-agentic" / "eval-harness-trajectory-factory"

import importlib.util

def load_mill():
    spec = importlib.util.spec_from_file_location("iac_mill_r609", MILL)
    mill = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mill)
    return mill


_mill = load_mill()
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


def publish_round(factory: Path, n: int, mill: Path) -> None:
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
    token = payload["token"]
    staging = payload["staging_dir"]
    print(f"reserved r{n} token={token} staging={staging}", flush=True)
    try:
        mill_proc = run(
            [sys.executable, str(mill), "--round", str(n), "--staging", staging]
        )
        sys.stdout.write(mill_proc.stdout or "")
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
    except subprocess.CalledProcessError as exc:
        print(exc.stdout, exc.stderr, flush=True)
        print(f"mill/publish failed for r{n}; abort reservation", flush=True)
        run(
            [
                sys.executable,
                str(TXN),
                "abort",
                str(factory),
                "--round",
                str(n),
                "--token",
                token,
            ],
            check=False,
        )
        raise


def main() -> int:
    max_rounds = int(sys.argv[1]) if len(sys.argv) > 1 else 64
    done = 0
    hops = 0
    published: list[int] = []
    while done < max_rounds:
        _mill = load_mill()
        CATALOG_FIRST = _mill.CATALOG_FIRST
        CATALOG_LEN = len(_mill.PAIRS)
        n = frontier(FACTORY)
        last = CATALOG_FIRST + CATALOG_LEN - 1
        if n > last:
            print(f"catalog exhausted at frontier {n} (last {last})", flush=True)
            break
        if reserved(FACTORY, n):
            print(f"infra-as-code r{n} already reserved; retry frontier (never steal)", flush=True)
            n2 = frontier(FACTORY)
            if n2 != n and not reserved(FACTORY, n2):
                print(f"frontier moved to r{n2}; continue IAC", flush=True)
                continue
            print("still reserved; hop observability-debug", flush=True)
            hops += 1
            hn = frontier(HOP)
            if HOP.resolve() == SKIP_HOP.resolve() or reserved(HOP, hn):
                print("hop unavailable; retry IAC frontier", flush=True)
                continue
            print(f"obs r{hn} unreserved but obs mill not wired; retry IAC", flush=True)
            continue
        try:
            publish_round(FACTORY, n, MILL)
        except subprocess.CalledProcessError:
            if reserved(FACTORY, n):
                print("lost race on reserve; never steal", flush=True)
                return 6
            print("reserve/mill/publish failed", flush=True)
            return 7
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
                "catalog_last": CATALOG_FIRST + CATALOG_LEN - 1,
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
