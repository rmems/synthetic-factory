#!/usr/bin/env python3
"""frontier → reserve --expected 3 → stage → publish. Never steal."""
from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

from importlib.machinery import SourceFileLoader

REPO = Path(__file__).resolve().parents[1]
FACTORY = REPO / "outputs/raw/2026-08-19-agentic/sandbox-refusal-factory"
HOP = REPO / "outputs/raw/2026-08-19-agentic/log-redaction-factory"
SSL = REPO / "outputs/raw/2026-08-19-agentic/ssl-cert-rotation-factory"
MILL = SourceFileLoader("sboxmill", str(REPO / "experiments/sbox-mill-r359.py")).load_module()
TXN = [sys.executable, str(REPO / "pipelines/round_txn.py")]
SSL_MILL = REPO / "experiments/ssl-mill-r27.py"


def mill_ssl_one() -> dict | None:
    """Hop mill one ssl-cert-rotation round. Never steal."""
    status = txn("frontier", str(SSL))
    nxt = int(status["next_round"])
    ssl_mod = SourceFileLoader("sslmill", str(SSL_MILL)).load_module()
    last = ssl_mod.CATALOG_FIRST + len(ssl_mod.PAIRS) - 1
    if nxt > last:
        print(f"ssl catalog exhausted at r{nxt} last={last}", flush=True)
        return None
    if sorted(SSL.glob("ROUND-r*.reserved.json")):
        print(f"ssl reserved at frontier r{nxt}", flush=True)
        return None
    try:
        payload = txn("reserve", str(SSL), "--round", str(nxt), "--expected", "2")
    except RuntimeError as exc:
        print(f"ssl reserve failed r{nxt}: {exc}", flush=True)
        return None
    stage = Path(payload["staging_dir"])
    token = payload["token"]
    print(f"hop ssl reserved r{nxt} token={token}", flush=True)
    proc = subprocess.run(
        [sys.executable, str(SSL_MILL), "--round", str(nxt), "--staging", str(stage)],
        cwd=REPO,
        text=True,
        capture_output=True,
        check=False,
    )
    if proc.returncode != 0:
        print(proc.stdout, proc.stderr, flush=True)
        return None
    pub = txn("publish", str(SSL), "--round", str(nxt), "--token", token)
    rec = {"factory": "ssl-cert-rotation-factory", "round": nxt, "records": pub["records"]}
    print(json.dumps(rec), flush=True)
    return rec


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
            f"round_txn {' '.join(args)} failed ({proc.returncode}): {proc.stderr.strip()}"
        )
    return json.loads(proc.stdout)


def main() -> int:
    want = int(sys.argv[1]) if len(sys.argv) > 1 else 80
    published = []
    started = time.time()
    deadline = started + 5 * 60 * 60
    last = MILL.FIRST + len(MILL.PLANTS) - 1
    while len(published) < want and time.time() < deadline:
        status = txn("frontier", str(FACTORY))
        nxt = int(status["next_round"])
        reserved = sorted(FACTORY.glob("ROUND-r*.reserved.json"))
        if reserved or nxt > last:
            hopped = mill_ssl_one()
            if hopped:
                published.append(hopped)
                continue
            if reserved:
                print(f"RESERVED {reserved[0].name}; hop factories busy", flush=True)
                hop = txn("frontier", str(HOP))
                print(json.dumps({"hop": hop, "sbox_next": nxt}, indent=2), flush=True)
                # Leftover mill holds sandbox; do not busy-spin.
                break
            print(f"catalog exhausted at r{nxt} have={len(MILL.PLANTS)} last={last}", flush=True)
            break
        try:
            payload = txn("reserve", str(FACTORY), "--round", str(nxt), "--expected", "3")
        except RuntimeError as exc:
            print(f"reserve failed r{nxt}: {exc}; hop", flush=True)
            hopped = mill_ssl_one()
            if hopped:
                published.append(hopped)
            continue
        stage = Path(payload["staging_dir"])
        token = payload["token"]
        print(f"reserved r{nxt} token={token} stage={stage}", flush=True)
        MILL.write_round(nxt, stage)
        pub = txn("publish", str(FACTORY), "--round", str(nxt), "--token", token)
        published.append({"round": nxt, "family": MILL.plant_for_round(nxt)["family"],
                          "ids": [p.name for p in []], "records": pub["records"]})
        published[-1]["ids"] = [
            json.loads(line)["id"]
            for line in (FACTORY / f"batch-r{nxt:02d}.jsonl").read_text().splitlines()
            if line.strip()
        ]
        print(json.dumps(published[-1]), flush=True)
    print(json.dumps({"published": published, "seconds": round(time.time() - started, 1)}, indent=2))
    return 0 if published else 1


if __name__ == "__main__":
    raise SystemExit(main())
