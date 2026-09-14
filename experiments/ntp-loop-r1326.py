#!/usr/bin/env python3
"""Prefer NTP: frontier → reserve --expected 2 → mill → publish.

Keep looping. Do not exit after one batch. Never steal. Never rewrite raw.
If NTP is reserved, hop another unreserved named factory (never sandbox-refusal
if reserved or writing), then immediately retry NTP.
"""
from __future__ import annotations

import json
import subprocess
import time
from pathlib import Path

ROOT = Path("/home/raulmc/rmems/synthetic-factory")
AGENTIC = ROOT / "outputs/raw/2026-08-19-agentic"
DIR = AGENTIC / "notebook-to-pipeline-factory"
TXN = ["python3", str(ROOT / "pipelines/round_txn.py")]
NTP_GEN = ["python3", str(ROOT / "experiments/ntp-mill-r1326.py")]
OBS_DIR = AGENTIC / "observability-debug-factory"
OBS_GEN = ROOT / "experiments/obs-mill-r401.py"
GQL_DIR = AGENTIC / "graphql-nplusone-factory"
GQL_GEN = ROOT / "experiments/gql-mill-r232.py"
SKIP_HOP = {"sandbox-refusal-factory"}
MAX_SECONDS = 6 * 60 * 60
TARGET_ROUNDS = 200


def run(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=str(ROOT), capture_output=True, text=True)


def reserved_here(factory: Path) -> list[Path]:
    return sorted(factory.glob("ROUND-r*.reserved.json"))


def frontier_n(factory: Path) -> int | None:
    fr = run(TXN + ["frontier", str(factory)])
    if fr.returncode != 0:
        return None
    try:
        return int(json.loads(fr.stdout)["next_round"])
    except (json.JSONDecodeError, KeyError, TypeError, ValueError):
        return None


def publish_ntp(n: int) -> tuple[bool, str]:
    rsv = run(TXN + ["reserve", str(DIR), "--round", str(n), "--expected", "2"])
    if rsv.returncode != 0:
        return False, (rsv.stderr or rsv.stdout)[-600:]
    payload = json.loads(rsv.stdout)
    rnd = payload["round"]
    staging = payload["staging_dir"]
    token = payload["token"]
    g = run(NTP_GEN + [str(rnd), staging])
    if g.returncode != 0:
        msg = (g.stderr or g.stdout)[-800:]
        run(TXN + ["abort", str(DIR), "--round", str(rnd), "--token", token])
        return False, msg
    pub = run(TXN + ["publish", str(DIR), "--round", str(rnd), "--token", token])
    if pub.returncode != 0:
        return False, (pub.stderr or pub.stdout)[-800:]
    return True, f"NTP r{rnd} {g.stdout.strip()}"


def publish_obs(n: int) -> tuple[bool, str]:
    rsv = run(TXN + ["reserve", str(OBS_DIR), "--round", str(n), "--expected", "2"])
    if rsv.returncode != 0:
        return False, (rsv.stderr or rsv.stdout)[-400:]
    payload = json.loads(rsv.stdout)
    rnd = payload["round"]
    staging = payload["staging_dir"]
    token = payload["token"]
    g = run(["python3", str(OBS_GEN), "--round", str(rnd), "--staging", staging])
    if g.returncode != 0:
        run(TXN + ["abort", str(OBS_DIR), "--round", str(rnd), "--token", token])
        return False, (g.stderr or g.stdout)[-600:]
    pub = run(TXN + ["publish", str(OBS_DIR), "--round", str(rnd), "--token", token])
    if pub.returncode != 0:
        return False, (pub.stderr or pub.stdout)[-400:]
    return True, f"HOP-OBS r{rnd} {g.stdout.strip()}"


def publish_gql(n: int) -> tuple[bool, str]:
    rsv = run(TXN + ["reserve", str(GQL_DIR), "--round", str(n), "--expected", "2"])
    if rsv.returncode != 0:
        return False, (rsv.stderr or rsv.stdout)[-400:]
    payload = json.loads(rsv.stdout)
    rnd = payload["round"]
    staging = payload["staging_dir"]
    token = payload["token"]
    g = run(
        [
            "python3",
            str(GQL_GEN),
            "--round",
            str(rnd),
            "--staging",
            staging,
            "--batch-file",
            f"batch-r{rnd:02d}.jsonl",
            "--notes-file",
            f"NOTES-r{rnd:02d}.md",
        ]
    )
    if g.returncode != 0:
        run(TXN + ["abort", str(GQL_DIR), "--round", str(rnd), "--token", token])
        return False, (g.stderr or g.stdout)[-600:]
    pub = run(TXN + ["publish", str(GQL_DIR), "--round", str(rnd), "--token", token])
    if pub.returncode != 0:
        return False, (pub.stderr or pub.stdout)[-400:]
    return True, f"HOP-GQL r{rnd} {g.stdout.strip()}"


def hop_one() -> str | None:
    if not reserved_here(OBS_DIR):
        n = frontier_n(OBS_DIR)
        if n is not None and 401 <= n <= 468:
            ok, msg = publish_obs(n)
            print(msg, flush=True)
            if ok:
                return msg
    if not reserved_here(GQL_DIR):
        n = frontier_n(GQL_DIR)
        if n is not None and 232 <= n <= 280:
            ok, msg = publish_gql(n)
            print(msg, flush=True)
            if ok:
                return msg
    hops = [
        d.name
        for d in sorted(AGENTIC.iterdir())
        if d.is_dir() and d.name not in SKIP_HOP and not reserved_here(d)
    ]
    print(f"HOP no mill seat; unreserved={hops[:8]}", flush=True)
    return None


def main() -> int:
    t0 = time.time()
    published: list[str] = []
    errors: list[dict] = []
    consecutive_fail = 0
    while time.time() - t0 < MAX_SECONDS and len(published) < TARGET_ROUNDS and consecutive_fail < 12:
        leftover = reserved_here(DIR)
        if leftover:
            print(f"NTP reserved {leftover[0].name} — never steal; hop", flush=True)
            hit = hop_one()
            if hit:
                published.append(hit)
                consecutive_fail = 0
            else:
                consecutive_fail += 1
            continue
        n = frontier_n(DIR)
        if n is None:
            consecutive_fail += 1
            print("FRONTIER_FAIL NTP", flush=True)
            continue
        ok, msg = publish_ntp(n)
        print(msg, flush=True)
        if ok:
            published.append(msg)
            consecutive_fail = 0
            continue
        errors.append({"ntp": msg, "n": n})
        if "theme table exhausted" in msg:
            print(f"THEMES_DONE r{n} — extend leftover table, do not dest-clone", flush=True)
            break
        if any(tok in msg.lower() for tok in ("already", "reserved", "not the frontier")):
            print("NTP race — never steal; hop", flush=True)
            hit = hop_one()
            if hit:
                published.append(hit)
                consecutive_fail = 0
            else:
                consecutive_fail += 1
            continue
        consecutive_fail += 1
    print(
        json.dumps(
            {
                "published": published,
                "n": len(published),
                "elapsed_s": int(time.time() - t0),
                "errors": errors[-6:],
            },
            indent=2,
        ),
        flush=True,
    )
    return 0 if published else 1


if __name__ == "__main__":
    raise SystemExit(main())
