#!/usr/bin/env python3
"""Prefer graphql leftover mill; hop browser-tool-use-factory if graphql reserved.

Never steal. Never rewrite raw. ≥12 rounds.
"""
from __future__ import annotations

import json
import py_compile
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GQL_MILL = ROOT / "experiments" / "gql-mill-r211.py"
BRW_MILL = ROOT / "experiments" / "brw-mill-r383.py"
TXN = ROOT / "pipelines" / "round_txn.py"
GQL = ROOT / "outputs" / "raw" / "2026-08-19-agentic" / "graphql-nplusone-factory"
BRW = ROOT / "outputs" / "raw" / "2026-08-19-agentic" / "browser-tool-use-factory"

import importlib.util

py_compile.compile(str(GQL_MILL), doraise=True)
py_compile.compile(str(BRW_MILL), doraise=True)

_gspec = importlib.util.spec_from_file_location("gql_mill_r211", GQL_MILL)
_gmill = importlib.util.module_from_spec(_gspec)
assert _gspec.loader is not None
_gspec.loader.exec_module(_gmill)
GQL_PAIRS = len(_gmill.PAIRS)

_bspec = importlib.util.spec_from_file_location("brw_mill_r383", BRW_MILL)
_bmill = importlib.util.module_from_spec(_bspec)
assert _bspec.loader is not None
_bspec.loader.exec_module(_bmill)
BRW_FIRST = _bmill.CATALOG_FIRST
BRW_LAST = BRW_FIRST + len(_bmill.PAIRS) - 1


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


def mill_gql(n: int, staging: str, token: str, base: int) -> None:
    mill = run(
        [
            sys.executable,
            str(GQL_MILL),
            "--round",
            str(n),
            "--staging",
            str(staging),
            "--base",
            str(base),
        ]
    )
    sys.stderr.write(mill.stderr or "")
    print(mill.stdout, flush=True)
    pub = run(
        [
            sys.executable,
            str(TXN),
            "publish",
            str(GQL),
            "--round",
            str(n),
            "--token",
            str(token),
        ]
    )
    print(pub.stdout, flush=True)


def mill_brw(n: int, staging: str, token: str) -> None:
    mill = run([sys.executable, str(BRW_MILL), "--round", str(n), "--out", str(staging)])
    sys.stderr.write(mill.stderr or "")
    print(mill.stdout, flush=True)
    pub = run(
        [
            sys.executable,
            str(TXN),
            "publish",
            str(BRW),
            "--round",
            str(n),
            "--token",
            str(token),
        ]
    )
    print(pub.stdout, flush=True)


def reserve(factory: Path, n: int) -> dict | None:
    if reserved(factory, n):
        return None
    try:
        proc = run(
            [
                sys.executable,
                str(TXN),
                "reserve",
                str(factory),
                "--round",
                str(n),
                "--expected",
                "2",
            ]
        )
    except subprocess.CalledProcessError as exc:
        print(exc.stdout, exc.stderr, flush=True)
        return None
    payload = json.loads(proc.stdout)
    print(proc.stdout, flush=True)
    return payload


def abort(factory: Path, n: int, token: str) -> None:
    run(
        [
            sys.executable,
            str(TXN),
            "abort",
            str(factory),
            "--round",
            str(n),
            "--token",
            str(token),
        ],
        check=False,
    )


def main() -> int:
    max_rounds = int(sys.argv[1]) if len(sys.argv) > 1 else 12
    done = 0
    published: list[tuple[str, int]] = []
    gql_base: int | None = None
    gql_used = 0
    while done < max_rounds:
        g = frontier(GQL)
        gn = g["next_round"]
        payload = None
        if gql_used < GQL_PAIRS:
            payload = reserve(GQL, gn)
        if payload is not None:
            token = payload["token"]
            staging = payload["staging_dir"]
            if gql_base is None:
                gql_base = gn
            print(f"reserved graphql r{gn} token={token} staging={staging} base={gql_base}", flush=True)
            try:
                mill_gql(gn, staging, token, gql_base)
            except subprocess.CalledProcessError as exc:
                print(exc.stdout, exc.stderr, flush=True)
                abort(GQL, gn, token)
                return 6
            published.append(("graphql-nplusone-factory", gn))
            gql_used += 1
            done += 1
            print(f"published graphql r{gn} ({done}/{max_rounds})", flush=True)
            continue

        print(f"graphql r{gn} reserved or catalog full; hop browser", flush=True)
        b = frontier(BRW)
        bn = b["next_round"]
        if bn < BRW_FIRST or bn > BRW_LAST:
            print(f"browser catalog cannot mill r{bn} (first={BRW_FIRST} last={BRW_LAST})", flush=True)
            break
        payload = reserve(BRW, bn)
        if payload is None:
            print(f"browser r{bn} also reserved; stop", flush=True)
            return 2
        token = payload["token"]
        staging = payload["staging_dir"]
        print(f"reserved browser r{bn} token={token} staging={staging}", flush=True)
        try:
            mill_brw(bn, staging, token)
        except subprocess.CalledProcessError as exc:
            print(exc.stdout, exc.stderr, flush=True)
            abort(BRW, bn, token)
            return 6
        published.append(("browser-tool-use-factory", bn))
        done += 1
        print(f"published browser r{bn} ({done}/{max_rounds})", flush=True)

    print(
        json.dumps(
            {
                "published": done,
                "rounds": published,
                "gql_frontier": frontier(GQL)["next_round"],
                "brw_frontier": frontier(BRW)["next_round"],
            }
        )
    )
    return 0 if done >= 12 else (0 if done else 8)


if __name__ == "__main__":
    raise SystemExit(main())
