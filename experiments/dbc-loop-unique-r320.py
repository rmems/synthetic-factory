#!/usr/bin/env python3
"""Prefer docker-build-cache unique mill; hop k8s-crashloop if docker is reserved.

Never steal a reservation. Never rewrite raw. Not eval-harness. Not sandbox-refusal.
"""
from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TXN = ROOT / "pipelines" / "round_txn.py"
AGENTIC = ROOT / "outputs" / "raw" / "2026-08-19-agentic"
DBC = AGENTIC / "docker-build-cache-factory"
KCL = AGENTIC / "k8s-crashloop-factory"
DBC_MILL = ROOT / "experiments" / "dbc-mill-unique-r320.py"
KCL_MILL = ROOT / "experiments" / "kcl-mill-unique-r1092.py"

import importlib.util


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


DBC_M = load(DBC_MILL, "dbc_mill_unique_r320")
KCL_M = load(KCL_MILL, "kcl_mill_unique_r1092")


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


def publish_one(factory: Path, n: int, mill: Path, idx: int) -> None:
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
    print(f"reserved {factory.name} r{n} token={token} idx={idx}", flush=True)
    mill_proc = run(
        [
            sys.executable,
            str(mill),
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
            str(factory),
            "--round",
            str(n),
            "--token",
            token,
        ]
    )
    print(pub.stdout, flush=True)


def main() -> int:
    max_rounds = int(sys.argv[1]) if len(sys.argv) > 1 else 16
    deadline = time.time() + 38 * 60
    done = 0
    published: list[str] = []
    dbc_idx = 0
    kcl_idx = 0
    dbc_last = len(DBC_M.PAIRS)
    kcl_last = len(KCL_M.PAIRS)
    while done < max_rounds and time.time() < deadline:
        if dbc_idx < dbc_last:
            n = frontier(DBC)
            if reserved(DBC, n):
                print(f"docker r{n} already reserved; hop k8s if unreserved", flush=True)
            else:
                try:
                    publish_one(DBC, n, DBC_MILL, dbc_idx)
                except subprocess.CalledProcessError as exc:
                    print(exc.stdout, exc.stderr, flush=True)
                    if reserved(DBC, n):
                        print("docker reserved during reserve; hop k8s", flush=True)
                    else:
                        print("docker mill/publish failed without seat", flush=True)
                        return 5
                else:
                    done += 1
                    published.append(f"dbc-r{n}")
                    dbc_idx += 1
                    print(f"published docker r{n} ({done}/{max_rounds}) idx={dbc_idx}", flush=True)
                    continue
        kn = frontier(KCL)
        if reserved(KCL, kn):
            print(f"k8s r{kn} reserved; wait docker", flush=True)
            time.sleep(2)
            continue
        if kcl_idx >= kcl_last:
            print(f"k8s hop catalog exhausted at idx={kcl_idx}; wait docker", flush=True)
            if dbc_idx >= dbc_last:
                break
            time.sleep(2)
            continue
        try:
            publish_one(KCL, kn, KCL_MILL, kcl_idx)
        except subprocess.CalledProcessError as exc:
            print(exc.stdout, exc.stderr, flush=True)
            if reserved(KCL, kn):
                print("k8s reserved during reserve; retry", flush=True)
                time.sleep(2)
                continue
            return 4
        done += 1
        published.append(f"kcl-r{kn}")
        kcl_idx += 1
        print(f"published k8s r{kn} ({done}/{max_rounds}) idx={kcl_idx}", flush=True)
    print(json.dumps({"published": done, "rounds": published, "dbc_idx": dbc_idx, "kcl_idx": kcl_idx}))
    return 0 if done >= 12 else 1


if __name__ == "__main__":
    raise SystemExit(main())
