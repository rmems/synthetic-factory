#!/usr/bin/env python3
"""Prefer llm-eval-flakiness; hop ssl-cert-rotation if LEF seat is reserved.

Never steal a reservation. Never eval-harness. Writes only via round_txn.py.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TXN = ROOT / "pipelines" / "round_txn.py"
AGENTIC = ROOT / "outputs" / "raw" / "2026-08-19-agentic"
LEF = AGENTIC / "llm-eval-flakiness-factory"
SSL = AGENTIC / "ssl-cert-rotation-factory"
SIR = AGENTIC / "search-index-rebuild-factory"
LEF_MILL = ROOT / "experiments" / "lef-mill-r629.py"
SSL_MILL = ROOT / "experiments" / "ssl-mill-r35.py"
SIR_MILL = ROOT / "experiments" / "sir-mill-r31.py"


def run(args: list[str], timeout: int = 1800) -> subprocess.CompletedProcess:
    print("+", " ".join(str(a) for a in args), flush=True)
    return subprocess.run(
        [str(a) for a in args],
        cwd=str(ROOT),
        check=True,
        text=True,
        capture_output=True,
        timeout=timeout,
    )


def frontier(factory: Path) -> int:
    proc = run([sys.executable, str(TXN), "frontier", str(factory)])
    nxt = json.loads(proc.stdout)["next_round"]
    print(f"frontier {factory.name} next={nxt}", flush=True)
    return nxt


def reserved(factory: Path, n: int) -> bool:
    return (factory / f"ROUND-r{n:02d}.reserved.json").exists()


def publish(factory: Path, n: int, mill: Path) -> None:
    proc = run(
        [sys.executable, str(TXN), "reserve", str(factory), "--round", str(n), "--expected", "2"]
    )
    payload = json.loads(proc.stdout)
    print(proc.stdout, flush=True)
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
                [sys.executable, str(TXN), "abort", str(factory), "--round", str(n), "--token", token],
                timeout=120,
            )
        except Exception as exc:
            print(f"abort failed r{n}: {exc}", flush=True)
        raise


def lef_in_catalog(n: int) -> bool:
    return 629 <= n <= 772


def ssl_in_catalog(n: int) -> bool:
    return 35 <= n <= 65


def sir_in_catalog(n: int) -> bool:
    return 31 <= n <= 46


def main() -> int:
    max_rounds = int(sys.argv[1]) if len(sys.argv) > 1 else 80
    done = []
    hops = []
    spins = 0
    while len(done) + len(hops) < max_rounds and spins < 40:
        n = frontier(LEF)
        if not reserved(LEF, n) and lef_in_catalog(n):
            try:
                publish(LEF, n, LEF_MILL)
            except subprocess.CalledProcessError as exc:
                print(exc.stdout or "", exc.stderr or "", flush=True)
                if reserved(LEF, n):
                    print(f"lost LEF r{n}; hop", flush=True)
                else:
                    return 5
            else:
                done.append(n)
                spins = 0
                print(f"published LEF r{n} ({len(done)})", flush=True)
                continue
        if reserved(LEF, n) or not lef_in_catalog(n):
            sn = frontier(SSL)
            if not reserved(SSL, sn) and ssl_in_catalog(sn):
                try:
                    publish(SSL, sn, SSL_MILL)
                except subprocess.CalledProcessError as exc:
                    print(exc.stdout or "", exc.stderr or "", flush=True)
                    if reserved(SSL, sn):
                        print(f"lost SSL r{sn}", flush=True)
                        spins += 1
                        continue
                    return 6
                hops.append(("ssl", sn))
                spins = 0
                print(f"hop published SSL r{sn} ({len(hops)})", flush=True)
                continue
            hn = frontier(SIR)
            if not reserved(SIR, hn) and sir_in_catalog(hn):
                try:
                    publish(SIR, hn, SIR_MILL)
                except subprocess.CalledProcessError as exc:
                    print(exc.stdout or "", exc.stderr or "", flush=True)
                    if reserved(SIR, hn):
                        print(f"lost SIR r{hn}", flush=True)
                        spins += 1
                        continue
                    return 7
                hops.append(("sir", hn))
                spins = 0
                print(f"hop published SIR r{hn} ({len(hops)})", flush=True)
                continue
            spins += 1
            print(f"seats blocked or catalog end (spin {spins})", flush=True)
            if not lef_in_catalog(n) and not ssl_in_catalog(sn) and not sir_in_catalog(hn):
                break
    print(json.dumps({"lef": done, "ssl_hops": hops, "spins": spins}), flush=True)
    return 0 if done or hops else 1


if __name__ == "__main__":
    raise SystemExit(main())
