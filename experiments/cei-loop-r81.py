#!/usr/bin/env python3
"""Hop mill: csv-excel-ingest-factory r81+ while SSR is reserved.

Never steal SSR. Never sandbox-refusal. Writes only via round_txn reserve/publish.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MILL = ROOT / "experiments" / "cei-mill-r81.py"
SSR_MILL = ROOT / "experiments" / "ssr-mill-r554.py"
TXN = ROOT / "pipelines" / "round_txn.py"
AGENTIC = ROOT / "outputs" / "raw" / "2026-08-19-agentic"
CEI = AGENTIC / "csv-excel-ingest-factory"
SSR = AGENTIC / "secret-scan-remediation-factory"
NEVER_HOP = {"sandbox-refusal-factory"}

import importlib.util

_spec = importlib.util.spec_from_file_location("cei81", MILL)
_mill = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(_mill)
CATALOG_FIRST = _mill.CATALOG_FIRST
CATALOG_LEN = len(_mill.PAIRS)

_ssr_spec = importlib.util.spec_from_file_location("ssr554", SSR_MILL)
_ssr = importlib.util.module_from_spec(_ssr_spec)
assert _ssr_spec.loader is not None
_ssr_spec.loader.exec_module(_ssr)
SSR_FIRST = _ssr.CATALOG_FIRST
SSR_LAST = SSR_FIRST + len(_ssr.PAIRS) - 1


def run(args, check=True):
    print("+", " ".join(str(a) for a in args), flush=True)
    return subprocess.run([str(a) for a in args], cwd=ROOT, check=check, text=True, capture_output=True)


def frontier(factory: Path) -> int:
    proc = run([sys.executable, str(TXN), "frontier", str(factory)])
    print(proc.stdout, flush=True)
    return json.loads(proc.stdout)["next_round"]


def reserved(factory: Path, n: int) -> bool:
    return (factory / f"ROUND-r{n:02d}.reserved.json").exists()


def mill_publish(factory: Path, mill: Path, n: int) -> None:
    proc = run([sys.executable, str(TXN), "reserve", str(factory), "--round", str(n), "--expected", "2"])
    print(proc.stdout, flush=True)
    payload = json.loads(proc.stdout)
    millp = run([sys.executable, str(mill), "--round", str(n), "--staging", payload["staging_dir"]])
    print(millp.stdout, flush=True)
    pub = run([sys.executable, str(TXN), "publish", str(factory), "--round", str(n), "--token", payload["token"]])
    print(pub.stdout, flush=True)


def main() -> int:
    max_rounds = int(sys.argv[1]) if len(sys.argv) > 1 else CATALOG_LEN
    done = 0
    published = []
    while done < max_rounds:
        ssr_n = frontier(SSR)
        if SSR_FIRST <= ssr_n <= SSR_LAST and not reserved(SSR, ssr_n):
            try:
                mill_publish(SSR, SSR_MILL, ssr_n)
            except subprocess.CalledProcessError as exc:
                print(exc.stdout, exc.stderr, flush=True)
                print("ssr reserve/mill failed; stay on hop", flush=True)
            else:
                published.append(("ssr", ssr_n))
                done += 1
                print(f"published ssr r{ssr_n}", flush=True)
                continue
        n = frontier(CEI)
        last = CATALOG_FIRST + CATALOG_LEN - 1
        if n > last:
            print(f"cei catalog exhausted at {n}", flush=True)
            break
        if n < CATALOG_FIRST:
            print(f"cei frontier {n} before catalog", flush=True)
            return 2
        if reserved(CEI, n):
            print(f"cei r{n} reserved; stop hop (never steal)", flush=True)
            return 4
        try:
            mill_publish(CEI, MILL, n)
        except subprocess.CalledProcessError as exc:
            print(exc.stdout, exc.stderr, flush=True)
            print("cei mill failed", flush=True)
            return 5
        published.append(("cei", n))
        done += 1
        print(f"published cei r{n} ({done}/{max_rounds})", flush=True)
    print(json.dumps({"published": published, "frontier_cei": frontier(CEI), "frontier_ssr": frontier(SSR)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
