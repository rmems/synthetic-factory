#!/usr/bin/env python3
"""Prefer docker-build-cache; hop k8s-crashloop if docker is reserved.

Never steal a reservation. Never rewrite raw. Not eval-harness. Not sandbox-refusal.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TXN = ROOT / "pipelines" / "round_txn.py"
AGENTIC = ROOT / "outputs" / "raw" / "2026-08-19-agentic"
DBC = AGENTIC / "docker-build-cache-factory"
KCL = AGENTIC / "k8s-crashloop-factory"
DBC_MILL = ROOT / "experiments" / "dbc-mill-r308.py"
KCL_MILL = ROOT / "experiments" / "kcl-mill-r1007.py"

import importlib.util


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


KCL_M = load(KCL_MILL, "kcl_mill_r1007")


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
    print(f"reserved {factory.name} r{n} token={token}", flush=True)
    mill_proc = run([sys.executable, str(mill), "--round", str(n), "--staging", staging])
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


def dbc_ready() -> tuple[bool, int]:
    if not DBC_MILL.exists():
        return False, -1
    n = frontier(DBC)
    if reserved(DBC, n):
        return False, n
    spec = importlib.util.spec_from_file_location("dbc_mill_r233", DBC_MILL)
    mill = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mill)
    last = mill.CATALOG_FIRST + len(mill.PAIRS) - 1
    return n <= last, n


def main() -> int:
    max_rounds = int(sys.argv[1]) if len(sys.argv) > 1 else 20
    done = 0
    published: list[str] = []
    kcl_last = KCL_M.CATALOG_FIRST + len(KCL_M.PAIRS) - 1
    while done < max_rounds:
        dbc_ok, dbc_n = dbc_ready()
        if dbc_ok:
            try:
                publish_one(DBC, dbc_n, DBC_MILL)
            except subprocess.CalledProcessError as exc:
                print(exc.stdout, exc.stderr, flush=True)
                if reserved(DBC, dbc_n):
                    print("docker reserved during reserve; hop k8s", flush=True)
                else:
                    return 5
            else:
                done += 1
                published.append(f"dbc-r{dbc_n}")
                print(f"published docker r{dbc_n} ({done}/{max_rounds})", flush=True)
                continue
        kn = frontier(KCL)
        if reserved(KCL, kn):
            print(f"k8s r{kn} reserved; stop hop", flush=True)
            return 3
        if kn > kcl_last:
            print(f"k8s catalog exhausted at {kn}", flush=True)
            break
        try:
            publish_one(KCL, kn, KCL_MILL)
        except subprocess.CalledProcessError as exc:
            print(exc.stdout, exc.stderr, flush=True)
            return 4
        done += 1
        published.append(f"kcl-r{kn}")
        print(f"published k8s r{kn} ({done}/{max_rounds})", flush=True)
    print(json.dumps({"published": done, "rounds": published}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
