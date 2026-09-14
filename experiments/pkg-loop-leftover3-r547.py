#!/usr/bin/env python3
"""16-round reserve/publish for leftover leftover leftover mill r547+."""
from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MILL = ROOT / "experiments" / "pkg-mill-leftover3-r547.py"
TXN = ROOT / "pipelines" / "round_txn.py"
FACTORY = ROOT / "outputs" / "raw" / "2026-08-19-agentic" / "package-release-factory"
TARGET = int(__import__("os").environ.get("PAIR_COUNT", "16"))


def run(args, check=True):
    print("+", " ".join(str(a) for a in args), flush=True)
    return subprocess.run([str(a) for a in args], cwd=ROOT, check=check, text=True, capture_output=True)


def frontier(factory: Path) -> dict:
    return json.loads(run([sys.executable, str(TXN), "frontier", str(factory)]).stdout)


def reserved_path(factory: Path, n: int) -> Path:
    return factory / f"ROUND-r{n:02d}.reserved.json"


def publish_round(factory: Path, mill: Path, n: int, pair: int) -> None:
    proc = run(
        [sys.executable, str(TXN), "reserve", str(factory), "--round", str(n), "--expected", "2"],
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError((proc.stderr or proc.stdout or "reserve failed").strip())
    payload = json.loads(proc.stdout)
    token, staging = payload["token"], payload["staging_dir"]
    print(f"reserved {factory.name} r{n} token={token} pair={pair}", flush=True)
    try:
        mill_out = run([sys.executable, str(mill), "--round", str(n), "--pair", str(pair), "--staging", staging])
        print(mill_out.stdout, flush=True)
        pub = run([sys.executable, str(TXN), "publish", str(factory), "--round", str(n), "--token", token])
        print(pub.stdout, flush=True)
    except subprocess.CalledProcessError as exc:
        print(exc.stdout or "", exc.stderr or "", flush=True)
        run([sys.executable, str(TXN), "abort", str(factory), "--round", str(n), "--token", token], check=False)
        raise


def main() -> int:
    sc = run([sys.executable, str(MILL), "--selfcheck"])
    print(sc.stdout, flush=True)
    start = int(__import__("os").environ.get("PAIR_START", "0"))
    done = 0
    published: list[str] = []
    while done < TARGET:
        status = frontier(FACTORY)
        n = status["next_round"]
        if reserved_path(FACTORY, n).exists():
            print(f"package-release r{n} reserved; never steal; retry frontier", flush=True)
            time.sleep(0.05)
            continue
        try:
            publish_round(FACTORY, MILL, n, start + done)
        except RuntimeError as exc:
            print(f"reserve race r{n}: {exc}; retry", flush=True)
            time.sleep(0.05)
            continue
        done += 1
        published.append(f"pkg-r{n}")
        print(f"published {n} ({done}/{TARGET})", flush=True)
    print(json.dumps({"published": published, "count": done}))
    return 0 if done == TARGET else 1


if __name__ == "__main__":
    raise SystemExit(main())
