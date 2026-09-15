#!/usr/bin/env python3
"""Reserve → stage → publish one PBC burst mill (cleaned round_txn driver)."""

from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

from . import record_builder as rb
from . import vocabulary as pv
from .burst_registry import plants_module

_LEAK_KEYS = (
    "thought",
    "chain_of_thought",
    "scratch",
    "inner_monologue",
    "spike_events",
)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _factory_dir(run_label: str) -> Path:
    return _repo_root() / "outputs/raw" / run_label / pv.FACTORY


def _txn(*args: str) -> dict:
    cmd = [sys.executable, str(_repo_root() / "pipelines/round_txn.py"), *args]
    out = subprocess.check_output(cmd, text=True)
    return json.loads(out)


def _guard_record(rec: dict, round_n: int) -> None:
    blob = json.dumps(rec)
    for bad in _LEAK_KEYS:
        if f'"{bad}"' in blob:
            raise ValueError(f"{rec['id']} leaked {bad}")
    if "sim_or_real" in blob and '"real"' in blob:
        raise ValueError(f"{rec['id']} claimed real")
    steps = rec["steps"]
    if not (18 <= len(steps) <= 22):
        raise ValueError(f"{rec['id']} bad step count {len(steps)}")
    if rec["meta"].get("generator") != pv.GENERATOR:
        raise ValueError(f"{rec['id']} bad generator")
    if rec["meta"].get("round") != round_n:
        raise ValueError(f"{rec['id']} round mismatch")
    if rec["meta"].get("factory") != pv.FACTORY:
        raise ValueError(f"{rec['id']} bad factory")


def publish_burst_mill(
    mill_id: str,
    *,
    run_label: str = pv.DEFAULT_RUN_LABEL,
    first_token: str | None = None,
    max_reserve_tries: int = 80,
) -> list[dict]:
    """Publish ``N_ROUNDS`` for one registered burst mill."""

    plants = plants_module(mill_id)
    factory = _factory_dir(run_label)
    published: list[dict] = []
    pair_i = 0
    tries = 0
    while pair_i < plants.N_ROUNDS:
        tries += 1
        if tries > max_reserve_tries:
            raise RuntimeError(
                f"gave up after {max_reserve_tries} reserve tries, published {pair_i}"
            )
        fr = _txn("frontier", str(factory))
        rnd = int(fr["next_round"])
        reserved = factory / f"ROUND-r{rnd}.reserved.json"
        if reserved.exists():
            time.sleep(0.25)
            continue
        token = first_token if pair_i == 0 and first_token else None
        if token is None:
            rsv = _txn(
                "reserve",
                str(factory),
                "--round",
                str(rnd),
                "--expected",
                str(pv.QUOTA_PER_ROUND),
            )
            token = rsv["token"]
            staging = Path(rsv["staging_dir"])
        else:
            staging = _repo_root() / (
                f"outputs/staging/{run_label}/{pv.FACTORY}/r{rnd}-{token}"
            )
            if not staging.is_dir():
                raise FileNotFoundError(staging)
        okp, badp = plants.PAIRS[pair_i]
        rec_a = rb.success_episode(rnd, okp)
        rec_b = rb.handoff_episode(rnd, badp)
        stamp = getattr(plants, "stamp_envelope", None)
        if callable(stamp):
            stamp(rec_a, okp)
            stamp(rec_b, badp)
        _guard_record(rec_a, rnd)
        _guard_record(rec_b, rnd)
        batch = (
            json.dumps(rec_a, separators=(",", ":"))
            + "\n"
            + json.dumps(rec_b, separators=(",", ":"))
            + "\n"
        )
        (staging / f"batch-r{rnd}.jsonl").write_text(batch)
        (staging / f"NOTES-r{rnd}.md").write_text(
            rb.notes_for(
                rnd,
                okp,
                badp,
                rec_a,
                rec_b,
                catalog_first=plants.CATALOG_FIRST,
                extra_ban=getattr(plants, "NOTES_EXTRA", ""),
                footer=getattr(plants, "NOTES_FOOTER", ""),
            )
        )
        pub = _txn("publish", str(factory), "--round", str(rnd), "--token", token)
        published.append({"round": rnd, "ids": [rec_a["id"], rec_b["id"]], "publish": pub})
        pair_i += 1
        first_token = None
    return published
