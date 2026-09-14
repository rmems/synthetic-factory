#!/usr/bin/env python3
"""Prefer llm-eval-flakiness r968+; hop only if LEF seat is reserved.

Never steal. Never eval-harness. Never sandbox-refusal if reserved/writing.
Writes only via pipelines/round_txn.py reserve --expected 2 / publish.
Does not exit after one batch.
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
LEF_MILL = ROOT / "experiments" / "lef-mill-r968.py"

# ssl mill r112 ends 131; sir mill r52 ends ~71. Only hop if still in range.
SSL = AGENTIC / "ssl-cert-rotation-factory"
SIR = AGENTIC / "search-index-rebuild-factory"
SSL_MILL = ROOT / "experiments" / "ssl-mill-r112.py"
SIR_MILL = ROOT / "experiments" / "sir-mill-r52.py"

LEF_FIRST, LEF_LAST = 968, 2629
SSL_FIRST, SSL_LAST = 112, 131
SIR_FIRST, SIR_LAST = 52, 71
SKIP = frozenset({"sandbox-refusal-factory", "eval-harness-trajectory-factory"})


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


def writing(factory: Path) -> bool:
    return any(factory.glob("ROUND-r*.reserved.json"))


def publish(factory: Path, n: int, mill: Path) -> None:
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


def try_one(factory: Path, mill: Path, first: int, last: int, label: str) -> str | None:
    if factory.name in SKIP:
        return None
    if writing(factory) and factory is not LEF:
        print(f"{factory.name} reserved/writing; skip hop", flush=True)
        return None
    n = frontier(factory)
    if reserved(factory, n):
        print(f"{factory.name} r{n} reserved; skip", flush=True)
        return None
    if n < first or n > last:
        print(f"{factory.name} r{n} outside mill {first}-{last}; skip", flush=True)
        return None
    try:
        publish(factory, n, mill)
    except subprocess.CalledProcessError as exc:
        print(exc.stdout or "", exc.stderr or "", flush=True)
        if reserved(factory, n):
            print(f"lost {label} r{n}", flush=True)
            return None
        print(f"{label} r{n} mill/publish failed; stop this factory this pass", flush=True)
        return "FAIL"
    return f"{label}-r{n}"


def main() -> int:
    max_rounds = int(sys.argv[1]) if len(sys.argv) > 1 else 200
    done: list[str] = []
    spins = 0
    while len(done) < max_rounds and spins < 80:
        hit = try_one(LEF, LEF_MILL, LEF_FIRST, LEF_LAST, "lef")
        if hit and hit != "FAIL":
            done.append(hit)
            spins = 0
            print(f"published {hit} ({len(done)})", flush=True)
            continue
        hit = try_one(SSL, SSL_MILL, SSL_FIRST, SSL_LAST, "ssl")
        if hit and hit != "FAIL":
            done.append(hit)
            spins = 0
            print(f"hop published {hit} ({len(done)})", flush=True)
            continue
        hit = try_one(SIR, SIR_MILL, SIR_FIRST, SIR_LAST, "sir")
        if hit and hit != "FAIL":
            done.append(hit)
            spins = 0
            print(f"hop published {hit} ({len(done)})", flush=True)
            continue
        spins += 1
        print(f"seats blocked or catalog end (spin {spins})", flush=True)
        ln = frontier(LEF)
        if ln > LEF_LAST or reserved(LEF, ln):
            if spins >= 8:
                break
    print(json.dumps({"done": done, "spins": spins}), flush=True)
    return 0 if done else 1


if __name__ == "__main__":
    raise SystemExit(main())
