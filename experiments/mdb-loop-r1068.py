#!/usr/bin/env python3
"""Reserve → mill → publish mdb from first unreserved frontier. No steal. No idle."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MILL = ROOT / "experiments" / "mdb-mill-r1068.py"
TXN = ROOT / "pipelines" / "round_txn.py"
FACTORY = ROOT / "outputs" / "raw" / "2026-08-19-agentic" / "monorepo-dep-bump-factory"

import importlib.util


def run(args: list[str], check: bool = True) -> subprocess.CompletedProcess:
    print("+", " ".join(str(a) for a in args), flush=True)
    return subprocess.run(
        [str(a) for a in args], cwd=ROOT, check=check, text=True, capture_output=True
    )


def frontier() -> int:
    proc = run([sys.executable, str(TXN), "frontier", str(FACTORY)])
    nxt = json.loads(proc.stdout)["next_round"]
    print(f"frontier next_round={nxt}", flush=True)
    return nxt


def catalog_last() -> tuple[int, int]:
    spec = importlib.util.spec_from_file_location("mill_live", MILL)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    first = mod.CATALOG_FIRST
    return first, first + len(mod.PAIRS) - 1


def main() -> int:
    max_rounds = int(sys.argv[1]) if len(sys.argv) > 1 else 16
    done = 0
    published: list[str] = []
    first, last = catalog_last()
    while done < max_rounds:
        n = frontier()
        if n > last:
            print(f"catalog exhausted frontier={n} last={last}", flush=True)
            break
        if n < first:
            print(f"frontier {n} < catalog first {first}; stop (would misalign)", flush=True)
            break
        if (FACTORY / f"ROUND-r{n:02d}.reserved.json").exists():
            print(f"r{n} reserved; skip steal", flush=True)
            continue
        try:
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
        except subprocess.CalledProcessError as exc:
            print(exc.stdout, exc.stderr, flush=True)
            continue
        payload = json.loads(proc.stdout)
        token = payload["token"]
        staging = payload["staging_dir"]
        print(f"reserved r{n} token={token}", flush=True)
        mill_proc = run(
            [sys.executable, str(MILL), "--round", str(n), "--staging", staging],
            check=False,
        )
        print(mill_proc.stdout, mill_proc.stderr, flush=True)
        if mill_proc.returncode != 0:
            return 4
        pub = run(
            [
                sys.executable,
                str(TXN),
                "publish",
                str(FACTORY),
                "--round",
                str(n),
                "--token",
                token,
            ],
            check=False,
        )
        print(pub.stdout, pub.stderr, flush=True)
        if pub.returncode != 0:
            continue
        done += 1
        published.append(f"mdb-r{n}")
        print(f"published r{n} ({done}/{max_rounds})", flush=True)
    print(json.dumps({"published": done, "rounds": published, "frontier": frontier()}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
