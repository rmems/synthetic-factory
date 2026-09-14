#!/usr/bin/env python3
"""Reserve → mill → publish leftover leftover leftover catalog (max 16)."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path("/home/raulmc/rmems/synthetic-factory")
DIR = ROOT / "outputs/raw/2026-08-19-agentic/graphql-nplusone-factory"
HOPS = [
    ROOT / "outputs/raw/2026-08-19-agentic/csv-excel-ingest-factory",
    ROOT / "outputs/raw/2026-08-19-agentic/cache-stampede-factory",
    ROOT / "outputs/raw/2026-08-19-agentic/k8s-crashloop-factory",
    ROOT / "outputs/raw/2026-08-19-agentic/authz-regression-factory",
    ROOT / "outputs/raw/2026-08-19-agentic/monorepo-dep-bump-factory",
]
MILL = ROOT / "experiments/gql-mill-r270.py"
MAX_ROUNDS = 16


def run(args: list[str]) -> dict:
    p = subprocess.run(args, cwd=ROOT, capture_output=True, text=True)
    if p.returncode != 0:
        print(p.stdout, p.stderr, file=sys.stderr)
        raise SystemExit(p.returncode)
    return json.loads(p.stdout)


def try_reserve(factory: Path, rnd: int) -> dict | None:
    p = subprocess.run(
        [
            "python3",
            "pipelines/round_txn.py",
            "reserve",
            str(factory),
            "--round",
            str(rnd),
            "--expected",
            "2",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    if p.returncode != 0:
        print(f"reserve failed {factory.name} r{rnd}: {p.stderr.strip()[:200]}")
        return None
    return json.loads(p.stdout)


def mill_publish(factory: Path, rnd: int, cat_idx: int, res: dict) -> dict:
    mill = subprocess.run(
        [
            "python3",
            str(MILL),
            "--staging",
            res["staging_dir"],
            "--batch-file",
            res["batch_file"],
            "--notes-file",
            res["notes_file"],
            "--round",
            str(rnd),
            "--idx",
            str(cat_idx),
            "--factory",
            factory.name,
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    if mill.returncode != 0:
        print(mill.stdout, mill.stderr, file=sys.stderr)
        raise SystemExit(mill.returncode)
    ids = json.loads(mill.stdout)["ids"]
    pub = run(
        [
            "python3",
            "pipelines/round_txn.py",
            "publish",
            str(factory),
            "--round",
            str(rnd),
            "--token",
            res["token"],
        ]
    )
    return {"round": rnd, "ids": ids, "factory": factory.name, "publish": pub}


def main() -> None:
    published = []
    cat_idx = 0
    factory = DIR
    while len(published) < MAX_ROUNDS and cat_idx < 16:
        fr = run(["python3", "pipelines/round_txn.py", "frontier", str(factory)])
        rnd = int(fr["next_round"])
        res = try_reserve(factory, rnd)
        if res is None:
            nxt = None
            for hop in HOPS:
                if hop == factory:
                    continue
                if list(hop.glob("ROUND-r*.reserved.json")):
                    continue
                nxt = hop
                break
            if nxt is None:
                print("no unreserved hop; stop")
                break
            print(f"{factory.name} reserved; hop {nxt.name}")
            factory = nxt
            continue
        rec = mill_publish(factory, rnd, cat_idx, res)
        published.append(rec)
        cat_idx += 1
        print(json.dumps({"published": rnd, "ids": rec["ids"], "factory": factory.name}))
    print(json.dumps({"done": [{"round": p["round"], "ids": p["ids"], "factory": p["factory"]} for p in published]}, indent=2))


if __name__ == "__main__":
    main()
