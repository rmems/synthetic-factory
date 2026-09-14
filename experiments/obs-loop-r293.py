#!/usr/bin/env python3
"""observability-debug-factory r293+ loop until catalog/quota dies.

Never steal. Never rewrite raw. Never hop to sandbox-refusal if reserved/writing.
Writes only via pipelines/round_txn.py reserve --expected 2 / publish.
Does not exit after one batch.
"""
from __future__ import annotations

import json
import py_compile
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MILL = ROOT / "experiments" / "obs-mill-r293.py"
TXN = ROOT / "pipelines" / "round_txn.py"
AGENTIC = ROOT / "outputs" / "raw" / "2026-08-19-agentic"
FACTORY = AGENTIC / "observability-debug-factory"
SKIP_IF_RESERVED = frozenset({"sandbox-refusal-factory", "eval-harness-trajectory-factory"})

import importlib.util

py_compile.compile(str(MILL), doraise=True)
py_compile.compile(str(ROOT / "experiments" / "obs-mill-plants-r293.py"), doraise=True)
_spec = importlib.util.spec_from_file_location("obs_mill_r293", MILL)
_mill = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(_mill)
CATALOG_FIRST = _mill.CATALOG_FIRST
CATALOG_LEN = len(_mill.PAIRS)
CATALOG_LAST = CATALOG_FIRST + CATALOG_LEN - 1

HOP_MILLS = [
    (AGENTIC / "llm-eval-flakiness-factory", ROOT / "experiments" / "lef-mill-r728.py", 728, 847),
    (AGENTIC / "ssl-cert-rotation-factory", ROOT / "experiments" / "ssl-mill-r35.py", 35, 105),
    (AGENTIC / "package-release-factory", ROOT / "experiments" / "pkg-mill-r296.py", 296, 400),
]


def run(args: list[str], check: bool = True, timeout: int = 1800) -> subprocess.CompletedProcess:
    print("+", " ".join(str(a) for a in args), flush=True)
    return subprocess.run(
        [str(a) for a in args],
        cwd=str(ROOT),
        check=check,
        text=True,
        capture_output=True,
        timeout=timeout,
    )


def frontier(factory: Path) -> int:
    proc = run([sys.executable, str(TXN), "frontier", str(factory)])
    print(proc.stdout, flush=True)
    return json.loads(proc.stdout)["next_round"]


def reserved(factory: Path, n: int) -> bool:
    return (factory / f"ROUND-r{n:02d}.reserved.json").exists()


def writing(factory: Path) -> bool:
    return any(factory.glob("ROUND-r*.reserved.json"))


def publish_one(factory: Path, n: int, mill: Path) -> None:
    proc = run(
        [sys.executable, str(TXN), "reserve", str(factory), "--round", str(n), "--expected", "2"]
    )
    print(proc.stdout, flush=True)
    payload = json.loads(proc.stdout)
    token = payload["token"]
    stage = payload["staging_dir"]
    try:
        mill_proc = run([sys.executable, str(mill), "--round", str(n), "--staging", stage])
        print(mill_proc.stdout, flush=True)
        pub = run(
            [sys.executable, str(TXN), "publish", str(factory), "--round", str(n), "--token", token]
        )
        print(pub.stdout, flush=True)
    except Exception:
        try:
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
                timeout=120,
            )
        except Exception as exc:
            print(f"abort failed r{n}: {exc}", flush=True)
        raise


def try_obs() -> str | None:
    n = frontier(FACTORY)
    if reserved(FACTORY, n):
        print(f"obs r{n} reserved; hop without steal", flush=True)
        return None
    if n < CATALOG_FIRST:
        print(f"obs r{n} before mill first={CATALOG_FIRST}; skip", flush=True)
        return None
    if n > CATALOG_LAST:
        print(f"obs catalog exhausted at frontier {n} (last={CATALOG_LAST})", flush=True)
        return None
    try:
        publish_one(FACTORY, n, MILL)
    except subprocess.CalledProcessError as exc:
        print(exc.stdout or "", exc.stderr or "", flush=True)
        print(f"obs r{n} reserve/publish failed", flush=True)
        return None
    return f"obs-r{n}"


def try_hop() -> str | None:
    for factory, mill, first, last in HOP_MILLS:
        if factory.name in SKIP_IF_RESERVED and (writing(factory) or reserved(factory, frontier(factory))):
            print(f"skip {factory.name}: reserved/writing", flush=True)
            continue
        if writing(factory):
            print(f"{factory.name} writing; skip hop", flush=True)
            continue
        if not mill.exists():
            continue
        n = frontier(factory)
        if reserved(factory, n):
            print(f"{factory.name} r{n} reserved; skip hop", flush=True)
            continue
        if n < first or n > last:
            print(f"{factory.name} r{n} outside mill {first}-{last}; skip", flush=True)
            continue
        try:
            py_compile.compile(str(mill), doraise=True)
            publish_one(factory, n, mill)
        except subprocess.CalledProcessError as exc:
            print(exc.stdout or "", exc.stderr or "", flush=True)
            print(f"hop {factory.name} r{n} failed", flush=True)
            continue
        return f"{factory.name}-r{n}"
    return None


def main() -> int:
    max_rounds = int(sys.argv[1]) if len(sys.argv) > 1 else 200
    done: list[str] = []
    spins = 0
    print(
        f"obs r293 loop catalog={CATALOG_LEN} first={CATALOG_FIRST} last={CATALOG_LAST}",
        flush=True,
    )
    while len(done) < max_rounds and spins < 40:
        hit = try_obs()
        if hit:
            done.append(hit)
            spins = 0
            print(f"LOOP published {hit} ({len(done)})", flush=True)
            continue
        n = frontier(FACTORY)
        if n <= CATALOG_LAST and not reserved(FACTORY, n):
            spins += 1
            print(f"obs seat blocked (spin {spins})", flush=True)
            continue
        hit = try_hop()
        if hit:
            done.append(hit)
            spins = 0
            print(f"HOP published {hit} ({len(done)})", flush=True)
            continue
        spins += 1
        print(f"seats blocked or catalog end (spin {spins})", flush=True)
        if n > CATALOG_LAST:
            break
        if spins >= 8:
            break
    print(json.dumps({"done": done, "spins": spins, "last": CATALOG_LAST}), flush=True)
    return 0 if done else 1


if __name__ == "__main__":
    raise SystemExit(main())
