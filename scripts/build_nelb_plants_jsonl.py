#!/usr/bin/env python3
"""One-shot builder: AST-extract NELB plants from the recover preserve (no exec)."""

from __future__ import annotations

import hashlib
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "pipelines"))
sys.path.insert(0, str(REPO / "scripts"))

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
    load_strict_json,
)
from nelb_committed_plants import read_committed_plants, round_from_record_id  # noqa: E402

RECOVER = SOURCE_COMMIT
NELB_DIR = REPO / "pipelines" / "nelb"
WAVE_MAX = 70


def _round_from_path(path: str) -> int | None:
    match = re.search(r"nelb-r(\d+)", path)
    return int(match.group(1)) if match else None


def _version(path: str) -> int:
    match = re.search(r"/versions/(v(\d+))/", path)
    return int(match.group(2)) if match else 0


def _git_executable() -> str:
    """Absolute ``git`` on PATH. A bare name is a partial-path launch."""

    found = shutil.which("git")
    if found is None:
        raise FileNotFoundError("git")
    return found


def _git_text(args: list[str]) -> str:
    git = _git_executable()
    # nosemgrep: python.lang.security.audit.dangerous-subprocess-use-audit.dangerous-subprocess-use-audit
    return subprocess.check_output(  # nosec B603 -- absolute git from PATH, no shell
        [git, *args],
        cwd=REPO,
        text=True,
    )


def _paths_by_round() -> dict[int, list[str]]:
    listing = _git_text(["ls-tree", "-r", "--name-only", RECOVER])
    paths = [
        line
        for line in listing.splitlines()
        if "/nelb-r" in line
        and line.endswith(".py")
        and "/versions/" in line
        and not line.endswith(".pyfrag")
    ]
    by_round: dict[int, list[str]] = {}
    for path in paths:
        want = _round_from_path(path)
        if want is None:
            continue
        by_round.setdefault(want, []).append(path)
    return by_round


def _pick_source(want_round: int, by_round: dict[int, list[str]]) -> str | None:
    candidates = sorted(
        by_round.get(want_round, []),
        key=lambda path: (
            0 if re.fullmatch(r"gen_r\d+\.py", Path(path).name) else 1,
            -_version(path),
            -len(path),
            path,
        ),
    )
    for path in candidates:
        text = _git_text(["show", f"{RECOVER}:{path}"])
        try:
            _extract(text, path, want_round)
        except NelbRefusal:
            continue
        return path
    return None


def _extract(text: str, path: str, want_round: int) -> tuple[cat.Plant, ...]:
    plants = cat.plants_from_source(text, Path(path).name)
    fixed: list[cat.Plant] = []
    for plant in plants:
        rid_round = round_from_record_id(plant.record_id)
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


def _extract_path(path: str, want_round: int) -> tuple[cat.Plant, ...]:
    text = _git_text(["show", f"{RECOVER}:{path}"])
    return _extract(text, path, want_round)


def _load_existing() -> tuple[tuple[cat.Plant, ...], list[int]] | None:
    plants_path = NELB_DIR / PLANTS_FILENAME
    meta_path = NELB_DIR / CATALOG_FILENAME
    if not plants_path.is_file() or not meta_path.is_file():
        return None
    meta = load_strict_json(meta_path.read_text(encoding="utf-8"))
    if not isinstance(meta, dict):
        raise SystemExit(f"{CATALOG_FILENAME} must be an object")
    extract = meta.get("extract")
    if not isinstance(extract, dict):
        raise SystemExit(f"{CATALOG_FILENAME} missing extract")
    deferred = extract.get("deferred_rounds")
    if not isinstance(deferred, list):
        raise SystemExit(f"{CATALOG_FILENAME} missing extract.deferred_rounds")
    plants = read_committed_plants(plants_path)
    return plants, [int(item) for item in deferred]


def _wave_deferred(rounds: list[int]) -> list[int]:
    present = set(rounds)
    return [number for number in range(1, WAVE_MAX + 1) if number not in present]


def _round_plants(want: int, by_round: dict[int, list[str]]) -> tuple[cat.Plant, ...] | None:
    """The plants of round ``want`` from its best source, or ``None`` when none extracts."""
    path = _pick_source(want, by_round)
    if path is None:
        return None
    try:
        return _extract_path(path, want)
    except NelbRefusal:
        return None


def _merge_deferred(
    existing: tuple[tuple[cat.Plant, ...], list[int]],
    by_round: dict[int, list[str]],
) -> tuple[dict[str, cat.Plant], list[int]]:
    """Committed plants plus every deferred round that now extracts; the rest stay deferred."""
    by_id: dict[str, cat.Plant] = {}
    still_deferred: list[int] = []
    committed, deferred = existing
    for plant in committed:
        by_id[plant.record_id] = plant
    for want in sorted(deferred):
        triple = _round_plants(want, by_round)
        if triple is None:
            still_deferred.append(want)
            continue
        for plant in triple:
            by_id[plant.record_id] = plant
    if len(by_id) == len(committed):
        raise SystemExit("no new plants extracted")
    return by_id, still_deferred


def _first_extract(by_round: dict[int, list[str]]) -> dict[str, cat.Plant]:
    """Plants of every round with a source that extracts; the first id seen wins."""
    by_id: dict[str, cat.Plant] = {}
    for want in sorted(by_round):
        triple = _round_plants(want, by_round)
        if triple is None:
            continue
        for plant in triple:
            by_id.setdefault(plant.record_id, plant)
    return by_id


def _plants_payload(plants: list[cat.Plant]) -> str:
    lines = [
        dumps_exact_json(plant.as_mapping(), ensure_ascii=False, sort_keys=True)
        for plant in plants
    ]
    return "\n".join(lines) + "\n"


def _catalog_header(
    plants: list[cat.Plant], digest: str, rounds: list[int], deferred_rounds: list[int]
) -> dict[str, Any]:
    return {
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
            "deferred_rounds": deferred_rounds,
        },
    }


def _write_catalog(payload: str, header: dict[str, Any]) -> None:
    NELB_DIR.mkdir(parents=True, exist_ok=True)
    (NELB_DIR / PLANTS_FILENAME).write_text(payload, encoding="utf-8", newline="\n")
    (NELB_DIR / CATALOG_FILENAME).write_text(
        dumps_exact_json(header, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def main() -> int:
    by_round = _paths_by_round()
    existing = _load_existing()
    if existing is not None:
        by_id, still_deferred = _merge_deferred(existing, by_round)
    else:
        by_id = _first_extract(by_round)
        still_deferred = _wave_deferred(sorted({plant.source_round for plant in by_id.values()}))
    plants = sorted(by_id.values(), key=lambda item: (item.source_round, item.index))
    if not plants:
        raise SystemExit("no plants extracted")
    payload = _plants_payload(plants)
    digest = hashlib.sha256(payload.encode()).hexdigest()
    rounds = sorted({plant.source_round for plant in plants})
    deferred_rounds = still_deferred if existing else _wave_deferred(rounds)
    _write_catalog(payload, _catalog_header(plants, digest, rounds, deferred_rounds))
    print(
        f"plants={len(plants)} rounds={len(rounds)} "
        f"landed_slice={len(rounds) - (len(existing[0]) // QUOTA_PER_ROUND if existing else 0)} "
        f"deferred={len(still_deferred)} sha256={digest}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
