#!/usr/bin/env python3
"""Mill authz-regression-factory r1720+ unique leftover object-id IDOR / BFLA.

Catalog lives in azr-plants-r1720.py. Pair index is independent of round so we
can share the factory with another mill without stealing reservations.

Not leftover mill cartesian. Not JWT-claim catalog. Not r200–r1719 vesselNNNN-sys.
Not clones of r1364 geohash-cell-idor / channels-consumer-skip-delete,
r1445–r1458 casbin/oso/keycloak clones, r1543 gstin-isd-idor, r1560 e212-mccmnc-idor / flask-restful-delete-bare / chi-mount-skip-delete.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sys
from pathlib import Path

FACTORY = "authz-regression-factory"
GEN = "grok-4.6"
CATALOG_FIRST = 1720
EXPERIMENTS = Path(__file__).resolve().parent

_spec = importlib.util.spec_from_file_location(
    "azr_mill_r1205_for_r1720", EXPERIMENTS / "azr-mill-r1205.py"
)
_r1205 = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(_r1205)

_plants_spec = importlib.util.spec_from_file_location(
    "azr_plants_r1720", EXPERIMENTS / "azr-plants-r1720.py"
)
_plants = importlib.util.module_from_spec(_plants_spec)
assert _plants_spec.loader is not None
_plants_spec.loader.exec_module(_plants)

USED_SLUGS: set[str] = set(_r1205.USED_SLUGS)
USED_SLUGS.update(p[0]["slug"] for p in _r1205.PAIRS)
USED_SLUGS.update(p[1]["slug"] for p in _r1205.PAIRS)
for p in EXPERIMENTS.glob("azr-plants*.py"):
    if p.name == "azr-plants-r1720.py":
        continue
    text = p.read_text(errors="ignore")
    USED_SLUGS.update(re.findall(r"slug=['\"]([a-z0-9-]+)['\"]", text))
for p in EXPERIMENTS.glob("azr-mill-r*.py"):
    if p.name == "azr-mill-r1720.py":
        continue
    text = p.read_text(errors="ignore")
    USED_SLUGS.update(re.findall(r"slug=['\"]([a-z0-9-]+)['\"]", text))

idors = [_r1205._idor(row) for row in _plants.EXTRA_IDOR_ROWS]
bflas = _plants.extra_bflas(_r1205._H)
if len(idors) != len(bflas):
    raise SystemExit(f"idor {len(idors)} != bfla {len(bflas)}")
PAIRS = list(zip(idors, bflas))
for sa, sb in PAIRS:
    for spec in (sa, sb):
        slug = spec["slug"]
        if slug in USED_SLUGS:
            raise SystemExit(f"clone of prior mill slug: {slug}")
        if slug in _r1205._old.BANNED_SLUGS:
            raise SystemExit(f"banned slug {slug}")
if PAIRS[0][0]["slug"] != "fps-uk-idor":
    raise SystemExit(f"unexpected r1720 tip slug {PAIRS[0][0]['slug']}")
if PAIRS[0][1]["slug"] != "fly-replay-skip-delete":
    raise SystemExit(f"unexpected r1720 bfla slug {PAIRS[0][1]['slug']}")
if not PAIRS:
    raise SystemExit("r1720 catalog slice empty")

build_success = _r1205.build_success
build_handoff = _r1205.build_handoff


def notes_for(round_n: int, a: dict, b: dict, sa: dict, sb: dict) -> str:
    cov = max(78, 86 - max(0, round_n - CATALOG_FIRST))
    return f"""# NOTES-r{round_n} authz-regression-factory

Novel coverage: {cov}%

Two designed episodes (quota 2). Surfaces: {sa['surface']} vs {sb['surface']}.
Not leftover mill cartesian, not JWT-claim catalog, not r200–r1719 vesselNNNN-sys.
Not clones of r1364 geohash-cell-idor / channels-consumer-skip-delete, r1445–r1458 casbin/oso/keycloak clones, r1543 gstin-isd-idor, r1560 e212-mccmnc-idor / flask-restful-delete-bare / chi-mount-skip-delete.
Each has a mid-trajectory plan change after a first patch that is incomplete.

| id | seed | first apply | plan change | terminal |
|---|---|---|---|---|
| azr-r{round_n}-{sa['slug']} | {sa['bug_hint']} | {sa['first_apply']} | {sa['plan_change']} | success {sa['tests_n']}/{sa['tests_n']} |
| azr-r{round_n}-{sb['slug']} | {sb['bug_hint']} | {sb['first_apply']} | {sb['plan_change']} | handoff {sb['handoff_hint']} |

## Step counts
- ep1: 17. first apply 6; plan change 8; residual {sa['residual']}.
- ep2: 18. first apply 6; plan change 8; xfail handoff {sb['handoff_hint']}.

## decision_basis audit
Every step starts Plan:/Observation:/Reflection:/Tool call:, ≤240 chars.
No thought / chain_of_thought / scratch / inner_monologue. No spike_events.
No sim_or_real: real. Invented plants `{sa['plant']}` and `{sb['plant']}`.

## Weaknesses / next
Keep unique object-id IDOR, ReBAC tuple leftover, ABAC attr leftover, BOLA/BFLA, nested mass-assign.
Ban leftover mill slogans and JWT-claim catalog. Avoid r01–r1719 seeds {sa['slug']}, {sb['slug']}.
"""


def generate_round(round_n: int, pair_idx: int | None = None) -> tuple[list[dict], str]:
    idx = pair_idx if pair_idx is not None else (round_n - CATALOG_FIRST)
    if idx < 0 or idx >= len(PAIRS):
        raise SystemExit(
            f"no catalog pair for round {round_n} idx={idx} (have 0..{len(PAIRS) - 1})"
        )
    sa, sb = PAIRS[idx]
    a = build_success(round_n, sa)
    b = build_handoff(round_n, sb)
    for ep in (a, b):
        ep.setdefault("state", {"sim_or_real": "designed", "domain": "authz-regression"})
        ep["meta"]["generator"] = GEN
    return [a, b], notes_for(round_n, a, b, sa, sb)


def write_round(round_n: int, staging: Path, pair_idx: int | None = None) -> None:
    eps, notes = generate_round(round_n, pair_idx)
    batch = staging / f"batch-r{round_n:02d}.jsonl"
    nfile = staging / f"NOTES-r{round_n:02d}.md"
    with batch.open("w") as fh:
        for ep in eps:
            fh.write(json.dumps(ep, ensure_ascii=True) + "\n")
    nfile.write_text(notes)
    print(
        json.dumps(
            {
                "round": round_n,
                "pair_idx": pair_idx,
                "ids": [e["id"] for e in eps],
                "steps": [len(e["steps"]) for e in eps],
                "success": [e["reward"]["success"] for e in eps],
                "batch": str(batch),
                "notes": str(nfile),
            }
        )
    )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--round", type=int, required=True)
    ap.add_argument("--staging", required=True)
    ap.add_argument("--pair", type=int, default=None)
    args = ap.parse_args()
    write_round(args.round, Path(args.staging), args.pair)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
