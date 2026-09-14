#!/usr/bin/env python3
"""Nest top-level RM-793 `rights` under `meta.rights` on preference arms.

stdlib-only structural fixer for PREFERENCE_ARM_EXTENSION_FIELDS.
Operates in place on a copy directory. Does not rewrite `state`,
`proposed_action`, diagnosis files, or `outputs/raw/`.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ARM_GLOBS = ("chosen-*.json", "rejected-*.json")
FROZEN_FIELDS = ("state", "proposed_action")


def sha256_obj(value: object) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def frozen_digests(arm: dict) -> dict[str, str]:
    return {field: sha256_obj(arm.get(field)) for field in FROZEN_FIELDS}


def nest_rights(arm: dict, label: str) -> bool:
    """Move a top-level `rights` object onto `meta.rights`. Return True if mutated."""

    if "rights" not in arm:
        return False
    stamp = arm["rights"]
    if not isinstance(stamp, dict):
        raise SystemExit(f"{label}: top-level rights is not an object")
    meta = arm.get("meta")
    if meta is None:
        arm["meta"] = {"rights": stamp}
    elif not isinstance(meta, dict):
        raise SystemExit(f"{label}: meta is not an object")
    elif "rights" not in meta:
        meta["rights"] = stamp
    elif meta["rights"] != stamp:
        raise SystemExit(f"{label}: top-level rights disagrees with meta.rights")
    del arm["rights"]
    if "rights" in arm:
        raise SystemExit(f"{label}: top-level rights survived nest")
    return True


def dump_arm(path: Path, arm: dict) -> None:
    path.write_text(
        json.dumps(arm, indent=2, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )


def process_arm(path: Path) -> dict:
    arm = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(arm, dict):
        raise SystemExit(f"{path.name}: arm is not an object")
    before_keys = list(arm.keys())
    before_frozen = frozen_digests(arm)
    before_meta = list(arm["meta"].keys()) if isinstance(arm.get("meta"), dict) else []
    mutated = nest_rights(arm, path.name)
    after_frozen = frozen_digests(arm)
    if before_frozen != after_frozen:
        raise SystemExit(f"{path.name}: froze state/proposed_action changed")
    if mutated:
        dump_arm(path, arm)
    return {
        "name": path.name,
        "mutated": mutated,
        "before_keys": before_keys,
        "after_keys": list(arm.keys()),
        "before_meta_keys": before_meta,
        "after_meta_keys": list(arm["meta"].keys()) if isinstance(arm.get("meta"), dict) else [],
        "top_rights_after": "rights" in arm,
        "meta_rights_after": isinstance(arm.get("meta"), dict) and "rights" in arm["meta"],
        "state_sha256": after_frozen["state"],
        "proposed_action_sha256": after_frozen["proposed_action"],
    }


def arm_paths(stage: Path) -> list[Path]:
    paths: list[Path] = []
    for glob in ARM_GLOBS:
        paths.extend(sorted(stage.glob(glob)))
    if not paths:
        raise SystemExit(f"no chosen-*.json or rejected-*.json under {stage}")
    return paths


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if len(args) != 1:
        print("usage: nest_rights.py <copy-dir>", file=sys.stderr)
        return 2
    stage = Path(args[0])
    if not stage.is_dir():
        raise SystemExit(f"not a directory: {stage}")
    if stage.resolve() == Path("/home/raulmc/rmems/synthetic-factory/outputs/raw"):
        raise SystemExit("refusing to write outputs/raw/")
    reports = [process_arm(path) for path in arm_paths(stage)]
    print(json.dumps({"stage": str(stage), "arms": reports}, indent=2, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
