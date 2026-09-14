#!/usr/bin/env python3
"""queue-backpressure mill r94+. Never steal."""
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
    "qbp_plants_r94", str(EXPERIMENTS / "qbp-plants-r94.py")
).load_module()
CATALOG_FIRST = _plants.CATALOG_FIRST
PAIRS = _plants.PAIRS

FACTORY = "queue-backpressure-factory"
PREFIX = "qbp"
BAN = {"disruptor-buffer-vs-timeout", "chronicle-cycle-handoff"}


def harvest_used(factory_dir: Path) -> set[str]:
    used: set[str] = set()
    for notes in factory_dir.glob("NOTES-r*.md"):
        for line in notes.read_text(encoding="utf-8").splitlines():
            if "`qbp-r" in line:
                for token in line.split("`"):
                    if token.startswith("qbp-r") and "-" in token:
                        seed = "-".join(token.split("-")[2:])
                        if seed:
                            used.add(seed)
    return used


def pair_for_round(round_n: int, used: set[str]):
    idx = round_n - CATALOG_FIRST
    if idx < 0 or idx >= len(PAIRS):
        raise ValueError(f"round {round_n} outside catalog {CATALOG_FIRST}+{len(PAIRS)}")
    ok, bad = PAIRS[idx]
    if ok["slug"] in BAN or bad["slug"] in BAN:
        raise ValueError(f"BAN slug at r{round_n}")
    if ok["slug"] in used or bad["slug"] in used:
        raise ValueError(f"used slug at r{round_n}: {ok['slug']} {bad['slug']}")
    return ok, bad


def emit_stage(stage: Path, round_n: int, ok: dict, bad: dict):
    ok_ep = build_success(FACTORY, PREFIX, round_n, ok)
    bad_ep = build_fail(FACTORY, PREFIX, round_n, bad)
    validate_pair(ok_ep, bad_ep, round_n)
    notes = notes_md(FACTORY, round_n, ok, bad, ok_ep["id"], bad_ep["id"])
    if "Novel coverage:" not in notes:
        raise ValueError("NOTES missing Novel coverage")
    (stage / f"batch-r{round_n:02d}.jsonl").write_text(
        dumps_episode(ok_ep) + "\n" + dumps_episode(bad_ep) + "\n",
        encoding="utf-8",
    )
    (stage / f"NOTES-r{round_n:02d}.md").write_text(notes, encoding="utf-8")
    return ok_ep["id"], bad_ep["id"]


def self_check() -> None:
    slugs, mods, tickets, domains = [], [], [], []
    for i, (ok, bad) in enumerate(PAIRS):
        round_n = CATALOG_FIRST + i
        if ok["first_old"] not in ok["src_body"]:
            raise ValueError(ok["slug"])
        if bad["first_old"] not in bad["src_body"]:
            raise ValueError(bad["slug"])
        for plant, kind in ((ok, "ok"), (bad, "bad")):
            slugs.append(plant["slug"])
            mods.append(plant["mod"])
            domains.append(plant["domain"])
            if kind == "bad":
                tickets.append(plant["ticket"])
        ok_ep = build_success(FACTORY, PREFIX, round_n, ok)
        bad_ep = build_fail(FACTORY, PREFIX, round_n, bad)
        validate_pair(ok_ep, bad_ep, round_n)
        assert_clean(ok_ep)
        assert_clean(bad_ep)
    if len(set(slugs)) != len(slugs):
        raise ValueError("dup slugs")
    if len(set(mods)) != len(mods):
        raise ValueError("dup mods")
    if len(set(tickets)) != len(tickets):
        raise ValueError("dup tickets")
    if len(set(domains)) != len(domains):
        raise ValueError("dup domains")
    print(f"self_check ok: {len(PAIRS)} pairs CATALOG_FIRST={CATALOG_FIRST} generator={GENERATOR}")


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv[:1] == ["self_check"]:
        self_check()
        return 0
    if "--round" in argv and "--staging" in argv:
        round_n = int(argv[argv.index("--round") + 1])
        stage = Path(argv[argv.index("--staging") + 1])
        factory_dir = REPO / "outputs/raw/2026-08-19-agentic/queue-backpressure-factory"
        used = harvest_used(factory_dir)
        ok, bad = pair_for_round(round_n, used)
        ids = emit_stage(stage, round_n, ok, bad)
        print(json.dumps({"round": round_n, "ids": ids}))
        return 0
    self_check()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
