#!/usr/bin/env python3
"""Reserve → mill → publish secret-scan-remediation-factory r252+ until catalog dies."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MILL = ROOT / "experiments" / "ssr-mill-r252.py"
TXN = ROOT / "pipelines" / "round_txn.py"
FACTORY = ROOT / "outputs" / "raw" / "2026-08-19-agentic" / "secret-scan-remediation-factory"

import importlib.util

_spec = importlib.util.spec_from_file_location("ssr_mill_r252", MILL)
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
    proc = run([sys.executable, str(TXN), "frontier", str(factory)])
    print(proc.stdout, flush=True)
    return json.loads(proc.stdout)["next_round"]


def reserved(factory: Path, n: int) -> bool:
    return (factory / f"ROUND-r{n:02d}.reserved.json").exists()


def main() -> int:
    max_rounds = int(sys.argv[1]) if len(sys.argv) > 1 else CATALOG_LEN
    done = 0
    published: list[int] = []
    while done < max_rounds:
        n = frontier(FACTORY)
        last = CATALOG_FIRST + CATALOG_LEN - 1
        if n > last:
            print(f"catalog exhausted at frontier {n} (last={last})", flush=True)
            break
        if n < CATALOG_FIRST:
            print(f"frontier {n} before catalog {CATALOG_FIRST}", flush=True)
            return 2
        if reserved(FACTORY, n):
            print(f"secret-scan r{n} already reserved; stop", flush=True)
            return 3
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
            print("reserve failed", flush=True)
            return 5
        payload = json.loads(proc.stdout)
        print(proc.stdout, flush=True)
        token = payload["token"]
        staging = payload["staging_dir"]
        try:
            mill = run([sys.executable, str(MILL), "--round", str(n), "--staging", staging])
            sys.stderr.write(mill.stderr or "")
            print(mill.stdout, flush=True)
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
                ]
            )
        except subprocess.CalledProcessError as exc:
            print(exc.stdout, exc.stderr, flush=True)
            print(f"mill/publish failed for r{n}", flush=True)
            return 6
        print(pub.stdout, flush=True)
        done += 1
        published.append(n)
        print(f"published r{n} ({done}/{max_rounds})", flush=True)
    print(json.dumps({"published": done, "rounds": published, "frontier": frontier(FACTORY)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
