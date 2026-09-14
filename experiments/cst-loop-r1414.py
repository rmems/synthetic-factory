#!/usr/bin/env python3
"""frontier → reserve --expected 2 → mill → publish CST r1414+ leftover leftover leftover.

Never steal. Never rewrite raw. Never hop to sandbox-refusal if reserved/writing.
Never write docker/search ids.
"""
from __future__ import annotations

import json
import subprocess
import sys
from importlib.machinery import SourceFileLoader
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
FACTORY = REPO / "outputs/raw/2026-08-19-agentic/cache-stampede-factory"
AGENTIC = FACTORY.parent
MILL_PATH = REPO / "experiments/cst-mill-r1414.py"
MILL = SourceFileLoader("cstmill1414", str(MILL_PATH)).load_module()
TXN = [sys.executable, str(REPO / "pipelines/round_txn.py")]


def txn(*args: str) -> dict:
    proc = subprocess.run(
        TXN + list(args),
        cwd=REPO,
        text=True,
        capture_output=True,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(
            f"round_txn {' '.join(args)} failed ({proc.returncode}): "
            f"{(proc.stderr or '').strip()}\n{(proc.stdout or '').strip()}"
        )
    print(proc.stdout, flush=True)
    return json.loads(proc.stdout[proc.stdout.find("{") :])


def reserved(factory: Path, n: int) -> bool:
    return (factory / f"ROUND-r{n:02d}.reserved.json").exists()


def writing(factory: Path) -> bool:
    return bool(
        list(factory.glob("ROUND-r*.reserved.json"))
        or list(factory.glob("ROUND-r*.publishing.json"))
    )


def hop_target() -> Path | None:
    for hop in sorted(AGENTIC.iterdir()):
        if not hop.is_dir() or hop == FACTORY:
            continue
        if hop.name == "sandbox-refusal-factory":
            continue
        try:
            st = txn("frontier", str(hop))
        except RuntimeError as exc:
            print(f"hop frontier {hop.name} failed: {exc}", flush=True)
            continue
        hn = int(st["next_round"])
        if reserved(hop, hn) or writing(hop):
            continue
        return hop
    return None


def main() -> int:
    published: list[int] = []
    last = MILL.CATALOG_FIRST + len(MILL.PAIRS) - 1
    while True:
        status = txn("frontier", str(FACTORY))
        nxt = int(status["next_round"])
        if reserved(FACTORY, nxt) or writing(FACTORY):
            hop = hop_target()
            print(
                json.dumps(
                    {
                        "stop": "cst_reserved",
                        "round": nxt,
                        "hop": None if hop is None else hop.name,
                        "published": published,
                    }
                ),
                flush=True,
            )
            return 2
        if nxt > last:
            print(
                json.dumps(
                    {
                        "stop": "catalog_exhausted",
                        "next_round": nxt,
                        "last": last,
                        "published": published,
                    }
                ),
                flush=True,
            )
            return 0
        try:
            payload = txn("reserve", str(FACTORY), "--round", str(nxt), "--expected", "2")
        except RuntimeError as exc:
            print(
                json.dumps(
                    {
                        "stop": "reserve_failed",
                        "round": nxt,
                        "err": str(exc)[-2000:],
                        "published": published,
                    }
                ),
                flush=True,
            )
            return 2
        token = payload["token"]
        stage = Path(payload["staging_dir"])
        print(f"RESERVED r{nxt} {token[:8]} {stage}", flush=True)
        try:
            ids = MILL.write_round(nxt, stage)
            print(json.dumps({"milled": nxt, "ids": ids}), flush=True)
        except Exception as exc:
            try:
                txn("abort", str(FACTORY), "--round", str(nxt), "--token", token)
            except RuntimeError as abort_exc:
                print(f"abort r{nxt} failed: {abort_exc}", flush=True)
            print(
                json.dumps(
                    {
                        "stop": "mill_failed",
                        "round": nxt,
                        "err": str(exc)[-2000:],
                        "published": published,
                    }
                ),
                flush=True,
            )
            return 3
        try:
            txn("publish", str(FACTORY), "--round", str(nxt), "--token", token)
        except RuntimeError as exc:
            print(
                json.dumps(
                    {
                        "stop": "publish_failed",
                        "round": nxt,
                        "err": str(exc)[-4000:],
                        "published": published,
                    }
                ),
                flush=True,
            )
            return 4
        published.append(nxt)
        print(f"PUBLISHED r{nxt}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
