#!/usr/bin/env python3
"""frontier → reserve --expected 3 → mill → publish. Never steal. Loop until catalog or quota.

Hop another unreserved named factory if CRP is reserved. Never sandbox-refusal.
"""
from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
FACTORY = REPO / "outputs/raw/2026-08-19-agentic/code-review-preference-factory"
AGENTIC = FACTORY.parent
MILL_PATH = REPO / "experiments/crp-mill-r538.py"
TXN = [sys.executable, str(REPO / "pipelines/round_txn.py")]
FIRST = 538
NEVER_HOP = {"sandbox-refusal-factory"}


def unused_left() -> int:
    from importlib.machinery import SourceFileLoader

    mill = SourceFileLoader("crp538cat", str(MILL_PATH)).load_module()
    return len(mill.unused_plants())


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


def reserved_path(factory: Path, n: int) -> Path:
    return factory / f"ROUND-r{n:02d}.reserved.json"


def list_hop_targets() -> list[Path]:
    out = []
    for path in sorted(AGENTIC.iterdir()):
        if not path.is_dir() or path == FACTORY:
            continue
        if path.name in NEVER_HOP:
            continue
        if list(path.glob("ROUND-r*.reserved.json")):
            continue
        out.append(path)
    return out


def mill_round(nxt: int, stage: Path) -> None:
    mill_proc = subprocess.run(
        [sys.executable, str(MILL_PATH), "--round", str(nxt), "--staging", str(stage)],
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
    want = int(sys.argv[1]) if len(sys.argv) > 1 else 10_000
    deadline = time.monotonic() + 6 * 60 * 60
    published: list[dict] = []
    while len(published) < want and time.monotonic() < deadline:
        status = txn("frontier", str(FACTORY))
        nxt = int(status["next_round"])
        left = unused_left()
        if left < 3:
            print(f"catalog exhausted at r{nxt} (unused={left})", flush=True)
            break
        marker = reserved_path(FACTORY, nxt)
        if marker.exists():
            hops = [p.name for p in list_hop_targets()]
            print(
                json.dumps(
                    {
                        "reserved": True,
                        "round": nxt,
                        "hop_candidates": hops[:12],
                        "never": sorted(NEVER_HOP),
                    }
                ),
                flush=True,
            )
            time.sleep(2)
            if marker.exists():
                print("CRP reserved by another writer; wait, do not steal", flush=True)
                continue
        try:
            payload = txn(
                "reserve",
                str(FACTORY),
                "--round",
                str(nxt),
                "--expected",
                "3",
            )
        except RuntimeError as exc:
            print(f"reserve race r{nxt}: {exc}", flush=True)
            time.sleep(1)
            continue
        stage = Path(payload["staging_dir"])
        token = payload["token"]
        print(f"reserved r{nxt} token={token} stage={stage}", flush=True)
        try:
            mill_round(nxt, stage)
            pub = txn("publish", str(FACTORY), "--round", str(nxt), "--token", token)
        except Exception as exc:
            print(f"mill/publish failed r{nxt}: {exc}", flush=True)
            try:
                txn("abort", str(FACTORY), "--round", str(nxt), "--token", token)
            except Exception as abort_exc:
                print(f"abort failed r{nxt}: {abort_exc}", flush=True)
            raise
        ids = [
            json.loads(line)["id"]
            for line in (FACTORY / f"batch-r{nxt:02d}.jsonl").read_text().splitlines()
            if line.strip()
        ]
        row = {"round": nxt, "ids": ids, "records": pub["records"]}
        published.append(row)
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
    return 0 if published else 1


if __name__ == "__main__":
    raise SystemExit(main())
