#!/usr/bin/env python3
"""frontier → reserve --expected 2 → mill → publish. Never steal. Loop ≥12 or 40 min."""
from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

from importlib.machinery import SourceFileLoader

REPO = Path(__file__).resolve().parents[1]
FACTORY = REPO / "outputs/raw/2026-08-19-agentic/agent-memory-compaction-factory"
AGENTIC = FACTORY.parent
MILL_PATH = REPO / "experiments/amc-mill-r316.py"
MILL = SourceFileLoader("amcmill316", str(MILL_PATH)).load_module()
TXN = [sys.executable, str(REPO / "pipelines/round_txn.py")]
HOP = AGENTIC / "log-redaction-factory"


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
    return json.loads(proc.stdout)


def reserved(factory: Path, n: int) -> bool:
    return (factory / f"ROUND-r{n:02d}.reserved.json").exists()


def mill_round(nxt: int, stage: Path, pair_idx: int) -> None:
    mill_proc = subprocess.run(
        [
            sys.executable,
            str(MILL_PATH),
            "--round",
            str(nxt),
            "--staging",
            str(stage),
            "--pair",
            str(pair_idx),
        ],
        cwd=REPO,
        text=True,
        capture_output=True,
        check=False,
    )
    sys.stderr.write(mill_proc.stderr or "")
    print(mill_proc.stdout, flush=True)
    if mill_proc.returncode != 0:
        raise RuntimeError(f"mill failed for r{nxt}: {mill_proc.stderr}")


def main() -> int:
    want = int(sys.argv[1]) if len(sys.argv) > 1 else 12
    pair_idx = int(sys.argv[2]) if len(sys.argv) > 2 else 0
    deadline = time.monotonic() + 40 * 60
    published: list[dict] = []
    hop_noted = False
    while len(published) < want and time.monotonic() < deadline:
        if pair_idx >= len(MILL.PAIRS):
            print("catalog exhausted", flush=True)
            break
        status = txn("frontier", str(FACTORY))
        nxt = int(status["next_round"])
        if reserved(FACTORY, nxt):
            print(f"RESERVED r{nxt}; wait (never steal)", flush=True)
            if not hop_noted:
                hop_st = txn("frontier", str(HOP))
                hn = int(hop_st["next_round"])
                if reserved(HOP, hn):
                    print(f"log-redaction r{hn} reserved; do not steal", flush=True)
                else:
                    print(
                        json.dumps(
                            {
                                "hop": "log-redaction-factory",
                                "next_round": hn,
                                "unreserved": True,
                                "note": "AMC seat reserved; hop named factory is free but this mill is AMC leftover-only",
                            }
                        ),
                        flush=True,
                    )
                hop_noted = True
            time.sleep(2)
            continue
        hop_noted = False
        try:
            payload = txn(
                "reserve",
                str(FACTORY),
                "--round",
                str(nxt),
                "--expected",
                "2",
            )
        except RuntimeError as exc:
            print(f"reserve race r{nxt}: {exc}", flush=True)
            time.sleep(1)
            continue
        stage = Path(payload["staging_dir"])
        token = payload["token"]
        print(f"reserved r{nxt} token={token} stage={stage} pair={pair_idx}", flush=True)
        mill_round(nxt, stage, pair_idx)
        pub = txn("publish", str(FACTORY), "--round", str(nxt), "--token", token)
        ids = [
            json.loads(line)["id"]
            for line in (FACTORY / f"batch-r{nxt:02d}.jsonl").read_text().splitlines()
            if line.strip()
        ]
        row = {"round": nxt, "ids": ids, "records": pub["records"], "pair": pair_idx}
        published.append(row)
        pair_idx += 1
        print(json.dumps(row), flush=True)
    print(
        json.dumps(
            {
                "published": len(published),
                "rounds": [p["round"] for p in published],
                "ids": [p["ids"] for p in published],
                "frontier": txn("frontier", str(FACTORY))["next_round"],
            },
            indent=2,
        )
    )
    return 0 if len(published) >= min(want, 1) else 1


if __name__ == "__main__":
    raise SystemExit(main())
