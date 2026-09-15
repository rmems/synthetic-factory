#!/usr/bin/env python3
"""CLI for the cleaned db mill: check, smoke/emit (fresh dirs), and loop."""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

from . import config as cfg
from . import episode as ep_mod
from .check import self_check
from .import_twins import bind_import_twin
from .notes import emit_stage

__all__ = ["main", "run_loop"]


def run_loop(min_rounds: int = 12, max_rounds: int = 16, minutes: float = 40.0) -> int:
    """Publish rounds via the transactional writer; deferred import keeps ``import`` pure."""
    # Deferred: round_txn is only needed for live publication, not for check/emit.
    from round_txn import TransactionError, abort, frontier_status, publish, reserve

    factory = Path(__file__).resolve().parents[2] / "outputs" / "raw" / "2026-08-19-agentic" / "db-migration-repair-factory"
    published: list[dict] = []
    hops: list[dict] = []
    deadline = time.monotonic() + minutes * 60
    while len(published) < max_rounds and time.monotonic() < deadline:
        status = frontier_status(factory)
        round_n = status["next_round"]
        if (factory / f"ROUND-r{round_n:02d}.reserved.json").exists():
            hops.append({"dbm_next": round_n, "dbm_reserved": True, "action": "HOP", "stolen": False})
            print(json.dumps({"hop": hops[-1]}), flush=True)
            time.sleep(0.08)
            continue
        try:
            ep_mod.pair_for(round_n)
        except KeyError as exc:
            print(f"STOP: {exc}")
            break
        try:
            payload = reserve(factory, round_n, 2)
        except TransactionError as exc:
            msg = str(exc)
            print(f"reserve failed r{round_n}: {exc}", flush=True)
            if "already exists" in msg or "not the frontier" in msg:
                hops.append({"dbm_next": round_n, "error": msg, "stolen": False, "action": "HOP"})
                print(json.dumps({"hop": hops[-1]}), flush=True)
                time.sleep(0.04)
                continue
            raise
        stage, token = Path(payload["staging_dir"]), payload["token"]
        try:
            ids = emit_stage(stage, round_n)
            manifest = publish(factory, round_n, token)
        except Exception as exc:
            try:
                abort(factory, round_n, token)
            except Exception as abort_exc:  # noqa: BLE001 - report, then chain
                print(f"abort failed r{round_n}: {abort_exc}")
            raise RuntimeError(f"stage/publish failed r{round_n}: {exc}") from exc
        published.append({"round": round_n, "ids": ids, "records": manifest.get("records")})
        print(json.dumps({"published": published[-1]}), flush=True)
        if len(published) >= min_rounds and time.monotonic() >= deadline:
            break
    print(json.dumps({"published_rounds": [p["round"] for p in published], "hops": hops}))
    return 0 if published else 1


def main(argv: list[str] | None = None) -> int:
    """Entry point; never writes except into a caller-provided fresh directory."""
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0] in ("check", "--smoke"):
        self_check()
        if argv and argv[0] == "--smoke":
            dest = Path("/tmp/dbm-unique-smoke")
            dest.mkdir(parents=True, exist_ok=True)
            print(json.dumps({"smoke_ids": emit_stage(dest, cfg.START_ROUND)}))
        return 0
    if argv[0] == "emit":
        round_n, dest = int(argv[1]), Path(argv[2])
        dest.mkdir(parents=True, exist_ok=True)
        print(json.dumps({"ids": emit_stage(dest, round_n)}))
        return 0
    if argv[0] == "loop":
        self_check()
        min_rounds = int(argv[1]) if len(argv) > 1 else cfg.MIN_ROUNDS
        max_rounds = int(argv[2]) if len(argv) > 2 else cfg.MAX_ROUNDS
        return run_loop(min_rounds=min_rounds, max_rounds=max_rounds)
    raise SystemExit("usage: db.cli [check|--smoke|emit N DIR|loop [min] [max]]")


bind_import_twin(__name__)

if __name__ == "__main__":
    raise SystemExit(main())
