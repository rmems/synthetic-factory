#!/usr/bin/env python3
"""Reserve → mill → publish monorepo-dep-bump-factory from r918 until catalog/quota.

If mdb is reserved, hop another unreserved named factory (never sandbox-refusal
if reserved or writing). Never steal. Never rewrite raw. No idle sleep.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MILL = ROOT / "experiments" / "mdb-mill-r918.py"
TXN = ROOT / "pipelines" / "round_txn.py"
AGENTIC = ROOT / "outputs" / "raw" / "2026-08-19-agentic"
FACTORY = AGENTIC / "monorepo-dep-bump-factory"
GQL = AGENTIC / "graphql-nplusone-factory"
GQL_MILL = ROOT / "experiments" / "gql-mill-r216.py"
SKIP_HOP = {"sandbox-refusal-factory"}

import importlib.util


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
    nxt = json.loads(proc.stdout)["next_round"]
    print(f"frontier {factory.name} next_round={nxt}", flush=True)
    return nxt


def reserved(factory: Path, n: int) -> bool:
    return (factory / f"ROUND-r{n:02d}.reserved.json").exists()


def writing(factory: Path) -> bool:
    return any(factory.glob("ROUND-r*.reserved.json"))


def publish_round(factory: Path, n: int, expected: int, mill: Path) -> None:
    proc = run(
        [
            sys.executable,
            str(TXN),
            "reserve",
            str(factory),
            "--round",
            str(n),
            "--expected",
            str(expected),
        ]
    )
    payload = json.loads(proc.stdout)
    print(proc.stdout, flush=True)
    token = payload["token"]
    staging = payload["staging_dir"]
    print(f"reserved {factory.name} r{n} token={token} staging={staging}", flush=True)
    mill_proc = run(
        [sys.executable, str(mill), "--round", str(n), "--staging", staging]
    )
    if mill_proc.stderr:
        sys.stderr.write(mill_proc.stderr)
    print(mill_proc.stdout, flush=True)
    pub = run(
        [
            sys.executable,
            str(TXN),
            "publish",
            str(factory),
            "--round",
            str(n),
            "--token",
            token,
        ]
    )
    print(pub.stdout, flush=True)


def catalog_last(mill: Path) -> tuple[int, int]:
    spec = importlib.util.spec_from_file_location("mill_live", mill)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    first = mod.CATALOG_FIRST
    return first, first + len(mod.PAIRS) - 1


def gql_ready() -> tuple[bool, int]:
    n = frontier(GQL)
    if GQL.name in SKIP_HOP or writing(GQL) or reserved(GQL, n):
        print(f"hop skip {GQL.name} r{n} reserved/writing", flush=True)
        return False, n
    first, last = catalog_last(GQL_MILL)
    unused = None
    spec = importlib.util.spec_from_file_location("gql_live", GQL_MILL)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    if hasattr(mod, "unused_pairs"):
        unused = len(mod.unused_pairs())
    ok = (first <= n <= last) or (unused is not None and unused > 0)
    print(f"gql ready={ok} n={n} catalog={first}..{last} unused={unused}", flush=True)
    return ok, n


def main() -> int:
    max_rounds = int(sys.argv[1]) if len(sys.argv) > 1 else 200
    done = 0
    hops = 0
    published: list[str] = []
    first, last = catalog_last(MILL)
    while done < max_rounds:
        n = frontier(FACTORY)
        if n > last:
            print(f"mdb catalog exhausted at frontier {n} (last={last})", flush=True)
            break
        if n < first:
            print(f"mdb frontier {n} below catalog first {first}; hop", flush=True)
            hops += 1
            break
        if reserved(FACTORY, n):
            print(f"mdb r{n} already reserved; hop (no steal)", flush=True)
            hops += 1
            gql_ok, gn = gql_ready()
            if not gql_ok:
                print("no unreserved hop mill; stop rather than idle", flush=True)
                break
            try:
                publish_round(GQL, gn, 2, GQL_MILL)
            except subprocess.CalledProcessError as exc:
                print(exc.stdout, exc.stderr, flush=True)
                if reserved(GQL, gn) and not (GQL / f"ROUND-r{gn:02d}.complete.json").exists():
                    print("lost gql race; hop next", flush=True)
                    continue
                return 4
            done += 1
            published.append(f"gql-r{gn}")
            print(f"published graphql r{gn} ({done}/{max_rounds})", flush=True)
            continue
        try:
            publish_round(FACTORY, n, 2, MILL)
        except subprocess.CalledProcessError as exc:
            print(exc.stdout, exc.stderr, flush=True)
            if reserved(FACTORY, n) and not (FACTORY / f"ROUND-r{n:02d}.complete.json").exists():
                print("lost race or mill/publish failed after reserve", flush=True)
                hops += 1
                continue
            print(f"reserve/mill/publish failed for r{n}", flush=True)
            return 5
        done += 1
        published.append(f"mdb-r{n}")
        print(f"published r{n} ({done}/{max_rounds})", flush=True)
    nxt = frontier(FACTORY) if FACTORY.exists() else None
    print(
        json.dumps(
            {
                "published": done,
                "rounds": published,
                "hops": hops,
                "frontier": nxt,
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
