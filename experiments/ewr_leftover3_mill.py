#!/usr/bin/env python3
"""email-webhook leftover leftover leftover mill: 16 rounds, Q=2.

BAN r39 beehiiv / constant-contact / invoice-row-dup. Skip Postmark Streams.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

EXPERIMENTS = Path(__file__).resolve().parent
REPO = EXPERIMENTS.parent
sys.path.insert(0, str(EXPERIMENTS))
sys.path.insert(0, str(REPO / "pipelines"))

from ewr_leftover3_plants import PAIRS  # noqa: E402
from hopper_mill_g46d import (  # noqa: E402
    build_pair,
    dumps_episode,
)

FACTORY = "email-webhook-retry-factory"
FACTORY_DIR = REPO / "outputs" / "raw" / "2026-08-19-agentic" / FACTORY
START = 40
N = 16


def self_check() -> None:
    slugs, mods, tickets, domains = [], [], [], []
    for i, (ok, bad) in enumerate(PAIRS):
        if ok["first_old"] not in ok["src_body"]:
            raise ValueError(ok["slug"])
        if bad["first_old"] not in bad["src_body"]:
            raise ValueError(bad["slug"])
        slugs.extend((ok["slug"], bad["slug"]))
        mods.extend((ok["mod"], bad["mod"]))
        tickets.append(bad["ticket"])
        domains.extend((ok["domain"], bad["domain"]))
        if "beehiiv" in ok["slug"] or "constant-contact" in bad["slug"]:
            raise ValueError("banned r39 clone")
        build_pair(FACTORY, START + i, ok, bad)
    if len(set(slugs)) != len(slugs):
        raise ValueError(f"dup slugs {slugs}")
    if len(set(mods)) != len(mods):
        raise ValueError(f"dup mods {mods}")
    if len(set(tickets)) != len(tickets):
        raise ValueError(f"dup tickets {tickets}")
    if len(set(domains)) != len(domains):
        raise ValueError(f"dup domains {domains}")
    if len(PAIRS) != N:
        raise ValueError(f"need {N} pairs, got {len(PAIRS)}")
    print(f"self_check ok: {N} leftover leftover leftover pairs")


def reserve(round_n: int) -> dict:
    from round_txn import reserve

    return reserve(FACTORY_DIR, round_n, expected=2)


def publish(round_n: int, token: str) -> None:
    from round_txn import publish as _pub

    _pub(FACTORY_DIR, round_n, token)


def emit(stage: Path, round_n: int, ok: dict, bad: dict) -> tuple[str, str]:
    ok_ep, bad_ep, notes = build_pair(FACTORY, round_n, ok, bad)
    (stage / f"batch-r{round_n:02d}.jsonl").write_text(
        dumps_episode(ok_ep) + "\n" + dumps_episode(bad_ep) + "\n",
        encoding="utf-8",
    )
    (stage / f"NOTES-r{round_n:02d}.md").write_text(notes, encoding="utf-8")
    return ok_ep["id"], bad_ep["id"]


def main() -> int:
    self_check()
    published: list[tuple[int, str, str]] = []
    for i, (ok, bad) in enumerate(PAIRS):
        round_n = START + i
        reserved = FACTORY_DIR / f"ROUND-r{round_n:02d}.reserved.json"
        complete = FACTORY_DIR / f"ROUND-r{round_n:02d}.complete.json"
        if complete.exists():
            print(f"skip published r{round_n}")
            continue
        if reserved.exists():
            print(f"reserved r{round_n}; hop would apply — abort this mill seat")
            return 2
        try:
            info = reserve(round_n)
        except Exception as exc:
            print(f"reserve r{round_n} failed: {exc}")
            return 3
        token = info["token"]
        stage = Path(info["staging_dir"])
        ids = emit(stage, round_n, ok, bad)
        publish(round_n, token)
        published.append((round_n, ids[0], ids[1]))
        print(f"published r{round_n} {ids[0]} {ids[1]}")
    print("PUBLISHED", published)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
