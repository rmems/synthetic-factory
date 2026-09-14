#!/usr/bin/env python3
"""Reserve → mill → publish leftover leftover leftover catalog (max 16)."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path("/home/raulmc/rmems/synthetic-factory")
DIR = ROOT / "outputs/raw/2026-08-19-agentic/graphql-nplusone-factory"
MILL = ROOT / "experiments/gql-mill-r232.py"
MAX_ROUNDS = 16
START = 232
END = 247  # 16 catalog slots


def run(args: list[str]) -> dict:
    p = subprocess.run(args, cwd=ROOT, capture_output=True, text=True)
    if p.returncode != 0:
        print(p.stdout, p.stderr, file=sys.stderr)
        raise SystemExit(p.returncode)
    return json.loads(p.stdout)


def main() -> None:
    published = []
    fr0 = run(["python3", "pipelines/round_txn.py", "frontier", str(DIR)])
    start = int(fr0["next_round"])
    for rnd in range(start, END + 1):
        if len(published) >= MAX_ROUNDS:
            break
        fr = run(["python3", "pipelines/round_txn.py", "frontier", str(DIR)])
        nxt = int(fr["next_round"])
        if nxt != rnd:
            print(f"frontier next_round={nxt} expected {rnd}; stop")
            break
        if rnd > END:
            print("catalog empty")
            break
        try:
            res = run(
                [
                    "python3",
                    "pipelines/round_txn.py",
                    "reserve",
                    str(DIR),
                    "--round",
                    str(rnd),
                    "--expected",
                    "2",
                ]
            )
        except SystemExit:
            print(f"reserve failed round {rnd}; stop/hop")
            break
        staging = res["staging_dir"]
        batch = res["batch_file"]
        notes = res["notes_file"]
        token = res["token"]
        mill = subprocess.run(
            [
                "python3",
                str(MILL),
                "--staging",
                staging,
                "--batch-file",
                batch,
                "--notes-file",
                notes,
                "--round",
                str(rnd),
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
                str(DIR),
                "--round",
                str(rnd),
                "--token",
                token,
            ]
        )
        published.append({"round": rnd, "ids": ids, "publish": pub})
        print(json.dumps({"published": rnd, "ids": ids}))
    print(json.dumps({"done": published}, indent=2))


if __name__ == "__main__":
    main()
