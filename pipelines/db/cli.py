#!/usr/bin/env python3
"""CLI for the cleaned db mill: check, smoke/emit (fresh dirs), and loop."""

from __future__ import annotations

import json
import sys
import tempfile
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any, NamedTuple

from . import config as cfg
from . import episode as ep_mod
from .check import self_check
from .import_twins import bind_import_twin
from .notes import emit_stage

__all__ = ["main", "run_loop"]


class _RoundTxn(NamedTuple):
    """The transactional-writer entry points ``run_loop`` publishes through."""

    transaction_error: type[Exception]
    abort: Callable[..., Any]
    frontier_status: Callable[..., Any]
    publish: Callable[..., Any]
    reserve: Callable[..., Any]


def _hop_reserved_round(factory: Path, round_n: int, hops: list[dict]) -> bool:
    """Record a hop when another writer already holds ``round_n``."""
    if not (factory / f"ROUND-r{round_n:02d}.reserved.json").exists():
        return False
    hops.append({"dbm_next": round_n, "dbm_reserved": True, "action": "HOP", "stolen": False})
    print(json.dumps({"hop": hops[-1]}), flush=True)
    time.sleep(0.08)
    return True


def _catalog_has_round(round_n: int) -> bool:
    try:
        ep_mod.pair_for(round_n)
    except KeyError as exc:
        print(f"STOP: {exc}")
        return False
    return True


def _reserve_or_hop(txn: _RoundTxn, factory: Path, round_n: int, hops: list[dict]) -> dict | None:
    """Reserve ``round_n``; ``None`` records a hop for a lost race, anything else re-raises."""
    try:
        return txn.reserve(factory, round_n, 2)
    except txn.transaction_error as exc:
        msg = str(exc)
        print(f"reserve failed r{round_n}: {exc}", flush=True)
        if "already exists" in msg or "not the frontier" in msg:
            hops.append({"dbm_next": round_n, "error": msg, "stolen": False, "action": "HOP"})
            print(json.dumps({"hop": hops[-1]}), flush=True)
            time.sleep(0.04)
            return None
        raise


def _stage_and_publish(txn: _RoundTxn, factory: Path, round_n: int, payload: dict) -> dict:
    """Stage and publish one reserved round; abort the reservation on any failure."""
    stage, token = Path(payload["staging_dir"]), payload["token"]
    try:
        ids = emit_stage(stage, round_n)
        manifest = txn.publish(factory, round_n, token)
    except Exception as exc:
        try:
            txn.abort(factory, round_n, token)
        except Exception as abort_exc:  # noqa: BLE001 - report, then chain
            print(f"abort failed r{round_n}: {abort_exc}")
        raise RuntimeError(f"stage/publish failed r{round_n}: {exc}") from exc
    return {"round": round_n, "ids": ids, "records": manifest.get("records")}


def _round_txn() -> _RoundTxn:
    # Deferred: round_txn is only needed for live publication, not for check/emit.
    if (__package__ or "").startswith("pipelines."):
        from ..round_txn import TransactionError, abort, frontier_status, publish, reserve
    else:
        from round_txn import TransactionError, abort, frontier_status, publish, reserve
    return _RoundTxn(TransactionError, abort, frontier_status, publish, reserve)


def _loop_summary(published: list[dict], hops: list[dict]) -> int:
    print(json.dumps({"published_rounds": [p["round"] for p in published], "hops": hops}))
    return 0 if published else 1


def run_loop(min_rounds: int = 12, max_rounds: int = 16, minutes: float = 40.0) -> int:
    """Publish rounds via the transactional writer; deferred import keeps ``import`` pure."""
    txn = _round_txn()
    factory = Path(__file__).resolve().parents[2] / "outputs" / "raw" / "2026-08-19-agentic" / "db-migration-repair-factory"
    published: list[dict] = []
    hops: list[dict] = []
    deadline = time.monotonic() + minutes * 60
    while len(published) < max_rounds:
        if len(published) >= min_rounds and time.monotonic() >= deadline:
            break
        status = txn.frontier_status(factory)
        round_n = status["next_round"]
        if _hop_reserved_round(factory, round_n, hops):
            continue
        if not _catalog_has_round(round_n):
            break
        payload = _reserve_or_hop(txn, factory, round_n, hops)
        if payload is None:
            continue
        published.append(_stage_and_publish(txn, factory, round_n, payload))
        print(json.dumps({"published": published[-1]}), flush=True)
    return _loop_summary(published, hops)


def _check_command(argv: list[str]) -> int:
    self_check()
    if argv and argv[0] == "--smoke":
        with tempfile.TemporaryDirectory(prefix="dbm-unique-smoke-") as td:
            dest = Path(td)
            print(json.dumps({"smoke_ids": emit_stage(dest, cfg.START_ROUND)}))
    return 0


def _emit_command(argv: list[str]) -> int:
    round_n, dest = int(argv[1]), Path(argv[2])
    dest.mkdir(parents=True, exist_ok=True)
    print(json.dumps({"ids": emit_stage(dest, round_n)}))
    return 0


def _loop_command(argv: list[str]) -> int:
    self_check()
    min_rounds = int(argv[1]) if len(argv) > 1 else cfg.MIN_ROUNDS
    max_rounds = int(argv[2]) if len(argv) > 2 else cfg.MAX_ROUNDS
    return run_loop(min_rounds=min_rounds, max_rounds=max_rounds)


def main(argv: list[str] | None = None) -> int:
    """Entry point; never writes except into a caller-provided fresh directory."""
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0] in ("check", "--smoke"):
        return _check_command(argv)
    if argv[0] == "emit":
        return _emit_command(argv)
    if argv[0] == "loop":
        return _loop_command(argv)
    raise SystemExit("usage: db.cli [check|--smoke|emit N DIR|loop [min] [max]]")


bind_import_twin(__name__)

if __name__ == "__main__":
    raise SystemExit(main())
