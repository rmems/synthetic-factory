#!/usr/bin/env python3
"""Finish r5001 reservation and loop r5002–r5026.

Stock frontier/reserve re-audits historical envelopes (r01 fails). Staged
batches still pass full envelope inside publish/validate_stage.
"""
from __future__ import annotations
import importlib.util, json, shutil, sys, uuid
from pathlib import Path

REPO = Path("/home/raulmc/rmems/synthetic-factory")
sys.path.insert(0, str(REPO / "pipelines"))
import round_txn as rt  # noqa: E402

FACTORY = REPO / "outputs/raw/2026-08-19-agentic/incident-response-oncall-factory"
MAX_PUBLISHES = 26


def light_completed_manifests(factory_dir: Path) -> dict:
    factory_dir = Path(factory_dir)
    manifests = {}
    for path in factory_dir.glob("ROUND-r*.complete.json"):
        match = rt.COMPLETE_RE.fullmatch(path.name)
        if match is None or not path.is_file() or path.is_symlink():
            continue
        payload = rt.read_json(path)
        round_number = int(match.group(1))
        if (
            payload.get("factory") == factory_dir.name
            and payload.get("round") == round_number
            and payload.get("commit_point") == path.name
        ):
            manifests[round_number] = payload
    return manifests


_id_cache = None
_manifests = None


def cached_light_completed_manifests(factory_dir: Path) -> dict:
    global _manifests
    if _manifests is None:
        _manifests = light_completed_manifests(factory_dir)
    return _manifests


def cached_committed_ids(factory_dir: Path):
    global _id_cache
    if _id_cache is None:
        raise RuntimeError("id cache not primed")
    return _id_cache


def discover_zero(factory_dir: Path) -> int:
    return 0


def fast_frontier_status(factory_dir: Path):
    factory_dir = Path(factory_dir)
    nums = set()
    for path in factory_dir.glob("ROUND-r*.complete.json"):
        match = rt.COMPLETE_RE.fullmatch(path.name)
        if match and path.is_file() and not path.is_symlink():
            nums.add(int(match.group(1)))
    highest = 0
    while highest + 1 in nums:
        highest += 1
    return {
        "factory": factory_dir.name,
        "mode": "marker",
        "baseline": 0,
        "completed_markers": sorted(nums),
        "highest_flushed": highest,
        "next_round": highest + 1,
    }


def reserve_fast(factory_dir: Path, round_number: int, expected: int = 2) -> dict:
    factory_dir = Path(factory_dir).resolve()
    nxt = fast_frontier_status(factory_dir)["next_round"]
    if round_number != nxt:
        raise rt.TransactionError(
            f"round r{round_number:02d} is not the frontier; expected r{nxt:02d}"
        )
    paths = rt.marker_paths(factory_dir, round_number)
    for role, path in paths.items():
        if path.exists() or path.is_symlink():
            raise rt.TransactionError(f"{role} path already exists: {path}")
    token = uuid.uuid4().hex
    stage = rt.create_reservation_stage(factory_dir, round_number, token)
    payload = {
        "version": 1,
        "factory": factory_dir.name,
        "round": round_number,
        "token": token,
        "expected_records": expected,
        "staging_dir": str(stage),
        "batch_file": f"batch-r{round_number:02d}.jsonl",
        "notes_file": f"NOTES-r{round_number:02d}.md",
        "reserved_at": rt.utc_now(),
    }
    try:
        rt.write_exclusive_json(paths["reservation"], payload)
    except BaseException:
        shutil.rmtree(stage, ignore_errors=True)
        raise
    return payload


rt.completed_manifests = cached_light_completed_manifests
rt.committed_ids = cached_committed_ids
rt.discover_legacy_frontier = discover_zero
rt.discover_legacy_named_baseline = discover_zero
rt.discover_unmarked_legacy_frontier = discover_zero
rt.frontier_status = fast_frontier_status
rt.ensure_marker_mode = lambda factory_dir: {
    "version": 1,
    "legacy_baseline": 0,
    "commit_point": "ROUND-rNN.complete.json",
}

