#!/usr/bin/env python3
"""Wave-60 tail: remaining unused plants from mill r4301, then stop for chain."""
from __future__ import annotations
import importlib.util, json, signal, sys
from pathlib import Path

signal.signal(signal.SIGTERM, signal.SIG_IGN)
signal.signal(signal.SIGHUP, signal.SIG_IGN)

spec = importlib.util.spec_from_file_location("irc4301", "/tmp/irc_mill_r4301.py")
w = importlib.util.module_from_spec(spec)
spec.loader.exec_module(w)
w.m.notes_for = w.notes_for
w.extra_unique_guards()
used_svc, used_clu, used_tix, _ids = w.m.harvest_used(w.m.FACTORY_DIR)
REMAINING = [
    p for p in w.PLANTS
    if p["service"] not in used_svc and p["cluster"] not in used_clu and p["ticket"] not in used_tix
]
for label, xs in (
    ("slug", [p["slug"] for p in REMAINING]),
    ("svc", [p["service"] for p in REMAINING]),
    ("clu", [p["cluster"] for p in REMAINING]),
    ("tix", [p["ticket"] for p in REMAINING]),
    ("node", [p["node"] for p in REMAINING]),
    ("ns", [p["ns"] for p in REMAINING]),
):
    if len(set(xs)) != len(xs):
        raise SystemExit("dup " + label)
if len(REMAINING) % 2:
    raise SystemExit(f"odd remaining {len(REMAINING)}")
print(json.dumps({"tail_remaining": len(REMAINING), "svcs": [p["service"] for p in REMAINING]}), flush=True)

RAW = Path("/home/raulmc/rmems/synthetic-factory/outputs/raw/2026-08-19-agentic")
SKIP = {"sandbox-refusal-factory"}


def hops():
    out = []
    for d in sorted(RAW.iterdir()):
        if not d.is_dir() or d.name in SKIP:
            continue
        if list(d.glob("ROUND-r*.reserved.json")):
            continue
        try:
            st = w.m.txn(["frontier", str(d)])
        except Exception:
            continue
        out.append({"factory": d.name, "next_round": st.get("next_round")})
    return out


def publish_round(rnd, pair, reservation):
    w.m.BASE_ROUND, w.m.PLANTS = rnd, pair
    w.m.write_stage(Path(reservation["staging_dir"]), rnd)
    manifest = w.m.txn(
        ["publish", str(w.m.FACTORY_DIR), "--round", str(rnd), "--token", reservation["token"]]
    )
    rec = {"round": rnd, "ids": [e["id"] for e in w.m.pair_for_round(rnd)], "records": manifest.get("records")}
    print(json.dumps({"published": rec}), flush=True)
    return rec


def main():
    published = []
    offset = 0
    factory = w.m.FACTORY_DIR
    while offset + 1 < len(REMAINING):
        status = w.m.txn(["frontier", str(factory)])
        rnd = int(status["next_round"])
        pair = REMAINING[offset:offset + 2]
        w.m.BASE_ROUND, w.m.PLANTS = rnd, pair
        try:
            reservation = w.m.txn(
                ["reserve", str(factory), "--round", str(rnd), "--expected", "2"]
            )
        except RuntimeError as exc:
            print(json.dumps({
                "reserve_failed": str(exc),
                "round": rnd,
                "published": published,
                "unreserved_hops": hops()[:16],
            }), flush=True)
            return 2
        rec = publish_round(rnd, pair, reservation)
        published.append(rec)
        offset += 2
    print(json.dumps({"ok": True, "count": len(published), "last": published[-1] if published else None}), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
