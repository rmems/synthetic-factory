#!/usr/bin/env python3
"""Reserve → stage → publish one CER burst mill (cleaned round_txn driver)."""

from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

from . import record_builder as rb
from . import vocabulary as cv
from .burst_registry import plants_module


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _factory_dir(run_label: str) -> Path:
    return _repo_root() / "outputs/raw" / run_label / cv.FACTORY


def _txn(*args: str) -> dict:
    cmd = [sys.executable, str(_repo_root() / "pipelines/round_txn.py"), *args]
    out = subprocess.check_output(cmd, text=True)
    return json.loads(out)


def publish_burst_mill(
    mill_id: str,
    *,
    run_label: str = cv.DEFAULT_RUN_LABEL,
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
            raise RuntimeError(f"gave up after {max_reserve_tries} reserve tries, published {pair_i}")
        fr = _txn("frontier", str(factory))
        rnd = int(fr["next_round"])
        reserved = factory / f"ROUND-r{rnd}.reserved.json"
        if reserved.exists():
            time.sleep(0.25)
            continue
        token = first_token if pair_i == 0 and first_token else None
        if token is None:
            rsv = _txn("reserve", str(factory), "--round", str(rnd), "--expected", str(cv.QUOTA_PER_ROUND))
            token = rsv["token"]
            staging = Path(rsv["staging_dir"])
        else:
            staging = _repo_root() / (
                f"outputs/staging/{run_label}/{cv.FACTORY}/r{rnd}-{token}"
            )
            if not staging.is_dir():
                raise FileNotFoundError(staging)
        okp, badp = plants.PAIRS[pair_i]
        rec_a = rb.episode(rnd, okp)
        rec_b = rb.episode(rnd, badp)
        batch = (
            json.dumps(rec_a, separators=(",", ":"))
            + "\n"
            + json.dumps(rec_b, separators=(",", ":"))
            + "\n"
        )
        (staging / f"batch-r{rnd}.jsonl").write_text(batch)
        (staging / f"NOTES-r{rnd}.md").write_text(
            rb.notes_markdown(
                rnd,
                rec_a,
                rec_b,
                ok_slug=okp["slug"],
                fail_slug=badp["slug"],
            )
        )
        pub = _txn("publish", str(factory), "--round", str(rnd), "--token", token)
        published.append({"round": rnd, "ids": [rec_a["id"], rec_b["id"]], "publish": pub})
        pair_i += 1
        first_token = None
    return published
