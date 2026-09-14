#!/usr/bin/env python3
"""Continue unique OpenAPI-drift ACM after r4102 catalog dies. Do not exit after one mill."""
from __future__ import annotations

import importlib.util
import json
import py_compile
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TXN = ROOT / "pipelines" / "round_txn.py"
FACTORY = ROOT / "outputs" / "raw" / "2026-08-19-agentic" / "api-contract-migration-factory"
AGENTIC = FACTORY.parent
MILLS = [
    ROOT / "experiments" / "acm-mill-r4118.py",
]


def load_mill(path: Path):
    py_compile.compile(str(path), doraise=True)
    spec = importlib.util.spec_from_file_location(path.stem.replace("-", "_"), path)
    mill = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mill)
    mill.catalog_selfcheck()
    return mill


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


def publish_one(mill_path: Path, n: int, idx: int) -> None:
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
            str(mill_path),
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


def hop_if_reserved(n: int, reserved_spins: int) -> int:
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
    return reserved_spins + 1


def run_mill(mill_path: Path, deadline: float) -> list[int]:
    mill = load_mill(mill_path)
    published: list[int] = []
    reserved_spins = 0
    print(
        json.dumps(
            {
                "mill": mill_path.name,
                "catalog": len(mill.PAIRS),
                "unused": len(mill.unused_pairs()),
            }
        ),
        flush=True,
    )
    while time.time() < deadline:
        idx = mill.next_free_idx()
        if idx is None:
            print(f"{mill_path.stem} OpenAPI drift catalog exhausted", flush=True)
            break
        n = frontier(FACTORY)
        if reserved(FACTORY, n) or writing(FACTORY, n):
            reserved_spins = hop_if_reserved(n, reserved_spins)
            if reserved_spins >= 80:
                raise SystemExit(3)
            time.sleep(2)
            continue
        reserved_spins = 0
        try:
            publish_one(mill_path, n, idx)
        except subprocess.CalledProcessError as exc:
            print(exc.stdout, exc.stderr, flush=True)
            if reserved(FACTORY, n):
                time.sleep(1)
                continue
            raise SystemExit(5)
        published.append(n)
        print(
            f"published acm r{n} ({len(published)}/{len(mill.PAIRS)}) idx={idx} mill={mill_path.name}",
            flush=True,
        )
    return published


def main() -> int:
    deadline = time.time() + 6 * 60 * 60
    all_pub: list[int] = []
    for mill_path in MILLS:
        if time.time() >= deadline:
            break
        all_pub.extend(run_mill(mill_path, deadline))
    print(json.dumps({"published": len(all_pub), "rounds": all_pub}), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
