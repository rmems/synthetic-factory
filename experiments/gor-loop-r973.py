#!/usr/bin/env python3
"""Reserve → mill → publish git-ops-recovery-factory until catalog or max_rounds."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MILL = ROOT / "experiments" / "gor-mill-r973.py"
TXN = ROOT / "pipelines" / "round_txn.py"
FACTORY = ROOT / "outputs" / "raw" / "2026-08-19-agentic" / "git-ops-recovery-factory"
HOP = ROOT / "outputs" / "raw" / "2026-08-19-agentic" / "secret-scan-remediation-factory"

import importlib.util

_spec = importlib.util.spec_from_file_location("gor_mill_r973", MILL)
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
    proc = run([sys.executable, TXN, "frontier", factory])
    return json.loads(proc.stdout)["next_round"]


def reserved(factory: Path, n: int) -> bool:
    return (factory / f"ROUND-r{n:02d}.reserved.json").exists()


def main() -> int:
    max_rounds = int(sys.argv[1]) if len(sys.argv) > 1 else 12
    done = 0
    hops = 0
    published: list[int] = []
    while done < max_rounds:
        n = frontier(FACTORY)
        last = CATALOG_FIRST + CATALOG_LEN - 1
        if n > last:
            print(f"catalog exhausted at frontier {n} (last {last})", flush=True)
            break
        if reserved(FACTORY, n):
            print(f"git-ops r{n} already reserved; hop secret-scan", flush=True)
            hn = frontier(HOP)
            if reserved(HOP, hn):
                print("secret-scan also reserved; stop", flush=True)
                return 2
            hops += 1
            print("secret-scan hop not implemented in this mill; never steal; stop", flush=True)
            return 3
        try:
            proc = run(
                [
                    sys.executable,
                    TXN,
                    "reserve",
                    FACTORY,
                    "--round",
                    str(n),
                    "--expected",
                    "2",
                ]
            )
        except subprocess.CalledProcessError as exc:
            print(exc.stdout, exc.stderr, flush=True)
            if reserved(FACTORY, n):
                print("lost race on reserve; never steal", flush=True)
                return 4
            print("reserve failed", flush=True)
            return 5
        payload = json.loads(proc.stdout)
        token = payload["token"]
        staging = payload["staging_dir"]
        print(f"reserved r{n} token={token} staging={staging}", flush=True)
        try:
            mill = run([sys.executable, MILL, "--round", str(n), "--staging", staging])
            sys.stderr.write(mill.stderr or "")
            pub = run(
                [
                    sys.executable,
                    TXN,
                    "publish",
                    FACTORY,
                    "--round",
                    str(n),
                    "--token",
                    token,
                ]
            )
        except subprocess.CalledProcessError as exc:
            print(exc.stdout, exc.stderr, flush=True)
            print(f"mill/publish failed for r{n}; abort reservation", flush=True)
            run(
                [
                    sys.executable,
                    TXN,
                    "abort",
                    FACTORY,
                    "--round",
                    str(n),
                    "--token",
                    token,
                ],
                check=False,
            )
            return 6
        print(pub.stdout, flush=True)
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
