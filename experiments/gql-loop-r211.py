#!/usr/bin/env python3
"""Reserve → mill → publish graphql-nplusone-factory from r211 leftover catalog.

Never steal. Never rewrite raw. If graphql is reserved, hop browser-tool-use-factory
only when that seat is unreserved; do not mill browser without a catalog.
"""
from __future__ import annotations

import json
import py_compile
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MILL = ROOT / "experiments" / "gql-mill-r211.py"
TXN = ROOT / "pipelines" / "round_txn.py"
FACTORY = ROOT / "outputs" / "raw" / "2026-08-19-agentic" / "graphql-nplusone-factory"
BROWSER = ROOT / "outputs" / "raw" / "2026-08-19-agentic" / "browser-tool-use-factory"

import importlib.util

py_compile.compile(str(MILL), doraise=True)
_spec = importlib.util.spec_from_file_location("gql_mill_r211", MILL)
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


def frontier(path: Path) -> dict:
    proc = run([sys.executable, str(TXN), "frontier", str(path)])
    print(proc.stdout, flush=True)
    return json.loads(proc.stdout)


def reserved(factory: Path, n: int) -> bool:
    return (factory / f"ROUND-r{n:02d}.reserved.json").exists()


def hop_or_stop(n: int) -> int:
    print(f"graphql r{n} already reserved; never steal", flush=True)
    b = frontier(BROWSER)
    bn = b["next_round"]
    if reserved(BROWSER, bn):
        print(f"browser r{bn} also reserved; stop", flush=True)
        return 2
    print(
        json.dumps({"hop": "browser-tool-use-factory", "next_round": bn, "unreserved": True}),
        flush=True,
    )
    print("browser unreserved but this mill has no leftover catalog there; stop", flush=True)
    return 3


def main() -> int:
    max_rounds = int(sys.argv[1]) if len(sys.argv) > 1 else 12
    skip_first_reserve = False
    token = None
    staging = None
    if len(sys.argv) >= 5 and sys.argv[2] == "--resume":
        skip_first_reserve = True
        token = sys.argv[3]
        staging = sys.argv[4]
    done = 0
    published: list[int] = []
    while done < max_rounds:
        status = frontier(FACTORY)
        n = status["next_round"]
        last = CATALOG_FIRST + CATALOG_LEN - 1
        if n > last:
            print(f"catalog exhausted at frontier {n} (last={last})", flush=True)
            break
        if n < CATALOG_FIRST:
            print(f"frontier {n} below catalog {CATALOG_FIRST}; stop", flush=True)
            return 7
        if skip_first_reserve and done == 0:
            print(f"resume reserved r{n} token={token} staging={staging}", flush=True)
        else:
            if reserved(FACTORY, n):
                return hop_or_stop(n)
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
                    return hop_or_stop(n)
                return 5
            payload = json.loads(proc.stdout)
            print(proc.stdout, flush=True)
            token = payload["token"]
            staging = payload["staging_dir"]
            print(f"reserved r{n} token={token} staging={staging}", flush=True)
        try:
            mill = run(
                [sys.executable, str(MILL), "--round", str(n), "--staging", str(staging)]
            )
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
                    str(token),
                ]
            )
        except subprocess.CalledProcessError as exc:
            print(exc.stdout, exc.stderr, flush=True)
            print(f"mill/publish failed for r{n}; abort", flush=True)
            run(
                [
                    sys.executable,
                    str(TXN),
                    "abort",
                    str(FACTORY),
                    "--round",
                    str(n),
                    "--token",
                    str(token),
                ],
                check=False,
            )
            return 6
        print(pub.stdout, flush=True)
        done += 1
        published.append(n)
        skip_first_reserve = False
        print(f"published r{n} ({done}/{max_rounds})", flush=True)
    print(json.dumps({"published": done, "rounds": published, "frontier": frontier(FACTORY)["next_round"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
