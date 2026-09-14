#!/usr/bin/env python3
"""Continue leftover leftover leftover unique ACM after r3714 catalog dies."""
from __future__ import annotations

import json
import py_compile
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MILL = ROOT / "experiments" / "acm-mill-r3787.py"
TXN = ROOT / "pipelines" / "round_txn.py"
FACTORY = ROOT / "outputs" / "raw" / "2026-08-19-agentic" / "api-contract-migration-factory"
AGENTIC = FACTORY.parent

import importlib.util

py_compile.compile(str(MILL), doraise=True)
_spec = importlib.util.spec_from_file_location("acm_mill_r3787", MILL)
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
    n = json.loads(proc.stdout)["next_round"]
    print(json.dumps({"next_round": n, "factory": factory.name}), flush=True)
    return n


def reserved(factory: Path, n: int) -> bool:
    return (factory / f"ROUND-r{n:02d}.reserved.json").exists()


def writing(factory: Path, n: int) -> bool:
    return (factory / f"ROUND-r{n:02d}.publishing.json").exists()


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
    mill_proc = run(
        [
            sys.executable,
            str(MILL),
            "--round",
            str(n),
            "--staging",
            payload["staging_dir"],
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
            payload["token"],
        ]
    )
    print(pub.stdout, flush=True)


def main() -> int:
    _mill.catalog_selfcheck()
    max_rounds = int(sys.argv[1]) if len(sys.argv) > 1 else 16
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
            print("acm r3787 leftover leftover leftover catalog exhausted", flush=True)
            break
        n = frontier(FACTORY)
        if reserved(FACTORY, n) or writing(FACTORY, n):
            reserved_spins += 1
            hops = []
            for path in sorted(AGENTIC.iterdir()):
                if not path.is_dir() or path.name in {
                    FACTORY.name,
                    "sandbox-refusal-factory",
                    "eval-harness-trajectory-factory",
                }:
                    continue
                try:
                    hn = frontier(path)
                except Exception:
                    continue
                if reserved(path, hn) or writing(path, hn):
                    continue
                hops.append(path.name)
            print(
                json.dumps(
                    {"acm_reserved": True, "round": n, "spin": reserved_spins, "hops": hops[:8]}
                ),
                flush=True,
            )
            if reserved_spins >= 80:
                return 3
            time.sleep(2)
            continue
        reserved_spins = 0
        try:
            publish_one(n, idx)
        except subprocess.CalledProcessError as exc:
            print(exc.stdout, exc.stderr, flush=True)
            if reserved(FACTORY, n):
                time.sleep(1)
                continue
            return 5
        done += 1
        published.append(n)
        print(f"published acm r{n} ({done}/{max_rounds}) idx={idx}", flush=True)
    print(json.dumps({"published": done, "rounds": published}), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
