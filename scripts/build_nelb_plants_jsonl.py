#!/usr/bin/env python3
"""One-shot builder: AST-extract NELB plants from the recover preserve (no exec)."""

from __future__ import annotations

import hashlib
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "pipelines"))

from nelb import catalog as cat  # noqa: E402
from nelb._contract import (  # noqa: E402
    NelbRefusal,
    CATALOG_FILENAME,
    CATALOG_FORMAT,
    CATALOG_ID,
    FACTORY,
    GENERATOR,
    LEGACY_COMMIT,
    LEGACY_REF,
    PLANTS_FILENAME,
    QUOTA_PER_ROUND,
    SOURCE_COMMIT,
    SOURCE_REF,
    dumps_exact_json,
)

RECOVER = SOURCE_COMMIT
NELB_DIR = REPO / "pipelines" / "nelb"


def _round_from_path(path: str) -> int | None:
    match = re.search(r"nelb-r(\d+)", path)
    return int(match.group(1)) if match else None


def _round_key(path: str) -> str | None:
    match = re.search(r"nelb-r(\d+)", path)
    return f"r{int(match.group(1))}" if match else None


def _version(path: str) -> int:
    match = re.search(r"/versions/(v(\d+))/", path)
    return int(match.group(2)) if match else 0


def _select_sources() -> dict[str, str]:
    listing = subprocess.check_output(
        ["git", "ls-tree", "-r", "--name-only", RECOVER],
        cwd=REPO,
        text=True,
    )
    paths = [
        line
        for line in listing.splitlines()
        if "/nelb-r" in line
        and line.endswith(".py")
        and "/versions/" in line
        and not line.endswith(".pyfrag")
    ]
    by_round: dict[str, tuple[int, str]] = {}
    for path in paths:
        key = _round_key(path)
        if not key:
            continue
        version = _version(path)
        if key not in by_round or version > by_round[key][0]:
            by_round[key] = (version, path)
    for key, (version, path) in list(by_round.items()):
        same = [item for item in paths if _round_key(item) == key and _version(item) == version]
        gen = [item for item in same if re.fullmatch(r"gen_r\d+\.py", Path(item).name)]
        if gen:
            by_round[key] = (version, gen[0])
    return {key: path for key, (_, path) in by_round.items()}


def _extract(path: str, want_round: int) -> tuple[cat.Plant, ...]:
    text = subprocess.check_output(["git", "show", f"{RECOVER}:{path}"], cwd=REPO, text=True)
    plants = cat.plants_from_source(text, Path(path).name)
    fixed: list[cat.Plant] = []
    for plant in plants:
        rid_round = cat._round_from_id(plant.record_id)
        if rid_round != want_round:
            raise NelbRefusal(
                cat.FINDING_FIELD_INVALID,
                f"{Path(path).name} id {plant.record_id} is not round r{want_round:02d}",
            )
        if plant.source_round != want_round:
            row = plant.as_mapping()
            row["source_round"] = want_round
            fixed.append(cat.plant_from_mapping(row, plant.record_id))
        else:
            fixed.append(plant)
    return tuple(fixed)


def main() -> int:
    sources = _select_sources()
    by_id: dict[str, cat.Plant] = {}
    rounds_ok: list[int] = []
    for key in sorted(sources, key=lambda item: int(item[1:])):
        path = sources[key]
        want = _round_from_path(path)
        if want is None:
            continue
        try:
            triple = _extract(path, want)
        except NelbRefusal:
            continue
        rounds_ok.append(want)
        for plant in triple:
            by_id.setdefault(plant.record_id, plant)
    plants = sorted(by_id.values(), key=lambda item: (item.source_round, item.index))
    if not plants:
        raise SystemExit("no plants extracted")
    lines = [
        dumps_exact_json(plant.as_mapping(), ensure_ascii=False, sort_keys=True)
        for plant in plants
    ]
    payload = "\n".join(lines) + "\n"
    digest = hashlib.sha256(payload.encode()).hexdigest()
    rounds = sorted({plant.source_round for plant in plants})
    deferred = [number for number in range(1, max(rounds) + 1) if number not in rounds]
    header = {
        "catalog_id": CATALOG_ID,
        "factory": FACTORY,
        "format": CATALOG_FORMAT,
        "generator": GENERATOR,
        "plant_count": len(plants),
        "plants_sha256": digest,
        "quota_per_round": QUOTA_PER_ROUND,
        "triples": len(plants) // QUOTA_PER_ROUND,
        "rounds": rounds,
        "extract": {
            "exec": False,
            "method": "ast.parse",
            "slice": "partial",
            "recover_ref": SOURCE_REF,
            "recover_commit": SOURCE_COMMIT,
            "legacy_ref": LEGACY_REF,
            "legacy_commit": LEGACY_COMMIT,
            "legacy_note": (
                "legacy-mill-lane has no nelb mill scripts; bridge fixtures only "
                "(see PR #288)."
            ),
            "n_rounds_committed": len(rounds),
            "n_plants_committed": len(plants),
            "deferred_rounds": deferred,
        },
    }
    NELB_DIR.mkdir(parents=True, exist_ok=True)
    (NELB_DIR / PLANTS_FILENAME).write_text(payload, encoding="utf-8")
    (NELB_DIR / CATALOG_FILENAME).write_text(
        dumps_exact_json(header, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(f"plants={len(plants)} rounds={len(rounds)} sha256={digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
