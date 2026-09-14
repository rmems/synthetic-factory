#!/usr/bin/env python3
"""frontier → reserve --expected 2 → mill → publish. Never steal. Loop until catalog or reserve dies."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from importlib.machinery import SourceFileLoader

REPO = Path(__file__).resolve().parents[1]
FACTORY = REPO / "outputs/raw/2026-08-19-agentic/agent-memory-compaction-factory"
AGENTIC = FACTORY.parent
MILL_PATH = REPO / "experiments/amc-mill-r229.py"
MILL = SourceFileLoader("amcmill229", str(MILL_PATH)).load_module()
TXN = [sys.executable, str(REPO / "pipelines/round_txn.py")]
HOP_ORDER = [
    AGENTIC / "mcp-tool-schema-drift-factory",
    AGENTIC / "payment-idempotency-factory",
    AGENTIC / "proto-breaking-change-factory",
    AGENTIC / "docker-build-cache-factory",
    AGENTIC / "k8s-crashloop-factory",
    AGENTIC / "log-redaction-factory",
]


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


def main() -> int:
    want = int(sys.argv[1]) if len(sys.argv) > 1 else len(MILL.PAIRS)
    published: list[dict] = []
    last = MILL.CATALOG_FIRST + len(MILL.PAIRS) - 1
    while len(published) < want:
        status = txn("frontier", str(FACTORY))
        nxt = int(status["next_round"])
        if reserved(FACTORY, nxt):
            print(f"RESERVED r{nxt}; hop check", flush=True)
            hopped = False
            for hop in HOP_ORDER:
                if hop.name in {"eval-harness-trajectory-factory", "sandbox-refusal-factory"}:
                    continue
                hop_st = txn("frontier", str(hop))
                hn = int(hop_st["next_round"])
                if reserved(hop, hn):
                    print(f"{hop.name} r{hn} reserved; skip", flush=True)
                    continue
                print(
                    json.dumps(
                        {
                            "hop": hop.name,
                            "next_round": hn,
                            "unreserved": True,
                            "note": "AMC seat reserved; hop named factory is free but this mill is AMC-only",
                        }
                    ),
                    flush=True,
                )
                hopped = True
                break
            return 2 if hopped else 3
        if nxt > last:
            print(f"catalog exhausted at frontier {nxt} (last={last})", flush=True)
            break
        payload = txn(
            "reserve",
            str(FACTORY),
            "--round",
            str(nxt),
            "--expected",
            "2",
        )
        stage = Path(payload["staging_dir"])
        token = payload["token"]
        print(f"reserved r{nxt} token={token} stage={stage}", flush=True)
        mill_proc = subprocess.run(
            [
                sys.executable,
                str(MILL_PATH),
                "--round",
                str(nxt),
                "--staging",
                str(stage),
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
        pub = txn("publish", str(FACTORY), "--round", str(nxt), "--token", token)
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
