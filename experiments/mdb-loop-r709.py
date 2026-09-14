#!/usr/bin/env python3
"""Reserve → mill → publish monorepo-dep-bump-factory until catalog or max_rounds.

Hop another unreserved named factory if the mdb seat is already reserved.
Never steal a reservation. Never rewrite raw. Skip eval-harness and
sandbox-refusal when reserved.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MILL = ROOT / "experiments" / "mdb-mill-r709.py"
TXN = ROOT / "pipelines" / "round_txn.py"
DATE = ROOT / "outputs" / "raw" / "2026-08-19-agentic"
FACTORY = DATE / "monorepo-dep-bump-factory"
HOP_SKIP = {
    "eval-harness-trajectory-factory",
    "sandbox-refusal-factory",
}

import importlib.util

_spec = importlib.util.spec_from_file_location("mdb_mill_r709", MILL)
_mill = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(_mill)
CATALOG_FIRST = _mill.CATALOG_FIRST
CATALOG_LEN = len(_mill.PAIRS)


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


def hop_target() -> Path | None:
    for path in sorted(DATE.iterdir()):
        if not path.is_dir() or path.name == FACTORY.name:
            continue
        if path.name in HOP_SKIP:
            continue
        if not (path / ".round-marker-mode.json").exists() and not list(
            path.glob("batch-r*.jsonl")
        ):
            continue
        try:
            n = frontier(path)
        except (subprocess.CalledProcessError, json.JSONDecodeError, KeyError):
            continue
        if reserved(path, n):
            continue
        return path
    return None


def publish_round(factory: Path, n: int, expected: int) -> None:
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
    spec = importlib.util.spec_from_file_location("mdb_mill_r709", MILL)
    mill = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mill)
    return mill.CATALOG_FIRST, len(mill.PAIRS)


def main() -> int:
    max_rounds = int(sys.argv[1]) if len(sys.argv) > 1 else 40
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
        if reserved(FACTORY, n):
            print(f"mdb r{n} already reserved; retry shortly (no steal)", flush=True)
            hops += 1
            # Tight retry: other mill sessions publish in seconds. Do not steal.
            import time

            time.sleep(2)
            continue
        try:
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
