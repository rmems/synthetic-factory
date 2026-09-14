#!/usr/bin/env python3
"""Reserve → mill → publish mcp-tool-schema-drift leftover r430+.

Never steal a live reservation. Never rewrite outputs/raw.
If MCP is reserved, hop graphql-nplusone-factory only when that mill is unreserved.
"""
from __future__ import annotations

import json
import py_compile
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MILL = ROOT / "experiments" / "msd-leftover-mill-r430.py"
GQL_MILL = ROOT / "experiments" / "gql-leftover-hop-r215.py"
TXN = ROOT / "pipelines" / "round_txn.py"
MCP = ROOT / "outputs" / "raw" / "2026-08-19-agentic" / "mcp-tool-schema-drift-factory"
GQL = ROOT / "outputs" / "raw" / "2026-08-19-agentic" / "graphql-nplusone-factory"

import importlib.util

py_compile.compile(str(MILL), doraise=True)
_spec = importlib.util.spec_from_file_location("msd_leftover_mill_r430", MILL)
_mill = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(_mill)


def run(args: list[str], check: bool = True) -> subprocess.CompletedProcess:
    print("+", " ".join(str(a) for a in args), flush=True)
    proc = subprocess.run(
        [str(a) for a in args],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )
    if check and proc.returncode != 0:
        sys.stderr.write(proc.stdout or "")
        sys.stderr.write(proc.stderr or "")
        raise SystemExit(proc.returncode)
    return proc


def frontier(path: Path) -> dict:
    proc = run([sys.executable, str(TXN), "frontier", str(path)])
    print(proc.stdout, flush=True)
    return json.loads(proc.stdout)


def reserved(factory: Path, n: int) -> bool:
    return (factory / f"ROUND-r{n:02d}.reserved.json").exists()


def load_gql():
    py_compile.compile(str(GQL_MILL), doraise=True)
    spec = importlib.util.spec_from_file_location("gql_leftover_hop_r215", GQL_MILL)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def publish_mcp(n: int) -> None:
    if reserved(MCP, n):
        raise SystemExit(f"MCP r{n} already reserved; never steal")
    proc = run(
        [sys.executable, str(TXN), "reserve", str(MCP), "--round", str(n), "--expected", "2"]
    )
    print(proc.stdout, flush=True)
    res = json.loads(proc.stdout)
    staging = Path(res["staging_dir"])
    _mill.stage_round(n, staging, res["batch_file"], res["notes_file"])
    pub = run(
        [
            sys.executable,
            str(TXN),
            "publish",
            str(MCP),
            "--round",
            str(n),
            "--token",
            res["token"],
        ]
    )
    print(pub.stdout, flush=True)


def publish_gql(n: int) -> None:
    if reserved(GQL, n):
        raise SystemExit(f"graphql r{n} already reserved; never steal")
    gql = load_gql()
    proc = run(
        [sys.executable, str(TXN), "reserve", str(GQL), "--round", str(n), "--expected", "2"]
    )
    print(proc.stdout, flush=True)
    res = json.loads(proc.stdout)
    staging = Path(res["staging_dir"])
    gql.stage_round(n, staging, res["batch_file"], res["notes_file"])
    pub = run(
        [
            sys.executable,
            str(TXN),
            "publish",
            str(GQL),
            "--round",
            str(n),
            "--token",
            res["token"],
        ]
    )
    print(pub.stdout, flush=True)


def try_reserve(factory: Path, n: int) -> dict | None:
    if reserved(factory, n):
        return None
    proc = run(
        [sys.executable, str(TXN), "reserve", str(factory), "--round", str(n), "--expected", "2"],
        check=False,
    )
    if proc.returncode != 0:
        print(proc.stderr or proc.stdout, flush=True)
        return None
    print(proc.stdout, flush=True)
    return json.loads(proc.stdout)


def publish_reserved(factory: Path, mill, n: int, res: dict) -> None:
    staging = Path(res["staging_dir"])
    mill.stage_round(n, staging, res["batch_file"], res["notes_file"])
    pub = run(
        [
            sys.executable,
            str(TXN),
            "publish",
            str(factory),
            "--round",
            str(n),
            "--token",
            res["token"],
        ]
    )
    print(pub.stdout, flush=True)


def main() -> int:
    max_rounds = int(sys.argv[1]) if len(sys.argv) > 1 else 12
    deadline = time.time() + 40 * 60
    done = 0
    published: list[str] = []
    gql = None
    while done < max_rounds and time.time() < deadline:
        status = frontier(MCP)
        n = status["next_round"]
        if reserved(MCP, n):
            print(f"MCP r{n} reserved; never steal. Checking graphql hop.", flush=True)
            gstatus = frontier(GQL)
            gn = gstatus["next_round"]
            if not reserved(GQL, gn):
                print(json.dumps({"hop": "graphql-nplusone-factory", "next_round": gn}), flush=True)
                if gql is None:
                    gql = load_gql()
                res = try_reserve(GQL, gn)
                if res:
                    publish_reserved(GQL, gql, gn, res)
                    published.append(f"gql-r{gn}")
                    done += 1
                    continue
            print("both seats reserved; wait rather than steal", flush=True)
            time.sleep(0.35)
            continue
        res = try_reserve(MCP, n)
        if not res:
            time.sleep(0.2)
            continue
        publish_reserved(MCP, _mill, n, res)
        published.append(f"msd-r{n}")
        done += 1
    print(json.dumps({"published": published, "done": done}), flush=True)
    return 0 if done else 1


if __name__ == "__main__":
    raise SystemExit(main())
