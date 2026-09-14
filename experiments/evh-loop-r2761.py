#!/usr/bin/env python3
"""Reserve-stage-publish eval-harness leftover mill r2761+ (no hop)."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
MILL = REPO / "scripts" / "eval_harness_unique_mill"
sys.path.insert(0, str(MILL))
sys.path.insert(0, str(REPO / "pipelines"))

import mill  # noqa: E402
from round_txn import (  # noqa: E402
    TransactionError,
    abort,
    frontier_status,
    publish,
    reserve,
)

COV_RE = re.compile(r"Novel coverage:\s*(\d+)%")
MAX_ROUNDS = 26
FACTORY = mill.FACTORY


def coverage_from_notes(round_n: int) -> int:
    text = (FACTORY / f"NOTES-r{round_n:02d}.md").read_text(encoding="utf-8")
    match = COV_RE.search(text)
    if not match:
        raise SystemExit(f"missing Novel coverage in NOTES-r{round_n:02d}.md")
    return int(match.group(1))


def main() -> int:
    published: list[dict] = []
    low_streak = 0
    while len(published) < MAX_ROUNDS:
        status = frontier_status(FACTORY)
        round_n = status["next_round"]
        reserved = FACTORY / f"ROUND-r{round_n:02d}.reserved.json"
        if reserved.exists():
            print(
                json.dumps({"stop": "foreign reservation", "round": round_n}),
                flush=True,
            )
            break
        try:
            mill.pair_for(round_n)
        except KeyError:
            print(json.dumps({"stop": "plants exhausted", "next": round_n}), flush=True)
            break
        try:
            payload = reserve(FACTORY, round_n, 2)
        except TransactionError as exc:
            print(
                json.dumps(
                    {
                        "stop": "reserve failed",
                        "round": round_n,
                        "error": str(exc),
                    }
                ),
                flush=True,
            )
            break
        stage = Path(payload["staging_dir"])
        token = payload["token"]
        try:
            ids = mill.emit_stage(stage, round_n)
            manifest = publish(FACTORY, round_n, token)
        except Exception as exc:
            try:
                abort(FACTORY, round_n, token)
            except Exception as abort_exc:
                print(
                    json.dumps(
                        {
                            "held": round_n,
                            "token": token,
                            "stage": str(stage),
                            "error": str(exc),
                            "abort": str(abort_exc),
                        }
                    ),
                    flush=True,
                )
                return 2
            print(
                json.dumps(
                    {
                        "stop": "stage/publish failed",
                        "round": round_n,
                        "error": str(exc),
                    }
                ),
                flush=True,
            )
            return 2
        cov = coverage_from_notes(round_n)
        rec = {
            "round": round_n,
            "ids": ids,
            "records": manifest.get("records"),
            "coverage": cov,
        }
        published.append(rec)
        print(json.dumps({"published": rec}), flush=True)
        if cov < 5:
            low_streak += 1
            if low_streak >= 2:
                print(
                    json.dumps(
                        {
                            "stop": "two consecutive NOTES <5%",
                            "rounds": [p["round"] for p in published[-2:]],
                        }
                    ),
                    flush=True,
                )
                break
        else:
            low_streak = 0
    print(
        json.dumps(
            {
                "published_rounds": [p["round"] for p in published],
                "count": len(published),
            }
        ),
        flush=True,
    )
    return 0 if published else 1


if __name__ == "__main__":
    raise SystemExit(main())
