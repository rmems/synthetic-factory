#!/usr/bin/env python3
"""Reserve → mill → publish db-migration-repair-factory r1014+ until catalog.

Do not exit after one batch. If this factory is reserved, hop another
unreserved named factory (never sandbox-refusal, never steal).
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MILL = ROOT / "experiments" / "dbm-mill-r1014.py"
TXN = ROOT / "pipelines" / "round_txn.py"
FACTORY = ROOT / "outputs" / "raw" / "2026-08-19-agentic" / "db-migration-repair-factory"
AGENTIC = FACTORY.parent
NEVER_HOP = {
    "sandbox-refusal-factory",
    "eval-harness-trajectory-factory",
}

import importlib.util

_spec = importlib.util.spec_from_file_location("dbm_mill_r1014", MILL)
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
    return json.loads(proc.stdout)["next_round"]


def reserved(factory: Path, n: int) -> bool:
    return (factory / f"ROUND-r{n:02d}.reserved.json").exists()


def hop_target() -> Path | None:
    for path in sorted(AGENTIC.iterdir()):
        if not path.is_dir() or path.name in NEVER_HOP:
            continue
        if path.name == FACTORY.name:
            continue
        try:
            n = frontier(path)
        except (subprocess.CalledProcessError, json.JSONDecodeError, KeyError):
            continue
        if not reserved(path, n):
            return path
    return None


def main() -> int:
    max_rounds = int(sys.argv[1]) if len(sys.argv) > 1 else CATALOG_LEN
    done = 0
    hops = 0
    published: list[int] = []
    while done < max_rounds:
        n = frontier(FACTORY)
        last = CATALOG_FIRST + CATALOG_LEN - 1
        if n < CATALOG_FIRST:
            print(f"frontier {n} before catalog {CATALOG_FIRST}; wait", flush=True)
            return 7
        if n > last:
            print(f"catalog exhausted at frontier {n} (last {last})", flush=True)
            break
        if reserved(FACTORY, n):
            hop = hop_target()
            hops += 1
            print(f"db-migration r{n} already reserved; hop={hop}", flush=True)
            if hop is None:
                print("no unreserved hop target; stop", flush=True)
                return 2
            print("named hop has no mill in this loop; never steal", flush=True)
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
            mill = run([sys.executable, str(MILL), "--round", str(n), "--staging", staging])
            sys.stderr.write(mill.stderr or "")
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
            print(pub.stdout, flush=True)
        except subprocess.CalledProcessError as exc:
            print(exc.stdout, exc.stderr, flush=True)
            print(f"mill/publish failed for r{n}; abort reservation", flush=True)
            run(
                [
                    sys.executable,
                    str(TXN),
                    "abort",
                    str(FACTORY),
                    "--round",
                    str(n),
                    "--token",
                    token,
                ],
                check=False,
            )
            return 6
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
