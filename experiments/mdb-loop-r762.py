#!/usr/bin/env python3
"""Reserve → mill → publish monorepo-dep-bump-factory until catalog or max_rounds.

Hop/retry if the mdb seat is already reserved. Never steal. Never rewrite raw.
"""
from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MILL = ROOT / "experiments" / "mdb-mill-r762.py"
TXN = ROOT / "pipelines" / "round_txn.py"
FACTORY = ROOT / "outputs" / "raw" / "2026-08-19-agentic" / "monorepo-dep-bump-factory"

import importlib.util

_spec = importlib.util.spec_from_file_location("mdb_mill_r762", MILL)
_mill = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(_mill)


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


def publish_round(factory: Path, n: int, expected: int, token: str | None = None, staging: str | None = None) -> None:
    if token is None or staging is None:
        proc = run(
            [
                sys.executable,
                str(TXN),
                "reserve",
                str(factory),
                "--round",
                str(n),
                "--expected",
                str(expected),
            ]
        )
        payload = json.loads(proc.stdout)
        print(proc.stdout, flush=True)
        token = payload["token"]
        staging = payload["staging_dir"]
    print(f"reserved r{n} token={token} staging={staging}", flush=True)
    mill = run(
        [
            sys.executable,
            str(MILL),
            "--round",
            str(n),
            "--staging",
            staging,
        ]
    )
    if mill.stderr:
        sys.stderr.write(mill.stderr)
    print(mill.stdout, flush=True)
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


def reload_catalog() -> tuple[int, int]:
    spec = importlib.util.spec_from_file_location("mdb_mill_r762", MILL)
    mill = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mill)
    return mill.CATALOG_FIRST, len(mill.PAIRS)


def main() -> int:
    max_rounds = int(sys.argv[1]) if len(sys.argv) > 1 else 16
    pre_token = sys.argv[2] if len(sys.argv) > 2 else None
    pre_staging = sys.argv[3] if len(sys.argv) > 3 else None
    done = 0
    hops = 0
    published: list[int] = []
    while done < max_rounds:
        first, length = reload_catalog()
        last = first + length - 1
        n = frontier(FACTORY)
        if n > last:
            print(f"catalog exhausted at frontier {n} (last={last})", flush=True)
            break
        if n < first:
            print(f"frontier {n} below catalog first {first}; waiting", flush=True)
            time.sleep(2)
            hops += 1
            continue
        if reserved(FACTORY, n) and not (pre_token and n == first and done == 0):
            print(f"mdb r{n} already reserved; retry shortly (no steal)", flush=True)
            hops += 1
            time.sleep(2)
            continue
        try:
            if done == 0 and pre_token and pre_staging and n == first:
                publish_round(FACTORY, n, 2, token=pre_token, staging=pre_staging)
                pre_token = None
                pre_staging = None
            else:
                publish_round(FACTORY, n, 2)
        except subprocess.CalledProcessError as exc:
            print(exc.stdout, exc.stderr, flush=True)
            if reserved(FACTORY, n) and not (FACTORY / f"ROUND-r{n:02d}.complete.json").exists():
                print("lost race or mill/publish failed after reserve", flush=True)
                return 4
            print(f"reserve/mill/publish failed for r{n}", flush=True)
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
