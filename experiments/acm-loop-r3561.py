#!/usr/bin/env python3
"""Reserve → mill leftover unique ACM plants → publish, looping until catalog or quota dies.

Never steal a reservation. Never rewrite raw. Never hop to sandbox-refusal
if that factory is reserved or writing. Do not exit after one batch.
"""
from __future__ import annotations

import json
import py_compile
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MILL = ROOT / "experiments" / "acm-mill-r3561.py"
TXN = ROOT / "pipelines" / "round_txn.py"
AGENTIC = ROOT / "outputs" / "raw" / "2026-08-19-agentic"
FACTORY = AGENTIC / "api-contract-migration-factory"

import importlib.util

py_compile.compile(str(MILL), doraise=True)
_spec = importlib.util.spec_from_file_location("acm_mill_r3561", MILL)
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


def writing(factory: Path, n: int) -> bool:
    return (factory / f"ROUND-r{n:02d}.publishing.json").exists()


def publish_one(factory: Path, n: int, idx: int) -> None:
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
            str(factory),
            "--round",
            str(n),
            "--token",
            token,
        ]
    )
    print(pub.stdout, flush=True)


def hop_candidates() -> list[Path]:
    out = []
    for path in sorted(AGENTIC.iterdir()):
        if not path.is_dir():
            continue
        if path.name == FACTORY.name:
            continue
        if path.name == "sandbox-refusal-factory":
            continue
        if path.name == "eval-harness-trajectory-factory":
            continue
        out.append(path)
    return out


def main() -> int:
    _mill.catalog_selfcheck()
    max_rounds = int(sys.argv[1]) if len(sys.argv) > 1 else 400
    deadline = time.time() + 6 * 60 * 60
    done = 0
    published: list[int] = []
    reserved_spins = 0
    print(
        json.dumps(
            {
                "catalog": len(_mill.PAIRS),
                "unused": len(_mill.unused_pairs()),
                "max_rounds": max_rounds,
            }
        ),
        flush=True,
    )
    while done < max_rounds and time.time() < deadline:
        idx = _mill.next_free_idx()
        if idx is None:
            print("acm leftover unique catalog exhausted", flush=True)
            break
        n = frontier(FACTORY)
        if reserved(FACTORY, n) or writing(FACTORY, n):
            reserved_spins += 1
            hops = []
            for hop in hop_candidates():
                hn = None
                try:
                    hn = frontier(hop)
                except Exception as exc:
                    print(f"hop frontier fail {hop.name}: {exc}", flush=True)
                    continue
                if reserved(hop, hn) or writing(hop, hn):
                    if hop.name == "sandbox-refusal-factory":
                        continue
                    print(f"{hop.name} r{hn} reserved/writing; skip", flush=True)
                    continue
                hops.append({"factory": hop.name, "next_round": hn, "unreserved": True})
            print(
                json.dumps(
                    {
                        "acm_reserved": True,
                        "round": n,
                        "spin": reserved_spins,
                        "unreserved_hops": hops[:8],
                    }
                ),
                flush=True,
            )
            if reserved_spins >= 80:
                print("acm seat stayed reserved; stop without stealing", flush=True)
                return 3
            time.sleep(2)
            continue
        reserved_spins = 0
        try:
            publish_one(FACTORY, n, idx)
        except subprocess.CalledProcessError as exc:
            print(exc.stdout, exc.stderr, flush=True)
            if reserved(FACTORY, n):
                print("lost race on reserve; retry without stealing", flush=True)
                time.sleep(1)
                continue
            print("reserve/mill/publish failed without seat", flush=True)
            return 5
        done += 1
        published.append(n)
        print(f"published acm r{n} ({done}/{max_rounds}) idx={idx}", flush=True)
    print(
        json.dumps(
            {
                "published": done,
                "rounds": published,
                "frontier": frontier(FACTORY),
                "unused_left": len(_mill.unused_pairs()),
            }
        ),
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
