#!/usr/bin/env python3
"""Reserve → mill leftover3 → publish search-index-rebuild-factory. Never steal."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MILL = ROOT / "experiments" / "sir-mill-leftover3-r72.py"
TXN = ROOT / "pipelines" / "round_txn.py"
FACTORY = ROOT / "outputs" / "raw" / "2026-08-19-agentic" / "search-index-rebuild-factory"

import importlib.util

_spec = importlib.util.spec_from_file_location("sir_mill_l3", MILL)
_mill = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(_mill)
CATALOG_FIRST = _mill.CATALOG_FIRST
CATALOG_LAST = CATALOG_FIRST + len(_mill.PAIRS) - 1


def run(args, check=True):
    print("+", " ".join(str(a) for a in args), flush=True)
    return subprocess.run(
        [str(a) for a in args], cwd=ROOT, check=check, text=True, capture_output=True
    )


def frontier(factory: Path) -> int:
    return json.loads(run([sys.executable, TXN, "frontier", factory]).stdout)["next_round"]


def reserved(factory: Path, n: int) -> bool:
    return (factory / f"ROUND-r{n:02d}.reserved.json").exists()


def main() -> int:
    max_rounds = int(sys.argv[1]) if len(sys.argv) > 1 else 16
    done = 0
    published = []
    ids = []
    while done < max_rounds:
        n = frontier(FACTORY)
        if n > CATALOG_LAST:
            print(f"sir leftover3 catalog exhausted at {n} (last {CATALOG_LAST})", flush=True)
            break
        if reserved(FACTORY, n):
            print(f"sir r{n} reserved; never steal", flush=True)
            return 3
        try:
            proc = run(
                [sys.executable, TXN, "reserve", FACTORY, "--round", str(n), "--expected", "2"]
            )
        except subprocess.CalledProcessError as exc:
            print(exc.stdout, exc.stderr, flush=True)
            return 5
        payload = json.loads(proc.stdout)
        token, staging = payload["token"], payload["staging_dir"]
        print(f"reserved sir r{n} token={token}", flush=True)
        try:
            mill = run([sys.executable, MILL, "--round", str(n), "--staging", staging])
            print(mill.stdout, flush=True)
            mill_ids = json.loads(mill.stdout.strip().splitlines()[-1])["ids"]
            pub = run(
                [sys.executable, TXN, "publish", FACTORY, "--round", str(n), "--token", token]
            )
        except subprocess.CalledProcessError as exc:
            print(exc.stdout, exc.stderr, flush=True)
            run(
                [sys.executable, TXN, "abort", FACTORY, "--round", str(n), "--token", token],
                check=False,
            )
            return 6
        print(pub.stdout, flush=True)
        done += 1
        published.append(n)
        ids.extend(mill_ids)
        print(f"published sir r{n} ({done}/{max_rounds})", flush=True)
    print(
        json.dumps(
            {
                "published": done,
                "rounds": published,
                "ids": ids,
                "sir_frontier": frontier(FACTORY),
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
