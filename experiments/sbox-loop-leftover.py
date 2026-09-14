#!/usr/bin/env python3
"""frontier → reserve --expected 3 → write → publish. Never steal."""
from __future__ import annotations

import json
import subprocess
import sys
import time
from importlib.machinery import SourceFileLoader
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
FACTORY = REPO / "outputs/raw/2026-08-19-agentic/sandbox-refusal-factory"
HOP = REPO / "outputs/raw/2026-08-19-agentic/log-redaction-factory"
TXN = [sys.executable, str(REPO / "pipelines/round_txn.py")]


def load_mill():
    name = f"sboxmill_{time.time_ns()}"
    return SourceFileLoader(name, str(REPO / "experiments/sbox-mill-r359.py")).load_module()


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
            f"{proc.stderr.strip()}\n{proc.stdout.strip()}"
        )
    return json.loads(proc.stdout)


def reserved_here() -> list[Path]:
    return sorted(FACTORY.glob("ROUND-r*.reserved.json"))


def main() -> int:
    want = int(sys.argv[1]) if len(sys.argv) > 1 else 200
    deadline_s = float(sys.argv[2]) if len(sys.argv) > 2 else 6 * 3600
    published: list[dict] = []
    started = time.time()
    mill = load_mill()
    last = mill.FIRST + len(mill.PLANTS) - 1
    while len(published) < want and time.time() - started < deadline_s:
        mill = load_mill()
        last = mill.FIRST + len(mill.PLANTS) - 1
        status = txn("frontier", str(FACTORY))
        nxt = int(status["next_round"])
        held = reserved_here()
        if held:
            print(f"RESERVED {held[0].name}; wait (never steal)", flush=True)
            time.sleep(0.25)
            continue
        if nxt > last:
            print(f"catalog exhausted at r{nxt} last={last}", flush=True)
            hop = txn("frontier", str(HOP))
            hop_held = sorted(HOP.glob("ROUND-r*.reserved.json"))
            print(json.dumps({"hop": hop, "hop_reserved": [p.name for p in hop_held]}, indent=2), flush=True)
            return 2 if hop_held else 3
        try:
            payload = txn("reserve", str(FACTORY), "--round", str(nxt), "--expected", "3")
        except RuntimeError as exc:
            msg = str(exc)
            if "not the frontier" in msg or "already exists" in msg:
                print(f"race on r{nxt}: {msg.splitlines()[0]}", flush=True)
                time.sleep(0.15)
                continue
            raise
        stage = Path(payload["staging_dir"])
        token = payload["token"]
        plant = mill.plant_for_round(nxt)
        print(f"reserved r{nxt} family={plant['family']} token={token}", flush=True)
        try:
            mill.write_round(nxt, stage)
            pub = txn("publish", str(FACTORY), "--round", str(nxt), "--token", token)
        except Exception as exc:
            print(f"FAIL r{nxt}: {exc}", flush=True)
            try:
                txn("abort", str(FACTORY), "--round", str(nxt), "--token", token)
                print(f"aborted r{nxt}", flush=True)
            except Exception as abort_exc:
                print(f"abort failed r{nxt}: {abort_exc}", flush=True)
            return 1
        rec_ids = [
            json.loads(line)["id"]
            for line in (FACTORY / f"batch-r{nxt:02d}.jsonl").read_text().splitlines()
            if line.strip()
        ]
        row = {
            "round": nxt,
            "family": plant["family"],
            "ids": rec_ids,
            "records": pub["records"],
        }
        published.append(row)
        print(json.dumps(row), flush=True)
    print(
        json.dumps(
            {
                "published": published,
                "count": len(published),
                "seconds": round(time.time() - started, 1),
                "last_catalog": last,
            },
            indent=2,
        )
    )
    return 0 if published else 1


if __name__ == "__main__":
    raise SystemExit(main())
