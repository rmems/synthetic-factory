#!/usr/bin/env python3
"""websocket-reconnect unique mill r73+. Never steal. Never rewrite raw."""
from __future__ import annotations

import json
import sys
from pathlib import Path

EXPERIMENTS = Path(__file__).resolve().parent
REPO = EXPERIMENTS.parent
sys.path.insert(0, str(EXPERIMENTS))

from importlib.machinery import SourceFileLoader

from hopper_mill_g46d import (  # noqa: E402
    GENERATOR,
    assert_clean,
    build_fail,
    build_success,
    dumps_episode,
    notes_md,
    validate_pair,
)

_plants = SourceFileLoader(
    "wsr_plants_r73", str(EXPERIMENTS / "wsr-plants-r73.py")
).load_module()
PAIRS = _plants.PAIRS

FACTORY = "websocket-reconnect-factory"
PREFIX = "wsr"
BAN = {
    "anycable-restore-session",
    "reverb-activity-timeout-handoff",
    "cookie-replay",
}


def harvest_used(factory_dir: Path) -> set[str]:
    used: set[str] = set()
    for notes in factory_dir.glob("NOTES-r*.md"):
        for line in notes.read_text(encoding="utf-8").splitlines():
            if "`wsr-r" in line:
                for token in line.split("`"):
                    if token.startswith("wsr-r") and "-" in token:
                        seed = "-".join(token.split("-")[2:])
                        if seed:
                            used.add(seed)
    return used


def next_free_idx(used: set[str], start: int = 0) -> int | None:
    for i in range(start, len(PAIRS)):
        okp, badp = PAIRS[i]
        if okp["slug"] in BAN or badp["slug"] in BAN:
            continue
        if okp["slug"] not in used and badp["slug"] not in used:
            return i
    return None


def emit_stage(stage: Path, round_n: int, ok: dict, bad: dict):
    ok_ep = build_success(FACTORY, PREFIX, round_n, ok)
    bad_ep = build_fail(FACTORY, PREFIX, round_n, bad)
    validate_pair(ok_ep, bad_ep, round_n)
    notes = notes_md(FACTORY, round_n, ok, bad, ok_ep["id"], bad_ep["id"])
    if "Novel coverage:" not in notes:
        raise ValueError("NOTES missing Novel coverage")
    batch = stage / f"batch-r{round_n:02d}.jsonl"
    notes_path = stage / f"NOTES-r{round_n:02d}.md"
    batch.write_text(
        dumps_episode(ok_ep) + "\n" + dumps_episode(bad_ep) + "\n",
        encoding="utf-8",
    )
    notes_path.write_text(notes, encoding="utf-8")
    return ok_ep["id"], bad_ep["id"]


def self_check() -> None:
    slugs, mods, tickets, domains = [], [], [], []
    for i, (okp, badp) in enumerate(PAIRS):
        if okp["slug"] in BAN or badp["slug"] in BAN:
            raise ValueError("BAN in catalog")
        if okp["first_old"] not in okp["src_body"]:
            raise ValueError(okp["slug"])
        if badp["first_old"] not in badp["src_body"]:
            raise ValueError(badp["slug"])
        for plant, kind in ((okp, "ok"), (badp, "bad")):
            slugs.append(plant["slug"])
            mods.append(plant["mod"])
            domains.append(plant["domain"])
            if kind == "bad":
                tickets.append(plant["ticket"])
        ok_ep = build_success(FACTORY, PREFIX, 73 + i, okp)
        bad_ep = build_fail(FACTORY, PREFIX, 73 + i, badp)
        validate_pair(ok_ep, bad_ep, 73 + i)
        assert_clean(ok_ep)
        assert_clean(bad_ep)
    if len(set(slugs)) != len(slugs):
        raise ValueError(f"dup slugs {slugs}")
    if len(set(mods)) != len(mods):
        raise ValueError(f"dup mods {mods}")
    if len(set(tickets)) != len(tickets):
        raise ValueError(f"dup tickets {tickets}")
    if len(set(domains)) != len(domains):
        raise ValueError(f"dup domains {domains}")
    print(f"self_check ok: {len(PAIRS)} pairs generator={GENERATOR}")


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv[:1] == ["self_check"]:
        self_check()
        return 0
    if "--round" in argv and "--staging" in argv:
        round_n = int(argv[argv.index("--round") + 1])
        stage = Path(argv[argv.index("--staging") + 1])
        factory_dir = REPO / "outputs/raw/2026-08-19-agentic/websocket-reconnect-factory"
        used = harvest_used(factory_dir)
        idx = int(argv[argv.index("--idx") + 1]) if "--idx" in argv else next_free_idx(used)
        if idx is None:
            raise SystemExit("wsr catalog exhausted")
        okp, badp = PAIRS[idx]
        if okp["slug"] in used or badp["slug"] in used:
            raise SystemExit(f"used slug {okp['slug']} {badp['slug']}")
        ids = emit_stage(stage, round_n, okp, badp)
        print(json.dumps({"round": round_n, "idx": idx, "ids": ids}))
        return 0
    self_check()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
