#!/usr/bin/env python3
"""Reserve → mill → publish db-migration-repair-factory r1340+ until catalog."""
from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MILL = ROOT / "experiments" / "dbm-mill-r1340.py"
TXN = ROOT / "pipelines" / "round_txn.py"
FACTORY = ROOT / "outputs" / "raw" / "2026-08-19-agentic" / "db-migration-repair-factory"
NEVER_HOP = {"sandbox-refusal-factory", "eval-harness-trajectory-factory"}
AGENTIC = FACTORY.parent
STOP = ROOT / "FACTORY_STOP"

import importlib.util

_spec = importlib.util.spec_from_file_location("dbm_mill_r1340", MILL)
_mill = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(_mill)
CATALOG_FIRST = _mill.CATALOG_FIRST
CATALOG_LEN = len(_mill.PAIRS)


def run(args: list[str], check: bool = True) -> subprocess.CompletedProcess:
    print("+", " ".join(str(a) for a in args), flush=True)
    return subprocess.run(
        [str(a) for a in args], cwd=ROOT, check=check, text=True, capture_output=True
    )


def frontier(factory: Path) -> int:
    return json.loads(run([sys.executable, str(TXN), "frontier", str(factory)]).stdout)["next_round"]


def reserved(factory: Path, n: int) -> bool:
    return (factory / f"ROUND-r{n:02d}.reserved.json").exists()


def hop_target() -> Path | None:
    for path in sorted(AGENTIC.iterdir()):
        if not path.is_dir() or path.name in NEVER_HOP or path.name == FACTORY.name:
            continue
        try:
            n = frontier(path)
        except (subprocess.CalledProcessError, json.JSONDecodeError, KeyError):
            continue
        if not reserved(path, n):
            return path
    return None


def main() -> int:
    max_rounds = int(sys.argv[1]) if len(sys.argv) > 1 else CATALOG_LEN
    done = 0
    hops = 0
    published: list[int] = []
    while done < max_rounds:
        if STOP.exists():
            print("FACTORY_STOP present; halt", flush=True)
            break
        n = frontier(FACTORY)
        last = CATALOG_FIRST + CATALOG_LEN - 1
        if n < CATALOG_FIRST:
            print(f"frontier {n} before catalog {CATALOG_FIRST}; stop", flush=True)
            return 7
        if n > last:
            print(f"catalog exhausted at frontier {n} (last {last})", flush=True)
            break
        if reserved(FACTORY, n):
            hop = hop_target()
            hops += 1
            print(f"db-migration r{n} already reserved; hop={hop}; retry", flush=True)
            time.sleep(3)
            if hops > 40:
                return 3 if hop else 2
            continue
        try:
            proc = run(
                [sys.executable, str(TXN), "reserve", str(FACTORY), "--round", str(n), "--expected", "2"]
            )
        except subprocess.CalledProcessError as exc:
            print(exc.stdout, exc.stderr, flush=True)
            if reserved(FACTORY, n):
                hop = hop_target()
                hops += 1
                print(f"reserve race r{n}; hop={hop}; retry", flush=True)
                time.sleep(3)
                if hops > 40:
                    return 3 if hop else 2
                continue
            return 5
        payload = json.loads(proc.stdout)
        token, staging = payload["token"], payload["staging_dir"]
        print(f"reserved r{n} token={token} staging={staging}", flush=True)
        try:
            mill = run([sys.executable, str(MILL), "--round", str(n), "--staging", staging])
            sys.stderr.write(mill.stderr or "")
            pub = run(
                [sys.executable, str(TXN), "publish", str(FACTORY), "--round", str(n), "--token", token]
            )
            print(pub.stdout, flush=True)
        except subprocess.CalledProcessError as exc:
            print(exc.stdout, exc.stderr, flush=True)
            run(
                [sys.executable, str(TXN), "abort", str(FACTORY), "--round", str(n), "--token", token],
                check=False,
            )
            return 6
        done += 1
        published.append(n)
        print(f"published r{n} ({done}/{max_rounds})", flush=True)
    print(json.dumps({"published": done, "rounds": published, "hops": hops, "frontier": frontier(FACTORY)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
