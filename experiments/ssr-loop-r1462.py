#!/usr/bin/env python3
"""Reserve → mill → publish secret-scan-remediation-factory r1462+ mill.

Keep looping until catalog exhausts. Never steal; never sandbox-refusal.
If this factory is reserved, hop another unreserved named factory (no mill).
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MILL = ROOT / "experiments" / "ssr-mill-r1462.py"
TXN = ROOT / "pipelines" / "round_txn.py"
AGENTIC = ROOT / "outputs" / "raw" / "2026-08-19-agentic"
FACTORY = AGENTIC / "secret-scan-remediation-factory"
NEVER_HOP = {"sandbox-refusal-factory"}

_catalog = json.loads((ROOT / "experiments" / ".ssr-catalog-r1462.json").read_text())
CATALOG_FIRST = _catalog["catalog_first"]
CATALOG_LEN = len(_catalog["pairs"])


def run(args, check=True):
    print("+", " ".join(str(a) for a in args), flush=True)
    return subprocess.run([str(a) for a in args], cwd=ROOT, check=check, text=True, capture_output=True)


def frontier(factory: Path) -> int:
    highest = 0
    for p in factory.glob("ROUND-r*.complete.json"):
        try:
            num = int(p.name[len("ROUND-r"):].split(".", 1)[0])
        except ValueError:
            continue
        if num > highest:
            highest = num
    return highest + 1


def reserved(factory: Path, n: int) -> bool:
    return (factory / f"ROUND-r{n:02d}.reserved.json").exists()


def hop_target() -> Path | None:
    for child in sorted(AGENTIC.iterdir()):
        if not child.is_dir():
            continue
        if child.name in NEVER_HOP or child == FACTORY:
            continue
        n = frontier(child)
        if reserved(child, n):
            continue
        return child
    return None


def main() -> int:
    max_rounds = int(sys.argv[1]) if len(sys.argv) > 1 else CATALOG_LEN
    done = 0
    published = []
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
            print(f"secret-scan r{n} already reserved; hop (never steal)", flush=True)
            other = hop_target()
            if other is None:
                print("no unreserved hop target; stop (never steal)", flush=True)
                return 4
            print(f"{other.name} unreserved; no mill in this seat; stop hop", flush=True)
            return 4
        try:
            proc = run([sys.executable, str(TXN), "reserve", str(FACTORY), "--round", str(n), "--expected", "2"])
        except subprocess.CalledProcessError as exc:
            print(exc.stdout, exc.stderr, flush=True)
            return 5
        payload = json.loads(proc.stdout)
        print(proc.stdout, flush=True)
        try:
            mill = run([sys.executable, str(MILL), "--round", str(n), "--staging", payload["staging_dir"]])
            print(mill.stdout, flush=True)
            pub = run([sys.executable, str(TXN), "publish", str(FACTORY), "--round", str(n), "--token", payload["token"]])
        except subprocess.CalledProcessError as exc:
            print(exc.stdout, exc.stderr, flush=True)
            return 6
        print(pub.stdout, flush=True)
        done += 1
        published.append(n)
        print(f"published r{n} ({done}/{max_rounds})", flush=True)
    print(json.dumps({"published": done, "rounds": published, "frontier": frontier(FACTORY)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
