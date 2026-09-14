#!/usr/bin/env python3
"""Race monorepo-dep-bump reserve/mill/publish. Never steal. If reserved, hop-tick."""
from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MILL = ROOT / "experiments" / "mdb-mill-r840.py"
TXN = ROOT / "pipelines" / "round_txn.py"
FACTORY = ROOT / "outputs" / "raw" / "2026-08-19-agentic" / "monorepo-dep-bump-factory"


def run(args: list[str], check: bool = True) -> subprocess.CompletedProcess:
    print("+", " ".join(str(a) for a in args), flush=True)
    return subprocess.run(
        [str(a) for a in args],
        cwd=ROOT,
        check=check,
        text=True,
        capture_output=True,
    )


def frontier() -> int:
    proc = run([sys.executable, str(TXN), "frontier", str(FACTORY)])
    nxt = json.loads(proc.stdout)["next_round"]
    print(f"frontier next_round={nxt}", flush=True)
    return nxt


def reserved(n: int) -> bool:
    return (FACTORY / f"ROUND-r{n:02d}.reserved.json").exists()


def catalog_last() -> int:
    import importlib.util

    spec = importlib.util.spec_from_file_location("mdb_mill_live", MILL)
    mill = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mill)
    return mill.CATALOG_FIRST, mill.CATALOG_FIRST + len(mill.PAIRS) - 1


def main() -> int:
    max_rounds = int(sys.argv[1]) if len(sys.argv) > 1 else 16
    deadline = time.time() + 40 * 60
    done = 0
    published: list[int] = []
    hops = 0
    while done < max_rounds and time.time() < deadline:
        first, last = catalog_last()
        try:
            n = frontier()
        except Exception as exc:
            print(f"frontier failed: {exc}", flush=True)
            hops += 1
            continue
        if n > last:
            print(f"catalog exhausted at frontier {n} last={last}", flush=True)
            break
        if n < first:
            print(f"frontier {n} below catalog {first}; hop", flush=True)
            hops += 1
            break
        if reserved(n):
            print(f"r{n} reserved; hop-tick (no steal)", flush=True)
            hops += 1
            continue
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
            ],
            check=False,
        )
        if proc.returncode != 0:
            print((proc.stdout or "")[-400:], (proc.stderr or "")[-400:], flush=True)
            print(f"reserve miss r{n}; hop-tick", flush=True)
            hops += 1
            continue
        payload = json.loads(proc.stdout)
        token = payload["token"]
        staging = payload["staging_dir"]
        print(f"reserved r{n} token={token} staging={staging}", flush=True)
        mill_proc = run(
            [sys.executable, str(MILL), "--round", str(n), "--staging", staging],
            check=False,
        )
        if mill_proc.stderr:
            sys.stderr.write(mill_proc.stderr)
        print(mill_proc.stdout or "", flush=True)
        if mill_proc.returncode != 0:
            print(f"mill failed r{n}; abort reservation", flush=True)
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
        print(pub.stdout or "", flush=True)
        if pub.returncode != 0:
            print(pub.stderr or "", flush=True)
            print(f"publish failed r{n}", flush=True)
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
                "frontier": frontier() if FACTORY.exists() else None,
            }
        ),
        flush=True,
    )
    return 0 if done >= 12 else (0 if done else 3)


if __name__ == "__main__":
    raise SystemExit(main())
