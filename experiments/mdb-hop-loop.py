#!/usr/bin/env python3
"""Prefer mdb; hop ssl-cert-rotation if mdb reserved. Never sandbox-refusal. Never steal."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TXN = ROOT / "pipelines" / "round_txn.py"
AGENTIC = ROOT / "outputs" / "raw" / "2026-08-19-agentic"
MDB = AGENTIC / "monorepo-dep-bump-factory"
SSL = AGENTIC / "ssl-cert-rotation-factory"
MDB_MILL = ROOT / "experiments" / "mdb-mill-r840.py"
SSL_MILL = ROOT / "experiments" / "ssl-mill-r106.py"
PBC = AGENTIC / "proto-breaking-change-factory"
PBC_MILL = ROOT / "experiments" / "pbc-mill-r966.py"
SKIP = {"sandbox-refusal-factory"}

import importlib.util


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def run(args: list[str], check: bool = True) -> subprocess.CompletedProcess:
    print("+", " ".join(str(a) for a in args), flush=True)
    return subprocess.run([str(a) for a in args], cwd=ROOT, check=check, text=True, capture_output=True)


def frontier(factory: Path) -> int:
    proc = run([sys.executable, str(TXN), "frontier", str(factory)])
    nxt = json.loads(proc.stdout)["next_round"]
    print(f"frontier {factory.name} next_round={nxt}", flush=True)
    return nxt


def reserved(factory: Path, n: int) -> bool:
    return (factory / f"ROUND-r{n:02d}.reserved.json").exists()


def catalog_span(mill: Path) -> tuple[int, int]:
    m = load(mill, "mill")
    first = m.CATALOG_FIRST
    return first, first + len(m.PAIRS) - 1


def publish_one(factory: Path, n: int, mill: Path) -> None:
    proc = run(
        [sys.executable, str(TXN), "reserve", str(factory), "--round", str(n), "--expected", "2"]
    )
    payload = json.loads(proc.stdout)
    print(proc.stdout, flush=True)
    token = payload["token"]
    staging = payload["staging_dir"]
    mill_proc = run([sys.executable, str(mill), "--round", str(n), "--staging", staging])
    if mill_proc.stderr:
        sys.stderr.write(mill_proc.stderr)
    print(mill_proc.stdout, flush=True)
    pub = run(
        [sys.executable, str(TXN), "publish", str(factory), "--round", str(n), "--token", token]
    )
    print(pub.stdout, flush=True)


def pick() -> tuple[Path, Path, int] | None:
    mdb_n = frontier(MDB)
    first, last = catalog_span(MDB_MILL)
    if first <= mdb_n <= last and not reserved(MDB, mdb_n):
        return MDB, MDB_MILL, mdb_n
    if reserved(MDB, mdb_n):
        print(f"mdb r{mdb_n} reserved; hop", flush=True)
    elif mdb_n > last:
        print(f"mdb catalog exhausted at {mdb_n}; hop", flush=True)
    ssl_n = frontier(SSL)
    sfirst, slast = catalog_span(SSL_MILL)
    if sfirst <= ssl_n <= slast and not reserved(SSL, ssl_n):
        return SSL, SSL_MILL, ssl_n
    if reserved(SSL, ssl_n):
        print(f"ssl r{ssl_n} reserved; hop pbc", flush=True)
    else:
        print(f"ssl catalog {sfirst}..{slast} vs frontier {ssl_n}; hop pbc", flush=True)
    pbc_n = frontier(PBC)
    if reserved(PBC, pbc_n):
        print(f"pbc r{pbc_n} reserved; no steal", flush=True)
        return None
    # unused-slug mill; any frontier is ok if unused pairs remain
    pbc = load(PBC_MILL, "pbc")
    if not pbc.unused_pairs():
        print("pbc unused catalog empty", flush=True)
        return None
    return PBC, PBC_MILL, pbc_n


def main() -> int:
    max_rounds = int(sys.argv[1]) if len(sys.argv) > 1 else 32
    done = 0
    published: list[str] = []
    while done < max_rounds:
        picked = pick()
        if picked is None:
            print("no hop target; stop", flush=True)
            break
        factory, mill, n = picked
        try:
            publish_one(factory, n, mill)
        except subprocess.CalledProcessError as exc:
            print(exc.stdout, exc.stderr, flush=True)
            if reserved(factory, n) and not (factory / f"ROUND-r{n:02d}.complete.json").exists():
                print(f"lost race on {factory.name} r{n}; hop next", flush=True)
                continue
            return 5
        done += 1
        published.append(f"{factory.name}-r{n}")
        print(f"published {factory.name} r{n} ({done}/{max_rounds})", flush=True)
    print(json.dumps({"published": done, "rounds": published}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