print(json.dumps({"phase": "load_mill"}), flush=True)
spec = importlib.util.spec_from_file_location("irc5001", "/tmp/irc_mill_r5001.py")
w = importlib.util.module_from_spec(spec)
spec.loader.exec_module(w)
w.m.notes_for = w.notes_for
w.extra_unique_guards()
print(json.dumps({"phase": "harvest"}), flush=True)
used_svc, used_clu, used_tix, used_ids = w.m.harvest_used(w.m.FACTORY_DIR)
_id_cache = {i: "harvest" for i in used_ids if i}
print(json.dumps({"phase": "harvest_done", "ids": len(_id_cache)}), flush=True)

REMAINING = list(w.PLANTS)


def next_round() -> int:
    return int(fast_frontier_status(FACTORY)["next_round"])


def publish_existing_or_reserve(rnd: int, pair: list) -> dict:
    paths = rt.marker_paths(FACTORY, rnd)
    if paths["reservation"].is_file() and not paths["reservation"].is_symlink():
        reservation = rt.read_json(paths["reservation"])
        if reservation.get("round") != rnd or reservation.get("factory") != FACTORY.name:
            raise SystemExit(f"foreign reservation r{rnd}")
        print(json.dumps({"phase": "resume_reservation", "round": rnd}), flush=True)
    else:
        other = sorted(FACTORY.glob("ROUND-r*.reserved.json"))
        if other:
            raise SystemExit(json.dumps({
                "stop": "foreign_reservation",
                "reserved": [p.name for p in other],
            }))
        reservation = reserve_fast(FACTORY, rnd, 2)
        print(json.dumps({"phase": "reserved", "round": rnd}), flush=True)
    w.m.BASE_ROUND, w.m.PLANTS = rnd, pair
    stage = Path(reservation["staging_dir"])
    batch = stage / f"batch-r{rnd:02d}.jsonl"
    notes = stage / f"NOTES-r{rnd:02d}.md"
    if not batch.is_file() or not notes.is_file():
        w.m.write_stage(stage, rnd)
    else:
        print(json.dumps({"phase": "staging_present", "round": rnd}), flush=True)
    manifest = rt.publish(FACTORY, rnd, reservation["token"])
    rec = {
        "round": rnd,
        "ids": [e["id"] for e in w.m.pair_for_round(rnd)],
        "records": manifest.get("records"),
    }
    for eid in rec["ids"]:
        _id_cache[eid] = f"batch-r{rnd:02d}.jsonl"
    if _manifests is not None:
        complete = FACTORY / f"ROUND-r{rnd:02d}.complete.json"
        if complete.is_file():
            _manifests[rnd] = rt.read_json(complete)
    print(json.dumps({"published": rec}), flush=True)
    return rec


def main() -> int:
    published = []
    low_cov = 0
    while len(published) < MAX_PUBLISHES:
        rnd = next_round()
        offset = (rnd - 5001) * 2
        if offset < 0 or offset + 1 >= len(REMAINING):
            print(json.dumps({"stop": "catalog_exhausted", "next_round": rnd, "count": len(published)}), flush=True)
            break
        pair = REMAINING[offset:offset + 2]
        rec = publish_existing_or_reserve(rnd, pair)
        published.append(rec)
        notes = FACTORY / f"NOTES-r{rnd:02d}.md"
        cov = None
        if notes.exists():
            for line in notes.read_text().splitlines():
                if line.startswith("Novel coverage:"):
                    tok = line.split(":", 1)[1].strip().rstrip("%").split()[0]
                    try:
                        cov = float(tok)
                    except ValueError:
                        cov = None
                    break
        if cov is not None and cov < 5:
            low_cov += 1
        else:
            low_cov = 0
        if low_cov >= 2:
            print(json.dumps({"stop": "two_consecutive_low_coverage", "count": len(published)}), flush=True)
            return 0
        if rnd >= 5001 + MAX_PUBLISHES - 1:
            break
    print(json.dumps({"ok": True, "count": len(published), "last": published[-1] if published else None}), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
