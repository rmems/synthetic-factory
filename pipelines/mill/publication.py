#!/usr/bin/env python3
"""Copy a validated mill run into a brand-new destination.

Refuses factory hop, ``outputs/raw``, an existing destination, and a run
whose records dest-stamp a foreign factory. Does not call ``round_txn``.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from . import catalog_load
from . import generate
from . import validation
from . import vocabulary as cv
from ._contract import bind_import_twin, dumps_exact_json, is_under_raw, load_strict_json, vocab

__all__ = ["PublishRequest", "publish"]


@dataclass(frozen=True)
class PublishRequest:
    run_dir: Path
    out_dir: Path
    catalog_dir: Path
    factory_id: str = cv.FACTORY_ID
    hop_factory: str | None = None


def _refuse_destination(path: Path) -> None:
    cv.refuse_when(path.exists(), cv.FINDING_DESTINATION_EXISTS, f"destination already exists: {path}")
    cv.refuse_when(is_under_raw(path), cv.FINDING_DESTINATION_UNDER_RAW, f"destination names the raw tree: {path}")


def _load_run(run_dir: Path) -> dict[str, Any]:
    run_path = run_dir / generate.RUN_FILENAME
    cv.refuse_when(not run_path.is_file(), cv.FINDING_RUN_FILE_MISSING, f"missing {generate.RUN_FILENAME}")
    payload = load_strict_json(run_path.read_text(encoding="utf-8"))
    cv.refuse_when(not isinstance(payload, dict), cv.FINDING_INPUT_NOT_AN_OBJECT, "RUN.json must be an object")
    return payload


def publish(request: PublishRequest) -> dict[str, Any]:
    """Validate ``run_dir`` against the catalog and write a receipt-only copy."""
    cv.refuse_when(
        request.hop_factory is not None,
        cv.FINDING_FACTORY_HOP_REFUSED,
        f"factory hop refused: {cv.shown(request.hop_factory)}",
    )
    cv.refuse_when(
        request.factory_id != cv.FACTORY_ID,
        cv.FINDING_FACTORY_MISMATCH,
        f"factory {cv.shown(request.factory_id)} is not {cv.FACTORY_ID}",
    )
    _refuse_destination(request.out_dir)
    summary = _load_run(request.run_dir)
    cv.refuse_when(
        summary.get("factory_id") != cv.FACTORY_ID,
        cv.FINDING_FACTORY_MISMATCH,
        f"run factory_id {cv.shown(summary.get('factory_id'))} is not {cv.FACTORY_ID}",
    )
    loaded = catalog_load.load_catalog(request.catalog_dir)
    pairs_path = request.run_dir / generate.PAIRS_FILENAME
    cv.refuse_when(not pairs_path.is_file(), cv.FINDING_RUN_FILE_MISSING, f"missing {generate.PAIRS_FILENAME}")
    lines = [line for line in pairs_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    plant_ids = summary.get("plant_ids")
    cv.refuse_when(
        not isinstance(plant_ids, list) or len(lines) != len(plant_ids) * cv.PAIR_QUOTA,
        cv.FINDING_RECORD_MALFORMED,
        "pairs.jsonl length does not match RUN.json plant_ids",
    )
    start_round = summary.get("start_round", 1)
    cv.refuse_when(
        not vocab.is_genuine_int(start_round) or start_round < 1,
        cv.FINDING_RECORD_MALFORMED,
        f"start_round {cv.shown(start_round)} is not a positive integer",
    )
    for index, plant_id in enumerate(plant_ids):
        try:
            plant = loaded.plant(plant_id)
        except KeyError:
            cv.refuse(cv.FINDING_RECORD_MALFORMED, f"unknown plant_id {cv.shown(plant_id)}")
        success = load_strict_json(lines[index * 2])
        failure = load_strict_json(lines[index * 2 + 1])
        validation.check_pair(success, failure, plant, start_round + index)
    request.out_dir.mkdir(parents=True)
    (request.out_dir / generate.PAIRS_FILENAME).write_bytes(pairs_path.read_bytes())
    (request.out_dir / generate.RUN_FILENAME).write_bytes((request.run_dir / generate.RUN_FILENAME).read_bytes())
    notes = request.run_dir / generate.NOTES_FILENAME
    if notes.is_file():
        (request.out_dir / generate.NOTES_FILENAME).write_bytes(notes.read_bytes())
    receipt = {
        "format": cv.PUBLICATION_FORMAT,
        "family": cv.FAMILY,
        "factory_id": cv.FACTORY_ID,
        "records": len(lines),
        "pairs": len(plant_ids),
        "plants_sha256": loaded.plants_sha256,
        "run": summary,
    }
    (request.out_dir / "receipt.json").write_text(
        dumps_exact_json(receipt, indent=2) + "\n", encoding="utf-8", newline="",
    )
    return receipt


bind_import_twin(__name__)
